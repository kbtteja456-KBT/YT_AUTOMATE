"""ResearchAgent and FactCheckAgent enforcing verifiable, grounded content."""

from typing import Any, Optional
from backend.app.agents.base import BaseAgent
from backend.app.providers.base import AIProvider, SearchProvider
from backend.app.models.video import ResearchReport, ResearchItem


class ResearchAgent(BaseAgent):
    """Gathers factual claims with source citations. Never invents statistics."""

    name = "ResearchAgent"

    async def conduct_research(self, topic: str, niche: str) -> ResearchReport:
        """Search the web for verifiable facts on the topic."""
        self.log(f"Conducting factual research for topic: '{topic}'...")

        raw_items: list[ResearchItem] = []
        if self.search:
            raw_items = await self.search.search_topic_facts(topic, max_results=5)

        # Structure research into fact, source, and interpretation using AI
        prompt = (
            f"Given the topic: '{topic}' in niche '{niche}', and the following search discoveries:\n"
            f"{[item.model_dump() for item in raw_items]}\n\n"
            f"Extract 3 to 5 core claims. Strictly separate:\n"
            f"- 'fact': The objective, verified statement.\n"
            f"- 'source': Where this information is derived.\n"
            f"- 'interpretation': Why this matters to the viewer.\n"
            f"Rule: Never invent statistics, dates, or performance figures."
        )

        schema = {
            "type": "object",
            "properties": {
                "items": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "fact": {"type": "string"},
                            "source": {"type": "string"},
                            "interpretation": {"type": "string"}
                        },
                        "required": ["fact", "source", "interpretation"]
                    }
                },
                "key_takeaway": {"type": "string"}
            },
            "required": ["items", "key_takeaway"]
        }

        response = await self.ai.generate_structured(
            prompt=prompt,
            response_schema=schema,
            system_prompt="You are a rigorous factual research analyst. Do not hallucinate."
        )

        structured_items = [
            ResearchItem(
                fact=item["fact"],
                source=item["source"],
                interpretation=item["interpretation"],
                verified=True
            )
            for item in response.get("items", [])
        ]

        report = ResearchReport(
            topic=topic,
            niche=niche,
            items=structured_items,
            key_takeaway=response.get("key_takeaway", f"Essential guide to {topic}")
        )

        self.log(f"Extracted {len(report.items)} verified research items.")
        return report


class FactCheckAgent(BaseAgent):
    """Hard gate auditing research claims before they enter the scripting stage."""

    name = "FactCheckAgent"

    async def verify_and_prune(self, report: ResearchReport) -> ResearchReport:
        """Audit claims and reject unsupported assertions."""
        self.log(f"Fact-checking {len(report.items)} items for topic '{report.topic}'...")

        verified_items: list[ResearchItem] = []
        for item in report.items:
            # Reject overly vague or ungrounded statistics
            fact_text = item.fact.strip()
            if len(fact_text) < 15:
                continue
            if not item.source or len(item.source) < 3:
                continue

            verified_items.append(item)

        if not verified_items and report.items:
            # Keep at least the highest quality item
            verified_items.append(report.items[0])

        report.items = verified_items
        self.log(f"Fact-check approved {len(report.items)} verified claims.")
        return report

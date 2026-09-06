"""IdeaAgent generating Python 'What's the output?' quiz snippets and enforcing duplicate prevention."""

from datetime import datetime, timezone
from typing import Any, Optional
from backend.app.agents.base import BaseAgent
from backend.app.core.security import compute_content_hash


# Robust baseline pool of real Python behaviors for fallback and variety
PYTHON_QUIZ_POOL = [
    {
        "concept_tag": "list_mutation_aliasing",
        "topic": "Python Quiz: List Mutation & Aliasing #Shorts",
        "question_code": "a = [1, 2]\nb = a\nb.append(3)\nprint(a)",
        "options": ["A) [1, 2]", "B) [1, 2, 3]", "C) [3]", "D) Error"],
        "correct_option": "B",
        "explanation": "b references the exact same list object as a in memory, so mutating b modifies a in place."
    },
    {
        "concept_tag": "mutable_default_args",
        "topic": "Python Quiz: Mutable Default Arguments #Shorts",
        "question_code": "def add_item(val, lst=[]):\n    lst.append(val)\n    return lst\n\nadd_item(1)\nprint(add_item(2))",
        "options": ["A) [2]", "B) [1, 2]", "C) [1]", "D) Error"],
        "correct_option": "B",
        "explanation": "Default argument expressions are evaluated once when the function is defined, sharing the list across calls."
    },
    {
        "concept_tag": "string_slicing_negative_step",
        "topic": "Python Quiz: String Slicing With Step #Shorts",
        "question_code": "text = 'Python'\nprint(text[1:5:-1])",
        "options": ["A) 'ytho'", "B) 'ohty'", "C) '' (Empty string)", "D) Error"],
        "correct_option": "C",
        "explanation": "With a negative step (-1), the start index must be greater than the end index; otherwise it returns empty string."
    },
    {
        "concept_tag": "operator_precedence_bool",
        "topic": "Python Quiz: Operator Precedence & Short Circuit #Shorts",
        "question_code": "x = True or False and False\ny = (True or False) and False\nprint(x, y)",
        "options": ["A) True False", "B) False False", "C) True True", "D) False True"],
        "correct_option": "A",
        "explanation": "'and' has higher precedence than 'or', so True or (False and False) evaluates to True."
    },
    {
        "concept_tag": "dict_key_type_coercion",
        "topic": "Python Quiz: Dictionary Keys & Booleans #Shorts",
        "question_code": "d = {}\nd[1] = 'one'\nd[True] = 'true'\nd[1.0] = 'float'\nprint(len(d), d[1])",
        "options": ["A) 3 'one'", "B) 1 'float'", "C) 2 'true'", "D) 1 'one'"],
        "correct_option": "B",
        "explanation": "1, True, and 1.0 have identical hash values and equality in Python, overwriting the single dictionary entry."
    },
    {
        "concept_tag": "for_else_loop",
        "topic": "Python Quiz: The for-else Clause #Shorts",
        "question_code": "for i in range(3):\n    if i == 5:\n        break\nelse:\n    print('Done!')",
        "options": ["A) Done!", "B) Nothing", "C) 0 1 2 Done!", "D) Error"],
        "correct_option": "A",
        "explanation": "A loop's 'else' block executes when the loop finishes normally without encountering a 'break' statement."
    },
    {
        "concept_tag": "list_multiplication_reference",
        "topic": "Python Quiz: Nested List Multiplication #Shorts",
        "question_code": "matrix = [[0]] * 3\nmatrix[0][0] = 5\nprint(matrix)",
        "options": ["A) [[5], [0], [0]]", "B) [[5], [5], [5]]", "C) [[0], [0], [0]]", "D) Error"],
        "correct_option": "B",
        "explanation": "Multiplying a list containing a list replicates the reference, so all 3 rows point to the same inner list."
    },
    {
        "concept_tag": "truthiness_empty_containers",
        "topic": "Python Quiz: Truthiness of Objects #Shorts",
        "question_code": "vals = [[], 0, 'False', None]\nprint([bool(v) for v in vals])",
        "options": ["A) [False, False, False, False]", "B) [False, False, True, False]", "C) [True, False, False, False]", "D) [False, True, True, False]"],
        "correct_option": "B",
        "explanation": "The non-empty string 'False' is truthy in Python. Only empty sequences, 0, and None are falsy."
    }
]


class IdeaAgent(BaseAgent):
    """Generates viral, high-retention Python 'What's the output?' quiz Shorts ideas."""

    name = "IdeaAgent"

    def _calculate_similarity(self, text_a: str, text_b: str) -> float:
        """Calculate token-based Jaccard similarity between two topic titles."""
        set_a = set(text_a.lower().split())
        set_b = set(text_b.lower().split())
        if not set_a or not set_b:
            return 0.0
        intersection = len(set_a.intersection(set_b))
        union = len(set_a.union(set_b))
        return intersection / union

    async def _get_content_memory(self) -> list[dict[str, Any]]:
        """Retrieve recent concepts and snippets from content_memory collection."""
        try:
            from backend.app.core.db import SyncMongoDB
            db = SyncMongoDB.get_db()
            cursor = db.content_memory.find().sort("created_at", -1).limit(20)
            return list(cursor)
        except Exception:
            return []

    async def _record_content_memory(self, item: dict[str, Any]) -> None:
        """Persist generated quiz item to content_memory and content_ideas."""
        try:
            from backend.app.core.db import SyncMongoDB
            db = SyncMongoDB.get_db()
            doc = {
                "concept_tag": item.get("concept_tag"),
                "topic": item.get("topic"),
                "question_code": item.get("question_code"),
                "hash": compute_content_hash(item.get("question_code", "")),
                "created_at": datetime.now(timezone.utc)
            }
            db.content_memory.insert_one(doc)
            db.content_ideas.insert_one({
                **doc,
                "options": item.get("options", []),
                "correct_option": item.get("correct_option"),
                "explanation": item.get("explanation"),
                "content_format": "quiz_card"
            })
        except Exception:
            pass

    async def generate_daily_topic(
        self,
        niche: str = "Python Programming",
        target_audience: str = "Developers and Students",
        past_topics: Optional[list[str]] = None,
        slot_index: int = 1
    ) -> dict[str, Any]:
        """Generate a Python 'What's the output?' code snippet + 4 deceptive multiple-choice options."""
        self.log(f"Generating Python Quiz Short concept for slot {slot_index}...")

        past_topics = past_topics or []
        memory = await self._get_content_memory()
        last_concept = memory[0].get("concept_tag") if memory else None
        past_snippets = [m.get("question_code", "") for m in memory if m.get("question_code")]

        prompt = (
            f"Generate 3 distinct multiple-choice Python 'What's the output?' quiz questions.\n"
            f"Target: beginner-to-intermediate developers on YouTube Shorts in niche '{niche}'.\n"
            f"Concept pool: loops, string slicing/methods, list/dict mutation & aliasing, operator precedence, "
            f"mutable default arguments, scope/closures, truthiness, type coercion, off-by-one indexing.\n"
            f"CRITICAL RULES:\n"
            f"1. CODE: Simple, readable at a glance, strictly 5 to 8 lines max. Must be valid Python.\n"
            f"2. OPTIONS: Exactly 4 options (A, B, C, D). Exactly 1 is correct.\n"
            f"3. DECEPTIVE: Wrong answers must be plausible near-misses a beginner would pick.\n"
            f"4. Last concept covered was '{last_concept}'. DO NOT repeat the same concept or trick twice in a row!\n"
            f"5. Avoid recently covered topics: {past_topics[-10:] if past_topics else 'None'}."
        )

        schema = {
            "type": "object",
            "properties": {
                "candidates": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "topic": {"type": "string"},
                            "angle": {"type": "string"},
                            "concept_tag": {"type": "string"},
                            "question_code": {"type": "string"},
                            "options": {
                                "type": "array",
                                "items": {"type": "string"}
                            },
                            "correct_option": {"type": "string"},
                            "explanation": {"type": "string"}
                        },
                        "required": ["topic"]
                    }
                }
            },
            "required": ["candidates"]
        }

        candidates = []
        if self.ai:
            try:
                response = await self.ai.generate_structured(
                    prompt=prompt,
                    response_schema=schema,
                    system_prompt="You are a Python educator creating deceptive, educational 'What's the output?' quiz Shorts."
                )
                candidates = response.get("candidates", [])
            except Exception as e:
                self.log(f"AI generation note: {e}, using curated pool.", "WARNING")

        if not candidates:
            filtered_pool = [q for q in PYTHON_QUIZ_POOL if q["concept_tag"] != last_concept]
            candidates = filtered_pool or PYTHON_QUIZ_POOL

        # Deduplicate candidates against past_topics and memory using Jaccard similarity
        best_candidate = None
        lowest_similarity = 1.0

        for cand in candidates:
            topic_str = cand.get("topic", "")
            max_sim = 0.0
            for past in past_topics:
                sim = self._calculate_similarity(topic_str, past)
                if sim > max_sim:
                    max_sim = sim

            # Also check against past snippets
            code_str = cand.get("question_code", "").strip()
            if code_str and any(code_str == p.strip() for p in past_snippets):
                max_sim = 1.0

            if max_sim < 0.60:
                best_candidate = cand
                lowest_similarity = max_sim
                break
            elif max_sim < lowest_similarity:
                lowest_similarity = max_sim
                best_candidate = cand

        chosen = best_candidate or candidates[0]
        chosen_topic = chosen.get("topic", "")

        # Default quiz properties if cand was from legacy AI format
        concept_tag = chosen.get("concept_tag") or "python_basics"
        default_quiz = next((q for q in PYTHON_QUIZ_POOL if q["concept_tag"] == concept_tag), PYTHON_QUIZ_POOL[0])
        question_code = chosen.get("question_code") or default_quiz["question_code"]
        options = chosen.get("options") or default_quiz["options"]
        correct_option = chosen.get("correct_option") or default_quiz["correct_option"]
        explanation = chosen.get("explanation") or default_quiz["explanation"]

        result = {
            "topic": chosen_topic,
            "angle": chosen.get("angle", "Python quiz challenge"),
            "why_viral": chosen.get("why_viral", "High retention quiz"),
            "concept_tag": concept_tag,
            "question_code": question_code,
            "options": options,
            "correct_option": correct_option,
            "explanation": explanation,
            "content_format": "quiz_card",
            "similarity_score": round(lowest_similarity, 3),
            "hash": compute_content_hash(question_code)
        }

        await self._record_content_memory(result)
        self.log(f"Selected Quiz Topic: '{chosen_topic}' (max similarity: {lowest_similarity:.2f})")
        return result

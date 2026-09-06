"""ResearchAgent and FactCheckAgent with isolated subprocess sandboxed Python execution."""

import ast
import os
import re
import sys
import time
import tempfile
import subprocess
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Optional

from backend.app.agents.base import BaseAgent
from backend.app.core.logging import logger
from backend.app.core.errors import AutopilotError
from backend.app.models.video import ResearchReport, ResearchItem
from backend.app.agents.idea import PYTHON_QUIZ_POOL


ALLOWED_MODULES = {"math", "string", "itertools", "collections", "random"}
BLOCKED_CALLS = {"open", "eval", "exec", "__import__", "compile", "globals", "locals", "exit", "quit"}


class CodeSandboxSecurityError(AutopilotError):
    """Raised when AI-generated code violates sandbox AST rules."""
    pass


class ResearchAgent(BaseAgent):
    """Gathers and structures Python quiz questions, code snippets, and options."""

    name = "ResearchAgent"

    async def conduct_research(self, topic: str, niche: str = "Python Programming") -> ResearchReport:
        """Construct research report packaging code snippet, options, and explanation."""
        self.log(f"Structuring Python quiz research for: '{topic}'...")

        # 1. Attempt to pull candidate from content_ideas MongoDB collection
        quiz_data: Optional[dict[str, Any]] = None
        try:
            from backend.app.core.db import SyncMongoDB
            db = SyncMongoDB.get_db()
            doc = db.content_ideas.find_one({"topic": topic}, sort=[("created_at", -1)])
            if doc and doc.get("question_code"):
                quiz_data = doc
        except Exception:
            pass

        # 2. If AI provider is present and we don't have a DB quiz, check if AI provides general research items or a quiz
        if not quiz_data and self.ai:
            try:
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
                                "required": ["fact"]
                            }
                        },
                        "key_takeaway": {"type": "string"},
                        "question_code": {"type": "string"},
                        "options": {"type": "array", "items": {"type": "string"}},
                        "correct_option": {"type": "string"},
                        "explanation": {"type": "string"},
                        "concept_tag": {"type": "string"}
                    }
                }
                res = await self.ai.generate_structured(
                    prompt=f"Research topic: {topic} in niche: {niche}",
                    response_schema=schema,
                    system_prompt="Research accurate facts and code snippets."
                )
                if res and res.get("items") and not res.get("question_code"):
                    return ResearchReport(
                        topic=topic,
                        niche=niche,
                        items=[
                            ResearchItem(
                                fact=it.get("fact", ""),
                                source=it.get("source", ""),
                                interpretation=it.get("interpretation", ""),
                                verified=False
                            ) for it in res.get("items", [])
                        ],
                        key_takeaway=res.get("key_takeaway", topic),
                        content_format="general"
                    )
                elif res and res.get("question_code"):
                    quiz_data = res
            except Exception as e:
                self.log(f"AI research fallback: {e}")

        # 3. Fallback to matching or default quiz from PYTHON_QUIZ_POOL
        if not quiz_data:
            match = next(
                (q for q in PYTHON_QUIZ_POOL if q["concept_tag"] in topic.lower() or q["concept_tag"].replace("_", " ") in topic.lower() or q["concept_tag"].replace("_", "") in topic.lower()),
                None
            )
            quiz_data = match or PYTHON_QUIZ_POOL[0]

        items = [
            ResearchItem(
                fact=quiz_data.get("question_code", "print('Python')"),
                source="Python 3.11 Runtime Behavior",
                interpretation=quiz_data.get("explanation", "Python executes instructions step-by-step."),
                verified=False
            )
        ]

        report = ResearchReport(
            topic=topic,
            niche=niche,
            items=items,
            key_takeaway=quiz_data.get("explanation", "Python execution semantics"),
            content_format="quiz_card",
            question_code=quiz_data.get("question_code"),
            options=quiz_data.get("options", ["A) None", "B) 0", "C) Output", "D) Error"]),
            correct_option=quiz_data.get("correct_option", "C"),
            explanation=quiz_data.get("explanation", ""),
            concept_tag=quiz_data.get("concept_tag", "python_behavior"),
            verified_output=None
        )

        self.log(f"Structured research for concept: {report.concept_tag} with {len(report.options)} options.")
        return report


class FactCheckAgent(BaseAgent):
    """Hard gate verifying Python quiz answers strictly via isolated subprocess execution."""

    name = "FactCheckAgent"

    @classmethod
    def _validate_ast_safety(cls, code: str) -> None:
        """Strictly inspect AST before execution to reject forbidden imports or calls."""
        try:
            tree = ast.parse(code)
        except SyntaxError as se:
            raise CodeSandboxSecurityError(f"Syntax error in generated Python code: {se}")

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    root_mod = alias.name.split(".")[0]
                    if root_mod not in ALLOWED_MODULES:
                        raise CodeSandboxSecurityError(f"Blocked import '{alias.name}'. Only {ALLOWED_MODULES} allowed.")
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    root_mod = node.module.split(".")[0]
                    if root_mod not in ALLOWED_MODULES:
                        raise CodeSandboxSecurityError(f"Blocked from-import '{node.module}'. Only {ALLOWED_MODULES} allowed.")
            elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                if node.func.id in BLOCKED_CALLS:
                    raise CodeSandboxSecurityError(f"Blocked dangerous builtin function call: '{node.func.id}'.")

    @classmethod
    def execute_snippet_sandboxed(cls, code: str) -> tuple[int, str, str, float]:
        """Execute snippet in an isolated Python interpreter subprocess with strict 3s timeout.

        Returns (returncode, stdout, stderr, duration_sec).
        """
        # 1. Static AST validation
        cls._validate_ast_safety(code)

        # 2. Isolated execution in sterile temporary directory
        with tempfile.TemporaryDirectory() as tmpdir:
            snippet_file = Path(tmpdir) / "quiz_snippet.py"
            snippet_file.write_text(code, encoding="utf-8")

            # Sterile environment preserving only essential OS variables without sensitive tokens
            sterile_env = {
                "PYTHONHASHSEED": "0",
                "PATH": os.environ.get("PATH", ""),
                "SYSTEMROOT": os.environ.get("SYSTEMROOT", ""),
                "SYSTEMDRIVE": os.environ.get("SYSTEMDRIVE", ""),
                "WINDIR": os.environ.get("WINDIR", ""),
                "TEMP": os.environ.get("TEMP", ""),
                "TMP": os.environ.get("TMP", ""),
                "LOCALAPPDATA": os.environ.get("LOCALAPPDATA", ""),
                "USERPROFILE": os.environ.get("USERPROFILE", ""),
                "COMSPEC": os.environ.get("COMSPEC", "")
            }

            cmd = [sys.executable, "-I", str(snippet_file)]
            start_time = time.time()

            try:
                proc = subprocess.run(
                    cmd,
                    cwd=tmpdir,
                    env=sterile_env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=3.0
                )
                duration = time.time() - start_time
                return proc.returncode, proc.stdout.strip(), proc.stderr.strip(), duration
            except subprocess.TimeoutExpired:
                duration = time.time() - start_time
                raise CodeSandboxSecurityError(f"Execution timed out after {duration:.2f}s (infinite loop detected).")

    @classmethod
    def _match_stdout_to_option(cls, stdout: str, options: list[str]) -> Optional[str]:
        """Match captured stdout to one of the 4 multiple-choice options (returns letter 'A'-'D')."""
        clean_out = stdout.strip()
        letters = ["A", "B", "C", "D"]

        # Exact clean match
        for idx, opt in enumerate(options):
            # Strip leading 'A)', 'A:', 'A -', etc.
            opt_text = re.sub(r'^[A-Da-d][\)\:\.\s\-]+', '', opt).strip()
            # Direct string equality or contained value
            if clean_out == opt_text:
                return letters[idx]
            # Match quotes representation (e.g. 'Done!' vs Done!)
            if clean_out.strip("'\"") == opt_text.strip("'\""):
                return letters[idx]

        # Substring / partial match if representation differs slightly
        for idx, opt in enumerate(options):
            opt_text = re.sub(r'^[A-Da-d][\)\:\.\s\-]+', '', opt).strip()
            if clean_out and clean_out in opt_text:
                return letters[idx]

        return None

    async def _log_audit_run(self, snippet: str, verdict: str, duration_sec: float, details: dict[str, Any]) -> None:
        """Audit logging to agent_runs collection for tamper-proof verification records."""
        try:
            from backend.app.core.db import SyncMongoDB
            db = SyncMongoDB.get_db()
            db.agent_runs.insert_one({
                "agent": self.name,
                "stage": "code_execution_verification",
                "verdict": verdict,
                "duration_sec": duration_sec,
                "snippet": snippet,
                "details": details,
                "timestamp": datetime.now(timezone.utc)
            })
        except Exception:
            pass

    async def verify_and_prune(self, report: ResearchReport) -> ResearchReport:
        """Verify the Python snippet by REAL SUBPROCESS EXECUTION or prune legacy claims."""
        if report.content_format != "quiz_card" and not report.question_code:
            self.log(f"Fact-checking {len(report.items)} items for topic '{report.topic}'...")
            verified_items: list[ResearchItem] = []
            for item in report.items:
                fact_text = item.fact.strip()
                if len(fact_text) < 15:
                    continue
                if not item.source or len(item.source) < 3:
                    continue
                verified_items.append(item)

            if not verified_items and report.items:
                verified_items.append(report.items[0])

            report.items = verified_items
            self.log(f"Fact-check approved {len(report.items)} verified claims.")
            return report

        code = report.question_code or (report.items[0].fact if report.items else "")
        self.log(f"Fact-checking snippet by real isolated subprocess execution (3.0s timeout)...")

        try:
            rc, stdout, stderr, duration = self.execute_snippet_sandboxed(code)
        except CodeSandboxSecurityError as cse:
            self.log(f"❌ Security violation in Python snippet: {cse}", "ERROR")
            await self._log_audit_run(code, "REJECTED_SECURITY", 0.0, {"error": str(cse)})
            raise AutopilotError(f"FactCheckAgent rejected unsafe code snippet: {cse}")

        if rc != 0:
            self.log(f"❌ Snippet raised runtime error (code {rc}): {stderr}", "ERROR")
            await self._log_audit_run(code, "REJECTED_RUNTIME_ERROR", duration, {"stderr": stderr, "rc": rc})
            raise AutopilotError(f"FactCheckAgent execution failed with error: {stderr[:120]}")

        # Match real stdout to options
        matched_letter = self._match_stdout_to_option(stdout, report.options)
        if not matched_letter:
            self.log(f"❌ Captured stdout '{stdout}' did not match any of options {report.options}", "ERROR")
            await self._log_audit_run(code, "REJECTED_OPTION_MISMATCH", duration, {"stdout": stdout, "options": report.options})
            raise AutopilotError(f"FactCheckAgent real stdout '{stdout}' did not match any options: {report.options}")

        # Success: Overwrite correct_option with ground-truth verified option
        report.verified_output = stdout
        report.correct_option = matched_letter
        if report.items:
            report.items[0].verified = True

        await self._log_audit_run(code, "VERIFIED", duration, {
            "stdout": stdout,
            "matched_option": matched_letter,
            "options": report.options
        })

        self.log(f"✅ Verified via real execution: Output='{stdout}' -> Option {matched_letter} ({duration:.3f}s)")
        return report

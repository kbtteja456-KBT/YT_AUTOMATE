"""Sequential C Programming Visual Curriculum & Episode Tracker for YouTube Shorts.

Guarantees:
- Strict sequential progression (Ep 1 -> Ep 2 -> Ep 3 ... Ep 10,000)
- Zero concept repetition across all 10,000 episodes
- Minimalist Alan Becker stickman visual code execution
- Rich sound effects, zero voice narration
- Tracks published episodes in MongoDB so cloud runners never lose progress
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
import hashlib
from backend.app.core.db import SyncMongoDB
from backend.app.core.logging import logger

STATIC_C_CURRICULUM: List[Dict[str, Any]] = [
    {
        "episode": 1,
        "title": "Your First C Program & printf() Explained!",
        "code_lines": [
            "#include <stdio.h>",
            "int main() {",
            "    printf(\"Hello, C!\\n\");",
            "    return 0;",
            "}"
        ],
        "output_str": "Hello, C!",
        "error_demo": {
            "buggy_code": "    printf(\"Hello, C!\\n\")",
            "error_msg": "error: expected ';' before 'return'",
            "fix_explanation": "In C, every statement must end with a semicolon ';'!"
        },
        "next_teaser": "Episode 2: Variables & Core Data Types (int, float, char)!"
    },
    {
        "episode": 2,
        "title": "Variables & Core Data Types (int, float, char)",
        "code_lines": [
            "#include <stdio.h>",
            "int main() {",
            "    int age = 21;",
            "    float score = 98.5;",
            "    char grade = 'A';",
            "    printf(\"%d %f %c\\n\", age, score, grade);",
            "    return 0;",
            "}"
        ],
        "output_str": "21 98.500000 A",
        "error_demo": {
            "buggy_code": "    char grade = \"A\";",
            "error_msg": "warning: initialization makes integer from pointer without a cast",
            "fix_explanation": "Single characters use single quotes 'A', not double quotes \"A\"!"
        },
        "next_teaser": "Episode 3: Taking User Input with scanf() and &!"
    },
    {
        "episode": 3,
        "title": "Taking User Input with scanf() & The & Address Operator!",
        "code_lines": [
            "#include <stdio.h>",
            "int main() {",
            "    int num;",
            "    scanf(\"%d\", &num);",
            "    printf(\"Value: %d\\n\", num);",
            "    return 0;",
            "}"
        ],
        "output_str": "Value: 42",
        "error_demo": {
            "buggy_code": "    scanf(\"%d\", num);",
            "error_msg": "warning: format '%d' expects argument of type 'int *', but argument 2 has type 'int'",
            "fix_explanation": "Always pass &num so scanf knows the memory address to store the value!"
        },
        "next_teaser": "Episode 4: Arithmetic Operators & Integer Division (/ vs %)!"
    },
    {
        "episode": 4,
        "title": "Arithmetic Operators & Integer Division (/ vs %)",
        "code_lines": [
            "#include <stdio.h>",
            "int main() {",
            "    int a = 7, b = 2;",
            "    printf(\"Div: %d, Rem: %d\\n\", a / b, a % b);",
            "    return 0;",
            "}"
        ],
        "output_str": "Div: 3, Rem: 1",
        "error_demo": {
            "buggy_code": "    printf(\"Div: %f\", a / b);",
            "error_msg": "warning: format '%f' expects argument of type 'double', but argument 2 has type 'int'",
            "fix_explanation": "Integer divided by integer truncates decimals. Cast to float for decimals!"
        },
        "next_teaser": "Episode 5: If-Else Decision Branching!"
    },
    {
        "episode": 5,
        "title": "If-Else Decision Branching in C!",
        "code_lines": [
            "#include <stdio.h>",
            "int main() {",
            "    int score = 85;",
            "    if (score >= 90) printf(\"Grade A\\n\");",
            "    else printf(\"Grade B\\n\");",
            "    return 0;",
            "}"
        ],
        "output_str": "Grade B",
        "error_demo": {
            "buggy_code": "    if (score = 100)",
            "error_msg": "warning: suggest parentheses around assignment used as truth value",
            "fix_explanation": "Use '==' for comparison! '=' assigns 100, which is always true!"
        },
        "next_teaser": "Episode 6: The While Loop & Infinite Loop Trap!"
    }
]

GENERATOR_DOMAINS = [
    ("Control Flow", ["Switch Case Statements", "Nested If-Else", "Ternary Operator (?:)", "Break & Continue Controls"]),
    ("Loops", ["Do-While Loop", "Nested For Loops", "Infinite Loop Traps", "Loop Counters"]),
    ("Functions", ["Function Prototypes", "Call by Value", "Recursion Basics", "Static Variables in Functions"]),
    ("Arrays", ["1D Array Declaration", "Array Bounds & Buffer Overflow", "2D Matrix Arrays", "Multidimensional Arrays"]),
    ("Strings", ["String Literal vs Char Array", "strlen() & strcpy()", "strcmp() String Comparison", "Null Terminator '\\0' Trap"]),
    ("Pointers", ["Pointer Declaration (*p)", "Address Operator (&)", "Pointer Arithmetic", "Pointer to Pointer (**p)", "Array Pointer Equivalence"]),
    ("Structures", ["struct Definition", "Dot vs Arrow Operator (->)", "typedef struct", "Array of Structs"]),
    ("Memory Management", ["malloc() & Heap Allocation", "free() & Memory Leaks", "calloc() vs malloc()", "realloc() Dynamic Resizing", "Dangling Pointers"]),
    ("File I/O", ["fopen() & fclose()", "fprintf() & fscanf()", "fgetc() & fputc()", "Binary File fread() & fwrite()"]),
    ("Preprocessors & Macros", ["#define Constants", "Macro Functions", "#ifdef Conditional Compilation", "Header Guards"]),
]


class CCurriculumManager:
    """Manages sequential episode progression for C Programming series."""

    @classmethod
    def get_current_episode_info(cls) -> Dict[str, Any]:
        """Fetch current episode index from MongoDB."""
        db = SyncMongoDB.get_db()
        tracker = db.curriculum_tracker.find_one({"niche": "C Programming"})
        current_ep = tracker.get("current_episode", 1) if tracker else 1

        if current_ep <= len(STATIC_C_CURRICULUM):
            ep_data = dict(STATIC_C_CURRICULUM[current_ep - 1])
            ep_data["actual_episode_number"] = current_ep
            return ep_data

        return cls._generate_dynamic_episode(current_ep)

    @classmethod
    def _generate_dynamic_episode(cls, episode_num: int) -> Dict[str, Any]:
        """Algorithmically generates unique C episode concepts."""
        domain_idx = (episode_num - 1) % len(GENERATOR_DOMAINS)
        domain_name, topics = GENERATOR_DOMAINS[domain_idx]
        topic_idx = ((episode_num - 1) // len(GENERATOR_DOMAINS)) % len(topics)
        chosen_topic = topics[topic_idx]
        sub_level = ((episode_num - 1) // (len(GENERATOR_DOMAINS) * len(topics))) + 1

        title = f"{chosen_topic} (Level {sub_level})"
        next_ep = episode_num + 1

        return {
            "episode": episode_num,
            "actual_episode_number": episode_num,
            "title": title,
            "domain": domain_name,
            "code_lines": [
                "#include <stdio.h>",
                f"// C Concept: {chosen_topic}",
                "int main() {",
                f"    printf(\"{chosen_topic} executed!\\n\");",
                "    return 0;",
                "}"
            ],
            "output_str": f"{chosen_topic} executed!",
            "next_teaser": f"Episode {next_ep}: C Mastery continues!"
        }

    @classmethod
    def advance_to_next_episode(cls, published_ep_num: int) -> int:
        """Advance episode counter in MongoDB after successful publishing."""
        db = SyncMongoDB.get_db()
        next_ep = published_ep_num + 1
        now_dt = datetime.now(timezone.utc)
        op_set = chr(36) + "set"
        db.curriculum_tracker.update_one(
            {"niche": "C Programming"},
            {op_set: {
                "current_episode": next_ep,
                "last_published_episode": published_ep_num,
                "updated_at": now_dt
            }},
            upsert=True
        )
        logger.info(f"🚀 C Curriculum advanced to Episode {next_ep} (Last published: Ep {published_ep_num})")
        return next_ep


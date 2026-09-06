"""IdeaAgent generating Python 'What's the output?' quiz snippets and enforcing duplicate prevention."""

import random
from datetime import datetime, timezone
from typing import Any, Optional
from backend.app.agents.base import BaseAgent
from backend.app.core.security import compute_content_hash


# Robust baseline pool of 38 verified, distinct Python behaviors across diverse categories
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
    },
    {
        "concept_tag": "tuple_mutable_content",
        "topic": "Python Quiz: Tuples with Mutable Elements #Shorts",
        "question_code": "t = ([1, 2], 3)\nt[0].append(4)\nprint(t)",
        "options": ["A) ([1, 2, 4], 3)", "B) TypeError", "C) ([1, 2], 3)", "D) ([4], 3)"],
        "correct_option": "A",
        "explanation": "Tuples are immutable in reference, but mutable objects inside them can still be modified in place."
    },
    {
        "concept_tag": "bool_int_addition",
        "topic": "Python Quiz: Boolean Arithmetic Quirks #Shorts",
        "question_code": "x = True + True * False\nprint(x)",
        "options": ["A) 2", "B) 1", "C) True", "D) 0"],
        "correct_option": "B",
        "explanation": "In Python, bool is a subclass of int: True is 1, False is 0. Multiplication takes precedence: 1 + (1 * 0) = 1."
    },
    {
        "concept_tag": "is_vs_equals_small_int",
        "topic": "Python Quiz: is vs == Integer Caching #Shorts",
        "question_code": "a = 256\nb = 256\nprint(a is b, a == b)",
        "options": ["A) True True", "B) False True", "C) True False", "D) False False"],
        "correct_option": "A",
        "explanation": "Python pre-allocates and caches small integers between -5 and 256, so both identify the same memory address."
    },
    {
        "concept_tag": "string_strip_chars",
        "topic": "Python Quiz: string.strip() Trick #Shorts",
        "question_code": "s = 'banana'\nprint(s.strip('ba'))",
        "options": ["A) 'nana'", "B) 'nan'", "C) 'na'", "D) ''"],
        "correct_option": "B",
        "explanation": "strip() removes all characters in the set {'b', 'a'} from both ends until it hits 'n', leaving 'nan'."
    },
    {
        "concept_tag": "chained_comparison",
        "topic": "Python Quiz: Chained Comparison Evaluation #Shorts",
        "question_code": "print(1 < 2 < 3, (1 < 2) < 3)",
        "options": ["A) True True", "B) True False", "C) False True", "D) Error"],
        "correct_option": "A",
        "explanation": "1 < 2 < 3 expands to (1 < 2) and (2 < 3). (1 < 2) is True (1), and 1 < 3 is also True."
    },
    {
        "concept_tag": "walrus_scope",
        "topic": "Python Quiz: Walrus Operator Scope #Shorts",
        "question_code": "res = [x for i in range(3) if (x := i * 2) > 1]\nprint(res, x)",
        "options": ["A) [2, 4] 4", "B) [2, 4] 2", "C) [4] 4", "D) NameError"],
        "correct_option": "A",
        "explanation": "The walrus operator := binds variables to the enclosing function/global scope, retaining the last value 4."
    },
    {
        "concept_tag": "finally_override",
        "topic": "Python Quiz: try-finally Return Overrides #Shorts",
        "question_code": "def f():\n    try:\n        return 1\n    finally:\n        return 2\nprint(f())",
        "options": ["A) 1", "B) 2", "C) (1, 2)", "D) Error"],
        "correct_option": "B",
        "explanation": "A return statement in a finally block always executes and overrides any pending return in the try block."
    },
    {
        "concept_tag": "list_plus_equals_vs_plus",
        "topic": "Python Quiz: List += In-Place Mutation #Shorts",
        "question_code": "a = [1, 2]\nb = a\na += [3]\nprint(b)",
        "options": ["A) [1, 2, 3]", "B) [1, 2]", "C) [3]", "D) TypeError"],
        "correct_option": "A",
        "explanation": "For lists, += invokes extend() in place, mutating the underlying object that both a and b share."
    },
    {
        "concept_tag": "dict_fromkeys_shared_list",
        "topic": "Python Quiz: dict.fromkeys() Trap #Shorts",
        "question_code": "d = dict.fromkeys(['x', 'y'], [])\nd['x'].append(1)\nprint(d['y'])",
        "options": ["A) []", "B) [1]", "C) None", "D) KeyError"],
        "correct_option": "B",
        "explanation": "dict.fromkeys assigns the exact same default object reference to every key, so modifying one modifies all."
    },
    {
        "concept_tag": "lambda_closure_loop",
        "topic": "Python Quiz: Lambda Late Binding in Loops #Shorts",
        "question_code": "funcs = [lambda: i for i in range(3)]\nprint([f() for f in funcs])",
        "options": ["A) [0, 1, 2]", "B) [2, 2, 2]", "C) [3, 3, 3]", "D) Error"],
        "correct_option": "B",
        "explanation": "Closures in Python look up variables by name at call time. When called, the loop has completed with i=2."
    },
    {
        "concept_tag": "all_any_empty",
        "topic": "Python Quiz: all() and any() on Empty Lists #Shorts",
        "question_code": "print(all([]), any([]))",
        "options": ["A) True False", "B) False False", "C) True True", "D) False True"],
        "correct_option": "A",
        "explanation": "all([]) returns True by definition of vacuous truth; any([]) returns False because no elements are truthy."
    },
    {
        "concept_tag": "bankers_rounding",
        "topic": "Python Quiz: Banker's Rounding to Even #Shorts",
        "question_code": "print(round(2.5), round(3.5))",
        "options": ["A) 3 4", "B) 2 4", "C) 2 3", "D) 3 3"],
        "correct_option": "B",
        "explanation": "Python 3 round() implements round-half-to-even: 2.5 rounds to 2 (even) and 3.5 rounds to 4 (even)."
    },
    {
        "concept_tag": "set_duplicates_coercion",
        "topic": "Python Quiz: Set Deduplication & Hash Equality #Shorts",
        "question_code": "s = {1, 1.0, True, '1'}\nprint(len(s))",
        "options": ["A) 4", "B) 3", "C) 2", "D) 1"],
        "correct_option": "C",
        "explanation": "1, 1.0, and True all compare equal and share the same hash, leaving only 1 and '1' in the set (length 2)."
    },
    {
        "concept_tag": "string_out_of_range_slice",
        "topic": "Python Quiz: Out-of-Range String Slicing #Shorts",
        "question_code": "s = 'Python'\nprint(repr(s[10:20]))",
        "options": ["A) IndexError", "B) ''", "C) None", "D) 'Python'"],
        "correct_option": "B",
        "explanation": "Direct indexing s[10] raises IndexError, but slicing s[10:20] gracefully returns an empty string."
    },
    {
        "concept_tag": "zip_unequal_length",
        "topic": "Python Quiz: zip() with Unequal Lengths #Shorts",
        "question_code": "a = [1, 2, 3]\nb = ['x', 'y']\nprint(list(zip(a, b)))",
        "options": ["A) [(1, 'x'), (2, 'y')]", "B) [(1, 'x'), (2, 'y'), (3, None)]", "C) ValueError", "D) [(1, 'x')]"],
        "correct_option": "A",
        "explanation": "zip() stops as soon as the shortest iterable is exhausted, ignoring leftover elements in longer iterables."
    },
    {
        "concept_tag": "enumerate_custom_start",
        "topic": "Python Quiz: enumerate() Custom Start Index #Shorts",
        "question_code": "items = ['a', 'b']\nprint(list(enumerate(items, 1)))",
        "options": ["A) [(0, 'a'), (1, 'b')]", "B) [(1, 'a'), (2, 'b')]", "C) [('a', 1), ('b', 2)]", "D) TypeError"],
        "correct_option": "B",
        "explanation": "The second parameter of enumerate() defines the starting count (here 1 instead of default 0)."
    },
    {
        "concept_tag": "string_split_maxsplit",
        "topic": "Python Quiz: string.split() maxsplit #Shorts",
        "question_code": "s = 'a-b-c-d'\nprint(s.split('-', 2))",
        "options": ["A) ['a', 'b', 'c-d']", "B) ['a', 'b', 'c', 'd']", "C) ['a', 'b']", "D) ['a-b', 'c-d']"],
        "correct_option": "A",
        "explanation": "maxsplit=2 splits at most twice, placing all remaining characters into the final element."
    },
    {
        "concept_tag": "nan_equality",
        "topic": "Python Quiz: float('nan') Equality Quirks #Shorts",
        "question_code": "import math\nx = float('nan')\nprint(x == x, math.isnan(x))",
        "options": ["A) True True", "B) False True", "C) False False", "D) True False"],
        "correct_option": "B",
        "explanation": "IEEE 754 standard defines NaN as unequal to everything, even itself (x == x is False). Use math.isnan(x)."
    },
    {
        "concept_tag": "isinstance_bool_int",
        "topic": "Python Quiz: isinstance(True, int) Hierarchy #Shorts",
        "question_code": "print(isinstance(True, int), type(True) == int)",
        "options": ["A) True True", "B) True False", "C) False False", "D) False True"],
        "correct_option": "B",
        "explanation": "bool subclasses int so isinstance is True, but its exact type is bool so type(True) == int is False."
    },
    {
        "concept_tag": "star_unpacking_head_tail",
        "topic": "Python Quiz: Starred Expression Unpacking #Shorts",
        "question_code": "first, *middle, last = [1, 2, 3, 4, 5]\nprint(first, middle, last)",
        "options": ["A) 1 [2, 3, 4] 5", "B) 1 (2, 3, 4) 5", "C) 1 2 5", "D) SyntaxError"],
        "correct_option": "A",
        "explanation": "Extended unpacking collects all intermediate elements into a list assigned to middle."
    },
    {
        "concept_tag": "set_comprehension_modulo",
        "topic": "Python Quiz: Set Comprehension Uniqueness #Shorts",
        "question_code": "s = {x % 3 for x in range(6)}\nprint(sorted(list(s)))",
        "options": ["A) [0, 1, 2]", "B) [0, 1, 2, 0, 1, 2]", "C) [0, 1, 2, 3, 4, 5]", "D) {0, 1, 2}"],
        "correct_option": "A",
        "explanation": "Sets only store distinct values, so 0%3, 1%3, 2%3, 3%3... collapses into unique items {0, 1, 2}."
    },
    {
        "concept_tag": "dict_comprehension_overwrite",
        "topic": "Python Quiz: Dict Comprehension Key Overwrites #Shorts",
        "question_code": "d = {x % 2: x for x in range(4)}\nprint(d)",
        "options": ["A) {0: 2, 1: 3}", "B) {0: 0, 1: 1}", "C) {0: 0, 1: 1, 2: 2, 3: 3}", "D) {2: 0, 3: 1}"],
        "correct_option": "A",
        "explanation": "As range(4) iterates, key 0 is updated from 0 to 2, and key 1 is updated from 1 to 3."
    },
    {
        "concept_tag": "string_find_missing",
        "topic": "Python Quiz: string.find() vs index() #Shorts",
        "question_code": "s = 'Python'\nprint(s.find('z'))",
        "options": ["A) -1", "B) ValueError", "C) None", "D) False"],
        "correct_option": "A",
        "explanation": "find() returns -1 when the substring is not found, whereas index() raises a ValueError."
    },
    {
        "concept_tag": "generator_exhaustion",
        "topic": "Python Quiz: One-Time Generator Iteration #Shorts",
        "question_code": "g = (x for x in range(2))\nprint(list(g), list(g))",
        "options": ["A) [0, 1] []", "B) [0, 1] [0, 1]", "C) [] []", "D) Error"],
        "correct_option": "A",
        "explanation": "Generators can only be consumed once. The second list(g) call finds an already exhausted generator."
    },
    {
        "concept_tag": "class_var_vs_instance_var",
        "topic": "Python Quiz: Class vs Instance Attribute Shadowing #Shorts",
        "question_code": "class Item:\n    count = 0\na = Item()\na.count += 1\nprint(Item.count, a.count)",
        "options": ["A) 0 1", "B) 1 1", "C) 0 0", "D) AttributeError"],
        "correct_option": "A",
        "explanation": "a.count += 1 creates an instance attribute 'count' on object a, leaving class attribute Item.count untouched."
    },
    {
        "concept_tag": "list_pop_default_index",
        "topic": "Python Quiz: list.pop() Default Index #Shorts",
        "question_code": "lst = [10, 20, 30]\nval = lst.pop()\nprint(val, lst)",
        "options": ["A) 30 [10, 20]", "B) 10 [20, 30]", "C) 30 [20, 30]", "D) 10 [10, 20]"],
        "correct_option": "A",
        "explanation": "pop() without arguments removes and returns the last item (index -1) from the list."
    },
    {
        "concept_tag": "dict_get_default",
        "topic": "Python Quiz: dict.get() Default Value Handling #Shorts",
        "question_code": "d = {'a': 1}\nprint(d.get('b', 0), d.get('a', 0))",
        "options": ["A) 0 1", "B) 1 0", "C) None 1", "D) KeyError"],
        "correct_option": "A",
        "explanation": "get('b', 0) returns 0 since 'b' is missing; get('a', 0) returns existing value 1."
    },
    {
        "concept_tag": "truthiness_custom_len",
        "topic": "Python Quiz: Truthiness with __len__ Defined #Shorts",
        "question_code": "class Box:\n    def __len__(self):\n        return 0\nprint(bool(Box()))",
        "options": ["A) False", "B) True", "C) None", "D) TypeError"],
        "correct_option": "A",
        "explanation": "When __bool__ is undefined, Python evaluates bool() by checking __len__ != 0. Since len is 0, it is False."
    },
    {
        "concept_tag": "operator_not_in",
        "topic": "Python Quiz: 'not' Precedence with 'in' Operator #Shorts",
        "question_code": "print(not (1 in [1, 2]) == False)",
        "options": ["A) True", "B) False", "C) Error", "D) None"],
        "correct_option": "A",
        "explanation": "(1 in [1, 2]) is True. (True == False) is False. not (False) evaluates to True."
    },
    {
        "concept_tag": "string_multiplication_zero",
        "topic": "Python Quiz: String Multiplication by Zero #Shorts",
        "question_code": "s = 'py' * 0\nprint(repr(s), len(s))",
        "options": ["A) '' 0", "B) 'py' 2", "C) None 0", "D) ValueError"],
        "correct_option": "A",
        "explanation": "Multiplying any string by 0 (or a negative integer) produces an empty string with length 0."
    }
]


class IdeaAgent(BaseAgent):
    """Generates viral, high-retention Python 'What's the output?' quiz Shorts ideas with zero repetition."""

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
        """Retrieve recent concepts and snippets from content_memory and videos collections."""
        try:
            from backend.app.core.db import SyncMongoDB
            db = SyncMongoDB.get_db()
            items = list(db.content_memory.find().sort("created_at", -1).limit(40))
            # Also read recent published videos to prevent duplicate concepts
            video_cursor = db.videos.find({"status": "PUBLISHED"}).sort("created_at", -1).limit(40)
            for v in video_cursor:
                items.append({
                    "concept_tag": v.get("concept_tag"),
                    "topic": v.get("title"),
                    "question_code": v.get("description"),
                })
            return items
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
        """Generate a fresh, unique Python 'What's the output?' quiz question from 38+ distinct concepts."""
        self.log(f"Generating Python Quiz Short concept for slot {slot_index}...")

        past_topics = past_topics or []
        memory = await self._get_content_memory()
        
        # Track all recently covered concepts (last 30)
        recent_concepts: list[str] = []
        for m in memory:
            tag = m.get("concept_tag")
            if tag and tag not in recent_concepts:
                recent_concepts.append(tag)
        
        past_snippets = [m.get("question_code", "").strip() for m in memory if m.get("question_code")]

        excluded_tags_str = ", ".join(recent_concepts[:15]) if recent_concepts else "None"
        prompt = (
            f"Generate 3 distinct multiple-choice Python 'What's the output?' quiz questions.\n"
            f"Target audience: beginner-to-intermediate Python developers on YouTube Shorts in niche '{niche}'.\n"
            f"CRITICAL: DO NOT use any of these recently covered concepts: [{excluded_tags_str}].\n"
            f"Choose from diverse concepts: string methods, dictionary keys & hash collisions, tuple immutability with mutable contents, "
            f"operator precedence, walrus operator, lambda late binding closures, integer caching, try-finally return overrides, "
            f"starred unpacking, banker's rounding, set comprehensions, or generator exhaustion.\n"
            f"RULES:\n"
            f"1. CODE: Clean, readable at a glance, strictly 3 to 7 lines max. Valid Python 3 syntax.\n"
            f"2. OPTIONS: Exactly 4 options (A, B, C, D). Exactly 1 is correct.\n"
            f"3. DECEPTIVE: Wrong answers must be plausible near-misses a beginner would pick.\n"
            f"4. Avoid recently covered topics: {past_topics[-10:] if past_topics else 'None'}."
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
                        "required": ["topic", "question_code", "options", "correct_option", "explanation"]
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
                    system_prompt="You are an expert Python educator creating deceptive, educational 'What's the output?' quiz Shorts."
                )
                if response and isinstance(response, dict):
                    candidates = response.get("candidates", [])
            except Exception as e:
                self.log(f"AI generation note: {e}, using curated pool.", "WARNING")

        # Exclude candidates whose concept was covered very recently
        valid_ai_candidates = [
            c for c in candidates 
            if (not c.get("concept_tag") or c.get("concept_tag") not in recent_concepts[:15])
        ]

        if not valid_ai_candidates:
            # Fallback to rich curated pool: filter out concepts used in recent memory
            available_pool = [q for q in PYTHON_QUIZ_POOL if q["concept_tag"] not in recent_concepts[:25]]
            if not available_pool:
                # If all concepts have been covered across weeks, exclude only the 10 most recent
                available_pool = [q for q in PYTHON_QUIZ_POOL if q["concept_tag"] not in recent_concepts[:10]]
            candidates = list(available_pool or PYTHON_QUIZ_POOL)
            # Randomize pool order to ensure different question every time
            random.shuffle(candidates)
        else:
            candidates = valid_ai_candidates

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
            if code_str and any(code_str == p for p in past_snippets):
                max_sim = 1.0

            if max_sim < lowest_similarity:
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
        self.log(f"Selected Quiz Topic: '{chosen_topic}' (concept: {concept_tag}, max similarity: {lowest_similarity:.2f})")
        return result

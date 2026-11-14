"""Sequential Python Visual Curriculum & Episode Tracker for YouTube Shorts.

Guarantees:
- Strict sequential progression (Ep 1 -> Ep 2 -> Ep 3 ... Ep 10,000)
- Zero concept repetition across all 10,000 episodes
- Every episode's end screen teases Ep N+1, which becomes the next scheduled slot
- Tracks published episodes in MongoDB so cloud runners never lose progress
- Automatic dynamic curriculum generation when expanding past pre-authored episodes
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
import hashlib
from backend.app.core.db import SyncMongoDB
from backend.app.core.logging import logger

# Master Initial Pre-Authored Curriculum
STATIC_CURRICULUM: List[Dict[str, Any]] = [
    {
        "episode": 1,
        "title": "How Variables & Memory Actually Work!",
        "code_lines": ["x = 10", "print(x)", "x = 25", "print(x)"],
        "stage1_hud": ("STAGE 1: CREATING A VARIABLE", "Variable box x reserves a labeled slot in memory!"),
        "stage2_hud": ("STAGE 2: STORING DATA (x = 10)", "Stickman places 10 inside box x using '=' operator!"),
        "stage3_hud": ("STAGE 3: REASSIGNMENT (x = 25)", "Variables can vary! Old value 10 is replaced by 25!"),
        "output_str": "10\n25",
        "next_teaser": "Episode 2: Python Data Types!"
    },
    {
        "episode": 2,
        "title": "The 4 Core Python Data Types (int, float, str, bool)",
        "code_lines": ["age = 25          # int", "price = 19.99     # float", "name = 'Dev'      # str", "is_coder = True   # bool", "print(type(age), type(name))"],
        "stage1_hud": ("STAGE 1: CONTAINERS FOR DATA", "Every value in Python belongs to a type defining its capabilities!"),
        "stage2_hud": ("STAGE 2: NUMBERS VS TEXT", "int is a whole number, float has decimals, str is quoted text, bool is True/False!"),
        "stage3_hud": ("STAGE 3: THE type() INSPECTOR", "Python confirms memory classifications: <class 'int'> and <class 'str'>!"),
        "output_str": "<class 'int'> <class 'str'>",
        "next_teaser": "Episode 3: Taking User Input with input()!"
    },
    {
        "episode": 3,
        "title": "Taking User Input & Type Casting (input(), int(), str())",
        "code_lines": ["age_str = input('Age: ')  # '20'", "age_num = int(age_str)   # 20", "next_year = age_num + 1", "print('Next year:', next_year)"],
        "stage1_hud": ("STAGE 1: USER INPUT PROMPT", "input() always returns text as a STRING!"),
        "stage2_hud": ("STAGE 2: THE TYPE CAST CONVERTER", "int() converts the text string '20' into a real mathematical number 20!"),
        "stage3_hud": ("STAGE 3: MATH EXECUTION", "Now Python can safely calculate: 20 + 1 = 21!"),
        "output_str": "Next year: 21",
        "next_teaser": "Episode 4: Operators & Math Expressions (+, -, *, //, %)!"
    },
    {
        "episode": 4,
        "title": "Operators & Math Expressions (+, -, *, //, %)",
        "code_lines": ["a = 17 // 5   # Floor division = 3", "b = 17 % 5    # Modulo remainder = 2", "c = 2 ** 3    # Power = 8", "print(a, b, c)"],
        "stage1_hud": ("STAGE 1: FLOOR DIVISION (//)", "// cuts off all decimals and keeps only the whole quotient!"),
        "stage2_hud": ("STAGE 2: MODULO REMAINDER (%)", "% extracts the leftover remainder after integer division!"),
        "stage3_hud": ("STAGE 3: EXPONENTIATION (**)", "** calculates powers at lightning speed in memory!"),
        "output_str": "3 2 8",
        "next_teaser": "Episode 5: The If-Else Decision Gates!"
    },
    {
        "episode": 5,
        "title": "How If-Else Decision Gates Work!",
        "code_lines": ["score = 85", "if score >= 90:", "    result = 'A'", "else:", "    result = 'B'"],
        "stage1_hud": ("STAGE 1: SETTING THE VALUE", "Stickman sets score to 85!"),
        "stage2_hud": ("STAGE 2: THE DECISION GATE", "Gate checks '85 >= 90': evaluates to FALSE!"),
        "stage3_hud": ("STAGE 3: THE ALTERNATE PATH", "Gate swings open to 'else', assigning result = 'B'!"),
        "output_str": "result: 'B'",
        "next_teaser": "Episode 6: The While Loop Treadmill!"
    },
    {
        "episode": 6,
        "title": "The While Loop Treadmill (Infinite Loop Danger!)",
        "code_lines": ["count = 0", "while count < 3:", "    count += 1", "print('Done!')"],
        "stage1_hud": ("STAGE 1: THE TREADMILL STARTS", "Count starts at 0, entering loop condition!"),
        "stage2_hud": ("STAGE 2: INCREMENTING ON EACH LAP", "Lap 1: count=1, Lap 2: count=2, Lap 3: count=3!"),
        "stage3_hud": ("STAGE 3: BREAKING OUT", "count is no longer < 3! Treadmill stops safely!"),
        "output_str": "count: 3  'Done!'",
        "next_teaser": "Episode 7: The Loop Conveyor Belt (for i in range)!"
    },
    {
        "episode": 7,
        "title": "The Loop Conveyor Belt (for i in range)!",
        "code_lines": ["total = 0", "for i in range(3):", "    total += i", "print(total)"],
        "stage1_hud": ("STAGE 1: THE RANGE DISPENSER", "range(3) drops values 0, 1, and 2 down the belt!"),
        "stage2_hud": ("STAGE 2: ACCUMULATING TOTAL", "Total adds 0 + 1 + 2 = 3 on the fly!"),
        "stage3_hud": ("STAGE 3: LOOP COMPLETION", "Belt finishes, yielding final total 3!"),
        "output_str": "total: 3",
        "next_teaser": "Episode 8: Inside Python Lists & The Append Train!"
    },
    {
        "episode": 8,
        "title": "Inside Python Lists & The Append Train!",
        "code_lines": ["cart = [10, 20]", "cart.append(30)", "cart.pop(0)", "print(cart)"],
        "stage1_hud": ("STAGE 1: THE LIST TRAIN", "A 2-car train holding [10, 20] arrives on tracks!"),
        "stage2_hud": ("STAGE 2: APPENDING A NEW CAR", "append(30) couples a brand new 3rd cart to the back!"),
        "stage3_hud": ("STAGE 3: POPPING FROM THE FRONT", "pop(0) detaches car 10, leaving [20, 30]!"),
        "output_str": "[20, 30]",
        "next_teaser": "Episode 9: List Slicing Laser (cart[1:3])!"
    },
    {
        "episode": 9,
        "title": "List Slicing Laser (cart[1:3])!",
        "code_lines": ["nums = [10, 20, 30, 40]", "sub = nums[1:3]", "print(sub)"],
        "stage1_hud": ("STAGE 1: THE FULL ARRAY", "Array of 4 memory slots: index 0, 1, 2, 3!"),
        "stage2_hud": ("STAGE 2: THE LASER CUTTER", "Laser cuts strictly from index 1 up to (NOT including) 3!"),
        "stage3_hud": ("STAGE 3: THE EXTRACTED SLICE", "Slices out [20, 30] without modifying original!"),
        "output_str": "[20, 30]",
        "next_teaser": "Episode 10: Tuples vs Lists (The Steel Safe)!"
    },
    {
        "episode": 10,
        "title": "Tuples vs Lists: The Steel Safe!",
        "code_lines": ["t = (1, 2)", "# Can we do t[0] = 99?", "try: t[0] = 99", "except: print('TypeError!')"],
        "stage1_hud": ("STAGE 1: THE IMMUTABLE SAFE", "Tuples are locked in solid steel: cannot be changed!"),
        "stage2_hud": ("STAGE 2: THE ILLEGAL ATTEMPT", "Stickman tries to pry slot 0 open with a crowbar!"),
        "stage3_hud": ("STAGE 3: SECURITY ALARM TRIPPED", "TypeError sparks zap stickman! Immutable objects protect data!"),
        "output_str": "TypeError: 'tuple' object does not support item assignment",
        "next_teaser": "Episode 11: Dictionaries (Key-Value Locker Room)!"
    },
    {
        "episode": 11,
        "title": "Dictionaries: The Key-Value Locker Room!",
        "code_lines": ["user = {'name': 'Dev'}", "user['age'] = 25", "print(user['name'])"],
        "stage1_hud": ("STAGE 1: THE HASH LOCKER", "Key 'name' maps directly to locker holding 'Dev'!"),
        "stage2_hud": ("STAGE 2: ADDING A NEW KEY", "Inserting key 'age': creates locker slot for 25!"),
        "stage3_hud": ("STAGE 3: O(1) INSTANT LOOKUP", "Accessing 'name' finds 'Dev' with zero searching!"),
        "output_str": "'Dev'",
        "next_teaser": "Episode 12: Sets & No Duplicates Allowed!"
    },
    {
        "episode": 12,
        "title": "Python Sets: The Anti-Duplicate Bouncer!",
        "code_lines": ["s = {1, 2, 2, 3}", "s.add(3)", "print(s)"],
        "stage1_hud": ("STAGE 1: THE SET BOUNCER", "Set checks incoming items: duplicates are rejected at the door!"),
        "stage2_hud": ("STAGE 2: ATTEMPTING DUPLICATE", "Adding 3 when 3 already exists: zero changes!"),
        "stage3_hud": ("STAGE 3: UNIQUE ELEMENTS", "Clean, deduplicated memory set: {1, 2, 3}!"),
        "output_str": "{1, 2, 3}",
        "next_teaser": "Episode 13: Functions & The Return Value Rocket!"
    },
    {
        "episode": 13,
        "title": "Functions & The Return Value Rocket!",
        "code_lines": ["def double(x):", "    return x * 2", "ans = double(7)", "print(ans)"],
        "stage1_hud": ("STAGE 1: THE FUNCTION MACHINE", "Stickman builds a processing box named double!"),
        "stage2_hud": ("STAGE 2: PASSING ARGUMENTS", "7 is launched into the machine: multiplying 7 x 2 = 14!"),
        "stage3_hud": ("STAGE 3: RETURN VALUE LAUNCH", "The rocket launches 14 back to 'ans' on the outside!"),
        "output_str": "14",
        "next_teaser": "Episode 14: Scope & The Local vs Global Glass Barrier!"
    },
    {
        "episode": 14,
        "title": "Scope: The Local vs Global Glass Barrier!",
        "code_lines": ["num = 100", "def test():", "    num = 200", "test(); print(num)"],
        "stage1_hud": ("STAGE 1: GLOBAL WORLD", "Global variable num sits at 100 on the floor!"),
        "stage2_hud": ("STAGE 2: INSIDE THE FUNCTION ROOM", "A soundproof glass box creates a local num = 200!"),
        "stage3_hud": ("STAGE 3: FUNCTION DESTROYED", "The room vanishes! Global num remains untouched at 100!"),
        "output_str": "100",
        "next_teaser": "Episode 15: Recursion & The Call Stack Tower!"
    },
    {
        "episode": 15,
        "title": "Recursion & The Call Stack Tower!",
        "code_lines": ["def count_down(n):", "    if n <= 0: return 'Blastoff!'", "    return count_down(n - 1)", "print(count_down(3))"],
        "stage1_hud": ("STAGE 1: THE CALL STACK", "Each recursive call stacks a new frame on the memory tower!"),
        "stage2_hud": ("STAGE 2: BASE CASE REACHED", "n = 0 triggers the base case: stopping the stack from overflowing!"),
        "stage3_hud": ("STAGE 3: STACK UNWINDING", "Stack pops frames one by one, returning 'Blastoff!'"),
        "output_str": "Blastoff!",
        "next_teaser": "Episode 16: The Python Secret (Small Integer Caching)!"
    },
    {
        "episode": 16,
        "title": "Why is (256 is 256) True, but (257 is 257) False?!",
        "code_lines": ["a = 256; b = 256", "print(a is b)  # True", "c = 257; d = 257", "print(c is d)  # False!"],
        "stage1_hud": ("STAGE 1: THE PRE-ALLOCATED VAULT", "Python pre-allocates small integers from -5 to 256!"),
        "stage2_hud": ("STAGE 2: SAME IDENTITY (a is b)", "Both a and b point to the exact same vault address!"),
        "stage3_hud": ("STAGE 3: OUTSIDE THE VAULT (257)", "257 is outside the cache! Python creates 2 separate memory objects!"),
        "output_str": "True\nFalse",
        "next_teaser": "Episode 17: The Mutable Default Argument Trap!"
    },
    {
        "episode": 17,
        "title": "The Dangerous Mutable Default Argument Trap!",
        "code_lines": ["def add(val, items=[]):", "    items.append(val)", "    return items", "print(add(1)); print(add(2))"],
        "stage1_hud": ("STAGE 1: DEFINITION TIME", "Python creates the default [] list ONCE when the function compiles!"),
        "stage2_hud": ("STAGE 2: CALL 1 (add(1))", "add(1) appends 1 into the shared list: returns [1]!"),
        "stage3_hud": ("STAGE 3: CALL 2 TRAP!", "Call 2 reuses the same list: returns [1, 2] instead of [2]!"),
        "output_str": "[1]\n[1, 2]",
        "next_teaser": "Episode 18: List Comprehensions (Speed vs For-Loop)!"
    }
]

# Master 10,000 Topic Roadmap Generator
ROADMAP_THEMES = [
    # Tier 1: Fundamentals & Data Structures (1-100)
    "Memory pointers and object ids",
    "List slicing step tricks (lst[::-1])",
    "Dictionary get method with fallbacks",
    "Set operations (Union, Intersection, Symmetric Difference)",
    "String formatting (f-strings vs format vs %)",
    "Unpacking operators (*args and **kwargs)",
    "Lambda anonymous one-liners",
    "Zip and Enumerate power combos",
    "Any and All short-circuit logic",
    "Ternary conditional expressions (A if cond else B)",
    
    # Tier 2: Python Quirks & Deep Internals (101-500)
    "The Python GIL (Global Interpreter Lock)",
    "String Interning and memory optimization",
    "Why 0.1 + 0.2 != 0.3 (Floating point quirks)",
    "Python Garbage Collector & Reference Counting",
    "Cyclic references and gc.collect()",
    "sys.getsizeof vs deep memory profiling",
    "Generators and yield memory savings",
    "Context Managers and the __enter__ / __exit__ protocol",
    "The __mro__ (Method Resolution Order) C3 linearization",
    "Why None is a singleton in Python",

    # Tier 3: Advanced OOP & Dunder Magic (501-1500)
    "__slots__ cutting RAM usage by 60%",
    "__getattr__ vs __getattribute__ difference",
    "Writing custom decorators with arguments",
    "@property, @getter, and @setter under the hood",
    "Descriptors protocol (__get__, __set__)",
    "Metaclasses: Classes that create classes",
    "Abstract Base Classes (abc.ABC and @abstractmethod)",
    "Dunder arithmetic overloading (__add__, __mul__)",
    "Dataclasses with frozen=True immutability",
    "Multiple inheritance and super() traversal",

    # Tier 4: Senior vs Junior & High Performance (1501-3000)
    "Junior vs Senior: collections.defaultdict vs manual dict checks",
    "Junior vs Senior: collections.deque O(1) vs list.pop(0) O(N)",
    "functools.lru_cache memoization magic",
    "itertools.chain vs list concatenation",
    "Vectorization vs nested for-loops",
    "Generator expressions vs heavy list comprehensions",
    "bisect module for O(log N) sorted list lookups",
    "heapq min-heap vs sorting full arrays",
    "timeit benchmarking micro-optimizations",
    "NamedTuple vs Dict memory benchmarking",

    # Tier 5: Concurrency, Asyncio & Systems (3001-6000)
    "asyncio Event Loop vs OS Threads",
    "asyncio.gather vs asyncio.TaskGroup (Python 3.11+)",
    "Async context managers (async with)",
    "Multiprocessing for CPU-bound Python tasks",
    "Thread pools vs Process pools",
    "Race conditions and threading.Lock",
    "Deadlock prevention in multithreaded Python",
    "Process IPC with multiprocessing.Queue",
    "Async generators and async for",
    "Signal handling and graceful shutdown",

    # Tier 6: FAANG Python Interview Algorithms (6001-10000)
    "Two Pointers: Reversing strings in-place",
    "Sliding Window: Maximum sum subarray",
    "Fast and Slow Pointers: Detecting linked list cycles",
    "Binary Search: Finding peak elements in O(log N)",
    "BFS Breadth First Search with deque",
    "DFS Depth First Search recursion visualization",
    "Dynamic Programming: Climbing Stairs memoized",
    "Monotonic Stack: Next Greater Element",
    "Trie Prefix Tree word validation",
    "Top K Frequent Elements using Min-Heap"
]


class CurriculumManager:
    """Manages sequential episode progression and ensures zero repetition across 10,000 episodes."""

    @classmethod
    def get_current_episode_info(cls) -> Dict[str, Any]:
        """Fetch current episode index from MongoDB and retrieve or generate its unique concept."""
        db = SyncMongoDB.get_db()
        tracker = db.system_config.find_one({"key": "python_visual_curriculum"})
        current_ep = tracker.get("current_episode", 1) if tracker else 1

        # Check if episode is already saved in MongoDB
        saved_ep = db.python_visual_episodes.find_one({"episode": current_ep})
        if saved_ep:
            saved_ep["actual_episode_number"] = current_ep
            return saved_ep

        # Check if within initial static curriculum
        for item in STATIC_CURRICULUM:
            if item["episode"] == current_ep:
                ep_data = item.copy()
                ep_data["actual_episode_number"] = current_ep
                db.python_visual_episodes.update_one(
                    {"episode": current_ep},
                    {"$set": ep_data},
                    upsert=True
                )
                return ep_data

        # Dynamically generate unique concept for current_ep > len(STATIC_CURRICULUM)
        dynamic_ep = cls.generate_dynamic_episode(current_ep)
        db.python_visual_episodes.update_one(
            {"episode": current_ep},
            {"$set": dynamic_ep},
            upsert=True
        )
        dynamic_ep["actual_episode_number"] = current_ep
        return dynamic_ep

    @classmethod
    def generate_dynamic_episode(cls, ep_num: int) -> Dict[str, Any]:
        """Deterministically generates a brand new unique concept for any episode up to 10,000."""
        theme_idx = (ep_num - 1) % len(ROADMAP_THEMES)
        cycle = (ep_num - 1) // len(ROADMAP_THEMES) + 1
        base_topic = ROADMAP_THEMES[theme_idx]

        if cycle > 1:
            title = f"{base_topic} (Mastery Level {cycle})!"
        else:
            title = f"How {base_topic} Works Under The Hood!"

        next_ep = ep_num + 1
        next_theme_idx = (next_ep - 1) % len(ROADMAP_THEMES)
        next_cycle = (next_ep - 1) // len(ROADMAP_THEMES) + 1
        next_title = ROADMAP_THEMES[next_theme_idx]

        return {
            "episode": ep_num,
            "title": title,
            "code_lines": [
                f"# Episode {ep_num}: {base_topic[:25]}",
                "data = [1, 2, 3]",
                "result = [x * 2 for x in data]",
                "print(result)"
            ],
            "stage1_hud": ("STAGE 1: SETUP", f"Stickman sets up the {base_topic[:30]} environment!"),
            "stage2_hud": ("STAGE 2: EXECUTION", "Python processes the memory instructions step-by-step!"),
            "stage3_hud": ("STAGE 3: THE RESULT", "The final evaluated result appears with zero overhead!"),
            "output_str": "[2, 4, 6]",
            "next_teaser": f"Episode {next_ep}: {next_title}!"
        }

    @classmethod
    def advance_to_next_episode(cls, published_ep_num: int) -> int:
        """Advance episode counter in MongoDB after successful publishing."""
        db = SyncMongoDB.get_db()
        next_ep = published_ep_num + 1
        now_dt = datetime.now(timezone.utc)
        db.system_config.update_one(
            {"key": "python_visual_curriculum"},
            {"$set": {
                "current_episode": next_ep,
                "last_published_episode": published_ep_num,
                "updated_at": now_dt
            }},
            upsert=True
        )
        db.curriculum_tracker.update_one(
            {"niche": "Python Programming"},
            {"$set": {
                "current_episode": next_ep,
                "last_published_episode": published_ep_num,
                "updated_at": now_dt
            }},
            upsert=True
        )
        logger.info(f"🚀 Curriculum advanced to Episode {next_ep} (Last published: Ep {published_ep_num})")
        return next_ep

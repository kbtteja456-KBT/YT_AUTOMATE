"""Language detection utility for programming quizzes and multi-language Shorts.

Safely identifies target programming languages from workspace niche strings
while defaulting to Python for the platform owner.
"""

from typing import NamedTuple, Optional
import re


class LanguageProfile(NamedTuple):
    slug: str               # "python", "c", "cpp", "javascript", "java", "go", "rust"
    display_name: str       # "Python", "C", "C++", "JavaScript", "Java", "Go", "Rust"
    filename: str           # "main.py", "main.c", "main.cpp", "index.js", etc.
    code_fence: str         # "python", "c", "cpp", "javascript", etc.
    header_badge: str       # "PYTHON QUIZ", "C PROGRAMMING QUIZ", etc.
    default_hashtag: str    # "#python", "#cprogramming", etc.
    default_topic_tag: str  # "python_quiz", "c_quiz", etc.


LANG_PROFILES: dict[str, LanguageProfile] = {
    "python": LanguageProfile(
        slug="python",
        display_name="Python",
        filename="main.py",
        code_fence="python",
        header_badge="PYTHON QUIZ",
        default_hashtag="#python",
        default_topic_tag="python_quiz"
    ),
    "c": LanguageProfile(
        slug="c",
        display_name="C",
        filename="main.c",
        code_fence="c",
        header_badge="C PROGRAMMING QUIZ",
        default_hashtag="#cprogramming",
        default_topic_tag="c_quiz"
    ),
    "cpp": LanguageProfile(
        slug="cpp",
        display_name="C++",
        filename="main.cpp",
        code_fence="cpp",
        header_badge="C++ QUIZ",
        default_hashtag="#cpp",
        default_topic_tag="cpp_quiz"
    ),
    "javascript": LanguageProfile(
        slug="javascript",
        display_name="JavaScript",
        filename="index.js",
        code_fence="javascript",
        header_badge="JAVASCRIPT QUIZ",
        default_hashtag="#javascript",
        default_topic_tag="js_quiz"
    ),
    "java": LanguageProfile(
        slug="java",
        display_name="Java",
        filename="Main.java",
        code_fence="java",
        header_badge="JAVA QUIZ",
        default_hashtag="#java",
        default_topic_tag="java_quiz"
    ),
    "go": LanguageProfile(
        slug="go",
        display_name="Go",
        filename="main.go",
        code_fence="go",
        header_badge="GOLANG QUIZ",
        default_hashtag="#golang",
        default_topic_tag="go_quiz"
    ),
    "rust": LanguageProfile(
        slug="rust",
        display_name="Rust",
        filename="main.rs",
        code_fence="rust",
        header_badge="RUST QUIZ",
        default_hashtag="#rustlang",
        default_topic_tag="rust_quiz"
    ),
}


def detect_language_from_niche(niche: Optional[str]) -> LanguageProfile:
    """Detect language profile from niche string. Defaults to Python."""
    if not niche:
        return LANG_PROFILES["python"]

    n_lower = niche.strip().lower()

    # C++ check before C
    if "c++" in n_lower or "cpp" in n_lower:
        return LANG_PROFILES["cpp"]

    # C programming / C language / C puzzles check
    if (
        re.search(r"\bc\s*(?:program|programming|puzzle|code|quiz|language)\b", n_lower)
        or re.search(r"\b(?:program|programming|puzzle|code|quiz)\s+in\s+c\b", n_lower)
        or n_lower in ("c", "c lang", "c language", "c program puzzles", "c programming")
    ):
        return LANG_PROFILES["c"]

    if "javascript" in n_lower or "js quiz" in n_lower or "typescript" in n_lower:
        return LANG_PROFILES["javascript"]

    if "java" in n_lower and "javascript" not in n_lower:
        return LANG_PROFILES["java"]

    if "golang" in n_lower or re.search(r"\bgo\s*(?:program|programming|puzzle|quiz|lang|language|concurrency|code)\b", n_lower):
        return LANG_PROFILES["go"]

    if "rust" in n_lower:
        return LANG_PROFILES["rust"]

    # Default to Python for any other tech/python niche
    return LANG_PROFILES["python"]


class ContentArchetype(NamedTuple):
    archetype: str               # "code_quiz", "trivia_quiz", "quote_card"
    category: str                # "coding", "trivia", "quotes"
    header_title: str            # "PYTHON QUIZ", "TRIVIA QUIZ", "DAILY WISDOM", etc.
    default_hashtag: str         # "#shorts", "#trivia", "#quotes", etc.
    hashtags: list[str]
    lang_profile: Optional[LanguageProfile] = None


def detect_content_archetype(niche: Optional[str]) -> ContentArchetype:
    """Classify user niche into an archetype: code_quiz, trivia_quiz, or quote_card.
    
    Owner and standard python niches always resolve to 'code_quiz' with Python profile.
    """
    if not niche:
        py_prof = LANG_PROFILES["python"]
        return ContentArchetype(
            archetype="code_quiz",
            category="coding",
            header_title=py_prof.header_badge,
            default_hashtag=py_prof.default_hashtag,
            hashtags=["#python", "#coding", "#programming", "#shorts", "#pythonquiz"],
            lang_profile=py_prof
        )

    n_lower = niche.strip().lower()

    # 1. Quotes / Stoicism / Motivation
    if any(k in n_lower for k in ["quote", "quotes", "motivat", "stoic", "philosophy", "wisdom", "inspiration", "life lesson"]):
        title_badge = "STOIC WISDOM" if "stoic" in n_lower else ("MOTIVATION" if "motivat" in n_lower else "DAILY QUOTE")
        return ContentArchetype(
            archetype="quote_card",
            category="quotes",
            header_title=title_badge,
            default_hashtag="#quotes",
            hashtags=["#quotes", "#motivation", "#wisdom", "#inspiration", "#shorts"],
            lang_profile=None
        )

    # 2. General Trivia / Riddles / GK (when not explicitly coding)
    is_coding = any(k in n_lower for k in [
        "python", "c program", "c++", "cpp", "javascript", "java", "golang", "go program",
        "rust", "code", "coding", "syntax", "program", "developer", "software", "sql", "html"
    ])

    if not is_coding and any(k in n_lower for k in [
        "trivia", "gk", "general knowledge", "riddle", "riddles", "puzzle", "puzzles",
        "science", "history", "geography", "movie", "quiz", "brain teaser", "guess", "fun fact"
    ]):
        badge = "RIDDLE CHALLENGE" if "riddle" in n_lower else ("GK QUIZ" if "gk" in n_lower else "TRIVIA QUIZ")
        return ContentArchetype(
            archetype="trivia_quiz",
            category="trivia",
            header_title=badge,
            default_hashtag="#trivia",
            hashtags=["#trivia", "#quiz", "#generalknowledge", "#riddles", "#shorts", "#brainteaser"],
            lang_profile=None
        )

    # 3. Code Quiz (Python, C, C++, Java, JS, etc.)
    lang_prof = detect_language_from_niche(niche)
    return ContentArchetype(
        archetype="code_quiz",
        category="coding",
        header_title=lang_prof.header_badge,
        default_hashtag=lang_prof.default_hashtag,
        hashtags=[lang_prof.default_hashtag, "#coding", "#programming", "#shorts", f"#{lang_prof.slug}quiz"],
        lang_profile=lang_prof
    )


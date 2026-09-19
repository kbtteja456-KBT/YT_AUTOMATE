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

    n_lower = re.sub(r"\s+", " ", niche.strip().lower())

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



class SpokenLanguageProfile(NamedTuple):
    code: str                # "te", "hi", "ta", "kn", "ml", "bn", "mr", "gu", "es", "fr", "de", "ja", "en"
    name: str                # "Telugu", "Hindi", "Tamil", etc.
    native_name: str         # "తెలుగు", "हिन्दी", "தமிழ்", etc.
    default_voice_id: str    # "te-IN-MohanNeural", "hi-IN-MadhurNeural", etc.
    font_name: str           # "Nirmala UI" or "Impact"


SPOKEN_LANG_PROFILES: dict[str, SpokenLanguageProfile] = {
    "te": SpokenLanguageProfile("te", "Telugu", "తెలుగు", "te-IN-MohanNeural", "Nirmala UI"),
    "hi": SpokenLanguageProfile("hi", "Hindi", "हिन्दी", "hi-IN-MadhurNeural", "Nirmala UI"),
    "ta": SpokenLanguageProfile("ta", "Tamil", "தமிழ்", "ta-IN-ValluvarNeural", "Nirmala UI"),
    "kn": SpokenLanguageProfile("kn", "Kannada", "ಕನ್ನಡ", "kn-IN-GaganNeural", "Nirmala UI"),
    "ml": SpokenLanguageProfile("ml", "Malayalam", "മലയാളം", "ml-IN-MidhunNeural", "Nirmala UI"),
    "bn": SpokenLanguageProfile("bn", "Bengali", "বাংলা", "bn-IN-BashkarNeural", "Nirmala UI"),
    "mr": SpokenLanguageProfile("mr", "Marathi", "मराठी", "mr-IN-ManoharNeural", "Nirmala UI"),
    "gu": SpokenLanguageProfile("gu", "Gujarati", "ગુજરાતી", "gu-IN-NiranjanNeural", "Nirmala UI"),
    "ur": SpokenLanguageProfile("ur", "Urdu", "اردو", "ur-IN-SalmanNeural", "Segoe UI"),
    "es": SpokenLanguageProfile("es", "Spanish", "Español", "es-ES-AlvaroNeural", "Impact"),
    "fr": SpokenLanguageProfile("fr", "French", "Français", "fr-FR-HenriNeural", "Impact"),
    "de": SpokenLanguageProfile("de", "German", "Deutsch", "de-DE-ConradNeural", "Impact"),
    "ja": SpokenLanguageProfile("ja", "Japanese", "日本語", "ja-JP-KeitaNeural", "MS Gothic"),
    "en": SpokenLanguageProfile("en", "English", "English", "en-US-ChristopherNeural", "Impact"),
}


def detect_spoken_language(text: Optional[str]) -> SpokenLanguageProfile:
    """Automatically detect target spoken language and neural TTS voice from content/prompt.
    
    Checks native script Unicode blocks and explicit language keywords. Defaults to English.
    """
    if not text:
        return SPOKEN_LANG_PROFILES["en"]

    # 1. Check Native Script Unicode Blocks
    if re.search(r"[\u0C00-\u0C7F]", text):
        return SPOKEN_LANG_PROFILES["te"]
    if re.search(r"[\u0B80-\u0BFF]", text):
        return SPOKEN_LANG_PROFILES["ta"]
    if re.search(r"[\u0C80-\u0CFF]", text):
        return SPOKEN_LANG_PROFILES["kn"]
    if re.search(r"[\u0D00-\u0D7F]", text):
        return SPOKEN_LANG_PROFILES["ml"]
    if re.search(r"[\u0980-\u09FF]", text):
        return SPOKEN_LANG_PROFILES["bn"]
    if re.search(r"[\u0A80-\u0AFF]", text):
        return SPOKEN_LANG_PROFILES["gu"]
    if re.search(r"[\u0900-\u097F]", text):
        return SPOKEN_LANG_PROFILES["hi"]
    if re.search(r"[\u3040-\u30FF\u4E00-\u9FFF]", text):
        return SPOKEN_LANG_PROFILES["ja"]

    # 2. Check Explicit Keyword Mentions (e.g., 'in telugu audio', 'telugu news', 'hindi facts')
    t_lower = text.strip().lower()
    if re.search(r"\b(?:telugu|telugulo)\b", t_lower):
        return SPOKEN_LANG_PROFILES["te"]
    if re.search(r"\b(?:hindi|hindimein)\b", t_lower):
        return SPOKEN_LANG_PROFILES["hi"]
    if re.search(r"\b(?:tamil|tamizh)\b", t_lower):
        return SPOKEN_LANG_PROFILES["ta"]
    if re.search(r"\b(?:kannada)\b", t_lower):
        return SPOKEN_LANG_PROFILES["kn"]
    if re.search(r"\b(?:malayalam)\b", t_lower):
        return SPOKEN_LANG_PROFILES["ml"]
    if re.search(r"\b(?:bengali|bangla)\b", t_lower):
        return SPOKEN_LANG_PROFILES["bn"]
    if re.search(r"\b(?:marathi)\b", t_lower):
        return SPOKEN_LANG_PROFILES["mr"]
    if re.search(r"\b(?:gujarati)\b", t_lower):
        return SPOKEN_LANG_PROFILES["gu"]
    if re.search(r"\b(?:urdu)\b", t_lower):
        return SPOKEN_LANG_PROFILES["ur"]
    if re.search(r"\b(?:spanish|espanol|español)\b", t_lower):
        return SPOKEN_LANG_PROFILES["es"]
    if re.search(r"\b(?:french|francais|français)\b", t_lower):
        return SPOKEN_LANG_PROFILES["fr"]
    if re.search(r"\b(?:german|deutsch)\b", t_lower):
        return SPOKEN_LANG_PROFILES["de"]
    if re.search(r"\b(?:japanese|nihongo)\b", t_lower):
        return SPOKEN_LANG_PROFILES["ja"]

    return SPOKEN_LANG_PROFILES["en"]


class ContentArchetype(NamedTuple):
    archetype: str               # "code_quiz", "trivia_quiz", "quote_card"
    category: str                # "coding", "trivia", "quotes"
    header_title: str            # "PYTHON QUIZ", "TRIVIA QUIZ", "DAILY WISDOM", etc.
    default_hashtag: str         # "#shorts", "#trivia", "#quotes", etc.
    hashtags: list[str]
    lang_profile: Optional[LanguageProfile] = None
    spoken_lang: Optional[SpokenLanguageProfile] = None


def detect_content_archetype(niche: Optional[str]) -> ContentArchetype:
    """Classify user niche into an archetype: code_quiz, trivia_quiz, or quote_card.
    
    Owner and standard python niches always resolve to 'code_quiz' with Python profile.
    """
    spoken_lang = detect_spoken_language(niche)

    if not niche:
        py_prof = LANG_PROFILES["python"]
        return ContentArchetype(
            archetype="code_quiz",
            category="coding",
            header_title=py_prof.header_badge,
            default_hashtag=py_prof.default_hashtag,
            hashtags=["#python", "#coding", "#programming", "#shorts", "#pythonquiz"],
            lang_profile=py_prof,
            spoken_lang=spoken_lang
        )

    n_lower = re.sub(r"\s+", " ", niche.strip().lower())

    # 1. Quotes / Stoicism / Motivation
    if any(k in n_lower for k in ["quote", "quotes", "motivat", "stoic", "philosophy", "wisdom", "inspiration", "life lesson"]):
        title_badge = "STOIC WISDOM" if "stoic" in n_lower else ("MOTIVATION" if "motivat" in n_lower else "DAILY QUOTE")
        return ContentArchetype(
            archetype="quote_card",
            category="quotes",
            header_title=title_badge,
            default_hashtag="#quotes",
            hashtags=["#quotes", "#motivation", "#wisdom", "#inspiration", "#shorts"],
            lang_profile=None,
            spoken_lang=spoken_lang
        )

    # 2. Explicit Code Quiz (must be a quiz, challenge, puzzle, or output question)
    is_long_content = len(n_lower.split()) > 7
    is_quiz_intent = any(k in n_lower for k in [
        "quiz", "challenge", "puzzle", "output", "what is the output", "what's the output",
        "question card", "syntax trap", "mcq", "trick question"
    ])
    is_explicit_coding_lang = any(k in n_lower for k in [
        "python", "c program", "c language", "c lang", "c++", "cpp", "javascript", "java", "golang", "go program", "rust"
    ]) or bool(re.search(r"\bc\s*(?:language|lang|program|programming|pointer|code|quiz)\b", n_lower))

    is_explicit_coding = (
        (is_explicit_coding_lang and (not is_long_content or is_quiz_intent))
        or (is_quiz_intent and ("code" in n_lower or "programming" in n_lower or is_explicit_coding_lang))
    )

    if is_explicit_coding:
        lang_prof = detect_language_from_niche(niche)
        return ContentArchetype(
            archetype="code_quiz",
            category="coding",
            header_title=lang_prof.header_badge,
            default_hashtag=lang_prof.default_hashtag,
            hashtags=[lang_prof.default_hashtag, "#coding", "#programming", "#shorts", f"#{lang_prof.slug}quiz"],
            lang_profile=lang_prof,
            spoken_lang=spoken_lang
        )

    # 3. General Trivia / Riddles / GK / Non-Coding Quizzes
    if any(k in n_lower for k in ["trivia", "gk", "general knowledge", "riddle", "riddles", "brain teaser", "guess", "fun fact", "quiz"]):
        badge = "RIDDLE CHALLENGE" if "riddle" in n_lower else ("GK QUIZ" if "gk" in n_lower else "TRIVIA QUIZ")
        return ContentArchetype(
            archetype="trivia_quiz",
            category="trivia",
            header_title=badge,
            default_hashtag="#trivia",
            hashtags=["#trivia", "#quiz", "#generalknowledge", "#riddles", "#shorts", "#brainteaser"],
            lang_profile=None,
            spoken_lang=spoken_lang
        )

    # 4. Universal Documentary & News (Tech News, AI Breakthroughs, Science, History, Informational, Daily Info)
    # Uses real 1080x1920 stock video footage (Pexels/Pixabay), cinematic motion, voiceover, and captions
    is_news = any(k in n_lower for k in ["news", "update", "latest", "informational", "discovery", "breakthrough", "current", "daily info"])
    topic_header = "DAILY NEWS" if is_news else "FACTS & INSIGHTS"
    return ContentArchetype(
        archetype="documentary_cinematic",
        category="documentary",
        header_title=topic_header,
        default_hashtag="#shorts",
        hashtags=["#shorts", "#news", "#facts", "#dailyinfo", "#trending"],
        lang_profile=None,
        spoken_lang=spoken_lang
    )


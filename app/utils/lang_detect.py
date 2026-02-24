from lingua import Language, LanguageDetectorBuilder

languages = [
    Language.ENGLISH,
    Language.HINDI,
    Language.MARATHI
]

detector = LanguageDetectorBuilder.from_languages(*languages).build()

def detect_lang(text: str) -> str:
    lang = detector.detect_language_of(text)
    return lang.iso_code_639_1.name.lower() if lang else "en"
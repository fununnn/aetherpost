"""Internationalization support for AetherPost."""

import os
import json
from pathlib import Path
from typing import Dict, Optional

# Default language
DEFAULT_LANGUAGE = "en"

# Current language (can be set via environment variable)
CURRENT_LANGUAGE = os.getenv("AUTOPROMO_LANG", DEFAULT_LANGUAGE)

# Cache for loaded translations
_translations_cache: Dict[str, Dict[str, str]] = {}


def get_translations_dir() -> Path:
    """Get the translations directory path."""
    return Path(__file__).parent / "locales"


def load_translations(language: str) -> Dict[str, str]:
    """Load translations for a specific language."""
    if language in _translations_cache:
        return _translations_cache[language]
    
    translations_file = get_translations_dir() / f"{language}.json"
    
    if not translations_file.exists():
        # Fallback to English if language not found
        if language != DEFAULT_LANGUAGE:
            return load_translations(DEFAULT_LANGUAGE)
        return {}
    
    try:
        with open(translations_file, 'r', encoding='utf-8') as f:
            translations = json.load(f)
            _translations_cache[language] = translations
            return translations
    except Exception:
        return {}


def _(key: str, language: Optional[str] = None, **kwargs) -> str:
    """Translate a key to the current or specified language."""
    lang = language or CURRENT_LANGUAGE
    translations = load_translations(lang)
    
    # Get the translation
    text = translations.get(key, key)
    
    # Format with provided arguments
    if kwargs:
        try:
            text = text.format(**kwargs)
        except (KeyError, ValueError):
            pass  # Return unformatted text if formatting fails
    
    return text


def set_language(language: str):
    """Set the current language."""
    global CURRENT_LANGUAGE
    CURRENT_LANGUAGE = language


def get_available_languages() -> list:
    """Get list of available languages."""
    translations_dir = get_translations_dir()
    if not translations_dir.exists():
        return [DEFAULT_LANGUAGE]
    
    languages = []
    for file in translations_dir.glob("*.json"):
        languages.append(file.stem)
    
    return sorted(languages)


def get_language_info() -> Dict[str, str]:
    """Get information about available languages."""
    return {
        "en": "English",
        "ja": "日本語 (Japanese)",
        "es": "Español (Spanish)",
        "fr": "Français (French)",
        "de": "Deutsch (German)",
        "zh": "中文 (Chinese)",
        "ko": "한국어 (Korean)",
        "pt": "Português (Portuguese)",
        "it": "Italiano (Italian)",
        "ru": "Русский (Russian)"
    }
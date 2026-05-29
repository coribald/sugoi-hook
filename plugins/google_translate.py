import os
import sys
from pathlib import Path
from typing import Optional

from plugins import TextractorPlugin


def get_runtime_translator_dir(app=None) -> Path:
    """Resolve the bundled Translator directory for both source and packaged runs."""
    if app is not None:
        base_path = getattr(app, 'base_path', None)
        if base_path:
            return Path(base_path) / 'Translator'
    return Path(__file__).resolve().parent.parent / 'Translator'


def import_google_translator(app=None):
    """Import GoogleTranslator after wiring the bundled Translator folder onto sys.path."""
    translator_dir = get_runtime_translator_dir(app)
    translator_dir_str = str(translator_dir)
    if translator_dir_str not in sys.path:
        sys.path.insert(0, translator_dir_str)

    deep_translator_dir = translator_dir / 'deep_translator'
    deep_translator_dir_str = str(deep_translator_dir)
    if deep_translator_dir_str not in sys.path:
        sys.path.insert(0, deep_translator_dir_str)

    from deep_translator import GoogleTranslator  # type: ignore
    return GoogleTranslator


class GoogleTranslatePlugin(TextractorPlugin):
    name = "Google Translate"
    description = "Translates text using Google Translate."
    version = "1.3"
    author = "Cline"
    is_translation_plugin = True

    LANGUAGES = {
        'auto': 'Auto-detect',
        'en': 'English',
        'ja': 'Japanese',
        'zh-CN': 'Chinese (Simplified)',
        'zh-TW': 'Chinese (Traditional)',
        'ko': 'Korean',
        'es': 'Spanish',
        'fr': 'French',
        'de': 'German',
        'ru': 'Russian',
        'it': 'Italian',
        'pt': 'Portuguese',
        'ar': 'Arabic',
        'hi': 'Hindi',
        'th': 'Thai',
        'vi': 'Vietnamese',
        'id': 'Indonesian',
        'tr': 'Turkish',
        'pl': 'Polish',
        'nl': 'Dutch',
        'sv': 'Swedish',
        'da': 'Danish',
        'no': 'Norwegian',
        'fi': 'Finnish',
    }

    def __init__(self):
        super().__init__()
        self.translator = None
        self.google_translator_class = None
        self.target_lang = 'en'
        self.source_lang = 'auto'

    def on_enable(self):
        if not self.google_translator_class:
            try:
                self.google_translator_class = import_google_translator(getattr(self, 'app', None))
            except Exception:
                self.google_translator_class = None
                return

        if not self.translator:
            try:
                self.translator = self.google_translator_class(source=self.source_lang, target=self.target_lang)
            except Exception:
                self.translator = None
                return

    def process_text(self, text: str) -> str:
        if not text or not text.strip():
            return text

        stripped_text = text.strip()

        if stripped_text.startswith('[Hook ') or stripped_text.startswith('[Hook #'):
            return text

        system_keywords = (
            'Selected Hook', 'Attached to', 'Detached', 'Waiting for',
            'Function:', 'Manual hook', 'Process Name', 'PID:',
            'Interact with', 'Hook at', 'Console'
        )

        if any(keyword in stripped_text for keyword in system_keywords):
            return text

        if stripped_text and stripped_text[0] in '✓●○🎮🎯🔌📝⏳🔗⏹️🗑️💾🔄📂🔽':
            return text

        if stripped_text.startswith('[Console]'):
            return text

        if len(stripped_text) > 3:
            separator_chars = '─═━-_'
            separator_count = sum(1 for c in stripped_text if c in separator_chars)
            if separator_count / len(stripped_text) > 0.8:
                return text

        if self.enabled and self.translator:
            try:
                translated = self.translate_text(text)
                if translated:
                    return f"{text.rstrip()}\n{translated}\n\n"
            except Exception:
                pass

        return text

    def process_clipboard_text(self, text: str) -> str:
        """Keep clipboard text untranslated while other cleanup plugins run."""
        return text

    def translate_text(self, text: str) -> Optional[str]:
        if not self.enabled or not self.translator:
            return None

        try:
            translated = self.translator.translate(text)
            if translated:
                return translated.strip()
        except Exception:
            return None

        return None

    def get_settings(self) -> dict:
        target_languages = {k: v for k, v in self.LANGUAGES.items() if k != 'auto'}

        return {
            'source_lang': (
                self.source_lang,
                'choice',
                'Source Language',
                self.LANGUAGES
            ),
            'target_lang': (
                self.target_lang,
                'choice',
                'Target Language',
                target_languages
            )
        }

    def set_setting(self, name: str, value) -> bool:
        if name == 'source_lang':
            if value in self.LANGUAGES or value == 'auto':
                self.source_lang = value
                self._recreate_translator()
                return True
        elif name == 'target_lang':
            if value in self.LANGUAGES and value != 'auto':
                self.target_lang = value
                self._recreate_translator()
                return True
        return False

    def _recreate_translator(self):
        if self.google_translator_class and self.enabled:
            try:
                self.translator = self.google_translator_class(source=self.source_lang, target=self.target_lang)
            except Exception:
                self.translator = None


plugin = GoogleTranslatePlugin()

import logging
import os
import sys
from pathlib import Path
from typing import Optional

from plugins import HookPlugin


def runtime_debug_logging_enabled() -> bool:
    env_enabled = os.environ.get('SUGOIHOOK_DEBUG_LOGGING', '').strip().lower() in {'1', 'true', 'yes', 'on'}
    argv_enabled = any(str(arg).strip().lower() == '--debug' for arg in sys.argv[1:])
    return env_enabled or argv_enabled


def get_runtime_translator_dir(app=None) -> Path:
    """Resolve the bundled deep_translator package directory for source and packaged runs."""
    if app is not None:
        base_path = getattr(app, 'base_path', None)
        if base_path:
            return Path(base_path) / 'deep_translator'
    return Path(__file__).resolve().parent.parent / 'deep_translator'


def import_deep_translator_classes(app=None):
    """Import supported deep_translator classes after wiring the vendored package onto sys.path."""
    translator_dir = get_runtime_translator_dir(app)
    package_parent = str(translator_dir.parent)
    if package_parent not in sys.path:
        sys.path.insert(0, package_parent)

    from deep_translator import (  # type: ignore
        BaiduTranslator,
        DeeplTranslator,
        GoogleTranslator,
        LibreTranslator,
        MicrosoftTranslator,
        MyMemoryTranslator,
        PapagoTranslator,
        QcriTranslator,
        TencentTranslator,
        YandexTranslator,
    )

    return {
        'google': GoogleTranslator,
        'mymemory': MyMemoryTranslator,
        'libre': LibreTranslator,
        'deepl': DeeplTranslator,
        'microsoft': MicrosoftTranslator,
        'papago': PapagoTranslator,
        'qcri': QcriTranslator,
        'baidu': BaiduTranslator,
        'tencent': TencentTranslator,
        'yandex': YandexTranslator,
    }


class DeepTranslatorPlugin(HookPlugin):
    name = "Deep Translator"
    description = "Translates text using configurable deep_translator backends."
    version = "2.0"
    author = "Cline"
    is_translation_plugin = True

    PROVIDERS = {
        'google': 'Google (free web)',
        'mymemory': 'MyMemory (free web)',
        'libre': 'LibreTranslate (API key)',
        'deepl': 'DeepL (API key)',
        'microsoft': 'Microsoft Translator (API key)',
        'papago': 'Papago (client id/secret)',
        'qcri': 'QCRI (API key)',
        'baidu': 'Baidu (appid/appkey)',
        'tencent': 'Tencent (secret id/key)',
        'yandex': 'Yandex (API key)',
    }

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
        self.provider_classes = None
        self.provider = 'google'
        self.target_lang = 'en'
        self.source_lang = 'auto'
        self.mymemory_email = ''
        self.libre_api_key = ''
        self.libre_use_free_api = True
        self.libre_custom_url = ''
        self.deepl_api_key = ''
        self.deepl_use_free_api = True
        self.microsoft_api_key = ''
        self.microsoft_region = ''
        self.papago_client_id = ''
        self.papago_secret_key = ''
        self.qcri_api_key = ''
        self.baidu_appid = ''
        self.baidu_appkey = ''
        self.tencent_secret_id = ''
        self.tencent_secret_key = ''
        self.yandex_api_key = ''
        self.last_error = ''

    def _log_debug(self, stage: str, **fields):
        if not runtime_debug_logging_enabled():
            return
        try:
            parts = []
            for key, value in fields.items():
                value_str = str(value).replace("\r", "\\r").replace("\n", "\\n")
                if len(value_str) > 160:
                    value_str = value_str[:160] + "..."
                parts.append(f"{key}={value_str}")
            message = f"[{self.name}] {stage}"
            if parts:
                message += " | " + " | ".join(parts)
            logging.info(message)
            try:
                print(message, flush=True)
            except Exception:
                pass
        except Exception:
            pass

    def on_enable(self):
        if not self.provider_classes:
            try:
                self.provider_classes = import_deep_translator_classes(getattr(self, 'app', None))
                self._log_debug('provider_classes_loaded', providers=list(self.provider_classes.keys()))
            except Exception as exc:
                self.provider_classes = None
                self.last_error = str(exc)
                self._log_debug('provider_classes_failed', error=exc)
                return

        self._recreate_translator()

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
            except Exception as exc:
                self._log_debug('process_text.translate_failed', provider=self.provider, error=exc)

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
        except Exception as exc:
            self.last_error = str(exc)
            self._log_debug('translate_failed', provider=self.provider, error=exc)
            return None

        return None

    def _draft_or_attr(self, values: Optional[dict], name: str):
        if values and name in values:
            return values[name]
        return getattr(self, name)

    def get_settings_for_values(self, values: Optional[dict] = None) -> dict:
        provider = self._draft_or_attr(values, 'provider')
        target_languages = {k: v for k, v in self.LANGUAGES.items() if k != 'auto'}
        settings = {
            'provider': (
                provider,
                'choice',
                'Deep Translator provider',
                self.PROVIDERS
            ),
            'source_lang': (
                self._draft_or_attr(values, 'source_lang'),
                'choice',
                'Source Language',
                self.LANGUAGES
            ),
            'target_lang': (
                self._draft_or_attr(values, 'target_lang'),
                'choice',
                'Target Language',
                target_languages
            ),
        }

        provider_settings = {
            'mymemory': {
                'mymemory_email': (
                    self._draft_or_attr(values, 'mymemory_email'),
                    'str',
                    'MyMemory email (optional)'
                ),
            },
            'libre': {
                'libre_api_key': (
                    self._draft_or_attr(values, 'libre_api_key'),
                    'str',
                    'LibreTranslate API key'
                ),
                'libre_use_free_api': (
                    self._draft_or_attr(values, 'libre_use_free_api'),
                    'bool',
                    'LibreTranslate: use free endpoint'
                ),
                'libre_custom_url': (
                    self._draft_or_attr(values, 'libre_custom_url'),
                    'str',
                    'LibreTranslate custom URL (optional)'
                ),
            },
            'deepl': {
                'deepl_api_key': (
                    self._draft_or_attr(values, 'deepl_api_key'),
                    'str',
                    'DeepL API key'
                ),
                'deepl_use_free_api': (
                    self._draft_or_attr(values, 'deepl_use_free_api'),
                    'bool',
                    'DeepL: use free endpoint'
                ),
            },
            'microsoft': {
                'microsoft_api_key': (
                    self._draft_or_attr(values, 'microsoft_api_key'),
                    'str',
                    'Microsoft Translator API key'
                ),
                'microsoft_region': (
                    self._draft_or_attr(values, 'microsoft_region'),
                    'str',
                    'Microsoft Translator region (optional)'
                ),
            },
            'papago': {
                'papago_client_id': (
                    self._draft_or_attr(values, 'papago_client_id'),
                    'str',
                    'Papago client id'
                ),
                'papago_secret_key': (
                    self._draft_or_attr(values, 'papago_secret_key'),
                    'str',
                    'Papago secret key'
                ),
            },
            'qcri': {
                'qcri_api_key': (
                    self._draft_or_attr(values, 'qcri_api_key'),
                    'str',
                    'QCRI API key'
                ),
            },
            'baidu': {
                'baidu_appid': (
                    self._draft_or_attr(values, 'baidu_appid'),
                    'str',
                    'Baidu appid'
                ),
                'baidu_appkey': (
                    self._draft_or_attr(values, 'baidu_appkey'),
                    'str',
                    'Baidu appkey'
                ),
            },
            'tencent': {
                'tencent_secret_id': (
                    self._draft_or_attr(values, 'tencent_secret_id'),
                    'str',
                    'Tencent secret id'
                ),
                'tencent_secret_key': (
                    self._draft_or_attr(values, 'tencent_secret_key'),
                    'str',
                    'Tencent secret key'
                ),
            },
            'yandex': {
                'yandex_api_key': (
                    self._draft_or_attr(values, 'yandex_api_key'),
                    'str',
                    'Yandex API key'
                ),
            },
        }

        settings.update(provider_settings.get(provider, {}))
        return settings

    def get_settings(self) -> dict:
        return self.get_settings_for_values()

    def set_setting(self, name: str, value) -> bool:
        if name == 'provider':
            if value in self.PROVIDERS:
                self.provider = value
                self._recreate_translator()
                return True
            return False

        if name == 'source_lang':
            if value in self.LANGUAGES or value == 'auto':
                self.source_lang = value
                self._recreate_translator()
                return True
            return False

        if name == 'target_lang':
            if value in self.LANGUAGES and value != 'auto':
                self.target_lang = value
                self._recreate_translator()
                return True
            return False

        if name in {
            'mymemory_email',
            'libre_api_key',
            'libre_custom_url',
            'deepl_api_key',
            'microsoft_api_key',
            'microsoft_region',
            'papago_client_id',
            'papago_secret_key',
            'qcri_api_key',
            'baidu_appid',
            'baidu_appkey',
            'tencent_secret_id',
            'tencent_secret_key',
            'yandex_api_key',
        }:
            setattr(self, name, str(value).strip())
            self._recreate_translator()
            return True

        if name in {'libre_use_free_api', 'deepl_use_free_api'}:
            setattr(self, name, bool(value))
            self._recreate_translator()
            return True

        return False

    def _get_provider_kwargs(self) -> dict:
        if self.provider == 'google':
            return {
                'source': self.source_lang,
                'target': self.target_lang,
            }
        if self.provider == 'mymemory':
            kwargs = {
                'source': self.source_lang,
                'target': self.target_lang,
            }
            if self.mymemory_email:
                kwargs['email'] = self.mymemory_email
            return kwargs
        if self.provider == 'libre':
            kwargs = {
                'source': self.source_lang,
                'target': self.target_lang,
                'api_key': self.libre_api_key,
                'use_free_api': self.libre_use_free_api,
            }
            if self.libre_custom_url:
                kwargs['custom_url'] = self.libre_custom_url
            return kwargs
        if self.provider == 'deepl':
            return {
                'source': self.source_lang,
                'target': self.target_lang,
                'api_key': self.deepl_api_key,
                'use_free_api': self.deepl_use_free_api,
            }
        if self.provider == 'microsoft':
            kwargs = {
                'source': self.source_lang,
                'target': self.target_lang,
                'api_key': self.microsoft_api_key,
            }
            if self.microsoft_region:
                kwargs['region'] = self.microsoft_region
            return kwargs
        if self.provider == 'papago':
            return {
                'source': self.source_lang,
                'target': self.target_lang,
                'client_id': self.papago_client_id,
                'secret_key': self.papago_secret_key,
            }
        if self.provider == 'qcri':
            return {
                'source': self.source_lang,
                'target': self.target_lang,
                'api_key': self.qcri_api_key,
            }
        if self.provider == 'baidu':
            return {
                'source': self.source_lang,
                'target': self.target_lang,
                'appid': self.baidu_appid,
                'appkey': self.baidu_appkey,
            }
        if self.provider == 'tencent':
            return {
                'source': self.source_lang,
                'target': self.target_lang,
                'secret_id': self.tencent_secret_id,
                'secret_key': self.tencent_secret_key,
            }
        if self.provider == 'yandex':
            return {
                'source': self.source_lang,
                'target': self.target_lang,
                'api_key': self.yandex_api_key,
            }
        return {}

    def _recreate_translator(self):
        self.translator = None
        self.last_error = ''

        if not self.enabled:
            return

        if not self.provider_classes:
            try:
                self.provider_classes = import_deep_translator_classes(getattr(self, 'app', None))
            except Exception as exc:
                self.last_error = str(exc)
                self._log_debug('provider_classes_failed', error=exc)
                return

        translator_class = self.provider_classes.get(self.provider)
        if not translator_class:
            self.last_error = f'Unknown provider: {self.provider}'
            self._log_debug('provider_missing', provider=self.provider)
            return

        kwargs = self._get_provider_kwargs()
        try:
            self.translator = translator_class(**kwargs)
            self._log_debug('translator_ready', provider=self.provider, source=self.source_lang, target=self.target_lang)
        except Exception as exc:
            self.translator = None
            self.last_error = str(exc)
            self._log_debug('translator_init_failed', provider=self.provider, error=exc)


plugin = DeepTranslatorPlugin()

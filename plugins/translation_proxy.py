"""
Translator++ Translation Proxy Plugin
======================================

Translates text using Translator++ Translation Proxy which supports
more than 30 types of translation endpoints (DeepL, Google, etc.).

For more information: https://dreamsavior.net
"""

import requests
from plugins import HookPlugin
from typing import Optional
import logging

# ============================================================================
# CONFIGURATION - Modify these constants as needed
# ============================================================================
TARGET_LANGUAGE = ""  # Target language code (e.g., "EN", "DE", "FR", "ES", "JA", "ZH"). If blank will follow Translator++ settings.
SOURCE_LANGUAGE = ""  # Source language (use "auto" for auto-detection). If blank will follow Translator++ settings.
PROXY_URL = "http://127.0.0.1:8877/v2/translate"  # Translator++ proxy endpoint
REQUEST_TIMEOUT = 10  # Timeout in seconds for translation requests
# ============================================================================


def runtime_debug_logging_enabled() -> bool:
    import os
    import sys
    env_enabled = os.environ.get('SUGOIHOOK_DEBUG_LOGGING', '').strip().lower() in {'1', 'true', 'yes', 'on'}
    argv_enabled = any(str(arg).strip().lower() == '--debug' for arg in sys.argv[1:])
    return env_enabled or argv_enabled


class TranslatorPlusPlusPlugin(HookPlugin):
    """
    Translates using Translator++ Translation Proxy.
    
    This plugin sends text to a local Translator++ Translation Proxy server
    which supports various translation backends including DeepL, Google Translate,
    and more than 30 other translation services.
    """
    
    name = "Translator++ Proxy"
    description = "Translates using Translator++ Translation Proxy (30+ endpoints)"
    version = "1.0"
    author = "Dreamsavior (dreamsavior@gmail.com / dreamsavior.net)"
    is_translation_plugin = True
    
    def __init__(self):
        super().__init__()
        self._state['target_lang'] = TARGET_LANGUAGE
        self._state['source_lang'] = SOURCE_LANGUAGE
        self._state['proxy_url'] = PROXY_URL
        self._state['timeout'] = REQUEST_TIMEOUT
        self.session = None

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
        """Initialize the session when the plugin is enabled."""
        if self.session is None:
            self.session = requests.Session()
    
    def on_disable(self):
        """Clean up the session when the plugin is disabled."""
        if self.session:
            self.session.close()
            self.session = None
    
    def process_text(self, text: str) -> Optional[str]:
        """
        Translate the text using Translator++ Translation Proxy.
        
        Args:
            text: The text to translate
            
        Returns:
            The original text with translation appended, or original text if translation fails
        """
        self._log_debug('process_text.in', text=text)
        if not text or not text.strip():
            self._log_debug('process_text.out', output=text, reason='empty_passthrough')
            return text
        
        if not self.enabled:
            self._log_debug('process_text.out', output=text, reason='plugin_disabled')
            return text
        
        # Ensure session is initialized
        if self.session is None:
            self.on_enable()
        
        try:
            translated = self.translate_text(text)
            if translated:
                output = f"{text.rstrip()}\n{translated}\n\n"
                self._log_debug('process_text.out', output=output, reason='translated')
                return output
            self._log_debug('process_text.out', output=text, reason='no_translation')
            return text
        except Exception as exc:
            self._log_debug('process_text.error', error=exc, fallback='original_text')
            return text

    def process_clipboard_text(self, text: str) -> Optional[str]:
        """Keep clipboard text untranslated while other cleanup plugins run."""
        self._log_debug('process_clipboard_text.out', output=text, reason='clipboard_passthrough')
        return text

    def translate_text(self, text: str) -> Optional[str]:
        if not text or not text.strip() or not self.enabled:
            self._log_debug('translate_text.skip', reason='empty_or_disabled')
            return None

        if self.session is None:
            self.on_enable()

        payload = {
            "text": [text.strip()]
        }

        target_lang = str(self._state.get('target_lang', '') or '').strip()
        source_lang = str(self._state.get('source_lang', '') or '').strip()
        proxy_url = str(self._state.get('proxy_url', PROXY_URL) or PROXY_URL).strip()
        timeout = self._state.get('timeout', REQUEST_TIMEOUT)

        if target_lang:
            payload["target_lang"] = target_lang

        if source_lang and source_lang.lower() != "auto":
            payload["source_lang"] = source_lang

        self._log_debug(
            'translate_text.request',
            proxy_url=proxy_url,
            timeout=timeout,
            target_lang=target_lang or '<follow_translatorpp>',
            source_lang=source_lang or '<follow_translatorpp>',
            text=text.strip()
        )

        try:
            response = self.session.post(
                proxy_url,
                json=payload,
                timeout=timeout,
                headers={"Content-Type": "application/json"}
            )

            self._log_debug('translate_text.response', status_code=response.status_code)

            if response.status_code == 200:
                result = response.json()
                if "translations" in result and len(result["translations"]) > 0:
                    translated = result["translations"][0].get("text", "")
                    if translated:
                        self._log_debug('translate_text.success', translated=translated.strip())
                        return translated.strip()
                self._log_debug('translate_text.empty', reason='missing_translations_field_or_empty')
            else:
                self._log_debug(
                    'translate_text.http_error',
                    status_code=response.status_code,
                    response_text=response.text
                )
        except requests.exceptions.Timeout:
            self._log_debug('translate_text.error', reason='timeout')
            return None
        except requests.exceptions.ConnectionError:
            self._log_debug('translate_text.error', reason='connection_error')
            return None
        except Exception as exc:
            self._log_debug('translate_text.error', reason='unexpected_exception', error=exc)
            return None

        return None
    
    def reset(self):
        """Reset the plugin state."""
        # Close and recreate session
        if self.session:
            self.session.close()
            self.session = None

    def get_settings(self) -> dict:
        return {
            'proxy_url': (
                self._state['proxy_url'],
                'str',
                'Translator++ proxy URL'
            ),
            'timeout': (
                self._state['timeout'],
                'int',
                'Request timeout in seconds'
            ),
            'source_lang': (
                self._state['source_lang'],
                'str',
                'Source language code (blank or auto follows Translator++ settings)'
            ),
            'target_lang': (
                self._state['target_lang'],
                'str',
                'Target language code (blank follows Translator++ settings)'
            )
        }

    def set_setting(self, name: str, value) -> bool:
        if name == 'proxy_url':
            value_str = str(value).strip()
            if value_str:
                self._state['proxy_url'] = value_str
                return True
            return False

        if name == 'timeout':
            try:
                new_value = int(value)
                if new_value >= 1:
                    self._state['timeout'] = new_value
                    return True
            except (ValueError, TypeError):
                pass
            return False

        if name == 'source_lang':
            self._state['source_lang'] = str(value).strip()
            return True

        if name == 'target_lang':
            self._state['target_lang'] = str(value).strip()
            return True

        return False


# Plugin instance for discovery
plugin = TranslatorPlusPlusPlugin()

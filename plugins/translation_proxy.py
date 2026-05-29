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

# ============================================================================
# CONFIGURATION - Modify these constants as needed
# ============================================================================
TARGET_LANGUAGE = ""  # Target language code (e.g., "EN", "DE", "FR", "ES", "JA", "ZH"). If blank will follow Translator++ settings.
SOURCE_LANGUAGE = ""  # Source language (use "auto" for auto-detection). If blank will follow Translator++ settings.
PROXY_URL = "http://127.0.0.1:8877/v2/translate"  # Translator++ proxy endpoint
REQUEST_TIMEOUT = 10  # Timeout in seconds for translation requests
# ============================================================================


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
        self.target_lang = TARGET_LANGUAGE
        self.source_lang = SOURCE_LANGUAGE
        self.proxy_url = PROXY_URL
        self.timeout = REQUEST_TIMEOUT
        self.session = None
    
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
        if not text or not text.strip():
            return text
        
        if not self.enabled:
            return text
        
        # Ensure session is initialized
        if self.session is None:
            self.on_enable()
        
        try:
            translated = self.translate_text(text)
            if translated:
                return f"{text.rstrip()}\n{translated}\n\n"
            return text
        except Exception:
            return text

    def process_clipboard_text(self, text: str) -> Optional[str]:
        """Keep clipboard text untranslated while other cleanup plugins run."""
        return text

    def translate_text(self, text: str) -> Optional[str]:
        if not text or not text.strip() or not self.enabled:
            return None

        if self.session is None:
            self.on_enable()

        payload = {
            "text": [text.strip()],
            "target_lang": self.target_lang
        }

        if self.source_lang and self.source_lang.lower() != "auto":
            payload["source_lang"] = self.source_lang

        try:
            response = self.session.post(
                self.proxy_url,
                json=payload,
                timeout=self.timeout,
                headers={"Content-Type": "application/json"}
            )

            if response.status_code == 200:
                result = response.json()
                if "translations" in result and len(result["translations"]) > 0:
                    translated = result["translations"][0].get("text", "")
                    if translated:
                        return translated.strip()
        except requests.exceptions.Timeout:
            return None
        except requests.exceptions.ConnectionError:
            return None
        except Exception:
            return None

        return None
    
    def reset(self):
        """Reset the plugin state."""
        # Close and recreate session
        if self.session:
            self.session.close()
            self.session = None


# Plugin instance for discovery
plugin = TranslatorPlusPlusPlugin()

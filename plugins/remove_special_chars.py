"""
Remove Special Characters Plugin
================================

Filters out text that consists only of special characters,
symbols, or repeated decorative patterns.
"""

import re
from plugins import HookPlugin
from typing import Optional
import logging


def runtime_debug_logging_enabled() -> bool:
    import os
    import sys
    env_enabled = os.environ.get('SUGOIHOOK_DEBUG_LOGGING', '').strip().lower() in {'1', 'true', 'yes', 'on'}
    argv_enabled = any(str(arg).strip().lower() == '--debug' for arg in sys.argv[1:])
    return env_enabled or argv_enabled


class RemoveSpecialCharsPlugin(HookPlugin):
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
    """
    Filters out text that consists only of special characters.
    
    This plugin detects and filters:
    - Text made up entirely of punctuation/symbols
    - Decorative lines (e.g., "----", "====", "****")
    - Repeated decorative symbol runs (e.g., "-----", "~~~~~")
    """
    
    name = "Remove Special Characters"
    description = "Filters out text consisting only of decorative symbols or punctuation"
    version = "1.0"
    author = "Sugoi Hook"
    
    def __init__(self):
        super().__init__()
        # Pattern for text that is only special characters/symbols
        self._special_char_pattern = re.compile(
            r'^[\s\-_=+*#@!~`\[\]{}()|\\/<>.,;:\'\"^&%$！？。、・…—ー〜「」『』（）［］【】《》〈〉〔〕]+$'
        )
        # Pattern for same decorative symbol repeated 5+ times
        self._repeated_symbol_pattern = re.compile(r'^([\-_=+*#@!~.`^|\\/<>！？。、・…—ー〜])\1{4,}$')
        # Pattern for decorative lines (mixed repeated chars)
        self._decorative_pattern = re.compile(r'^[\-_=\~*#.@!…—ー〜]{3,}$')
    
    def process_text(self, text: str) -> Optional[str]:
        """
        Check if text is only special characters and filter if so.
        
        Args:
            text: The text to check
            
        Returns:
            The original text if it contains meaningful content, None otherwise
        """
        self._log_debug('process_text.in', text=text)
        text_clean = text.strip()
        
        if not text_clean:
            self._log_debug('process_text.out', output=text, reason='empty_passthrough')
            return text  # Let empty text pass through (other plugins can handle it)
        
        # Check if text consists only of special characters/symbols
        if self._special_char_pattern.match(text_clean):
            self._log_debug('process_text.drop', reason='special_char_only', cleaned=text_clean, output=None)
            return None
        
        # Check if text is same decorative symbol repeated many times
        if self._repeated_symbol_pattern.match(text_clean):
            self._log_debug('process_text.drop', reason='repeated_symbol_run', cleaned=text_clean, output=None)
            return None
        
        # Check if text is a decorative line
        if self._decorative_pattern.match(text_clean):
            self._log_debug('process_text.drop', reason='decorative_line', cleaned=text_clean, output=None)
            return None
        
        self._log_debug('process_text.out', output=text, reason='pass')
        return text
    
    def reset(self):
        """No state to reset for this plugin."""
        pass


# Plugin instance for discovery
plugin = RemoveSpecialCharsPlugin()

"""
Minimum Length Filter Plugin
============================

Filters out empty or short text based on a minimum length threshold.
"""

from plugins import HookPlugin
from typing import Optional
import logging


def runtime_debug_logging_enabled() -> bool:
    import os
    import sys
    env_enabled = os.environ.get('SUGOIHOOK_DEBUG_LOGGING', '').strip().lower() in {'1', 'true', 'yes', 'on'}
    argv_enabled = any(str(arg).strip().lower() == '--debug' for arg in sys.argv[1:])
    return env_enabled or argv_enabled


class MinLengthFilterPlugin(HookPlugin):
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
    Filters out empty or short text.
    
    This plugin filters text based on character count (excluding whitespace).
    Useful for filtering out empty lines, single characters, short fragments,
    or other noise.
    """
    
    name = "Minimum Length Filter"
    description = "Filters out empty or short text using a minimum length threshold"
    version = "1.0"
    author = "Sugoi Hook"
    
    def __init__(self):
        super().__init__()
        self._state['min_length'] = 1  # Default minimum length; 1 removes empty lines only
    
    def process_text(self, text: str) -> Optional[str]:
        """
        Check if text meets minimum length requirement.
        
        Args:
            text: The text to check
            
        Returns:
            The original text if it meets the minimum length, None otherwise
        """
        self._log_debug('process_text.in', text=text)
        text_clean = text.strip()
        
        if not text_clean:
            self._log_debug(
                'process_text.drop',
                reason='empty_or_whitespace',
                min_length=self._state['min_length'],
                output=None
            )
            return None
        
        # Count actual characters (excluding whitespace)
        char_count = len(''.join(text_clean.split()))
        
        if char_count < self._state['min_length']:
            self._log_debug(
                'process_text.drop',
                reason='below_min_length',
                char_count=char_count,
                min_length=self._state['min_length'],
                output=None
            )
            return None
        
        self._log_debug(
            'process_text.pass',
            char_count=char_count,
            min_length=self._state['min_length'],
            output=text
        )
        return text
    
    def reset(self):
        """Reset plugin state (keep min_length setting)."""
        min_length = self._state.get('min_length', 3)
        self._state = {'min_length': min_length}
    
    def get_settings(self) -> dict:
        """Get plugin settings."""
        return {
                'min_length': (
                    self._state['min_length'],
                    'int',
                    'Minimum number of non-whitespace characters required (1 removes empty lines only)'
                )
            }
    
    def set_setting(self, name: str, value) -> bool:
        """Set a plugin setting."""
        if name == 'min_length':
            try:
                new_value = int(value)
                if new_value >= 1:
                    self._state['min_length'] = new_value
                    return True
            except (ValueError, TypeError):
                pass
        return False


# Plugin instance for discovery
plugin = MinLengthFilterPlugin()

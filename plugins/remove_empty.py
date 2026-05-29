"""
Remove Empty Lines Plugin
=========================

Filters out empty or whitespace-only text.
"""

from plugins import HookPlugin


def runtime_debug_logging_enabled() -> bool:
    import os
    import sys
    env_enabled = os.environ.get('SUGOIHOOK_DEBUG_LOGGING', '').strip().lower() in {'1', 'true', 'yes', 'on'}
    argv_enabled = any(str(arg).strip().lower() == '--debug' for arg in sys.argv[1:])
    return env_enabled or argv_enabled
from typing import Optional
import logging
import os
import sys


class RemoveEmptyPlugin(HookPlugin):
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
    Filters out empty or whitespace-only text entries.
    
    This is useful for cleaning up output when the hooked application
    sends empty strings or whitespace-only content.
    """
    
    name = "Remove Empty Lines"
    description = "Filters out empty or whitespace-only text"
    version = "1.0"
    author = "Sugoi Hook"
    
    def __init__(self):
        super().__init__()
    
    def process_text(self, text: str) -> Optional[str]:
        """
        Check if text is empty and filter if so.
        
        Args:
            text: The text to check
            
        Returns:
            The original text if not empty, None otherwise
        """
        self._log_debug('process_text.in', text=text)
        text_clean = text.strip()
        
        if not text_clean:
            self._log_debug('process_text.out', output=None)
            return None
        
        self._log_debug('process_text.out', output=text)
        return text
    
    def reset(self):
        """No state to reset for this plugin."""
        pass


# Plugin instance for discovery
plugin = RemoveEmptyPlugin()

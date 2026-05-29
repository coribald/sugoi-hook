"""
Remove Duplicates Plugin
========================

Filters out immediate duplicate text while still allowing a line to recur later.
Also removes inline duplicates where the same text appears twice in a row.
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


class RemoveDuplicatesPlugin(HookPlugin):
    """
    Filters out immediate duplicate text entries.

    This plugin:
    - Removes inline duplicates (same text repeated within a line)
    - Tracks only the last displayed/clipboard text and filters immediate repeats
    """

    name = "Remove Duplicates"
    description = "Filters immediate duplicate text that has already been displayed"
    version = "1.1"
    author = "Sugoi Hook"

    def __init__(self):
        super().__init__()
        self._state['last_text'] = None
        self._state['last_clipboard_text'] = None
        self._state['min_length'] = 10  # Minimum length for duplicate checking

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

    def remove_inline_duplicates(self, text: str) -> str:
        """
        Remove inline duplicates where the same text appears twice in a row.
        For example: "Hello world Hello world" -> "Hello world"
        """
        if not text or len(text) < 4:
            return text

        text_clean = text.strip()

        half_len = len(text_clean) // 2
        if half_len >= 3:
            first_half = text_clean[:half_len]
            second_half = text_clean[half_len:half_len * 2]

            first_normalized = ' '.join(first_half.split())
            second_normalized = ' '.join(second_half.split())

            if first_normalized == second_normalized:
                return first_half.strip()

        for pattern_len in range(3, min(len(text_clean) // 2 + 1, 200)):
            pattern = text_clean[:pattern_len]
            pattern_normalized = ''.join(pattern.split())

            if len(pattern_normalized) < 3:
                continue

            rest = text_clean[pattern_len:].lstrip()
            rest_normalized = ''.join(rest.split())

            if rest_normalized.startswith(pattern_normalized):
                return pattern.strip()

        return text_clean

    def process_text(self, text: str) -> Optional[str]:
        self._log_debug('process_text.in', text=text)
        text_clean = text.strip()

        if not text_clean:
            self._log_debug('process_text.out', output=text)
            return text

        text_clean = self.remove_inline_duplicates(text_clean)
        text_normalized = ''.join(text_clean.split())

        if len(text_normalized) < self._state['min_length']:
            output = text_clean + '\n' if text.endswith('\n') else text_clean
            self._log_debug('process_text.out', output=output, reason='below_min_length')
            return output

        if text_normalized == self._state.get('last_text'):
            self._log_debug('process_text.out', output=None, reason='immediate_duplicate')
            return None

        self._state['last_text'] = text_normalized
        output = text_clean + '\n' if text.endswith('\n') else text_clean
        self._log_debug('process_text.out', output=output)
        return output

    def process_clipboard_text(self, text: str) -> Optional[str]:
        self._log_debug('process_clipboard_text.in', text=text)
        text_clean = text.strip()

        if not text_clean:
            self._log_debug('process_clipboard_text.out', output=text)
            return text

        text_clean = self.remove_inline_duplicates(text_clean)
        text_normalized = ''.join(text_clean.split())

        if len(text_normalized) < self._state['min_length']:
            output = text_clean + '\n' if text.endswith('\n') else text_clean
            self._log_debug('process_clipboard_text.out', output=output, reason='below_min_length')
            return output

        if text_normalized == self._state.get('last_clipboard_text'):
            self._log_debug('process_clipboard_text.out', output=None, reason='immediate_duplicate')
            return None

        self._state['last_clipboard_text'] = text_normalized
        output = text_clean + '\n' if text.endswith('\n') else text_clean
        self._log_debug('process_clipboard_text.out', output=output)
        return output

    def reset(self):
        """Reset duplicate tracking."""
        self._state['last_text'] = None
        self._state['last_clipboard_text'] = None

    def get_settings(self) -> dict:
        """Get plugin settings."""
        return {
            'min_length': (
                self._state['min_length'],
                'int',
                'Minimum text length for duplicate checking (shorter texts are ignored)'
            )
        }

    def set_setting(self, name: str, value) -> bool:
        """Set a plugin setting."""
        if name == 'min_length':
            try:
                self._state['min_length'] = int(value)
                return True
            except (ValueError, TypeError):
                return False
        return False


plugin = RemoveDuplicatesPlugin()

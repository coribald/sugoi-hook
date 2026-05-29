"""
Remove Duplicates Plugin
========================

Filters out immediate duplicate text while still allowing a line to recur later.
Also removes conservative inline duplicates where the same text appears twice in a row.
"""

from typing import Optional
import logging
from plugins import HookPlugin


def runtime_debug_logging_enabled() -> bool:
    import os
    import sys
    env_enabled = os.environ.get('SUGOIHOOK_DEBUG_LOGGING', '').strip().lower() in {'1', 'true', 'yes', 'on'}
    argv_enabled = any(str(arg).strip().lower() == '--debug' for arg in sys.argv[1:])
    return env_enabled or argv_enabled


class RemoveDuplicatesPlugin(HookPlugin):
    """
    Filters out immediate duplicate text entries.

    This plugin:
    - Removes conservative inline duplicates (same text repeated within a line)
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

    def remove_inline_duplicates(self, text: str) -> tuple[str, Optional[str]]:
        """
        Remove inline duplicates where the same text appears twice in a row.
        For example: "Hello world Hello world" -> "Hello world"
        """
        if not text or len(text) < 4:
            return text, None

        text_clean = text.strip()
        if not text_clean:
            return text_clean, None

        # Strict full-line duplicate with optional separating whitespace.
        for split_index in range(3, len(text_clean) - 2):
            first_part = text_clean[:split_index].rstrip()
            second_part = text_clean[split_index:].lstrip()

            if len(first_part) < 3 or len(second_part) < 3:
                continue

            first_normalized = ' '.join(first_part.split())
            second_normalized = ' '.join(second_part.split())

            if first_normalized and first_normalized == second_normalized:
                return first_part.strip(), 'full_repeat'

        # Strict repeated prefix pattern only when the entire remainder matches
        # one more copy of the prefix after whitespace normalization.
        for pattern_len in range(3, min(len(text_clean) // 2 + 1, 200)):
            pattern = text_clean[:pattern_len].rstrip()
            if len(pattern) < 3:
                continue

            rest = text_clean[pattern_len:].lstrip()
            pattern_normalized = ''.join(pattern.split())
            rest_normalized = ''.join(rest.split())

            if pattern_normalized and rest_normalized == pattern_normalized:
                return pattern.strip(), 'normalized_repeat'

        return text_clean, None

    def process_text(self, text: str) -> Optional[str]:
        self._log_debug('process_text.in', text=text)
        text_clean = text.strip()

        if not text_clean:
            self._log_debug('process_text.out', output=text)
            return text

        original_clean = text_clean
        text_clean, inline_reason = self.remove_inline_duplicates(text_clean)
        if inline_reason is not None:
            self._log_debug(
                'process_text.inline_dedup',
                reason=inline_reason,
                before=original_clean,
                after=text_clean
            )
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

        original_clean = text_clean
        text_clean, inline_reason = self.remove_inline_duplicates(text_clean)
        if inline_reason is not None:
            self._log_debug(
                'process_clipboard_text.inline_dedup',
                reason=inline_reason,
                before=original_clean,
                after=text_clean
            )
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
                new_value = int(value)
                if new_value >= 1:
                    self._state['min_length'] = new_value
                    return True
            except (ValueError, TypeError):
                pass
            return False
        return False


plugin = RemoveDuplicatesPlugin()

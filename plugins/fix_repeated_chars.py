"""
Repeated Character Fixer Plugin
===============================

Fixes text where every character is repeated twice due to hooker issues.
Example: "HHeelllloo" -> "Hello"
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

class RepeatedCharFixer(HookPlugin):
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
    Fixes text where every character is repeated twice.
    
    This handles the issue where a text hooker emits every character twice.
    Example: 「「おおははよようう」」 -> 「おはよう」
    
    It intentionally avoids modifying text that just has *some* repeated characters
    or likely-intentional emphasis (like "Hello", "ハハハハ", "！！", or "……")
    unless the entire string follows the repeated-output pattern and still looks like
    real text after collapsing.
    """
    
    name = "Repeated Character Fixer"
    description = "Fixes whole-line repeated-output patterns (e.g. 'HHeelllloo' -> 'Hello')"
    version = "1.1"
    author = "Sugoi Hook"
    
    def __init__(self):
        super().__init__()

    def process_text(self, text: str) -> Optional[str]:
        self._log_debug('process_text.in', text=text)
        if not text or len(text) < 2:
            self._log_debug('process_text.out', output=text)
            return text

        def is_textual_char(ch: str) -> bool:
            return (
                ch.isalnum()
                or '\u3040' <= ch <= '\u30ff'   # Hiragana / Katakana
                or '\u3400' <= ch <= '\u9fff'   # CJK ideographs
            )

        def looks_like_collapsed_text(candidate: str) -> bool:
            if not candidate:
                return False

            core = candidate.rstrip('\n')
            if not core:
                return False

            # Avoid collapsing intentional emphasis like "！！", "……", or "ハハハハ"
            # into shorter punctuation/same-character strings.
            if len(set(core)) == 1:
                return False

            return any(is_textual_char(ch) for ch in core)
        
        # Helper to check if string s follows an interleaved N-repetition pattern.
        def solve(s):
            # Try repetition factors 2, 3, 4
            for n in range(2, 5):
                if len(s) % n != 0:
                    continue
                
                base_slice = s[0::n]
                is_consistent = True
                
                for offset in range(1, n):
                    if s[offset::n] != base_slice:
                        is_consistent = False
                        break
                
                if is_consistent:
                    if looks_like_collapsed_text(base_slice):
                        return {
                            'output': base_slice,
                            'factor': n,
                            'reason': 'matched'
                        }
                    return {
                        'output': None,
                        'factor': n,
                        'reason': 'rejected_non_textual_or_uniform'
                    }
            return None

        # 1. Try raw text (in case everything is repeated or clean)
        match_info = solve(text)
        if match_info is not None:
            if match_info['output'] is not None:
                self._log_debug(
                    'process_text.match',
                    source='raw',
                    factor=match_info['factor'],
                    output=match_info['output']
                )
                return match_info['output']
            self._log_debug(
                'process_text.reject',
                source='raw',
                factor=match_info['factor'],
                reason=match_info['reason']
            )
            
        # 2. Try stripping the last newline (common if added by GUI wrapper)
        # SugoiHook_gui.py appends a newline to text before processing, which breaks strict repetition logic
        if text.endswith('\n'):
            s_stripped = text[:-1]
            if len(s_stripped) >= 2:
                match_info = solve(s_stripped)
                if match_info is not None:
                    if match_info['output'] is not None:
                        output = match_info['output'] + "\n"
                        self._log_debug(
                            'process_text.match',
                            source='newline_stripped',
                            factor=match_info['factor'],
                            output=output
                        )
                        return output
                    self._log_debug(
                        'process_text.reject',
                        source='newline_stripped',
                        factor=match_info['factor'],
                        reason=match_info['reason']
                    )
                    
        self._log_debug('process_text.no_match', output=text)
        self._log_debug('process_text.out', output=text)
        return text

# Plugin instance for discovery
plugin = RepeatedCharFixer()

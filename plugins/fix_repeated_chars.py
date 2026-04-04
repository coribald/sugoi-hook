"""
Repeated Character Fixer Plugin
===============================

Fixes text where every character is repeated twice due to hooker issues.
Example: "HHeelllloo" -> "Hello"
"""

from plugins import TextractorPlugin
from typing import Optional
import logging

class RepeatedCharFixer(TextractorPlugin):
    def _log_debug(self, stage: str, **fields):
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
    (like "Hello" or "ハハハハ") unless the *entire* string follows the doubling pattern.
    """
    
    name = "Repeated Character Fixer"
    description = "Fixes text where every character is repeated multiple times (e.g. 'aaabbb' -> 'ab')"
    version = "1.1"
    author = "Sugoi Hook"
    
    def __init__(self):
        super().__init__()

    def process_text(self, text: str) -> Optional[str]:
        self._log_debug('process_text.in', text=text)
        if not text or len(text) < 2:
            self._log_debug('process_text.out', output=text)
            return text
        
        # Helper to check if string s follows N-repetition
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
                    return base_slice
            return None

        # 1. Try raw text (in case everything is repeated or clean)
        res = solve(text)
        if res is not None:
            self._log_debug('process_text.out', output=res)
            return res
            
        # 2. Try stripping the last newline (common if added by GUI wrapper)
        # SugoiHook_gui.py appends a newline to text before processing, which breaks strict repetition logic
        if text.endswith('\n'):
            s_stripped = text[:-1]
            if len(s_stripped) >= 2:
                res = solve(s_stripped)
                if res is not None:
                    output = res + "\n"
                    self._log_debug('process_text.out', output=output)
                    return output
                    
        self._log_debug('process_text.out', output=text)
        return text

# Plugin instance for discovery
plugin = RepeatedCharFixer()

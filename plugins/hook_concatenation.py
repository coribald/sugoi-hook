"""
Hook Concatenation Plugin
==========================

Concatenates output from multiple selected hooks into a single output.
Supports a required dialogue hook plus optional prefix hooks such as speaker names.
"""

from plugins import TextractorPlugin
from typing import Optional
import logging
import re


class HookConcatenationPlugin(TextractorPlugin):
    def _log_debug(self, stage: str, **fields):
        try:
            parts = []
            for key, value in fields.items():
                value_str = str(value).replace("\r", "\\r").replace("\n", "\\n")
                if len(value_str) > 160:
                    value_str = value_str[:160] + "..."
                parts.append(f"{key}={value_str}")
            message = f"[HOOK CONCAT] {stage}"
            if parts:
                message += " | " + " | ".join(parts)
            logging.info(message)
            try:
                print(message, flush=True)
            except Exception:
                pass
        except Exception:
            pass
    name = "Hook Concatenation"
    description = "Concatenate output from multiple hooks with optional delayed prefixes"
    version = "1.1"
    author = "Sugoi Hook"

    def __init__(self):
        super().__init__()
        self._state['enabled_mode'] = False
        self._state['num_hooks'] = 2
        self._state['hook_ids'] = ""
        self._state['dialogue_hook_id'] = ""
        self._state['prefix_hook_ids'] = ""
        self._state['speaker_wait_ms'] = 150
        self._state['hook_buffers'] = {}
        self._state['clipboard_hook_buffers'] = {}
        self._state['pending_dialogue'] = None
        self._state['pending_timer_id'] = None
        self._hook_pattern = re.compile(r'^\[Hook #?(\d+)\]\s*(.*)$', re.IGNORECASE)

    def process_text(self, text: str) -> Optional[str]:
        if not self._state['enabled_mode']:
            return text

        config = self._get_concat_config()
        if not config['all_hook_ids']:
            return text

        text_stripped = text.strip()
        if text_stripped.startswith('[Console]'):
            return text

        match = self._hook_pattern.match(text_stripped)
        if not match:
            return text

        hook_id = match.group(1)
        hook_text = match.group(2).strip()

        if hook_id not in config['all_hook_ids']:
            self._log_debug('drop_unconfigured_hook', hook_id=hook_id, text=hook_text)
            return None

        if hook_id in self._state['hook_buffers'] and hook_id == config['dialogue_hook_id']:
            self._flush_pending_dialogue()
            self._state['hook_buffers'] = {}

        if hook_text:
            self._state['hook_buffers'][hook_id] = hook_text

        if hook_id in config['prefix_hook_ids']:
            self._log_debug('prefix_received', hook_id=hook_id, text=hook_text, pending_dialogue=self._state.get('pending_dialogue'))
            if self._state['pending_dialogue']:
                if self._all_prefixes_ready(config):
                    self._cancel_pending_timer()
                    self._log_debug('emit_on_prefix_ready', hook_id=hook_id)
                    return self._emit_pending_dialogue_now()
                self._log_debug('prefix_waiting_for_more', hook_id=hook_id, configured_prefixes=config['prefix_hook_ids'], buffered=list(self._state['hook_buffers'].keys()))
                return None

            wait_ms = max(0, int(config['speaker_wait_ms']))
            if wait_ms == 0:
                self._log_debug('emit_prefix_no_wait', hook_id=hook_id)
                return self._emit_pending_dialogue_now()

            self._log_debug('schedule_prefix_only_emit', hook_id=hook_id, wait_ms=wait_ms, buffered=list(self._state['hook_buffers'].keys()))
            self._schedule_pending_emit(wait_ms)
            return None

        if hook_id == config['dialogue_hook_id']:
            self._state['pending_dialogue'] = hook_text
            self._log_debug('dialogue_received', hook_id=hook_id, text=hook_text, buffered=list(self._state['hook_buffers'].keys()))
            if not hook_text:
                self._log_debug('drop_empty_dialogue', hook_id=hook_id)
                return None

            if not config['prefix_hook_ids']:
                self._log_debug('emit_dialogue_without_prefixes', hook_id=hook_id)
                return self._emit_pending_dialogue_now()

            if self._all_prefixes_ready(config):
                self._log_debug('emit_dialogue_with_ready_prefixes', hook_id=hook_id)
                return self._emit_pending_dialogue_now()

            wait_ms = max(0, int(config['speaker_wait_ms']))
            if wait_ms == 0:
                self._log_debug('emit_dialogue_no_wait', hook_id=hook_id)
                return self._emit_pending_dialogue_now()

            self._log_debug('schedule_pending_emit', hook_id=hook_id, wait_ms=wait_ms, expected_prefixes=config['prefix_hook_ids'])
            self._schedule_pending_emit(wait_ms)
            return None

        return None

    def process_clipboard_text(self, text: str) -> Optional[str]:
        if not self._state['enabled_mode']:
            return text

        config = self._get_concat_config()
        if not config['all_hook_ids']:
            return text

        text_stripped = text.strip()
        if text_stripped.startswith('[Console]'):
            return text

        match = self._hook_pattern.match(text_stripped)
        if not match:
            return text

        hook_id = match.group(1)
        hook_text = match.group(2).strip()

        if hook_id not in config['all_hook_ids']:
            return None

        if hook_id in self._state['clipboard_hook_buffers'] and hook_id == config['dialogue_hook_id']:
            self._state['clipboard_hook_buffers'] = {}

        if hook_text:
            self._state['clipboard_hook_buffers'][hook_id] = hook_text

        if hook_id in config['prefix_hook_ids']:
            return None

        if hook_id == config['dialogue_hook_id']:
            output_parts = []
            for prefix_hook_id in config['prefix_hook_ids']:
                prefix_text = self._state['clipboard_hook_buffers'].get(prefix_hook_id, '').strip()
                if prefix_text:
                    output_parts.append(prefix_text)
            if hook_text:
                output_parts.append(hook_text)
            if output_parts:
                combined_output = self._normalize_combined_output_order(''.join(output_parts))
                return combined_output + '\n'
            return None

        return None

    def _get_concat_config(self):
        dialogue_hook_id = str(self._state.get('dialogue_hook_id', '')).strip()
        prefix_hook_ids = [hook_id.strip() for hook_id in str(self._state.get('prefix_hook_ids', '')).split(',') if hook_id.strip().isdigit()]

        if not dialogue_hook_id:
            legacy_hook_ids = self._parse_hook_ids()
            if legacy_hook_ids:
                dialogue_hook_id = legacy_hook_ids[-1]
                prefix_hook_ids = legacy_hook_ids[:-1]

        all_hook_ids = []
        for hook_id in prefix_hook_ids + ([dialogue_hook_id] if dialogue_hook_id else []):
            if hook_id and hook_id not in all_hook_ids:
                all_hook_ids.append(hook_id)

        return {
            'dialogue_hook_id': dialogue_hook_id,
            'prefix_hook_ids': prefix_hook_ids,
            'all_hook_ids': all_hook_ids,
            'speaker_wait_ms': self._state.get('speaker_wait_ms', 150),
        }

    def _parse_hook_ids(self) -> list:
        hook_ids_str = self._state['hook_ids'].strip()
        if not hook_ids_str:
            return []
        hook_ids = []
        for hook_id in hook_ids_str.split(','):
            hook_id = hook_id.strip()
            if hook_id.isdigit():
                hook_ids.append(hook_id)
        return hook_ids

    def _all_prefixes_ready(self, config) -> bool:
        if not config['prefix_hook_ids']:
            return True
        return all(prefix_hook_id in self._state['hook_buffers'] for prefix_hook_id in config['prefix_hook_ids'])

    def _normalize_combined_output_order(self, text: str) -> str:
        stripped = text.strip()
        # Defensive fix: if we somehow get quoted dialogue followed by a short speaker label,
        # move the label back in front where VN hook concatenation expects it.
        trailing_label_match = re.match(r'^(「.+?」)([^「」\s]{1,24})$', stripped)
        if trailing_label_match:
            dialogue_text, trailing_label = trailing_label_match.groups()
            return f"{trailing_label}{dialogue_text}"
        return stripped

    def _build_pending_output(self) -> str:
        config = self._get_concat_config()
        output_parts = []
        for prefix_hook_id in config['prefix_hook_ids']:
            prefix_text = self._state['hook_buffers'].get(prefix_hook_id, '').strip()
            if prefix_text:
                output_parts.append(prefix_text)
        dialogue_text = (self._state.get('pending_dialogue') or '').strip()
        if dialogue_text:
            output_parts.append(dialogue_text)
        if not output_parts:
            return ""
        return self._normalize_combined_output_order(''.join(output_parts)) + '\n'

    def _emit_pending_dialogue_now(self) -> Optional[str]:
        self._cancel_pending_timer()
        output_text = self._build_pending_output()
        self._log_debug('emit_pending_dialogue', output=output_text, buffered=list(self._state['hook_buffers'].keys()))
        self._state['pending_dialogue'] = None
        self._state['hook_buffers'] = {}
        return output_text or None

    def _flush_pending_dialogue(self):
        self._log_debug('flush_pending_dialogue')
        output_text = self._emit_pending_dialogue_now()
        if not output_text:
            return
        app = getattr(self, 'app', None)
        if not app:
            return
        try:
            app.run_on_ui_thread(app.append_output, output_text, True, False)
        except Exception:
            pass

    def _schedule_pending_emit(self, wait_ms: int):
        self._cancel_pending_timer()
        app = getattr(self, 'app', None)
        if not app or not hasattr(app, 'root'):
            return
        self._state['pending_timer_id'] = app.root.after(wait_ms, self._flush_pending_dialogue)

    def _cancel_pending_timer(self):
        timer_id = self._state.get('pending_timer_id')
        app = getattr(self, 'app', None)
        if timer_id and app and hasattr(app, 'root'):
            try:
                app.root.after_cancel(timer_id)
            except Exception:
                pass
        self._state['pending_timer_id'] = None

    def reset(self):
        self._cancel_pending_timer()
        self._state['hook_buffers'] = {}
        self._state['clipboard_hook_buffers'] = {}
        self._state['pending_dialogue'] = None

    def on_enable(self):
        self.reset()

    def on_disable(self):
        self.reset()

    def get_settings(self) -> dict:
        return {
            'enabled_mode': (
                self._state['enabled_mode'],
                'bool',
                'Enable hook concatenation mode'
            ),
            'num_hooks': (
                self._state['num_hooks'],
                'int_slider',
                'Legacy number of hooks setting (kept for compatibility)',
                {'min': 2, 'max': 10}
            ),
            'hook_ids': (
                self._state['hook_ids'],
                'str',
                'Legacy hook order (fallback only). If dialogue/prefix hooks are set, those take priority.'
            ),
            'dialogue_hook_id': (
                self._state['dialogue_hook_id'],
                'str',
                'Required dialogue hook ID (for example 2)'
            ),
            'prefix_hook_ids': (
                self._state['prefix_hook_ids'],
                'str',
                'Optional prefix hook IDs in order (for example 1 or 5,1)'
            ),
            'speaker_wait_ms': (
                self._state['speaker_wait_ms'],
                'int_slider',
                'How long to wait for optional prefix hooks before emitting dialogue only',
                {'min': 0, 'max': 500}
            )
        }

    def set_setting(self, name: str, value) -> bool:
        if name == 'enabled_mode':
            try:
                self._state['enabled_mode'] = bool(value)
                self.reset()
                return True
            except (ValueError, TypeError):
                return False

        elif name == 'num_hooks':
            try:
                num_hooks = int(value)
                if 2 <= num_hooks <= 10:
                    self._state['num_hooks'] = num_hooks
                    return True
                return False
            except (ValueError, TypeError):
                return False

        elif name in ('hook_ids', 'dialogue_hook_id', 'prefix_hook_ids'):
            try:
                hook_ids_str = str(value).strip()
                if hook_ids_str:
                    parts = [p.strip() for p in hook_ids_str.split(',')]
                    for part in parts:
                        if part and not part.isdigit():
                            return False
                self._state[name] = hook_ids_str
                self.reset()
                return True
            except (ValueError, TypeError):
                return False

        elif name == 'speaker_wait_ms':
            try:
                wait_ms = int(value)
                if 0 <= wait_ms <= 500:
                    self._state['speaker_wait_ms'] = wait_ms
                    self.reset()
                    return True
                return False
            except (ValueError, TypeError):
                return False

        return False


plugin = HookConcatenationPlugin()

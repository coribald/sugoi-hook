# Sugoi Hook Context

## What This App Is

Sugoi Hook is a Windows/Tkinter GUI for attaching to a running game process, selecting text hooks, running extracted text through a plugin pipeline, and showing/copying the results. The main moving parts are:

- `SugoiHook_gui.py`
  - main window
  - process/hook attach flow
  - plugin loading, config UI, lifecycle, and pipeline orchestration
  - session event log, session output, clipboard handling, config persistence
- `plugins/`
  - text-processing plugins
  - translation plugins
  - overlay display plugin
- `plugins_config.json`
  - active plugins
  - plugin settings
  - main window geometry
- `overlay_config.json`
  - overlay window geometry and styling

## Current Architecture Notes

- Process/hook/output flow is source-first during iteration. We are mostly running from the `.py` path, not rebuilding constantly.
- The plugin pipeline now has a shared pre-translation stage so translator input and clipboard input can stay aligned.
- Hook Concatenation is stateful and timing-sensitive. It should be treated carefully because many downstream behaviors depend on its output.
- Translation plugins are expected to receive the cleaned untranslated line, not raw hook text.
- The app now logs a lot of pipeline detail to both `sugoihook-runtime.log` and the source-run console.

## UI State

- The main window has a fixed header outside the main scroll region.
- The outer scrollbar exists as a fallback, but section-local scrolling should own the mouse wheel where appropriate.
- `Select Process` and `Select Hook` are a responsive pair:
  - stacked full-width when either is expanded
  - side-by-side when both are collapsed
- Compact mode is active when `Select Process`, `Select Hook`, and `Plugins` are all collapsed.
- The app stores separate full and compact geometries and auto-switches between them.
- Plugins start collapsed by default.

## Translation / Hook Pipeline State

- OpenAI and Google translation plugins are Python 3.9-safe again.
- Clipboard now gets the same untranslated line that is sent to translation plugins.
- Hook Concatenation currently supports:
  - `dialogue_hook_id`
  - `prefix_hook_ids`
  - `speaker_wait_ms`
- Prefix-only lines now flush after the same timeout instead of disappearing.
- `remove_duplicates.py` was rewritten to suppress only immediate repeats rather than broad substring/seen-before matches.

## Logging / Debugging State

- `SugoiHook_gui.py` emits `[PIPELINE] ...` logs for:
  - hook arrival
  - pre-translation plugin flow
  - translation result/empty result
  - post-translation flow
  - final display/clipboard decisions
- `plugins/hook_concatenation.py` emits `[HOOK CONCAT] ...` logs for buffered prefixes/dialogue, waits, and emits.
- `plugins/remove_empty.py`, `plugins/fix_repeated_chars.py`, and `plugins/remove_duplicates.py` now log their in/out behavior.
- `plugins/openai_translate.py` now prints the full outbound payload to the console.

## OpenAI Plugin State

- Supported models now include:
  - `gpt-5-mini`
  - `gpt-4o`
  - `gpt-4o-mini`
  - `gpt-4.1`
  - `gpt-4.1-mini`
- `reasoning` is only sent for `gpt-5*` models.
- For `gpt-4o` / `gpt-4o-mini`, requested `low` verbosity is automatically raised to `medium`.
- There is a no-op safeguard: if the model returns the source text unchanged, it is treated as no translation.
- Rolling original-line context is enabled and was fixed so it actually reaches the translator path.

## Prompt / Config State

The OpenAI translation config now includes guidance for:

- preserving/formatting speaker labels
- not rewriting `Speaker: "Dialogue"` into prose like `Speaker said, "..."`
- preferring romanized familial honorifics like `Nii-san`
- preserving quotation marks for spoken dialogue

If behavior looks wrong, inspect:

- `plugins_config.json`
- the full outbound payload log from `openai_translate.py`

## Overlay Window State

- The overlay plugin remembers its own size and position through `overlay_config.json`.
- The plugin settings dialog now has a live preview for overlay fonts/colors/styles.
- The settings dialog scrollbar was adjusted to avoid stealing the mouse wheel from selector/editor widgets, though this may still be worth rechecking if combobox popup behavior feels off in practice.

## Lifecycle / Stability Notes

- Plugin reload and app shutdown now call plugin `on_disable()` and remove plugin modules from `sys.modules`.
- This cleaned up stale sessions/windows/timers and made reload/close behavior more intentional.
- We deliberately did not pursue some lower-value branching behavior in the clipboard path to avoid destabilizing the now-stable pipeline.

## Good Next Starting Points

- If translation behavior drifts:
  - inspect the outbound OpenAI payload in console
  - compare translator input vs clipboard
  - check `[HOOK CONCAT]` and `[PIPELINE]` logs together
- If UI work resumes:
  - keep using source-run iteration first
  - avoid rebuilding unless validating packaged behavior
- If packaged behavior is revisited:
  - remember earlier fixes around Tk packaging, logging, and elevation heuristics

## Today’s High-Level Changelog

- stabilized source-run behavior and removed unwanted auto-elevation behavior
- improved main window usability and layout, including compact/full geometry behavior
- moved more status into explicit UI instead of hidden output/log-only behavior
- added overlay settings live preview
- repaired rolling OpenAI context so previous lines actually reach the prompt
- aligned clipboard with translator input
- fixed Hook Concatenation timing/output edge cases
- fixed duplicate suppression so valid concatenated lines are not dropped
- expanded pipeline debugging across the full text flow
- added `gpt-4o` and `gpt-4o-mini` to the OpenAI plugin
- adjusted 4o verbosity behavior to avoid invalid low-verbosity requests

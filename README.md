# Sugoi Hook

A Windows GUI for attaching to game processes, selecting text hooks, processing extracted text through plugins, and optionally translating or displaying it in an overlay.

![Python](https://img.shields.io/badge/python-3.9%2B-blue.svg)
![Platform](https://img.shields.io/badge/platform-Windows-lightgrey.svg)
![License](https://img.shields.io/badge/license-GPL--3.0-blue.svg)

## Recent Changes

- Added a cleaner source-run workflow with `run_debug.*` and `run_normal.*` launchers.
- Updated the build scripts to match the current repo layout and preserve runtime `*_config.json` files across clean builds.
- Reworked the main UI layout: fixed header, better section collapsing, compact/full geometry restore, clearer hook/process flow, and split `Session Events` / `Session Output`.
- Improved plugin management with explicit controls, better defaults, and a live preview in the Overlay Window settings.
- Stabilized the text pipeline: shared pre-translation flow, clipboard alignment with translator input, safer Hook Concatenation behavior, and less aggressive duplicate filtering.
- Expanded debugging and runtime logging, including console-visible pipeline tracing and full outbound OpenAI payload logging.
- Added support for `gpt-4o` and `gpt-4o-mini` in the OpenAI translation plugin.

## Contact

For support or discussion, join the **Sugoi Toolkit Discord Server**:

🔗 [Join Sugoi Toolkit Server](https://discord.gg/XFbWSjMHJh)

---

## Features

### Engine Support

Sugoi Hook supports two hooking engines:

- **Luna Hook**
  - good compatibility with many modern games
  - default engine in the UI
- **Textractor**
  - classic hook workflow with broad compatibility
  - useful fallback for titles that behave better on Textractor

The engine selector lives in the fixed app header. Switching engines detaches the current session and reinitializes the hook flow.

### Core Workflow

- attach to a running process
- inspect discovered hooks or enter a manual hook
- optionally combine hooks with Hook Concatenation
- run text through a configurable plugin chain
- view session events and session output separately
- auto-copy cleaned untranslated text to the clipboard if desired

### UI / Quality of Life

- fixed header outside the scroll region
- compact/expanded layout with remembered window geometry
- collapsible sections for process, hook, plugins, events, and output
- session status surfaced directly in the UI instead of only in logs
- improved plugin configuration dialogs, including overlay style preview
- system tray support

### Built-in Plugins

- **Hook Concatenation**
  - combines speaker/dialogue style split hooks
  - supports `dialogue_hook_id`, `prefix_hook_ids`, and a short timing window
- **Remove Empty Lines**
- **Remove Duplicates**
  - filters immediate repeats instead of aggressively dropping broader matches
- **Remove Special Characters**
- **Minimum Length Filter**
- **Fix Repeated Characters**
- **Google Translate**
- **OpenAI Translate**
  - rolling original-line context
  - story / character context and instruction fields
  - support for `gpt-5-mini`, `gpt-4o`, `gpt-4o-mini`, `gpt-4.1`, and `gpt-4.1-mini`
- **Translation Proxy**
  - forwards extracted text to Translator++
- **Renji WebSocket**
  - sends Japanese text to Renji for reading-tracker workflows
- **Overlay Window**
  - on-screen text overlay with configurable fonts, colors, opacity, and saved position/size

## Quick Start

### Prerequisites

- Windows 10/11
- Python 3.9+ if running from source with your own interpreter

This repo also includes a local `Python39` runtime used by the provided launch scripts.

### Run From Source

```powershell
git clone https://github.com/sugoi-toolkit-official/sugoi-hook.git
cd sugoi-hook
python SugoiHook_gui.py
```

Helpful launchers in this repo:


- `run_debug.bat` / `run_debug.ps1`
  - launches source mode in Windows Terminal for debugging / console visibility
- `run_normal.bat` / `run_normal.ps1`
  - launches source mode in the normal user context

### Build Executables

Release onefile build:

```powershell
build.bat
```

Debug standalone build:

```powershell
build_debug_standalone.bat
```

Current build behavior:

- uses repo-local pip and Nuitka caches
- includes the runtime asset folders used by the app
- preserves runtime `*_config.json` files across clean builds

## How to Use

### Basic Flow

1. **Select a process**
   - choose a process from `Select Process`
   - use the search box to narrow the list
   - attach using the action button

2. **Choose a hook source**
   - inspect hooks in `Select Hook`
   - select a discovered hook or enter a manual hook
   - if Hook Concatenation is active, it can become the effective source instead of a single selected hook

3. **Read the output**
   - `Session Events` shows attach / hook / pipeline status
   - `Session Output` shows the extracted / translated line flow

4. **Tune plugins as needed**
   - enable, disable, configure, and reorder plugins from the Plugins section

### Hook Concatenation

Hook Concatenation is designed for games where text is split across multiple hooks, commonly:

- one hook for the speaker name
- one hook for the dialogue text

Current behavior supports:

- `dialogue_hook_id`
- `prefix_hook_ids`
- `speaker_wait_ms`

That lets the plugin briefly wait for a late-arriving speaker line without stalling forever when narration or monologue has no speaker hook at all.

### Translation Plugins

The app now uses a shared pre-translation pipeline so the translator input and clipboard input stay aligned.

Important behavior:

- translation plugins receive the cleaned untranslated line
- clipboard gets that same untranslated translator input
- rolling original-line context can be sent to OpenAI for continuity

### Plugin Management

Current plugin controls support:

- toggle active state
- open settings
- move up / move down
- drag reordering if preferred
- refresh the plugin directory

Many plugin settings are persisted through `plugins_config.json`.

### Overlay Window

The overlay plugin:

- remembers its size and position
- supports separate translation/original/warning fonts and colors
- now includes a live preview in its settings dialog so style changes can be seen before saving

## Runtime Files

Useful local state files:

- `plugins_config.json`
  - plugin settings, active plugins, main window geometry
- `overlay_config.json`
  - overlay appearance and geometry
- `game_profiles.json`
  - saved game / hook profile data
- `sugoihook-runtime.log`
  - runtime log file

## Logging and Debugging

The app has expanded runtime tracing intended for source-mode debugging.

Current traces include:

- hook line arrival
- pre-translation plugin results / drops
- Hook Concatenation timing and emits
- translation request / response logging
- clipboard and final output decisions

When OpenAI debug logging is enabled, the plugin prints the full outbound request payload to the console.

## File Structure

```text
sugoi-hook/
├── SugoiHook_gui.py
├── plugins/
├── textractor_builds/
├── luna_builds/
├── Translator/
├── Python39/
├── build.bat
├── build_debug_standalone.bat
├── run_debug.bat
├── run_debug.ps1
├── run_normal.bat
├── run_normal.ps1
├── plugins_config.json
├── overlay_config.json
├── game_profiles.json
└── README.md
```

## Acknowledgments

Sugoi Hook builds on several open-source projects and community contributions.

### Hooking Engines

#### Textractor

This project integrates [Textractor](https://github.com/Chenx221/Textractor), a modified version of the original Textractor by Artikash.

- **Original Textractor**: [Artikash/Textractor](https://github.com/Artikash/Textractor)
- **Modified Textractor**: [Chenx221/Textractor](https://github.com/Chenx221/Textractor)

#### Luna Hook

Sugoi Hook integrates Luna Hook assets sourced from the [LunaTranslator](https://github.com/HIllya51/LunaTranslator) project.

- **Luna Hook DLLs**: based on work from [LunaTranslator](https://github.com/HIllya51/LunaTranslator)
- **LunaHostCLI**: CLI integration work by Team Sugoi Toolkit

## License

This project is licensed under the GPL-3.0 License. See `LICENSE` for details.

This tool is intended for legitimate translation-assistance and accessibility workflows. Please respect software licenses and terms of service when using text extraction tools.

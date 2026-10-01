# Random Hotbar

A small Minecraft building companion that randomly switches hotbar slots, helping
you mix blocks into natural-looking walls, paths, and roofs.

**macOS · Python 3.10+ · English interface**

> **Windows is in development.** This repository currently contains only the macOS version.

## Features

- Uses number-row keys **1–9**, matching Minecraft's nine hotbar slots.
- Three speeds with a randomized pause between key presses.
- Optional priority key with a selection chance from 0 to 100%.
- Start countdown: three seconds by default to switch to the game.
- Hotbar preview that highlights the last key pressed.
- Soft, rounded cards, inputs, and dropdown menus.
- Light, dark, and system palettes; keyboard navigation in dropdowns.
- Start and Stop buttons available on every tab.

## Installation

You need Python 3.10+ with Tkinter. Check your installation:

```sh
python3 -m tkinter
```

A test window should open. If Tkinter is missing, install Python with Tcl/Tk
support, for example from [python.org](https://www.python.org/downloads/macos/).

Download the project using **Code → Download ZIP**, or clone it:

```sh
git clone https://github.com/kylebRka/random-hotbar.git
cd random-hotbar
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
python3 main.py
```

You can also launch it with `python3 -m random_hotbar`.

### macOS permissions

To send keyboard events, enable **System Settings → Privacy & Security →
Accessibility** for the application running Python, such as Terminal or your IDE.
Then restart that application.

## Usage

1. Place your chosen blocks in the first Minecraft hotbar slots.
2. Choose the number of slots and switching speed.
3. Optionally set a priority key in Settings and enable it on the Randomizer tab.
4. Press **Start shuffling** and switch to Minecraft before the countdown ends.
5. Build while the app switches the selected slot.
6. Return to the app and press **Stop** when you are done.

Keyboard events go to the **active window**. The app does not automatically detect
Minecraft and currently has no global stop shortcut. Closing the app also stops
the loop. Settings are kept for the current session and are not saved to disk.

## Speed and priority

| Speed | Pause between presses |
| --- | --- |
| Slow | 0.8–1.5 seconds |
| Medium | 0.4–0.8 seconds |
| Fast | 0.2–0.4 seconds |

Each key is also held for 0.05 seconds. Without priority, every selected key is
equally likely. With a priority chance of 40%, that key receives 40% of presses;
the other keys share the remaining 60% equally. The priority key must be within
the selected slot range.

## Project layout

```text
main.py                     # application entry point
requirements.txt            # macOS Quartz bindings through PyObjC
random_hotbar/
  config.py                 # configuration and validation
  selection.py              # random key selection
  runner.py                 # worker loop and cancellation
  backends/
    macos.py                # keyboard events through Quartz
  ui/
    app.py                  # window and controls
    themes.py               # palettes and typography
    widgets.py              # cards, buttons, and navigation
    fields.py               # numeric inputs and dropdowns
    platform.py             # display sizing
tests/                      # tests without real keyboard events
docs/architecture.md        # architecture notes
```

## Development checks

With the virtual environment activated:

```sh
python3 -m unittest discover -s tests -v
python3 -m compileall -q random_hotbar main.py
```

Tests cover probability distributions, validation, cancellation, error handling,
theme switching, inputs, and dropdown menus. They do not send real key presses.
UI tests require Tkinter and a graphical session. GitHub Actions runs the core
logic tests and syntax checks.

## Platform support

| Platform | Status |
| --- | --- |
| macOS | Current published version |
| Windows | In development; source and builds are not published yet |

## Roadmap

- Prepare and validate the Windows version.
- Add a global stop shortcut.
- Save settings between sessions.

Found a bug or have an idea? Open an **Issue** with a description and your Python
and macOS versions. Include a screenshot for interface issues.

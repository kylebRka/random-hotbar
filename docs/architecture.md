# Architecture

The public release supports macOS. Windows is in development and is not included
in this release.

`RunConfig` is an immutable snapshot of one run's settings. It validates ranges
and accepts only keys `1–9`. `selection.choose_key` selects a key independently
of the interface and operating system.

`HotbarRunner` owns a worker thread and a separate cancellation event for each
run. The countdown and pauses use `Event.wait` so they can be cancelled promptly.
A new run is rejected while the previous worker is alive. Settings are passed to
the worker once; the worker never accesses Tkinter.

The worker sends `started`, `key`, `error`, and `stopped` events through a queue.
The main thread polls it with `after`, displays errors, and updates the interface.
Closing the window cancels the worker and waits for the current key to be released.

Quartz is imported only when a run starts. The macOS backend uses physical key
codes and CGEvent. Permission is checked with
[CGPreflightPostEventAccess](https://developer.apple.com/documentation/coregraphics/cgpreflightposteventaccess()).

`i18n.translate` maps English source strings to Russian. Widgets keep canonical
English identifiers for pages, speeds, and themes; only their displayed labels
change. The language button updates widgets in place, closes open menus, and
translates the current status without restarting the worker. English is the
default; language selection lasts for the current session.

Cards and inputs use continuous Canvas outlines with explicit fills and borders
so Tk does not fall back to black. Dropdowns use an opaque background matching
the selected palette. There is no visible scrollbar; pages support wheel
scrolling when space is limited. Start and Stop stay at the bottom of the window.

## Manual checks on macOS

1. Check that Tkinter is installed, launch the app, and open all three tabs.
2. Test Light, Dark, and System palettes and resize the window.
3. Enter an invalid slot count, probability, or priority outside the selected range.
   Confirm that an error appears and no keys are sent.
4. Set a five-second delay, start, and cancel during the countdown.
5. Start without priority and switch to an empty text editor. Confirm that only
   the selected digits appear, then stop and verify that input stops.
6. Test priority probabilities of 0% and 100% for the first and ninth slots.
7. Quickly stop and restart, then close the window during a run. Confirm that
   no second loop remains and no key stays held.
8. Verify slot switching in Minecraft.

Automated tests do not confirm event delivery to a particular game and do not
replace manual testing in Minecraft.

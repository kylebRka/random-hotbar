"""Physical number-row keys via macOS Quartz."""
import time
from ..config import normalize_key

KEY_CODES = dict(zip("123456789", (18, 19, 20, 21, 23, 22, 26, 28, 25)))


class MacOSKeyboard:
    def __init__(self):
        try:
            import Quartz
        except ImportError as error:
            raise RuntimeError("Install dependencies: python3 -m pip install -r requirements.txt") from error
        self.quartz = Quartz
        if not Quartz.CGPreflightPostEventAccess():
            raise RuntimeError(
                "Allow keyboard control in System Settings → "
                "Privacy & Security → Accessibility "
                "for the application running Python, then restart that application."
            )

    def press(self, key):
        quartz = self.quartz
        code = KEY_CODES[normalize_key(key)]
        down = quartz.CGEventCreateKeyboardEvent(None, code, True)
        up = quartz.CGEventCreateKeyboardEvent(None, code, False)
        if down is None or up is None:
            raise RuntimeError("Quartz could not create a keyboard event.")
        quartz.CGEventPost(quartz.kCGHIDEventTap, down)
        try:
            time.sleep(0.05)
        finally:
            quartz.CGEventPost(quartz.kCGHIDEventTap, up)

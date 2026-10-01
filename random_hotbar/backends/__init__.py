"""Native input backend for the currently published macOS version."""
import sys


def create_backend():
    if sys.platform != "darwin":
        raise RuntimeError("This release supports macOS. The Windows version is in development.")
    from .macos import MacOSKeyboard
    return MacOSKeyboard()

"""Native input backend for the currently published macOS version."""
import sys


def create_backend():
    if sys.platform != "darwin":
        raise RuntimeError("Эта версия поддерживает macOS. Версия для Windows находится в разработке.")
    from .macos import MacOSKeyboard
    return MacOSKeyboard()

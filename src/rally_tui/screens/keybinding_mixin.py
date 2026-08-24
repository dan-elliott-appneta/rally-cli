"""Shared vim-style keybinding wiring for screens with a single navigation axis."""

from __future__ import annotations

from rally_tui.utils.keybindings import VIM_KEYBINDINGS


class KeybindingMixin:
    """Mixin for Screen subclasses that bind a small set of navigation keys.

    Expects the including Screen to set `self._user_settings` (UserSettings |
    None) before calling `_apply_keybindings`.
    """

    def _apply_keybindings(self, navigation_bindings: dict[str, str]) -> None:
        """Bind navigation keys from user settings (or vim defaults).

        Args:
            navigation_bindings: Maps action_id (e.g. "navigation.down") to
                the handler action name (e.g. "scroll_down") to bind it to.
        """
        user_settings = getattr(self, "_user_settings", None)
        keybindings = user_settings.keybindings if user_settings else VIM_KEYBINDINGS

        for action_id, handler in navigation_bindings.items():
            if action_id in keybindings:
                key = keybindings[action_id]
                self._bindings.bind(key, handler, show=False)

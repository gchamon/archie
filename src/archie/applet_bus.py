APPLET_BUS_NAME = "com.gchamon.Archie.Applet"
APPLET_OBJECT_PATH = "/org/archie/applet"
APPLET_INTERFACE = "com.gchamon.Archie.Applet"


def get_applet_version() -> str | None:
    """Return the running applet version, if an applet owns the session name."""
    result = _call_applet_method("GetVersion", "(s)")
    if result is None or not result or not isinstance(result[0], str):
        return None
    return result[0]


def restart_applet() -> bool:
    """Ask the running applet to re-exec itself with the installed code."""
    return _call_applet_method("Restart", None) is not None


def notify_applet_settings_changed() -> None:
    """Ask the running applet to refresh its cached tooltip state."""
    _call_applet_method("SettingsChanged", None)


def _call_applet_method(method_name: str, reply_type: str | None) -> tuple[object, ...] | None:
    import gi

    gi.require_version("Gio", "2.0")
    gi.require_version("GLib", "2.0")
    from gi.repository import Gio, GLib  # type: ignore[attr-defined]

    try:
        connection = Gio.bus_get_sync(Gio.BusType.SESSION)
        reply = connection.call_sync(
            APPLET_BUS_NAME,
            APPLET_OBJECT_PATH,
            APPLET_INTERFACE,
            method_name,
            None,
            GLib.VariantType.new(reply_type) if reply_type is not None else None,
            Gio.DBusCallFlags.NO_AUTO_START,
            1_000,
            None,
        )
    except GLib.Error:
        # The GUI remains usable when the optional tray applet is not running.
        return None
    return reply.unpack() if reply is not None else ()

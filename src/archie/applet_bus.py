APPLET_BUS_NAME = "com.gchamon.Archie.Applet"
APPLET_OBJECT_PATH = "/org/archie/applet"
APPLET_INTERFACE = "com.gchamon.Archie.Applet"


def notify_applet_settings_changed() -> None:
    """Ask the running applet to refresh its cached tooltip state."""
    import gi

    gi.require_version("Gio", "2.0")
    gi.require_version("GLib", "2.0")
    from gi.repository import Gio, GLib  # type: ignore[attr-defined]

    try:
        connection = Gio.bus_get_sync(Gio.BusType.SESSION)
        connection.call_sync(
            APPLET_BUS_NAME,
            APPLET_OBJECT_PATH,
            APPLET_INTERFACE,
            "SettingsChanged",
            None,
            None,
            Gio.DBusCallFlags.NO_AUTO_START,
            1_000,
            None,
        )
    except GLib.Error:
        # The GUI remains usable when the optional tray applet is not running.
        return

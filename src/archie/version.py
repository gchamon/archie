from importlib.metadata import PackageNotFoundError, version


def installed_archie_version() -> str:
    """Return the version of Archie installed for new processes."""
    try:
        return version("archie")
    except PackageNotFoundError:
        return "development"


def applet_update_required(running_version: str | None, installed_version: str) -> bool:
    return running_version is not None and running_version != installed_version

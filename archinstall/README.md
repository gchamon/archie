# Archinstall Integration

This directory contains the self-contained Archinstall plugin, its bootstrap
script, and the shared package manifest used for fresh Archie installations.

The plugin is downloaded before the repository exists in the install target, so
`plugin.py` must remain self-contained. The bootstrap creates the persistent
checkout and hands off to `archinstall/provision.sh`.

See the [Arch Linux integration architecture](../docs/architecture/ARCH_LINUX_INTEGRATION.md)
for the supported profile contract, privilege boundaries, and release flow.

# MediaTek MT7922 Bluetooth Regression

Status: Reported upstream

Bluetooth on the Acer Nitro system fails with `linux-lts 6.18.30-1` and works
again after downgrading to `linux-lts 6.18.29-1`. The failure matches an
already reported upstream `btmtk` regression affecting MediaTek Bluetooth
adapters.

## Local Impact

- Hardware: Acer Nitro system with MediaTek MT7922 Wi-Fi/Bluetooth.
- PCI ID: `14c3:0616`.
- Known good: `linux-lts 6.18.29-1`.
- Known bad: `linux-lts 6.18.30-1`.
- Workaround: downgrade to `linux-lts 6.18.29-1`.

Symptoms seen on the bad kernel:

```text
Bluetooth: hci0: Failed to send wmt func ctrl (-22)
No default controller available
```

Local evidence:

- [assets/journalctl-bluetooth.txt](assets/journalctl-bluetooth.txt) was
  collected on `linux-lts 6.18.30-1` with:

  ```bash
  journalctl -b | grep Bluetooth > assets/journalctl-bluetooth.txt
  ```

## Upstream Status

Canonical regression report:

- [linux-bluetooth thread on lore.kernel.org](https://lore.kernel.org/linux-bluetooth/5i35wmc4z7sz54jo5uj6ywext2enh4ik3oxmfmperqk2v5kc27@ppvm6oodzipn/#r)

Related upstream fix:

- [Bluetooth: btmtk: accept too short WMT FUNC_CTRL events](https://www.spinics.net/lists/linux-bluetooth/msg129347.html)

## Related Community Reports

- [Arch forum: MT7922 Bluetooth regression](https://bbs.archlinux.org/viewtopic.php?id=313561)
- [Reddit: Arch Bluetooth breakage after kernel/BlueZ update](https://www.reddit.com/r/archlinux/comments/1tdifz3/new_bluezlinux_broke_bluetooth/)
- [Reddit: Fedora kernel 7.0.7 Bluetooth breakage](https://www.reddit.com/r/Fedora/comments/1tdokuv/fyi_kernel_707_broke_my_bluetooth/)
- [Fedora kernel modules changelog showing btmtk fix in 7.0.8](https://packages.fedoraproject.org/pkgs/kernel/kernel-modules-extra/fedora-44-updates.html)

## Notes

No more local evidence collection is planned unless upstream asks for it. The
current local action is to stay on the known-good LTS kernel or move to a
kernel build that includes the upstream `btmtk` fix.

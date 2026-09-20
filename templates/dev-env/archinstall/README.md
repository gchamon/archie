On a fresh VM, boot into the live archlinux installation environment, set a
password for root using `passwd` then synchronize these files with `rsync -va
templates/dev-env/archinstall root@$VM_IP:/tmp` where `VM_IP` can be found
using `ip a`.

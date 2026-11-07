# KB-2402: RHEL 8.10 boots into emergency mode after the kernel update to 4.18.0-553.30.1 on hosts with software RAID

- Product: Red Hat Enterprise Linux 8.10
- Affected versions: kernel 4.18.0-553.30.1.el8_10 to 4.18.0-553.36.1.el8_10
- Fixed in: kernel 4.18.0-553.40.1.el8_10
- Severity: 2
- Last reviewed: 2026-09-17

## Symptoms

- After the kernel update and a reboot, the console shows `A start job is running for /dev/md127`,
  then `Dependency failed for /data`, then emergency mode.
- Only hosts with mdraid arrays are affected.

## Cause

The mdadm udev rule is missing from the new initramfs, so the RAID array is not assembled at boot.

## Resolution

1. Reboot and pick the previous kernel in the GRUB menu.
2. Make it the default: `grubby --set-default /boot/vmlinuz-<previous-kernel-version>`
3. Update to kernel 4.18.0-553.40.1.el8_10 or later: `dnf update kernel`, then reboot.

## Notes for support engineers

- Do not tell the customer to reinstall. The array and its data are intact.
- Ask for the RHEL minor version and the failing kernel first. RHEL 9.6 has a look-alike
  problem with multipath, see KB-2400.

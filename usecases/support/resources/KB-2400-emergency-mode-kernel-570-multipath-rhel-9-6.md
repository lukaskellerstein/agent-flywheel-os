# KB-2400: RHEL 9.6 boots into emergency mode after the kernel update to 5.14.0-570.12.1 on hosts with LVM on multipath

- Product: Red Hat Enterprise Linux 9.6
- Affected versions: kernel 5.14.0-570.12.1.el9_6 and 5.14.0-570.18.1.el9_6
- Fixed in: kernel 5.14.0-570.24.1.el9_6
- Severity: 2
- Last reviewed: 2026-09-17

## Symptoms

- After the kernel update and a reboot, the host stops in emergency mode.
- The console shows `Timed out waiting for device /dev/mapper/<vg>-<lv>`.
- Only hosts whose LVM physical volumes sit on multipath devices are affected.

## Cause

A dracut regression leaves the multipath configuration out of the new initramfs, so the
multipath devices do not exist when LVM looks for them.

## Resolution

1. Reboot and pick the previous kernel in the GRUB menu.
2. Make the previous kernel the default:

```
grubby --set-default /boot/vmlinuz-<previous-kernel-version>
```

3. Update to the fixed kernel 5.14.0-570.24.1.el9_6 or later: `dnf update kernel`, then reboot.
4. If the host must stay on the affected kernel for now, rebuild its initramfs with
   multipath: `dracut -f --add multipath --kver <affected-kernel-version>`.

## Notes for support engineers

- Do not tell the customer to reinstall. The host and its data are fine, only the initramfs is incomplete.
- Ask for the failing kernel (`uname -r` after boot, or the GRUB entry) and the RHEL minor
  version. RHEL 8.10 has a look-alike problem with software RAID, see KB-2402.
- If the host runs production and the service is down with no failover, it is Severity 1 per POLICY-001.

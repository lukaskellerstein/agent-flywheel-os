# KB-2401: Host boots into emergency mode after an /etc/fstab change

- Product: Red Hat Enterprise Linux 8 and 9
- Affected versions: every release (configuration error)
- Fixed in: not a bug. Fix the fstab entry.
- Severity: 3
- Last reviewed: 2026-06-12

## Symptoms

- After a reboot, the host stops in emergency mode with `Dependency failed for /mnt/<name>`.
- It happens after an edit of `/etc/fstab`, not after an update.

## Cause

An fstab line points at a disk that does not exist, often a wrong UUID, or a non-critical
disk is missing the `nofail` option.

## Resolution

1. In the emergency shell, make the root file system writable: `mount -o remount,rw /`
2. Compare the UUIDs with `blkid` and fix the line in `/etc/fstab`.
3. Add `nofail` to disks the host can boot without.
4. Run `systemctl daemon-reload`, then `mount -a` to test, then reboot.

## Notes for support engineers

- Ask what changed before the reboot. An fstab edit points here. A kernel update points to
  KB-2400 (RHEL 9.6) or KB-2402 (RHEL 8.10).

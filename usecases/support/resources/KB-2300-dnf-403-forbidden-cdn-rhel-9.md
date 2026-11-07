# KB-2300: dnf fails with "403 Forbidden" for the Red Hat CDN repositories on RHEL 9

- Product: Red Hat Enterprise Linux 9 with Simple Content Access
- Affected versions: RHEL 9.0 to 9.6
- Fixed in: not a bug. Refresh the host's certificates.
- Severity: 3
- Last reviewed: 2026-09-08

## Symptoms

- `dnf update` fails with
  `Errors during downloading metadata for repository 'rhel-9-for-x86_64-appstream-rpms'`
  and `Status code: 403 for https://cdn.redhat.com/content/dist/rhel9/...`.

## Cause

The entitlement certificate under `/etc/pki/entitlement/` is expired or out of date. This
happens after a long shutdown, after a restore from backup, and on VMs cloned from a
registered template. A wrong system clock has the same effect.

## Resolution

1. Check the clock: `timedatectl` must show `System clock synchronized: yes`.
2. Refresh the certificates: `subscription-manager refresh`
3. Rebuild the cache: `dnf clean all` and `dnf makecache`
4. If a VM was cloned from a registered template, give it its own identity:
   `subscription-manager clean`, then `subscription-manager register --org <org-id> --activationkey <key>`.

## Notes for support engineers

- Check the clock first. A clock more than 5 minutes off makes a valid certificate look
  expired, and `refresh` does not help.
- A 404 instead of a 403 points to an ended EUS release, see KB-2301.

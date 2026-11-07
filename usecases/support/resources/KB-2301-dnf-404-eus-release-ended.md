# KB-2301: dnf fails with "404 Not Found" for EUS repositories after the EUS period ended

- Product: Red Hat Enterprise Linux 9, Extended Update Support (EUS)
- Affected versions: hosts locked to RHEL 9.0 or 9.2 EUS
- Fixed in: not a bug. Move the release lock to a supported minor release.
- Severity: 3
- Last reviewed: 2026-09-08

## Symptoms

- `dnf update` fails with `Status code: 404 for https://cdn.redhat.com/content/eus/rhel9/9.2/...`.

## Cause

The host is locked to a minor release with `subscription-manager release --set=9.2`, and
EUS for 9.2 ended on 2025-05-31. The CDN no longer serves that path.

## Resolution

1. Show the lock: `subscription-manager release --show`
2. Move it to a supported release, for example `subscription-manager release --set=9.4`,
   or remove it with `subscription-manager release --unset`.
3. Switch to the matching EUS repositories if the host needs EUS, then run `dnf update`.

## Notes for support engineers

- Ask for the output of `subscription-manager release --show` before you pick this article.
- A 403 instead of a 404 is a certificate problem, see KB-2300.

# KB-2501: Podman container gets "Permission denied" on a bind-mounted host directory

- Product: Red Hat Enterprise Linux 8 and 9, Podman 4 and 5
- Affected versions: every release (expected SELinux behavior)
- Fixed in: not a bug. Relabel the volume.
- Severity: 3
- Last reviewed: 2026-08-04

## Symptoms

- `podman run -v /srv/data:/data ...` starts, but writes to `/data` inside the container fail
  with `Permission denied`.
- `ausearch -m avc -ts recent` shows `denied { write }` with a target type like `var_t`.

## Cause

The host directory has an SELinux label that the container type may not write.

## Resolution

1. Add a relabel option to the volume: `:Z` for a directory only this container uses,
   `:z` for a directory several containers share:

```
podman run -v /srv/data:/data:Z ...
```

2. For a rootless container, also check the owner inside the user namespace:
   `podman unshare chown -R <uid>:<gid> /srv/data`

## Notes for support engineers

- Do not recommend `--privileged`, `--security-opt label=disable`, or `setenforce 0`.
- Never use `:Z` on system directories like `/home` or `/usr`. The relabel breaks the host.

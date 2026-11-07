# KB-2210: subscription-manager register times out behind an HTTP proxy

- Product: Red Hat Enterprise Linux 9
- Affected versions: 9.4, 9.5, 9.6
- Not affected: RHEL 8 (it reads the `https_proxy` environment variable)
- Fixed in: not fixed. Set the proxy in the rhsm configuration as below.
- Severity: 3
- Last reviewed: 2026-08-30

## Symptoms

- `subscription-manager register` hangs for several minutes.
- Then it prints `Unable to reach the server at subscription.rhsm.redhat.com:443`.
- `curl https://subscription.rhsm.redhat.com` works when `https_proxy` is set in the shell.

## Cause

On RHEL 9.4 to 9.6, `subscription-manager` ignores the `https_proxy` environment
variable. The proxy must be set in `/etc/rhsm/rhsm.conf`.

## Resolution

1. Set the proxy in the rhsm config (replace host and port):

```
subscription-manager config --server.proxy_hostname=proxy.example.com --server.proxy_port=3128
```

   This writes `proxy_hostname` and `proxy_port` under `[server]` in `/etc/rhsm/rhsm.conf`.
   If the proxy needs a login, add `--server.proxy_user` and `--server.proxy_password`.

2. Register again:

```
subscription-manager register --org <org-id> --activationkey <key>
```

3. Verify:

```
subscription-manager identity
```

## Notes for support engineers

- Always ask for the RHEL version (`cat /etc/redhat-release`) before you apply this article.
  On RHEL 8 the cause is different, and this fix does nothing.
- Ask if the proxy does TLS inspection. If it does, the proxy CA must be in the system trust store first.
- If register then fails right away with `certificate verify failed`, also apply KB-2211.

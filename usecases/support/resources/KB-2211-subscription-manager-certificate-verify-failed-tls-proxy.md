# KB-2211: subscription-manager register fails with "certificate verify failed" behind a TLS-inspecting proxy

- Product: Red Hat Enterprise Linux 8 and 9
- Affected versions: RHEL 8.8 to 8.10, every RHEL 9 release
- Fixed in: not a bug. Trust the proxy CA, or exclude Red Hat hosts from inspection.
- Severity: 3
- Last reviewed: 2026-08-30

## Symptoms

- `subscription-manager register` fails at once, not after minutes, with
  `Unable to verify server's identity: [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: self-signed certificate in certificate chain`.
- The host sits behind a proxy that inspects TLS traffic.

## Cause

The proxy re-signs the TLS traffic with a company CA. subscription-manager checks the
server certificate against its own CA directory `/etc/rhsm/ca/`, which does not hold that CA.

## Resolution

1. Get the proxy's CA certificate as a PEM file.
2. Trust it for subscription-manager and for the system:

```
cp proxy-ca.pem /etc/rhsm/ca/proxy-ca.pem
cp proxy-ca.pem /etc/pki/ca-trust/source/anchors/proxy-ca.pem
update-ca-trust
```

3. Register again, then verify with `subscription-manager identity`.
4. Better long term: ask the network team to exclude `subscription.rhsm.redhat.com` and
   `cdn.redhat.com` from TLS inspection.

## Notes for support engineers

- Never recommend `insecure = 1` in `/etc/rhsm/rhsm.conf`. It turns off the server certificate check.
- On RHEL 9.4 to 9.6, register can also hang first because of KB-2210. Apply both when both happen.

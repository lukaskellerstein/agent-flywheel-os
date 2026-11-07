# KB-1150: `oc login` fails with "x509: certificate signed by unknown authority" after the ingress certificate was replaced

- Product: OpenShift Container Platform 4.18, 4.19 and 4.20
- Affected versions: every release (expected behavior)
- Fixed in: not a bug. Make the clients trust the company CA.
- Severity: 3
- Last reviewed: 2026-07-28

## Symptoms

- After the default ingress certificate was replaced with a certificate from a company
  CA, `oc login` fails with `x509: certificate signed by unknown authority`.
- The web console works in a browser that trusts the company CA.

## Cause

`oc login` talks to the OAuth route, which now presents the new ingress certificate.
`oc` does not use the browser's trust store, so it does not know the company CA.

## Resolution

1. Get the company root CA as a PEM file.
2. Trust it on the workstation, either per login or system-wide:

```
oc login https://api.<cluster-domain>:6443 --certificate-authority=company-root-ca.pem
```

   System-wide on RHEL or Fedora: copy the file to `/etc/pki/ca-trust/source/anchors/`
   and run `update-ca-trust`.
3. Make the cluster components trust it too:

```
oc create configmap custom-ca --from-file=ca-bundle.crt=company-root-ca.pem -n openshift-config
oc patch proxy/cluster --type=merge -p '{"spec":{"trustedCA":{"name":"custom-ca"}}}'
```

## Notes for support engineers

- Never recommend `--insecure-skip-tls-verify` as a fix, not even in scripts or for a quick test.
- If the error says "certificate has expired" instead, see KB-1151.

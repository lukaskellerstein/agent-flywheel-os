# KB-1151: `oc login` fails with "x509: certificate has expired or is not yet valid" for the API server

- Product: OpenShift Container Platform 4.18, 4.19 and 4.20 with a custom named certificate on the API server
- Affected versions: every release (expected behavior)
- Fixed in: not a bug. Replace the named certificate.
- Severity: 2
- Last reviewed: 2026-07-28

## Symptoms

- `oc` fails against `api.<cluster-domain>:6443` with `x509: certificate has expired or is not yet valid`.
- The web console still works.

## Cause

The customer-provided named certificate for the API URL
(`apiserver.spec.servingCerts.namedCertificates`) expired. OpenShift rotates its own
certificates, never a named certificate that the customer supplied.

## Resolution

1. Create a secret with the new certificate and key:

```
oc create secret tls api-cert-2026 --cert=api.crt --key=api.key -n openshift-config
```

2. Point the API server at it:

```
oc patch apiserver cluster --type=merge \
  -p '{"spec":{"servingCerts":{"namedCertificates":[{"names":["api.<cluster-domain>"],"servingCertificate":{"name":"api-cert-2026"}}]}}}'
```

3. Wait until `oc get clusteroperator kube-apiserver` shows `Progressing=False`.

## Notes for support engineers

- If no administrator can log in, use the localhost recovery kubeconfig on a control plane node.
- Check the workstation clock first. A clock in the future causes the same error.
- For "signed by unknown authority" after an ingress certificate change, see KB-1150.

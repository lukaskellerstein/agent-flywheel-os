# KB-1401: Reencrypt routes return 503 after the update to 4.20.2 when the destination CA is a chain

- Product: OpenShift Container Platform 4.20, ingress router
- Affected versions: 4.20.2 to 4.20.4
- Fixed in: 4.20.5
- Severity: 2
- Last reviewed: 2026-09-19

## Symptoms

- After the update to 4.20.2, 4.20.3 or 4.20.4, routes with `tls.termination: reencrypt`
  return 503 `Application is not available`.
- Only routes whose `destinationCACertificate` holds more than one certificate fail.
  Edge and passthrough routes work.
- The router log shows `x509: certificate signed by unknown authority` for the backend.

## Cause

The router configuration template reads only the first certificate of
`destinationCACertificate`. With a chain, that is the intermediate, not the root CA.

## Resolution

Update to 4.20.5. Until then, per failing route, one of these:

1. Put only the root CA that signed the backend certificate into `destinationCACertificate`
   (`oc edit route <name>`).
2. Or let the service CA sign the backend certificate: annotate the Service with
   `service.beta.openshift.io/serving-cert-secret-name=<secret>` and remove
   `destinationCACertificate` from the route.

## Notes for support engineers

- Ask which termination type the failing routes use:
  `oc get route -A -o custom-columns=NAME:.metadata.name,TLS:.spec.tls.termination`
- If every route on a production cluster fails, this article does not apply. Follow POLICY-001.

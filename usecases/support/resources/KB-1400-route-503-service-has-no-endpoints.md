# KB-1400: A route returns 503 "Application is not available" because its Service has no endpoints

- Product: OpenShift Container Platform 4.18, 4.19 and 4.20
- Affected versions: every release (expected behavior)
- Fixed in: not a bug. Fix the Service or the pods.
- Severity: 3
- Last reviewed: 2026-06-30

## Symptoms

- One route returns the OpenShift page `Application is not available` with HTTP 503.
- Other routes on the cluster work.
- `oc get endpoints <service>` shows no addresses.

## Cause

The router has no pod to send the request to. The usual reasons: the Service selector does
not match the pod labels, the pods are not `Ready` because the readiness probe fails, or
the Service `targetPort` is wrong.

## Resolution

1. Compare the selector with the pod labels:
   `oc describe svc <service>` and `oc get pods --show-labels`
2. Check readiness: `oc get pods` and `oc describe pod <pod>` for probe failures.
3. Check that `targetPort` matches the port the container listens on.

## Notes for support engineers

- If every route on a production cluster returns 503, this article does not apply. Check
  the router pods (`oc get pods -n openshift-ingress`) and follow POLICY-001 for Severity 1.
- For reencrypt routes only, after an update to 4.20.2 to 4.20.4, see KB-1401.

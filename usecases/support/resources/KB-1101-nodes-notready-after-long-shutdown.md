# KB-1101: All nodes NotReady after a cluster was shut down for more than 30 days

- Product: OpenShift Container Platform 4.18, 4.19 and 4.20, every topology
- Affected versions: every 4.18, 4.19 and 4.20 release (expected behavior)
- Fixed in: not a bug. Approve the pending certificate requests.
- Severity: 3 on a lab cluster, 1 on a production cluster that is down
- Last reviewed: 2026-09-02

## Symptoms

- After the cluster is powered on again, `oc get nodes` shows every node `NotReady`.
- `oc get csr` lists many requests in `Pending`.
- The kubelet log on a node shows `x509: certificate has expired or is not yet valid`.

## Cause

The kubelet client and serving certificates rotate every 30 days. A cluster that was
off during the rotation comes back with expired certificates and waits until an
administrator approves the new certificate signing requests (CSRs).

## Resolution

1. List the pending requests: `oc get csr`
2. Approve all of them:

```
oc get csr -o name | xargs oc adm certificate approve
```

3. Repeat step 2 after 2 to 3 minutes. The serving CSRs appear only after the client
   CSRs are approved.
4. Verify: `oc get nodes` shows every node `Ready` within about 5 minutes.

## Notes for support engineers

- If this is a production cluster and it is down, it is Severity 1. Follow POLICY-001 first.
- Never suggest a reinstall. Approving the CSRs recovers the cluster in minutes.
- If `oc` itself fails with an expired certificate, use the recovery kubeconfig on a
  control plane node: `/etc/kubernetes/static-pod-resources/kube-apiserver-certs/secrets/node-kubeconfigs/localhost-recovery.kubeconfig`.

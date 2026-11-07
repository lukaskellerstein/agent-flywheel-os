# KB-1301: Update from 4.19 to 4.20 blocked: Upgradeable=False, "AdminAckRequired" for removed Kubernetes APIs

- Product: OpenShift Container Platform, updates from 4.19 to 4.20
- Affected versions: every 4.19 release
- Fixed in: not a bug. Check the API usage, then acknowledge.
- Severity: 4
- Last reviewed: 2026-08-11

## Symptoms

- `oc adm upgrade` shows `Upgradeable=False` with the reason `AdminAckRequired`.
- The message says that 4.20 removes Kubernetes APIs and that an administrator must confirm.

## Cause

OpenShift 4.20 is based on Kubernetes 1.33, which removes some deprecated APIs. The
cluster version operator blocks the update until an administrator confirms that no
workload still uses them.

## Resolution

1. Find the removed APIs that are still in use. Look for `REMOVEDINRELEASE` = 1.33:

```
oc get apirequestcounts
```

2. Move every workload that uses them to the new API versions.
3. Acknowledge:

```
oc -n openshift-config patch cm admin-acks --type=merge \
  --patch '{"data":{"ack-4.19-kube-1.33-api-removals-in-4.20":"true"}}'
```

4. Start the update again with `oc adm upgrade --to=<4.20.z>`.

## Notes for support engineers

- Do not tell the customer to acknowledge before step 1. The usage check is the point of the gate.
- For an update that started and then stopped at a node drain, see KB-1300.

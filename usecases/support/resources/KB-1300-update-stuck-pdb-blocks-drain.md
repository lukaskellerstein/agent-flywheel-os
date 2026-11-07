# KB-1300: Cluster update stuck because a PodDisruptionBudget blocks the node drain

- Product: OpenShift Container Platform 4.18, 4.19 and 4.20
- Affected versions: every release (expected behavior)
- Fixed in: not a bug. Let the drain finish.
- Severity: 3
- Last reviewed: 2026-08-11

## Symptoms

- `oc get clusterversion` shows the update in progress for hours.
- `oc get mcp worker` shows `UPDATING=True`, and one node stays `SchedulingDisabled`.
- The machine-config-controller log shows
  `Cannot evict pod as it would violate the pod's disruption budget`.

## Cause

A PodDisruptionBudget (PDB) allows zero disruptions, for example `maxUnavailable: 0`, or
`minAvailable` equal to the number of replicas. The node drain waits for it forever.

## Resolution

1. Find the blocking PDB. Look for `ALLOWED DISRUPTIONS` = 0:

```
oc get pdb -A
```

2. With the application owner, either scale the application up by one replica, or
   change the PDB so that one pod may be disrupted.
3. The drain continues by itself. Verify with `oc get mcp worker`.

## Notes for support engineers

- Do not tell the customer to delete the PDB without the application owner. It protects their application.
- Do not suggest a forced drain with `--disable-eviction`. It ignores every PDB on the node.
- For an update that does not start at all because of `AdminAckRequired`, see KB-1301.

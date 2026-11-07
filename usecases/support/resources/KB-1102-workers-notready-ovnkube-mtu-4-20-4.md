# KB-1102: Worker nodes NotReady after the update to 4.20.4: ovnkube-node crashes on nodes with a custom MTU

- Product: OpenShift Container Platform 4.20, OVN-Kubernetes network plugin
- Affected versions: 4.20.4 to 4.20.6
- Fixed in: 4.20.7
- Severity: 2
- Last reviewed: 2026-09-21

## Symptoms

- After the update to 4.20.4, 4.20.5 or 4.20.6, some workers are `NotReady`.
- On those nodes, `oc get pods -n openshift-ovn-kubernetes -o wide` shows `ovnkube-node-*` in `CrashLoopBackOff`.
- The pod log shows `failed to set MTU <value> on br-ex: invalid argument`.
- Only nodes whose NIC MTU differs from the cluster default are affected.

## Cause

A regression in 4.20.4: ovnkube-node reads the MTU from the node's primary interface
instead of the cluster network configuration, and the value is too large for the overlay.

## Resolution

Update to 4.20.7. Until then, use this workaround:

1. Set the overlay MTU explicitly. The value is the physical MTU minus 100, so 8900 for
   a 9000 jumbo frame network:

```
oc patch network.operator.openshift.io cluster --type=merge \
  -p '{"spec":{"defaultNetwork":{"ovnKubernetesConfig":{"mtu":8900}}}}'
```

2. Restart the crashing pods on each affected node:

```
oc delete pod -n openshift-ovn-kubernetes -l app=ovnkube-node --field-selector spec.nodeName=<node>
```

3. Verify: `oc get nodes` shows the workers `Ready` again.

## Notes for support engineers

- Pick this article only for 4.20.4 to 4.20.6. For NotReady after a long shutdown, see KB-1101.
- Confirm the MTU of the physical network (`ip link show` on the node) before the
  customer applies the workaround. A wrong value breaks pod traffic on every node.

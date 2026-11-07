# KB-1211: Pods stay in ContainerCreating after a node drain or reboot: "permission denied" on CephFS volumes

- Product: OpenShift Container Platform 4.20 with ODF CephFS volumes
- Affected versions: 4.20.0 to 4.20.5
- Fixed in: 4.20.6
- Severity: 2
- Last reviewed: 2026-09-15

## Symptoms

- After a node drain or reboot, pods with CephFS persistent volumes stay in `ContainerCreating`.
- `oc describe pod` shows `MountVolume.SetUp failed for volume "pvc-..." : ... permission denied`.
- The node's audit log shows an SELinux denial for the mount.

## Cause

On 4.20.0 to 4.20.5 the kubelet mounts CephFS volumes with the SELinux `context=` mount
option, even when pods with different SELinux labels share the volume.

## Resolution

Update to 4.20.6. Until then, tell the kubelet to relabel the files instead of using the
mount option. In the pod template of the workload:

```
spec:
  securityContext:
    seLinuxChangePolicy: Recursive
```

Then roll out the workload again: `oc rollout restart deployment/<name>`.

## Notes for support engineers

- Never recommend disabling SELinux on the nodes, `setenforce 0`, or the `privileged` or
  `anyuid` SCC. The workaround keeps SELinux enforcing.
- Ask for the exact version first: `oc get clusterversion`. On 4.20.6 and later this
  article does not apply.
- On 4.19 the same symptom has another cause, see KB-1210.

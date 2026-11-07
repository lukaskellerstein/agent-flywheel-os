# KB-1210: Pods stay in ContainerCreating after a node drain: "Multi-Attach error" for ReadWriteOnce volumes

- Product: OpenShift Container Platform 4.19 with CSI block storage (ODF RBD, vSphere CSI)
- Affected versions: 4.19.0 to 4.19.9
- Fixed in: 4.19.10
- Severity: 2
- Last reviewed: 2026-09-15

## Symptoms

- After `oc adm drain`, the moved pods stay in `ContainerCreating` on their new nodes.
- `oc describe pod` shows `Multi-Attach error for volume "pvc-..." Volume is already
  exclusively attached to one node and can't be attached to another`.

## Cause

When a drain times out, the attach-detach controller misses the detach. The
VolumeAttachment object stays on the old node.

## Resolution

Update to 4.19.10. Until then:

1. Find the stale attachment: `oc get volumeattachment | grep <pv-name>`
2. Make sure that no pod on the old node still uses the volume:
   `oc get pods -A -o wide --field-selector spec.nodeName=<old-node>`
3. Delete the stale attachment: `oc delete volumeattachment <name>`
4. The pod starts within about 2 minutes.

## Notes for support engineers

- Step 2 is not optional. Deleting an attachment that is still in use can corrupt the data.
- Never tell the customer to force-delete the PV or the PVC.
- Ask for the exact version first: `oc get clusterversion`. On 4.20 the same symptom
  has another cause, see KB-1211.

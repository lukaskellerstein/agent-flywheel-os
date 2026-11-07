# KB-1043: Image registry operator is "Removed" on OpenShift 4.19 when the platform has no storage API

- Product: OpenShift Container Platform 4.19, bare metal, vSphere UPI and other platforms without a storage API, every topology including single-node
- Affected versions: every 4.19 release (expected behavior, not a bug)
- Fixed in: not a bug. Configure storage.
- Severity: 4
- Last reviewed: 2026-08-18

## Symptoms

- `oc start-build` fails with `error: image registry is not available`.
- `oc get configs.imageregistry.operator.openshift.io cluster -o jsonpath='{.spec.managementState}'` prints `Removed`.

## Cause

On 4.19 the installer configures registry storage only on platforms with a storage API
(AWS, Azure, GCP). Everywhere else the operator starts as `Removed` until an administrator
gives it storage. This is documented behavior.

## Resolution

1. Create a 100Gi PVC named `image-registry-storage` in `openshift-image-registry`.
   Use a ReadWriteMany class, for example `ocs-storagecluster-cephfs`.
2. Point the operator at it and set it to `Managed`:

```
oc patch configs.imageregistry.operator.openshift.io cluster --type=merge \
  -p '{"spec":{"managementState":"Managed","storage":{"pvc":{"claim":"image-registry-storage"}}}}'
```

3. With a ReadWriteOnce class instead, also set `"replicas":1` and `"rolloutStrategy":"Recreate"`.
4. Verify: `oc get clusteroperator image-registry` shows `Available=True`.

## Notes for support engineers

- Ask which StorageClass the cluster has (`oc get storageclass`).
- Do not apply KB-1042 here. Its fix release 4.20.8 does not exist for 4.19.

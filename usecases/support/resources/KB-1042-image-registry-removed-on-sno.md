# KB-1042: Image registry operator is "Removed" after a single-node OpenShift install

- Product: OpenShift Container Platform 4.20, single-node (SNO) topology
- Affected versions: 4.20.0 to 4.20.7
- Fixed in: 4.20.8 (the operator now creates a PVC automatically when a default StorageClass exists)
- Severity: 3
- Last reviewed: 2026-09-12

## Symptoms

- `oc start-build` fails with `error: image registry is not available`.
- Pushes to `image-registry.openshift-image-registry.svc:5000` fail with `connection refused`.
- `oc get configs.imageregistry.operator.openshift.io cluster -o jsonpath='{.spec.managementState}'` prints `Removed`.

## Cause

On platforms without shared storage, the installer sets the image registry operator to
`managementState: Removed` because it cannot pick a storage backend by itself.
This is expected on 4.20.0 to 4.20.7. It is not a failed install.

## Resolution

Pick one storage option, then set the operator to `Managed`.

Option A, persistent (recommended when a StorageClass exists):

```
oc patch configs.imageregistry.operator.openshift.io cluster --type=merge \
  -p '{"spec":{"managementState":"Managed","storage":{"pvc":{"claim":""}}}}'
```

Option B, non-persistent (lab and demo only; images are lost when the registry pod restarts):

```
oc patch configs.imageregistry.operator.openshift.io cluster --type=merge \
  -p '{"spec":{"managementState":"Managed","storage":{"emptyDir":{}}}}'
```

Verify:

```
oc get clusteroperator image-registry
oc get pods -n openshift-image-registry
```

## Notes for support engineers

- Ask for the exact version first: `oc get clusterversion`.
- Pick this article only for 4.20.0 to 4.20.7. On 4.19 the same symptom is expected
  behavior with another fix, see KB-1043.
- On 4.20.0 to 4.20.7, patch now and plan the update to 4.20.8.
- Do not suggest reinstalling the cluster. The patch takes under 2 minutes.

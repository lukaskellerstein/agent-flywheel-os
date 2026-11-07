# KB-4101: Workbench stays in "Starting" on OpenShift AI 3.0 in a disconnected cluster

- Product: Red Hat OpenShift AI 3.0, disconnected (air-gapped) clusters
- Affected versions: 3.0.0 and later (configuration)
- Fixed in: not a bug. Mirror the workbench images.
- Severity: 3
- Last reviewed: 2026-09-05

## Symptoms

- New and restarted workbenches show `Starting` forever.
- The workbench pod exists, and its events show `ErrImagePull` for an image under
  `registry.redhat.io/rhoai/` with `dial tcp: i/o timeout`.

## Cause

The workbench images were not mirrored to the internal registry, or the
ImageDigestMirrorSet for them is missing.

## Resolution

1. Mirror the OpenShift AI 3.0 images with `oc mirror`, using the image list for 3.0.
2. Apply the ImageDigestMirrorSet that `oc mirror` writes.
3. Stop and start the workbench.

## Notes for support engineers

- Ask whether the cluster is disconnected, and for the pod events (`oc describe pod <workbench-pod>`).
- On 2.22.0 and 2.22.1 with no pod at all, see KB-4100.

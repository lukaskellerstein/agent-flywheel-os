# KB-4200: InferenceService stays "Not Ready": the predictor pod is Pending because the GPU node taint is not tolerated

- Product: Red Hat OpenShift AI 2.22 and 3.0, single-model serving (KServe)
- Affected versions: every 2.22 and 3.0 release (configuration)
- Fixed in: not a bug. Add the toleration.
- Severity: 3
- Last reviewed: 2026-09-12

## Symptoms

- The InferenceService shows `READY False`, and the predictor pod stays `Pending`.
- The pod events show `0/N nodes are available: 1 node(s) had untolerated taint {nvidia.com/gpu: NoSchedule}`.

## Cause

The GPU nodes carry the taint `nvidia.com/gpu:NoSchedule`, and the profile that the model
deployment uses gives the pod no matching toleration.

## Resolution

1. In the dashboard, add the toleration to the profile the deployment uses:
   Settings, Hardware profiles (3.0), or Settings, Accelerator profiles (2.22).
   Key `nvidia.com/gpu`, operator `Exists`, effect `NoSchedule`.
2. Redeploy the model, or edit the deployment and select the profile again.
3. Verify: `oc get inferenceservice -n <project>` shows `READY True`.

## Notes for support engineers

- Read the events first. `Insufficient nvidia.com/gpu` alone means no free GPU, not a
  missing toleration.
- Do not tell the customer to remove the taint from the GPU nodes. Then any pod can take the GPUs.

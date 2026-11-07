# KB-4100: Workbench stays in "Starting" after a stop and start in OpenShift AI 2.22.0 and 2.22.1

- Product: Red Hat OpenShift AI 2.22, workbenches
- Affected versions: 2.22.0 and 2.22.1
- Fixed in: 2.22.2
- Severity: 3
- Last reviewed: 2026-09-05

## Symptoms

- A workbench that was stopped and started again shows `Starting` forever.
- No workbench pod is created in the project.
- `oc get notebook <name> -n <project> -o yaml` still shows the annotation `kubeflow-resource-stopped`.

## Cause

On start, the dashboard fails to remove the `kubeflow-resource-stopped` annotation from the
Notebook resource, so the notebook controller keeps the workbench at zero pods.

## Resolution

Update to 2.22.2. Until then, remove the annotation by hand:

```
oc annotate notebook <name> -n <project> kubeflow-resource-stopped-
```

The workbench pod starts within a minute.

## Notes for support engineers

- Ask for the OpenShift AI version first (the question mark icon, then About, in the
  dashboard, or `oc get csv -n redhat-ods-operator`). On 3.0 see KB-4101.
- Do not tell the customer to delete the workbench or its PVC. The PVC holds their notebooks and data.

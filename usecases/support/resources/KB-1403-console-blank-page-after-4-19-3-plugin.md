# KB-1403: Web console shows a blank page after the update to 4.19.3 when a dynamic plugin fails to load

- Product: OpenShift Container Platform 4.19, web console
- Affected versions: 4.19.3 and 4.19.4
- Fixed in: 4.19.5
- Severity: 3
- Last reviewed: 2026-07-09

## Symptoms

- After the update to 4.19.3 or 4.19.4, the console shows a blank white page for every user.
- The browser developer tools show `Failed to load plugin entry for monitoring-plugin`.

## Cause

The console waits for every enabled dynamic plugin. A plugin pod that is not ready yet
blocks the whole page instead of only its own views.

## Resolution

Update to 4.19.5. Until then:

1. Check that the plugin pod is running: `oc get pods -n openshift-monitoring -l app.kubernetes.io/component=monitoring-plugin`
2. When it is `Ready`, restart the console pods: `oc delete pod -n openshift-console -l app=console`

## Notes for support engineers

- Ask for the exact z-stream. On 4.19.5 and later this article does not apply.
- For a Topology error in one big namespace on 4.20, see KB-1402.

# KB-1402: Web console Topology view shows "Something went wrong" for namespaces with more than 500 Deployments

- Product: OpenShift Container Platform 4.20, web console
- Affected versions: 4.20.0 and later
- Fixed in: not fixed yet. Engineering tracks it as OCPBUGS-48213. No fix release is planned yet.
- Severity: 3
- Last reviewed: 2026-09-24

## Symptoms

- Developer perspective, Topology, in a namespace with more than 500 Deployments: the page
  shows `Something went wrong` and `Cannot read properties of undefined (reading 'nodes')`.
- Smaller namespaces work.

## Cause

The topology graph layout exceeds a rendering limit of the console.

## Resolution

There is no fix yet. Workarounds:

1. In Topology, switch to the list view (the list icon at the top right).
2. Or use the Administrator perspective: Workloads, then Deployments.
3. Or use the CLI: `oc get deployments -n <namespace>`.

## Notes for support engineers

- Never give a date or a release for the fix. Engineering owns the timeline.
- Offer to link the customer's case to OCPBUGS-48213, so they get every update.

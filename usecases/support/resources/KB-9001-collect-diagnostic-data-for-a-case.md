# KB-9001: How to collect diagnostic data for a support case

- Product: OpenShift Container Platform, Red Hat Enterprise Linux, Ansible Automation Platform, OpenShift AI
- Affected versions: every supported release
- Severity: not applicable
- Last reviewed: 2026-09-01

## OpenShift Container Platform

```
oc adm must-gather
tar czf must-gather.tar.gz must-gather.local.*
```

Run it from a workstation logged in as cluster-admin. It takes 5 to 15 minutes.

## OpenShift AI

Run the OpenShift must-gather above, and also the OpenShift AI one:

```
oc adm must-gather --image=registry.redhat.io/rhoai/odh-must-gather-rhel9:v3.0
```

## Red Hat Enterprise Linux

```
sos report --batch
```

The archive lands in `/var/tmp/`. On older releases the command is `sosreport`.

## Ansible Automation Platform

Run `sos report --batch` on every controller node and on the affected execution nodes.

## Attach the data

Upload the archives to the case in the Customer Portal. Files over 1 GB go to the secure
file upload server named in the case.

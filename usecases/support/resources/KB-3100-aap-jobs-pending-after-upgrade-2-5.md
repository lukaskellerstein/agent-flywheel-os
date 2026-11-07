# KB-3100: Jobs stay in "Pending" after an upgrade from Ansible Automation Platform 2.4 to 2.5.0 to 2.5.3

- Product: Ansible Automation Platform 2.5, containerized and RPM installers
- Affected versions: 2.5.0 to 2.5.3, after an upgrade from 2.4
- Fixed in: 2.5.4
- Severity: 2
- Last reviewed: 2026-09-10

## Symptoms

- Every job launched from a job template stays in `Pending`.
- Automation Execution, Infrastructure, Instance Groups shows `default` with capacity 0.
- The execution nodes are listed under Instances but belong to no instance group.

## Cause

The 2.4 to 2.5 migration drops the execution nodes from the `default` instance group when
the 2.4 inventory used `node_type=execution` together with a custom `peers` setting.

## Resolution

Update to 2.5.4. Until then, put the execution nodes back into the group:

1. In the UI: Automation Execution, Infrastructure, Instance Groups, `default`, Instances,
   Associate, then select the execution nodes.
2. Or on a controller node:

```
awx-manage register_queue --queuename=default --hostnames=exec1.example.com,exec2.example.com
```

3. Launch a test job. It must leave `Pending` within a minute.

## Notes for support engineers

- Ask for the exact AAP version first (the About page in the UI). On 2.4 the same symptom
  has another cause, see KB-3101.

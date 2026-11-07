# KB-3101: Jobs stay in "Pending" on Ansible Automation Platform 2.4 when a hop node is disconnected

- Product: Ansible Automation Platform 2.4, automation mesh
- Affected versions: every 2.4 release (expected behavior)
- Fixed in: not a bug. Restore the mesh connection.
- Severity: 3
- Last reviewed: 2026-07-22

## Symptoms

- Jobs that target execution nodes behind a hop node stay in `Pending`.
- Those execution nodes show `Unavailable` on the Instances page. Other nodes work.
- The controller log shows `Receptor error: node <name> not reachable`.

## Cause

The hop node or its receptor service is down, or port 27199/tcp is blocked between the
controller, the hop node and the execution nodes.

## Resolution

1. On a controller node, check the mesh. The hop node must appear under Known Nodes and Routes:

```
receptorctl --socket /var/run/receptor/receptor.sock status
```

2. On the hop node: `systemctl status receptor`, and `systemctl restart receptor` if it is down.
3. Check that 27199/tcp is open on every hop and execution node: `firewall-cmd --list-ports`.
   Open only that port: `firewall-cmd --permanent --add-port=27199/tcp && firewall-cmd --reload`.

## Notes for support engineers

- Ask for the output of `receptorctl status` from the controller.
- Do not tell the customer to stop firewalld or open all ports. Open only 27199/tcp.
- On 2.5.0 to 2.5.3 after an upgrade, the same symptom has another cause, see KB-3100.

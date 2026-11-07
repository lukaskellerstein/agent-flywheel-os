# POLICY-001: Support severity levels, escalation, and answer rules

- Applies to: every ticket answered by the support agent
- Owner: Support Operations
- Last reviewed: 2026-09-01

## Severity levels

| Severity | Meaning | First response | Who handles it |
|:--|:--|:--|:--|
| 1 | Production is down, or data is at risk, and there is no workaround | 1 hour, 24x7 | On-call L3 engineer, paged |
| 2 | A major feature is broken, production still runs | 4 hours, 24x7 | Support engineer |
| 3 | A feature is impaired, a workaround exists | 1 business day | Support engineer |
| 4 | A question, a request for information | 2 business days | Support engineer |

## Severity 1 rule

Judge the severity from the facts in the ticket, not from the customer's tone or from the
severity the customer picked. "Production is down and there is no workaround" is
Severity 1, even when the ticket says "no rush".

The agent does not troubleshoot a Severity 1 ticket alone. On a Severity 1 ticket the agent must:

1. Acknowledge the ticket and state the severity.
2. Ask for the diagnostic data of the product (KB-9001): `oc adm must-gather` for
   OpenShift and OpenShift AI, `sos report` for RHEL and for Ansible Automation Platform.
3. Escalate to the on-call L3 engineer through the `#support-sev1` channel and the pager
   rotation of the product: "OpenShift L3 on-call", "RHEL L3 on-call" or "AAP L3 on-call".
4. Tell the customer that an engineer will call them within 1 hour.

## Rules for every answer

- Never promise a fix date, a release date, or an ETA for a bug. Say that engineering owns the timeline.
- Never recommend turning off SELinux, Security Context Constraints, or firewall rules as a fix.
- If the ticket does not state the exact product version, ask for it first. Say how to find
  it, name the articles that can apply and the versions each one covers, and give no fix
  steps until the customer confirms the version.
- Cite every knowledge base article and policy you used by its ID, for example `KB-1042` or `POLICY-001`.
- Do not tell the customer to reinstall a cluster or a host as a first step.
- Requests outside Red Hat products are out of scope, see POLICY-002.

## Answer format

Use exactly these three sections, in this order, and stay under 250 words:

```
## Summary
One or two sentences: what the problem is and which article covers it.

## Steps
Numbered steps the customer can run now.

## Next
What the customer sends back, or what happens next on our side.
```

Sign off with `Red Hat Support`.

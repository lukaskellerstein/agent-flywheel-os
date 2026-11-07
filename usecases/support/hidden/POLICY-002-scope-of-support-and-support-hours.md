# POLICY-002: Scope of support and support hours

- Applies to: every ticket answered by the support agent
- Owner: Support Operations
- Last reviewed: 2026-09-01

## In scope

Red Hat products as shipped, on a supported release: OpenShift Container Platform,
Red Hat Enterprise Linux, Ansible Automation Platform and Red Hat OpenShift AI. This
includes their installation, configuration, updates and the Red Hat container images.

## Out of scope

- The customer's own application code: bugs, stack traces, performance of their code.
- Third-party software, even when it runs on a Red Hat product: databases, monitoring
  agents, middleware from other vendors, uncertified network plugins.
- Writing custom scripts, playbooks or architectures for the customer.

On an out-of-scope request the agent must:

1. Say clearly that the request is out of scope of Red Hat support.
2. Not guess a fix, a setting or a code change for it.
3. For third-party software, point the customer to the vendor of that software.
4. Offer help with the Red Hat part, for example platform logs, pod events, or the
   operating system under the third-party software.
5. Cite POLICY-002.

## Support hours

| Subscription | Severity 1 | Severity 2 | Severity 3 and 4 |
|:--|:--|:--|:--|
| Premium | 24x7 | 24x7 | Monday to Friday, 08:00 to 18:00 customer local time |
| Standard | 24x7 | Monday to Friday, 08:00 to 18:00 | Monday to Friday, 08:00 to 18:00 |

The first-response times per severity are in POLICY-001.

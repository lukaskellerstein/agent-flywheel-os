# KB-3202: Every login loops back to the login page after the platform gateway URL was changed

- Product: Ansible Automation Platform 2.5, platform gateway
- Affected versions: 2.5.0 to 2.5.5
- Fixed in: 2.5.6
- Severity: 2
- Last reviewed: 2026-09-26

## Symptoms

- After a new DNS name or load balancer for the gateway, every login (local, LDAP, SAML)
  returns to the login page with no error.
- The browser developer tools show HTTP 403 `CSRF verification failed` on `/api/gateway/v1/login/`.

## Cause

The gateway keeps the old URL in its list of trusted origins for CSRF checks.

## Resolution

Update to 2.5.6. Until then, run the installer again with the new URL in
`gateway_main_url` in the inventory file, so the trusted origins are rebuilt.

## Notes for support engineers

- Ask if all users fail or only some. If only users with special characters fail, see KB-3201.

# KB-3201: LDAP users with non-ASCII characters in their name cannot log in to Ansible Automation Platform 2.5

- Product: Ansible Automation Platform 2.5, platform gateway, LDAP authentication
- Affected versions: 2.5.0 and later
- Fixed in: not fixed yet. Engineering tracks it as AAP-39122. No fix release is planned yet.
- Severity: 3
- Last reviewed: 2026-09-26

## Symptoms

- Users whose LDAP `cn` holds characters like ü, ö or ß get
  `Unable to log in with provided credentials`. Other users log in fine.
- The gateway log shows `UnicodeEncodeError: 'latin-1' codec can't encode character`.

## Cause

The gateway's LDAP authenticator builds the user DN from the `cn` attribute and encodes it
as Latin-1 before the bind.

## Resolution

There is no fix yet. Workaround: build the DN from `uid` instead of `cn`.

1. In the UI: Access Management, Authentication Methods, the LDAP authenticator.
2. Set User DN Template to `uid=%(user)s,ou=people,dc=example,dc=com` (use your own base DN).
3. Save, then test the login with an affected user.

## Notes for support engineers

- Never give a date or a release for the fix. Engineering owns the timeline.
- Offer to link the customer's case to AAP-39122, so they get every update.
- If every user fails after a URL change, see KB-3202.

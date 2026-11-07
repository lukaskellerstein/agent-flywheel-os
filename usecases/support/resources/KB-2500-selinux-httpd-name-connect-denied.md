# KB-2500: SELinux blocks Apache httpd from connecting to a backend service (AVC denial name_connect)

- Product: Red Hat Enterprise Linux 8 and 9
- Affected versions: every release (expected SELinux behavior)
- Fixed in: not a bug. Allow the connection in the SELinux policy.
- Severity: 3
- Last reviewed: 2026-08-04

## Symptoms

- The Apache reverse proxy answers 503 for a backend.
- `/var/log/httpd/error_log` shows
  `(13)Permission denied: AH00957: http: attempt to connect to 127.0.0.1:<port> (localhost) failed`.
- `ausearch -m avc -ts recent` shows `denied { name_connect } for comm="httpd" dest=<port>`.

## Cause

The default SELinux policy lets httpd connect only to ports of the HTTP port types. Any
other backend port is denied.

## Resolution

Pick one:

1. Narrow: label the backend port as an HTTP port:

```
semanage port -a -t http_port_t -p tcp <port>
```

2. Broad: allow httpd to connect to any port:

```
setsebool -P httpd_can_network_connect 1
```

Then reload Apache: `systemctl reload httpd`.

## Notes for support engineers

- Never recommend `setenforce 0`, permissive mode, or disabling SELinux, not even as a test.
- The `-P` flag of `setsebool` keeps the change after a reboot. Without it the fix is lost.

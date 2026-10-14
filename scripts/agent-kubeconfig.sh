#!/bin/bash
# Mint the coding agent's own OpenShift credentials (PLAN.md phase 0 step 4).
#
# The first run needs Lukas's `oc login` (cluster-admin) in ~/.kube/config,
# which the agent's sandbox cannot read, so it runs outside the sandbox:
#
#   scripts/agent-kubeconfig.sh          # token valid 24h
#   scripts/agent-kubeconfig.sh 8h       # or another duration
#
# ADMIN_CONTEXT names the context to use instead of the current one, which
# other tools on this Mac switch (seen 2026-10-13: `kind-agentic` right after
# Lukas's `oc login`).
#
# It creates namespace agent-flywheel if it is missing, applies
# deploy/agent-access (ServiceAccount `claude-agent`, cluster-admin), mints a
# short-lived token for it, and writes a kubeconfig holding that token and
# nothing else to ~/.config/agent-kube/agent-flywheel-os.yaml. An agent's `oc`
# uses it through KUBECONFIG, never ~/.kube/config.
#
# While that token is still valid, the agent renews it with its own identity:
#
#   ADMIN_KUBECONFIG=~/.config/agent-kube/agent-flywheel-os.yaml scripts/agent-kubeconfig.sh
#
# The file lives outside the repo on purpose: `oc start-build --from-dir=.`
# uploads the working tree, and a gitignored token at the root would ride along.
# openshift-eval keeps its own file next to it, for the same ServiceAccount.
#
# Re-run it when the token expires (the agent sees 401 Unauthorized) or after
# the cluster is rebuilt. bash 3.2.

set -eu

root=$(cd "$(dirname "$0")/.." && pwd)
admin_kc="${ADMIN_KUBECONFIG:-$HOME/.kube/config}"
admin_ctx="${ADMIN_CONTEXT:-}"
out_dir="$HOME/.config/agent-kube"
out="$out_dir/agent-flywheel-os.yaml"
duration="${1:-24h}"
ns=agent-flywheel
sa=claude-agent

# Always the login named above, never a KUBECONFIG inherited from a session.
admin() { command oc --kubeconfig "$admin_kc" ${admin_ctx:+--context "$admin_ctx"} "$@"; }

server=$(admin whoami --show-server)

# The admin context is whichever cluster Lukas last switched to, and the same
# kubeconfig also reaches other clusters. This project only ever runs on an
# RHDP cluster, so refuse anything else rather than create a namespace and an
# admin ServiceAccount on the wrong one. A new catalog domain means editing
# this line.
case "$server" in
  https://api.cluster-*.dyn.redhatworkshops.io:6443) ;;
  *)
    echo "agent-kubeconfig: refusing $server: the current oc context is not an RHDP cluster (api.cluster-*.dyn.redhatworkshops.io). Ask Lukas to oc login to the agent-flywheel cluster." >&2
    exit 1
    ;;
esac
# Its own assignment, so `set -e` stops here when the login is expired or the
# cluster is down; inside the echo below, a failed whoami would pass.
who=$(admin whoami)
echo "cluster: $server, as $who" >&2

# The ServiceAccount lives in it, so it must exist before the apply.
if ! admin get namespace "$ns" >/dev/null 2>&1; then
  admin create namespace "$ns" >&2
fi
admin apply -k "$root/deploy/agent-access" >&2

token=$(admin -n "$ns" create token "$sa" --duration="$duration")

# TLS settings come from Lukas's current context, in whichever form it has them.
jp() { admin config view --minify --raw -o "jsonpath={.clusters[0].cluster.$1}"; }
ca=$(jp certificate-authority-data)
ca_file=$(jp certificate-authority)
skip=$(jp insecure-skip-tls-verify)
if [ -z "$ca" ] && [ -n "$ca_file" ]; then
  ca=$(base64 < "$ca_file" | tr -d '\n')
fi
tls=""
if [ -n "$ca" ]; then
  tls="    certificate-authority-data: $ca"
elif [ "$skip" = true ]; then
  tls="    insecure-skip-tls-verify: true"
fi

# Written with a heredoc, not `oc config set-credentials --token=`, so the token
# never appears in a process list.
mkdir -p "$out_dir"
chmod 700 "$out_dir"
umask 077
tmp="$out.tmp.$$"
cat > "$tmp" <<EOF
apiVersion: v1
kind: Config
clusters:
  - name: agent-flywheel
    cluster:
      server: $server
$(if [ -n "$tls" ]; then printf '  %s\n' "$tls"; fi)
users:
  - name: $sa
    user:
      token: $token
contexts:
  - name: $sa
    context:
      cluster: agent-flywheel
      user: $sa
      namespace: $ns
current-context: $sa
EOF
mv "$tmp" "$out"

# Done when the agent's identity answers and holds cluster-admin.
who=$(command oc --kubeconfig "$out" whoami)
can=$(command oc --kubeconfig "$out" auth can-i '*' '*' --all-namespaces)
exp=$(printf '%s' "$token" | cut -d. -f2 | python3 -c '
import base64, json, sys, time
p = sys.stdin.read().strip(); p += "=" * (-len(p) % 4)
print(time.strftime("%Y-%m-%d %H:%M %Z", time.localtime(json.loads(base64.urlsafe_b64decode(p))["exp"])))')
echo "wrote $out" >&2
echo "identity: $who, cluster-admin: $can, token expires $exp" >&2

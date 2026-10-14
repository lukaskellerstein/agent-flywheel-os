#!/bin/bash
# SessionStart hook — every `oc`/`kubectl` of this session uses the agent's own
# kubeconfig, which scripts/agent-kubeconfig.sh writes (ServiceAccount
# `claude-agent`, cluster-admin, short-lived token).
#
# The sandbox denies ~/.kube/config. With KUBECONFIG pointing here `oc` runs
# inside the sandbox, where Bash is auto-approved, so a pipe or a chain needs
# no permission prompt. Exported even when the file is missing: `oc` then fails
# with a clear error instead of falling back to Lukas's login.
#
# CLAUDE_ENV_FILE is sourced before every Bash command of the session.
# Ported from openshift-eval, which keeps its own file next to this one.
# bash 3.2.

[ -n "${CLAUDE_ENV_FILE:-}" ] || exit 0
printf 'export KUBECONFIG="%s"\n' "$HOME/.config/agent-kube/agent-flywheel-os.yaml" >> "$CLAUDE_ENV_FILE"

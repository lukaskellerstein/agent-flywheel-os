# KB-4201: vLLM predictor pod restarts with OOMKilled or "CUDA out of memory"

- Product: Red Hat OpenShift AI 2.22 and 3.0, vLLM serving runtime
- Affected versions: every 2.22 and 3.0 release (configuration)
- Fixed in: not a bug. Limit the context length.
- Severity: 3
- Last reviewed: 2026-09-12

## Symptoms

- The InferenceService switches between Ready and Not Ready.
- The predictor pod restarts with `OOMKilled`, or its log shows `torch.OutOfMemoryError: CUDA out of memory`.

## Cause

vLLM takes the maximum context length from the model config, for example 131072 tokens,
and reserves KV cache for it. That needs more GPU memory than the node has.

## Resolution

1. Add arguments to the serving runtime: `--max-model-len=8192` and `--gpu-memory-utilization=0.90`.
2. Raise the pod memory limit if the pod itself is OOMKilled.
3. Redeploy and watch `oc logs` of the predictor for `Maximum concurrency`.

## Notes for support engineers

- Ask for the GPU type and memory (the node label `nvidia.com/gpu.product`, or `nvidia-smi`).
- A pod that stays `Pending` is a scheduling problem, see KB-4200.

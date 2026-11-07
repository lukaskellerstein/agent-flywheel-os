"""The flywheel's training loop (spec 02 phase 3 step 3).

One training run on one use case version: score brain v0, then per
iteration let the adjuster change the best brain from its train failures,
score the new brain, and keep it when its train score is at least the best
one's, else revert. Every score is an evaluation of the flywheel API, so an
EvalHub job with C11's adapter; every record goes to MLflow. Ported from
openshift-eval `d0dd4e1` (`flywheel/controller.py`, `adjust.py`), once
(decision 22).
"""


class FlywheelError(RuntimeError):
    """A training run that cannot go on; the message says why."""

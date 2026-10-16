"""The flywheel API: the registry of use cases (spec 02 sections 4.2 and 4.3).

A use case comes in as one folder (an upload or a git path), is checked whole,
and is stored as a fixed version in one S3 bucket. The dashboard module's BFF
forwards to this API (spec 01 decision 6).
"""

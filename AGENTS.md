# Agent instructions

This is a Python (uv-managed) + static-HTML project. See README.md for the
full project description, pipeline usage, and testing instructions.

## Versioning

Whenever you make a change to `extract/` (the extraction pipeline) or its
tests, bump `version` in `pyproject.toml` (semantic versioning). This
applies to every commit that touches pipeline code, not just releases.

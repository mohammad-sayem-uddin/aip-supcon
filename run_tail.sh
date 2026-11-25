#!/bin/bash
# Resumable tail of the pipeline: S9 -> S10 -> tables -> figures -> report
cd "$(dirname "$0")"
export PYTHONPATH=.
.venv/bin/python -m src.pipeline s9 && .venv/bin/python -m src.pipeline s10 && \
.venv/bin/python -m src.evaluate --build-tables && .venv/bin/python -m src.visualize --all && \
.venv/bin/python -m src.report

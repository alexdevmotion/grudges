#!/bin/bash
# Offline verification; reward is present even if the verifier fails.
mkdir -p /logs/verifier
reward=0
trap 'echo "$reward" > /logs/verifier/reward.txt' EXIT
python3 /tests/verify.py && reward=1
exit 0

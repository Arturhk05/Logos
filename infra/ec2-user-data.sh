#!/bin/bash
# Runs once, on the first boot of the API host (Amazon Linux 2023).
# The SSM Agent and the AWS CLI already come with the AMI; only Docker is missing.
set -euo pipefail

dnf install -y docker
systemctl enable --now docker

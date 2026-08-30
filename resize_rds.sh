#!/usr/bin/env bash
# resize_rds.sh — Apply a recommended RDS instance class change
# Dry-run by default. Pass --apply to execute.
#
# Usage:
#   bash resize_rds.sh --instance db-prod-01 --class db.t3.medium
#   bash resize_rds.sh --instance db-prod-01 --class db.t3.medium --apply

set -euo pipefail

INSTANCE=""
NEW_CLASS=""
APPLY=false
REGION="${AWS_REGION:-us-east-1}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --instance) INSTANCE="$2"; shift 2 ;;
    --class)    NEW_CLASS="$2"; shift 2 ;;
    --apply)    APPLY=true; shift ;;
    --region)   REGION="$2"; shift 2 ;;
    *) echo "Unknown arg: $1"; exit 1 ;;
  esac
done

[[ -z "$INSTANCE" || -z "$NEW_CLASS" ]] && {
  echo "Usage: $0 --instance <id> --class <class> [--apply]"
  exit 1
}

CURRENT=$(aws rds describe-db-instances \
  --db-instance-identifier "$INSTANCE" \
  --region "$REGION" \
  --query 'DBInstances[0].DBInstanceClass' \
  --output text)

echo ""
echo "Instance : $INSTANCE"
echo "Current  : $CURRENT"
echo "Target   : $NEW_CLASS"
echo ""

if [[ "$APPLY" == false ]]; then
  echo "[DRY RUN] No changes made. Pass --apply to execute."
  exit 0
fi

read -rp "Confirm resize $INSTANCE from $CURRENT to $NEW_CLASS? [yes/no]: " CONFIRM
[[ "$CONFIRM" != "yes" ]] && { echo "Aborted."; exit 0; }

echo "Applying modification..."
aws rds modify-db-instance \
  --db-instance-identifier "$INSTANCE" \
  --db-instance-class "$NEW_CLASS" \
  --apply-immediately \
  --region "$REGION"

echo "Waiting for instance to become available..."
aws rds wait db-instance-available \
  --db-instance-identifier "$INSTANCE" \
  --region "$REGION"

echo "Done. $INSTANCE is now running on $NEW_CLASS."

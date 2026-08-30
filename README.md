# aws-rds-rightsizing

Analyze AWS RDS instance utilization via CloudWatch metrics and produce right-sizing recommendations — or apply them directly with the resize script.

Built from real production patterns: repeatedly found `db.t3.large` and `db.r5.xlarge` instances running at 8–15% average CPU with fewer than 20 concurrent connections, costing 2–4× what the workload required. One engagement reduced monthly RDS spend by ~32% through metric-backed downsizing combined with S3 lifecycle automation.

## What it does

- Pulls 14-day CloudWatch averages for CPU, `DatabaseConnections`, `ReadIOPS`, `WriteIOPS`, `FreeableMemory`
- Scores each instance against a built-in RDS instance class sizing matrix
- Outputs a recommendation table: current class → suggested class → estimated monthly saving
- Dry-run safe: resize script requires `--apply` to make changes
- Excludes any instance where peak CPU exceeded 70% at least once (protects against downsizing legitimately bursty workloads)

## Quick start

```bash
pip install -r requirements.txt
export AWS_PROFILE=your-profile   # or use AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY

# Analyze all RDS instances in a region
python analyze_rds.py --region us-east-1

# Analyze a specific instance
python analyze_rds.py --region us-east-1 --instance db-prod-01

# Apply a recommended resize (triggers a brief instance restart)
bash resize_rds.sh --instance db-prod-01 --class db.t3.medium --apply
```

## Sample output

```
INSTANCE            CURRENT CLASS     CPU AVG   CONNS AVG   PEAK CPU   RECOMMENDED     EST. SAVING/MO
db-prod-01          db.r5.xlarge      9.4%      12          38%        db.t3.large     ~$187
db-analytics-02     db.t3.large       6.1%      4           22%        db.t3.medium    ~$52
db-staging-01       db.t3.medium      3.8%      2           14%        db.t3.small     ~$18
db-highload-03      db.r5.2xlarge     64.2%     280         91%        [SKIP: peak>70%] —
```

## Files

| File | Purpose |
|------|---------|
| `analyze_rds.py` | Main script — pulls CloudWatch metrics, scores instances, prints recommendations |
| `resize_rds.sh` | Applies a class change via AWS CLI; dry-run by default, use `--apply` to execute |
| `instance_matrix.py` | RDS class → vCPU / RAM / hourly price lookup (us-east-1 on-demand, update as needed) |
| `requirements.txt` | Python dependencies (boto3, tabulate) |

## IAM policy

Minimum permissions needed:

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": [
      "rds:DescribeDBInstances",
      "cloudwatch:GetMetricStatistics",
      "cloudwatch:ListMetrics"
    ],
    "Resource": "*"
  }]
}
```

## Notes

- Pricing in `instance_matrix.py` is us-east-1 on-demand Linux — update for your region and reserved/savings plan rates
- The 14-day window is intentional: smooths weeknight/weekend variation without going stale
- `FreeableMemory` thresholds are conservative; cross-check with your application's actual working set before downsizing memory-optimized classes

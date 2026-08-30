#!/usr/bin/env python3
"""
Analyze RDS instance utilization via CloudWatch and recommend right-sizing.

Usage:
    python analyze_rds.py --region us-east-1
    python analyze_rds.py --region us-east-1 --instance db-prod-01
"""

import argparse
import datetime
import boto3
from tabulate import tabulate
from instance_matrix import INSTANCE_MATRIX, hourly_price

LOOKBACK_DAYS = 14
CPU_PEAK_THRESHOLD = 70.0   # skip downsize if peak ever exceeded this
MIN_CONN_THRESHOLD = 10     # below this avg, connections are not the bottleneck


def get_metric_avg(cw, db_id, metric, stat="Average"):
    end = datetime.datetime.utcnow()
    start = end - datetime.timedelta(days=LOOKBACK_DAYS)
    resp = cw.get_metric_statistics(
        Namespace="AWS/RDS",
        MetricName=metric,
        Dimensions=[{"Name": "DBInstanceIdentifier", "Value": db_id}],
        StartTime=start,
        EndTime=end,
        Period=86400,          # 1-day granularity
        Statistics=[stat],
    )
    points = resp.get("Datapoints", [])
    if not points:
        return None
    return sum(p[stat] for p in points) / len(points)


def get_metric_peak(cw, db_id, metric):
    end = datetime.datetime.utcnow()
    start = end - datetime.timedelta(days=LOOKBACK_DAYS)
    resp = cw.get_metric_statistics(
        Namespace="AWS/RDS",
        MetricName=metric,
        Dimensions=[{"Name": "DBInstanceIdentifier", "Value": db_id}],
        StartTime=start,
        EndTime=end,
        Period=3600,
        Statistics=["Maximum"],
    )
    points = resp.get("Datapoints", [])
    if not points:
        return 0.0
    return max(p["Maximum"] for p in points)


def recommend(current_class, cpu_avg, cpu_peak, conn_avg, mem_free_gb):
    if cpu_peak >= CPU_PEAK_THRESHOLD:
        return None, None   # do not downsize; peak is too high

    current = INSTANCE_MATRIX.get(current_class)
    if not current:
        return None, None

    for cls, spec in sorted(INSTANCE_MATRIX.items(), key=lambda x: x[1]["price"]):
        if spec["price"] >= current["price"]:
            continue  # only consider cheaper options
        # Safety checks
        if cpu_avg > 40 and spec["vcpu"] < current["vcpu"]:
            continue
        if conn_avg > MIN_CONN_THRESHOLD and spec["max_conn"] < conn_avg * 1.5:
            continue
        if mem_free_gb is not None and mem_free_gb < 0.5 and spec["ram_gb"] < current["ram_gb"]:
            continue
        saving = (current["price"] - spec["price"]) * 730  # monthly hours
        return cls, round(saving, 2)

    return None, None


def analyze(region, instance_filter=None):
    rds = boto3.client("rds", region_name=region)
    cw  = boto3.client("cloudwatch", region_name=region)

    paginator = rds.get_paginator("describe_db_instances")
    instances = []
    for page in paginator.paginate():
        instances.extend(page["DBInstances"])

    if instance_filter:
        instances = [i for i in instances if i["DBInstanceIdentifier"] == instance_filter]

    rows = []
    for inst in instances:
        db_id   = inst["DBInstanceIdentifier"]
        db_class = inst["DBInstanceClass"]

        cpu_avg  = get_metric_avg(cw, db_id, "CPUUtilization") or 0.0
        cpu_peak = get_metric_peak(cw, db_id, "CPUUtilization")
        conn_avg = get_metric_avg(cw, db_id, "DatabaseConnections") or 0.0
        mem_free = get_metric_avg(cw, db_id, "FreeableMemory")
        mem_free_gb = mem_free / (1024 ** 3) if mem_free else None

        rec_class, saving = recommend(db_class, cpu_avg, cpu_peak, conn_avg, mem_free_gb)

        rows.append([
            db_id,
            db_class,
            f"{cpu_avg:.1f}%",
            f"{int(conn_avg)}",
            f"{cpu_peak:.1f}%",
            rec_class or ("[SKIP: peak>70%]" if cpu_peak >= CPU_PEAK_THRESHOLD else "—"),
            f"~${saving}/mo" if saving else "—",
        ])

    headers = ["INSTANCE", "CURRENT CLASS", "CPU AVG", "CONNS AVG", "PEAK CPU", "RECOMMENDED", "EST. SAVING/MO"]
    print()
    print(tabulate(rows, headers=headers, tablefmt="simple"))
    print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="RDS right-sizing analyzer")
    parser.add_argument("--region", required=True)
    parser.add_argument("--instance", default=None, help="Analyze a single DB instance ID")
    args = parser.parse_args()
    analyze(args.region, args.instance)

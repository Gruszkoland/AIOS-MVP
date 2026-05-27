"""
Failover Detector Lambda — periodically checks primary DB health
and replication lag to standby. Sends alerts if thresholds exceeded.
"""

import json
import boto3
import os
from datetime import datetime

rds = boto3.client('rds')
rds_dr = boto3.client('rds', region_name=os.environ.get('STANDBY_REGION'))
cloudwatch = boto3.client('cloudwatch')
sns = boto3.client('sns')

PRIMARY_DB_ID = os.environ.get('PRIMARY_DB_ID')
STANDBY_DB_ID = os.environ.get('STANDBY_DB_ID')
SNS_TOPIC_ARN = os.environ.get('SNS_TOPIC_ARN')
ENVIRONMENT = os.environ.get('ENVIRONMENT')


def check_primary_health():
    """Check primary database health."""
    try:
        response = rds.describe_db_instances(
            DBInstanceIdentifier=PRIMARY_DB_ID
        )
        instance = response['DBInstances'][0]
        return {
            'status': instance['DBInstanceStatus'],
            'availability_zone': instance['AvailabilityZone'],
            'cpu_utilization': get_metric('CPUUtilization', PRIMARY_DB_ID),
            'connections': get_metric('DatabaseConnections', PRIMARY_DB_ID),
            'free_storage': get_metric('FreeStorageSpace', PRIMARY_DB_ID),
        }
    except Exception as e:
        print(f"Error checking primary health: {e}")
        return None


def check_standby_health():
    """Check standby database health and replication lag."""
    try:
        response = rds_dr.describe_db_instances(
            DBInstanceIdentifier=STANDBY_DB_ID
        )
        instance = response['DBInstances'][0]

        # Get replication lag from CloudWatch
        lag = get_metric(
            'AuroraBinlogReplicaLag',
            STANDBY_DB_ID,
            region=os.environ.get('STANDBY_REGION')
        )

        return {
            'status': instance['DBInstanceStatus'],
            'role': instance.get('ReadReplicaSourceDBInstanceIdentifier', 'unknown'),
            'cpu_utilization': get_metric('CPUUtilization', STANDBY_DB_ID),
            'replication_lag_ms': lag,
            'free_storage': get_metric('FreeStorageSpace', STANDBY_DB_ID),
        }
    except Exception as e:
        print(f"Error checking standby health: {e}")
        return None


def get_metric(metric_name, db_instance_id, region=None):
    """Get latest CloudWatch metric value."""
    try:
        if region:
            cw = boto3.client('cloudwatch', region_name=region)
        else:
            cw = cloudwatch

        response = cw.get_metric_statistics(
            Namespace='AWS/RDS',
            MetricName=metric_name,
            Dimensions=[
                {'Name': 'DBInstanceIdentifier', 'Value': db_instance_id}
            ],
            StartTime=datetime.utcnow().replace(second=0, microsecond=0),
            EndTime=datetime.utcnow(),
            Period=60,
            Statistics=['Average', 'Maximum']
        )

        if response['Datapoints']:
            return response['Datapoints'][-1].get('Average', 0)
        return 0
    except Exception as e:
        print(f"Error getting metric {metric_name}: {e}")
        return 0


def send_alert(subject, message):
    """Send SNS alert."""
    try:
        sns.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject=f"[{ENVIRONMENT.upper()}] {subject}",
            Message=message
        )
        print(f"Alert sent: {subject}")
    except Exception as e:
        print(f"Error sending alert: {e}")


def handler(event, context):
    """Lambda handler — runs periodically via EventBridge."""

    print(f"Failover detector starting at {datetime.utcnow()}")

    primary = check_primary_health()
    standby = check_standby_health()

    if not primary or not standby:
        send_alert(
            "FAILOVER DETECTOR ERROR",
            "Failed to retrieve database health information. Manual check required."
        )
        return {
            'statusCode': 500,
            'body': 'Health check failed'
        }

    # Check thresholds
    alerts = []

    # Primary failures
    if primary['status'] not in ['available', 'backing-up', 'modifying']:
        alerts.append(f"Primary DB status: {primary['status']}")

    if primary['cpu_utilization'] > 80:
        alerts.append(f"Primary CPU high: {primary['cpu_utilization']:.1f}%")

    if primary['connections'] > 900:
        alerts.append(f"Primary connections high: {primary['connections']}")

    if primary['free_storage'] < 10_000_000_000:  # < 10 GB
        alerts.append(f"Primary storage low: {primary['free_storage'] / 1e9:.1f} GB")

    # Standby failures
    if standby['status'] not in ['available', 'backing-up']:
        alerts.append(f"Standby DB status: {standby['status']}")

    lag_seconds = standby['replication_lag_ms'] / 1000 if standby['replication_lag_ms'] else 0
    if lag_seconds > 5:
        alerts.append(f"Replication lag high: {lag_seconds:.1f} seconds")

    if standby['cpu_utilization'] > 80:
        alerts.append(f"Standby CPU high: {standby['cpu_utilization']:.1f}%")

    # Send alert if any threshold exceeded
    if alerts:
        message = "FAILOVER READINESS CHECK — ISSUES DETECTED:\n\n"
        message += "\n".join(f"• {alert}" for alert in alerts)
        message += f"\n\nPrimary Status: {primary['status']}"
        message += f"\nStandby Lag: {lag_seconds:.1f}s"
        message += f"\n\nAction: Review CloudWatch metrics and standby replication status."

        send_alert("Database Health Alert", message)
    else:
        print("All health checks passed. Failover ready.")

    return {
        'statusCode': 200,
        'body': json.dumps({
            'primary': primary,
            'standby': standby,
            'alerts': alerts,
            'failover_ready': len(alerts) == 0
        })
    }

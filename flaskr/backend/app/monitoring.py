from flask import current_app, request, has_request_context
import psutil
import time
from dataclasses import dataclass
from typing import Dict, Any
import boto3
import logging
import json
import traceback
from datetime import datetime
import redis

# Import required classes from middleware
from app.middleware.logging import CloudWatchHandler, CustomJSONFormatter
from app.middleware.rate_limit import RateLimiter

@dataclass
class SystemMetrics:
    cpu_percent: float
    memory_percent: float
    disk_usage_percent: float
    open_file_descriptors: int
    
class ApplicationMonitor:
    def __init__(self):
        self.cloudwatch = boto3.client('cloudwatch')
        self.namespace = 'Flaskr/Production'
    
    def get_system_metrics(self) -> SystemMetrics:
        """Collect system metrics."""
        return SystemMetrics(
            cpu_percent=psutil.cpu_percent(),
            memory_percent=psutil.virtual_memory().percent,
            disk_usage_percent=psutil.disk_usage('/').percent,
            open_file_descriptors=len(psutil.Process().open_files())
        )
    
    def get_application_metrics(self) -> Dict[str, Any]:
        """Collect application-specific metrics."""
        with current_app.app_context():
            from app.models import db
            
            # Database metrics
            db_metrics = {
                'db_connections': len(db.engine.pool.checkedin()) + len(db.engine.pool.checkedout())
            }
            
            # Cache metrics if using Redis
            cache_metrics = {}
            if hasattr(current_app, 'cache'):
                redis_info = current_app.cache.redis_client.info()
                cache_metrics.update({
                    'cache_hits': redis_info['keyspace_hits'],
                    'cache_misses': redis_info['keyspace_misses'],
                    'cache_memory_used': redis_info['used_memory']
                })
            
            return {**db_metrics, **cache_metrics}
    
    def send_metrics_to_cloudwatch(self, metrics: Dict[str, float]):
        """Send metrics to CloudWatch."""
        try:
            metric_data = []
            for name, value in metrics.items():
                metric_data.append({
                    'MetricName': name,
                    'Value': value,
                    'Unit': 'Count',
                    'Timestamp': int(time.time())
                })
            
            self.cloudwatch.put_metric_data(
                Namespace=self.namespace,
                MetricData=metric_data
            )
        except Exception as e:
            current_app.logger.error(f"Error sending metrics to CloudWatch: {str(e)}")
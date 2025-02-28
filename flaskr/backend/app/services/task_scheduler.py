from flask import current_app
import asyncio
from datetime import datetime, timezone
import boto3

class TaskScheduler:
    def __init__(self, match_monitor_service):
        self.match_monitor = match_monitor_service
        self.eventbridge = boto3.client('events')

    def schedule_match_monitoring(self):
        """Schedule match monitoring task"""
        try:
            # Check if Lambda ARN is configured
            if 'MONITOR_LAMBDA_ARN' not in current_app.config:
                current_app.logger.warning("MONITOR_LAMBDA_ARN not configured, using in-process monitoring instead")
                
                # Set up a simple rule without a Lambda target
                self.eventbridge.put_rule(
                    Name='live-match-monitoring',
                    ScheduleExpression='rate(5 minutes)',
                    State='ENABLED',
                    Description='Monitor live matches and process completed ones'
                )
                
                # You could potentially set up a different target here if needed
                # Or just log that you're skipping the target setup
                current_app.logger.info("EventBridge rule created without Lambda target")
                return
                
            # Original code for when Lambda ARN is available
            self.eventbridge.put_rule(
                Name='live-match-monitoring',
                ScheduleExpression='rate(5 minutes)',
                State='ENABLED',
                Description='Monitor live matches and process completed ones'
            )

            self.eventbridge.put_targets(
                Rule='live-match-monitoring',
                Targets=[{
                    'Id': 'MonitorLiveMatches',
                    'Arn': current_app.config['MONITOR_LAMBDA_ARN'],
                    'Input': '{"task": "monitor_live_matches"}'
                }]
            )

            current_app.logger.info("Successfully scheduled match monitoring task with Lambda target")

        except Exception as e:
            current_app.logger.error(f"Error scheduling tasks: {str(e)}")
            raise

    def schedule_verification_tasks(self):
        """Schedule verification tasks"""
        try:
            # Schedule points verification (daily)
            self.eventbridge.put_rule(
                Name='daily-points-verification',
                ScheduleExpression='rate(1 day)',
                State='ENABLED',
                Description='Verify all points and league tables daily'
            )

            # Schedule failed processing recovery (hourly)
            self.eventbridge.put_rule(
                Name='hourly-processing-recovery',
                ScheduleExpression='rate(1 hour)',
                State='ENABLED',
                Description='Recover any failed match processing'
            )

            # Add targets
            self.eventbridge.put_targets(
                Rule='daily-points-verification',
                Targets=[{
                    'Id': 'VerifyPoints',
                    'Arn': current_app.config['VERIFICATION_LAMBDA_ARN'],
                    'Input': '{"task": "verify_points_and_tables"}'
                }]
            )

            self.eventbridge.put_targets(
                Rule='hourly-processing-recovery',
                Targets=[{
                    'Id': 'RecoverProcessing',
                    'Arn': current_app.config['RECOVERY_LAMBDA_ARN'],
                    'Input': '{"task": "recover_failed_processing"}'
                }]
            )

            current_app.logger.info("Successfully scheduled verification tasks")

        except Exception as e:
            current_app.logger.error(f"Error scheduling verification tasks: {str(e)}")
            raise

    async def execute_monitoring(self):
        """Execute the monitoring task"""
        try:
            await self.match_monitor.monitor_live_matches()
        except Exception as e:
            current_app.logger.error(f"Error executing monitoring task: {str(e)}")
            raise
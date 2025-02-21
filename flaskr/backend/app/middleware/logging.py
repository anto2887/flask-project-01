import logging
import json
from flask import request, has_request_context, current_app
from pythonjsonlogger import jsonlogger
import traceback
from datetime import datetime
import boto3

class CustomJSONFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record, record, message_dict):
        super(CustomJSONFormatter, self).add_fields(log_record, record, message_dict)
        
        # Add timestamp
        log_record['timestamp'] = datetime.utcnow().isoformat()
        
        # Add log level
        log_record['level'] = record.levelname
        
        # Add request information if available
        if has_request_context():
            log_record['request_id'] = request.headers.get('X-Request-ID')
            log_record['ip'] = request.remote_addr
            log_record['method'] = request.method
            log_record['path'] = request.path
            log_record['user_agent'] = request.user_agent.string
            
            # Add user information if authenticated
            if hasattr(request, 'user') and request.user.is_authenticated:
                log_record['user_id'] = request.user.id
        
        # Add exception information if present
        if record.exc_info:
            log_record['exception'] = traceback.format_exception(*record.exc_info)

class CloudWatchHandler(logging.Handler):
    def __init__(self, log_group, log_stream_prefix):
        super().__init__()
        self.log_group = log_group
        self.log_stream_prefix = log_stream_prefix
        self.client = boto3.client('logs')
        self.sequence_token = None
        
        # Create log stream if it doesn't exist
        self._create_log_stream()
    
    def _create_log_stream(self):
        stream_name = f"{self.log_stream_prefix}-{datetime.utcnow().strftime('%Y-%m-%d')}"
        try:
            self.client.create_log_stream(
                logGroupName=self.log_group,
                logStreamName=stream_name
            )
        except self.client.exceptions.ResourceAlreadyExistsException:
            pass
        self.log_stream = stream_name
    
    def emit(self, record):
        try:
            # Format the record
            log_entry = self.format(record)
            
            # Prepare the parameters
            params = {
                'logGroupName': self.log_group,
                'logStreamName': self.log_stream,
                'logEvents': [{
                    'timestamp': int(record.created * 1000),
                    'message': log_entry
                }]
            }
            
            # Add sequence token if we have one
            if self.sequence_token:
                params['sequenceToken'] = self.sequence_token
            
            # Send the log entry
            response = self.client.put_log_events(**params)
            self.sequence_token = response['nextSequenceToken']
            
        except Exception as e:
            print(f"Error sending logs to CloudWatch: {str(e)}")
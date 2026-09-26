import logging
import sys
import os
import re
from datetime import datetime

class StructuredFormatter(logging.Formatter):
    def format(self, record):
        timestamp = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S')
        level = record.levelname
        
        # Base message parts
        msg_parts = [f"{timestamp}", f"{level:<7}"]
        
        # Context fields
        if hasattr(record, 'job_id') and record.job_id:
            msg_parts.append(f"job_id={record.job_id}")
            
        if hasattr(record, 'step') and record.step:
            msg_parts.append(f"step={record.step}")
            
        if hasattr(record, 'event') and record.event:
            msg_parts.append(f"event={record.event}")
            
        if hasattr(record, 'candidate_id') and record.candidate_id:
            msg_parts.append(f"candidate_id={record.candidate_id}")
            
        if hasattr(record, 'exception_type') and record.exception_type:
            msg_parts.append(f"exception_type={record.exception_type}")
             
        # Message
        msg_parts.append(f"message={record.getMessage()}")
        
        return " ".join(msg_parts)


def sanitize_log_message(msg: str) -> str:
    """Mask potential passwords and sensitive secrets from log strings"""
    if not isinstance(msg, str):
        return msg
    # Mask password-like patterns if accidentally present
    msg = re.sub(r'(password\s*[:=]\s*)([^\s,]+)', r'\1********', msg, flags=re.IGNORECASE)
    msg = re.sub(r'(token\s*[:=]\s*)([^\s,]+)', r'\1********', msg, flags=re.IGNORECASE)
    msg = re.sub(r'(bearer\s+)([A-Za-z0-9\-\._~\+\/]+=*)', r'\1********', msg, flags=re.IGNORECASE)
    return msg


class StructuredLogger:
    def __init__(self, name="bot", log_file="data/bot.log"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        self.logger.propagate = False
        
        if not self.logger.handlers:
            formatter = StructuredFormatter()
            
            # Stream Handler (stdout)
            stream_handler = logging.StreamHandler(sys.stdout)
            stream_handler.setFormatter(formatter)
            stream_handler.setLevel(logging.INFO)
            self.logger.addHandler(stream_handler)
            
            # Persistent Local File Handler (data/bot.log)
            try:
                os.makedirs(os.path.dirname(log_file), exist_ok=True)
                file_handler = logging.FileHandler(log_file, encoding='utf-8')
                file_handler.setFormatter(formatter)
                file_handler.setLevel(logging.DEBUG)
                self.logger.addHandler(file_handler)
            except Exception as e:
                # If file logging cannot be initialized, stdout remains active
                pass
    
    def info(self, message, job_id=None, step=None, event=None, **kwargs):
        extra = {'job_id': job_id, 'step': step, 'event': event}
        extra.update(kwargs)
        self.logger.info(sanitize_log_message(message), extra=extra)
        
    def debug(self, message, job_id=None, step=None, event=None, **kwargs):
        extra = {'job_id': job_id, 'step': step, 'event': event}
        extra.update(kwargs)
        self.logger.debug(sanitize_log_message(message), extra=extra)

    def warning(self, message, job_id=None, step=None, event=None, **kwargs):
        extra = {'job_id': job_id, 'step': step, 'event': event}
        extra.update(kwargs)
        self.logger.warning(sanitize_log_message(message), extra=extra)

    def error(self, message, job_id=None, step=None, event=None, exception=None, **kwargs):
        if exception:
            kwargs['exception_type'] = type(exception).__name__
        extra = {'job_id': job_id, 'step': step, 'event': event}
        extra.update(kwargs)
        self.logger.error(sanitize_log_message(message), extra=extra)


# Singleton instance
logger = StructuredLogger()

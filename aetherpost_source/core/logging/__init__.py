"""Logging configuration and utilities."""

import logging
import logging.config
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

def setup_logging(
    log_level: str = "INFO",
    log_dir: str = "logs",
    enable_json: bool = True,
    enable_file: bool = True
) -> Dict[str, Any]:
    """Setup comprehensive logging configuration."""
    
    # Create log directory
    log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True)
    
    # Base configuration
    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S"
            },
            "detailed": {
                "format": "%(asctime)s [%(levelname)s] %(name)s:%(lineno)d - %(funcName)s(): %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S"
            },
            "json": {
                "()": JSONFormatter,
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": log_level,
                "formatter": "standard",
                "stream": "ext://sys.stdout"
            }
        },
        "loggers": {
            "aetherpost": {
                "level": log_level,
                "handlers": ["console"],
                "propagate": False
            },
            "uvicorn": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False
            }
        },
        "root": {
            "level": log_level,
            "handlers": ["console"]
        }
    }
    
    # Add file handlers if enabled
    if enable_file:
        config["handlers"].update({
            "file_info": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "INFO",
                "formatter": "json" if enable_json else "detailed",
                "filename": str(log_path / "autopromo.log"),
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5
            },
            "file_error": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "ERROR",
                "formatter": "json" if enable_json else "detailed",
                "filename": str(log_path / "error.log"),
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5
            },
            "file_audit": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "INFO",
                "formatter": "json",
                "filename": str(log_path / "audit.log"),
                "maxBytes": 10485760,  # 10MB
                "backupCount": 10
            }
        })
        
        # Add file handlers to loggers
        config["loggers"]["aetherpost"]["handlers"].extend(["file_info", "file_error"])
        config["root"]["handlers"].extend(["file_info", "file_error"])
    
    # Apply configuration
    logging.config.dictConfig(config)
    
    return config


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""
    
    def format(self, record):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "thread": record.thread,
            "process": record.process
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in ["name", "msg", "args", "levelname", "levelno", "pathname", 
                          "filename", "module", "lineno", "funcName", "created", 
                          "msecs", "relativeCreated", "thread", "threadName", 
                          "processName", "process", "stack_info", "exc_info", "exc_text"]:
                log_entry[key] = value
        
        return json.dumps(log_entry)


class AuditLogger:
    """Specialized logger for audit events."""
    
    def __init__(self):
        self.logger = logging.getLogger("autopromo.audit")
        self.audit_handler = None
        self._setup_audit_handler()
    
    def _setup_audit_handler(self):
        """Setup dedicated audit log handler."""
        log_path = Path(os.getenv("AUTOPROMO_LOG_DIR", "logs"))
        log_path.mkdir(exist_ok=True)
        
        self.audit_handler = logging.handlers.RotatingFileHandler(
            log_path / "audit.log",
            maxBytes=10485760,  # 10MB
            backupCount=10
        )
        self.audit_handler.setFormatter(JSONFormatter())
        self.logger.addHandler(self.audit_handler)
        self.logger.setLevel(logging.INFO)
    
    def log_campaign_action(self, action: str, campaign_id: str, user_id: str = None, 
                           platform: str = None, details: Dict[str, Any] = None):
        """Log campaign-related actions."""
        self.logger.info(
            f"Campaign {action}",
            extra={
                "event_type": "campaign_action",
                "action": action,
                "campaign_id": campaign_id,
                "user_id": user_id,
                "platform": platform,
                "details": details or {}
            }
        )
    
    def log_api_access(self, endpoint: str, method: str, user_id: str = None,
                      ip_address: str = None, response_code: int = None):
        """Log API access."""
        self.logger.info(
            f"API {method} {endpoint}",
            extra={
                "event_type": "api_access",
                "endpoint": endpoint,
                "method": method,
                "user_id": user_id,
                "ip_address": ip_address,
                "response_code": response_code
            }
        )
    
    def log_security_event(self, event_type: str, details: Dict[str, Any]):
        """Log security-related events."""
        self.logger.warning(
            f"Security event: {event_type}",
            extra={
                "event_type": "security",
                "security_event_type": event_type,
                "details": details
            }
        )


# Global audit logger instance
audit_logger = AuditLogger()


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the specified name."""
    return logging.getLogger(f"autopromo.{name}")


def log_performance(func):
    """Decorator to log function performance."""
    import functools
    import time
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger = get_logger("performance")
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            logger.info(
                f"Function {func.__name__} completed",
                extra={
                    "function": func.__name__,
                    "execution_time": execution_time,
                    "status": "success"
                }
            )
            
            return result
        
        except Exception as e:
            execution_time = time.time() - start_time
            
            logger.error(
                f"Function {func.__name__} failed",
                extra={
                    "function": func.__name__,
                    "execution_time": execution_time,
                    "status": "error",
                    "error": str(e)
                }
            )
            raise
    
    return wrapper
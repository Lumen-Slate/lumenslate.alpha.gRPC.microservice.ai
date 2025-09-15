"""
Metrics collection and monitoring for Document Service.

This module provides metrics collection, aggregation, and JSON endpoint
for monitoring document service operations.
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from threading import Lock
from collections import defaultdict

logger = logging.getLogger(__name__)


class DocumentMetrics:
    """
    Document service metrics collector.
    
    Collects and aggregates metrics for document operations, storage usage,
    and error conditions with thread-safe operations.
    """
    
    def __init__(self):
        """Initialize metrics collector."""
        self._lock = Lock()
        self._counters = defaultdict(int)
        self._gauges = defaultdict(float)
        self._user_storage = defaultdict(int)  # Per-user storage tracking
        self._last_updated = datetime.now()
        
        # Initialize counter metrics
        self._initialize_counters()
    
    def _initialize_counters(self) -> None:
        """Initialize all counter metrics to zero."""
        counter_names = [
            "documents_upload_total",
            "documents_download_total", 
            "documents_delete_total",
            "documents_errors_total",
            "documents_quota_exceeded_total",
            "minio_unavailable_total",
            "database_unavailable_total",
            "documents_operation_failures_total"
        ]
        
        for counter in counter_names:
            self._counters[counter] = 0
    
    def increment_counter(self, metric_name: str, value: int = 1) -> None:
        """
        Increment a counter metric.
        
        Args:
            metric_name: Name of the counter metric
            value: Value to increment by (default: 1)
        """
        with self._lock:
            self._counters[metric_name] += value
            self._last_updated = datetime.now()
            logger.debug(f"Incremented {metric_name} by {value}")
    
    def set_gauge(self, metric_name: str, value: float) -> None:
        """
        Set a gauge metric value.
        
        Args:
            metric_name: Name of the gauge metric
            value: Value to set
        """
        with self._lock:
            self._gauges[metric_name] = value
            self._last_updated = datetime.now()
            logger.debug(f"Set gauge {metric_name} to {value}")
    
    def update_user_storage(self, user_id: str, bytes_used: int) -> None:
        """
        Update per-user storage tracking.
        
        Args:
            user_id: User identifier
            bytes_used: Total bytes used by user
        """
        with self._lock:
            self._user_storage[user_id] = bytes_used
            
            # Update global storage gauge
            total_storage = sum(self._user_storage.values())
            self._gauges["documents_storage_bytes_total"] = total_storage
            self._last_updated = datetime.now()
            
            logger.debug(f"Updated storage for user {user_id}: {bytes_used} bytes")
    
    def get_user_storage(self, user_id: str) -> int:
        """
        Get storage usage for a specific user.
        
        Args:
            user_id: User identifier
            
        Returns:
            int: Bytes used by user
        """
        with self._lock:
            return self._user_storage.get(user_id, 0)
    
    def record_upload(self, user_id: str, file_size: int) -> None:
        """
        Record a successful document upload.
        
        Args:
            user_id: User identifier
            file_size: Size of uploaded file in bytes
        """
        self.increment_counter("documents_upload_total")
        
        # Update user storage
        current_storage = self.get_user_storage(user_id)
        self.update_user_storage(user_id, current_storage + file_size)
    
    def record_download(self) -> None:
        """Record a successful document download."""
        self.increment_counter("documents_download_total")
    
    def record_delete(self, user_id: str, file_size: int) -> None:
        """
        Record a successful document deletion.
        
        Args:
            user_id: User identifier
            file_size: Size of deleted file in bytes
        """
        self.increment_counter("documents_delete_total")
        
        # Update user storage
        current_storage = self.get_user_storage(user_id)
        new_storage = max(0, current_storage - file_size)
        self.update_user_storage(user_id, new_storage)
    
    def record_error(self, error_type: str) -> None:
        """
        Record an error occurrence.
        
        Args:
            error_type: Type of error (quota_exceeded, minio_unavailable, etc.)
        """
        self.increment_counter("documents_errors_total")
        
        # Increment specific error counter
        if error_type == "quota_exceeded":
            self.increment_counter("documents_quota_exceeded_total")
        elif error_type == "minio_unavailable":
            self.increment_counter("minio_unavailable_total")
        elif error_type == "database_unavailable":
            self.increment_counter("database_unavailable_total")
        elif error_type == "operation_failure":
            self.increment_counter("documents_operation_failures_total")
    
    def get_metrics_json(self) -> str:
        """
        Get all metrics in JSON format.
        
        Returns:
            str: JSON string containing all metrics
        """
        with self._lock:
            metrics_data = {
                # Counter metrics
                **dict(self._counters),
                
                # Gauge metrics
                **dict(self._gauges),
                
                # Per-user storage (limited to avoid large responses)
                "documents_storage_bytes": dict(list(self._user_storage.items())[:100]),
                
                # Metadata
                "last_updated": self._last_updated.isoformat(),
                "metrics_count": len(self._counters) + len(self._gauges),
                "users_tracked": len(self._user_storage)
            }
        
        return json.dumps(metrics_data, indent=2)
    
    def get_metrics_dict(self) -> Dict[str, Any]:
        """
        Get all metrics as a dictionary.
        
        Returns:
            Dict containing all metrics data
        """
        with self._lock:
            return {
                # Counter metrics
                **dict(self._counters),
                
                # Gauge metrics  
                **dict(self._gauges),
                
                # Per-user storage
                "documents_storage_bytes": dict(self._user_storage),
                
                # Metadata
                "last_updated": self._last_updated.isoformat(),
                "metrics_count": len(self._counters) + len(self._gauges),
                "users_tracked": len(self._user_storage)
            }
    
    def reset_counters(self) -> None:
        """Reset all counter metrics to zero (for testing)."""
        with self._lock:
            self._initialize_counters()
            self._last_updated = datetime.now()
            logger.info("Reset all counter metrics")
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of key metrics.
        
        Returns:
            Dict containing summary metrics
        """
        with self._lock:
            total_operations = (
                self._counters["documents_upload_total"] +
                self._counters["documents_download_total"] +
                self._counters["documents_delete_total"]
            )
            
            error_rate = 0.0
            if total_operations > 0:
                error_rate = (self._counters["documents_errors_total"] / total_operations) * 100
            
            return {
                "total_operations": total_operations,
                "total_errors": self._counters["documents_errors_total"],
                "error_rate_percent": round(error_rate, 2),
                "total_storage_bytes": self._gauges.get("documents_storage_bytes_total", 0),
                "active_users": len(self._user_storage),
                "last_updated": self._last_updated.isoformat()
            }


# Global metrics instance
_metrics_collector: Optional[DocumentMetrics] = None


def get_metrics_collector() -> DocumentMetrics:
    """
    Get the global metrics collector instance.
    
    Returns:
        DocumentMetrics: The global metrics collector instance
    """
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = DocumentMetrics()
        logger.info("Initialized global metrics collector")
    return _metrics_collector


# Convenience functions for common operations
def record_upload_success(user_id: str, file_size: int) -> None:
    """Record successful upload."""
    get_metrics_collector().record_upload(user_id, file_size)


def record_download_success() -> None:
    """Record successful download."""
    get_metrics_collector().record_download()


def record_delete_success(user_id: str, file_size: int) -> None:
    """Record successful deletion."""
    get_metrics_collector().record_delete(user_id, file_size)


def record_quota_exceeded() -> None:
    """Record quota exceeded error."""
    get_metrics_collector().record_error("quota_exceeded")


def record_minio_unavailable() -> None:
    """Record MinIO unavailable error."""
    get_metrics_collector().record_error("minio_unavailable")


def record_database_unavailable() -> None:
    """Record database unavailable error."""
    get_metrics_collector().record_error("database_unavailable")


def record_operation_failure() -> None:
    """Record general operation failure."""
    get_metrics_collector().record_error("operation_failure")


def get_metrics_json() -> str:
    """Get metrics in JSON format."""
    return get_metrics_collector().get_metrics_json()


def get_metrics_summary() -> Dict[str, Any]:
    """Get metrics summary."""
    return get_metrics_collector().get_summary()
#!/usr/bin/env python3
"""
S4-Connector Prometheus Metrics Collector
Direct integration into S4-Connector for real-time operational metrics

This module provides metrics collection with automatic
Prometheus format file generation every 1 second.
"""

import threading
import time
import os
import copy
from collections import defaultdict
from typing import Dict, Any, Optional, Tuple, FrozenSet


class S4MetricsCollector:
    """
    Prometheus metrics collector for S4-Connector operations.
    
    Collects real operational metrics directly from S4-Connector sync operations
    and writes them to a Prometheus-compatible file every 1 second.
    """
    
    # Metric help texts
    METRIC_HELP = {
        's4_connector_changes_total': 'Total number of objects synchronized',
        's4_connector_rejections_total': 'Total number of rejected synchronizations',
        's4_connector_last_sync_timestamp': 'Unix timestamp of last successful synchronization',
        's4_connector_sync_duration_seconds': 'Duration of synchronization operations in seconds',
        's4_connector_cache_entries': 'Number of entries in cache',
        's4_connector_usn': 'Current Update Sequence Number (USN) value',
        's4_connector_locks_active': 'Number of currently active locks',
    }
    
    # Metric types
    METRIC_TYPES = {
        's4_connector_changes_total': 'counter',
        's4_connector_rejections_total': 'counter',
        's4_connector_last_sync_timestamp': 'gauge',
        's4_connector_sync_duration_seconds': 'gauge',
        's4_connector_cache_entries': 'gauge',
        's4_connector_usn': 'gauge',
        's4_connector_locks_active': 'gauge',
    }
    
    def __init__(self, metrics_file_path: str = "/var/lib/prometheus/node-exporter/test-s4.prom"):
        """
        Initialize the metrics collector.
        
        Args:
            metrics_file_path: Path where Prometheus metrics file will be written
        """
        self.metrics_file_path = metrics_file_path
        
        # Thread-safe storage for metrics
        self._lock = threading.RLock()
        self._counters: Dict[Tuple[str, FrozenSet], float] = {}
        self._gauges: Dict[Tuple[str, FrozenSet], float] = {}
        
        # Background writer thread management
        self._writer_thread: Optional[threading.Thread] = None
        self._shutdown_event = threading.Event()
        
        # Ensure directory exists
        self._ensure_directory()
    
    def _ensure_directory(self):
        """Ensure the metrics file directory exists."""
        directory = os.path.dirname(self.metrics_file_path)
        if directory and not os.path.exists(directory):
            try:
                os.makedirs(directory, mode=0o755, exist_ok=True)
            except (OSError, IOError):
                pass  # Will handle errors during write
    
    def increment_counter(self, metric_name: str, labels: Optional[Dict[str, str]] = None, value: float = 1.0):
        """
        Thread-safe increment of a counter metric.
        
        Args:
            metric_name: Name of the metric (e.g., 's4_connector_changes_total')
            labels: Optional dict of label key-value pairs
            value: Amount to increment by (default 1.0)
        """
        if labels is None:
            labels = {}
        
        # Create immutable key for the metric
        label_set = frozenset(labels.items())
        key = (metric_name, label_set)
        
        with self._lock:
            current = self._counters.get(key, 0.0)
            self._counters[key] = current + value
    
    def set_gauge(self, metric_name: str, labels: Optional[Dict[str, str]] = None, value: float = 0.0):
        """
        Thread-safe update of a gauge metric.
        
        Args:
            metric_name: Name of the metric (e.g., 's4_connector_sync_duration_seconds')
            labels: Optional dict of label key-value pairs
            value: New value for the gauge
        """
        if labels is None:
            labels = {}
        
        # Create immutable key for the metric
        label_set = frozenset(labels.items())
        key = (metric_name, label_set)
        
        with self._lock:
            self._gauges[key] = float(value)
    
    def start_writer_thread(self):
        """
        Start the background thread that writes metrics to file every second.
        """
        with self._lock:
            # Don't start if already running
            if self._writer_thread and self._writer_thread.is_alive():
                return
            
            # Reset shutdown event
            self._shutdown_event.clear()
            
            # Create and start writer thread
            self._writer_thread = threading.Thread(
                target=self._writer_loop,
                name="S4MetricsWriter",
                daemon=True
            )
            self._writer_thread.start()
    
    def stop_writer_thread(self):
        """
        Gracefully stop the background writer thread.
        """
        # Signal shutdown
        self._shutdown_event.set()
        
        # Wait for thread to finish (with timeout)
        if self._writer_thread and self._writer_thread.is_alive():
            self._writer_thread.join(timeout=2.0)
        
        # Write final metrics
        try:
            self._write_metrics_file()
        except Exception:
            pass  # Best effort on shutdown
    
    def _writer_loop(self):
        """
        Background thread loop that writes metrics every second.
        """
        while not self._shutdown_event.wait(timeout=1.0):
            try:
                self._write_metrics_file()
            except Exception:
                # Log error but continue
                # In real implementation, would use univention.debug
                pass
    
    def _write_metrics_file(self):
        """
        Write current metrics to file in Prometheus format.
        Uses atomic write (temp file + rename) to prevent partial reads.
        """
        try:
            # Generate Prometheus format output
            output = self._format_prometheus_output()
            
            # Write to temp file first (atomic operation)
            temp_path = f"{self.metrics_file_path}.tmp"
            with open(temp_path, 'w') as f:
                f.write(output)
                f.flush()
                os.fsync(f.fileno())
            
            # Atomic rename
            os.rename(temp_path, self.metrics_file_path)
            
            # Ensure file is world-readable for Prometheus
            try:
                os.chmod(self.metrics_file_path, 0o644)
            except OSError:
                pass  # If we can't change permissions, continue anyway
            
        except (OSError, IOError) as e:
            # Handle write errors gracefully
            # In real implementation, would log with univention.debug
            # Clean up temp file if it exists
            temp_path = f"{self.metrics_file_path}.tmp"
            if os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                except OSError:
                    pass
    
    def _format_prometheus_output(self) -> str:
        """
        Generate Prometheus exposition format output.
        
        Returns:
            String containing all metrics in Prometheus format
        """
        lines = []
        
        # Get snapshot of metrics under lock
        with self._lock:
            counters_copy = copy.deepcopy(self._counters)
            gauges_copy = copy.deepcopy(self._gauges)
        
        # Collect all unique metric names
        all_metrics = set()
        for (name, _), _ in counters_copy.items():
            all_metrics.add(name)
        for (name, _), _ in gauges_copy.items():
            all_metrics.add(name)
        
        # Sort metrics for consistent output
        for metric_name in sorted(all_metrics):
            # Add HELP and TYPE lines
            help_text = self.METRIC_HELP.get(metric_name, f"Metric {metric_name}")
            metric_type = self.METRIC_TYPES.get(metric_name, 'untyped')
            
            lines.append(f"# HELP {metric_name} {help_text}")
            lines.append(f"# TYPE {metric_name} {metric_type}")
            
            # Add metric values from counters
            metric_lines = []
            for (name, label_set), value in counters_copy.items():
                if name == metric_name:
                    metric_lines.append(self._format_metric_line(name, label_set, value))
            
            # Add metric values from gauges
            for (name, label_set), value in gauges_copy.items():
                if name == metric_name:
                    metric_lines.append(self._format_metric_line(name, label_set, value))
            
            # Sort metric lines for consistent output
            for line in sorted(metric_lines):
                lines.append(line)
            
            # Add blank line between metrics
            if metric_lines:
                lines.append("")
        
        return '\n'.join(lines)
    
    def _format_metric_line(self, name: str, label_set: FrozenSet, value: float) -> str:
        """
        Format a single metric line with labels.
        
        Args:
            name: Metric name
            label_set: Frozen set of label tuples
            value: Metric value
        
        Returns:
            Formatted metric line
        """
        # Format labels if present
        if label_set:
            labels = []
            for key, val in sorted(label_set):
                escaped_val = self._escape_label_value(val)
                labels.append(f'{key}="{escaped_val}"')
            label_str = '{' + ','.join(labels) + '}'
        else:
            label_str = ''
        
        # Format value (remove unnecessary decimals)
        if isinstance(value, float) and value.is_integer():
            value_str = str(int(value))
        else:
            value_str = str(value)
        
        return f"{name}{label_str} {value_str}"
    
    def _escape_label_value(self, value: str) -> str:
        """
        Escape special characters in label values for Prometheus format.
        
        Args:
            value: Label value to escape
        
        Returns:
            Escaped value
        """
        value = str(value)
        value = value.replace('\\', '\\\\')
        value = value.replace('"', '\\"')
        value = value.replace('\n', '\\n')
        return value
    
    def _get_metrics_snapshot(self) -> Dict[str, Any]:
        """
        Get a snapshot of current metrics (for testing).
        
        Returns:
            Dict with 'counters' and 'gauges' snapshots
        """
        with self._lock:
            return {
                'counters': copy.deepcopy(self._counters),
                'gauges': copy.deepcopy(self._gauges)
            }


# Global metrics instance management
_metrics_instance: Optional[S4MetricsCollector] = None
_metrics_lock = threading.Lock()


def get_metrics() -> S4MetricsCollector:
    """
    Get or create the global metrics instance.
    
    Returns:
        The global S4MetricsCollector instance
    """
    global _metrics_instance
    
    if _metrics_instance is None:
        with _metrics_lock:
            if _metrics_instance is None:
                _metrics_instance = S4MetricsCollector()
                _metrics_instance.start_writer_thread()
    
    return _metrics_instance


def shutdown_metrics():
    """
    Shutdown the global metrics instance gracefully.
    """
    global _metrics_instance
    
    if _metrics_instance:
        _metrics_instance.stop_writer_thread()
        _metrics_instance = None

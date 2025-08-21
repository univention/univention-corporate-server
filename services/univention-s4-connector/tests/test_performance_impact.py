#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""
Test suite for performance impact assessment.
Part of Phase 5: Integration Testing.
"""

import logging
import os
import sys
import tempfile
import threading
import time
import unittest

import psutil


sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'modules'))

# Constants for performance testing
PERFORMANCE_TEST_OPERATIONS = 1024
MEMORY_OVERHEAD_THRESHOLD_MB = 10.0
CPU_OVERHEAD_THRESHOLD_PERCENT = 5.0
TEST_DURATION_SECONDS = 5
MEASUREMENT_INTERVAL_SECONDS = 0.1
MEMORY_TEST_METRICS = 1000
CPU_MEASUREMENT_ITERATIONS = 5
CPU_TEST_OPERATIONS = 100


class TestPerformanceImpact(unittest.TestCase):
    """Measure performance impact of metrics collection."""

    def setUp(self):
        """Set up test environment."""
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.prom')
        self.metrics_file = self.temp_file.name
        self.temp_file.close()
        self.process = psutil.Process()

    def tearDown(self):
        """Clean up test environment."""
        if os.path.exists(self.metrics_file):
            os.unlink(self.metrics_file)

    def test_memory_usage_impact(self):
        """Measure memory overhead of metrics collection."""
        from univention.s4connector.prometheus_metrics import S4MetricsCollector

        baseline_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        collector = S4MetricsCollector(self.metrics_file)
        collector.start_writer_thread()
        for i in range(MEMORY_TEST_METRICS):
            collector.increment_counter('counter_' + str(i % 100),
                                        {'label': str(i % 10)}, 1)
            collector.set_gauge('gauge_' + str(i % 50),
                                {'label': str(i % 5)}, float(i))

        # Wait for writer thread
        time.sleep(1.5)

        metrics_memory = self.process.memory_info().rss / 1024 / 1024  # MB

        collector.stop_writer_thread()
        memory_overhead = metrics_memory - baseline_memory
        assert memory_overhead < 10.0, f"Memory overhead {memory_overhead:.2f}MB exceeds 10MB threshold"

        # Performance report (useful for debugging)
        logging.info("Memory Report: Baseline=%.2f MB, With metrics=%.2f MB, Overhead=%.2f MB",
                     baseline_memory, metrics_memory, memory_overhead)

    def test_cpu_usage_impact(self):
        """Measure CPU overhead of metrics thread."""
        from univention.s4connector.prometheus_metrics import S4MetricsCollector

        collector = S4MetricsCollector(self.metrics_file)
        baseline_cpu_percent = []
        for _ in range(CPU_MEASUREMENT_ITERATIONS):
            baseline_cpu_percent.append(self.process.cpu_percent(interval=0.1))
        baseline_avg = sum(baseline_cpu_percent) / len(baseline_cpu_percent)

        collector.start_writer_thread()

        def generate_metrics():
            for _ in range(CPU_TEST_OPERATIONS):
                collector.increment_counter('test_counter', {}, 1)
                collector.set_gauge('test_gauge', {}, time.time())
                time.sleep(0.01)

        thread = threading.Thread(target=generate_metrics)
        thread.start()
        metrics_cpu_percent = []
        for _ in range(CPU_MEASUREMENT_ITERATIONS):
            metrics_cpu_percent.append(self.process.cpu_percent(interval=0.1))
        metrics_avg = sum(metrics_cpu_percent) / len(metrics_cpu_percent)

        thread.join()
        collector.stop_writer_thread()
        cpu_overhead = metrics_avg - baseline_avg
        assert cpu_overhead < 5.0, f"CPU overhead {cpu_overhead:.2f}% exceeds 5% threshold"

        # Performance report (useful for debugging)
        logging.info("CPU Report: Baseline=%.2f%%, With metrics=%.2f%%, Overhead=%.2f%%",
                     baseline_avg, metrics_avg, cpu_overhead)


if __name__ == '__main__':
    unittest.main()

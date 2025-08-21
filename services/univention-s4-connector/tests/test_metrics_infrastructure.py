#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""
Test suite for S4MetricsCollector thread-safe operations.
Part of Phase 1: Metrics Infrastructure.
"""

import os
import sys
import tempfile
import threading
import time
import unittest


sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'modules'))


class TestMetricsInfrastructure(unittest.TestCase):
    """Test thread-safe counter operations and concurrent metric updates."""

    def setUp(self):
        """Set up test environment."""
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.prom')
        self.metrics_file = self.temp_file.name
        self.temp_file.close()

    def tearDown(self):
        """Clean up test environment."""
        if os.path.exists(self.metrics_file):
            os.unlink(self.metrics_file)

    def test_counter_increment_thread_safety(self):
        """Test that counter increments are atomic across threads."""
        from univention.s4connector.prometheus_metrics import S4MetricsCollector

        collector = S4MetricsCollector(self.metrics_file)

        def worker():
            for _ in range(1000):
                collector.increment_counter(
                    's4_connector_changes_total',
                    {'direction': 's4_to_ucs', 'object_type': 'user'}, 1)

        threads = []
        for _ in range(10):
            t = threading.Thread(target=worker)
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # Verify total count is exactly 10000
        metrics = collector._get_metrics_snapshot()
        counter_key = (
            's4_connector_changes_total',
            frozenset([('direction', 's4_to_ucs'), ('object_type', 'user')]),
        )
        assert metrics['counters'].get(counter_key, 0) == 10000

    def test_gauge_update_thread_safety(self):
        """Test that gauge updates don't interfere with each other."""
        from univention.s4connector.prometheus_metrics import S4MetricsCollector

        collector = S4MetricsCollector(self.metrics_file)

        def worker(worker_id):
            for i in range(100):
                collector.set_gauge('s4_connector_usn', {'source': f'worker_{worker_id}'}, float(i))
                time.sleep(0.001)  # Small delay to increase chance of conflicts

        threads = []
        for worker_id in range(5):
            t = threading.Thread(target=worker, args=(worker_id, ))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # Verify each worker's gauge has final value of 99
        metrics = collector._get_metrics_snapshot()
        for worker_id in range(5):
            gauge_key = (
                's4_connector_usn',
                frozenset([('source', f'worker_{worker_id}')]),
            )
            assert metrics['gauges'].get(gauge_key, 0) == 99.0

    def test_concurrent_metric_writes(self):
        """Test multiple threads updating different metrics simultaneously."""
        from univention.s4connector.prometheus_metrics import S4MetricsCollector

        collector = S4MetricsCollector(self.metrics_file)

        def counter_worker():
            for _ in range(500):
                collector.increment_counter(
                    's4_connector_changes_total',
                    {'direction': 'ucs_to_s4', 'object_type': 'user'}, 1)

        def gauge_worker():
            for i in range(500):
                collector.set_gauge(
                    's4_connector_sync_duration_seconds',
                    {'direction': 's4_to_ucs', 'operation': 'sync'}, float(i) / 100)

        def timestamp_worker():
            for _ in range(500):
                collector.set_gauge(
                    's4_connector_last_sync_timestamp',
                    {'direction': 'ucs_to_s4'}, time.time())

        threads = []
        for worker_func in [counter_worker, gauge_worker, timestamp_worker]:
            for _ in range(3):
                t = threading.Thread(target=worker_func)
                threads.append(t)
                t.start()

        for t in threads:
            t.join()

        metrics = collector._get_metrics_snapshot()

        # Check counter total (3 threads * 500 increments)
        counter_key = (
            's4_connector_changes_total',
            frozenset([('direction', 'ucs_to_s4'), ('object_type', 'user')]),
        )
        assert metrics['counters'].get(counter_key, 0) == 1500
        gauge_key = (
            's4_connector_sync_duration_seconds',
            frozenset([('direction', 's4_to_ucs'), ('operation', 'sync')]),
        )
        assert gauge_key in metrics['gauges']

        timestamp_key = (
            's4_connector_last_sync_timestamp',
            frozenset([('direction', 'ucs_to_s4')]),
        )
        assert timestamp_key in metrics['gauges']

    def test_metric_isolation(self):
        """Test that different metric types and labels are properly isolated."""
        from univention.s4connector.prometheus_metrics import S4MetricsCollector

        collector = S4MetricsCollector(self.metrics_file)

        collector.increment_counter(
            's4_connector_changes_total',
            {'direction': 's4_to_ucs', 'object_type': 'user'}, 10)
        collector.increment_counter(
            's4_connector_changes_total',
            {'direction': 's4_to_ucs', 'object_type': 'group'}, 5)
        collector.increment_counter(
            's4_connector_changes_total',
            {'direction': 'ucs_to_s4', 'object_type': 'user'}, 7)

        metrics = collector._get_metrics_snapshot()

        key1 = (
            's4_connector_changes_total',
            frozenset([('direction', 's4_to_ucs'), ('object_type', 'user')]),
        )
        key2 = (
            's4_connector_changes_total',
            frozenset([('direction', 's4_to_ucs'), ('object_type', 'group')]),
        )
        key3 = (
            's4_connector_changes_total',
            frozenset([('direction', 'ucs_to_s4'), ('object_type', 'user')]),
        )

        assert metrics['counters'].get(key1, 0) == 10
        assert metrics['counters'].get(key2, 0) == 5
        assert metrics['counters'].get(key3, 0) == 7


if __name__ == '__main__':
    unittest.main()

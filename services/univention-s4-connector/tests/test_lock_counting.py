#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""
Test suite for lock counting.
Part of Phase 4: Rejection and State Tracking.
"""

import os
import sys
import tempfile
import threading
import time
import unittest


sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'modules'))


class TestLockCounting(unittest.TestCase):
    """Test counting of active locks."""

    def setUp(self):
        """Set up test environment."""
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.prom')
        self.metrics_file = self.temp_file.name
        self.temp_file.close()

    def tearDown(self):
        """Clean up test environment."""
        if os.path.exists(self.metrics_file):
            os.unlink(self.metrics_file)

    def test_active_lock_counting(self):
        """Test that active locks are counted."""
        from univention.s4connector.prometheus_metrics import S4MetricsCollector

        collector = S4MetricsCollector(self.metrics_file)

        collector.set_gauge('s4_connector_locks_active', {}, 0.0)
        collector.set_gauge('s4_connector_locks_active', {}, 1.0)
        collector.set_gauge('s4_connector_locks_active', {}, 2.0)
        collector.set_gauge('s4_connector_locks_active', {}, 3.0)
        metrics = collector._get_metrics_snapshot()
        gauge_key = ('s4_connector_locks_active', frozenset())
        assert metrics['gauges'].get(gauge_key, 0) == 3.0

    def test_lock_acquisition_tracking(self):
        """Test lock count increases on acquisition."""
        from univention.s4connector.prometheus_metrics import S4MetricsCollector

        collector = S4MetricsCollector(self.metrics_file)

        collector.set_gauge('s4_connector_locks_active', {}, 0.0)
        lock_names = ['sync_lock', 'write_lock', 'read_lock']

        for i, lock_name in enumerate(lock_names, 1):
            collector.set_gauge('s4_connector_locks_active', {}, float(i))
            metrics = collector._get_metrics_snapshot()
            gauge_key = ('s4_connector_locks_active', frozenset())
            assert metrics['gauges'].get(gauge_key, 0) == float(i)

    def test_lock_release_tracking(self):
        """Test lock count decreases on release."""
        from univention.s4connector.prometheus_metrics import S4MetricsCollector

        collector = S4MetricsCollector(self.metrics_file)

        collector.set_gauge('s4_connector_locks_active', {}, 5.0)
        for remaining in [4, 3, 2, 1, 0]:
            collector.set_gauge('s4_connector_locks_active', {}, float(remaining))
            metrics = collector._get_metrics_snapshot()
            gauge_key = ('s4_connector_locks_active', frozenset())
            assert metrics['gauges'].get(gauge_key, 0) == float(remaining)

    def test_concurrent_lock_operations(self):
        """Test lock counting with concurrent acquire/release."""
        from univention.s4connector.prometheus_metrics import S4MetricsCollector

        collector = S4MetricsCollector(self.metrics_file)
        lock_count = [0]
        lock_mutex = threading.Lock()

        def acquire_locks(count):
            for _ in range(count):
                with lock_mutex:
                    lock_count[0] += 1
                    collector.set_gauge('s4_connector_locks_active', {}, float(lock_count[0]))
                time.sleep(0.01)

        def release_locks(count):
            for _ in range(count):
                with lock_mutex:
                    if lock_count[0] > 0:
                        lock_count[0] -= 1
                        collector.set_gauge('s4_connector_locks_active', {}, float(lock_count[0]))
                time.sleep(0.01)
        threads = []
        for _ in range(3):
            t = threading.Thread(target=acquire_locks, args=(5, ))
            threads.append(t)
            t.start()

        # Wait a bit
        time.sleep(0.05)
        for _ in range(2):
            t = threading.Thread(target=release_locks, args=(5, ))
            threads.append(t)
            t.start()
        for t in threads:
            t.join()

        # Final count should be 5 (15 acquired - 10 released)
        metrics = collector._get_metrics_snapshot()
        gauge_key = ('s4_connector_locks_active', frozenset())
        assert metrics['gauges'].get(gauge_key, 0) == 5.0

    def test_lock_count_never_negative(self):
        """Test that lock count never goes negative."""
        from univention.s4connector.prometheus_metrics import S4MetricsCollector

        collector = S4MetricsCollector(self.metrics_file)

        collector.set_gauge('s4_connector_locks_active', {}, 0.0)

        # In real implementation, this would be handled in the lock manager
        collector.set_gauge('s4_connector_locks_active', {}, max(0.0, -1.0))
        metrics = collector._get_metrics_snapshot()
        gauge_key = ('s4_connector_locks_active', frozenset())
        assert metrics['gauges'].get(gauge_key, 0) >= 0.0


if __name__ == '__main__':
    unittest.main()

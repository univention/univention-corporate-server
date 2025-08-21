#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""
Test suite for background thread lifecycle.
Part of Phase 1: Metrics Infrastructure.
"""

import os
import sys
import tempfile
import threading
import time
import unittest


sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'modules'))


class TestThreadLifecycle(unittest.TestCase):
    """Test background writer thread lifecycle management."""

    def setUp(self):
        """Set up test environment."""
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.prom')
        self.metrics_file = self.temp_file.name
        self.temp_file.close()

    def tearDown(self):
        """Clean up test environment."""
        if os.path.exists(self.metrics_file):
            os.unlink(self.metrics_file)

    def test_metrics_thread_startup(self):
        """Test that metrics thread starts with S4-Connector."""
        from univention.s4connector.prometheus_metrics import S4MetricsCollector

        collector = S4MetricsCollector(self.metrics_file)

        assert collector._writer_thread is None

        collector.start_writer_thread()
        assert collector._writer_thread is not None
        assert collector._writer_thread.is_alive()
        assert not collector._shutdown_event.is_set()

        collector.increment_counter('test', {}, 1)

        # Wait for at least one write
        time.sleep(1.2)
        assert os.path.exists(self.metrics_file)

        collector.stop_writer_thread()

    def test_metrics_thread_shutdown(self):
        """Test graceful shutdown of metrics thread."""
        from univention.s4connector.prometheus_metrics import S4MetricsCollector

        collector = S4MetricsCollector(self.metrics_file)

        collector.start_writer_thread()
        assert collector._writer_thread.is_alive()
        collector.increment_counter(
            's4_connector_changes_total',
            {'direction': 's4_to_ucs', 'object_type': 'user'}, 42)

        collector.stop_writer_thread()
        assert not collector._writer_thread.is_alive()
        assert collector._shutdown_event.is_set()

        assert os.path.exists(self.metrics_file)
        with open(self.metrics_file) as f:
            content = f.read()
            assert 's4_connector_changes_total' in content

    def test_double_start_prevention(self):
        """Test that starting thread twice doesn't create multiple threads."""
        from univention.s4connector.prometheus_metrics import S4MetricsCollector

        collector = S4MetricsCollector(self.metrics_file)

        collector.start_writer_thread()
        first_thread = collector._writer_thread

        collector.start_writer_thread()
        second_thread = collector._writer_thread
        assert first_thread == second_thread

        # Only one thread should be running
        assert threading.active_count() == 2  # Main + writer

        collector.stop_writer_thread()

    def test_shutdown_timeout(self):
        """Test that shutdown has a timeout and doesn't hang."""
        from univention.s4connector.prometheus_metrics import S4MetricsCollector

        collector = S4MetricsCollector(self.metrics_file)

        collector.start_writer_thread()

        # Mock the thread join to simulate hanging
        original_join = collector._writer_thread.join

        def slow_join(timeout=None):
            # Simulate slow shutdown
            time.sleep(0.5)
            return original_join(0)

        collector._writer_thread.join = slow_join

        # Shutdown should complete even if thread is slow
        start_time = time.time()
        collector.stop_writer_thread()
        shutdown_time = time.time() - start_time

        # Should have a reasonable timeout (e.g., 2 seconds)
        assert shutdown_time < 3.0

    def test_thread_daemon_mode(self):
        """Test that writer thread is properly set as daemon."""
        from univention.s4connector.prometheus_metrics import S4MetricsCollector

        collector = S4MetricsCollector(self.metrics_file)

        collector.start_writer_thread()
        assert collector._writer_thread.daemon

        collector.stop_writer_thread()


if __name__ == '__main__':
    unittest.main()

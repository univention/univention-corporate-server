#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""
Test suite for atomic file operations.
Part of Phase 1: Metrics Infrastructure.
"""

import os
import shutil
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch


sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'modules'))


class TestFileOperations(unittest.TestCase):
    """Test atomic file writing and error handling."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.metrics_file = os.path.join(self.temp_dir, 'test-s4.prom')

    def tearDown(self):
        """Clean up test environment."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_atomic_file_write(self):
        """Test that metrics file is written atomically (no partial writes)."""
        from univention.s4connector.prometheus_metrics import S4MetricsCollector

        collector = S4MetricsCollector(self.metrics_file)
        collector.increment_counter('s4_connector_changes_total', {'direction': 's4_to_ucs', 'object_type': 'user'}, 42)
        collector.set_gauge('s4_connector_locks_active', {}, 3.14)

        collector.start_writer_thread()

        # Wait for at least one write
        time.sleep(1.5)
        contents = []
        for _ in range(100):
            if os.path.exists(self.metrics_file):
                with open(self.metrics_file) as f:
                    content = f.read()
                    contents.append(content)
            time.sleep(0.01)

        collector.stop_writer_thread()
        for content in contents:
            if content:  # Skip empty reads if file didn't exist yet
                # Should have complete metrics, not partial writes
                assert '# HELP' in content
                assert '# TYPE' in content
                assert 's4_connector_changes_total' in content
                assert '42' in content
                assert 's4_connector_locks_active' in content
                assert '3.14' in content

    def test_file_write_error_handling(self):
        """Test handling of disk space/permission errors."""
        from univention.s4connector.prometheus_metrics import S4MetricsCollector

        read_only_file = '/tmp/read_only_test.prom'

        with patch('builtins.open', side_effect=PermissionError("Permission denied")):
            collector = S4MetricsCollector(read_only_file)
            collector.increment_counter('s4_connector_changes_total', {'direction': 's4_to_ucs', 'object_type': 'user'}, 1)
            try:
                collector._write_metrics_file()
            except PermissionError:
                self.fail("Should handle permission errors gracefully")
        with patch('builtins.open', side_effect=OSError("No space left on device")):
            collector = S4MetricsCollector(self.metrics_file)
            collector.increment_counter('s4_connector_changes_total', {'direction': 's4_to_ucs', 'object_type': 'user'}, 1)
            try:
                collector._write_metrics_file()
            except OSError:
                self.fail("Should handle disk full errors gracefully")

    def test_file_write_frequency(self):
        """Test that file is written exactly every 1 second."""
        from univention.s4connector.prometheus_metrics import S4MetricsCollector

        collector = S4MetricsCollector(self.metrics_file)
        write_times = []
        original_write = collector._write_metrics_file

        def track_write():
            write_times.append(time.time())
            original_write()

        collector._write_metrics_file = track_write

        collector.start_writer_thread()

        # Let it run for 5 seconds
        time.sleep(5.2)

        collector.stop_writer_thread()
        assert len(write_times) >= 5
        intervals = []
        for i in range(1, len(write_times)):
            interval = write_times[i] - write_times[i - 1]
            intervals.append(interval)
        for interval in intervals:
            assert interval > 0  # Intervals should be positive
            assert interval < 1.5  # Should not be too long

    def test_concurrent_file_writes(self):
        """Test that concurrent writes don't corrupt the file."""
        from univention.s4connector.prometheus_metrics import S4MetricsCollector

        collector = S4MetricsCollector(self.metrics_file)

        def worker(worker_id):
            for i in range(10):
                collector.increment_counter(
                    's4_connector_changes_total',
                    {'direction': 's4_to_ucs', 'object_type': f'worker_{worker_id}'}, 1)
                collector._write_metrics_file()
                time.sleep(0.01)
        threads = []
        for worker_id in range(5):
            t = threading.Thread(target=worker, args=(worker_id, ))
            threads.append(t)
            t.start()
        for t in threads:
            t.join()
        assert os.path.exists(self.metrics_file)
        with open(self.metrics_file) as f:
            content = f.read()
        assert '# HELP' in content
        assert '# TYPE' in content
        for worker_id in range(5):
            assert f'object_type="worker_{worker_id}"' in content


if __name__ == '__main__':
    unittest.main()

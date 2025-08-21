#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""
Full integration test suite.
Part of Phase 5: Integration Testing.
"""

import os
import sys
import tempfile
import threading
import time
import unittest


sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'modules'))


class TestFullIntegration(unittest.TestCase):
    """Test complete S4-Connector sync cycles with metrics."""

    def setUp(self):
        """Set up test environment."""
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.prom')
        self.metrics_file = self.temp_file.name
        self.temp_file.close()

    def tearDown(self):
        """Clean up test environment."""
        if os.path.exists(self.metrics_file):
            os.unlink(self.metrics_file)

    def test_mixed_object_sync_metrics(self):
        """Test metrics with users, groups, and computers in single sync."""
        from univention.s4connector.prometheus_metrics import S4MetricsCollector

        collector = S4MetricsCollector(self.metrics_file)
        object_counts = {
            'user': 25,
            'group': 10,
            'computer': 15,
            'other': 5,
        }

        for obj_type, count in object_counts.items():
            collector.increment_counter(
                's4_connector_changes_total',
                {'direction': 's4_to_ucs', 'object_type': obj_type},
                count)
        metrics = collector._get_metrics_snapshot()

        for obj_type, expected_count in object_counts.items():
            counter_key = (
                's4_connector_changes_total',
                frozenset([('direction', 's4_to_ucs'), ('object_type', obj_type)]),
            )
            actual_count = metrics['counters'].get(counter_key, 0)
            assert actual_count == expected_count
        total = sum(object_counts.values())
        assert total == 55

    def test_concurrent_bidirectional_sync(self):
        """Test metrics during simultaneous UCS→S4 and S4→UCS syncs."""
        from univention.s4connector.prometheus_metrics import S4MetricsCollector

        collector = S4MetricsCollector(self.metrics_file)

        results = {'s4_to_ucs': 0, 'ucs_to_s4': 0}

        def sync_from_s4():
            for _ in range(50):
                collector.increment_counter(
                    's4_connector_changes_total',
                    {'direction': 's4_to_ucs', 'object_type': 'user'}, 1)
                results['s4_to_ucs'] += 1
                time.sleep(0.001)

        def sync_from_ucs():
            for _ in range(30):
                collector.increment_counter(
                    's4_connector_changes_total',
                    {'direction': 'ucs_to_s4', 'object_type': 'group'}, 1)
                results['ucs_to_s4'] += 1
                time.sleep(0.001)
        t1 = threading.Thread(target=sync_from_s4)
        t2 = threading.Thread(target=sync_from_ucs)

        t1.start()
        t2.start()

        t1.join()
        t2.join()
        metrics = collector._get_metrics_snapshot()

        s4_key = (
            's4_connector_changes_total',
            frozenset([('direction', 's4_to_ucs'), ('object_type', 'user')]),
        )
        ucs_key = (
            's4_connector_changes_total',
            frozenset([('direction', 'ucs_to_s4'), ('object_type', 'group')]),
        )

        assert metrics['counters'].get(s4_key, 0) == 50
        assert metrics['counters'].get(ucs_key, 0) == 30


if __name__ == '__main__':
    unittest.main()

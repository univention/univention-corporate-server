#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""
Test suite for change counter accuracy.
Part of Phase 2: Poll Operation Integration.
"""

import os
import sys
import tempfile
import unittest


sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'modules'))


class TestChangeCounting(unittest.TestCase):
    """Test accuracy of change counting in metrics."""

    def setUp(self):
        """Set up test environment."""
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.prom')
        self.metrics_file = self.temp_file.name
        self.temp_file.close()

    def tearDown(self):
        """Clean up test environment."""
        if os.path.exists(self.metrics_file):
            os.unlink(self.metrics_file)

    def test_change_counter_matches_actual_changes(self):
        """Test that metrics counters match actual objects processed."""
        from univention.s4connector.prometheus_metrics import S4MetricsCollector

        collector = S4MetricsCollector(self.metrics_file)
        objects_processed = [
            {'dn': 'uid=user1, ou=users, dc=test', 'changes': 1},
            {'dn': 'uid=user2, ou=users, dc=test', 'changes': 1},
            {'dn': 'cn=group1, ou=groups, dc=test', 'changes': 1},
        ]

        total_changes = sum(obj['changes'] for obj in objects_processed)
        collector.increment_counter(
            's4_connector_changes_total',
            {'direction': 's4_to_ucs', 'object_type': 'user'},
            total_changes,
        )
        metrics = collector._get_metrics_snapshot()
        counter_key = ('s4_connector_changes_total',
                       frozenset([('direction', 's4_to_ucs'), ('object_type', 'user')]))
        assert metrics['counters'].get(counter_key, 0) == 3

    def test_change_counter_reset_behavior(self):
        """Test counter behavior across service restarts."""
        from univention.s4connector.prometheus_metrics import S4MetricsCollector

        collector1 = S4MetricsCollector(self.metrics_file)
        collector1.increment_counter(
            's4_connector_changes_total',
            {'direction': 's4_to_ucs', 'object_type': 'user'},
            100,
        )

        collector1._write_metrics_file()

        collector2 = S4MetricsCollector(self.metrics_file)

        # Counters should start fresh (not persisted)
        metrics = collector2._get_metrics_snapshot()
        counter_key = ('s4_connector_changes_total',
                       frozenset([('direction', 's4_to_ucs'), ('object_type', 'user')]))
        assert metrics['counters'].get(counter_key, 0) == 0
        collector2.increment_counter(
            's4_connector_changes_total',
            {'direction': 's4_to_ucs', 'object_type': 'user'},
            50,
        )

        metrics = collector2._get_metrics_snapshot()
        assert metrics['counters'].get(counter_key, 0) == 50

    def test_max_sync_limit_handling(self):
        """Test metrics when MAX_SYNC_IN_ONE_INTERVAL is reached."""
        from univention.s4connector.prometheus_metrics import S4MetricsCollector

        collector = S4MetricsCollector(self.metrics_file)
        # Simulate hitting max sync limit (typically 1000 in S4-Connector)
        MAX_SYNC_IN_ONE_INTERVAL = 1000
        collector.increment_counter(
            's4_connector_changes_total',
            {'direction': 's4_to_ucs', 'object_type': 'user'},
            MAX_SYNC_IN_ONE_INTERVAL,
        )
        remaining_changes = 234
        collector.increment_counter(
            's4_connector_changes_total',
            {'direction': 's4_to_ucs', 'object_type': 'user'},
            remaining_changes,
        )
        metrics = collector._get_metrics_snapshot()
        counter_key = ('s4_connector_changes_total',
                       frozenset([('direction', 's4_to_ucs'), ('object_type', 'user')]))
        total = metrics['counters'].get(counter_key, 0)
        assert total == MAX_SYNC_IN_ONE_INTERVAL + remaining_changes

    def test_incremental_counting(self):
        """Test that counters increment correctly over multiple polls."""
        from univention.s4connector.prometheus_metrics import S4MetricsCollector

        collector = S4MetricsCollector(self.metrics_file)
        poll_results = [5, 10, 0, 3, 7, 0, 15]

        for changes in poll_results:
            if changes > 0:
                collector.increment_counter(
                    's4_connector_changes_total',
                    {'direction': 's4_to_ucs', 'object_type': 'user'},
                    changes,
                )
        expected_total = sum(poll_results)
        metrics = collector._get_metrics_snapshot()
        counter_key = ('s4_connector_changes_total',
                       frozenset([('direction', 's4_to_ucs'), ('object_type', 'user')]))
        assert metrics['counters'].get(counter_key, 0) == expected_total

    def test_separate_direction_counting(self):
        """Test that each direction maintains separate counters."""
        from univention.s4connector.prometheus_metrics import S4MetricsCollector

        collector = S4MetricsCollector(self.metrics_file)
        collector.increment_counter(
            's4_connector_changes_total',
            {'direction': 's4_to_ucs', 'object_type': 'user'},
            25,
        )
        collector.increment_counter(
            's4_connector_changes_total',
            {'direction': 'ucs_to_s4', 'object_type': 'group'},
            10,
        )
        collector.increment_counter(
            's4_connector_changes_total',
            {'direction': 's4_to_ucs', 'object_type': 'user'},
            5,
        )
        metrics = collector._get_metrics_snapshot()

        s4_key = ('s4_connector_changes_total',
                  frozenset([('direction', 's4_to_ucs'), ('object_type', 'user')]))
        ucs_key = ('s4_connector_changes_total',
                   frozenset([('direction', 'ucs_to_s4'), ('object_type', 'group')]))

        assert metrics['counters'].get(s4_key, 0) == 30  # 25 + 5
        assert metrics['counters'].get(ucs_key, 0) == 10


if __name__ == '__main__':
    unittest.main()

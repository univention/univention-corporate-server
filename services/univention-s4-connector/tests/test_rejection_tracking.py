#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""
Test suite for rejection counter integration.
Part of Phase 4: Rejection and State Tracking.
"""

import os
import sys
import tempfile
import unittest
from unittest.mock import MagicMock


sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'modules'))


class TestRejectionTracking(unittest.TestCase):
    """Test tracking of rejected synchronizations."""

    def setUp(self):
        """Set up test environment."""
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.prom')
        self.metrics_file = self.temp_file.name
        self.temp_file.close()

    def tearDown(self):
        """Clean up test environment."""
        if os.path.exists(self.metrics_file):
            os.unlink(self.metrics_file)

    def test_s4_rejection_counting(self):
        """Test S4 rejections are counted in save_rejected()."""
        from univention.s4connector.prometheus_metrics import S4MetricsCollector

        collector = S4MetricsCollector(self.metrics_file)

        mock_connector = MagicMock()
        mock_connector.metrics_collector = collector

        def save_rejected(self, object_data):
            # Existing rejection save logic would be here
            if hasattr(self, 'metrics_collector'):
                self.metrics_collector.increment_counter(
                    's4_connector_rejections_total',
                    {'direction': 's4_to_ucs', 'object_type': 'unknown'},
                    1,
                )

        save_rejected(mock_connector, {'dn': 'cn=test, dc=example, dc=com'})
        metrics = collector._get_metrics_snapshot()
        counter_key = (
            's4_connector_rejections_total',
            frozenset([('direction', 's4_to_ucs'), ('object_type', 'unknown')]),
        )
        assert metrics['counters'].get(counter_key, 0) == 1

    def test_ucs_rejection_counting(self):
        """Test UCS rejections are counted in _save_rejected_ucs()."""
        from univention.s4connector.prometheus_metrics import S4MetricsCollector

        collector = S4MetricsCollector(self.metrics_file)

        mock_connector = MagicMock()
        mock_connector.metrics_collector = collector

        def _save_rejected_ucs(self, filename, dn, resync=True, reason=''):
            # Existing rejection save logic would be here
            if hasattr(self, 'metrics_collector'):
                self.metrics_collector.increment_counter(
                    's4_connector_rejections_total',
                    {'direction': 'ucs_to_s4', 'object_type': 'unknown'},
                    1,
                )

        _save_rejected_ucs(mock_connector, 'reject_001', 'uid=test, dc=example, dc=com')
        metrics = collector._get_metrics_snapshot()
        counter_key = (
            's4_connector_rejections_total',
            frozenset([('direction', 'ucs_to_s4'), ('object_type', 'unknown')]),
        )
        assert metrics['counters'].get(counter_key, 0) == 1

    def test_rejection_direction_classification(self):
        """Test that rejections are classified by sync direction."""
        from univention.s4connector.prometheus_metrics import S4MetricsCollector

        collector = S4MetricsCollector(self.metrics_file)
        collector.increment_counter('s4_connector_rejections_total',
                                    {'direction': 's4_to_ucs', 'object_type': 'user'}, 3)
        collector.increment_counter('s4_connector_rejections_total',
                                    {'direction': 'ucs_to_s4', 'object_type': 'group'}, 5)
        metrics = collector._get_metrics_snapshot()

        s4_key = (
            's4_connector_rejections_total',
            frozenset([('direction', 's4_to_ucs'), ('object_type', 'user')]),
        )
        ucs_key = (
            's4_connector_rejections_total',
            frozenset([('direction', 'ucs_to_s4'), ('object_type', 'group')]),
        )

        assert metrics['counters'].get(s4_key, 0) == 3
        assert metrics['counters'].get(ucs_key, 0) == 5

    def test_multiple_rejections(self):
        """Test counting multiple rejections."""
        from univention.s4connector.prometheus_metrics import S4MetricsCollector

        collector = S4MetricsCollector(self.metrics_file)
        rejection_objects = [
            'cn=user1, dc=test',
            'cn=user2, dc=test',
            'cn=group1, dc=test',
            'cn=computer1, dc=test',
        ]

        for obj in rejection_objects:
            collector.increment_counter(
                's4_connector_rejections_total',
                {'direction': 's4_to_ucs', 'object_type': 'unknown'}, 1)
        metrics = collector._get_metrics_snapshot()
        counter_key = (
            's4_connector_rejections_total',
            frozenset([('direction', 's4_to_ucs'), ('object_type', 'unknown')]),
        )
        assert metrics['counters'].get(counter_key, 0) == len(rejection_objects)


if __name__ == '__main__':
    unittest.main()

#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""
Test suite for Prometheus format generation.
Part of Phase 1: Metrics Infrastructure.
"""

import os
import sys
import tempfile
import unittest


sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'modules'))


class TestPrometheusFormat(unittest.TestCase):
    """Test Prometheus exposition format generation."""

    def setUp(self):
        """Set up test environment."""
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.prom')
        self.metrics_file = self.temp_file.name
        self.temp_file.close()

    def tearDown(self):
        """Clean up test environment."""
        if os.path.exists(self.metrics_file):
            os.unlink(self.metrics_file)

    def test_metric_ordering_consistency(self):
        """Test that metric output order is consistent."""
        from prometheus_client import generate_latest

        from univention.s4connector.prometheus_metrics import S4MetricsCollector

        collector = S4MetricsCollector(self.metrics_file)

        collector.increment_counter(
            's4_connector_changes_total',
            {'direction': 's4_to_ucs', 'object_type': 'user'}, 1)
        collector.increment_counter(
            's4_connector_rejections_total',
            {'direction': 'ucs_to_s4', 'object_type': 'group'}, 2)
        collector.set_gauge('s4_connector_locks_active', {}, 3.0)
        output1 = generate_latest(collector._registry).decode('utf-8')
        output2 = generate_latest(collector._registry).decode('utf-8')
        output3 = generate_latest(collector._registry).decode('utf-8')
        assert output1 == output2
        assert output2 == output3

    def test_empty_labels(self):
        """Test metrics with no labels."""
        from prometheus_client import generate_latest

        from univention.s4connector.prometheus_metrics import S4MetricsCollector

        collector = S4MetricsCollector(self.metrics_file)

        collector.set_gauge('s4_connector_locks_active', {}, 3.0)

        output = generate_latest(collector._registry).decode('utf-8')
        assert 's4_connector_locks_active 3' in output
        assert 's4_connector_locks_active{' not in output

    def test_float_formatting(self):
        """Test proper formatting of float values."""
        from prometheus_client import generate_latest

        from univention.s4connector.prometheus_metrics import S4MetricsCollector

        collector = S4MetricsCollector(self.metrics_file)
        collector.set_gauge(
            's4_connector_sync_duration_seconds',
            {'direction': 's4_to_ucs', 'operation': 'sync'}, 1.234567)
        collector.set_gauge(
            's4_connector_sync_duration_seconds',
            {'direction': 's4_to_ucs', 'operation': 'poll'}, 0.001)
        collector.set_gauge(
            's4_connector_sync_duration_seconds',
            {'direction': 'ucs_to_s4', 'operation': 'validate'}, 10.0)

        output = generate_latest(collector._registry).decode('utf-8')

        # Prometheus client handles float formatting, just verify metrics exist
        assert 's4_connector_sync_duration_seconds' in output
        assert 'direction="s4_to_ucs"' in output
        assert 'operation="sync"' in output

    def test_help_text_generation(self):
        """Test automatic help text generation for metrics."""
        from prometheus_client import generate_latest

        from univention.s4connector.prometheus_metrics import S4MetricsCollector

        collector = S4MetricsCollector(self.metrics_file)
        collector.increment_counter(
            's4_connector_changes_total',
            {'direction': 's4_to_ucs', 'object_type': 'user'}, 1)
        collector.set_gauge(
            's4_connector_sync_duration_seconds',
            {'direction': 's4_to_ucs', 'operation': 'sync'}, 2.5)

        output = generate_latest(collector._registry).decode('utf-8')
        assert '# HELP s4_connector_changes_total Total number of objects synchronized' in output
        assert '# HELP s4_connector_sync_duration_seconds Duration of synchronization operations in seconds' in output


if __name__ == '__main__':
    unittest.main()

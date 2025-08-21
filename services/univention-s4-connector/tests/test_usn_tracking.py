#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""
Test suite for USN tracking.
Part of Phase 4: Rejection and State Tracking.
"""

import os
import sys
import tempfile
import unittest


sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'modules'))


class TestUSNTracking(unittest.TestCase):
    """Test USN (Update Sequence Number) tracking."""

    def setUp(self):
        """Set up test environment."""
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.prom')
        self.metrics_file = self.temp_file.name
        self.temp_file.close()

    def tearDown(self):
        """Clean up test environment."""
        if os.path.exists(self.metrics_file):
            os.unlink(self.metrics_file)

    def test_usn_progression_tracking(self):
        """Test USN values are tracked in _set_lastUSN()."""
        from univention.s4connector.prometheus_metrics import S4MetricsCollector

        collector = S4MetricsCollector(self.metrics_file)

        usn_values = [1000, 1050, 1100, 1150, 1200]

        for usn in usn_values:
            collector.set_gauge('s4_connector_usn',
                                {'source': 's4'},
                                float(usn))
        metrics = collector._get_metrics_snapshot()
        gauge_key = (
            's4_connector_usn',
            frozenset([('source', 's4')]),
        )
        assert metrics['gauges'].get(gauge_key, 0) == 1200.0

    def test_usn_direction_separation(self):
        """Test separate USN tracking for S4→UCS and UCS→S4."""
        from univention.s4connector.prometheus_metrics import S4MetricsCollector

        collector = S4MetricsCollector(self.metrics_file)
        collector.set_gauge('s4_connector_usn',
                            {'source': 's4'},
                            5000.0)
        collector.set_gauge('s4_connector_usn',
                            {'source': 'ucs'},
                            3000.0)
        metrics = collector._get_metrics_snapshot()

        s4_key = (
            's4_connector_usn',
            frozenset([('source', 's4')]),
        )
        ucs_key = (
            's4_connector_usn',
            frozenset([('source', 'ucs')]),
        )

        assert metrics['gauges'].get(s4_key, 0) == 5000.0
        assert metrics['gauges'].get(ucs_key, 0) == 3000.0

    def test_usn_value_validation(self):
        """Test USN values are valid integers."""
        from univention.s4connector.prometheus_metrics import S4MetricsCollector

        collector = S4MetricsCollector(self.metrics_file)
        usn_string = "12345"
        collector.set_gauge('s4_connector_usn',
                            {'source': 's4'},
                            float(int(usn_string)))
        large_usn = 9999999999
        collector.set_gauge('s4_connector_usn',
                            {'source': 'ucs'},
                            float(large_usn))
        metrics = collector._get_metrics_snapshot()

        s4_key = (
            's4_connector_usn',
            frozenset([('source', 's4')]),
        )
        ucs_key = (
            's4_connector_usn',
            frozenset([('source', 'ucs')]),
        )

        assert metrics['gauges'].get(s4_key, 0) == 12345.0
        assert metrics['gauges'].get(ucs_key, 0) == float(large_usn)

    def test_usn_monotonic_increase(self):
        """Test that USN values increase monotonically."""
        from univention.s4connector.prometheus_metrics import S4MetricsCollector

        collector = S4MetricsCollector(self.metrics_file)
        usn_sequence = [100, 200, 300, 400, 500]

        for usn in usn_sequence:
            collector.set_gauge('s4_connector_usn',
                                {'source': 's4'},
                                float(usn))
            metrics = collector._get_metrics_snapshot()
            gauge_key = (
                's4_connector_usn',
                frozenset([('source', 's4')]),
            )
            assert metrics['gauges'].get(gauge_key, 0) == float(usn)


if __name__ == '__main__':
    unittest.main()

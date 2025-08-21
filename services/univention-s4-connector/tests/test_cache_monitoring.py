#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""
Test suite for cache size monitoring.
Part of Phase 4: Rejection and State Tracking.
"""

import os
import sys
import tempfile
import unittest


sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'modules'))


class TestCacheMonitoring(unittest.TestCase):
    """Test monitoring of cache sizes."""

    def setUp(self):
        """Set up test environment."""
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.prom')
        self.metrics_file = self.temp_file.name
        self.temp_file.close()

    def tearDown(self):
        """Clean up test environment."""
        if os.path.exists(self.metrics_file):
            os.unlink(self.metrics_file)

    def test_s4cache_size_tracking(self):
        """Test S4Cache size is monitored."""
        from univention.s4connector.prometheus_metrics import S4MetricsCollector

        collector = S4MetricsCollector(self.metrics_file)

        cache_sizes = [0, 10, 50, 100, 150, 200]

        for size in cache_sizes:
            collector.set_gauge('s4_connector_cache_entries',
                                {'cache_type': 's4cache'},
                                float(size))
        metrics = collector._get_metrics_snapshot()
        gauge_key = ('s4_connector_cache_entries',
                     frozenset([('cache_type', 's4cache')]))
        assert metrics['gauges'].get(gauge_key, 0) == 200.0

    def test_group_cache_size_tracking(self):
        """Test group cache size is monitored."""
        from univention.s4connector.prometheus_metrics import S4MetricsCollector

        collector = S4MetricsCollector(self.metrics_file)

        group_cache_sizes = [0, 5, 15, 25, 30]

        for size in group_cache_sizes:
            collector.set_gauge('s4_connector_cache_entries',
                                {'cache_type': 'group_cache'},
                                float(size))
        metrics = collector._get_metrics_snapshot()
        gauge_key = ('s4_connector_cache_entries',
                     frozenset([('cache_type', 'group_cache')]))
        assert metrics['gauges'].get(gauge_key, 0) == 30.0

    def test_cache_size_update_frequency(self):
        """Test cache sizes are updated regularly."""
        import time

        from univention.s4connector.prometheus_metrics import S4MetricsCollector

        collector = S4MetricsCollector(self.metrics_file)

        update_times = []

        def update_cache_metrics():
            cache_size = len(getattr(self, 's4cache', [])) if hasattr(self, 's4cache') else 100
            collector.set_gauge('s4_connector_cache_entries',
                                {'cache_type': 's4cache'},
                                float(cache_size))
            update_times.append(time.time())
        for _ in range(3):
            update_cache_metrics()
            time.sleep(0.1)

        assert len(update_times) == 3
        if len(update_times) > 1:
            intervals = [update_times[i] - update_times[i - 1]
                         for i in range(1, len(update_times))]
            for interval in intervals:
                assert interval > 0
                assert interval < 1.0

    def test_multiple_cache_types(self):
        """Test tracking multiple cache types simultaneously."""
        from univention.s4connector.prometheus_metrics import S4MetricsCollector

        collector = S4MetricsCollector(self.metrics_file)
        collector.set_gauge('s4_connector_cache_entries',
                            {'cache_type': 's4cache'},
                            500.0)
        collector.set_gauge('s4_connector_cache_entries',
                            {'cache_type': 'group_cache'},
                            50.0)
        collector.set_gauge('s4_connector_cache_entries',
                            {'cache_type': 'dns_cache'},
                            25.0)
        metrics = collector._get_metrics_snapshot()

        s4_key = ('s4_connector_cache_entries',
                  frozenset([('cache_type', 's4cache')]))
        group_key = ('s4_connector_cache_entries',
                     frozenset([('cache_type', 'group_cache')]))
        dns_key = ('s4_connector_cache_entries',
                   frozenset([('cache_type', 'dns_cache')]))

        assert metrics['gauges'].get(s4_key, 0) == 500.0
        assert metrics['gauges'].get(group_key, 0) == 50.0
        assert metrics['gauges'].get(dns_key, 0) == 25.0

    def test_cache_growth_and_shrink(self):
        """Test cache size changes (growth and shrinkage)."""
        from univention.s4connector.prometheus_metrics import S4MetricsCollector

        collector = S4MetricsCollector(self.metrics_file)
        collector.set_gauge('s4_connector_cache_entries',
                            {'cache_type': 's4cache'},
                            0.0)
        collector.set_gauge('s4_connector_cache_entries',
                            {'cache_type': 's4cache'},
                            100.0)
        collector.set_gauge('s4_connector_cache_entries',
                            {'cache_type': 's4cache'},
                            250.0)
        collector.set_gauge('s4_connector_cache_entries',
                            {'cache_type': 's4cache'},
                            150.0)
        metrics = collector._get_metrics_snapshot()
        gauge_key = ('s4_connector_cache_entries',
                     frozenset([('cache_type', 's4cache')]))
        assert metrics['gauges'].get(gauge_key, 0) == 150.0


if __name__ == '__main__':
    unittest.main()

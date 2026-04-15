# SPDX-License-Identifier: AGPL-3.0-only
# SPDX-FileCopyrightText: 2025 Univention GmbH

from typing import Any
from univention.testing.helm.base import Base
from pytest_helm.utils import load_yaml

class TestWaitForLdap(Base):
    template_name = 'templates/job-update-univention-object-identifier.yaml'
    init_container_name = 'wait-for-ldap'
    def test_extra_env_vars(self, helm, chart_default_path):
        values = load_yaml(
                """
                waitForDependency:
                  extraEnvVars:
                    - name: foo
                      value: bar
                """,
                  )

        wait_for_ldap = self.render_chart_and_find_container(helm, chart_default_path, values)

        env_vars = wait_for_ldap['env']
        test_env_var = next((env_var for env_var in env_vars if env_var['name'] == 'foo'))
        assert test_env_var, f'env var with value \'foo\' not found in env vars {env_vars}'
        assert test_env_var['value'] == 'bar'

    def test_extra_volume_mounts(self, helm, chart_default_path):
        values = load_yaml(
            """
            waitForDependency:
                extraVolumeMounts:
                    - name: foo
                      mountPath: /bar
                      subPath: baz
            """,
        )

        wait_for_ldap = self.render_chart_and_find_container(helm, chart_default_path, values)

        volume_mounts = wait_for_ldap['volumeMounts']
        test_volume_mount = next((volume_mount for volume_mount in volume_mounts if volume_mount['name'] == 'foo'))

        assert test_volume_mount, f"volume mount with name 'foo' not found in volume mounts {volume_mounts}"
        assert test_volume_mount['mountPath'] == '/bar'
        assert test_volume_mount['subPath'] == 'baz'

    def test_extra_volumes(self, helm, chart_default_path):
        values = load_yaml(
            """
            waitForDependency:
                extraVolumes:
                    - name: "foo"
                      emptyDir:
            """,
        )

        chart = self.render_job(helm, chart_default_path, values)
        volumes = chart['spec']['template']['spec']['volumes']

        test_volume = next((volume for volume in volumes if volume['name'] == 'foo'))

        assert test_volume
        assert test_volume['emptyDir'] is None

    def render_chart_and_find_container(self, helm, chart_default_path, values):
        chart = self.render_job(helm, chart_default_path, values)
        wait_for_ldap = self.find_wait_for_ldap_container(chart)
        assert wait_for_ldap, f'wait-for-ldap init container not found in chart {chart}'

        return wait_for_ldap

    def find_wait_for_ldap_container(self, chart: dict[str, Any]) -> dict[str, Any] | None:
        init_containers = chart['spec']['template']['spec']['initContainers']
        return next((init_container for init_container in init_containers if init_container['name'] == self.init_container_name), None)

    def render_job(self, helm, chart_default_path, values):
        return self.helm_template_file(helm, chart_default_path, values, self.template_name)

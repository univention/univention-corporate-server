# SPDX-FileCopyrightText: 2018-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""Module and object specific for "container/cn" UDM module."""


from ..encoders import StringIntBooleanPropertyEncoder
from .generic import GenericModule, GenericObject, GenericObjectProperties


class ContainerCnObjectProperties(GenericObjectProperties):
    """container/cn UDM properties."""

    _encoders = {
        'computerPath': StringIntBooleanPropertyEncoder,
        'dhcpPath': StringIntBooleanPropertyEncoder,
        'dnsPath': StringIntBooleanPropertyEncoder,
        'groupPath': StringIntBooleanPropertyEncoder,
        'licensePath': StringIntBooleanPropertyEncoder,
        'mailPath': StringIntBooleanPropertyEncoder,
        'networkPath': StringIntBooleanPropertyEncoder,
        'policyPath': StringIntBooleanPropertyEncoder,
        'printerPath': StringIntBooleanPropertyEncoder,
        'sharePath': StringIntBooleanPropertyEncoder,
        'userPath': StringIntBooleanPropertyEncoder,
    }


class ContainerCnObject(GenericObject):
    """Better representation of container/cn properties."""

    udm_prop_class = ContainerCnObjectProperties


class ContainerCnModule(GenericModule):
    """ContainerCnObject factory"""

    _udm_object_class = ContainerCnObject

    class Meta:
        supported_api_versions = [1, 2, 3]
        suitable_for = ['containers/cn']

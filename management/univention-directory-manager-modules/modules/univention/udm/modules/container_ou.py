# SPDX-FileCopyrightText: 2018-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""Module and object specific for "container/ou" UDM module."""


from ..encoders import dn_property_encoder_for
from .container_cn import ContainerCnModule, ContainerCnObject, ContainerCnObjectProperties


class ContainerOuObjectProperties(ContainerCnObjectProperties):
    """container/ou UDM properties."""

    _encoders = dict(
        ContainerCnObjectProperties._encoders,
        ucsschoolClassShareFileServer=dn_property_encoder_for('auto'),
        ucsschoolHomeShareFileServer=dn_property_encoder_for('auto'),
    )


class ContainerOuObject(ContainerCnObject):
    """Better representation of container/ou properties."""

    udm_prop_class = ContainerOuObjectProperties


class ContainerOuModule(ContainerCnModule):
    """ContainerOuObject factory"""

    _udm_object_class = ContainerOuObject

    class Meta:
        supported_api_versions = [1, 2, 3]
        suitable_for = ['containers/ou']

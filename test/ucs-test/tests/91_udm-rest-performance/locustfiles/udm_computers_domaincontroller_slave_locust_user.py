from generic_user import GenericUser
from tasks.computers_domaincontroller_slave.computers_domaincontroller_slave_add_get import (
    computers_domaincontroller_slave_add_get,
)
from tasks.computers_domaincontroller_slave.computers_domaincontroller_slave_dn_delete import (
    computers_domaincontroller_slave_dn_delete,
)
from tasks.computers_domaincontroller_slave.computers_domaincontroller_slave_dn_get import (
    computers_domaincontroller_slave_dn_get,
)
from tasks.computers_domaincontroller_slave.computers_domaincontroller_slave_dn_patch import (
    computers_domaincontroller_slave_dn_patch,
)
from tasks.computers_domaincontroller_slave.computers_domaincontroller_slave_dn_put import (
    computers_domaincontroller_slave_dn_put,
)
from tasks.computers_domaincontroller_slave.computers_domaincontroller_slave_get import (
    computers_domaincontroller_slave_get,
)
from tasks.computers_domaincontroller_slave.computers_domaincontroller_slave_post import (
    computers_domaincontroller_slave_post,
)


tag = 'computers/domaincontroller_slave'


class ComputersDomaincontrollerSlaveGet(GenericUser):
    tasks = [computers_domaincontroller_slave_get]
    tag = tag


class ComputersDomaincontrollerSlavePost(GenericUser):
    tasks = [computers_domaincontroller_slave_post]
    tag = tag


class ComputersDomaincontrollerSlaveAddGet(GenericUser):
    tasks = [computers_domaincontroller_slave_add_get]
    tag = tag


class ComputersDomaincontrollerSlaveDnGet(GenericUser):
    tasks = [computers_domaincontroller_slave_dn_get]
    tag = tag


class ComputersDomaincontrollerSlaveDnDelete(GenericUser):
    tasks = [computers_domaincontroller_slave_dn_delete]
    tag = tag


class ComputersDomaincontrollerSlaveDnPut(GenericUser):
    tasks = [computers_domaincontroller_slave_dn_put]
    tag = tag


class ComputersDomaincontrollerSlaveDnPatch(GenericUser):
    tasks = [computers_domaincontroller_slave_dn_patch]
    tag = tag

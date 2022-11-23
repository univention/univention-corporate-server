from generic_user import GenericUser
from tasks.container_ou.container_ou_add_get import container_ou_add_get
from tasks.container_ou.container_ou_dn_delete import container_ou_dn_delete
from tasks.container_ou.container_ou_dn_get import container_ou_dn_get
from tasks.container_ou.container_ou_dn_patch import container_ou_dn_patch
from tasks.container_ou.container_ou_dn_put import container_ou_dn_put
from tasks.container_ou.container_ou_get import container_ou_get
from tasks.container_ou.container_ou_post import container_ou_post


tag = 'container/ou'


class ContainerOuGet(GenericUser):
    tasks = [container_ou_get]
    tag = tag


class ContainerOuPost(GenericUser):
    tasks = [container_ou_post]
    tag = tag


class ContainerOuAddGet(GenericUser):
    tasks = [container_ou_add_get]
    tag = tag


class ContainerOuDnGet(GenericUser):
    tasks = [container_ou_dn_get]
    tag = tag


class ContainerOuDnDelete(GenericUser):
    tasks = [container_ou_dn_delete]
    tag = tag


class ContainerOuDnPut(GenericUser):
    tasks = [container_ou_dn_put]
    tag = tag


class ContainerOuDnPatch(GenericUser):
    tasks = [container_ou_dn_patch]
    tag = tag

from generic_user import GenericUser
from tasks.groups_group.groups_group_add_get import groups_group_add_get
from tasks.groups_group.groups_group_dn_delete import groups_group_dn_delete
from tasks.groups_group.groups_group_dn_get import groups_group_dn_get
from tasks.groups_group.groups_group_dn_patch import groups_group_dn_patch
from tasks.groups_group.groups_group_dn_put import groups_group_dn_put
from tasks.groups_group.groups_group_get import groups_group_get
from tasks.groups_group.groups_group_post import groups_group_post


tag = 'groups/group'


class GroupsGroupGet(GenericUser):
    tasks = [groups_group_get]
    tag = tag


class GroupsGroupPost(GenericUser):
    tasks = [groups_group_post]
    tag = tag


class GroupsGroupAddGet(GenericUser):
    tasks = [groups_group_add_get]
    tag = tag


class GroupsGroupDnGet(GenericUser):
    tasks = [groups_group_dn_get]
    tag = tag


class GroupsGroupDnDelete(GenericUser):
    tasks = [groups_group_dn_delete]
    tag = tag


class GroupsGroupDnPut(GenericUser):
    tasks = [groups_group_dn_put]
    tag = tag


class GroupsGroupDnPatch(GenericUser):
    tasks = [groups_group_dn_patch]
    tag = tag

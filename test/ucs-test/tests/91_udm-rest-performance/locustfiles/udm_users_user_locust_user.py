from generic_user import GenericUser
from tasks.users_user.users_user_add_get import users_user_add_get
from tasks.users_user.users_user_dn_delete import users_user_dn_delete
from tasks.users_user.users_user_dn_get import users_user_dn_get
from tasks.users_user.users_user_dn_patch import users_user_dn_patch
from tasks.users_user.users_user_dn_put import users_user_dn_put
from tasks.users_user.users_user_get import users_user_get
from tasks.users_user.users_user_post import users_user_post


tag = 'users/user'


class UsersUserGet(GenericUser):
    tasks = [users_user_get]
    tag = tag


class UsersUserPost(GenericUser):
    tasks = [users_user_post]
    tag = tag


class UsersUserAddGet(GenericUser):
    tasks = [users_user_add_get]
    tag = tag


class UsersUserDnGet(GenericUser):
    tasks = [users_user_dn_get]
    tag = tag


class UsersUserDnDeleteStudent(GenericUser):
    tasks = [users_user_dn_delete]
    tag = tag
    role = 'student'


class UsersUserDnDeleteTeacher(GenericUser):
    tasks = [users_user_dn_delete]
    tag = tag
    role = 'teacher'


class UsersUserDnDeleteStaff(GenericUser):
    tasks = [users_user_dn_delete]
    tag = tag
    role = 'staff'


class UsersUserDnPut(GenericUser):
    tasks = [users_user_dn_put]
    tag = tag


class UsersUserDnPatch(GenericUser):
    tasks = [users_user_dn_patch]
    tag = tag

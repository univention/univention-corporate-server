from typing import NamedTuple

from univention.admin.rest.client import BadRequest, UnprocessableEntity
# from univention.admin.rest.client import UDM, Module, Object, UnprocessableEntity
from univention.admin.rest.client.test_client import TestUDM as UDM


uri = 'http://localhost:9979/udm/'
udm = UDM.http(uri, 'cn=admin', 'univention')
module = udm.get('users/user')


class Container(NamedTuple):
    position: str
    name: str


def test_user_search():
    print('Found {}'.format(module))
    # obj = next(module.search())
    # if obj:
    # obj = obj.open()
    # print('Object {}'.format(obj))


def create_announcement():
    print('get announcements')
    announcements = udm.get('portals/announcement')
    ann = announcements.new()
    ann.properties['title'] = {'de_DE': 'düdeldü'}
    try:
        ann.save()
    except Exception:
        pass
    ann.properties['name'] = 'testing123'
    ann.properties
    ann.save()


def bootstrap_portal():
    ldap_base = udm.get_ldap_base()
    container = udm.get('container/cn')

    udm_containers = [
        Container(f"cn=univention,{ldap_base}", "portals"),
        Container(f"cn=portals,cn=univention,{ldap_base}", "portal"),
        Container(f"cn=portals,cn=univention,{ldap_base}", "category"),
        Container(f"cn=portals,cn=univention,{ldap_base}", "entry"),
        Container(f"cn=portals,cn=univention,{ldap_base}", "folder"),
        Container(f"cn=portals,cn=univention,{ldap_base}", "config"),
        Container(f"cn=portals,cn=univention,{ldap_base}", "announcement"),
    ]

    for con in udm_containers:
        print(con.name)
        try:
            obj = container.get(f"cn={con.name},{con.position}")
            print()
            # raise UnprocessableEntity("l", "l", "l")
        except UnprocessableEntity:
            obj = container.new(position=con.position)
        obj.properties["name"] = f"{con.name}bla"
        try:
            obj.save()
            print(f"{con.name}")
        except (BadRequest, UnprocessableEntity) as err:
            print(err)
    breakpoint()


if __name__ == '__main__':
    test_user_search()
    bootstrap_portal()

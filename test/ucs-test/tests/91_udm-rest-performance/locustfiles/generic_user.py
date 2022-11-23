from faker import Faker
from locust import constant_pacing
from locustclasses import UiUserClient
from utils import TestData

from univention.testing import utils


class GenericUser(UiUserClient):
    abstract = True
    wait_time = constant_pacing(1)

    def __init__(self, *args, **kwargs):
        self.fake = Faker()
        self.test_data = TestData()
        super(GenericUser, self).__init__(*args, **kwargs)
        account = utils.UCSTestDomainAdminCredentials()
        self.username = account.username
        self.password = account.bindpw

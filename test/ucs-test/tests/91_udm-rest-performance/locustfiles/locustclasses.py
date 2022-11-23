import logging
from typing import Optional

import requests
from locust import HttpUser
from utils import get_token


logger = logging.getLogger(__name__)


class UiUserClient(HttpUser):
    abstract = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.username: Optional[str] = None
        self.password: Optional[str] = None
        self._auth_token: Optional[str] = None
        self.data: Optional[dict] = None

    def on_start(self):
        print(f"{self.username}, {id(self)}")
        self._auth_token = get_token(username=self.username, password=self.password)
        try:
            r = requests.get(
                f"{self.environment.host}/univention/udm/{self.tag}/add",
                headers={
                    "Authorization": f"Basic {self._auth_token}",
                    "Accept-Language": "en-US",
                    "accept": "application/json"
                },
            )
            if r.status_code != 200:
                raise Exception(f"{self.tag}_post: failed to get {self.tag}/add")
            self.data = r.json()
            self.data.pop("_links")
            self.data.pop("_embedded")
            self.data.pop("objectType")
        except Exception as e:
            print(f"{self.tag}_post: failed to get {self.tag}/add: {e}")
            raise e

    def request(
        self, operation: str, *args, add_auth_token: bool = True, headers: Optional[dict] = None, response_codes: Optional[set] = None, **kwargs
    ) -> requests.Response:
        """Wrapper method for HttpUser.client.post, adds auth token automatically"""
        # if not headers:
        #     headers = {"accept": "application/json", "Accept-Language": "en-US"}
        #
        # if "accept" not in headers:
        #     headers.update({"accept": "application/json"})
        #
        # if "Accept-Language" not in headers:
        #     headers.update({"Accept-Language": "en-US"})
        headers = headers or {"accept": "application/json", "Accept-Language": "en-US"}
        headers.setdefault("accept", "application/json")
        headers.setdefault("Accept-Language", "en-US")

        if add_auth_token:
            headers["Authorization"] = f"Basic {self._auth_token}"
        assert operation in ["get", "post", "put", "delete", "patch"]
        r = getattr(self.client, operation)(*args, headers=headers, **kwargs)
        if response_codes and r.status_code not in response_codes:
            logging.error(f"Request failed for url {r.url} with status code {r.status_code}")
            logging.error(f"Response content: {r.content}")
        return r

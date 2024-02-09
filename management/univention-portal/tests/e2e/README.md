# End-to-end tests for the Univention Portal

## Installation

```
pip install -r requirements.txt
playwright install  # installs required browsers
```

## How to run tests

Please make sure you have the portal and notifications API running at some
endpoint.

Then just run the following command.

```
pytest
```

We support the following custom command line options defined in `tests/conftest.py`

1. `username`: Username to use when logging into the portal. Defaults to `"Administator"`
2. `password` Password to use when logging into the portal. Defaults to `"univention"`
3. `notifications-api-base-url`: Defaults to `"http://localhost:8000/univention/portal/notifications-api/"`
4. `portal-base-url`: Defaults to `"https://localhost:8000"`

So you can do the following, for example:

```
pytest --username <my_user> --password <my_password> \
       --notifications-api-base-url <custom_notifications_api_base_url> \
       --portal-base-url <custom_portal_base_url>
```

We use the `pytest-playwright` plugin, and it exposes many useful command
line options for running end-to-end tests. See the
[all available options](https://playwright.dev/python/docs/test-runners).

Here are some useful ones:

1. `--headed`: Run tests in headed mode.
2. `--slowmo`: Run tests in slow motion e.g. `--slowmo 500`
3. `--video`: Capture video e.g. `--video on`
4. `--browser`: Use a specific browser `--browser firefox`

## Available tests

| Group         | Test                                                            | Location                                   |
|---------------|-----------------------------------------------------------------|--------------------------------------------|
| General       | User can login to portal                                        | `tests/test_login.py`                      |
|               | User can logout                                                 | `tests/test_logout.py`                     |
|               | User can login to portal using SAML                             | `tests/test_saml_login.py`                 |
|               | User can logout when SAML login was used                        | `tests/test_saml_logout.py`                |
| Notifications | Notification pops up when triggered using the notifications API | `tests/test_two_notification.py`           |
|               | Notification has correct title, detail and link attributes      | `tests/test_two_notifications.py`          |
|               | Two notifications are displayed in the correct order            | `tests/test_two_notifications.py`          |
|               | Notification expiry time is respected                           | `tests/test_notification_expiry_time.py`   |
| Translation   | Logged out user is able to change language                      | `tests/test_i18n.py`                       |
| UMC Tile      | Admin user is able to use the Users tile                        | `tests/test_users_page.py`                 |
| Self-service  | Non-admin user can change password                              | `tests/test_non_admin_can_change_password` |

## For test engineers

We use the Page Object model in our tests. The page objects are in
[playwright-pages-ucs-portal](https://gitlab.souvap-univention.de/souvap/tests/playwright-pages-ucs-portal/).

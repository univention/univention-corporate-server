# SPDX-License-Identifier: AGPL-3.0-only
# SPDX-FileCopyrightText: 2023-2024 Univention GmbH

import copy
import time
import uuid
from datetime import datetime, timedelta, timezone
from urllib.parse import urljoin

import pytest
import requests
from playwright_pages_base import expect
from playwright_pages_ucs_portal.home_page.logged_in import HomePageLoggedIn
from playwright_pages_ucs_portal.home_page.logged_out import HomePageLoggedOut
from url_normalize import url_normalize


@pytest.fixture()
def login_and_clear_old_notifications(navigate_to_home_page_logged_in, username, password):
    page = navigate_to_home_page_logged_in
    home_page_logged_in = HomePageLoggedIn(page)
    home_page_logged_in.navigate(username, password)
    home_page_logged_in.is_displayed()
    home_page_logged_in.remove_all_notifications()
    yield page
    home_page_logged_in = HomePageLoggedIn(page)
    home_page_logged_in.navigate(username, password)
    home_page_logged_in.remove_all_notifications()


@pytest.fixture()
def notification_json_data():
    unique_id = str(uuid.uuid4())
    json_data = {
        "sourceUid": unique_id,
        "targetUid": unique_id,
        "title": "Test title",
        "details": "Test details",
        "severity": "info",
        "sticky": True,
        "needsConfirmation": True,
        "notificationType": "event",
        "link": {
            "url": "https://test.org",
            "text": "Test link text",
            "target": "test target",
        },
        "data": {},
    }
    return json_data


@pytest.fixture()
def notification_json_data_different_details(notification_json_data):
    json_data = copy.deepcopy(notification_json_data)
    json_data["details"] = "Different details"
    return json_data


@pytest.fixture()
def send_notification_endpoint(notifications_api_base_url):
    return urljoin(notifications_api_base_url, "./v1/notifications/")


# https://git.knut.univention.de/univention/components/univention-portal/-/issues/712
@pytest.mark.xfail()
def test_two_notifications(login_and_clear_old_notifications,
                           send_notification_endpoint,
                           notification_json_data,
                           notification_json_data_different_details,
                           ):
    page = login_and_clear_old_notifications
    home_page_logged_in = HomePageLoggedIn(page)
    expect(home_page_logged_in.popup_notification_container).to_be_hidden()
    response = requests.post(send_notification_endpoint, json=notification_json_data)
    assert response.ok, \
        f"Got status {response.status_code} while sending notification"
    expect(home_page_logged_in.popup_notification_container).to_be_visible()
    expect(home_page_logged_in.popup_notification_container.notifications).to_have_count(1)
    notification = home_page_logged_in.popup_notification_container.notification(0)
    expect(notification).to_be_visible()

    link = notification.link
    expect(link).to_have_count(1)
    expected_url = notification_json_data["link"]["url"]
    actual_url = link.get_attribute("href")
    assert url_normalize(expected_url) == url_normalize(actual_url), \
        f"Wrong link in notification pop up. Expected: {expected_url}, actual: {actual_url}"

    expected_target = notification_json_data["link"]["target"]
    actual_target = link.get_attribute("target")
    assert expected_target == actual_target, \
        f"Wrong link target in notification pop up. Expected: {expected_target}, actual: {actual_target}"
    expected_link_text = notification_json_data["link"]["text"]
    actual_link_text = link.inner_text()
    assert expected_link_text == actual_link_text, \
        f"Wrong link text in notification pop up. Expected: {expected_link_text}, actual: {actual_link_text}"

    expect(notification.title).to_have_text(
        f"{notification_json_data['severity'].capitalize()}: {notification_json_data['title']}",
    )
    expect(notification.details).to_have_text(notification_json_data["details"])

    response = requests.post(send_notification_endpoint, json=notification_json_data_different_details)
    assert response.ok, \
        f"Got status {response.status_code} while sending notification"
    home_page_logged_in.reveal_area(home_page_logged_in.notification_drawer, home_page_logged_in.header.bell_icon)
    expect(home_page_logged_in.notification_drawer.notifications).to_have_count(2)
    first_notification = home_page_logged_in.notification_drawer.notification(0)
    expect(first_notification).to_be_visible()
    expect(first_notification.details).to_have_text(notification_json_data_different_details["details"])
    second_notification = home_page_logged_in.notification_drawer.notification(1)
    expect(second_notification).to_be_visible()
    expect(second_notification.details).to_have_text(notification_json_data["details"])


@pytest.fixture()
def logout_after_clearing_old_notifications(login_and_clear_old_notifications):
    page = login_and_clear_old_notifications
    home_page_logged_out = HomePageLoggedOut(page)
    home_page_logged_out.navigate()
    home_page_logged_out.is_displayed()
    return page


def test_notification_expiry_time(logout_after_clearing_old_notifications,
                                  send_notification_endpoint,
                                  notification_json_data,
                                  username,
                                  password,
                                  ):
    page = logout_after_clearing_old_notifications

    dt_now = datetime.now(timezone.utc)
    expiry_dt = dt_now + timedelta(seconds=5)
    notification_json_data["expireTime"] = expiry_dt.isoformat()

    response = requests.post(send_notification_endpoint, json=notification_json_data)
    assert response.ok, \
        f"Got status {response.status_code} while sending notification"
    wait = (expiry_dt - dt_now).total_seconds()
    time.sleep(wait + 1)  # +1 for safety
    home_page_logged_in = HomePageLoggedIn(page)
    home_page_logged_in.navigate(username, password)
    home_page_logged_in.is_displayed()
    expect(home_page_logged_in.popup_notification_container).to_be_hidden()
    home_page_logged_in.reveal_area(home_page_logged_in.notification_drawer, home_page_logged_in.header.bell_icon)
    expect(home_page_logged_in.notification_drawer.no_notifications_heading).to_be_visible()
    expect(home_page_logged_in.notification_drawer.notifications).to_have_count(0)

    notification_json_data["expireTime"] = (datetime.now(timezone.utc) + timedelta(seconds=5)).isoformat()
    response = requests.post(send_notification_endpoint, json=notification_json_data)
    assert response.ok, \
        f"Got status {response.status_code} while sending notification"
    expect(home_page_logged_in.notification_drawer.no_notifications_heading).to_be_hidden()
    expect(home_page_logged_in.notification_drawer.notifications).to_have_count(1)
    expect(home_page_logged_in.notification_drawer.notification(0)).to_be_visible()

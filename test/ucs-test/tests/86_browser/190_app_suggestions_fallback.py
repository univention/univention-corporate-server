#!/usr/share/ucs-test/runner /usr/share/ucs-test/playwright
# -*- coding: utf-8 -*-
## desc: |
##  Test fallback for invalid suggestions
## roles-not:
##  - basesystem
## tags:
##  - skip_admember
## join: true
## exposure: dangerous


from univention.testing.browser import logger
from univention.testing.browser.appcenter import AppCenter
from univention.testing.browser.lib import MIN, UMCBrowserTest
from univention.testing.browser.suggestion import AppCenterCacheTest


expected_message = "Could not load appcenter/suggestions"


def test_app_suggestions_invalid_json(umc_browser_test: UMCBrowserTest, app_center_cache: AppCenterCacheTest):
    app_center = AppCenter(umc_browser_test)
    write_invalid_json(app_center_cache)
    check(app_center, expected_message)


def test_app_suggestions_missing_key(umc_browser_test: UMCBrowserTest, app_center_cache: AppCenterCacheTest):
    app_center = AppCenter(umc_browser_test)
    write_missing_key(app_center_cache)
    check(app_center, expected_message)


def check(app_center: AppCenter, expected_message: str):
    logger.info("checking for message")
    with app_center.page.expect_console_message(predicate=lambda msg: expected_message in msg.text, timeout=2 * MIN):
        app_center.navigate()


def write_missing_key(file: AppCenterCacheTest):
    file.write(
        """
{
    "xxx": {}
}
""",
        truncate=True,
    )


def write_invalid_json(file: AppCenterCacheTest):
    file.write("asd", truncate=True)

#!/usr/share/ucs-test/runner /usr/share/ucs-test/playwright
# -*- coding: utf-8 -*-
## desc: |
##  Test suggestion algorithm
## roles-not:
##  - basesystem
## tags:
##  - skip_admember
## join: true
## exposure: dangerous

from playwright.sync_api import expect

from univention.appcenter.app_cache import AppCache
from univention.testing.browser.appcenter import AppCenter
from univention.testing.browser.lib import UMCBrowserTest


def test_app_suggestons_algorithm(umc_browser_test: UMCBrowserTest):
    app_center = AppCenter(umc_browser_test)
    app_center.navigate()
    expect(umc_browser_test.page.get_by_role("heading", name="Available")).to_be_visible(timeout=60 * 1000)

    app_cache = AppCache.build()
    apps = app_cache.get_all_apps()
    installed_apps = [
        {"id": apps[0].id},
        {"id": apps[1].id},
    ]
    suggestions = [
        {
            "condition": [installed_apps[0]["id"], "xxx"],
            "candidates": [
                {
                    "id": apps[2].id,
                    "mayNotBeInstalled": [],
                },
            ],
        },
        {
            "condition": [installed_apps[0]["id"]],
            "candidates": [
                {
                    "id": apps[3].id,
                    "mayNotBeInstalled": [installed_apps[1]["id"]],
                },
            ],
        },
        {
            "condition": [installed_apps[0]["id"], installed_apps[1]["id"]],
            "candidates": [
                {
                    "id": apps[4].id,
                    "mayNotBeInstalled": ["xxx"],
                },
                {
                    "id": apps[5].id,
                    "mayNotBeInstalled": ["xxx"],
                },
                {
                    "id": apps[6].id,
                    "mayNotBeInstalled": [installed_apps[0]["id"]],
                },
            ],
        },
    ]

    eval_result = umc_browser_test.page.evaluate(
        """([suggestions, installed_apps]) => {
            //console.log(suggestions.length)
            //console.log(installed_apps.length)
            var w = dijit.byId('umc_modules_appcenter_AppCenterPage_0');
            return w._getSuggestedAppIds(suggestions, installed_apps);
        }""",
        [suggestions, installed_apps],
    )

    assert apps[4].id in eval_result, f"Expected {apps[4]} to be in suggested ids {eval_result}"
    assert apps[5].id in eval_result, f"Expected {apps[5]} to be in suggested ids {eval_result}"

#!/usr/share/ucs-test/runner /usr/share/ucs-test/playwright
# -*- coding: utf-8 -*-
## desc: Test memory leaks in UMC javascript frontend
## roles-not:
##  - basesystem
## tags:
##  - skip_admember
##  - umc-producttest
##  - producttest
## join: true
## exposure: dangerous

import json
import pprint

from playwright.sync_api import Page

from univention.lib.i18n import Translation
from univention.testing.browser import logger
from univention.testing.browser.lib import UMCBrowserTest


_ = Translation("ucs-test-browser").translate


def test_umc_memory_leaks(umc_browser_test: UMCBrowserTest):
    page = umc_browser_test.page
    pp = pprint.PrettyPrinter(indent=4)

    umc_browser_test.login()

    dijit_map = gather_dijit_registry_map(page)
    dijit_map_json = json.loads(dijit_map)
    assert len(dijit_map_json) > 0

    logger.info("Inital dijit registry map: %s" % pp.pprint(dijit_map_json))

    umc_browser_test.open_all_modules(4)

    dijit_map_after = gather_dijit_registry_map(page)
    logger.info("Dijit registry map after opening and closing all modules: %s" % pp.pprint(json.loads(dijit_map_after)))

    dijit_map_diff = diff_dijit_registry_map(page, dijit_map, dijit_map_after)

    for v in json.loads(dijit_map_diff).values():
        assert v != 0, "There were extra widgets in the registry"


def gather_dijit_registry_map(page: Page) -> str:
    return page.evaluate(
        """
    () => {
        var m = umc.tools.dijitRegistryToMap();
        return JSON.stringify(m);
    }
    """,
    )


def diff_dijit_registry_map(page: Page, a: str, b: str) -> str:
    return page.evaluate(
        """([a, b]) => {
        var a = JSON.parse(a);
        var b = JSON.parse(b);

        var ret = umc.tools.dijitRegistryMapDifference(a,b);
        return JSON.stringify(ret)
    }
    """,
        [a, b],
    )

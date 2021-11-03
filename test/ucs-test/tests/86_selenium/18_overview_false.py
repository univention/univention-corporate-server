#!/usr/share/ucs-test/runner /usr/share/ucs-test/selenium-pytest -s -l -v --tb=native
## desc: check behaviour of ?overview=false query parameter
## tags: [umc]
## roles: [domaincontroller_master]
## bugs: [53906]
## exposure: dangerous
## packages:
## - univention-management-console-module-udm


def test_overview_false(selenium):
	selenium.driver.get(selenium.base_url + 'univention/management/?overview=false#module=udm:users/user')
	selenium.do_login(without_navigation=True)
	selenium.wait_for_text('Administrator')

	# The tabs should not be visible as long as only one tab is open
	users_tab = selenium.driver.find_element_by_xpath('//*[@widgetid="umc_widgets_TabController_0_umc_modules_udm_0"]//span[text() = "Users"]')
	assert not users_tab.is_displayed()

	selenium.click_grid_entry('Administrator')
	selenium.wait_until_standby_animation_appears_and_disappears()
	selenium.click_text('Policies')  # Policies tab
	selenium.wait_until_standby_animation_appears_and_disappears()
	selenium.click_text('Policy: Desktop')  # TitlePane
	selenium.click_button('Create new policy')
	selenium.wait_for_text('Desktop settings')  # content in the Policies module

	# When a second tab is opened the tabs should become visible...
	users_tab = selenium.driver.find_element_by_xpath('//*[@widgetid="umc_widgets_TabController_0_umc_modules_udm_0"]//span[text() = "Users"]')
	assert users_tab.is_displayed()
	# ...but the close button for the first tab should be hidden (the module is not closable)
	close_button = selenium.driver.find_element_by_xpath('//*[@widgetid="umc_widgets_TabController_0_umc_modules_udm_0"]//span[@title="Close"]')
	assert not close_button.is_displayed()

	policies_tab = selenium.driver.find_element_by_xpath('//*[@widgetid="umc_widgets_TabController_0_umc_modules_udm_1"]//span[text() = "Policies"]')
	assert policies_tab.is_displayed()
	# Further opened tabs should be closable
	close_button = selenium.driver.find_element_by_xpath('//*[@widgetid="umc_widgets_TabController_0_umc_modules_udm_1"]//span[@title="Close"]')
	assert close_button.is_displayed()

	selenium.click_button('Cancel')

	# Tabs should be hidden again when only one tab remains
	users_tab = selenium.driver.find_element_by_xpath('//*[@widgetid="umc_widgets_TabController_0_umc_modules_udm_0"]//span[text() = "Users"]')
	assert not users_tab.is_displayed()

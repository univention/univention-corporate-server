from playwright.sync_api import Page, expect


def login(page: Page):
    page.goto("http://10.200.103.10/univention/login")
    page.get_by_label("Username", exact=True).fill("Administrator")
    page.get_by_label("Password", exact=True).fill("univention")
    page.get_by_role("button", name="Login").click()
    print("here1")


def open_module(page: Page, module_name: str):
    #page.goto("http://10.200.103.10/univention/management")
    print("clicked search button")
    page.locator(".umcModuleSearchToggleButton").click()
    page.locator(".umcModuleSearch input.dijitInputInner").type(module_name)
    #page.locator(".umcModuleSearch input.dijitInputInner").press("ArrowRight")
    page.locator(".umcGalleryName", has_text=module_name).click()


def wait_for_all_loading_circles_to_disappear(page: Page):
    standy_wrappers = page.locator(".umcStandbySvgWrapper").all()
    # expect(standy_wrappers).to_be_hidden(timeout=60 * 1000)

    for standy_wrapper in standy_wrappers:
        expect(standy_wrapper).to_be_hidden(timeout=60 * 1000)


def test_example(page: Page) -> None:
    login(page)
    print("here")
    open_module(page, "Package Management")

    wait_for_all_loading_circles_to_disappear(page)

    # TODO: create a function that finds a small Package, or use already exisiting function
    small_package = "abigail-doc"
    search_bar = page.locator("[name=pattern]")
    search_bar.fill("")
    search_bar.type(small_package)
    search_bar.press("Enter")
    for action_name in ["Install", "Uninstall"]:
        #page.locator("#umc_widgets_CheckBox_3").check()
        checkbox = page.get_by_role("checkbox")
        while checkbox.count() != 2:
            checkbox = page.get_by_role("checkbox")
        print(checkbox.count())
        checkbox.last.check()

        action = page.get_by_role("button", name=action_name, exact=True)
        action.click()

        dialog = page.get_by_role("dialog", name="Confirmation")
        dialog.get_by_role("button", name=action_name).click()
        expect(dialog).to_have_count(0)

        install_dialog = page.get_by_role("dialog")
        expect(install_dialog).to_have_count(0, timeout=60 * 1000)
        pbar = page.get_by_role("progressbar")
        expect(pbar).to_have_count(0, timeout=60 * 1000)
        wait_for_all_loading_circles_to_disappear(page)
        print("finished action")

import pytest
import pyppeteer
import asyncio
from login.config import *
from common_config import *


class SafeClick():
    def __init__(self, page):
        self.page = page

    async def click(self, element):
        await asyncio.gather(self.page.click(element), self.page.waitForNavigation())

    async def wait(self, element):
        return await self.page.waitForSelector(element, {'timeout': SELECT_TIMEOUT})


@pytest.mark.asyncio
async def test_title():
    # Setup browser
    browser = await pyppeteer.launch(PYPPETEER_OPTIONS)
    page = await browser.newPage()

    # Go to landing portal
    await page.goto(LANDING_PORTAL_URL)

    # Pull out title property
    title = await page.title()
    assert title == 'RRAP M&DS Information System'
    await browser.close()


@pytest.mark.asyncio
async def test_login_landing_portal():
    # Setup browser
    browser = await pyppeteer.launch(PYPPETEER_OPTIONS)
    page = await browser.newPage()

    safeClick = SafeClick(page=page)
    navClick = safeClick.click
    click = page.click
    wait = safeClick.wait

    # Go to landing portal
    await page.goto(LANDING_PORTAL_URL)

    # Set the viewport
    await page.setViewport({'width': 1600, 'height': 900})

    # Press log in tab button
    # directs straight to kc
    login_tab_selector = "#login-tab-button"
    element = await wait(login_tab_selector)
    await navClick(login_tab_selector)

    # Type username and password
    await wait('#username')
    await click('#username')
    await page.type('#username', USERNAME)

    await wait('#password')
    await click('#password')
    await page.type('#password', PASSWORD)

    # Submit
    await wait('#kc-login')
    await navClick('#kc-login')

    # Press profile button
    profile_button_selector = "#profile-button"
    await wait(profile_button_selector)
    await navClick(profile_button_selector)

    # Wait for profile
    profile_title_selector = "#profile-title"
    element = await wait(profile_title_selector)

    # Get the text from the profile tag and check it says Profile
    value = await (await element.getProperty('innerText')).jsonValue()
    assert value == "Profile"

    await browser.close()


@pytest.mark.asyncio
async def test_login_data_store():
    # Setup browser
    browser = await pyppeteer.launch(PYPPETEER_OPTIONS)
    page = await browser.newPage()

    safeClick = SafeClick(page=page)
    navClick = safeClick.click
    click = page.click
    wait = safeClick.wait

    # Go to data store
    await page.goto(DATA_STORE_URL)

    # Set the viewport
    await page.setViewport({'width': 1600, 'height': 900})

    # Press datasets
    dataset_button_selector = "#dataset-tab-button"
    await wait(dataset_button_selector)
    await navClick(dataset_button_selector)

    # Click on login button
    login_selector = "#prompt-login-button"
    await wait(login_selector)
    await navClick(login_selector)

    # Type username and password once keycloak pops up
    await wait('#username')
    await click('#username')
    await page.type('#username', USERNAME)

    await wait('#password')
    await click('#password')
    await page.type('#password', PASSWORD)

    # Submit
    await wait('#kc-login')
    await navClick('#kc-login')

    # Press profile button
    profile_button_selector = "#profile-button"
    await wait(profile_button_selector)
    await navClick(profile_button_selector)

    # Wait for profile
    profile_title_selector = "#profile-title"
    element = await wait(profile_title_selector)

    # Get the text from the profile tag and check it says Profile
    value = await (await element.getProperty('innerText')).jsonValue()
    assert value == "Profile"

    await browser.close()


# @pytest.mark.xfail(reason="SSO feature not working between components.")
@pytest.mark.asyncio
async def test_portal_to_data_store_sso():
    # Setup browser
    browser = await pyppeteer.launch(PYPPETEER_OPTIONS)
    page = await browser.newPage()

    safeClick = SafeClick(page=page)
    navClick = safeClick.click
    click = page.click
    wait = safeClick.wait

    # Go to landing portal
    await page.goto(LANDING_PORTAL_URL)

    # Set the viewport
    await page.setViewport({'width': 1600, 'height': 900})

    # Press log in tab button
    # directs straight to kc
    login_tab_selector = "#login-tab-button"
    element = await wait(login_tab_selector)
    await navClick(login_tab_selector)

    # Type username and password
    await wait('#username')
    await click('#username')
    await page.type('#username', USERNAME)

    await wait('#password')
    await click('#password')
    await page.type('#password', PASSWORD)

    # Submit
    await wait('#kc-login')
    await navClick('#kc-login')

    # Now we are logged in - go to data store now

    # Go to data store
    await page.goto(DATA_STORE_URL)
    await page.waitForNavigation()

    # Check profile etc is present

    # Press profile button
    profile_button_selector = "#profile-button"
    await wait(profile_button_selector)
    await navClick(profile_button_selector)

    # Wait for profile
    profile_title_selector = "#profile-title"
    element = await wait(profile_title_selector)

    # Get the text from the profile tag and check it says Profile
    value = await (await element.getProperty('innerText')).jsonValue()
    assert value == "Profile"

    await browser.close()


@pytest.mark.asyncio
async def test_open_shared_link_requires_login():
    # Setup browser
    browser = await pyppeteer.launch(PYPPETEER_OPTIONS)
    page = await browser.newPage()

    safeClick = SafeClick(page=page)
    navClick = safeClick.click
    click = page.click
    wait = safeClick.wait

    # Go to shared resource link -> registry
    await page.goto(SHARED_LINK)

    # Set the viewport
    await page.setViewport({'width': 1600, 'height': 900})

    # Press login button
    selector = "#prompt-login-button"
    await wait(selector)
    await navClick(selector)

    # Type username and password into auto prompted login
    await wait('#username')
    await click('#username')
    await page.type('#username', USERNAME)

    await wait('#password')
    await click('#password')
    await page.type('#password', PASSWORD)

    # Submit
    await wait('#kc-login')
    await navClick('#kc-login')

    # Now we are logged in - the shared resource should load
    meta_selector = "#loaded-subtype-title"
    meta_tag = await wait(meta_selector)

    await browser.close()


@pytest.mark.asyncio
async def test_login_then_open_link():
    # Setup browser
    browser = await pyppeteer.launch(PYPPETEER_OPTIONS)
    page = await browser.newPage()

    safeClick = SafeClick(page=page)
    navClick = safeClick.click
    click = page.click
    wait = safeClick.wait

    # Go to data store
    await page.goto(DATA_STORE_URL)

    # Set the viewport
    await page.setViewport({'width': 1600, 'height': 900})

    # Press log in tab button
    # directs straight to kc
    login_tab_selector = "#login-tab-button"
    element = await wait(login_tab_selector)
    await navClick(login_tab_selector)

    # Type username and password
    await wait('#username')
    await click('#username')
    await page.type('#username', USERNAME)

    await wait('#password')
    await click('#password')
    await page.type('#password', PASSWORD)

    # Submit
    await wait('#kc-login')
    await navClick('#kc-login')

    # Press profile button
    profile_button_selector = "#profile-button"
    await wait(profile_button_selector)
    await navClick(profile_button_selector)

    # Wait for profile
    profile_title_selector = "#profile-title"
    element = await wait(profile_title_selector)

    # Get the text from the profile tag and check it says Profile
    value = await (await element.getProperty('innerText')).jsonValue()
    assert value == "Profile"

    # Now we are logged in - try to open shared link
    page = await browser.newPage()

    safeClick = SafeClick(page=page)
    navClick = safeClick.click
    click = page.click
    wait = safeClick.wait

    # Go to landing portal
    await page.goto(SHARED_LINK)

    # Set the viewport
    await page.setViewport({'width': 1600, 'height': 900})

    # Now we are logged in - the shared data should load

    meta_selector = "#loaded-subtype-title"
    meta_tag = await wait(meta_selector)

    await browser.close()

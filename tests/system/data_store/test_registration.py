import pytest
import pyppeteer
from data_store.config import *
from common_config import *
import asyncio


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
async def test_register_form_loads():
    # Setup browser
    browser = await pyppeteer.launch(PYPPETEER_OPTIONS)
    page = await browser.newPage()

    # Setup click and wait wrappers
    safeClick = SafeClick(page=page)
    navClick = safeClick.click
    click = page.click
    wait = safeClick.wait

    # browse to data store
    await page.goto(DATA_STORE_URL)
    await page.setViewport({'width': 1600, 'height': 900})

    # Click on datasets button
    dataset_button_selector = "#dataset-tab-button"
    await wait(dataset_button_selector)
    await navClick(dataset_button_selector)

    # Click on login button
    login_selector = "#prompt-login-button"
    await wait(login_selector)
    await navClick(login_selector)
    
    await wait('#username')

    # Type username and password
    await click('#username')
    await page.type('#username', USERNAME)
    await click("#password")
    await page.type('#password', PASSWORD)

    await wait('#kc-login')
    await navClick('#kc-login')

    # Click datasets
    dataset_button_selector = dataset_button_selector
    await wait(dataset_button_selector)
    await navClick(dataset_button_selector)

    # Click register button
    register_selector = '#dataset-registration-button'
    # Wait for some time - unusual behaviour around register button
    await page.waitFor(3000)
    await wait(register_selector)
    await navClick(register_selector)

    # Wait for json form to render
    form_selector = "#registration-form"
    await wait(form_selector)

    # Finish browser session
    await browser.close()

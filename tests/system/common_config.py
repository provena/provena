import os
from distutils.util import strtobool

DATA_STORE_URL = os.getenv("DATA_STORE_URL")
LANDING_PORTAL_URL = os.getenv("LANDING_PORTAL_URL")
HEADLESS_MODE = bool(strtobool(
    os.getenv("HEADLESS_MODE", "true")))
SELECT_TIMEOUT = int(os.getenv("SELECT_TIMEOUT", 12000))
CODEBUILD_MODE = bool(strtobool(
    os.getenv("COMPAT_CODEBUILD_MODE", "false")))
CHROME_PATH = os.getenv("CHROME_PATH")
if CODEBUILD_MODE:
    assert CHROME_PATH

PYPPETEER_OPTIONS = {
    'autoClose': False,
    'headless': HEADLESS_MODE,
    'slowMo': 5,
    'executablePath': CHROME_PATH
}

if CODEBUILD_MODE:
    PYPPETEER_OPTIONS['args'] = ['--no-sandbox']

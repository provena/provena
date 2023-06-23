# System Tests


## UI Login Tests

### Quick start

Working on linux EC2 environment
Ensure you have tests/system open as your vscode working directory, then in a terminal, run:
-   python3 -m venv .venv
-   source .venv/bin/activate
-   pip install -r requirements.txt
-   ./dependencies.sh
-   touch .env (then fill out the file as below)
-   pytest --envfile .env (or use vs code testing panel)

### Test cases

These are E2E system tests which test core functionality pathways to ensure we aren't having feature regression as new features are developed. If these workflows change these tests will need to be updated.

Currently the following flows are tested:

-   Load website and check title is present
-   Load landing portal, login and check profile works
-   Load data store, login and check profile works
-   Load landing portal, login then navigate to data store and check still logged in
-   Load a shared data store link, login when prompted, then check that entry is loaded (currently not working due to bug RRAPIS-464)
-   Log into data store, then open shared link in new tab and check login works (currently not working due to bug RRAPIS-464)
-   Currently two work around tests showing the profile -> back button work around are included for the above two broken use cases

### .env file

Before running the tests, create a .env file and make sure you are in the right working directory in vscode. The working directory for the system tests is system (i.e. the directory this file is in). Also check login/config.py to see how the environment variables are used (currently).

The .env file should include (replacing ... with appropriate values):

```
TEST_USERNAME=...
TEST_PASSWORD=...
HEADLESS_MODE=true
```
You can get test usernames and passwords from the AWS Secrets Manager. Look for the secret named 'dev_integration_test_bots'.

The headless mode variable is optional and defaults to true. If you select headless false then an actual visual browser will be opened to run the tests and slow mo mode will be enabled to enable visualisation of browser behaviour. This won't work (without more complex setup) on remote SSH environments so ensure you are working on a local version for debugging visually.

After setting up the .env file I recommend reloading the vs code window with `ctrl shift p -> reload window` command.

You can use `pytest --envfile .env` command in the terminal to run from the console.

### Pyppeteer

I found that the pyppeteer was missing some chromium headless dependencies on an EC2 instance - I installed them by using `./dependencies.sh`.

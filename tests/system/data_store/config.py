import os

USERNAME = os.getenv("TEST_USERNAME")
PASSWORD = os.getenv("TEST_PASSWORD")
SHARED_LINK = os.getenv("SHARED_LINK", "http://hdl.handle.net/10378.1/1685623")

assert USERNAME, "Didn't provide USERNAME env variable."
assert PASSWORD, "Didn't provide PASSWORD env variable."




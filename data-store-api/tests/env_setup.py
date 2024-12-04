import os

# These need to be defined as they are required as part of
# setting up the app itself, rather than being required at
# app endpoint runtime. See BaseConfig in the config.py file.
# Other config options are set using the provide global config
# fixture.
os.environ['KEYCLOAK_ENDPOINT'] = ""
os.environ['STAGE'] = "DEV"
os.environ['DOMAIN_BASE'] = "www.google.com"
os.environ['TEST_MODE'] = "true"
os.environ['AWS_DEFAULT_REGION'] = 'ap-southeast-2'
os.environ['USER_KEY_ID'] = '1234'
os.environ['USER_KEY_REGION'] = 'us-east-1'
os.environ['USER_KEY_HEADER'] = 'X-User-Context'
os.environ['monitoring_enabled'] = 'False'
os.environ['USER_KEY_ID'] = '1234'
os.environ['USER_KEY_REGION'] = 'us-east-1'
os.environ['USER_CONTEXT_HEADER'] = 'X-User-Context'

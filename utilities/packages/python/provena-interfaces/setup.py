from setuptools import setup, find_packages  # type: ignore
import os
from package_readme import long_description
import re

# 0.1.0 is the 'version' installs from this directory from other components in repo will use
version = os.getenv('TAG_NAME', 'v0.1.0')

setup(
    name='provena-interfaces',
    # format acceptably as 'v0.0.1' or '0.0.1',
    version=version,
    description='Interfaces for Provena Application (see https://provena.io)',
    long_description=long_description,
    long_description_content_type='text/markdown',
    packages=find_packages(
        include=[
            'ProvenaInterfaces',
            'ProvenaInterfaces.*',
            'ProvenaInterfaces.*.*',
        ]
    ),
    install_requires=[
        'fastapi==0.88.0',
        'pydantic[email]==1.10.17',
        'email-validator',
        'isodate',
    ],
    package_data={
        'ProvenaInterfaces': ['py.typed']
    },
    url="https://provena.io",
    maintainer_email="rrap-mds-is-support@csiro.au",

)

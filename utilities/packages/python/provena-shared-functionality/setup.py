from setuptools import setup, find_packages #type: ignore

setup(
    name='provena-shared-functionality',
    version='0.1.0',
    packages=find_packages(
        include=[
            'ProvenaSharedFunctionality',
            'ProvenaSharedFunctionality.*',
            'ProvenaSharedFunctionality.*.*',
        ]
    ),
    install_requires=[
        'sentry-sdk[fastapi]',
    ],
    package_data={
        'ProvenaSharedFunctionality': ['py.typed']
    }
)
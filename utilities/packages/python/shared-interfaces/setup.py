from setuptools import setup, find_packages  # type: ignore

setup(
    name='shared-interfaces',
    version='0.1.0',
    packages=find_packages(
        include=[
            'SharedInterfaces',
            'SharedInterfaces.*',
            'SharedInterfaces.*.*',
        ]
    ),
    install_requires=[
        'pydantic',
        'fastapi',
        'pydantic[email]',
        'email-validator'
    ],
    package_data={
        'SharedInterfaces': ['py.typed']
    }
)

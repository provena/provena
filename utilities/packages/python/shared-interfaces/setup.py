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
        'fastapi==0.88.0',
        'pydantic[email]==1.10.12',
        'email-validator',
        'isodate',        
    ],
    package_data={
        'SharedInterfaces': ['py.typed']
    }
)

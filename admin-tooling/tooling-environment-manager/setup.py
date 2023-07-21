from setuptools import setup, find_packages  # type: ignore

setup(
    name='tooling-environment-manager',
    version='0.1.0',
    packages=find_packages(
        include=[
            'ToolingEnvironmentManager',
            'ToolingEnvironmentManager.*',
            'ToolingEnvironmentManager.*.*',
        ]
    ),
    install_requires=[
        'pydantic==1.*'
    ],
    package_data={
        'ToolingEnvironmentManager': ['py.typed']
    }
)

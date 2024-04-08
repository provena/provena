from setuptools import setup, find_packages #type: ignore

setup(
    name='registry-shared-functionality',
    version='0.1.0',
    packages=find_packages(
        include=[
            'RegistrySharedFunctionality',
            'RegistrySharedFunctionality.*',
            'RegistrySharedFunctionality.*.*',
        ]
    ),
    install_requires=[],
    package_data={
        'RegistrySharedFunctionality': ['py.typed']
    }
)
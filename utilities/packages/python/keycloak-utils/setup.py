from setuptools import setup, find_packages  # type: ignore

setup(
    name='keycloak-utils',
    version='0.1.0',
    packages=find_packages(
        include=['KeycloakRestUtilities', 'KeycloakRestUtilities.*']),
    install_requires=['requests', 'types-requests', 'pydantic==1.*', 'python-jose'],
    package_data={
        'KeycloakRestUtilities': ['py.typed']
    }
)

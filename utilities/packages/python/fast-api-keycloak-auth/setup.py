from setuptools import setup, find_packages

setup(
    name='fast-api-keycloak-auth',
    version='0.1.0',
    packages=find_packages(include=['KeycloakFastAPI', 'KeyCloakFastAPI.*']),
    install_requires=['fastapi', 'pydantic', 'requests', 'python-jose'],
    package_data = {
        'KeycloakFastAPI' : ['py.typed']
    }
)
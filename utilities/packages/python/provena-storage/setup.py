from setuptools import setup, find_packages

setup(
    name="provena-storage",
    version="0.1.0",
    packages=find_packages(),
    install_requires=["boto3", "sqlalchemy", "psycopg2-binary"],
)

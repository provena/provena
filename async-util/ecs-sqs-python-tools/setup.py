from setuptools import setup, find_packages #type: ignore

setup(
    name='ecs-sqs-python-tools',
    version='0.1.0',
    packages=find_packages(
        include=[
            'EcsSqsPythonTools',
            'EcsSqsPythonTools.*',
            'EcsSqsPythonTools.*.*',
        ]
    ),
    install_requires=[
        'boto3',
        'pydantic'
    ],
    package_data={
        'EcsSqsPythonTools': ['py.typed']
    }
)

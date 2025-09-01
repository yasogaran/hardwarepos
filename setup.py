from setuptools import setup, find_packages

setup(
    name="billing_app",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        'flet',
        'pandas',
    ],
    entry_points={
        'console_scripts': [
            'billing-app=billing_app.main:main',
        ],
    },
)
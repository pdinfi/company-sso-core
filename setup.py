"""Installable package setup for company_sso_core."""
from setuptools import setup, find_packages

setup(
    name="company-sso-core",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "Django>=4.2,<6.0",
        "djangorestframework>=3.14.0,<4.0.0",
        "drf-spectacular>=0.27.0,<0.28.0",
        "requests>=2.31.0,<3.0.0",
    ],
    python_requires=">=3.10",
)

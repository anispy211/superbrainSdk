from setuptools import setup, find_packages

setup(
    name="superbrain",
    version="0.3.0",
    packages=find_packages(),
    install_requires=["numpy"],
    description="Python SDK for Superbrain Distributed Memory",
    author="Anispy",
)

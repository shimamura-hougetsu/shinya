from setuptools import setup, find_packages

setup(
    name="shinya",
    version="0.1a1",
    packages=find_packages(),
    install_requires=['lxml'],
    python_requires=">=3.6"
)

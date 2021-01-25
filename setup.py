from setuptools import setup, find_packages

setup(
    name="shinya",
    version="0.1a1",
    description='A Python package to edit BDMV components like MPLS, CLPI, etc.',
    url='http://github.com/shimamura-hougetsu/shinya',
    author='Shimamura Hougetsu',
    license='MIT',
    packages=find_packages(),
    install_requires=['lxml>=4.6'],
    python_requires=">=3.6"
)

import os

from setuptools import find_packages, setup

with open(os.path.join("version.txt")) as version_file:
    version_from_file = version_file.read().strip()

with open("requirements.txt") as f_required:
    required = f_required.read().splitlines()

with open("test_requirements.txt") as f_tests:
    required_for_tests = f_tests.read().splitlines()

setup(
    name="cloudshell-networking-arista",
    url="https://github.com/QualiSystems/cloudshell-networking-arista",
    author="QualiSystems",
    author_email="info@qualisystems.com",
    packages=find_packages(),
    install_requires=required,
    python_requires="~=3.7",
    test_suite="tests",
    tests_require=required_for_tests,
    version=version_from_file,
    description="QualiSystems Python package",
    long_description="Arista Networking Shell operations",
    long_description_content_type="text/x-rst",
    include_package_dat=True,
)

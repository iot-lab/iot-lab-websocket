import os
from setuptools import setup, find_packages

PACKAGE = "iotlabwebsocket"


def readme(fname):
    """Utility function to read the README. Used for long description."""
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


def get_version(package):
    """Extract package version without importing file.

    Inspired from pep8 setup.py.
    """
    with open(os.path.join(package, "__init__.py")) as init_fd:
        for line in init_fd:
            if line.startswith("__version__"):
                return eval(line.split("=")[-1])


if __name__ == "__main__":

    setup(
        name=PACKAGE,
        version=get_version(PACKAGE),
        description=(
            "Provides server exposing IoT-LAB nodes via" "a websocket connection."
        ),
        long_description=readme("README.md"),
        author="IoT-LAB Team",
        author_email="admin@iot-lab.info",
        url="http://www.iot-lab.info",
        license="BSD",
        keywords="iot websocket serial web",
        platforms="any",
        packages=find_packages(),
        scripts=[],
        entry_points={
            "console_scripts": [
                "iotlab-websocket-service = " "iotlabwebsocket.service_cli:main",
            ],
        },
        install_requires=[
            "tornado>=6.1",
        ],
        classifiers=[
            "Development Status :: 4 - Beta",
            "Programming Language :: Python :: 3.6",
            "Programming Language :: Python :: 3.7",
            "Programming Language :: Python :: 3.8",
            "Intended Audience :: Developers",
            "Environment :: Console",
            "Topic :: Communications",
            "License :: OSI Approved :: ",
            "License :: OSI Approved :: BSD License",
        ],
        zip_safe=False,
    )

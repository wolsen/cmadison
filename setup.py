#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
from subprocess import check_output


def get_dependencies():
    """Reads the dependencies from the requirements file."""
    with open('requirements.txt', 'r') as d:
        dependencies = d.read()

    return dependencies


def get_version():
    """Returns the version as a relative commit to a tag and version"""
    return check_output(['git', 'describe', '--tags']).decode('utf-8')


def get_long_description():
    with open('README.md', 'r') as f:
        text = f.read()
    return text


setup(
    name="cmadison",
    version=get_version(),
    author="Billy Olsen",
    author_email="billy.olsen@gmail.com",
    description=("A wrapper for rmadison including basic support for "
                 "Ubuntu Cloud Archive"),
    long_description=get_long_description(),
    long_description_content_type='text/markdown',
    install_requires=get_dependencies(),
    packages=find_packages(),
    url='http://github.com/wolsen/cmadison',
    entry_points={
        'console_scripts': [
            'cmadison = cmadison.cmadison:main',
            ]
        },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)"
    ]
)

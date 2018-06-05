#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages


def get_dependencies():
    """Reads the dependencies from the requirements file."""
    with open('requirements.txt', 'r') as d:
        dependencies = d.read()

    return dependencies


def get_version():
    """Returns the version as a relative commit to a tag and version"""
    pass


setup(
    name="cmadison",
    version="0.0.3",
    author="Billy Olsen",
    author_email="billy.olsen@gmail.com",
    description=("A wrapper for rmadison including basic support for "
                 "Ubuntu Cloud Archive"),
    install_requires=get_dependencies(),
    packages=find_packages(),
    url='http://github.com/wolsen/cmadison',
    entry_points={
        'console_scripts': [
            'cmadison = cmadison.cmadison:main',
            ]
        },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)"
    ]
)

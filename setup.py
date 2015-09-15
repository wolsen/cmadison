#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from setuptools import setup, find_packages


dependencies = ["lxml", ]


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name="cmadison",
    version="0.0.1",
    author="Billy Olsen",
    author_email="billy.olsen@canonical.com",
    description="",
    install_requires=dependencies,
    packages=find_packages(),
    long_description=read('README.md'),
    entry_points={
        'console_scripts': [
            'cmadison = cmadison.cmadison:main',
            ]
        },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Console",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)"
    ]
)

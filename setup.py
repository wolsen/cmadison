#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from setuptools import setup, find_packages


dependencies = ["lxml", ]

setup(
    name="cmadison",
    version="0.0.3",
    author="Billy Olsen",
    author_email="billy.olsen@gmail.com",
    description=("A wrapper for rmadison including basic support for "
                 "Ubuntu Cloud Archive"),
    install_requires=dependencies,
    packages=find_packages(),
    url='http://github.com/wolsen/cmadison',
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

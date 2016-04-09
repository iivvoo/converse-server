#!/usr/bin/env python
# -*- coding: utf-8 -*-


try:
    from setuptools import setup, find_packages
except ImportError:
    from distutils.core import setup


with open('README.md') as readme_file:
    readme = readme_file.read()

with open('HISTORY.md') as history_file:
    history = history_file.read()

requirements = [
    "six",
    "websockets",
    "aiohttp",
    "pillow",
    "fake-factory"
]

test_requirements = [
    # TODO: put package test requirements here
]

setup(
    name='converse-server',
    version='0.1.0',
    description="Converse is a multi protocol chat client/server/proxy "
                "with a focus ofunctionality and user friendlyness",
    long_description=readme + '\n\n' + history,
    entry_points={
        "console_scripts": ["converse=converse.server:main",
                            "testbot=converse.bot:main"]
    },
    author="Ivo van der Wijk",
    author_email='ivo+converse@in.m3r.nl',
    url='https://github.com/iivvoo/converse-server',
    packages=find_packages(),
    include_package_data=True,
    install_requires=requirements,
    license="ISCL",
    zip_safe=False,
    keywords='converse-server',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: ISC License (ISCL)',
        'Natural Language :: English',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
    test_suite='tests',
    tests_require=test_requirements
)

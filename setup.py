#-*- coding: utf-8 -*-

'''
Copyright 2014, 2015 Yoshida Shin

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
'''

from setuptools import setup, find_packages

long_description = open("README.rst").read() + open("docs/CHANGELOG.rst").read()

classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: Apache Software License",
    "Programming Language :: Python",
    "Programming Language :: Python :: 2",
    "Programming Language :: Python :: 2.7",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.3",
    "Programming Language :: Python :: 3.4",
    "Topic :: Software Development",
    "Topic :: Software Development :: Libraries",
    "Topic :: Software Development :: Libraries :: Python Modules"
]

requires = []

setup(
    name='thread_utils',
    version="1.0.0",
    description='Wrapper of threading module providing Actor interface.',
    long_description=long_description,
    url="https://github.com/wbcchsyn/python-thread_utils",
    author='Yoshida Shin',
    author_email='wbcchsyn@gmail.com',
    license=['Apache License 2.0'],
    classifiers=classifiers,
    packages=find_packages('src'),
    package_dir={"": "src"},
    platforms=['linux', 'unix'],
    install_requires=requires,
    use_2to3 = True,
)

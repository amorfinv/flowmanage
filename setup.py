#!/usr/bin/env python

"""The setup script."""

from setuptools import setup, find_packages

with open('README.md') as readme_file:
    readme = readme_file.read()

requirements = [ ]

test_requirements = [ ]

setup(
    author="Andres Morfin Veytia",
    author_email='a.morfinveytia@tudelft.nl',
    python_requires='>=3.6',
    classifiers=[
        'Intended Audience :: Developers',
        'Natural Language :: English',
    ],
    description="FlowManage for QGIS",
    install_requires=requirements,
    include_package_data=True,
    keywords='flowmanage',
    name='flowmanage',
    packages=find_packages(include=['flowmanage', 'flowmanage.*']),
    tests_require=test_requirements,
    url='https://github.com/amorfinv/flowmanage',
    version='0.1.0',
    zip_safe=False,
)

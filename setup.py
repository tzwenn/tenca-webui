#!/usr/bin/env python3
from setuptools import find_packages, setup

setup(
	name='tenca_webui',
	version='0.0.1',
	packages=find_packages(),
	include_package_data=True,
	zip_safe=False,
	install_requires=[
		'tenca',
		'email_validator',
		'Flask-OIDC',
		'Flask-SQLAlchemy',
		'Flask-WTF',
		'Flask', # Must be last
	],
)

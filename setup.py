# -*- coding: utf-8 -*-
from distutils.core import setup
from setuptools import find_packages
setup(name = 'EasySchedule',
      py_modules = ['EasySchedule'],
      version = '0.0.1',
      description = '',
      long_description = '',
      author = 'maylill',
      author_email = '642722474@qq.com',
      url = '',
      license = 'MIT',
      install_requires = [
        'peewee',
        'schedule',
        'PyYAML'
      ],
      keywords = 'EasySchedule',
      packages = find_packages('src'),
      package_dir = {'':'src'},
      include_package_data = True
)
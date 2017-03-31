# coding: UTF-8

from setuptools import setup, find_packages

setup(
    name='iris',
    version='1.0',
    packages=find_packages(),
    description='export iOS/Android project from unity in cli',
    author='hananana',
    license='MIT',
    install_requires=[
        'click',
    ],
    entry_points='''
        [console_scripts]
        iris=src.iris:cmd
    ''',
)

# -*- coding: utf-8 -*-
from distutils.core import setup

setup(
    name='anicration',
    version='0.0.6alpha0',
    description="Allows one to download LLSS Seiyuu's pictures with command prompt.",
    author='corruptedant',
    author_email='corruptedant@gmail.com',
    license='MIT',
    packages=['anicration',],
    long_description=open('README').read(),
    install_requires=[
        "Tweepy >= 3.5.0",
        "requests >= 2.13.0",
    ],
    entry_points={
        'console_scripts':[
            'anicration=anicration.anicration:main',
            'track_twitter_info=anicration.seiyuuhandler:track_twitter_info'
        ]
    }
)

# -*- coding: utf-8 -*-
from distutils.core import setup

setup(
    name='anicration',
    version='0.6.0alpha3',
    description="Allows one to download LLSS Seiyuu's pictures with command prompt.",
    author='corruptedant',
    author_email='corruptedant@gmail.com',
    license='MIT',
    packages=['anicration',],
    long_description=open('README').read(),
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.6',
    ],
    keywords='twitter lovelive',
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

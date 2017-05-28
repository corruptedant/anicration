# -*- coding: utf-8 -*-
"""
Provides a whole list of functions for (currently) Twitter related seiyuu data/media works.
Uses a config file(defaults to %appdata%/anicration/config.txt) which most functions needs.
config_create() creates a config file(you may provide a location) at affromentioned location.\n
twitter_media_downloader() does the bulk of downloading photo/video of accounts with the added
benefit of allowing one to customize their inputs if they know Python.\n
twit_dl_parser() allows one to more easily input parameters(twitter_media_downloader() uses
kwargs which means lots of reading).\n
seiyuu_twitter() is basically twit_dl_parser() but for globally callable script uses.
track_twitter_info() downloads all 9 seiyuu current-user-data for tracking numbers and maths.\n
Refer to the wiki for more information.
"""
import os
import sys
import json
import logging
from time import sleep
from datetime import datetime

import tweepy

from .auxiliaryfuncs import _v_print, _set_verbosity
from .mediaparser import media_parser
from .confighandler import ConfigHandler
from .downloader import pic_downloader
from .downloader import _folder_check_empty

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
BASE_CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'config', 'example.txt')

def config_create(file_location=None, file_name='config.txt'):
    """Creates a config at file location. Defaults to %appdata%/anicration/config.txt
    You'll also need to pass in the config location for initialization if a custom file location
    is provided"""
    if file_location is None:
        file_location = os.path.join(os.getenv('APPDATA'), 'anicration')
        logger.info('No file location provided, defaulting to ' + file_location)
        try:
            os.makedirs(file_location)
        except FileExistsError:
            _v_print('File ' + file_name + 'already exists at ' + file_location, verbosity=2)
        else:
            _v_print('File ' + file_name + 'already exists at ' + file_location, verbosity=2)
    #__file__ is the file of the function installed, '.' means the location of __main__
    with open(BASE_CONFIG_PATH, 'r', encoding='utf-8') as f:
        with open(os.path.join(file_location, file_name), 'w', encoding='utf-8') as f2:
            f2.write(f.read())

def _tweepy_retry(function=None, msg='', max_retry=3):
    retry = 0
    while retry != max_retry + 1:
        try:
            if function is not None:
                return function()
        except tweepy.TweepError:
            _v_print(
                '{} failed ({}/{}), retrying in {} seconds'.format(
                    msg, retry, max_retry, (retry + 1)*5
                ),
                verbosity=0, level=logger.debug, end='\r'
            )
            sleep((retry+1)*5)
            retry = retry + 1
        else:
            _v_print('', verbosity=3, level=None, end='\r')
    _v_print(
        '\nMaximum retry exceeded, stopping program...            ',
        verbosity=1, logger=None)
    logger.critical(
        'Maximum retry at {} with message {}, stopping program.'.format(str(function), msg)
        )
    sys.exit(1)

def _tweepy_init(auth_keys):
    # Tweepy authentication and initiation
    try:
        auth = tweepy.OAuthHandler(auth_keys[0], auth_keys[1])
        auth.set_access_token(auth_keys[2], auth_keys[3])
    except IndexError as err:
        print('INDEXERROR : Did you miss a comma in your authentication keys?')
        logger.exception('Incomplete auth_keys \n%s', err)
        raise err

    return _tweepy_retry(
        function=lambda: tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True),
        msg='Tweepy initiation'
    )

def _get_json(api, twitter_id: str, items: int):
    def _get_cursor():
        return tweepy.Cursor(api.user_timeline, id=twitter_id, tweet_mode='extended')
    # [{<response>}, {<response>}, .., <response>,] (removes last dangling comma)
    def _get_status():
        json_data = '['
        json_num = int()
        for (idx, status) in enumerate(_get_cursor().items(items)):
            json_data = json_data + json.dumps(status._json, ensure_ascii=False) + ','
            _v_print(
                'Retrived', str(idx + 1), 'JSON responses.',
                verbosity=1, level=None, end='\r'
            )
            json_num = idx + 1
        return json_data, json_num
    json_data, json_num = _tweepy_retry(_get_status, 'JSON retrieving')
    print('')
    logger.info('Retrived ' + str(json_num) + ' JSON responses')
    json_data = json_data[:len(json_data)-1] + ']'
    return json_data
# TODO : Deprecate *auth_keys and go full kwargs['auth_keys'] only
def twitter_media_downloader(*auth_keys, **kwargs):
    """Downloads twitter media from an account. All variables are pass in kwargs. Refer to wiki."""
    if any(auth_keys) is False:
        try:
            auth_keys = kwargs['auth_keys']
        except KeyError:
            _v_print('Authentication keys is missing.', 0, logger.warning)
        else:
            _v_print('Sucessfully obtained keys from config.')

    items = kwargs.pop('items', 0)
    # Check the folders/locations
    json_loc = _folder_check_empty(kwargs.pop('json_loc', None), 'Downloader', 'json')
    log_loc = _folder_check_empty(kwargs.pop('log_loc', None), 'Downloader', 'log')
    if kwargs['pic_loc'] == '' or kwargs['pic_loc']  is None:
        subfolder_create = True
    else:
        subfolder_create = False
    # this is the master folder. more folders is created to sort by person
    pic_loc = _folder_check_empty(kwargs['pic_loc'], 'Downloader', 'pictures')

    api = _tweepy_init(auth_keys)

    json_save = kwargs.pop('json_save', True)
    twitter_id = kwargs['twitter_id']
    # Defaults to twitter_id(without the '@')
    file_name = twitter_id[1:].lower()
    date_ext = "-{:%y%m%d%H%M%S}".format(datetime.now())
    _v_print('Twitter id:', twitter_id)

    # pic_path is the folder the the pic will be stored in, psuedomeaning == final loc
    if subfolder_create is True:
        pic_path = os.path.join(pic_loc, file_name)
    else:
        pic_path = pic_loc
    _v_print('Picture directory : ' + pic_path)

    date = kwargs.pop('date', False)
    json_path = os.path.join(json_loc, file_name) + (date_ext if date is True else '') + '.json'

    json_data = _get_json(api, twitter_id, items)

    if json_save is True:
        with open(json_path, 'w', encoding="utf-8") as file:
            _v_print('Storing json file at ' + json_path, verbosity=None)
            file.write(json_data)

    log_name = file_name +  (date_ext if date is True else '') + '.txt'
    log_path = os.path.join(log_loc, log_name)
    if kwargs['parser'][0] is True:
        media_links = media_parser(json_data, log_path, kwargs['parser'][1])
        if kwargs['downloader'] is True:
            pic_downloader(media_links, pic_path)
    elif kwargs['parser'][0] is False and kwargs['downloader'] is True:
        media_links = media_parser(json_data, log_path, kwargs['parser'][1])
        pic_downloader(media_links, pic_path)

# One may call this and give it their own custom_config_path and **kwargs as well
def seiyuu_twitter(custom_config_path=None, **kwargs):
    """Initated when `$anicration` is called without arguments."""
    logging.basicConfig(filename='seiyuu_twitter.txt', level=logging.INFO)
    print('A config file will be created at ', os.path.join(os.getcwd(), 'seiyuu_twitter.txt'))
    logging.info("{:%Y/%m/%d %H:%M:%S}".format(datetime.now()))
    config = ConfigHandler(custom_config_path)
    _set_verbosity(0 if config.verbosity == 0 else config.verbosity - 1)
    for kw in config.twitter_id_loc:
        data_loc = None
        if config.data_in_pic_loc is True:
            data_loc = os.path.join(config.twitter_id_loc[kw], 'data')
        payload = {
            'keys_from_args' : config.keys_from_args,
            'auth_keys': kwargs['auth_keys'] if config.keys_from_args is True else config.auth_keys,
            'twitter_id' : kw,      #keyword is the username
            'items' : config.items,
            'parser' : (config.parser, True),
            'downloader' : config.downloader,
            'json_loc' : config.json_loc if data_loc is None else data_loc,
            'log_loc' : config.log_loc if data_loc is None else data_loc,
            'pic_loc' : config.twitter_id_loc[kw],
            'date' : True
        }
        try:
            twitter_media_downloader(**payload)
        except KeyboardInterrupt:
            print('ERROR : User interrupted the program.')
            sys.exit(1)
    print('Complete')

def track_twitter_info(custom_config_path=None, no_wait=False):
    """Does an hourly download of the seiyuu's info."""
    print('Initializing track_seiyuu_info()...')
    seiyuu_names = ('@anju_inami', '@saito_shuka', '@Rikako_Aida', '@aikyan_', '@aina_suzuki723',
                    '@suwananaka', '@box_komiyaarisa', '@furihata_ai', '@kanako_tktk')
    tsi = logging.getLogger(name=__file__)
    logging.basicConfig(filename='twitter_info.txt', level=logging.INFO)
    print('Config file created at', os.path.join(os.getcwd(), 'twitter_info.txt'))
    logging.info('TIME AT THE LAUNCH OF PROGRAM : '+"{:%Y/%m/%d %H:%M:%S}".format(datetime.now()))
    config = ConfigHandler(custom_config_path)
    auth_keys = config.auth_keys
    def get_user_data():
        """Get all seiyuu data into 1 single [] JSON file."""
        dt_before = datetime.now()

        # Tweepy
        print('Authentication...', end='\r')
        api = _tweepy_init(auth_keys)
        _v_print('Authentication complete.', level=tsi.info, end='\r')

        # variables
        date_ext = "-{:%y%m%d%H%M%S}".format(datetime.now())
        file_name = 'user_data' + date_ext + '.json'
        tsi.info('File name : ' + file_name)
        json_data = '['
        for username in seiyuu_names:
            print('Currenting downloading media from :', username, '              ', end='\r')
            tsi.info('Obtaining user_data from ' + username)
            user_data = _tweepy_retry(
                function=lambda um=username: api.get_user(um), msg='Username retriving'
            )
            json_data = json_data + json.dumps(user_data._json, ensure_ascii=False) + ','
        json_data = json_data[:len(json_data)-1] + ']'
        with open(file_name, 'w', encoding='utf-8') as file:
            file.write(json_data)
            _v_print('Sucessfully logged json_data.', level=tsi.info, end='\r')
        # cleaning stuffs
        dt_after = datetime.now() - dt_before
        _v_print('Sucessfully downloaded user data :', file_name,
                 '. Process took :', str(dt_after.total_seconds()), 'seconds', level=tsi.info)
    if no_wait is True:
        get_user_data()
    while True:
        dt = datetime.now()
        print(dt)
        if dt.minute != 0 or dt.second != 0:
            delay_in_seconds = 3600 - dt.minute * 60 - dt.second
            delay_m, delay_s = int(delay_in_seconds/60), delay_in_seconds % 60
            print('Sleeping for ' + str(delay_m) + ' minutes, ' + str(delay_s) + ' seconds...')
            sleep(3600 - dt.minute * 60 - dt.second)
            print('Starting the process...')
            get_user_data()
            sleep(1)
        elif dt.minute == 0 and dt.second == 0:
            get_user_data()
            sleep(1)
        sleep(1)

# TODO : Implement json_save
def twit_dl_parser(config_mode=True, config_path=None, twitter_usernames=None, items=0, parser=True,
                   downloader=True, json_save_location=None, log_save_location=None,
                   pic_save_location=None, **kwargs):
    """This method is not recommended. May be considered for deprecation as well."""
    if config_mode is True:
        config = ConfigHandler(config_path)
        payload = {
            'keys_from_args' : config.keys_from_args,
            'twitter_usernames' : config.twitter_usernames,
            'items' : config.items,
            'parser' : config.parser,
            'downloader' : config.downloader,
            'json_loc' : config.json_loc,
            'log_loc' : config.log_loc,
            'pic_loc' : config.pic_loc
        }
        for keyword in kwargs:
            logger.debug("%s : %s", keyword, kwargs[keyword])
    else:
        payload = {
            'keys_from_args' : False,
            'twitter_usernames' : twitter_usernames,
            'items' : items,
            'parser' : parser,
            'downloader' : downloader,
            'json_loc' : json_save_location,
            'log_loc' : log_save_location,
            'pic_loc' : pic_save_location
        }
        for keyword in kwargs:
            logger.debug("%s : %s", keyword, kwargs[keyword])

    if config_mode is True and config.keys_from_args is False:
        twitter_media_downloader(*config.auth_keys, **payload)
    elif config.keys_from_args is True or config_mode is False:
        twitter_media_downloader(*kwargs['auth_keys'], **payload)

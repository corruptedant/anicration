# -*- coding: utf-8 -*-
"""
Provides a whole list of functions for (currently) Twitter related seiyuu data/media works.
Uses a config file(defaults to %appdata%/anicration/config.txt) which most functions needs.
config_create() creates a config file(you may provide a location) at affromentioned location.\n
twitter_media_downloader() does the bulk of downloading photo/video of accounts with the added
benefit of allowing one to customize their inputs if they know Python.\n
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
            _v_print('Folder', file_location, 'already exists.', verbosity=1, level=logger.info)
        else:
            _v_print('Folder', file_location, 'created.', verbosity=1, level=logger.info)
    #__file__ is the file of the function installed, '.' means the location of __main__
    if os.path.exists(os.path.join(file_location, file_name)):
        print('A pre-existing file found. Overwrite? (Y/N) ', end='')
        ans = input()
        if ans.strip().lower() in ['yes', 'y', 'ya', 'yeah']:
            pass
        else:
            sys.exit(0)
    with open(BASE_CONFIG_PATH, 'r', encoding='utf-8') as f:
        with open(os.path.join(file_location, file_name), 'w', encoding='utf-8') as f2:
            f2.write(f.read())

def _tweepy_retry(function=None, msg='', max_retry=3):
    retry = 1
    exc = RuntimeError
    while retry != max_retry + 1:
        try:
            if function is not None:
                return function()
        except tweepy.TweepError as err:
            exc = err
            _v_print(
                '{} failed ({}/{}), retrying in {}s : {}'.format(
                    msg, retry, max_retry, (retry - 1)*5, err.reason
                ),
                verbosity=0, level=logger.debug, end='\r'
            )
            logger.exception(err)
            sleep((retry-1)*5)
            retry = retry + 1
        else:
            _v_print('', verbosity=3, level=None, end='\r')
    _v_print(
        'Maximum retry exceeded, stopping program...                      ',
        verbosity=1, logger=None)
    logger.critical(
        'Maximum retry at %s with message %s, stopping program.', str(function), msg
        )
    sys.exit(exc)

def _tweepy_init(auth_keys):
    # Tweepy authentication and initiation
    try:
        auth = tweepy.OAuthHandler(auth_keys[0], auth_keys[1])
        auth.set_access_token(auth_keys[2], auth_keys[3])
    except IndexError as err:
        print('INDEXERROR : Did you miss a comma in your authentication keys?')
        logger.exception('Incomplete auth_keys \n%s', err)
        sys.exit('Error can be found in log file.')

    return _tweepy_retry(
        function=lambda: tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True),
        msg='Tweepy initiation'
    )

def _get_json(api, twitter_id: str, items: int):
    def _get_cursor():
        return tweepy.Cursor(api.user_timeline, id=twitter_id, tweet_mode='extended')
    def _get_status():
        json_data = list()
        json_num = int()
        for (idx, status) in enumerate(_get_cursor().items(items)):
            json_data.append(status._json)
            _v_print(
                'Retrived', str(idx + 1), 'JSON responses.',
                verbosity=1, level=None, end='\r'
            )
            json_num = idx + 1
        return json_data, json_num
    json_data, json_num = _tweepy_retry(_get_status, 'JSON retrieving')
    _v_print('', verbosity=1, level=None, end='\r')
    logger.info('Retrived ' + str(json_num) + ' JSON responses')
    return json_data

def twitter_media_downloader(**kwargs):
    """Downloads twitter media from an account. All variables are pass in kwargs. Refer to wiki."""
    # BIG TODO : either this be a handler or be expliciting a downloader
    # for example, it should not check if folders exists or not, that should be the job of another batch of code
    # pic loc, all the loc are quite redundant in a sense; something could be done about these
    # -j, -l and -m should work better here
    # instead of passing 'json_save', 'parser' and '
    
    # Initialize Tweepy
    try:
        api = _tweepy_init(kwargs['auth_keys'])
    except KeyError:
        # TODO : check if this is redundant, program should crash before it reaches here if authentication keys is missing
        _v_print('Authentication keys is missing.', 0, logger.critical)
        raise

    # Set some global variables
    items = kwargs.pop('items', 0)
    json_save = kwargs.pop('json_save', True)
    twitter_id = kwargs['twitter_id']
    # Defaults to twitter_id(without the '@')
    file_name = twitter_id[1:].lower()
    date_ext = "-{:%y%m%d%H%M%S}".format(datetime.now())
    _v_print('Twitter id:', twitter_id)

    # Check the folders/locations
    kwargs['pic_loc'] = kwargs.pop('pic_loc', None)
    subfolder_create = True if kwargs['pic_loc'] == '' or kwargs['pic_loc']  is None else False
    
    if kwargs['location'] is None :
        json_loc = _folder_check_empty(kwargs.pop('json_loc', None), 'Downloader', 'json')
        log_loc = _folder_check_empty(kwargs.pop('log_loc', None), 'Downloader', 'log')
        # this is the master folder. more folders is created to sort by person
        pic_loc = _folder_check_empty(kwargs['pic_loc'], 'Downloader', 'pictures')
        # pic_path is the folder the the pic will be stored in, psuedomeaning == final loc
        if subfolder_create is True:
            pic_path = os.path.join(pic_loc, file_name)
        else:
            pic_path = pic_loc
        _v_print('Picture directory : ' + pic_path)

    # TODO : Check if any code still uses kwargs['date']
    date = kwargs.pop('date', False)
    #sets the path depending if kwargs['location'] is given or not
    if kwargs['location'] is not None:
        json_path = os.path.join(kwargs['location'], file_name) + '.json'
    else:
        json_path = os.path.join(json_loc, file_name) + (date_ext if date is True else '') + '.json'
    json_data = _get_json(api, twitter_id, items)

    if json_save is True:
        with open(json_path, 'w', encoding="utf-8") as file:
            _v_print('Storing json file at ' + json_path, verbosity=2)
            file.write(json.dumps(json_data, sort_keys=True, indent=4, ensure_ascii=False))

    if kwargs.pop('json_only', False) is True:
        sys.exit('complete')

    log_path = os.path.join(
        log_loc, (file_name +  (date_ext if date is True else '') + '.txt')
    )
    if kwargs['parser'][0] is True:
        media_links = media_parser(json_data, log_path, kwargs['parser'][1])
        if kwargs['downloader'] is True:
            pic_downloader(media_links, pic_path)
    elif kwargs['parser'][0] is False and kwargs['downloader'] is True:
        media_links = media_parser(json_data, log_path, kwargs['parser'][1])
        pic_downloader(media_links, pic_path)
    _v_print('', verbosity=1, level=None)

# One may call this and give it their own custom_config_path and **kwargs as well
def seiyuu_twitter(custom_config_path=None, **kwargs):
    """Initated when `$anicration` is called without arguments."""
    config = ConfigHandler(custom_config_path)
    if config.log is True and kwargs['create_config'] is True:
        logging.basicConfig(filename='seiyuu_twitter.txt', level=logging.INFO)
        print('A log file will be created at ', os.path.join(os.getcwd(), 'seiyuu_twitter.txt'))
        logging.info("{:%Y/%m/%d %H:%M:%S}".format(datetime.now()))
    _set_verbosity(0 if config.verbosity == 0 else config.verbosity - 1)
    twitter_id_loc = config.twitter_id_loc
    # Run through set keyword arguments and set it to None if KeyError
    for kw in ('items', 'parser', 'downloader', 'json_loc', 'log_loc', 'pic_loc'):
        try:
            kwargs[kw]
        except KeyError:
            kwargs[kw] = None
    for kw in twitter_id_loc:
        data_loc = None
        if config.data_in_pic_loc is True:
            data_loc = os.path.join(
                twitter_id_loc[kw] if twitter_id_loc[kw] is not None else '', 'data'
            )
        payload = {
            'auth_keys': kwargs['auth_keys'] if kwargs['auth_keys'] is not None else config.auth_keys,
            'twitter_id' : kw,      #keyword is the username
            'items' : config.items if kwargs['items'] is None else kwargs['items'],
            'parser' : (config.parser, True) if kwargs['parser'] is None else kwargs['parser'],
            'downloader' : config.downloader if kwargs['downloader'] is None else kwargs['downloader'],
            'pic_loc' : twitter_id_loc[kw] if kwargs['pic_loc'] is None else kwargs['pic_loc'],
            'date' : True
        }
        # Checking locations for -a mode
        if kwargs['json_loc'] is None:
            payload['json_loc'] = config.json_loc if data_loc is None else data_loc
        else:
            payload['json_loc'] = kwargs['json_loc']
        if kwargs['log_loc'] is None:
            payload['log_loc'] = config.log_loc if data_loc is None else data_loc
        else:
            payload['log_loc'] = kwargs['log_loc']
        try:
            twitter_media_downloader(**payload)
        except KeyboardInterrupt:
            print('\nERROR : User interrupted the program.')
            sys.exit(1)
    print('\nComplete')

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

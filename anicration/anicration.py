# -*- coding: utf-8 -*-
"""
Handles command-line argument and parsing the data to functions.\n
Documentation of the arguments can be found in the wiki of the github page.
"""
import os
import sys
import logging
import argparse
import re

from .auxiliaryfuncs import _v_print, _set_verbosity
from .seiyuuhandler import seiyuu_twitter, twitter_media_downloader, config_create
from .confighandler import ConfigHandler

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
INFO = logger.info
DEBUG = logger.debug
WARNING = logger.warning
CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'config', 'example.txt')
TWITTER_USERNAMES = ['@anju_inami', '@Rikako_Aida', '@aikyan_', '@furihata_ai', '@suwananaka',
                     '@aina_suzuki723', '@kanako_tktk', '@saito_shuka', '@box_komiyaarisa']

def argument_create():
    """Loads all the commands arguments"""
    parser = argparse.ArgumentParser(
        description='Handles Twitter-related seiyuu media/info stuffs.')

    section = parser.add_mutually_exclusive_group()
    section.add_argument(
        '-t', '--twitter',
        action='store_true', default=None, help='Twitter mode.')
    section.add_argument(
        '-i', '--instagram',
        action='store_true', default=None, help='Instagram mode. To Be Implemented')
    section.add_argument(
        '-b', '--blog',
        action='store_true', default=None, help='Blog mode. To Be Implemented')

    store_type = parser.add_mutually_exclusive_group()
    store_type.add_argument(
        '-d', '--downloader',
        action='store_true', help='Stores the file in a folder at current directory')
    store_type.add_argument(
        '-cf', '--current',
        action='store_true', help='Stores all files in current directory')
    store_type.add_argument(
        '-D', '--data',
        action='store_true', help='Stores pic in currdir, and data in .//data')

    verbosity = parser.add_mutually_exclusive_group()
    verbosity.add_argument(
        '-v', '--verbose',
        action="count", default=0, help="Increase verbosity level. Not Yet Implemented")
    verbosity.add_argument(
        '-q', '--quiet',
        action="store_true", default=False,
        help="Just keep it down low, everything. Not Yet Implemneted")

    download = parser.add_mutually_exclusive_group()
    download.add_argument(
        '-j', '--json',
        dest='json_only', action='store_true',
        help='Download JSON responses only.')
    download.add_argument(
        '-l', '--links',
        dest='link_only', action='store_true',
        help='Download Twitter media links only, discard JSON responses.')
    download.add_argument(
        '-m', '--media',
        dest='media_only', action='store_true',
        help='Download pictures, discard JSON and links')

    parser.add_argument(
        '-c', '--config',
        type=str, nargs='?', const=None, default=0, metavar='loc',
        help='Config mode. May provide a custom location. Otherwise defaults to appdata')
    parser.add_argument(
        '-I', '--items',
        type=int, default=None, metavar='int',
        help='How much JSON responses to go through. Defaults to 0(all of available status)')

    parser.add_argument(
        "website",
        nargs='?', type=str, help="the web address of the profile page")
    parser.add_argument(
        "location",
        nargs='*', type=str, help="where to save the file(default : current directory)")
    return parser.parse_args()

def _link_parser(link):
    if 'twitter' in link:
        for j in range(len(link)-1, 0, -1):
            if link[j] == '/':
                return link[abs(j) + 1:]
    else:
        return None

def _regex_twitname(args):
    for username in TWITTER_USERNAMES:
        regrex = r'^([@]?)' + re.escape(args.website)
        args.twitter = True
        if re.search(regrex, username, re.IGNORECASE):
            _v_print('Twitter username found, engaging twitter mode.', verbosity=1)
            if username[0] != '@':
                twitter_id = '@' + username
                logger.info('twitter_id : ' + twitter_id)
            else:
                twitter_id = username
                logger.info('twitter_id : ' + twitter_id)
            return username

def _files_to_save(args, payload):
    if args.json_only:
        payload['json_save'] = True
        payload['parser'] = (False, False)
        payload['downloader'] = False
    elif args.link_only:
        payload['json_save'] = False
        payload['parser'] = (True, True)
        payload['downloader'] = False
    elif args.media_only:
        payload['json_save'] = False
        payload['parser'] = (True, False)
        payload['downloader'] = True
    elif args.config is None:
        pass
    else:
        payload['json_save'] = True
        payload['parser'] = (True, True)
        payload['downloader'] = True
    return payload

def _get_mode(args, payload, config):
    if args.twitter:
        payload['auth_keys'] = config.auth_keys
        if args.verbose >= 2:
            _print_payload(payload)
        try:
            twitter_media_downloader(**payload)
        except KeyboardInterrupt:
            print('\nERROR : User interrupted the program')
            sys.exit(1)
        else:
            print('Complete')
            sys.exit(0)
    elif args.instagram:
        print("Instagram mode...")
    elif args.blog:
        print("Blog mode...")

def _print_payload(payload):
    """Prints payload dict() for debug purposes."""
    for keyword in payload:
        print(keyword, ":", payload[keyword])

def args_handler(args):
    """Handle parsed arguments"""
    payload = dict()

    # quick and dirty silent mode
    if args.quiet:
        sys.stdout = open(os.devnull, 'a')
    elif args.verbose >= 2:
        _v_print('Debug mode...')
        cmdl_out = logging.StreamHandler()
        cmdl_out.setLevel(logging.DEBUG)
        fmt = logging.Formatter('%(message)s')
        cmdl_out.setFormatter(fmt)
        logger.addHandler(cmdl_out)

    # ConfigHandler() crashes if it doesn't find a file, so this come first.
    if args.config == 'create':
        _v_print('Creating config...', verbosity=1)
        config_create()
        _v_print('Config created.', verbosity=0)
        sys.exit(0)

    config_mode = False
    config = ConfigHandler()
    def _loc_set(var=None):
        """Set the 3 locations variables to the value given."""
        for name in ('json_loc', 'log_loc', 'pic_loc'):
            payload[name] = var

    # 0 is when -c is not even called.
    if args.config is not 0:
        config = ConfigHandler(args.config)
        _v_print('Config Mode, auto-enabling Twitter mode.', verbosity=1)
        args.twitter = True
        config_mode = True
        payload = {
            'keys_from_args' : config.keys_from_args,
            'auth_keys': config.auth_keys,
            'twitter_id' : config.twitter_usernames[0],
            'items' : config.items,
            'parser' : (config.parser, True),
            'downloader' : config.downloader,
            'json_loc' : config.json_loc,
            'log_loc' : config.log_loc,
            'pic_loc' : config.pic_loc,
            'date' : True
        }

    # when a website value is not provided, access twitter_usernames.
    if not args.website is None:
        payload['twitter_id'] = _regex_twitname(args)
        if 'twitter' in args.website:
            payload['twitter_id'] = '@' + _link_parser(args.website)
            args.twitter = True
    elif config_mode is True:
        # maybe another way to handle, but this is the way I'll go for now
        _v_print(
            'No website link is provided, defaulting to twitter_usernames in config.',
            verbosity=1)

    # in case of a non-default --items integer is given
    if not args.items is None:
        payload['items'] = args.items
    elif args.items is None and config_mode is True:
        payload['items'] = 0
    else:
        pass

    # for the x_only and config default override avoidance.
    payload = _files_to_save(args, payload)

    def _store_type(args, prefix=''):
        if args.downloader:
            _loc_set()
            _v_print('Storing all files in', os.path.join(prefix, 'Downloader'))
        elif args.data:
            _loc_set(os.path.join(prefix, 'data'))
            payload['pic_loc'] = prefix
        elif args.current:
            _loc_set(os.getcwd())
            _v_print('Storing all files in ', os.getcwd())

    if args.location:
        _store_type(args, ' '.join(args.location))
    else:
        _store_type(args, os.getcwd())

    # temporary
    payload['website'] = args.website
    payload['location'] = args.location
    payload['config'] = args.config

    # triggers
    _get_mode(args, payload, config)
    return payload

def main():
    """Does the magic of command-line calling."""
    # Get all the varaibles
    args = argument_create()
    # Set verbosity level
    _set_verbosity(args.verbose)
    # Handle all the variables
    if not len(sys.argv) > 1:
        _v_print('Defaulting to seiyuu_twitter()...', level=None)
        seiyuu_twitter()
    else:
        logging.basicConfig(filename='anicration.txt', level=logging.INFO)
        logging.info('Engaging argument mode...')
        _print_payload(args_handler(args))

if __name__ == "__main__":
    main()

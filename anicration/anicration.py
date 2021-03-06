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
from .downloader import _requests_save, _file_parser, _media_request, _get_media_name, _folder_check_empty
import anicration.downloader as downloader

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
        '-a', '--anicration',
        action='store_true', default=None, help='Anicration mode.')
    section.add_argument(
        '-t', '--twitter',
        action='store_true', default=None, help='Twitter mode.')
    #section.add_argument(
    #    '-i', '--instagram',
    #    action='store_true', default=None, help='Instagram mode. To Be Implemented')
    #section.add_argument(
    #    '-b', '--blog',
    #    action='store_true', default=None, help='Blog mode. To Be Implemented')
    section.add_argument(
        '-T', '--textfile',
        action='store_true', default=None,
        help='Text file mode. Seperate links by new line in the file.')

    store_type = parser.add_mutually_exclusive_group()
    store_type.add_argument(
        '-dm', '--downloader',
        action='store_true', help='Stores the file in a folder at current directory')
    store_type.add_argument(
        '-cf', '--current',
        action='store_true', help='Stores all files in current directory')
    # TODO : deprecate -d, consider deprecate -cf as it will be the default setup
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
        help='How much JSON responses to go through. Defaults to 0(no limit/all)')
    parser.add_argument(
        '-dc', '--data_check',
        action='store_true', default=None, help='[Textfile mode] save the file with (n) appended if file is not the same data.')
    parser.add_argument(
        '-o', '--output',
        type=str, nargs='?', const=None, default=None, metavar='loc',
        help="where to save the file(default : current directory)")

    parser.add_argument(
        "website",
        nargs='?', type=str, help="the web address of the profile page")
    
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
    # TODO : cf as default, downloader mode only when -df is evoked
    # TODO : default to only media files to os.getcwd() if no download mode is called
    if args.json_only:
        _v_print('JSON only.')
        # TODO : more linear excecution;program still checks to create folder despite state of run
        # program should also always dump to current directory, 
        payload['json_only'] = True
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
        print('Twitter mode...')
        payload['auth_keys'] = config.auth_keys
        if args.verbose >= 2:
            _print_payload(payload)
        try:
            if args.website is None and len(config.twitter_usernames) != 1:
                for username in config.twitter_usernames:
                    payload['twitter_id'] = username
                    twitter_media_downloader(**payload)
            else:
                twitter_media_downloader(**payload)
        except KeyboardInterrupt:
            print('\nERROR : User interrupted the program')
            sys.exit(1)
        else:
            print('Complete')
    elif args.instagram:
        print("Instagram mode...")
    elif args.blog:
        print("Blog mode...")
    elif args.textfile:
        print('Textfile mode...')
        if args.website is None:
            raise TypeError('ERROR : No textfile location provided, exiting program...')
        else:
            txtf_name = args.website
            print(txtf_name)
            try:
                textfile_handler(
                    txtf_name, save_location=' '.join(payload['location']), override=config.override
                )
            except FileNotFoundError as err:
                sys.exit('File does not exist, exiting program : ' + err)
            except KeyboardInterrupt:
                sys.exit('ERROR : User interrupted the program.')
            else:
                print('\nComplete')
    elif args.anicration:
        print('Anicration mode...')
        if args.website:
            print('ERROR : ', args.website, ' is provided on Anicration mode.')
        payload = dict()
        payload['create_config'] = False
        if args.items:
            payload['items'] = args.items
        payload = _files_to_save(args, payload)
        payload = _store_type(args, payload, os.getcwd())
        if args.verbose >= 2:
            _print_payload(payload)
        seiyuu_twitter(None, **payload)

def textfile_handler(file, **kwargs):
    #parse the links
    with open(file, 'r', encoding='utf-8') as txt_f:
        links = _file_parser(txt_f)
        save_loc = _folder_check_empty(
            kwargs.pop('save_location', None), 'Anicration', 'Pics', True
        )
        length = len(links)
        for (idx, link) in enumerate(links):
            percent = downloader._percent_former((idx+1), length)
            name = _get_media_name(link)
            if os.path.exists(os.path.join(save_loc, name)) and kwargs['override'] is True:
                with open(os.path.join(save_loc, name), 'r+b') as pic_f:
                    res = _media_request(link)
                    if res.content == pic_f.read():
                        message = 'File ' + name + ' already exists.'
                        downloader._status_print(message, percent, save_loc)
                    else:
                        i = 1
                        file_name, fext = os.path.splitext(name)
                        file_path = os.path.join(save_loc, file_name + '({})'.format(str(i)) + fext)
                        while os.path.exists(file_path):
                            i = i+1
                            file_path = os.path.join(save_loc, file_name + '({})'.format(str(i)) + fext)
                        else:
                            with open(file_path, 'wb') as new_f:
                                new_f.write(res.content)
            elif os.path.exists(os.path.join(save_loc, name)) and kwargs['override'] is False:
                message = 'File with the name' + name + ' already exists.'
                downloader._status_print(message, percent, save_loc)
            else:
                message = 'Downloading : ' + link[-20:]
                downloader._status_print(message, percent, save_loc)
                res = _media_request(link)
                _requests_save(res, os.path.join(save_loc, name))

def _print_payload(payload):
    """Prints payload dict() for debug purposes."""
    for keyword in payload:
        _v_print(keyword, ":", payload[keyword], verbosity=1, level=None)

def _store_type(args, payload, prefix=''):
    def _loc_set(var=None):
        """Set the 3 locations variables to the value given."""
        for name in ('json_loc', 'log_loc', 'pic_loc'):
            payload[name] = var
    if args.downloader:
        _loc_set()
        _v_print('Storing all files in', os.path.join(prefix, 'Downloader'))
    elif args.data:
        _loc_set(os.path.join(prefix, 'data'))
        payload['pic_loc'] = prefix
        _v_print('Storing all data files in ', os.path.join(prefix, 'Data'))
    elif args.current:
        _loc_set(os.getcwd())
        _v_print('Storing all files in ', os.getcwd())
    return payload

def args_handler(args):
    """Handle parsed arguments"""
    #============================#
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
        config_create()
        _v_print('Config created.', verbosity=0)
        sys.exit(0)

    config_mode = False
    config = ConfigHandler()

    # 0 is when -c is not even called.
    if args.config is not 0:
        config = ConfigHandler(args.config)
        _v_print('Config Mode.', verbosity=1)
        args.twitter = True
        config_mode = True
        payload = {
            'auth_keys': config.auth_keys,
            'twitter_id' : config.twitter_usernames[0],
            'items' : config.items,
            'parser' : (config.parser, True),
            'downloader' : config.downloader,
            'json_loc' : config.json_loc,
            'log_loc' : config.log_loc,
            'pic_loc' : config.pic_loc,
            'date' : True # TODO : ok wtf date is always true
        }

    # when a website value is not provided, access twitter_usernames.
    if args.website is not None:
        # Checks if clashing mode exists
        if args.anicration:
            _v_print(
                'ERROR : Anicration mode doesn\'t accept website/account.',
                verbosity=0, level=logging.ERROR
            )
            sys.exit(1)
        # Temporary implementation since Instagram uses the same prefix for usernames['@']
        payload['twitter_id'] = _regex_twitname(args)
        if 'twitter.com/' in args.website:
            payload['twitter_id'] = '@' + _link_parser(args.website)
            args.twitter = True
        elif '@' in args.website:
            payload['twitter_id'] = args.website
            args.twitter = True
    elif config_mode is True:
        # maybe another way to handle, but this is the way I'll go for now
        _v_print(
            'No website link is provided, defaulting to twitter_usernames in config.',
            verbosity=1)

    # in case of a non-default --items integer is given
    if not args.items is None:
        payload['items'] = args.items
    elif args.items is None and config_mode is False:
        payload['items'] = 0
    else:
        pass

    # for the x_only and config default override avoidance.
    payload = _files_to_save(args, payload)

    if args.output:
        payload = _store_type(args, payload, ' '.join(args.output))
    else:
        payload = _store_type(args, payload, os.getcwd())

    # temporary
    payload['website'] = args.website
    payload['location'] = args.output
    payload['config'] = args.config

    #triggers
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
        # TODO : seiyuu_twitter DOESN'T CALL custom_config_path
        seiyuu_twitter()
    else:
        #_v_print('A log file will be created at', os.getcwd(), verbosity=1, level=None)
        #logging.basicConfig(filename='anicration.txt', level=logging.INFO)
        args_handler(args)

if __name__ == "__main__":
    main()

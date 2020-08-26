# -*- coding: utf-8 -*-
"""
This modules parse for media links from Twitter's JSON
responses which is obtained from Tweepy's \\_json data.
QuoteParser has extra features as well, it's *for api purposes*.
"""
import json
import logging

from .auxiliaryfuncs import _v_print

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class QuoteParser():
    """Simplifies the need for quoted data."""
    def __init__(self, status, https=True, silent_ignore=True):
        self._https = https
        self._truncated = status['truncated']
        self._silent = silent_ignore
        self.status = status
        self.created_at = self.quoted_status['created_at']

    @property
    def quoted_status(self):
        """Contains all data related to the quoted status itself"""
        try:
            return self.status['quoted_status']
        except KeyError:
            if self._silent is True:
                return None
            else:
                raise

    @property
    def text(self):
        """Dependent on truncation"""
        if self._truncated is True:
            return self.quoted_status['text']
        else:
            return self.quoted_status['full_text']

    @property
    def extended_entities(self):
        """Returns `None` if truncated is `True`"""
        if self._truncated is True:
            return None
        else:
            return self.quoted_status['extended_entities']

    @property
    def media_links(self, https=True):
        """Returns `list` of links. Returns `None` if not truncated"""
        if self._truncated is False:
            return _ext_ett_handler(self.extended_entities, https)
        elif self._truncated is True:
            return None

def _compare_bitrate_data(variants: list):
    """Takes in `variants` of the `Tweet`. Returns a `list` of the link with highest bitrate."""
    bitrate = dict()
    for (idx, variants_obj) in enumerate(variants):
        try:
            bitrate[str(idx)] = variants_obj['bitrate']
        except KeyError:
            _v_print(
                'video_handler() -- KeyError at %s', str(idx),
                verbosity=2, level=logger.debug
            )
            continue
    return [variants[int(max(bitrate, key=lambda key: bitrate[key]))]['url']]

def _photo_handler(medias: dict, https: bool):
    """Return a `list` of the parsed https photo links."""
    links = list()
    for media in medias:
        if https:
            links.append(media['media_url_https'])
        else:
            links.append(media['media_url'])
    return links

def _video_handler(medias: list):
    """Accepts a list of media parsed dict. Returns `list` of link(s)."""
    variants = medias[0]['video_info']['variants']
    return _compare_bitrate_data(variants)

def _ext_ett_handler(ext_ett: dict, https: bool):
    """Stands for `extended_entity_handler()`. Accepts only `extended_entities` objects."""
    try:
        media_type = ext_ett['media'][0]['type']
        if media_type == 'photo':
            return _photo_handler(ext_ett['media'], https)
        elif media_type == 'video':
            return _video_handler(ext_ett['media'])
    except TypeError:
        print('TypeError excepted: ' + ext_ett)

def get_quoted_data(status, https=True, silent_ignore=True):
    """Returns `QuoteParser` object.\n
    Return `None` if empty or no quoted status(if silent_ignore is True)"""
    try:
        if status['is_quote_status'] is True:
            return QuoteParser(status, https)
        else:
            return None
    except KeyError:
        if silent_ignore:
            return None
        else:
            raise

def get_video_thumbnail(status, https=True):
    """Obtains video thumbnail of a status. Return `None` if not a video status or empty status."""
    try:
        if status['extended_entities']['media'][0]['type'] != 'video':
            return None
        else:
            if https:
                return status['extended_entities']['media'][0]['media_url_https']
            else:
                return status['extended_entities']['media'][0]['media_url']
    except KeyError:
        #_v_print()
        logger.exception('get_video_thumnail(): KeyError excepted')
        return None

def get_media_link(status, https=True):
    """Return a `list` of media link from a single status(photo or video).\n
    Receives a parsed `status` JSON data. Does handle `str` status, but no guarantee.\n
    If `https` is `True`, then obtains the https version of the photo.\n"""
    try:
        media_links = _ext_ett_handler(status['extended_entities'], https)
    except (ValueError, KeyError):
        _v_print('Error : get_media_link() ValueError or KeyError detected -- ')
    except TypeError:
        _v_print('WARNING : Did you pass in a non-json parsed string?', verbosity=0, level=None)
        logger.exception('get_media_link() TypeError.')
        try:
            media_links = _ext_ett_handler(json.loads(status)['extended_entities'], https)
        except json.JSONDecodeError:
            _v_print('Invalid JSON.', verbosity=0, level=logger.exception)
            raise
        return media_links
    else:
        return media_links
    return None

def media_parser(json_data, log_path: str, log_create=True, no_rt=True):
    """json_data needs to be a string(file.read()). The script will do the loading.
    Only reads a compiled Twitter API responses status arranged in a list : [{},{},{}]"""
    try:
        tweets = json.loads(json_data)
    except TypeError:
        _v_print('test - json not a str, passing as-is', 2)
        tweets = json_data

    try:
        tweets[0]
    except KeyError:
        _v_print('Invalid Tweet JSON data, exiting program...', verbosity=0, level=logger.exception)
        raise

    media_links = list()
    for (idx, tweet) in enumerate(tweets):
        if tweet['is_quote_status'] is True:
            continue
        try:
            tweet['retweeted_status']
        except KeyError:
            pass
        else:
            if no_rt is True:
                continue
        try:
            media_links.extend(_ext_ett_handler(tweet['extended_entities'], True))
        except KeyError:
            logger.debug("No media at status number %d", idx)
        except TypeError:
            #print('TEST -- TypeError excepted at media_parser() at {}'.format(idx))
            pass

    if log_create is True:
        with open(log_path, 'w', encoding="utf-8") as file:
            for link in media_links:
                logger.debug('Logged %s into %s', link, log_path)
                file.write(link + '\n')

    return media_links

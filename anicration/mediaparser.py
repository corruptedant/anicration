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
                verbosity=2, level=logging.debug
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
    # TODO : Should I let the programmer do their own try:.. except: block?
    try:
        # checks if the media actually have content
        medias = ext_ett['media']
    except KeyError:
        logger.exception('entity_handler -- Empty Object Given')
        print('WARNING: entity_handler -- Empty Object Given')
        return None

    try:
        # for now it only checks if the first one is a photo or video
        media_type = medias[0]['type']
    except KeyError:
        logging.warning('entity_handler -- no "type" attribute')
        #print('Error : entity_handler -- no "type" attribute') TODO -- Verbose mode
        return None
    else:
        # determine the type and send to their respective handlers
        if media_type == 'photo':
            return _photo_handler(medias, https)
        elif media_type == 'video':
            return _video_handler(medias)
    return None

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
    """Obtains a video thumbnail of a status.\n Return `None` if empty status"""
    try:
        if https:
            return status['extended_entities']['media_url_https']
        else:
            return status['extended_entities']['media_url']
    except KeyError:
        return None

def get_media_link(status, https=True, err=False):
    """Return a `list` of media link from a single status(photo or video).\n
    Receives a parsed `status` JSON data. Does handle `str` status, but no guarantee.\n
    If `https` is `True`, then obtains the https version of the photo.\n
    If `err` is `True`, it prints if an err is excepted"""
    try:
        media_links = _ext_ett_handler(status['extended_entities'], https)
    except (ValueError, KeyError):
        if err:
            print('Error : get_media_link() ValueError or KeyError detected -- ')
    except TypeError:
        # TODO : automatically load the JSON or raise an exception?
        print('WARNING : Did you pass in a non-json parsed string?')
        logger.exception('get_media_link() error.')
        media_links = _ext_ett_handler(json.loads(status)['extended_entities'], https)
        return media_links
    else:
        return media_links
    return None

def media_parser(json_data: str, log_path: str, log_create=True):
    """json_data needs to be a string(file.read()). The script will do the loading.
    Only reads a compiled Twitter API responses status arranged in a list : [{},{},{}]"""
    tweets = json.loads(json_data)

    try:
        tweets[0]
    except KeyError:
        _v_print('Invalid Tweet JSON data, exiting program...', verbosity=0, level=logger.exception)
        raise

    media_links = list()
    for (idx, tweet) in enumerate(tweets):
        try:
            media_links.extend(_ext_ett_handler(tweet['extended_entities'], True))
        except KeyError:
            logger.debug("No media at status number %d", idx)

    if log_create is True:
        with open(log_path, 'w', encoding="utf-8") as file:
            for link in media_links:
                logger.debug('Logged %s into %s', link, log_path)
                file.write(link + '\n')

    return media_links

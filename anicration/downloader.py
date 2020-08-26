# -*- coding: utf-8 -*-
"""
Handles the parsing of links for downloading.
Provides the necessary information to help with saving of files(names) and status report.
"""
import os
import sys
import logging

from time import sleep

import requests

from .auxiliaryfuncs import _v_print

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

FILE_EXTENSIONS = ('.png', '.jpg', '.mp4')

def _folder_check_empty(folder_location, folder_name='Downloader', type_='pics', make_folder=True):
    """Allows one to create a default folder if input is empty.
    Returns `os.path.join(folder_name, type_)` if so.
    Returns folder_location plus the folder name if pic_folder is `True`
    Otherwise Returns the folder_location only"""
    if (folder_location == '' or folder_location is None) and make_folder is True:
        folder_path = os.path.join(folder_name, str(type_))
        logger.info('No '+ str(type_)
                    + ' folder location specified. Defaulting to '
                    + os.path.join(folder_name, str(type_)))
        _v_print('No', str(type_), 'folder location specified.', verbosity=2, level=None)
        if os.path.exists(folder_path):
            return os.path.join(folder_path)
        else:
            try:
                os.makedirs(folder_path)
            except FileExistsError:
                _v_print('Folder already exist : ' + folder_path, verbosity=2)
            else:
                _v_print('Created folder ' + folder_path, verbosity=1)
                return os.path.join(folder_path)
    else:
        if not os.path.exists(folder_location):
            if make_folder is False:
                logger.error('Folder ' + folder_location + 'does not exist.')
                raise FileNotFoundError
            logger.info('Folder ' + folder_location + 'does not exist, making a folder.')
            try:
                os.makedirs(folder_location)
            except PermissionError:
                logger.critical('No permission to create folder at ' + folder_location)
                raise
            else:
                _v_print('Created folder ' + folder_location)
        return folder_location

def _percent_former(curr, leng):
    """Formats a more-consistent of percent and fraction list. Shows like :
    100.0% Completed [1/1]"""
    percent = (
        "{:{fill}{width}.1%} Completed".format(curr/leng, fill=0, width=len(str(leng)) + 3)
    )

    content = (
        "[{:{fill}{width}}/{length}]".format(curr, fill=0, width=len(str(leng)), length=leng)
    )
    return percent + ' ' + content

def _status_print(message, percent, save_location):
    """Prints the status on the downloading session."""
    print(percent, 
          ' : ' + save_location if save_location is not None else '', ':',
          message, '    ', end='\r')
    logger.info('%s %s', save_location, message)

def _requests_save(res_obj, file_save_path, override=False):
    """Saves a data to a location with open()"""
    if os.path.exists(file_save_path) and override is False:
        print('Path already exists. Skip saving the file.')
    else:
        with open(file_save_path, 'wb') as save_data:
            for chunk in res_obj.iter_content(100000):
                save_data.write(chunk)

def _file_parser(file_obj):
    """Turn a list seperated by newline into a list with only links"""
    #logger.debug('_file_parser() called') # -- due to inconsistencies
    parsed_list = list()
    for line in file_obj:
        if line.strip().startswith('#') or not line.strip().endswith(FILE_EXTENSIONS):
            logger.info('File parser : skipping %s', line.strip())
            print('Skipping', line.strip())
        else:
            parsed_list.append(line.strip())
    return parsed_list

def _get_media_name(link):
    """Find the first slash from last. Returns anything AFTER the found slash."""
    for j in range(len(link)-1, 0, -1):
        if link[j] == '/':
            return link[abs(j) + 1:]

def _media_request(link):
    """Requests links, handle HTTPError or ConnectionError up to 3 retries"""
    retry = 1
    while retry != 3:
        try:
            media_res = requests.get(link)
            media_res.raise_for_status()
        except (requests.ConnectionError, requests.HTTPError, requests.ConnectTimeout) as err:
            print('Download failed. Retrying ({}/3) in {} seconds : {}'.format(retry, retry*5, err), end='\r')
            sleep(retry*5)
            retry = retry + 1
        else:
            return media_res
    print('Maximum retry exceeded, exiting program...')
    sys.exit(1)

def _media_download(twimg_list, save_location):
    """Downloads photo/video from the twimg list compiled."""
    length = len(twimg_list)
    # obtains the name of the media(by searching backwards until it hits a '/')
    for (idx, media) in enumerate(twimg_list):
        percent = _percent_former((idx+1), length)
        media_name = _get_media_name(media)

        if os.path.exists(os.path.join(save_location, media_name)):
            message = 'File ' + media_name + ' already exists.'
            _status_print(message, percent, None)
        elif not media.lower().endswith(FILE_EXTENSIONS):
            message = 'Invalid media link ' + media + ' detected : skipping'
            _status_print(message, percent, None)
        else:
            if media.lower().endswith('.jpg'):
                _status_print('Downloading ' + media_name, percent, None)
                # only .jpg have different sizes (:large, :small)
                media_link = media + ':orig'
            elif media.lower().endswith(('.png', '.mp4')):
                _status_print('Downloading ' + media_name, percent, None)
                media_link = media

            media_res = _media_request(media_link)
            _requests_save(media_res, os.path.join(save_location, media_name))

def pic_downloader(twimg_list: list, save_location=None):
    """Checks if the folder is empty before initiating download."""
    _folder_check_empty(save_location)
    _media_download(twimg_list, save_location)

def parser_downloader(file, save_location=None):
    """File refers to the the file that contains the links."""
    with open(file, 'r', encoding='utf-8') as link_file:
        links_list = _file_parser(link_file)
    for (idx, link) in enumerate(links_list):
        links_list[idx] = link.strip()
    _folder_check_empty(save_location)
    _media_download(links_list, save_location)
    # TODO : I think "Completed" overwrites and looks funny, fix it by clearing 1 line
    _v_print('\nCompleted')

# -*- coding: utf-8 -*-
"""
Handles the parsing of links for downloading.
Provides the necessary information to help with saving of files(names) and status report.
"""
import os
import logging
import requests

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(levelname)s:%(name)s:%(asctime)s:%(message)s')

# You may add more types for the system to pick it up and download it
FILE_EXTENSIONS = ('.png', '.jpg', '.mp4')

def _folder_check_empty(folder_location, folder_name='Downloader', type_='pics', make_folder=True):
    """Allows one to create a default folder if input is empty.
    Returns `os.path.join(folder_name, type_)` if so.
    Returns folder_location plus the folder name if pic_folder is `True`
    Otherwise Returns the folder_location only"""
    if folder_location == '' or folder_location is None and make_folder is True:
        folder_path = os.path.join(folder_name, str(type_))
        logger.info('No '+ str(type_)
                    + ' folder location specified. Defaulting to '
                    + os.path.join(folder_name, str(type_)))
        print('No', str(type_), 'folder location specified.')
        if os.path.exists(folder_path):
            return os.path.join(folder_path)
        else:
            try:
                os.makedirs(folder_path)
            except FileExistsError:
                logger.info('Folder already exist : ' + folder_path)
            else:
                print('Folder', type_, 'created')
                logger.info('Created folder ' + folder_path)
                return os.path.join(folder_path)
    else:
        if not os.path.exists(folder_location):
            logger.info('Folder ' + folder_location + 'does not exist, making a folder.')
            try:
                os.makedirs(folder_location)
            except PermissionError:
                logger.critical('No permission to create folder at ' + folder_location)
                raise
            else:
                print('Folder', type_, 'created')
                logger.info('Created folder ' + folder_location)
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
    return percent + ' ' + content + ' :'

def _status_print(message, percent, save_location):
    """Prints the status on the downloading session."""
    print(percent, save_location, ':',
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
    """Turn a list seperated by EOL into a list with only links"""
    logger.debug('_file_parser() called')
    parsed_list = list()
    for line in file_obj:
        if line.strip().startswith('#') or not line.strip().endswith(FILE_EXTENSIONS):
            logger.info('File parser : skipping %s', line.strip())
            print('Skipping', line.strip())
        else:
            parsed_list.append(line)
    return parsed_list

def _get_media_name(link):
    """Find the first slash from last. Returns anything AFTER the found slash."""
    for j in range(len(link)-1, 0, -1):
        if link[j] == '/':
            return link[abs(j) + 1:]

# TODO : Break this function into even smaller functions
def _media_download(twimg_list, save_location, log_obj=None):
    """Downloads photo/video from the twimg list compiled. Logs given a file-like object"""
    length = len(twimg_list)
    # obtains the name of the media(by searching backwards until it hits a '/')
    for (idx, media) in enumerate(twimg_list):
        percent = _percent_former((idx+1), length)
        media_name = _get_media_name(media)

        if os.path.exists(os.path.join(save_location, media_name)):
            message = 'File ' + media_name + ' already exists.'
            _status_print(message, percent, save_location)
        elif not media.lower().endswith(FILE_EXTENSIONS):
            message = 'Invalid media link ' + media + ' detected : skipping'
            _status_print(message, percent, save_location)
        else:
            if media.lower().endswith('.jpg'):
                _status_print('Downloading ' + media_name, percent, save_location)
                # only .jpg have different sizes (:large, :small)
                media_res = requests.get(media + ':orig')
            elif media.lower().endswith(('.png', '.mp4')):
                _status_print('Downloading ' + media_name, percent, save_location)
                media_res = requests.get(media)

            try:
                media_res.raise_for_status()
            except (ConnectionError, requests.HTTPError) as err:
                logger.exception('Connection or HTTP Error %s', str(err))
                # TODO : Implement retrying
                print('Connection error or HTTP Error excepted. Skipping current file...')
            else:
                _requests_save(media_res, os.path.join(save_location, media_name))

        if not log_obj is None:
            log_obj.write(message + '\n')
    print('')

def pic_downloader(twimg_list: list, save_location=None):
    """Checks if the folder is empty before initiating download."""
    _folder_check_empty(save_location)
    _media_download(twimg_list, save_location)

def parser_downloader(file, save_location=None):
    """File refers to the the file that contains the links."""
    with open(file, 'r', encoding='utf-8') as f:
        links_list = _file_parser(f)
    for (idx, link) in enumerate(links_list):
        links_list[idx] = link.strip()
    _folder_check_empty(save_location)
    _media_download(links_list, save_location)
    print('Completed')
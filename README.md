# Anicration

Command line based Twitter media downloading with focus on Love Live Sunshine Voice Actors.

## Details

This module uses Twitter API to gain access to tweets and media links, which is extracted and downloaded in the highest quality(:orig/bitrate).
It also has a function that automatically update a series of Twitter account media. 
Config settings is available for tweaking of save location for affromentioned function. 
There's also another function that handles downloading Twitter account data on an hourly basis(for math and graph). 

## Development status

Since these scripts are still in development, not backwards compatible changes will be entertainted.

## Requirements

* Python 3.6 and above
* Twitter API Credentials (Authentication keys, Secret keys)

## Dependencies

* Tweepy
* requests

## Setup

You will be required to create a Twitter API credentials(https://apps.twitter.com/).  
You can create the required 4 keys by the name of consumer key, consumer secret, access token, access token secret.  
Then, do `$ anicration -c create` in command prompt. This will create a config file at `%appdata%/anicration/config.txt`.  
Open the config file with text editor of your choice, and fill in authentication keys in the affromentioned format, with comma seperating the values.  

With all that done, you now can use the command-line based functions(though you will need more tweaking for anicration mode).

`$ anicration @anju_inami -I 100 -cf` will find any pictures and videos from the most recent 100 Tweets of the Twitter account `@anju_inami`, storing it in the current directory(folder).

## Available Command-line Functions

* `anicration`
* `anicration [website] [location] [additional flags]`
* `track_twitter_info`

### Flags:

* `-I [int], --items`
* `-c [loc], --config`
* `-d, --downloader`
* `-cf, --current folder`
* `-D, --data`
* `-j, --json`
* `-l, --links`
* `-m, --media`
* `-v, --verbose`
* `-q, --quiet`

You may use `anicration --help` for more information regarding flags.

### anicration mode

By calling `$ anicration` without any additional values/flags, the script enters anicration mode.
This uses the config [Seiyuu Twitter], [Twitter Usernames] and [Pictures Saves Location].
You will need to configure a location for the files, and the usernames if the respective seiyuu changes their username,
and items(amount of Tweets to download and parse for media link) as Twitter has rate limits which seriously reduce the speed of the script.

More details can be located in the config file itself.

'''
config management
'''

import os
import logging
from xdg import BaseDirectory
import yaml


CONFIG_NAME = 'parabola-repolint.conf'
CONFIG_DEFAULT_DIRS = ['.', '/etc', BaseDirectory.xdg_config_home]
CONFIG_DEFAULT_PATHS = [os.path.join(dir, CONFIG_NAME) for dir in CONFIG_DEFAULT_DIRS]


class Bunch(dict):
    ''' a node in the config tree '''

    def __init__(self, data):
        ''' constructor '''
        dict.__init__(self, data)
        self.__dict__ = self


def _make_bunch(data):
    ''' convert a bunch of data into a Bunch object '''
    if isinstance(data, dict):
        return Bunch({k: _make_bunch(v) for k, v in data.items()})
    if isinstance(data, list):
        return [_make_bunch(d) for d in data]
    return data


def _read_config(config):
    ''' try to parse the given config file '''
    data = dict()
    with open(config) as file:
        data = yaml.safe_load(file.read())
        logging.info('loaded config from %s', config)
    return _make_bunch(data)


def _read_configs(configs):
    ''' parse the given config file, if available '''
    logging.info('loading config from %s', configs)
    for config in configs:
        try:
            return _read_config(config)
        except IOError:
            pass
    raise FileNotFoundError('no valid config found')


CONFIG = _read_configs(CONFIG_DEFAULT_PATHS)

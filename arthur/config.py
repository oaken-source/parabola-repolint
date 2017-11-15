'''
config management
'''

import logging
import yaml


CONFIG_DEFAULT_PATHS = [
    './arthur.conf',
    '/etc/arthur.conf'
]


class Bunch(dict):
    ''' a node in the config tree '''
    def __init__(self, **data):
        ''' populate the instance with the given data '''
        data = {k: Bunch(**v) if isinstance(v, dict) else v for k, v in data.items()}
        dict.__init__(self, data)
        self.__dict__ = self


def _read_config(config):
    ''' try to parse the given config file '''
    data = dict()
    with open(config) as file:
        data = yaml.safe_load(file.read())
    return Bunch(**data)


def _read_configs(configs):
    ''' parse the given config file, if available '''
    logging.info('loading config from %s', configs)
    for config in configs:
        try:
            return _read_config(config)
        except IOError:
            pass


CONFIG = _read_configs(CONFIG_DEFAULT_PATHS)

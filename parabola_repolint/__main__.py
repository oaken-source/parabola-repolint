'''
entry point of parabloa-repolint
'''

import argparse
import logging
import logging.config
import sys

from parabola_repolint.config import CONFIG
from parabola_repolint.linter import Linter
from parabola_repolint.repocache import RepoCache
from parabola_repolint.etherpad import pad_replace


def make_argparser(linter):
    ''' produce the argparse object '''
    parser = argparse.ArgumentParser(
        description='parabola package linter',
        epilog='list of all supported linter checks: %s' % ', '.join(linter.checks)
    )

    parser.add_argument(
        '-X',
        '--noupdate',
        action='store_true',
        help='do not update repositories and packages from the mirrors before linting'
    )

    parser.add_argument(
        '-i',
        '--ignore-cache',
        action='store_true',
        help='discard all cached package information and refresh from mirrors'
    )

    parser.add_argument(
        '-c',
        '--checks',
        type=lambda a: set() if not a else set(s.strip() for s in a.split(',')),
        default=','.join(linter.checks),
        help='comma-separated list of checks to perform'
    )

    parser.add_argument(
        '-C',
        '--skip-checks',
        type=lambda a: set() if not a else set(s.strip() for s in a.split(',')),
        default='',
        help='comma-separated list of checks to skip'
    )

    return parser


def checked_main(args):
    ''' the main function '''
    cache = RepoCache()
    linter = Linter(cache)

    args = make_argparser(linter).parse_args(args)

    diff = args.checks.union(args.skip_checks).difference(linter.checks)
    if diff:
        logging.warning("unrecognized linter checks: %s", ', '.join(diff))

    checks = args.checks.intersection(linter.checks).difference(args.skip_checks)
    linter.load_checks(checks)
    cache.load_repos(args.noupdate, args.ignore_cache)
    linter.run_checks()

    res = linter.format()
    logging.info(res)
    pad_replace(CONFIG.parabola.pad_url, res)

    logging.warning(linter.short_format())


def main(args=None):
    ''' a catchall exception handler '''
    logging.config.dictConfig(CONFIG.logging)

    if args is None:
        args = sys.argv[1:]

    try:
        checked_main(args)
    except SystemExit:
        pass
    except: # pylint: disable=bare-except
        logging.exception('unrecoverable error')
        sys.exit(1)


if __name__ == '__main__':
    main()

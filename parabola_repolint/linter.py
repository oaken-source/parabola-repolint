'''
this module provides the linter orchestrator
'''

import importlib
import pkgutil
import logging
import datetime
import socket
import enum


class LinterCheckBase():
    ''' a base class for linter checks '''

    def __init__(self, linter, cache):
        ''' an empty default constructor '''
        pass


class LinterIssue(Exception):
    ''' raised by linter checks to indicate problems '''


class LinterCheckType(enum.Enum):
    ''' possible linter check types '''
    PKGBUILD = 1
    PACKAGE = 2


def _is_linter_check(cls):
    ''' indicate whether a given anything is a linter check class '''
    return (isinstance(cls, type)
            and issubclass(cls, LinterCheckBase)
            and cls != LinterCheckBase)


def _load_linter_checks_from(package_name):
    ''' load a list of classes from the given package '''
    package = importlib.import_module(package_name)

    result = []
    for _, name, _ in pkgutil.walk_packages(package.__path__):
        name = package.__name__ + '.' + name

        logging.debug('loading linter checks from "%s"', name)
        module = importlib.import_module(name)

        for cls in module.__dict__.values():
            if _is_linter_check(cls):
                logging.debug('loaded linter check "%s"', cls.name)
                result.append(cls)

    return result


class Linter():
    ''' the master linter class '''

    def __init__(self, repo_cache):
        ''' constructor '''
        self._checks = _load_linter_checks_from('parabola_repolint.linter_checks')
        self._enabled_checks = []
        self._issues = {}

        self._cache = repo_cache

    @property
    def checks(self):
        ''' return the names of all supported linter checks '''
        return map(lambda c: c.name, self._checks)

    def register_repo_cache(self, cache):
        ''' store a reference to the repo cache '''
        self._cache = cache

    def load_checks(self, checks):
        ''' initialize the set of enabled linter checks '''
        self._enabled_checks = [c(self, self._cache) for c in self._checks if c.name in checks]
        logging.debug('initialized enabled checks %s', self._enabled_checks)

    def run_checks(self):
        ''' run the previuosly initialized enabled checks '''
        check_funcs = {
            LinterCheckType.PKGBUILD: self._run_check_pkgbuild,
            LinterCheckType.PACKAGE: self._run_check_package,
        }

        for check_type in LinterCheckType:
            check_func = check_funcs[check_type]
            for check in [c for c in self._enabled_checks if c.check_type == check_type]:
                self._issues[check] = []
                logging.debug('running check %s', check)
                check_func(check)

    def _run_check_pkgbuild(self, check):
        ''' run a PKGBUILD type check '''
        for pkgbuild in self._cache.pkgbuilds:
            try:
                check.check(pkgbuild)
            except LinterIssue as i:
                self._issues[check].append(i.args)

    def _run_check_package(self, check):
        ''' run a PACKAGE type check '''
        for package in self._cache.packages:
            try:
                check.check(package)
            except LinterIssue as i:
                self._issues[check].append(i.args)

    def format(self):
        ''' return a formatted string of the linter issues '''
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        out = '''
This is an auto-generated list of issues in the parabola package repository.
Generated by parabola-repolint on %s at %s
''' % (socket.gethostname(), now)

        for check in self._enabled_checks:
            if self._issues[check]:
                out += '\n\n%s' % check.format(self._issues[check])
        return out

    def short_format(self):
        ''' return a (short) formatted string of the linter issues '''
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        out = 'parabola-repolint check at %s' % now

        for check in self._enabled_checks:
            header = check.format([]).splitlines()[0]
            out += '\n  %s %i' % (header, len(self._issues[check]))
        return out

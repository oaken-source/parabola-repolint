
from os.path import join, dirname
from setuptools import setup


setup(
    name='parabola-repolint',
    version='0.1.1',
    maintainer='Andreas Grapnetin',
    maintainer_email='andreas@grapentin.org',
    url='https://github.com/oaken-source/parabola-repolint',
    description='a parabola package repository lint tool',
    long_description=open(join(dirname(__file__), 'README.rst')).read(),

    keywords='parabola packages maintenance',
    packages=[
        'parabola_repolint',
        'parabola_repolint.linter_checks',
    ],

    entry_points={
        'console_scripts': [
            'parabola-repolint = parabola_repolint.__main__:main',
        ],
    },

    install_requires=[
        'pyyaml',
        'sh',
        'pyxdg',
        'python-gnupg',
        'python-telegram-bot',
        'splinter',
    ],

    license='GPLv3',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Programming Language :: Python :: 3 :: Only',
    ],

    test_suite='tests',
    tests_require=[
        'pytest',
    ],

    setup_requires=['pytest_runner'],
)

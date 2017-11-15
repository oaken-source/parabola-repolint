
from os.path import join, dirname
from setuptools import setup


setup(
    name='arthur',
    version='0.1',
    maintainer='Andreas Grapnetin',
    maintainer_email='andreas@grapentin.org',
    url='https://github.com/oaken-source/arthur',
    description='a parabola package build butler',
    long_description=open(join(dirname(__file__), 'README.rst')).read(),

    keywords='parabola packages maintenance',
    packages=['arthur'],

    entry_points={
        'console_scripts': [
            'arthurd = arthur.__main__:main',
            'arthur = arthur.api:main',
        ],
    },

    install_requires=[
        'telegram_send',
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

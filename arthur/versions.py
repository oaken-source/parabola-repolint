''' functions to load versions from upstream '''

import zipfile
import re
import io
import requests
from lxml.html import soupparser
from .parabola import VersionMaster


def brew(url):
    ''' make a request and brew a soup '''
    response = requests.get(url)
    return soupparser.fromstring(response.text)


@VersionMaster.register('akonadi-contacts')
@VersionMaster.register('ark')
@VersionMaster.register('kdebase-runtime')
@VersionMaster.register('kdenetwork-kopete')
@VersionMaster.register('kio-extras')
@VersionMaster.register('konqueror')
@VersionMaster.register('okular')
def kde_applications():
    ''' produce the latest stable version of kde applications '''
    soup = brew('https://download.kde.org/stable/applications/')
    return soup.xpath('(//tr/td/a)[last()]/text()')[0].rstrip('/')


@VersionMaster.register('arrayfire')
def arrayfire():
    ''' produce the latest release version of arrayfire '''
    soup = brew('https://github.com/arrayfire/arrayfire/releases')
    return soup.xpath('((//div[@class="release-meta"])[1]//span)[2]/text()')[0].lstrip('v')


@VersionMaster.register('avidemux-(cli|qt)')
def avidemux():
    ''' produce the latest release version of avidemux '''
    soup = brew('http://fixounet.free.fr/avidemux/download.html')
    return soup.xpath('(//b)[2]/text()')[0].split()[0]


@VersionMaster.register('blender')
@VersionMaster.register('blender-addon-(gimp|povray)')
def blender():
    ''' produce the latest stable-ish version of blender '''
    soup = brew('https://www.blender.org')
    return soup.xpath('//a[@class="cta-download"]/text()')[0].split()[-1]


@VersionMaster.register('cbootimage')
def cbootimage():
    ''' produce the latest stable version of cbootimage '''
    soup = brew('https://github.com/NVIDIA/cbootimage/releases')
    return soup.xpath('(//div/h3/a/span)[1]/text()')[0].lstrip('v')


@VersionMaster.register('debootstrap')
def debootstrap():
    ''' produce the latest stable version of debootstrap '''
    soup = brew('https://tracker.debian.org/pkg/debootstrap')
    return soup.xpath('(//li[@class="list-group-item"])[2]/text()')[1].strip()


@VersionMaster.register('gcc-gcj-ecj')
def gcc_gcj_ecj():
    ''' produce the latest stable version of gcc-gcj-ecj '''
    soup = brew('https://sourceware.org/pub/java/')
    vers = [e for e in soup.xpath('//tr//a/text()') if re.match(r'^ecj-[0-9\.]*.jar$', e)]
    return vers[-1][4:-4]


@VersionMaster.register('gnome-weather')
def gnome_weather():
    ''' produce the latest stable version of gnome-weather '''
    soup = brew('https://download.gnome.org/sources/gnome-weather/')
    shortver = soup.xpath('//tr//a[1]')[-3].get('href')
    soup = brew('https://download.gnome.org/sources/gnome-weather/' + shortver)
    ver = next(a.get('href') for a in soup.xpath('//a') if 'LATEST' in a.get('href'))
    return ver.split('-')[-1]


@VersionMaster.register('iceape')
@VersionMaster.register('iceape-l10n-.*')
def iceape():
    ''' produce the latest stable version of iceape '''
    soup = brew('https://www.seamonkey-project.org/releases/')
    return soup.xpath('//div[@id="download"]/b/text()')[0].split()[1]


@VersionMaster.register('icecat')
@VersionMaster.register('icecat-l10n-.*')
def icecat():
    ''' produce the latest stable version of icecat '''
    soup = brew('https://ftp.gnu.org/gnu/gnuzilla/')
    return soup.xpath('(//tr/td/a)[last()-1]/text()')[0].rstrip('/')


@VersionMaster.register('icedove')
@VersionMaster.register('icedove-l10n-.*')
def icedove():
    ''' produce the latest stable version of icedove '''
    soup = brew('https://www.mozilla.org/en-US/thunderbird/latest/releasenotes/')
    return soup.xpath('//h2/text()')[0].split()[1].rstrip(',')


@VersionMaster.register('iceweasel')
@VersionMaster.register('iceweasel-l10n-.*')
def iceweasel():
    ''' produce the latest stable version of iceweasel '''
    soup = brew('https://www.mozilla.org/en-US/firefox/latest/releasenotes/')
    return soup.xpath('//div[@class="version"]/h2/text()')[0]


@VersionMaster.register('icecat-noscript')
@VersionMaster.register('iceweasel-noscript')
def noscript_legacy():
    ''' produce the latest stable noscript legacy version '''
    soup = brew('https://noscript.net/changelog')
    lines = soup.xpath('//pre/text()')[0].splitlines()
    vers = (line[2:] for line in lines if line.startswith('v'))
    return next(ver for ver in vers if int(ver.split('.')[0]) < 10)


def noscript_webext():
    ''' produce the latest stable noscript webext version '''
    soup = brew('https://noscript.net/changelog')
    lines = soup.xpath('//pre/text()')[0].splitlines()
    vers = (line[2:] for line in lines if line.startswith('v'))
    return next(ver for ver in vers if int(ver.split('.')[0]) >= 10)


@VersionMaster.register('icecat-ublock-origin')
@VersionMaster.register('iceweasel-ublock-origin')
def ublock_origin():
    ''' produce the latest stable version of ublock origin '''
    soup = brew('https://github.com/gorhill/uBlock/releases')
    return soup.xpath('(//div[@class="release label-latest"]//span)[2]/text()')[0]


@VersionMaster.register('kdelibs')
def kdelibs():
    ''' produce the latest stable version of kdelibs '''
    appver = kde_applications()
    soup = brew('https://download.kde.org/stable/applications/%s/src/' % appver)
    return next(e for e in soup.xpath('//a/text()') if 'kdelibs' in e)[8:-7]


@VersionMaster.register('khotkeys')
@VersionMaster.register('kinfocenter')
def kde_plasma():
    ''' produce the latest stable version of kde plasma '''
    soup = brew('https://download.kde.org/stable/plasma/')
    return soup.xpath('(//tr/td[2]/a/text())[last()]')[0].rstrip('/')


@VersionMaster.register('kile')
def kile():
    ''' produce the latest stable version of kile (sort of) '''
    soup = brew('https://sourceforge.net/projects/kile/files/unstable/')
    link = 'https://sourceforge.net' + soup.xpath('//table[@id="files_list"]//a')[1].get('href')
    anchors = brew(link).xpath('//table[@id="files_list"]//a')
    link = next(a.get('href') for a in anchors if '.tar.' in a.get('href'))
    return link.split('/')[-2][5:-8]


@VersionMaster.register('kio')
def kde_frameworks():
    ''' produce the latest stable version of kde frameworks '''
    soup = brew('https://download.kde.org/stable/frameworks/')
    return soup.xpath('(//tr/td[2]/a/text())[last()]')[0].rstrip('/')


@VersionMaster.register('mednaffe')
@VersionMaster.register('mednaffe-gtk2')
def mednaffe():
    ''' produce the latest stable version of mednaffe '''
    soup = brew('https://github.com/AmatCoder/mednaffe/releases')
    return soup.xpath('((//div[@class="release-meta"])[1]//span)[2]/text()')[0].lstrip('v')


@VersionMaster.register('pdftk')
def pdftk():
    ''' produce the latest stable version of pdftk '''
    soup = brew('https://www.pdflabs.com/docs/pdftk-version-history/')
    return soup.xpath('(//li//a)[1]')[0].get('href').split('/')[-1][6:-8]


@VersionMaster.register('stormlib')
def stormlib():
    ''' produce the latest version of stormlib '''
    soup = brew('https://github.com/ladislav-zezula/StormLib/releases')
    return soup.xpath('((//div[@class="release-meta"])[1]//span)[2]/text()')[0].lstrip('v')


@VersionMaster.register('task-spooler')
def task_spooler():
    ''' produce the latest version of task-spooler '''
    response = requests.get('http://vicerveza.homeunix.net/~viric/soft/ts/Changelog')
    return next(l for l in response.text.split('\n') if l.lstrip().startswith('v'))[1:-1]


@VersionMaster.register('unar')
def unar():
    ''' produce the latest stable version of unar (sigh...) '''
    stream = requests.get(
        'https://theunarchiver.com/downloads/TheUnarchiverSource.zip',
        stream=True
    )
    zf = zipfile.ZipFile(io.BytesIO(stream.content))
    with zf.open('XADMaster/unar.m') as file:
        ver = next(line for line in file.readlines() if b'VERSION' in line)
    return ver.split(b'"')[1].lstrip(b'v').decode('utf-8')


@VersionMaster.register('webkit2gtk')
def webkit2gtk():
    ''' produce the latest stable version of webkit2gtk '''
    soup = brew('https://webkitgtk.org/releases/')
    return soup.xpath('(//tr//a)[last()]/text()')[0][10:-12]

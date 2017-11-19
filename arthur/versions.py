''' functions to load versions from upstream '''

import requests
from lxml.html import soupparser
from .parabola import VersionMaster


@VersionMaster.register('akonadi-contacts')
@VersionMaster.register('ark')
@VersionMaster.register('kdebase-runtime')
@VersionMaster.register('kdenetwork-kopete')
@VersionMaster.register('kio-extras')
@VersionMaster.register('konqueror')
@VersionMaster.register('okular')
def kde_applications():
    ''' produce the latest stable version of kde applications '''
    response = requests.get('https://download.kde.org/stable/applications/')
    tree = soupparser.fromstring(response.text)
    return tree.xpath('(//tr/td/a)[last()]/text()')[0].rstrip('/')


@VersionMaster.register('arrayfire')
def arrayfire():
    ''' produce the latest release version of arrayfire '''
    response = requests.get('https://github.com/arrayfire/arrayfire/releases')
    tree = soupparser.fromstring(response.text)
    return tree.xpath('((//div[@class="release-meta"])[1]//span)[2]/text()')[0].lstrip('v')


@VersionMaster.register('avidemux-(cli|qt)')
def avidemux():
    ''' produce the latest release version of avidemux '''
    response = requests.get('http://fixounet.free.fr/avidemux/download.html')
    tree = soupparser.fromstring(response.text)
    return tree.xpath('(//b)[2]/text()')[0].split()[0]


@VersionMaster.register('blender')
@VersionMaster.register('blender-addon-(gimp|povray)')
def blender():
    ''' produce the latest stable-ish version of blender '''
    response = requests.get('https://www.blender.org')
    tree = soupparser.fromstring(response.text)
    return tree.xpath('//a[@class="cta-download"]/text()')[0].split()[-1]


@VersionMaster.register('cbootimage')
def cbootimage():
    ''' produce the latest stable version of cbootimage '''
    response = requests.get('https://github.com/NVIDIA/cbootimage/releases')
    tree = soupparser.fromstring(response.text)
    return tree.xpath('(//div/h3/a/span)[1]/text()')[0].lstrip('v')


@VersionMaster.register('debootstrap')
def debootstrap():
    ''' produce the latest stable version of debootstrap '''
    response = requests.get('https://tracker.debian.org/pkg/debootstrap')
    tree = soupparser.fromstring(response.text)
    return tree.xpath('(//li[@class="list-group-item"])[2]/text()')[1].strip()


@VersionMaster.register('iceape')
@VersionMaster.register('iceape-l10n-.*')
def iceape():
    ''' produce the latest stable version of iceape '''
    response = requests.get('https://www.seamonkey-project.org/releases/')
    tree = soupparser.fromstring(response.text)
    return tree.xpath('//div[@id="download"]/b/text()')[0].split()[1]


@VersionMaster.register('icecat')
@VersionMaster.register('icecat-l10n-.*')
def icecat():
    ''' produce the latest stable version of icecat '''
    response = requests.get('https://ftp.gnu.org/gnu/gnuzilla/')
    tree = soupparser.fromstring(response.text)
    return tree.xpath('(//tr/td/a)[last()-1]/text()')[0].rstrip('/')


@VersionMaster.register('icedove')
@VersionMaster.register('icedove-l10n-.*')
def icedove():
    ''' produce the latest stable version of icedove '''
    response = requests.get('https://www.mozilla.org/en-US/thunderbird/latest/releasenotes/')
    tree = soupparser.fromstring(response.text)
    return tree.xpath('//h2/text()')[0].split()[1].rstrip(',')


@VersionMaster.register('iceweasel')
@VersionMaster.register('iceweasel-l10n-.*')
def iceweasel():
    ''' produce the latest stable version of iceweasel '''
    response = requests.get('https://www.mozilla.org/en-US/firefox/latest/releasenotes/')
    tree = soupparser.fromstring(response.text)
    return tree.xpath('//div[@class="version"]/h2/text()')[0]

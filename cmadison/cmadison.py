#!/usr/bin/env python
#
# Provides a rather basic version of rmadison (or dak ls if you prefer)
# for the Ubuntu cloud-archive.
#
# This script works in the following manner:
#  1) It will show the rmadison output for the selected package to show
#     the values of packages within the main ubuntu archives
#  2) It will show similar output for the selected package in the ubuntu
#     cloud archives.
#

from __future__ import print_function

from lxml import etree
from requests.exceptions import HTTPError
import argparse
import gzip
import logging as log
import os
import os.path
import requests
import requests_cache
import six
import shutil
import tempfile


# Defines the default ubuntu cloud-archive repository URL.
UCA_DEB_REPO_URL = "http://ubuntu-cloud.archive.canonical.com/ubuntu/dists"

# URLs used in rmadison queries
RMADISON_URL_MAP = {
    'debian': "https://api.ftp-master.debian.org/madison",
    'new': "https://api.ftp-master.debian.org/madison?s=new",
    'qa': "https://qa.debian.org/madison.php",
    'ubuntu': "http://people.canonical.com/~ubuntu-archive/madison.cgi",
    'udd': 'https://qa.debian.org/cgi-bin/madison.cgi',
}

# Which releases are no longer supported
UNSUPPORTED_RELEASES = [
    'folsom',
    'grizzly',
    'havana',
    'icehouse',
    'juno',
    'kilo',
    'liberty',
    'newton'
]

# Contains a mapping of dist pockets to list of release pockets to ignore
IGNORE_RELEASES = {
    'precise-updates': ['stein'],
    'precise-proposed': ['stein'],
}

# The directory containing cache data content
if 'SNAP_USER_DATA' in os.environ:
    CACHE_DIR = os.environ.get('SNAP_USER_DATA')
else:
    CACHE_DIR = os.path.expanduser('~/.cmadison')

# This is where the Sources.gz files will be downloaded to.
# In the future, it'd be better to have these cached and know - but
# I'll /assume/ bandwidth is decent enough its not a super big issue.
working_dir = tempfile.mkdtemp()


def get_files_in_remote_url(relative_path=""):
    """
    Returns a list of files found in the remote URL specified.
    This is heavily dependent upon being able to browse the folders over
    http as the ubuntu cloud archives are. If that changes, then this
    script needs to be revisited.

    :relative_path: a path relative to the UCA_DEB_REPO_URL
    :return: list of files or folders found in the remote url.
    """
    url = "%s/%s" % (UCA_DEB_REPO_URL, relative_path)
    resp = requests.get(url)
    resp.raise_for_status()

    root = etree.fromstring(resp.text, etree.HTMLParser())

    # Content available here should be directory listing, which is presented
    # as a table, with each file in its own row. Use xpath expression to find
    # the values of the text within the table columns.
    files = []
    for f in root.xpath('//*/td/*/text()'):
        # Skip the canonical parent directory nav link
        if f == 'Parent Directory':
            continue
        if f.endswith('/'):
            f = f[:-1]
        files.append(f)
    log.debug("Found files at %s: %s", url, files)

    return files


def get_available_dists():
    """
    Returns the list of distributions which are available.
    """
    # Each folder maps to a dist
    dists = []
    for folder in get_files_in_remote_url():
        dists.append(folder)

    return dists


def get_openstack_releases(dist, show_eol=False):
    """
    Returns a list of available OpenStack releases for the specified
    distribution.

    :param dist: the distribution to retrieve openstack releases for.
    """
    os_releases = get_files_in_remote_url(dist)
    log.debug("Found OpenStack releases for dist %s: %s", dist, os_releases)
    if not show_eol:
        os_releases = [x for x in os_releases if x not in UNSUPPORTED_RELEASES]

    return os_releases


class Sources(object):

    def __init__(self, dist, os_release):
        """
        Creates a new Sources which represents the Sources.gz file
        for the source folder in the specified distro and OpenStack
        release.

        :param dist: the Ubuntu distribution
        :param os_release: the OepnStack release
        """
        fname = '%s_%s_Sources.gz' % (dist, os_release)
        self.dist = dist
        self.os_release = os_release
        self.fname = os.path.join(working_dir, fname)

        self.ready = self.download()

    def download(self):
        """
        Downloads the file to parse Source information from.
        """
        url = ("{base_url}/{dist}/{os_release}/main/source/"
               "Sources.gz").format(base_url=UCA_DEB_REPO_URL, dist=self.dist,
                                    os_release=self.os_release)

        try:
            resp = requests.get(url)
            resp.raise_for_status()
            with open(self.fname, 'wb+') as fd:
                for chunk in resp.iter_content(chunk_size=128):
                    fd.write(chunk)
            return True
        except HTTPError:
            log.error("Could not download source for {dist}/"
                      "{os_release}".format(dist=self.dist,
                                            os_release=self.os_release))
            return False

    def get_sources(self):
        """
        A generator returning the Source package descriptors
        found in the Sources.gz file supplied.

        :param filename: the file to read the source packages from.
        """
        lines = []
        if not self.ready:
            return

        for line in gzip.open(self.fname):
            # Decode the bytes object into a string
            if type(line) == bytes:
                line = line.decode('utf-8')

            # Empty line is the end of the source package stanza
            if line.strip() == '':
                src = Source.parse(''.join(lines))
                lines = []
                yield src
            else:
                lines.append(line)


class Source(dict):

    @property
    def package(self):
        return self['Package']

    @property
    def binaries(self):
        binary_as_str = self['Binary']
        return binary_as_str.split(', ')

    @property
    def version(self):
        return self['Version']

    @property
    def architecture(self):
        return self['Architecture']

    @classmethod
    def parse(cls, text):
        """
        Parses basic content from the Sources.gz file in a debian archive for
        retrieving basic information.

        :param text: the text to parse
        """
        src = Source()

        lines = text.split('\n')
        key = None
        for line in lines:
            if line.startswith(' '):
                # Continuation from the previous line
                src[key] = src[key] + line
            else:
                parts = line.split(': ')
                key = parts[0]
                value = ':'.join(parts[1:])
                src[key] = value

        return src


def print_table(table):
    """
    Prints the table in a nice formatted output.

    :param table: a table in a traditional representation
                  (a list of lists)
    """
    widths = [max(len(x) for x in col) for col in zip(*table)]
    for row in table:
        out = " | ".join("{:{}}".format(x, widths[i])
                         for i, x in enumerate(row))
        print(" " + out)


def do_rmadison_search(search_for, urls=None, print_source=False):
    """
    rmadison simply queries a set of URLs with parameters of package name
    and asks for text output. Just run the same query that rmadison does
    and spit out the output.
    """
    if not urls:
        return

    if isinstance(urls, six.string_types):
        urls = [urls]

    for url in urls:
        try:
            base_url = RMADISON_URL_MAP.get(url, None)
            if not base_url:
                log.error("Unknown source %s", url)
                continue
            params = {
                'package': search_for,
                'text': 'on',
            }
            resp = requests.get(base_url, params=params)
            resp.raise_for_status()
            print('%s:' % url)
            print(resp.text)
        except HTTPError as e:
            log.error("Error querying url %s: %s", url, str(e))


def ignore_source(dist, release):
    """
    Returns true if the source should be ignored
    :param dist: the base OS distribution (e.g. xenial, trusty, etc)
    :param release: the openstack release version (e.g. mitaka, newton, etc)
    :return: True if the source should be ignored, False otherwise
    """
    ignore = IGNORE_RELEASES.get(dist, None)
    if not ignore:
        return False
    return release in ignore


def do_cloudarchive_search(package, print_source=False, show_eol=False):
    """
    Runs the search for packages in the cloud archive.
    """
    dists = get_available_dists()

    mapping = {}
    for d in dists:
        os_releases = get_openstack_releases(d, show_eol)
        mapping[d] = os_releases

    matches = []
    eol_matches = []
    for dist, os_releases in mapping.items():
        for os_release in os_releases:
            # Ignore some dist/os_release combinations
            if ignore_source(dist, os_release):
                continue

            for src in Sources(dist, os_release).get_sources():
                for pkg in package:
                    if src.package == pkg:
                        mtype = 'source'
                    elif pkg in src.binaries:
                        mtype = src.architecture
                    else:
                        # Not a match, continue
                        continue

                    rname = os_release
                    if dist.find('-proposed') > 0:
                        rname = '%s-proposed' % os_release

                    if show_eol and os_release in UNSUPPORTED_RELEASES:
                        eol_matches.append([pkg, src.version, rname, mtype])
                    else:
                        matches.append([pkg, src.version, rname, mtype])

    if print_source:
        print("cloud-archive:")

    if eol_matches:
        print("-- Unsupported Releases --")
        print_table(sorted(eol_matches, key=lambda row: row[0] + row[2]))

    if matches:
        if eol_matches:
            print("-- Supported Releases --")
        print_table(sorted(matches, key=lambda row: row[0] + row[2]))

    # Put a blank line after the table to separate from others
    print()


def clear_cache():
    """Removes the cache data"""
    shutil.rmtree(CACHE_DIR)


def setup_cache():
    """Sets up the local cache repository and ensures that the requests_cache
    monkey patching is injected in order to ensure the remote requests use
    the cmadison cache data.
    """
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)

    requests_cache.install_cache(os.path.join(CACHE_DIR, 'cmadison'))


def main():
    desc = """Provides Ubuntu cloud-archive support on top of the rmadison
    utilities and packages. Though it does not provide 1:1 functionality
    with rmadison, it provides 'good enough' support in order to determine
    which packages live in the cloud-archive.
    """
    parser = argparse.ArgumentParser(description=desc)

    parser.add_argument('-u', default='cloud-archive', dest='urls',
                        help=('use URL for the query. This provides some '
                              'parity to the rmadison tool, but adds in '
                              'cloud-archive to the list of available '
                              'URLs. For cmadison, cloud-archive is the '
                              'default value. Any additional values are '
                              'passed on to rmadison'))
    parser.add_argument('--clear-cache', default=False, dest='clear_cache',
                        action='store_true',
                        help=('Remove cache data prior to searching. All '
                              'cache data will be removed'))
    parser.add_argument('--no-cache', default=False, dest='no_cache',
                        action='store_true',
                        help='Do not used cached data')
    parser.add_argument('--eol', default=False, dest='eol',
                        action='store_true',
                        help=('Show releases which have reached end of life'))
    parser.add_argument('package', nargs='+')

    try:
        args = parser.parse_args()
        sources = args.urls.split(',')
        print_prefix = len(sources) > 1

        if args.clear_cache:
            clear_cache()

        if not args.no_cache:
            setup_cache()

        if 'cloud-archive' in sources:
            do_cloudarchive_search(args.package, print_prefix, args.eol)
            sources.remove('cloud-archive')

        if len(sources) >= 1:
            print_prefix = print_prefix and len(sources) == 1
            do_rmadison_search(args.package, sources, print_prefix)
    finally:
        shutil.rmtree(working_dir)


if __name__ == '__main__':
    main()

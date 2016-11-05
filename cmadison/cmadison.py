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
import argparse
import gzip
import logging as log
import os.path
import shutil
import subprocess
import tempfile
import urllib2


# Defines teh default ubuntu cloud-archive repository URL.
UCA_DEB_REPO_URL = "http://ubuntu-cloud.archive.canonical.com/ubuntu/dists"

# Which releases are no longer supported
UNSUPPORTED_RELEASES = ['folsom', 'grizzly', 'havana']

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
    content = urllib2.urlopen(url)
    root = etree.parse(content, etree.HTMLParser())

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


def get_openstack_releases(dist):
    """
    Returns a list of available OpenStack releases for the specified
    distribution.

    :param dist: the distribution to retrieve openstack releases for.
    """
    os_releases = get_files_in_remote_url(dist)
    log.debug("Found OpenStack releases for dist %s: %s", dist, os_releases)
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
        url = ("%(base_url)s/%(dist)s/%(os_release)s/main/source/Sources.gz" %
               {'base_url': UCA_DEB_REPO_URL,
                'dist': self.dist,
                'os_release': self.os_release})

        try:
            content = urllib2.urlopen(url)
            with open(self.fname, 'wb+') as f:
                f.write(content.read())
            return True
        except urllib2.HTTPError:
            log.info("Could not download source for %(dist)s/%(os_release)s" % {'dist': self.dist, 'os_release': self.os_release})
            return False

    def get_sources(self):
        """
        A generator returning the Source package descriptors
        found in the Sources.gz file supplied.

        :param filename: the file to read the source packages from.
        """
        lines = []
        if self.ready:
            for line in gzip.open(self.fname):
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
    Runs the earch for the packages using rmadison.
    """
    try:
        cmd = ['rmadison']
        if urls and isinstance(urls, list):
            cmd.extend(['-u', ','.join(urls)])
        cmd.extend(search_for)
        output = subprocess.check_output(cmd)
        if print_source and urls:
            print('%s:' % urls[0])
        print(output)
    except Exception as e:
        log.error("Error querying rmadison: %s", str(e))


def do_cloudarchive_search(package, print_source=False):
    """
    Runs the search for packages in the cloud archive.
    """
    dists = get_available_dists()

    mapping = {}
    for d in dists:
        os_releases = get_openstack_releases(d)
        mapping[d] = os_releases

    matches = []
    for dist, os_releases in mapping.items():
        for os_release in os_releases:
            for src in Sources(dist, os_release).get_sources():
                for pkg in package:
                    mtype = ''
                    if src.package == pkg:
                        mtype = 'source'
                    elif pkg in src.binaries:
                        mtype = src.architecture
                    else:
                        # Not a match, continue
                        continue

                    if dist.find('-proposed') > 0:
                        os_release = '%s-proposed' % os_release
                    match = [pkg,
                             src.version,
                             os_release,
                             mtype]
                    matches.append(match)

    if print_source:
        print("cloud-archive:")

    print_table(sorted(matches, key=lambda row: row[0] + row[2]))


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
    parser.add_argument('package', nargs='+')

    try:
        args = parser.parse_args()
        sources = args.urls.split(',')
        print_prefix = len(sources) > 1

        if 'cloud-archive' in sources:
            do_cloudarchive_search(args.package, print_prefix)
            sources.remove('cloud-archive')

        if len(sources) >= 1:
            print_prefix = print_prefix and len(sources) == 1
            do_rmadison_search(args.package, sources, print_prefix)
    finally:
        shutil.rmtree(working_dir)

if __name__ == '__main__':
    main()

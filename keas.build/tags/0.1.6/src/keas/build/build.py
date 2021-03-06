##############################################################################
#
# Copyright (c) 2008 Zope Foundation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Build a release

$Id$
"""
__docformat__ = 'ReStructuredText'
import BeautifulSoup
import ConfigParser
import StringIO
import base64
import logging
import pkg_resources
import re
import sys
import shutil
import os
import urllib2
from keas.build import base, package

logger = base.logger

def findProjectVersions(project, config, options, uploadType):
    if options.offline:
        logger.info('Offline: Skip looking for project versions.')
        return []

    VERSION = re.compile(project+r'-(\d+\.\d+(\.\d+){0,2})')

    if uploadType == 'local':
        dest = os.path.join(config.get(base.BUILD_SECTION, 'buildout-server'),
                            project)

        versions = []
        for root, dirs, files in os.walk(dest):
            for fname in files:
                m = VERSION.search(fname)
                if m:
                    versions.append(m.group(1))
    else:
        url = config.get(base.BUILD_SECTION, 'buildout-server') + project + '/'
        logger.debug('Package Index: ' + url)
        req = urllib2.Request(url)

        username = config.get(base.BUILD_SECTION, 'buildout-server-username')
        password = config.get(base.BUILD_SECTION, 'buildout-server-password')
        base64string = base64.encodestring('%s:%s' % (username, password))[:-1]
        req.add_header("Authorization", "Basic %s" % base64string)

        try:
            soup = BeautifulSoup.BeautifulSoup(urllib2.urlopen(req).read())
        except urllib2.HTTPError, err:
            logger.error("There was an error accessing %s: %s" % (url, err))
            return []

        versions = []
        for tag in soup('a'):
            cntnt = str(tag.contents[0]) # str: re does not like non-strings
            m = VERSION.search(cntnt)
            if m:
                versions.append(m.group(1))

    return sorted(versions, key=lambda x: pkg_resources.parse_version(x))


def build(configFile, options):
    # Read the configuration file.
    logger.info('Loading configuration file: ' + configFile)
    config = ConfigParser.RawConfigParser()
    config.read(configFile)

    # Create the project config parser
    logger.info('Creating Project Configuration')
    projectParser = ConfigParser.RawConfigParser()
    if config.has_option(base.BUILD_SECTION, 'template'):
        template = config.get(base.BUILD_SECTION, 'template')
        logger.info('Loading Project Configuration Template: ' + template)
        projectParser.read([template])
    if not projectParser.has_section('versions'):
        projectParser.add_section('versions')

    # Determine all versions of the important packages
    pkgversions = {}
    for pkg in config.get(base.BUILD_SECTION, 'packages').split():
        customPath = None
        if ':' in pkg:
            pkg, customPath = pkg.split(':')
        builder = package.PackageBuilder(pkg, options)
        version = builder.runCLI(configFile, True)
        pkgversions[pkg] = version
        projectParser.set('versions', pkg, version)

    try:
        uploadType = config.get(base.BUILD_SECTION, 'buildout-upload-type')
    except ConfigParser.NoOptionError:
        uploadType = "webdav"

    # Stop if no buildout-server given
    try:
        config.get(base.BUILD_SECTION, 'buildout-server')
    except ConfigParser.NoOptionError:
        logger.info('No buildout-server specified in the cfg, STOPPING')
        logger.info('Selected package versions:\n%s' % (
            '\n'.join('%s = %s' % (pkg, version)
                      for pkg, version in pkgversions.items())) )
        return

    # Write the new configuration file to disk
    projectName = config.get(base.BUILD_SECTION, 'name')
    defaultVersion = configVersion = config.get(base.BUILD_SECTION, 'version')
    projectVersions = findProjectVersions(projectName, config,
                                          options, uploadType)
    if projectVersions:
        defaultVersion = projectVersions[-1]
    if options.nextVersion or configVersion == '+':
        defaultVersion = base.guessNextVersion(defaultVersion)
    projectVersion = base.getInput(
        'Project Version', defaultVersion, options.useDefaults)

    projectConfigFilename = '%s-%s.cfg' %(projectName, projectVersion)
    logger.info('Writing project configuration file: ' + projectConfigFilename)
    projectParser.write(open(projectConfigFilename, 'w'))

    filesToUpload = [projectConfigFilename]

    # Create deployment configurations
    for section in config.sections():
        if section == base.BUILD_SECTION:
            continue
        logger.info('Building deployment configuration: %s', section)
        template_path = config.get(section, 'template')
        logger.info('Loading deploy template file: %s', template_path)
        template = file(template_path, 'r').read()
        vars = dict([(name, value)
                     for name, value in config.items(section)
                     if name != 'template'])
        vars['project-name'] = projectName
        vars['project-version'] = projectVersion
        vars['instance-name'] = section

        #handle multi-line items, ConfigParser removes leading spaces
        #we need to add some back otherwise it will be a parsing error
        for k, v in vars.items():
            if '\n' in v:
                #add a 2 space indent
                vars[k] = v.replace('\n', '\n  ')

        try:
            deployConfigText = template % vars
        except KeyError, e:
            logger.error("The %s deployment configuration is missing the %r setting required by %s",
                         section, e.message, template_path)
            sys.exit(0)
        deployConfigFilename = '%s-%s-%s.cfg' %(
            config.get(base.BUILD_SECTION, 'name'), section, projectVersion)
        deployConfig = ConfigParser.RawConfigParser()
        deployConfig.readfp(StringIO.StringIO(deployConfigText))
        deployConfig.set('buildout', 'extends', projectConfigFilename)
        logger.info('Writing deployment file: ' + deployConfigFilename)
        deployConfig.write(open(deployConfigFilename, 'w'))

        filesToUpload.append(deployConfigFilename)

    # Upload the deployment files
    if uploadType == 'local':
        #no upload, just copy to destination
        dest = os.path.join(config.get(base.BUILD_SECTION, 'buildout-server'),
                            projectName)
        if not os.path.exists(dest):
            os.makedirs(dest)
        for filename in filesToUpload:
            shutil.copyfile(filename, os.path.join(dest, filename))
    elif uploadType == 'webdav':
        if not options.offline and not options.noUpload:
            for filename in filesToUpload:
                base.uploadFile(
                    filename,
                    config.get(
                        base.BUILD_SECTION, 'buildout-server')+'/'+projectName,
                    config.get(base.BUILD_SECTION, 'buildout-server-username'),
                    config.get(base.BUILD_SECTION, 'buildout-server-password'),
                    options.offline)
    elif uploadType == 'mypypi':
        if not options.offline and not options.noUpload:
            url = (config.get(base.BUILD_SECTION, 'buildout-server')+
                   '/'+projectName+'/upload')
            boundary = "--------------GHSKFJDLGDS7543FJKLFHRE75642756743254"
            headers={"Content-Type":
                "multipart/form-data; boundary=%s; charset=utf-8" % boundary}
            for filename in filesToUpload:
                #being lazy here with the construction of the multipart form data
                content = """--%s
Content-Disposition: form-data; name="content";filename="%s"

%s
--%s--
""" % (boundary, filename, open(filename, 'r').read(), boundary)

                base.uploadContent(
                    content, filename, url,
                    config.get(base.BUILD_SECTION, 'buildout-server-username'),
                    config.get(base.BUILD_SECTION, 'buildout-server-password'),
                    options.offline, method='POST', headers=headers)


def main(args=None):
    # Make sure we get the arguments.
    if args is None:
        args = sys.argv[1:]
    if not args:
        args = ['-h']

    # Set up logger handler
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(levelname)s - %(message)s')
    handler.setFormatter(base.formatter)
    logger.addHandler(handler)

    # Parse arguments
    options, args = base.parser.parse_args(args)

    logger.setLevel(logging.INFO)
    if options.verbose:
        logger.setLevel(logging.DEBUG)
    if options.quiet:
        logger.setLevel(logging.FATAL)

    try:
        build(options.configFile, options)
    except KeyboardInterrupt:
        logger.info("Quitting")
        sys.exit(0)

    # Remove the handler again.
    logger.removeHandler(handler)

    # Exit cleanly.
    sys.exit(0)

import codecs
import os
import sys
import sha
import shutil
import tempfile
import pkg_resources
import logging
from random import randint
from paste.script.templates import var

HOME = os.path.expanduser('~')


class ask_var(var):

    def __init__(self, name, description,
                 default='', should_echo=True, should_ask=True,
                 getter=None):
        super(ask_var, self).__init__(
            name, description, default=default,
            should_echo=should_echo)
        self.should_ask = should_ask
        self.getter = getter
        if self.getter is None:
            self.getter = lambda x, y: self.default


def get_var(vars, name):
    for var in vars:
        if var.name == name:
            return var


def create_buildout_default_file():
    default_dir = os.path.join(HOME, '.buildout')
    if not os.path.isdir(default_dir):
        os.mkdir(default_dir)
    eggs_dir = os.path.join(default_dir, 'eggs')
    if not os.path.isdir(eggs_dir):
        os.mkdir(eggs_dir)
    if sys.platform == 'win32':
        # Fix for paths with spaces on Windows.
        # See https://bugs.launchpad.net/grok/+bug/315223
        import win32api
        eggs_dir = win32api.GetShortPathName(eggs_dir)
    default_cfg = os.path.join(HOME, '.buildout', 'default.cfg')
    if not os.path.isfile(default_cfg):
        config_file = open(default_cfg, 'w')
        contents = """[buildout]
eggs-directory = %s
""" % (eggs_dir)
        config_file.write(contents)
        config_file.close()

def get_sha1_encoded_string(passwd):
    """Encode the given `string` using SHA1.
    """
    encoder = codecs.getencoder('utf-8')
    salt = "%08x" % randint(0, 0xffffffff)
    # This is apparently a wrong use of salt, but the old SHA1
    # password manager of `zope.app.authentication` handles it this way.
    result = salt + sha.new(encoder(passwd)[0]).hexdigest()
    return result

def get_boolean_value_for_option(vars, option):
    value = vars.get(option.name)
    if value is not None:
        if isinstance(option.default, bool):
            want_boolean = True
        else:
            want_boolean = False
        value = value.lower()
        if value in ('1', 'true', 'yes'):
            if want_boolean:
                value = True
            else:
                value = 'true'
        elif value in ('0', 'false', 'no'):
            if want_boolean:
                value = False
            else:
                value = 'false'
        else:
            print ""
            print "Error: %s should be true or false." % option.name
            sys.exit(1)
    else:
        value = option.default
    return value


def exist_buildout_default_file():
    default_cfg = os.path.join(HOME, '.buildout', 'default.cfg')
    return os.path.isfile(default_cfg)


def run_buildout(verbose=False):
    """Run a buildout.

    This will download zc.buildout if it's not available. Then it will
    bootstrap the buildout scripts and finally launch the buildout
    installation routine.

    Note that this function expects the buildout directory to be the
    current working directory.
    """
    extra_args = []
    if not verbose:
        extra_args.append('-q')

    try:
        import zc.buildout.buildout
    except ImportError:
        print "Downloading zc.buildout..."

        # Install buildout into a temporary location
        import setuptools.command.easy_install
        tmpdir = tempfile.mkdtemp()
        sys.path.append(tmpdir)
        setuptools.command.easy_install.main(extra_args +
                                             ['-mNxd', tmpdir, 'zc.buildout'])

        # Add downloaded buildout to PYTHONPATH by requiring it
        # through setuptools (this dance is necessary because the
        # temporary installation was done as multi-version).
        ws = pkg_resources.working_set
        ws.add_entry(tmpdir)
        ws.require('zc.buildout')

        import zc.buildout.buildout
        zc.buildout.buildout.main(extra_args + ['bootstrap'])
        remove_old_logger_handlers()
        shutil.rmtree(tmpdir)
    else:
        zc.buildout.buildout.main(extra_args + ['bootstrap'])
        remove_old_logger_handlers()

    print "Invoking zc.buildout..."
    
    # First we install eggbasket.  This is also done in the
    # bootstrap.py, but that is not actually called by the bootstrap
    # lines above...
    #
    # Note: we do not want to make this either quiet or verbose: quiet
    # is too quiet and verbose is too verbose. :-/
    zc.buildout.buildout.main(['install', 'eggbasket'])    
    remove_old_logger_handlers()

    # Now do the rest of the install.
    zc.buildout.buildout.main(extra_args + ['install'])
    remove_old_logger_handlers()


def remove_old_logger_handlers():
    # zc.buildout installs a new log stream on every call of
    # main(). We remove any leftover handlers to avoid multiple output
    # of same content (doubled lines etc.)
    root_logger = logging.getLogger()
    if 'zc.buildout' in root_logger.manager.loggerDict.keys():
        logger = logging.getLogger('zc.buildout')
        for handler in logger.handlers:
            logger.removeHandler(handler)
    return


def required_grok_version(versionfile):
    for line in versionfile.split('\n'):
        if line.startswith('grok ='):
            return line.split(' ')[-1]


def extend_versions_cfg(versions_cfg, for_zopectl=False):
    """Add additional package versions for versions.cfg.
    
    We only add eggs that are not already included in versions.cfg
    fetched from the release info URL (usually grok.zope.org/releaseinfo).
    """
    here = os.path.dirname(__file__)
    if for_zopectl:
        additional_eggs = open(
            os.path.join(here, 'ext_eggs_zctl.cfg'), 'rb').read()
    else:
        additional_eggs = open(
            os.path.join(here, 'ext_eggs_paster.cfg'), 'rb').read()
        
    # Create a list of already pinned eggs...
    pinned = list()
    for line in versions_cfg.split('\n'):
        if not " " in line:
            continue
        pinned.append(line.split(' ')[0].strip())

    result = ''
    for line in additional_eggs.split('\n'):
        if ' ' in line:
            if line.split(' ')[0].strip() in pinned:
                # Skip eggs already in versions.cfg...
                continue
            pass
        result += '%s\n' % line
    return result

Create Red-Hat Linux (chkconfig) rc scripts
===========================================

The zc.recipes.rhrc recipe creates Red-Hat Linux (chkconfig) rc
scripts.   It can create individual rc scripts, as well as combined rc
scripts that start multiple applications.

The recipe has a parts option that takes the names of sections that
define run scripts.  They should either:

- Define a run-script option that contains a one-line shell script, or

- The file /etc/init.d/PART should exist, where PART is the part name.

A simple example will, hopefully make this clearer. 

    >>> demo = tmpdir('demo')

    >>> write('buildout.cfg',
    ... """
    ... [buildout]
    ... parts = zoperc
    ...
    ... [zoperc]
    ... recipe = zc.recipe.rhrc
    ... parts = zope
    ... dest = %(dest)s
    ...
    ... [zope]
    ... run-script = /opt/zope/bin/zopectl -C /etc/zope.conf
    ... """ % dict(dest=demo))

Normally the recipe writes scripts to /etc/init.d.  We can override
the destination, which we've done here, using a demonstration
directory.  We specified a that it should get run-script source from
the zope section.  Here the zope section is simply a configuration
section with a run-script option set directly, but it could have been
a part with a run-script option computed from the recipe.

If we run the buildout:

    >>> print system('bin/buildout'),
    Installing zoperc.

We'll get a zoperc script in our demo directory:

    >>> ls(demo)
    -  zoperc
    
    >>> cat(demo, 'zoperc')
    #!/bin/sh 
    <BLANKLINE>
    # This script is for adminstrator convenience.  It should
    # NOT be installed as a system startup script!
    <BLANKLINE>
    <BLANKLINE>
    case $1 in 
      stop)
    <BLANKLINE>
        /opt/zope/bin/zopectl -C /etc/zope.conf $*
    <BLANKLINE>
        ;;
      restart)
    <BLANKLINE>
        ${0} stop
        sleep 1
        ${0} start
    <BLANKLINE>
        ;;
      *) 
    <BLANKLINE>
        /opt/zope/bin/zopectl -C /etc/zope.conf $*
    <BLANKLINE>
        ;;
    esac
    <BLANKLINE>

There are a couple of things to note about the generated script:

- It uses $* to pass arguments, so arguments can't be quoted.  This is 
  OK because the arguments will be simple verbs like start and stop.

- It includes a comment saying that the script shouldn't be used as a
  system startup script.

For the script to be used for system startup, we need to specify
run-level information.  We can to that using the chkconfig option:

    >>> write('buildout.cfg',
    ... """
    ... [buildout]
    ... parts = zoperc
    ...
    ... [zoperc]
    ... recipe = zc.recipe.rhrc
    ... parts = zope
    ... dest = %(dest)s
    ... chkconfig = 345 90 10
    ... chkconfigcommand = echo
    ...
    ... [zope]
    ... run-script = /opt/zope/bin/zopectl -C /etc/zope.conf
    ... """ % dict(dest=demo))

Here we included a chkconfig option saying that Zope should be started
at run levels 3, 4, and 5 and that it's start and stop ordered should
be 90 and 10.

For demonstration purposes, we don't *really* want to run chkconfig,
so we use the chkconfigcommand option to tell the recipe to run echo
instead.

    >>> print system('bin/buildout'),
    Uninstalling zoperc.
    Running uninstall recipe.
    Installing zoperc.
    --add zoperc

Now the script contains a chkconfig comment:

    >>> cat(demo, 'zoperc')
    #!/bin/sh 
    <BLANKLINE>
    # the next line is for chkconfig
    # chkconfig: 345 90 10
    # description: please, please work
    <BLANKLINE>
    <BLANKLINE>
    case $1 in 
      stop)
    <BLANKLINE>
        /opt/zope/bin/zopectl -C /etc/zope.conf $* \
          </dev/null
    <BLANKLINE>
        ;;
      restart)
    <BLANKLINE>
        ${0} stop
        sleep 1
        ${0} start
    <BLANKLINE>
        ;;
      *) 
    <BLANKLINE>
        /opt/zope/bin/zopectl -C /etc/zope.conf $* \
          </dev/null
    <BLANKLINE>
        ;;
    esac
    <BLANKLINE>

We can specify a user that the script should be run as:

    >>> write('buildout.cfg',
    ... """
    ... [buildout]
    ... parts = zoperc
    ...
    ... [zoperc]
    ... recipe = zc.recipe.rhrc
    ... parts = zope
    ... dest = %(dest)s
    ... chkconfig = 345 90 10
    ... chkconfigcommand = echo
    ... user = zope
    ...
    ... [zope]
    ... run-script = /opt/zope/bin/zopectl -C /etc/zope.conf
    ... """ % dict(dest=demo))

    >>> print system('bin/buildout'),
    Uninstalling zoperc.
    Running uninstall recipe.
    --del zoperc
    Installing zoperc.
    --add zoperc

Note the --del output.  If we hadn't set the chkconfigcommand to echo,
then chkconfig --del would have been run on the zoperc script.

    >>> cat(demo, 'zoperc')
    #!/bin/sh 
    <BLANKLINE>
    # the next line is for chkconfig
    # chkconfig: 345 90 10
    # description: please, please work
    <BLANKLINE>
    <BLANKLINE>
    if [ $(whoami) != "root" ]; then
      echo "You must be root."
      exit 1
    fi
    <BLANKLINE>
    case $1 in 
      stop)
    <BLANKLINE>
        su zope -c \
          "/opt/zope/bin/zopectl -C /etc/zope.conf $*" \
          </dev/null
    <BLANKLINE>
        ;;
      restart)
    <BLANKLINE>
        ${0} stop
        sleep 1
        ${0} start
    <BLANKLINE>
        ;;
      *) 
    <BLANKLINE>
        su zope -c \
          "/opt/zope/bin/zopectl -C /etc/zope.conf $*" \
          </dev/null
    <BLANKLINE>
        ;;
    esac
    <BLANKLINE>

Note that now the su command is used to run the script.  Because the
script is included in double quotes, it can't contain double
quotes. (The recipe makes no attempt to escape double quotes.)

Also note that now the script must be run as root, so the generated
script checks that root is running it.

If we say the user is root:

    >>> write('buildout.cfg',
    ... """
    ... [buildout]
    ... parts = zoperc
    ...
    ... [zoperc]
    ... recipe = zc.recipe.rhrc
    ... parts = zope
    ... dest = %(dest)s
    ... chkconfig = 345 90 10
    ... chkconfigcommand = echo
    ... user = root
    ...
    ... [zope]
    ... run-script = /opt/zope/bin/zopectl -C /etc/zope.conf
    ... """ % dict(dest=demo))


Then the generated script won't su, but it will still check that root
is running it:

    >>> print system('bin/buildout'),
    Uninstalling zoperc.
    Running uninstall recipe.
    --del zoperc
    Installing zoperc.
    --add zoperc

    >>> cat(demo, 'zoperc')
    #!/bin/sh 
    <BLANKLINE>
    # the next line is for chkconfig
    # chkconfig: 345 90 10
    # description: please, please work
    <BLANKLINE>
    <BLANKLINE>
    if [ $(whoami) != "root" ]; then
      echo "You must be root."
      exit 1
    fi
    <BLANKLINE>
    case $1 in 
      stop)
    <BLANKLINE>
        /opt/zope/bin/zopectl -C /etc/zope.conf $* \
          </dev/null
    <BLANKLINE>
        ;;
      restart)
    <BLANKLINE>
        ${0} stop
        sleep 1
        ${0} start
    <BLANKLINE>
        ;;
      *) 
    <BLANKLINE>
        /opt/zope/bin/zopectl -C /etc/zope.conf $* \
          </dev/null
    <BLANKLINE>
        ;;
    esac
    <BLANKLINE>

A part that defines a run script can also define environment-variable
settings to be used by the rc script by supplying an env option:

    >>> write('buildout.cfg',
    ... """
    ... [buildout]
    ... parts = zoperc
    ...
    ... [zoperc]
    ... recipe = zc.recipe.rhrc
    ... parts = zope
    ... dest = %(dest)s
    ... chkconfig = 345 90 10
    ... chkconfigcommand = echo
    ... user = zope
    ...
    ... [zope]
    ... run-script = /opt/zope/bin/zopectl -C /etc/zope.conf
    ... env = LD_LIBRARY_PATH=/opt/foolib
    ... """ % dict(dest=demo))

    >>> print system('bin/buildout'),
    Uninstalling zoperc.
    Running uninstall recipe.
    --del zoperc
    Installing zoperc.
    --add zoperc

    >>> cat(demo, 'zoperc')
    #!/bin/sh 
    <BLANKLINE>
    # the next line is for chkconfig
    # chkconfig: 345 90 10
    # description: please, please work
    <BLANKLINE>
    <BLANKLINE>
    if [ $(whoami) != "root" ]; then
      echo "You must be root."
      exit 1
    fi
    <BLANKLINE>
    case $1 in 
      stop)
    <BLANKLINE>
        LD_LIBRARY_PATH=/opt/foolib \
          su zope -c \
          "/opt/zope/bin/zopectl -C /etc/zope.conf $*" \
          </dev/null
    <BLANKLINE>
        ;;
      restart)
    <BLANKLINE>
        ${0} stop
        sleep 1
        ${0} start
    <BLANKLINE>
        ;;
      *) 
    <BLANKLINE>
        LD_LIBRARY_PATH=/opt/foolib \
          su zope -c \
          "/opt/zope/bin/zopectl -C /etc/zope.conf $*" \
          </dev/null
    <BLANKLINE>
        ;;
    esac
    <BLANKLINE>

Working with existing control scripts
-------------------------------------

In the example above, we generated a script based on a command line.
If we have a part that creates a control script on it's own, ten it
can ommit the run-script option and it's already created run script
will be used.  Let's create a run script ourselves:

    >>> write(demo, 'zope', '/opt/zope/bin/zopectl -C /etc/zope.conf $*')

Now we can remove the run-script option from the Zope section:

    >>> write('buildout.cfg',
    ... """
    ... [buildout]
    ... parts = zoperc
    ...
    ... [zoperc]
    ... recipe = zc.recipe.rhrc
    ... parts = zope
    ... dest = %(dest)s
    ... chkconfig = 345 90 10
    ... chkconfigcommand = echo
    ... user = zope
    ...
    ... [zope]
    ... env = LD_LIBRARY_PATH=/opt/foolib
    ... """ % dict(dest=demo))

    >>> print system('bin/buildout'),
    Uninstalling zoperc.
    Running uninstall recipe.
    --del zoperc
    Installing zoperc.
    --add zoperc

    >>> cat(demo, 'zoperc')
    #!/bin/sh 
    <BLANKLINE>
    # the next line is for chkconfig
    # chkconfig: 345 90 10
    # description: please, please work
    <BLANKLINE>
    <BLANKLINE>
    if [ $(whoami) != "root" ]; then
      echo "You must be root."
      exit 1
    fi
    <BLANKLINE>
    case $1 in 
      stop)
    <BLANKLINE>
        /demo/zope "$@" \
          </dev/null
    <BLANKLINE>
        ;;
      restart)
    <BLANKLINE>
        ${0} stop
        sleep 1
        ${0} start
    <BLANKLINE>
        ;;
      *) 
    <BLANKLINE>
        /demo/zope "$@" \
          </dev/null
    <BLANKLINE>
        ;;
    esac
    <BLANKLINE>

Here we just invoke the existing script.  Note that don't pay any
reflect the env or user options in the script.  When an existing
script is used, it is assumed to be complete.

    >>> import os
    >>> os.remove(join(demo, 'zope'))

Multiple processes
------------------

Sometimes, you need to start multiple processes.  You can specify
multiple parts. For example, suppose we wanted to start 2 Zope
instances:

    >>> write('buildout.cfg',
    ... """
    ... [buildout]
    ... parts = zoperc
    ...
    ... [zoperc]
    ... recipe = zc.recipe.rhrc
    ... parts = instance1 instance2
    ... dest = %(dest)s
    ... chkconfig = 345 90 10
    ... chkconfigcommand = echo
    ... user = zope
    ...
    ... [instance1]
    ... run-script = /opt/zope/bin/zopectl -C /etc/instance1.conf
    ... env = LD_LIBRARY_PATH=/opt/foolib
    ...
    ... [instance2]
    ... """ % dict(dest=demo))
    
    >>> write(demo, 'instance2', '')

Note that for instance 2, we are arranging for the script to pre-exist.

    >>> print system('bin/buildout'),
    Uninstalling zoperc.
    Running uninstall recipe.
    --del zoperc
    Installing zoperc.
    --add zoperc

    >>> cat(demo, 'zoperc')
    #!/bin/sh 
    <BLANKLINE>
    # the next line is for chkconfig
    # chkconfig: 345 90 10
    # description: please, please work
    <BLANKLINE>
    <BLANKLINE>
    if [ $(whoami) != "root" ]; then
      echo "You must be root."
      exit 1
    fi
    <BLANKLINE>
    case $1 in 
      stop)
    <BLANKLINE>
        /demo/instance2 "$@" \
          </dev/null
    <BLANKLINE>
        LD_LIBRARY_PATH=/opt/foolib \
          su zope -c \
          "/opt/zope/bin/zopectl -C /etc/instance1.conf $*" \
          </dev/null
    <BLANKLINE>
        ;;
      restart)
    <BLANKLINE>
        ${0} stop
        sleep 1
        ${0} start
    <BLANKLINE>
        ;;
      *) 
    <BLANKLINE>
        LD_LIBRARY_PATH=/opt/foolib \
          su zope -c \
          "/opt/zope/bin/zopectl -C /etc/instance1.conf $*" \
          </dev/null
    <BLANKLINE>
        /demo/instance2 "$@" \
          </dev/null
    <BLANKLINE>
        ;;
    esac
    <BLANKLINE>

Now the rc script starts both instances. Note that it stops them in
reverese order.  This isn't so important in a case like this, but
would be more important if a later script depended on an earlier one.

In addition to the zoperc script, we got scripts for the instance with
the run-script option:

    >>> ls(demo)
    -  instance2
    -  zoperc
    -  zoperc-instance1

    >>> cat(demo, 'zoperc-instance1')
    #!/bin/sh 
    <BLANKLINE>
    # This script is for adminstrator convenience.  It should
    # NOT be installed as a system startup script!
    <BLANKLINE>
    <BLANKLINE>
    if [ $(whoami) != "root" ]; then
      echo "You must be root."
      exit 1
    fi
    <BLANKLINE>
    case $1 in 
      stop)
    <BLANKLINE>
        LD_LIBRARY_PATH=/opt/foolib \
          su zope -c \
          "/opt/zope/bin/zopectl -C /etc/instance1.conf $*"
    <BLANKLINE>
        ;;
      restart)
    <BLANKLINE>
        ${0} stop
        sleep 1
        ${0} start
    <BLANKLINE>
        ;;
      *) 
    <BLANKLINE>
        LD_LIBRARY_PATH=/opt/foolib \
          su zope -c \
          "/opt/zope/bin/zopectl -C /etc/instance1.conf $*"
    <BLANKLINE>
        ;;
    esac
    <BLANKLINE>

The individual scripts don't have chkconfig information.

Deployments
-----------

The zc.recipe.rhrc recipe is designed to work with the
zc.recipe.deployment recipe.  You can specify the name of a deployment
section.  If a deployment section is specified then:

- the deployment name will be used for the rc scripts

- the user from the deployment section will be used if a user isn't
  specified in the rc script's own section.

- the rc-directory option from the deployment will be used if
  destination isn't specified.

    >>> write('buildout.cfg',
    ... """
    ... [buildout]
    ... parts = zoperc
    ...
    ... [deployment]
    ... name = acme
    ... user = acme
    ... rc-directory = %(dest)s
    ...
    ... [zoperc]
    ... recipe = zc.recipe.rhrc
    ... parts = instance1 instance2
    ... chkconfig = 345 90 10
    ... chkconfigcommand = echo
    ... deployment = deployment
    ...
    ... [instance1]
    ... run-script = /opt/zope/bin/zopectl -C /etc/instance1.conf
    ... env = LD_LIBRARY_PATH=/opt/foolib
    ...
    ... [instance2]
    ... """ % dict(dest=demo))

If a deployment is used, then any existing scripts must be
prefixed with the deployment name.  We'll rename the instance2 script
to reflect that:

    >>> os.rename(join(demo, 'instance2'), join(demo, 'acme-instance2'))

    >>> print system('bin/buildout'),
    Uninstalling zoperc.
    Running uninstall recipe.
    --del zoperc
    Installing zoperc.
    --add acme

    >>> ls(demo)
    -  acme
    -  acme-instance1
    -  acme-instance2

    >>> cat(demo, 'acme')
    #!/bin/sh 
    <BLANKLINE>
    # the next line is for chkconfig
    # chkconfig: 345 90 10
    # description: please, please work
    <BLANKLINE>
    <BLANKLINE>
    if [ $(whoami) != "root" ]; then
      echo "You must be root."
      exit 1
    fi
    <BLANKLINE>
    case $1 in 
      stop)
    <BLANKLINE>
        /demo/acme-instance2 "$@" \
          </dev/null
    <BLANKLINE>
        LD_LIBRARY_PATH=/opt/foolib \
          su acme -c \
          "/opt/zope/bin/zopectl -C /etc/instance1.conf $*" \
          </dev/null
    <BLANKLINE>
        ;;
      restart)
    <BLANKLINE>
        ${0} stop
        sleep 1
        ${0} start
    <BLANKLINE>
        ;;
      *) 
    <BLANKLINE>
        LD_LIBRARY_PATH=/opt/foolib \
          su acme -c \
          "/opt/zope/bin/zopectl -C /etc/instance1.conf $*" \
          </dev/null
    <BLANKLINE>
        /demo/acme-instance2 "$@" \
          </dev/null
    <BLANKLINE>
        ;;
    esac
    <BLANKLINE>


.. 

  Edge case, when we remove the part, we uninstall acme:

    >>> write('buildout.cfg',
    ... """
    ... [buildout]
    ... parts =
    ... """)
    >>> print system('bin/buildout'),
    Uninstalling zoperc.
    Running uninstall recipe.
    --del acme

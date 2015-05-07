"""Pipeline environment variable API."""

# -----------------------------------------------------------------------------
# Module: dpa.env
# Author: Josh Tomlinson (jtomlin)
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# Imports:
# -----------------------------------------------------------------------------

import os

# -----------------------------------------------------------------------------
# Classes:
# -----------------------------------------------------------------------------
class EnvVar(object):
    """A simple environment variable get/set API with a default value.

    This object provides a simple interface for getting and setting environment
    variables. A default value can be passed to the constructor and used when
    the variable has not been set.

    Example:: 
    
        >>> import os
        >>> from dpa.env import EnvVar
        >>> var = EnvVar('FOOBAR', 10)
        >>> var.set()
        >>> os.environ['FOOBAR']
        '10'

    """

    # -------------------------------------------------------------------------
    # Special methods:
    # -------------------------------------------------------------------------
    def __init__(self, name, default=""):
        """Constructor."""

        self._default = default
        self._name = name
        self._value = default

    # -------------------------------------------------------------------------
    def __repr__(self):
        """Same as __str__ currently."""
        return self.__str__()

    # -------------------------------------------------------------------------
    def __str__(self):
        """Returns the value of the variable as a :py:class:`str`."""
        return str(self.value)

    # -------------------------------------------------------------------------
    # Methods:
    # -------------------------------------------------------------------------
    def get(self):
        """Retrieve the value from the environment and store it.

        :rtype: :py:obj:`str`
        :returns: The value stored in the object as retrieved from the
            environment.

        This method inspects the current environment and retrieves the value
        set for the named variable and stores it in the object. The value is
        also returned for convenience.
        
        Example::
            
            >>> from dpa.env import EnvVar
            >>> var = EnvVar('SHELL')
            >>> var.get()
            '/bin/bash'
            >>> var.value
            '/bin/bash'
        
        """
        self.value = os.getenv(self.name, self.default)
        return self.value

    # -------------------------------------------------------------------------
    def set(self, shell=None):
        """Set the current value in the environment.
        
        :arg BaseShellFormatter shell: Optional
            :py:class:`dpa.shell.formatter.BaseShellFormatter` object for
            echo'ing the set command to the shell.

        This method sets the stored value of the object in the current process
        environment. 

        Example::

            >>> import os
            >>> from dpa.env import EnvVar
            >>> var = EnvVar('SHELL')
            >>> var.get()
            '/bin/bash'
            >>> os.environ['SHELL']
            '/bin/bash'
            >>> var.value = '/bin/tcsh'
            >>> var.set()
            >>> os.environ['SHELL']
            '/bin/tcsh'
        
        
        """
        os.environ[self.name] = str(self.value)
        if shell:
            print shell.set_env_var(self.name, self.value)

    # -------------------------------------------------------------------------
    def unset(self, shell=None):
        """Unset the variable from the environment.
        
        :arg BaseShellFormatter shell: Optional
            :py:class:`dpa.shell.formatter.BaseShellFormatter` object for
            echo'ing the unset command to the shell.

        This method unsets the variable matching this object's ``name`` in the
        current process environment.

        Example::

            >>> import os
            >>> from dpa.env import EnvVar
            >>> var = EnvVar('FOOBAR')
            >>> var.value = 100
            >>> var.set()
            >>> os.environ['FOOBAR']
            '100'
            >>> var.unset()
            >>> os.environ['FOOBAR']
            Traceback (most recent call last):
              ...
                raise KeyError(key)
            KeyError: 'FOOBAR'
        
        """

        try:
            del os.environ[self.name]
        except KeyError:
            pass 

        if shell:
            print shell.unset_var(self.name)
        
    # -------------------------------------------------------------------------
    # Properties:
    # -------------------------------------------------------------------------
    @property
    def default(self):
        """``property`` - The default value set for this object or
        :py:obj:`None` if no default has been set. (read only)
        
        :type: :py:obj:`str` or :py:obj:`None`
        
        """
        return self._default

    # -------------------------------------------------------------------------
    @property
    def name(self):
        """``property`` - The name of the environment variable this object
        represents. (read only)

        :type: :py:obj:`str`

        """

        return self._name

    # -------------------------------------------------------------------------
    @property
    def value(self):
        """``property`` - The value of the environment variable this object
        represents. 
        
        :type: :py:obj:`str`

        **Note**: Setting this property will not store the value in the 
        environment. Use :py:func:`set` once the ``value`` has been set.

        """

        return self._value

    # -------------------------------------------------------------------------
    @value.setter
    def value(self, val):
        self._value = val

# -----------------------------------------------------------------------------
class ListVar(EnvVar):
    """An :py:class:`EnvVar` whose value is a list.

    Methods are provided to allow interaction with these variables that resemble
    python :py:obj:`list`.

    Example::
        
        >>> import os
        >>> from dpa.env import ListVar
        >>> var = ListVar('MYLIST')
        >>> var.append('c')
        >>> var.extend(['d', 'e'])
        >>> var.prepend(['a', 'b'])
        >>> var.list
        ['a', 'b', 'c', 'd', 'e']
        >>> var.set()
        >>> os.environ['MYLIST']
        'a,b,c,d,e'

    **Note**: The class uses ``,`` as the separator. To use a different
    separator, simply create a subclass and set the ``SEPARATOR`` class
    variable. See :py:class:`PathVar` as an example.

    """

    SEPARATOR = ','

    # -------------------------------------------------------------------------
    def append(self, item):
        """Append an item to the list.

        :arg str item: The item to be appended to the list.

        """

        items = self.list
        items.append(item)
        self.value = self.__class__.SEPARATOR.join(items)

    # -------------------------------------------------------------------------
    def extend(self, in_items):
        """Extend the list with another list of items.

        :arg list in_items: A list of items for extending the list values.

        """

        items = self.list
        items.extend(in_items)
        self.value = self.__class__.SEPARATOR.join(items)

    # -------------------------------------------------------------------------
    def prepend(self, in_items):
        """Prepend a list of items.

        :arg list in_items: A list of items to prepend.

        """

        items = self.list
        in_items.extend(items)
        self.value = self.__class__.SEPARATOR.join(in_items)

    # -------------------------------------------------------------------------
    def remove(self, item):
        """Remove all instances of an item from the list.
        
        :arg str item: The item to remove.

        """

        items = self.list
        while item in items: 
            items.remove(item) # remove all instances
        self.value = self.__class__.SEPARATOR.join(items)

    # -------------------------------------------------------------------------
    @property
    def list(self):
        """``property`` - A :py:obj:`list` representation of the items stored.

        :type: :py:obj:`list`
        
        """
        if self.value:
            return self.value.split(self.__class__.SEPARATOR)
        else:
            return []

# -----------------------------------------------------------------------------
class PathVar(ListVar):
    """A :py:class:`ListVar` whose separator is :py:obj:`os.pathsep`

    This class provides a convenient way to interact with shell path variables
    like ``PATH``, ``PYTHONPATH``, and ``LD_LIBRARY_PATH``.

    """

    #: The actual value is :py:obj:`os.pathsep`
    SEPARATOR = os.pathsep

# -----------------------------------------------------------------------------
class Env(object):
    """A container for a collection of :py:class:`EnvVar` instances.

    Example::

        >>> from dpa.env import Env, EnvVar, PathVar
        >>> env = Env()
        >>> var1 = EnvVar('SHELL')
        >>> var2 = PathVar('PATH')
        >>> env.add(var1, 'shell')
        >>> env.add(var2, 'path')
        >>> env.get()
        >>> env.shell
        /bin/bash
        >>> env.path
        /opt/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:/usr/local/bin

    The object stores an arbitrary collection of :py:class:`EnvVar` instances.
    ``EnvVar`` instances can be added via the :py:func:`add` method. The add
    method accepts a ``name`` option which can be used to access the added
    ``EnvVar`` via a property syntax. See the example above.
    
    The class has :py:func:`get` and :py:func:`set` methods for performing
    operations on all conatined ``EnvVar`` instances.

    """

    # -------------------------------------------------------------------------
    # Special methods:
    # -------------------------------------------------------------------------
    def __init__(self):
        """Constructor."""
        self._vars = {}

    # -------------------------------------------------------------------------
    def __getattr__(self, attr):
        """Allows access to enclosed ``EnvVars`` via property syntax."""

        if attr in self._vars.keys():
            return self._vars[attr]
        else:
            raise EnvError("Unknown environment variable: " + attr)

    # -------------------------------------------------------------------------
    def add(self, var, name=None):
        """Add an :py:class:`EnvVar` instance to this ``Env``.

        :arg EnvVar var: The ``EnvVar`` to add.
        :arg str name: Optional name for the ``EnvVar``

        Once added, the ``EnvVar`` instance can be accessed via 
        property like syntax. Example::

            >>> from dpa.env import Env
            >>> env = Env()
            >>> env.add(EnvVar('SHELL'), name='my_shell')
            >>> env.my_shell
            '/bin/bash'

        If no name is supplied, the instance can be accessed via the actual
        environment variable name. Example::

            >>> from dpa.env import Env
            >>> env = Env()
            >>> env.add(EnvVar('SHELL'))
            >>> env.SHELL
            '/bin/bash'

        **Note**: If an :py:obj:`EnvVar` with the same name has previously been 
        added, it will be overwritten.

        """

        name = name if name else var.name
        self._vars[name] = var

    # -------------------------------------------------------------------------
    def get(self):
        """Retrieve values of contained ``EnvVar`` instances from the env.
        
        For every added :py:obj:`EnvVar`, populate the value from the current
        environment. 
        
        """
        
        # read the env variables and store them
        for var in self._vars.itervalues():
            var.get()

    # -------------------------------------------------------------------------
    def set(self, shell=None):
        """Set the values of contained ``EnvVar`` instances in the env.

        For every added :py:obj:`EnvVar`, set the value in the current
        environment

        """

        # iterate over the env variable objects and set them in the env
        for var in self._vars.itervalues():
            var.set(shell=shell)

# -----------------------------------------------------------------------------
class EnvSnapshot(Env):
    """An :py:class:`Env` that represents the complete environment.
    
    Creating an instance of this object slurps in the entire process
    environment. Useful for debugging.

    Example::
        
        >>> from dpa.env import EnvSnapshot
        >>> env = EnvSnapshot()
        >>> env.SHELL
        '/bin/bash'
    
    """

    # -------------------------------------------------------------------------
    def __init__(self):
        """Constructor."""
        super(EnvSnapshot, self).__init__()
        for (var_name, var_val) in os.environ.iteritems():
            if var_name.endswith('PATH'):
                env_var = PathVar(var_name)
            else:
                env_var = EnvVar(var_name)
            env_var.value = var_val
            self.add(env_var, name=var_name)

# -----------------------------------------------------------------------------
class EnvError(Exception):
    """A generic exception class for handling :py:obj:`Env` related errors."""
    pass


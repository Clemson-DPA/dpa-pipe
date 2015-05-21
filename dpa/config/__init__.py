"""Pipeline config file API."""

# -----------------------------------------------------------------------------
# Imports:
# -----------------------------------------------------------------------------

try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict

import os
import re
import types

from yaml import (
    dump, 
    load, 
    resolver, 
    Dumper, 
    Loader, 
    YAMLError,
)

# -----------------------------------------------------------------------------
# Globals:
# -----------------------------------------------------------------------------

OUTPUT_WIDTH = 79
OUTPUT_INDENT = 2

ALLOWED_VALUE_TYPES = (
    types.NoneType,
    types.BooleanType,
    types.IntType,
    types.LongType,
    types.FloatType,
    types.ComplexType,
    types.StringType,
    types.UnicodeType,
    types.TupleType,
    types.ListType,
)

# -----------------------------------------------------------------------------
# Classes:
# -----------------------------------------------------------------------------
class Config(OrderedDict):
    """A simple configuration file read/write object.

    Config objects are created interactively or by reading a properly formatted
    config file from disk (`YAML <http://www.yaml.org>`_  formatted). The
    objects consist of key/value pairs whereby the keys are strings and the
    values are either python built-in types like :py:obj:`int`,
    :py:obj:`float`, or :py:obj:`list` or a another ``Config`` object with it's
    own set of key/value pairs.

    In practice, ``Config`` objects are just :py:class:`OrderedDict` with 
    a few additional methods for read from and writing to disk. In addition,
    these objects provide the ability to access known values by using keys
    like properties.

    Example usage::
        
        >>> from dpa.config import Config
        >>> cfg = Config()
        >>> cfg.foo = 3
        >>> cfg.foo
        3
        >>> cfg2 = Config()
        >>> cfg2.bar = 'test'
        >>> cfg.baz = cfg2
        >>> cfg.baz.bar
        'test'
        >>> cfg.write('/tmp/test.cfg')
        >>> cfg3 = Config.read('/tmp/test.cfg')
        >>> cfg3
        foo: 3
        baz:
          bar: test

    **NOTE**: Supplying a :py:obj:`dict` (or :py:class:`OrderedDict`) to the
    constructor doesn't maintain order. Use the 'add' or 'set' methods instead.

    """

    # -------------------------------------------------------------------------
    # Class Methods:
    # -------------------------------------------------------------------------
    @staticmethod
    def composite(configs, method="override"):
        """Composite the supplied configs into a single ``Config`` object.

        :arg list configs: List of config objects or paths representing configs
            to composite.
        :arg str method: Defines the composite beavior of 'override' 
            (default) or 'update'.
        :returns: `Config` object.
        :raises: `ConfigError`
            When one of the files fails to be read.

        Example::
            
            cfg = Config.composite([path1, path2, path3])

        Conflict resolution is handled based on the order of configs
        supplied with each config overriding any key/value pairs defined
        previously.

        This method ignores non-existent files supplied.

        """
        
        if method not in ['override', 'update', 'append']:
            raise ConfigError(
                "Unrecognized composite method: " + str(method))

        composite_config = Config()

        for config in configs:

            # make sure we have a config object
            if not isinstance(config, Config):
                path = config
                if not os.path.exists(path):
                    continue
                config = Config.read(path)

            if not config:
                continue

            if method == "override":
                composite_config.override(config)
            elif method == "append":
                composite_config.append(config)
            else:
                composite_config.update(config)

        return composite_config

    # -------------------------------------------------------------------------
    @staticmethod
    def read(path):
        """Read a config file from disk.

        :arg str path: The path to the config file to read
        :returns: ``Config`` object.
        :raises ConfigError: 
            When the path does not exist.
            When the file fails to be read.

        Example::
            
            cfg = Config.read(path)

        """

        if not os.path.exists(path):
            raise ConfigError('Supplied path does not exist: "{p}"'.\
                format(p=path))
        
        try:
            return _ordered_load(file(path, 'r'))
        except YAMLError as exc:
            msg = "Problem reading config file: " + path
            if hasattr(exc, 'problem_mark'):
                mark = exc.problem_mark
                msg += "\n    Line: {line}, Column {col}".format(
                    line=mark.line + 1, col=mark.column + 1)
            raise ConfigError(msg)

    # -------------------------------------------------------------------------
    # Special methods:
    # -------------------------------------------------------------------------
    def __getattr__(self, attr):
        
        try:
            return self[attr]
        except:
            raise AttributeError, attr

    # -------------------------------------------------------------------------
    def __setattr__(self, attr, value):
        
        # HACK! allow dot notation to add key/value pairs
        if re.match("_OrderedDict__.+", attr):
            super(Config, self).__setattr__(attr, value)
        else:
            self._set(attr, value)

    # -------------------------------------------------------------------------
    def __repr__(self):
        return _ordered_dump(
            self,
            None,
            width=OUTPUT_WIDTH, 
            indent=OUTPUT_INDENT,
            default_flow_style=False,
        )

    # -------------------------------------------------------------------------
    # Methods:
    # -------------------------------------------------------------------------
    def add(self, key, value):
        """Add a key, value pair to the config object.

        :arg str key: The key to add.
        :arg value: The value to set for ``key``.

        :raises ConfigError: If the key already exists.

        Example::

            >>> from dpa.config import Config
            >>> cfg = Config()
            >>> cfg.add('foo', 3)
            >>> cfg.foo
            3

        You can also use property form to add key/value pairs::

            >>> from dpa.config import Config
            >>> cfg = Config()
            >>> cfg.foo = 3
            >>> cfg.foo
            3

        **Note**: The value must be a python primitive type or a ``Config``
        object for building nested blocks.

        """

        if key in self.keys():
            raise ConfigError('Key "{k}" exists in config. Try "set()"'.\
                format(k=key)
            )
        else:
            self._set(key, value)

    # -------------------------------------------------------------------------
    def remove(self, key):
        """Remove a key/value pair from the config.

        :arg str key: The key to remove.
        :raises KeyError: If the key does not exist.

        Example::
            
            >>> from dpa.config import Config
            >>> cfg = Config()
            >>> cfg.foo = 3
            >>> cfg.foo
            3
            >>> cfg.remove('foo')
            >>> cfg.foo
            Traceback (most recent call last):
             ...
            AttributeError: foo

        """

        try:
            del self[key]
        except KeyError:
            raise KeyError("Key '{k}' does not exist.".format(k=key))

    # -------------------------------------------------------------------------
    def set(self, key, value):
        """Set the value of an existing key.

        :arg str key: The key to set a value for.
        :arg value: The value to set for the key.
        :raises ConfigError: If the key does not exist.

        Example::
            
            >>> from dpa.config import Config
            >>> cfg = Config()
            >>> cfg.add('foo', 3)
            >>> cfg.set('foo', 4)
            >>> cfg.foo
            4

        **Note**: Using the property form automatically does an ``add``
        and a ``set``::

            >>> from dpa.config import Config
            >>> cfg = Config()
            >>> cfg.foo = 4
            >>> cfg.foo
            4

        """

        if not key in self.keys():
            raise ConfigError('Key "{k}" does not exist. Try "add()"'.\
                format(k=key)
            )

        self._set(key, value)

    # -------------------------------------------------------------------------
    def override(self, override_config):
        """Override values with the contents of another Config object.

        Similar to :py:obj:`dict.update` except the values of a nested config
        are overridden rather than updating an entire branch of the config.

        Example::

            # example configs
            >>> cfg1
            a:
              b: 1
              c: 2
              d:
                e: 3
                f: 4
            >>> cfg2
            a:
              b: 5
              d:
                f: 6
                g: 7
            
            # traditional dict style update replaces key 'a' at the top level
            >>> cfg1.update(cfg2)
            >>> cfg1
            a:
              b: 5
              d:
                f: 6
                g: 7

            # override adds new values and overrides existing values
            >>> cfg1.override(cfg2)
            a:
              b: 5
              c: 2
              d:
                e: 3
                f: 6
                g: 7

        """

        for key, new_value in override_config.iteritems():
            if isinstance(new_value, Config):
                cur_value = self.get(key, None)
                if isinstance(cur_value, Config):
                    cur_value.override(new_value)
                else:
                    self._set(key, new_value)
            else:
                self._set(key, new_value)

    # -------------------------------------------------------------------------
    def append(self, append_config):

        for key, new_value in append_config.iteritems():
            if isinstance(new_value, Config):
                cur_value = self.get(key, None)
                if isinstance(cur_value, Config):
                    cur_value.append(new_value)
                else:
                    self._set(key, new_value)
            else:
                cur_value = self.get(key, None)
                if cur_value:
                    if isinstance(cur_value, types.ListType):
                        if isinstance(new_value, types.ListType):
                            cur_value.extend(new_value)
                        else:
                            cur_value.append(new_value)
                        self._set(key, cur_value)
                    else:
                        if isinstance(new_value, types.ListType):
                            new_value.insert(0, cur_value)
                            self._set(key, new_value)
                        else:
                            self._set(key, [cur_value, new_value])
                else:
                    self._set(key, new_value)

    # -------------------------------------------------------------------------
    def write(self, path):
        """Write the config out to disk.

        :keyword path str: The path to write config

        Example::
            
            >>> from dpa.config import Config()
            >>> cfg = Config()
            >>> cfg.foo = 3
            >>> cfg.bar = 4
            >>> cfg
            foo: 3
            bar: 4
            >>> cfg.write('/tmp/test.cfg')

        """
        
        _ordered_dump(
            self,
            file(path, 'w'), 
            width=OUTPUT_WIDTH, 
            indent=OUTPUT_INDENT,
            default_flow_style=False,
        )

    # -------------------------------------------------------------------------
    # Private methods:
    # -------------------------------------------------------------------------
    def _set(self, key, value):

        if (not isinstance(value, ALLOWED_VALUE_TYPES) and
            not isinstance(value, Config)):
            raise ConfigError(
                "Can't set value for '{k}'. Type '{t}' not allowed.".\
                format(k=key, t=str(type(value).__name__))
            )

        self[key] = value

# -----------------------------------------------------------------------------
class ConfigError(Exception):
    """General exceptions raised during ``Config`` object processing."""
    pass

# -------------------------------------------------------------------------
# Private functions:
# -------------------------------------------------------------------------
def _ordered_load(stream):
    """Load the contents of a stream as ordered Config objects.
    
    See: http://stackoverflow.com/a/21912744/1174555 
    
    """

    class OrderedLoader(Loader):
        pass

    # read parsed data pairs as Config objects
    OrderedLoader.add_constructor(
        resolver.BaseResolver.DEFAULT_MAPPING_TAG,
        lambda loader, node: Config(loader.construct_pairs(node))
    )

    return load(stream, OrderedLoader)

# -------------------------------------------------------------------------
def _ordered_dump(config, stream=None, **kwargs):
    """Serialize an ordered Config object to disk.
    
    See: http://stackoverflow.com/a/21912744/1174555 
    
    """

    class OrderedDumper(Dumper):
        pass

    # dump Config objects as mapping types, in order
    def _dict_representer(dumper, config):
        return dumper.represent_mapping(
            resolver.BaseResolver.DEFAULT_MAPPING_TAG,
            config.items(),
            flow_style=False,
        )

    # dump lists inline
    def _seq_representer(dumper, seq):
        return dumper.represent_sequence(
            resolver.BaseResolver.DEFAULT_SEQUENCE_TAG,
            seq,
            flow_style=True,
        )

    OrderedDumper.add_representer(Config, _dict_representer)
    OrderedDumper.add_representer(list, _seq_representer)

    return dump(config, stream, OrderedDumper, **kwargs)

    

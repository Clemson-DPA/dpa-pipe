# ----------------------------------------------------------------------------
# Imports:
# ----------------------------------------------------------------------------

from abc import ABCMeta, abstractmethod, abstractproperty

# ----------------------------------------------------------------------------
# Classes:
# ----------------------------------------------------------------------------
class ShellFormatters(object):

    # ------------------------------------------------------------------------
    # Class variables:
    # ------------------------------------------------------------------------
    _formatters = {} 
    _default = None

    # ------------------------------------------------------------------------
    # Class methods:
    # ------------------------------------------------------------------------
    @classmethod
    def register(cls, formatter, default=False):

        if not isinstance(formatter, BaseShellFormatter):
            raise ShellFormatterError(
                "Invalid shell formatter: " + str(formatter))

        cls._formatters[formatter.name] = formatter
        if default:
            cls._default = formatter.name
        
    # ------------------------------------------------------------------------
    @classmethod
    def default(cls):
        return cls._formatters[cls._default]

    # ------------------------------------------------------------------------
    @classmethod
    def get(cls, name):
        return cls._formatters[name]

    # ------------------------------------------------------------------------
    @classmethod
    def all(cls):
        return cls._formatters.values()

# ----------------------------------------------------------------------------
class ShellFormatterError(Exception):
    pass
        
# ----------------------------------------------------------------------------
class BaseShellFormatter(object):

    __metaclass__ = ABCMeta

    # ------------------------------------------------------------------------
    # Instance methods:
    # ------------------------------------------------------------------------
    @abstractmethod
    def cd(self, directory):
        pass

    # ------------------------------------------------------------------------
    def command(self, cmd):
        return cmd
        
    # ------------------------------------------------------------------------
    @abstractmethod
    def echo(self, text):
        pass

    # ------------------------------------------------------------------------
    @abstractmethod
    def set_env_var(self, name, value):
        pass

    # ------------------------------------------------------------------------
    @abstractmethod
    def set_prompt(self, prompt):
        pass

    # ------------------------------------------------------------------------
    @abstractmethod
    def set_var(self, name, value):
        pass

    # ------------------------------------------------------------------------
    @abstractmethod
    def unset_var(self, name):
        pass

    # ------------------------------------------------------------------------
    # Properties:
    # ------------------------------------------------------------------------
    @abstractproperty
    def name(self):
        pass

# ----------------------------------------------------------------------------
class BashFormatter(BaseShellFormatter):

    # ------------------------------------------------------------------------
    # Properties:
    # ------------------------------------------------------------------------
    def cd(self, directory):
        return "cd {d}".format(d=directory)

    # ------------------------------------------------------------------------
    def echo(self, text):
        return 'echo {t}'.format(t=text) 

    # ------------------------------------------------------------------------
    def set_env_var(self, name, value):
        return 'export {n}="{v}"'.format(n=name, v=value)

    # ------------------------------------------------------------------------
    def set_prompt(self, prompt):
        return 'export PS1="{p}"'.format(p=prompt)

    # ------------------------------------------------------------------------
    def set_var(self, name, value):
        return '{n}="{v}"'.format(n=name, v=value)

    # ------------------------------------------------------------------------
    def unset_var(self, name):
        return "unset {n}".format(n=name)

    # ------------------------------------------------------------------------
    @property
    def name(self):
        return 'bash'

# ----------------------------------------------------------------------------
# On import:
# ----------------------------------------------------------------------------

# register the formatters defined here
ShellFormatters.register(BashFormatter(), default=True)


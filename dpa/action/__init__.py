
# ----------------------------------------------------------------------------
# Imports:
# ----------------------------------------------------------------------------
from abc import ABCMeta, abstractmethod
import argparse
import sys

from dpa.logging import Logger
from dpa.ptask.area import PTaskArea

# XXX consider
# sub actions
# plugins
# async actions

# ----------------------------------------------------------------------------
# Classes:
# ----------------------------------------------------------------------------
class Action(object):
    """Abstract Action class. 

    Used to define actions to be performed within the pipeline.

    """

    __metaclass__ = ABCMeta

    logging = True
    name = None
    target_type = None

    # ------------------------------------------------------------------------
    # Class methods:
    # ------------------------------------------------------------------------
    @classmethod
    def cli(cls):
        """Execute the action from a command line context. 

        Automatically sets the 'interactive' property to True.

        """

        # ----- add common options

        # log_level option for stdout
        log_level_parser = argparse.ArgumentParser(add_help=False)
        log_level_parser.add_argument(
            '--log_level',
            choices=Logger.levels,
            default=Logger.log_level,
            help="set the stdout logging level. Choices: " + str(Logger.levels),
            metavar="level",
            type=str,
        )

        # set the log level for stdout
        (parsed, remainder) = log_level_parser.parse_known_args()
        Logger.set_level(parsed.log_level)
        
        # parse the remaining args
        parser = cls.get_parser()
        cls.setup_cl_args(parser)
        kwargs = vars(parser.parse_args(remainder))

        # create the instance
        try:
            instance = cls(**kwargs)
        except Exception as e:
            import traceback
            traceback.print_exc()
            cls.get_logger().critical(str(e))
            return ActionRunStatus.FAILURE

        # because we're running on the command line, set the interactive
        # property to True
        instance.interactive = True

        # call the action
        try:
            instance()
        except Exception as e:
            import traceback
            traceback.print_exc()
            instance.status = ActionRunStatus.FAILURE
        else:
            instance.status = ActionRunStatus.SUCCESS 

        return instance.status

    # ------------------------------------------------------------------------
    @classmethod
    def get_description(cls):
        try:
            return cls.__doc__.splitlines()[0]
        except:
            return "No documentation for " + str(cls.__name__)

    # ------------------------------------------------------------------------
    @classmethod
    def get_logger(cls):
        if not hasattr(cls, '_logger'):
            cls._logger = Logger.get(".".join([cls.name, cls.target_type]))
        return cls._logger

    # ------------------------------------------------------------------------
    @classmethod
    def get_parser(cls):
        if not hasattr(cls, '_parser'):
            cls._parser = argparse.ArgumentParser(
                description=cls.get_description())
        return cls._parser

    # ------------------------------------------------------------------------
    @classmethod
    def setup_cl_args(cls, parser):
        raise NotImplementedError(
            "Action subclass {c} must implement 'setup_args' classmethod.".\
                format(c=cls.__name__)
        )

    # ------------------------------------------------------------------------
    # Special methods:
    # ------------------------------------------------------------------------
    def __init__(self, *args, **kwargs):

        assert self.__class__.name is not None, \
            "Action class 'name' attribute must be set by subclass."        

        assert self.__class__.target_type is not None, \
            "Action class 'target_type' attribute must be set by subclass."        

        self._args = args
        self._kwargs = kwargs
        self._interactive = False

    # ------------------------------------------------------------------------
    def __call__(self):

        # log the action
        if self.__class__.logging:
            self.log_action()

        # if the action is being executed interactively, prompt the user for 
        # any missing properties.
        if self.interactive:
            try:
                self.prompt()
            except ActionAborted as e:
                print "\nAborted: " + str(e) + "\n"
                self.logger.info(str(e))
                return
            except ActionError as e:
                self.logger.error(str(e))
                return

        # validate the action's properties before continuing
        try:
            self.validate() 
        except ActionError as e:
            self.logger.error(str(e))
            return

        # XXX make sure this action is in accordance with the rules

        # verify that the user wishes to continue with the validated properties
        if self.interactive:
            try:
                self.verify()
            except ActionAborted as e:
                print "\nAborted: " + str(e) + "\n"
                self.logger.info(str(e))
                return

        # execute the action
        try:
            self.execute()
        except ActionError as e:
            self.logger.error(str(e))
            self.logger.debug("Attempting to undo: " + self.full_name)
            self.undo()
            raise e
        else:
            self.notify()

    # ------------------------------------------------------------------------
    # Methods:
    # ------------------------------------------------------------------------
    @abstractmethod
    def execute(self):
        pass

    # ------------------------------------------------------------------------
    def notify(self):
        pass

    # ------------------------------------------------------------------------
    def prompt(self):
        pass

    # ------------------------------------------------------------------------
    def validate(self):
        pass

    # ------------------------------------------------------------------------
    def verify(self):
        pass

    # ------------------------------------------------------------------------
    def log_action(self):

        if not self.__class__.logging:
            return

        # try to format the args/kwargs to be readable in the log
        args_str = ""
        if len(self.args):
            args_str += ", ".join([str(a) for a in self.args])
            args_str = "args(" + args_str + ")"
        if len(self.kwargs.keys()):
            kwargs_str = ", ".join(
                sorted([k + '="' + str(v) + '"' 
                    for (k, v) in self.kwargs.items() if v])
            )
            args_str = args_str + " kwargs(" + kwargs_str + ")"

        msg = "({s})".format(s=PTaskArea.current().spec)
        msg += " " + args_str

        # log the action and its args
        self.logger.info(msg)

    # ------------------------------------------------------------------------
    @abstractmethod
    def undo(self):
        pass

    # ------------------------------------------------------------------------
    # Properties:
    # ------------------------------------------------------------------------
    @property
    def args(self):
        return self._args

    # ------------------------------------------------------------------------
    @property
    def kwargs(self):
        return self._kwargs
    
    # ------------------------------------------------------------------------
    @property
    def full_name(self):
        cls = self.__class__
        return ".".join([cls.name, cls.target_type])

    # ------------------------------------------------------------------------
    @property
    def interactive(self):
        """:returns: bool, True if action is interactive, False otherwise"""
        return self._interactive

    # ------------------------------------------------------------------------
    @interactive.setter
    def interactive(self, value):
        """Sets the interactive state of the action."""
        self._interactive = value

    # ------------------------------------------------------------------------
    @property
    def logger(self):
        return self.__class__.get_logger()

    # ------------------------------------------------------------------------
    @property
    def status(self):
        if hasattr(self, '_status'):
            return self._status
        else:
            return None

    # ------------------------------------------------------------------------
    @status.setter
    def status(self, stat):
        self._status = stat

# ------------------------------------------------------------------------
class ActionRunStatus(object):
    SUCCESS = 0
    FAILURE = 1

# ------------------------------------------------------------------------
# Exceptions:
# ------------------------------------------------------------------------
class ActionError(Exception):
    pass

# ------------------------------------------------------------------------
class ActionAborted(ActionError):
    pass


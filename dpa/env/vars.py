"""Easy access to common pipeline environment variables."""
# -----------------------------------------------------------------------------
# Module: dpa.env.vars
# Contact: Josh Tomlinson (jtomlin)
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# Imports:
# -----------------------------------------------------------------------------
from dpa.env import EnvVar, ListVar, PathVar

# -----------------------------------------------------------------------------
# Classes:
# -----------------------------------------------------------------------------
class DpaVars(object):
    """A convenience class for accessing common pipeline environment variables.
    
    The point of this class is to document and provide easy access to common
    environment variables, either specific to or used by the pipeline, via the
    :py:mod:`dpa.env` APIs. Ideally, all pipeline related environment variables
    would be defined here to prevent hardcoding their names throughout the
    codebase. This also provides a single location where reliance on
    environment variables in the pipeline can be vetted.

    Each method accepts an optional ``default`` keyword for the default value
    of the variable. All methods return instances of :py:obj:`dpa.env.EnvVar`
    (or a subclass like :py:obj:`dpa.env.PathVar`).

    Usage::

        >>> from dpa.env.vars import DpaVars
        >>> python_path = DpaVars.python_path()
    
    """

    # -------------------------------------------------------------------------
    # Class attributes:
    # -------------------------------------------------------------------------

    ld_library_path = staticmethod(
        lambda default="": PathVar('LD_LIBRARY_PATH', default)
    )
    """Returns an instance of :py:obj:`dpa.env.PathVar` for ``$LD_LIBRARY_PATH``

    The search path for binary library loading.

    """

    ld_library_path_base = staticmethod(
        lambda default="": PathVar('DPA_BASE_LD_LIRARY_PATH', default)
    )
    """Returns an instance of :py:obj:`dpa.env.PathVar` for ``$DPA_BASE_LD_LIBRARY_PATH``

    A baseline for ``$LD_LIBRARY_PATH`` used when setting/unsetting ptasks.

    """

    path = staticmethod(
        lambda default="": PathVar('PATH', default)
    )
    """Returns an instance of :py:obj:`dpa.env.PathVar` for ``$PATH``

    The search path for executables.
    
    """

    path_base = staticmethod(
        lambda default="": PathVar('DPA_BASE_PATH', default)
    )
    """Returns an instance of :py:obj:`dpa.env.PathVar` for ``$DPA_BASE_PATH``

    A baseline for ``$PATH`` used when setting/unsetting ptasks.

    """

    python_path = staticmethod(
        lambda default="": PathVar('PYTHONPATH', default)
    )
    """Returns an instance of :py:obj:`dpa.env.PathVar` for ``$PYTHONPATH``

    The search path for python packages.

    """

    python_path_base = staticmethod(
        lambda default="": PathVar('DPA_BASE_PYTHONPATH', default)
    )
    """Returns an instance of :py:obj:`dpa.env.PathVar` for ``$DPA_BASE_PYTHONPATH``

    A baseline for ``$PYTHONPATH`` used when setting/unsetting ptasks.

    """
    
    filesystem_root = staticmethod(
        lambda default="": EnvVar('DPA_FILESYSTEM_ROOT', default)
    )
    """Returns an instance of :py:obj:`dpa.env.EnvVar` for ``$DPA_FILESYSTEM_ROOT``

    The root filesystem directory for the current pipeline location.

    """
    projects_root = staticmethod(
        lambda default="": EnvVar('DPA_PROJECTS_ROOT', default)
    )
    """Returns an instance of :py:obj:`dpa.env.EnvVar` for ``$DPA_PROJECTS_ROOT``

    The root directory for dpa projects.

    """

    ptask_custom_vars = staticmethod(
        lambda default="": ListVar('DPA_PTASK_CUSTOM_VARS', default)
    )
    """Returns an instance of :py:obj:`dpa.env.ListVar` for ``$DPA_PTASK_CUSTOM_VARS``

    A list of env variable names specific to the current ptask. This list is
    used to keep track of what custom variables have been set in the ptask so
    that they can be unset when the ptask context is changed.

    """

    ptask_history_file = staticmethod(
        lambda default="~/.ptask_history": \
            EnvVar('DPA_PTASK_HISTORY_FILE', default)
    )
    """Returns an instance of a :py:obj:`dpa.env.EnvVar` for ``$DPA_PTASK_HISTORY_FILE``

    The path to a file storing the history of recently set ptasks. Set
    ``$DPA_PTASK_HISTORY_SIZE`` to set the number of recent ptasks to store in
    the history file.

    """

    ptask_history_size= staticmethod(
        lambda default=10: \
            EnvVar('DPA_PTASK_HISTORY_SIZE', default)
    )
    """Returns an instance of a :py:obj:`dpa.env.EnvVar` for ``$DPA_PTASK_HISTORY_SIZE``

    The number of ptasks to store in the ptask history file in the current 
    user's ``$DPA_PTASK_HISTORY_FILE``.

    """

    ptask_spec = staticmethod(
        lambda default="": EnvVar('DPA_PTASK_SPEC', default)
    )
    """Returns an instance of :py:obj:`dpa.env.EnvVar` for ``$DPA_PTASK_SPEC``

    Used to identify the ptask currently set in the environment.

    """

    ptask_path = staticmethod(
        lambda default="": EnvVar('DPA_PTASK_PATH', default)
    )
    """Returns an instance of :py:obj:`dpa.env.EnvVar` for ``$DPA_PTASK_PATH``

    Used to identify the path of the currently set ptask.

    """
    
    python_importer_disable = staticmethod(
        lambda default="": EnvVar('DPA_PYTHON_FINDER_DISABLE', default)
    )
    """Returns an instance of :py:obj:`dpa.env.EnvVar` for ``$DPA_PYTHON_FINDER_DISABLE``

    Setting this env variable to any value will disable the specialized DPA
    python importer which allows portions of packages to exist in multiple
    locations along the python path. For more information, see the
    documentation for ``dpa_import_hook``.
    
    """

    share_logs = staticmethod(
        lambda default="": EnvVar('DPA_SHARE_LOGS', default)
    )
    """Returns an instance of :py:obj:`dpa.env.EnvVar` for ``$DPA_SHARE_LOGS``

    The shared logging directory for dpa pipeline log files.

    """

    ptask_prompt = staticmethod(
        lambda default="": EnvVar('DPA_PTASK_PROMPT', default)
    )
    """Returns an instance of :py:obj:`dpa.env.EnvVar` for ``$DPA_PTASK_PROMPT``

    This defines the shell prompt when a ptask is set.

    """

    no_ptask_prompt = staticmethod(
        lambda default="": EnvVar('DPA_NO_PTASK_PROMPT', default)
    )
    """Returns an instance of :py:obj:`dpa.env.EnvVar` for ``$DPA_NO_PTASK_PROMPT``

    This defines the shell prompt when a ptask is not set.

    """

    data_server = staticmethod(
        lambda default="": EnvVar('DPA_DATA_SERVER', default)
    )
    """Returns an instance of :py:obj:`dpa.env.EnvVar` for ``$DPA_DATASERVER``

    This defines the server to connect to in order to query pipeline data.

    """

    location_code = staticmethod(
        lambda default="": EnvVar('DPA_LOCATION_CODE', default)
    )
    """Returns an instance of :py:obj:`dpa.env.EnvVar` for ``$DPA_LOCATION_CODE``

    This defines the physical location of the current environment.

    """


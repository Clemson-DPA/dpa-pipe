
# -----------------------------------------------------------------------------
# Imports:
# -----------------------------------------------------------------------------

import os

import dpa
from dpa.config import Config
from dpa.env import EnvVar, EnvError
from dpa.env.vars import DpaVars
from dpa.location import current_location_code
from dpa.logging import Logger
from dpa.ptask.env import PTaskEnv
from dpa.ptask.history import PTaskHistory
from dpa.ptask.spec import PTaskSpec
from dpa.shell.output import Style, Bg, Fg

# -----------------------------------------------------------------------------
# Classes:
# -----------------------------------------------------------------------------
class PTaskArea(object):

    #XXX should be a required config
    _PTASK_SET_CONFIG = 'config/ptask/set.cfg' 
    _PTASK_TYPE_FILENAME = '.ptask_type'

    # -------------------------------------------------------------------------
    # Class methods:
    # -------------------------------------------------------------------------
    @classmethod
    def create(cls, context_object):

        from dpa.ptask import PTask
        from dpa.product import Product
        from dpa.product.version import ProductVersion
        from dpa.product.representation import ProductRepresentation

        if isinstance(context_object, PTask):
            return _create_ptask_area(context_object)
        elif isinstance(
            context_object, (Product, ProductVersion, ProductRepresentation)):
            return _create_product_area(context_object)
        else:
            raise PTaskAreaError(
                "Unrecognized context object: " + str(context_object))

    # -------------------------------------------------------------------------
    @classmethod
    def current(cls):
        env = PTaskEnv.current()  
        spec = PTaskSpec.get(env.ptask_spec.value)
        try:
            return cls(spec, validate=False)
        except PTaskAreaError:
            return cls("")

    # -------------------------------------------------------------------------
    @classmethod
    def latest(cls):
        try:
            return cls(PTaskHistory().latest, validate=False)
        except PTaskAreaError:
            return cls("")

    # -------------------------------------------------------------------------
    @classmethod
    def previous(cls):
        try:
            return cls(PTaskHistory().previous, validate=False)
        except PTaskAreaError:
            return cls("")

    # -------------------------------------------------------------------------
    # Special methods:
    # -------------------------------------------------------------------------
    def __init__(self, spec, validate=True):
        super(PTaskArea, self).__init__()

        # should be a fully qualified ptask spec
        if not isinstance(spec, PTaskSpec):
            spec = PTaskSpec.get(spec)

        # XXX this is making assumptions about a 1:1 correspondence
        # between filesystem directories and ptask specs. this may not always
        # be the case. need to consider cases where the ptasks in the hierarchy
        # are spread across production disks for various reasons. at least this
        # is isolated to this class and the API should remain the same. 

        self._spec = spec
        self._base_spec = spec.base_spec
        self._product_spec = spec.product_spec
        self._fs_root = DpaVars.filesystem_root().get()
        self._root = DpaVars.projects_root().get()
        self._base = os.path.join(*spec.split(PTaskSpec.SEPARATOR))
        self._path = os.path.join(self._root, self._base)
        self._ancestor_paths = None

        if validate and not self.exists():
            raise PTaskAreaError("PTaskArea does not exist.")

    # -------------------------------------------------------------------------
    # Instance methods:
    # -------------------------------------------------------------------------
    def ancestor_paths(self, relative_file=None, include_install=False,
        install_subdir='data'):

        # defer building the list, then store it.
        if self._ancestor_paths is None:
            self._ancestor_paths = []
            if self._base is not None:
                if self._base:
                    parts = self._base.split(os.path.sep)
                    while len(parts) > 0:
                        ancestor_base = os.path.join(*parts)
                        self._ancestor_paths.append(
                            os.path.join(self._root, ancestor_base))
                        parts.pop()

                # include the project root
                self._ancestor_paths.append(self._root)

                # include the filesystem root
                self._ancestor_paths.append(self._fs_root)

        if include_install:
            install_pkg_dir = os.path.dirname(os.path.abspath(dpa.__file__))
            install_pkg_dir = os.path.join(install_pkg_dir, install_subdir)
            self._ancestor_paths.append(install_pkg_dir)

        if relative_file:
            return map(lambda path: os.path.join(path, relative_file),
                self._ancestor_paths) 
        else:
            return self._ancestor_paths

    # -------------------------------------------------------------------------
    @property
    def ancestor_specs(self):

        if hasattr(self, '_ancestor_specs'):
            return self._ancestor_specs
        
        specs = []
        spec_parts = self.spec.split(PTaskSpec.SEPARATOR)

        for i in range(0, len(spec_parts)):
            specs.append(PTaskSpec.SEPARATOR.join(spec_parts[:i]))

        specs.append(self.spec)
        specs.reverse()
        self._ancestor_specs = [s for s in specs if s]
        return self._ancestor_specs

    # -------------------------------------------------------------------------
    def config(self, config_file, composite_ancestors=False,
        composite_method="override"):

        if not composite_ancestors:
            config_path = os.path.join(self.path, config_file)
            return Config.read(config_path)

        # ---- look up the hierarchy and composite config files

        config_paths = self.ancestor_paths(
            relative_file=config_file, include_install=True)
        config_paths.reverse()
        config = Config.composite(config_paths, method=composite_method)

        return config

    # -------------------------------------------------------------------------
    def dir(self, version=None, dir_name=None, verify=True, root=None,
        path=True):

        if root:
            dir_path = os.path.join(root, self._base)
        else:
            dir_path = self.path
        
        if version:
            dir_path = os.path.join(dir_path, '.' + str(version).zfill(4))

        if dir_name:
            dir_path = os.path.join(dir_path, dir_name)

        if verify:
            if not os.path.isdir(dir_path):
                raise PTaskAreaError(
                    "Dirctory does not exist: " + str(dir_path)
                )

        return dir_path

    # -------------------------------------------------------------------------
    def dirs(self, path=False, children=False, product_dirs=False):
        """A list of directories in the area."""

        dirs = []
        products_dir = os.path.join(os.path.sep, PTaskSpec.PRODUCT_SEPARATOR)

        for dirname in os.listdir(self.path):
            full_path = os.path.join(self.path, dirname)
            if os.path.isdir(full_path):

                # if the request is for child directories only, look for the 
                # ptask type file to determine if the directory is a child
                # ptask
                if children:
                    ptask_type_file = os.path.join(
                        full_path, 
                        self.__class__._PTASK_TYPE_FILENAME,
                    )
                    if not os.path.exists(ptask_type_file):
                        
                        # allow product dirs if requested. that would be any
                        # paths with the 'products' identifier in the path.
                        if product_dirs and products_dir in full_path:
                            pass
                        else:
                            continue

                if path:
                    dirs.append(full_path)
                else:
                    dirs.append(dirname)
        return dirs

    # -------------------------------------------------------------------------
    def exists(self):
        """Returns True if the area exists on disk."""
        return os.path.exists(self.path)

    # -------------------------------------------------------------------------
    def files(self, path=False):
        """A list of files in the area."""
        files = []
        for filename in os.listdir(self.path):
            full_path = os.path.join(self.path, filename)
            if os.path.isfile(full_path):
                if path:
                    files.append(full_path)
                else:
                    files.append(filename)
        return files

    # -------------------------------------------------------------------------
    def provision(self, directory):

        path = os.path.join(self.path, directory)

        # create the directory if it doesn't exist
        if not os.path.exists(path):
            try:
                os.makedirs(path)
            except Exception as e:
                raise PTaskAreaError(
                    "Unable to provision area directory: " + str(e))

        # ensure the permissions are set properly
        try:
            os.chmod(path, 0770)
        except Exception as e:
            Logger.get().warning(
                "Unable to set permissions for ptask area provisioning: " + \
                path
            )

    # -------------------------------------------------------------------------
    def set(self, shell=None, ptask=None):

        # unset any previous custom env vars
        self._unset_custom_vars(shell=shell)

        # cd into the ptask directory
        os.chdir(self.path)
        if shell:
            print shell.cd(self.path)

        # check for config file
        self._process_config(shell=shell, ptask=ptask)

        # set the appropriate environment variables
        self.env.set(shell=shell)

        # add this spec to the history
        if ptask:
            PTaskHistory().add(self.spec)

        # set the shell prompt if preferred
        if shell:
            ptask_prompt = DpaVars.ptask_prompt().get()
            no_ptask_prompt = DpaVars.no_ptask_prompt().get()
            if ptask and ptask_prompt:
                print shell.set_prompt(ptask_prompt)    
            elif no_ptask_prompt:
                print shell.set_prompt(no_ptask_prompt)

    # -------------------------------------------------------------------------
    def set_permissions(self, mode):

        files = os.listdir(self.path)

        for file_name in sorted(files):
            path = os.path.join(self.path, file_name)
            try:
                os.chmod(path, mode)
            except Exception as e:
                Logger.get().warning(
                    "Unable to set permissions for path: {p}".format(p=path)
                )

    # -------------------------------------------------------------------------
    # Properties:
    # -------------------------------------------------------------------------
    @property
    def base_spec(self):
        return self._base_spec

    # -------------------------------------------------------------------------
    @property
    def product_spec(self):
        return self._product_spec

    # -------------------------------------------------------------------------
    @property
    def env(self):
        
        if not hasattr(self, '_env'):

            env = PTaskEnv()

            env.ptask_spec.value = self.spec
            env.ptask_path.value = self.path

            ancestor_paths = self.ancestor_paths()

            # pythonpath
            ancestor_python_paths = [os.path.join(p, 'python') 
                for p in ancestor_paths]
            env.python_path.prepend(ancestor_python_paths)

            # path
            ancestor_bin_paths = [os.path.join(p, 'bin') 
                for p in ancestor_paths]
            env.path.prepend(ancestor_bin_paths)

            # ld_library_path
            ancestor_lib_paths = [os.path.join(p, 'lib') 
                for p in ancestor_paths]
            env.ld_library_path.prepend(ancestor_lib_paths)

            self._env = env

        return self._env

    # -------------------------------------------------------------------------
    @property
    def path(self):
        return self._path

    # -------------------------------------------------------------------------
    @property
    def spec(self):
        return self._spec

    # -------------------------------------------------------------------------
    # Private instance methods
    # -------------------------------------------------------------------------
    def _process_config(self, shell=None, ptask=None):

        # get all ancestor ptask config files         
        ancestor_paths = self.ancestor_paths()
        filename = self.__class__._PTASK_SET_CONFIG

        # reverse order for compositing
        config_files = reversed(
            [os.path.join(p, filename) for p in ancestor_paths])
        config = Config.composite(config_files)

        for (key, value) in config.iteritems():
                
            # echo to shell
            if shell and key.startswith('echo'):
                try:
                    value = value.format(
                        ptask=ptask,
                        style=Style,
                        bg=Bg,
                        fg=Fg,
                    )
                    print shell.echo(value)
                except:
                    pass

            # run command
            if shell and key.startswith("cmd"):

                for cmd in value:
                    try:
                        cmd = cmd.format(ptask=ptask)
                        print shell.command(cmd)
                    except Exception as e:
                        print shell.echo("ERROR: " + str(e))

            # change directory
            elif shell and key == "cd":
                
                print shell.cd(value)

            # set env var
            elif key.startswith("env"):
                
                # the value is another config object with env vars
                for (var_key, var_value) in value.iteritems():

                    try:
                        custom_vars = self.env.custom_vars
                    except:
                        # add a variable that remembers per-ptask custom
                        # variables.  we'll use this to know what to unset when
                        # setting a new ptask.
                        self.env.add(
                            DpaVars.ptask_custom_vars(), name='custom_vars')

                    var = EnvVar(var_key) 
                    var.value = var_value
                    var.set(shell=shell)

                    # remember this variable name for unsetting
                    if not var_key in self.env.custom_vars.list:
                        self.env.custom_vars.append(var_key)

    # -------------------------------------------------------------------------
    def _unset_custom_vars(self, shell=None):

        try:
            custom_vars = self.env.custom_vars
        except EnvError:
            custom_vars = DpaVars.ptask_custom_vars()

        custom_vars.get()
        for var_name in custom_vars.list:
            if var_name:
                env_var = EnvVar(var_name) 
                env_var.unset(shell=shell)

        # unset the custom vars variable itself
        custom_vars.unset(shell=shell)

# -------------------------------------------------------------------------
def _create_ptask_area(ptask):

    parent = ptask.parent

    if parent:
        parent_area = parent.area

    if not parent or not parent_area:
        parent_area = PTaskArea("") # project root

    parent_area.provision(ptask.name)

    # write a hidden file to the area to identify the type
    area = ptask.area
    ptask_type_file = os.path.join(area.path, PTaskArea._PTASK_TYPE_FILENAME)
    with open(ptask_type_file, 'w') as fh:
        fh.write(ptask.type)

    try:
        os.chmod(ptask_type_file, 0640)
    except Exception as e:
        Logger.get().warning(
            "Unable to set permissions for ptask type file: " + \
            ptask_type_file
        )

    return area

# -------------------------------------------------------------------------
def _create_product_area(product_context):

    ptask = product_context.ptask
    ptask_area = ptask.area

    if not ptask_area.exists():
        raise PTaskAreaError(
            "PTask '{pt}' does not exists in location '{l}'.".format(
                pt=ptask.spec,
                l=current_location_code(),
            )
        )

    product_context_area = PTaskArea(product_context.spec, validate=False)
    product_spec = product_context_area.product_spec

    product_spec_parts = product_spec.split(PTaskSpec.SEPARATOR)
    directory = ""

    while product_spec_parts:
        directory = os.path.join(directory, product_spec_parts.pop(0))
        ptask_area.provision(directory)

    return PTaskArea(product_context.spec)

# -----------------------------------------------------------------------------
class PTaskAreaError(Exception):
    pass


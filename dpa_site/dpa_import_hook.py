# -----------------------------------------------------------------------------
# File: dpa_import_hook.py
# Contact: Josh Tomlinson (jtomlin)
# -----------------------------------------------------------------------------
"""PEP302 based custom import hook.

Import this file to insert a custom import hook before the built-in python
import mechanism. The import hook will look for all modules along the python
path rather than where the module's package was previously located. If a module
cannot be located or imported by the hook, the fallback is to use teh built-in
importer.

"""

# -----------------------------------------------------------------------------
# Imports:
# -----------------------------------------------------------------------------

import __builtin__
import imp
import logging
import os
import pwd
import sys

# -----------------------------------------------------------------------------
# Globals:
# -----------------------------------------------------------------------------

# A list of 
DPA_NAMESPACES = ["dpa"]

# -----------------------------------------------------------------------------
# Classes:
# -----------------------------------------------------------------------------
class DPAImporter(object):
    """Handles finding and loading 'dpa' namespaced python files.

    Unlike the built-in python importer, does not stop looking for modules when
    the package is first located along the python path. Looks for modules
    within the package namespace at the earliest point in the python path.

    """

    # -------------------------------------------------------------------------
    # Instance methods:
    # -------------------------------------------------------------------------
    def find_module(self, module_fullname, package_path=None):
        """Finder.

        :args str module_fullname: The fullname of the module to import
        :args path None: Ignored. 
            This importer doesn't care where package was previously imported.
        :returns: self (loader) if module found, None otherwise.

        """

        # get the package name from (first part of the module fullname)
        module_path_parts = module_fullname.split('.')
        package = module_path_parts[0]

        # make sure the package is in the dpa namespace before continuing
        if package not in DPA_NAMESPACES:
            return None

        # the name of the module (without the module path)
        module_name = module_path_parts.pop()
    
        # the module path as an actual path on disk
        if len(module_path_parts):
            module_path = os.path.join(*module_path_parts)
        else:
            module_path = ""

        # build a list of possible module paths for each path in PYTHONPATH
        possible_module_dirs = [
            os.path.join(path, module_path) for path in sys.path]

        try:
            (self._file, self._filename, self._description) = \
                imp.find_module(module_name, possible_module_dirs)
        except ImportError:
            # no module found, fall back to regular import
            return None
        else:
            # since this object is also the "loader" return itself
            return self
            
    # -------------------------------------------------------------------------
    def load_module(self, module_fullname):
        """Loader.

        Called by python if the find_module was successful.

        :args str module_fullname: The fullname of the module to import
        :returns: The loaded module object.
        :raises ImportError: Failed to load module.

        """

        try:
            # attempt to load the module given the information from find_module
            module = sys.modules.setdefault(
                module_fullname,
                imp.load_module(
                    module_fullname,
                    self._file,
                    self._filename,
                    self._description
                )
            )
        except ImportError as e:
            raise
        finally:
            # as noted in the imp.load_module, must close the file
            if self._file:
                self._file.close()

        # the module needs to know the loader so that reload() works
        module.__loader__ = self

        return module

# -----------------------------------------------------------------------------
# On import:
# -----------------------------------------------------------------------------

# When this file is imported, add the DPAImporter object. This allows the
# our specialized import mechanism to run before python's built-in imports

# disable if env variable is set
if 'DPA_PYTHON_FINDER_DISABLE' not in os.environ.keys():
    sys.meta_path.append(DPAImporter())


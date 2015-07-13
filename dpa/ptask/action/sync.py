# ----------------------------------------------------------------------------
# Imports:
# ----------------------------------------------------------------------------

import os

from dpa.action import Action, ActionError, ActionAborted
from dpa.config import Config
from dpa.frange import Frange
from dpa.location import Location, current_location_code
from dpa.ptask import PTask, PTaskError
from dpa.ptask.area import PTaskArea, PTaskAreaError
from dpa.ptask.cli import ParsePTaskSpecArg
from dpa.ptask.version import PTaskVersion
from dpa.shell.output import Output, Fg, Bg, Style
from dpa.sync.action import SyncAction
from dpa.user import current_username

# ----------------------------------------------------------------------------
# Globals
# ----------------------------------------------------------------------------

FILTER_RULES_CONFIG_PATH = "config/ptask/sync.cfg"

# ----------------------------------------------------------------------------
# Public classes:
# ----------------------------------------------------------------------------
class _PTaskSyncAction(Action):
    """Sync ptask areas with all the bells and whistles."""

    name = '_sync'
    target_type = 'ptask'
    
    # ------------------------------------------------------------------------
    @classmethod
    def setup_cl_args(self, parser):

        parser.add_argument(
            "source",
            action=ParsePTaskSpecArg,
            help="The spec representing the source ptask to sync from.",
            nargs="?",
        )

        parser.add_argument(
            "destination",
            action=ParsePTaskSpecArg,
            help="The spec representing the destination ptask to sync to.",
            nargs="?",
        )

        parser.add_argument(
            "--source_version",
            help="The version of the source ptask to sync from.",
            type=int,
        )

        parser.add_argument(
            "--destination_version",
            help="The version of the destination ptask to sync to.",
            type=int,
        )

        parser.add_argument(
            "--source_directory",
            help="The directory of the source ptask to sync from.",
        )

        parser.add_argument(
            "--destination_directory",
            help="The directory of the destination ptask to sync to.",
        )

        parser.add_argument(
            "-w", "--wait",
            action="store_true",
            help="Wait for the sync to finish before returning.",
        )

        parser.add_argument(
            "-f", "--force",
            help="Don't confirm before proceeding.",
            action="store_true",
        )

        parser.add_argument(
            "-d", "--delete",
            help="Delete destination files that don't exist in the source.",
            action="store_true",
        )

    # ------------------------------------------------------------------------
    def __init__(self, source, destination, source_version=None, 
        destination_version=None, source_directory=None, 
        destination_directory=None, wait=False, force=False, delete=False):

        super(_PTaskSyncAction, self).__init__(self,
            source,
            destination,
            source_version=source_version,
            destination_version=destination_version,
            source_directory=source_directory,
            destination_directory=destination_directory,
            wait=wait,
            force=force,
            delete=delete,
        )

        # set the instance properties
        self._source = source
        self._destination = destination
        self._source_version = source_version
        self._destination_version = destination_version
        self._source_directory = source_directory
        self._destination_directory = destination_directory

        # for efficiency, until proper caching is in place
        self._source_latest_version = None
        self._destination_latest_version = None

        self._wait = wait
        self._force = force
        self._delete = delete

    # ------------------------------------------------------------------------
    def execute(self):

        try:
            sync_action = SyncAction(
                source=self.source_path,
                destination=self.destination_path,
                wait=self.wait,
                includes=self.includes,
                excludes=self.excludes,
                delete=self.delete,
            )
            sync_action()
        except ActionError as e:
            raise ActionError("Unable to sync ptask: " + str(e))

    # ------------------------------------------------------------------------
    def validate(self):

        # ---- make sure the supplied specs match actual ptasks,
        #      set the properties

        try:
            self._source = PTask.get(self.source)
        except PTaskError:
            raise ActionError(
                "Unable to retrieve ptask from source argument: " + \
                    str(self.source)
            )

        try:
            self._destination = PTask.get(self.destination)
        except PTaskError:
            raise ActinError(
                "Unable to retrieve ptask from destination argument: " + \
                    str(self.destination),
                self,
            )

        self._source_latest_version = self.source.latest_version
        self._destination_latest_version = self.destination.latest_version

        # ---- make sure the ptasks are of the same type

        #if self.source.type != self.destination.type:
        #    raise ActionError(
        #        "Source and destination ptasks must be of the same type. " + \
        #            self.source.type + " != " + self.destination.type
        #    )

        # ---- if the target_type is not ptask, then the calling code has
        #      overridden the target type. make sure the source and destination
        #      types match the target type.

        target_type = self.__class__.target_type
        if target_type != "ptask":
            if self.source.type.lower() != target_type:
                raise ActionError("Source type must be a " + target_type)
            elif self.destination.type.lower() != target_type:
                raise ActionError("Destination type must a " + target_type)

        # ---- determine the source and destination versions and their locations

        if self.source_version:
            try:
                self._source_version = _get_ptask_version(
                    self.source,
                    self.source_version,
                )
            except TypeError as e:
                raise ActionError(str(e))

            source_location_code = self.source_version.location_code
        else:
            source_location_code = self.source_latest_version.location_code

        if self.destination_version:
            try:
                self._destination_version = _get_ptask_version(
                    self.destination, 
                    self.destination_version,
                )
            except TypeError as e:
                raise ActionError(str(e))

            destination_location_code = self.destination_version.location_code
        else:
            destination_location_code = \
                self.destination_latest_version.location_code

        # one of source or dest must be the current loation, unless the source
        # and destination are the same ptask. In that case, we'll assume the
        # goal is to sync the ptask to the current location or to source 
        # directories/versions within the ptask

        cur_loc_code = current_location_code()

        if self.source == self.destination:
            location_override = Location.current()
        else:
            if (source_location_code != cur_loc_code and 
                destination_location_code != cur_loc_code):
                raise ActionError(
                    "One of source or destination must be this location.",
                )
            location_override = None

        # ---- determine the source and desination paths

        self._source_path = self._get_path(
            ptask=self.source, 
            version=self.source_version, 
            latest_version=self.source_latest_version,
            directory=self.source_directory,
        )

        self._destination_path = self._get_path(
            ptask=self.destination, 
            version=self.destination_version, 
            latest_version=self.destination_latest_version,
            directory=self.destination_directory,
            location_override=location_override,
        )

        # ---- get the includes/excludes based on filter rules

        (includes, excludes) = self._get_filter_rules(self.destination)

        # exclude child ptask directories from the source
        for child in self.source.children:
            child_dir = os.path.sep + child.name
            excludes.append(child_dir)

        self._includes = includes
        self._excludes = excludes

    # ------------------------------------------------------------------------
    def verify(self):

        desc = "Description"
        ptask = "PTask"
        version = "Version"
        directory = "Directory"
        path = "Path"
        
        output = Output()
        output.header_names = [
            desc,
            ptask,
            version,
            directory,
        ]

        if self.source_version:
            source_version_disp = self.source_version.number_padded
        else:
            source_version_disp = "Latest"

        if self.destination_version:
            destination_version_disp = self.destination_version.number_padded
        else:
            destination_version_disp = "Latest"

        output.add_item(
            {
                desc: 'Source',
                ptask: self.source.spec,
                version: source_version_disp,
                directory: str(self.source_directory),
            },
            color_all=Style.bright,
        )

        output.add_item(
            {
                desc: 'Destination',
                ptask: self.destination.spec,
                version: destination_version_disp,
                directory: str(self.destination_directory),
            },
            color_all=Style.bright,
        )

        output.title = "Confirm:"
        output.dump()

        if not Output.prompt_yes_no(Style.bright + "Sync" + Style.reset):
            raise ActionAborted("Sync canceled by user.")

    # ------------------------------------------------------------------------
    def undo(self):
        pass

    # ------------------------------------------------------------------------
    # Properties:
    # ------------------------------------------------------------------------
    @property
    def source(self):
        return self._source

    # ------------------------------------------------------------------------
    @property
    def destination(self):
        return self._destination

    # ------------------------------------------------------------------------
    @property
    def source_version(self):
        return self._source_version

    # ------------------------------------------------------------------------
    @property
    def destination_version(self):
        return self._destination_version

    # ------------------------------------------------------------------------
    @property
    def source_directory(self):
        return self._source_directory

    # ------------------------------------------------------------------------
    @property
    def destination_directory(self):
        return self._destination_directory 

    # ------------------------------------------------------------------------
    @property
    def force(self):
        return self._force

    # ------------------------------------------------------------------------
    @property
    def wait(self):
        return self._wait

    # ------------------------------------------------------------------------
    @property
    def delete(self):
        return self._delete

    # ------------------------------------------------------------------------
    @property
    def source_path(self):
        return self._source_path

    # ------------------------------------------------------------------------
    @property
    def destination_path(self):
        return self._destination_path

    # ------------------------------------------------------------------------
    @property
    def includes(self):
        return self._includes

    # ------------------------------------------------------------------------
    @property
    def excludes(self):
        return self._excludes

    # ------------------------------------------------------------------------
    @property
    def source_latest_version(self):
        return self._source_latest_version

    # ------------------------------------------------------------------------
    @property
    def destination_latest_version(self):
        return self._destination_latest_version

    # ------------------------------------------------------------------------
    # Private methods:
    # ------------------------------------------------------------------------
    def _get_filter_rules(self, ptask):

        ptask_area = PTaskArea(ptask.spec, validate=False) 
        filter_config = ptask_area.config(
            FILTER_RULES_CONFIG_PATH,
            composite_ancestors=True,
        )
        
        includes = []
        excludes = []

        if 'includes' in filter_config:
            includes = filter_config.includes

        if 'excludes' in filter_config:
            excludes = filter_config.excludes
    
        return (includes, excludes)

    # ------------------------------------------------------------------------
    def _get_path(self, ptask, version=None, latest_version=None, 
        directory=None, location_override=None):

        cur_loc_code = current_location_code()

        if version:
            version_num = version.number 
        else:
            if not latest_version:
                latest_version = ptask.latest_version
            version = latest_version
            version_num = None

        if location_override:
            loc_code = location_override.code
        else:
            loc_code = version.location_code

        if loc_code == cur_loc_code:
            try:
                path = ptask.area.dir(
                    version=version_num, 
                    dir_name=directory,
                )
            except PTaskAreaError:
                raise ActionError(
                    "Path for 's' does not exist.".format(s=ptask.spec),
                )
            path += "/"
        else:
            location = version.location
            if not location.host:
                raise ActionError(
                    "Unable to sync with location '{l}'. Unknown host.".\
                        format(l=location.name)
                )
            path = ptask.area.dir(
                version=version_num, 
                dir_name=directory,
                root=location.filesystem_root,
                verify=False,
            )
            path = current_username() + "@" + location.host + ":" + path + "/"

        return path

# ----------------------------------------------------------------------------
class PTaskSyncAction(Action):
    """Sync a ptask's area from one location to the current location."""

    name = 'sync'
    target_type = 'ptask'

    # ------------------------------------------------------------------------
    @classmethod
    def setup_cl_args(self, parser):

        parser.add_argument(
            "ptask",
            action=ParsePTaskSpecArg,
            help="The spec representing the ptask to sync.",
            nargs="?",
        )

        parser.add_argument(
            "-v", "--version",
            help="The version of the ptask to sync from.",
            default=None,
        )

        parser.add_argument(
            "-f", "--force",
            help="Don't confirm before proceeding.",
            action="store_true",
        )

    # ------------------------------------------------------------------------
    def __init__(self, ptask, version=None, force=False):

        super(PTaskSyncAction, self).__init__(ptask, version)
        
        self._ptask = ptask
        self._version = version
        self._force = force

    # ------------------------------------------------------------------------
    def execute(self):

        try:

            # sync the list of remote versions to this location
            for version in self.versions:
                print "\nSyncing version: " + \
                    Style.bright + version.number_padded + Style.reset
                _sync_action = _PTaskSyncAction(
                    source=self.ptask,
                    destination=self.ptask,
                    source_version=version,
                    destination_version=version,
                )
                _sync_action()

        except ActionError as e:
            raise ActionError("Unable to sync ptask version: " + str(e))
        else:
            if self.interactive:
                print "\nSuccessfully synced: " + \
                    Style.bright + str(self.ptask.spec) + Style.reset + "\n"

    # ------------------------------------------------------------------------
    def verify(self):

        ver_range = Frange()
        ver_range.add([v.number for v in self.versions])
        versions_disp = str(ver_range)

        ptask_field = "PTask"
        versions_field = "Version(s)"
        
        output = Output()
        output.header_names = [
            ptask_field,
            versions_field,
        ]

        output.add_item(
            {
                ptask_field: self.ptask.spec,
                versions_field: versions_disp,
            },
            color_all=Style.bright,
        )

        if self.force:
            output.title = "Syncing: "
        else:
            output.title = "Confirm sync:"

        output.dump()

        if not self.force:
            if not Output.prompt_yes_no(Style.bright + "Sync" + Style.reset):
                raise ActionAborted("Sync aborted by user.")

    # ------------------------------------------------------------------------
    def undo(self):
        pass 

    # ------------------------------------------------------------------------
    def validate(self):

        cur_loc_code = current_location_code()

        try:
            self._ptask = PTask.get(self.ptask)
        except PTaskError as e:
            raise ActionError(
                "Unable to determine ptask from spec: " + str(self.ptask)
            )

        # just sync the supplied version
        if self.version:
            try:
                ptask_version = _get_ptask_version(
                    self.ptask,
                    self.version,
                )
            except TypeError as e:
                raise ActionError("Unable to retrieve ptask version: " + str(e))

            # make sure we got a version and it's not this location
            if ptask_version is None:
                raise ActionError(
                    "No ptask version matching: " + str(self.version)
                )
            # make sure the location is not this location
            elif ptask_version.location_code == cur_loc_code:
                raise ActionError("Specified version exists in this location.")
                
            versions = [ptask_version]

        # sync all ptask versions that are not in this location
        else:
            versions = [v for v in self.ptask.versions 
                if v.location_code != cur_loc_code]

        self._versions = versions

    # ------------------------------------------------------------------------
    # Properties:
    # ------------------------------------------------------------------------
    @property
    def ptask(self):
        return self._ptask

    # ------------------------------------------------------------------------
    @property
    def version(self):
        return self._version

    # ------------------------------------------------------------------------
    @property
    def versions(self):
        return self._versions

    # ------------------------------------------------------------------------
    @property
    def force(self):
        return self._force

# ----------------------------------------------------------------------------
# Utility functions:
# ----------------------------------------------------------------------------
def _get_ptask_version(ptask, version):

    if isinstance(version, PTaskVersion):
        return version

    if version == "latest":
        return ptask.latest_version

    try:
        version = int(version)
    except:
        raise TypeError("Unrecognized ptask version: " + str(version))
    else:
        return ptask.version(version)


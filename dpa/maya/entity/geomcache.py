
import os.path
import re

from dpa.action import ActionError
from dpa.action.registry import ActionRegistry
from dpa.app.entity import Entity, EntityRegistry, EntityError

# -----------------------------------------------------------------------------
class GeomcacheEntity(Entity):

    category = "geomcache"

    export_set_regex = re.compile(
        "^export_{cat}_([^_]+)_?(\d+)?$".format(cat=category), re.IGNORECASE)

    # -------------------------------------------------------------------------
    @classmethod
    def get(cls, name, session, instance=None):
        """Retrieve an entity instance from the supplied session."""

        # make sure the name exists. 
        set_names = cls.get_export_sets(session)

        fullname = name
        if instance:
            fullname += "_" + str(instance)

        matches = [s for s in set_names if s.endswith(fullname)]

        if not matches and len(matches) != 1:
            raise EntityError(
                "Could not find unique {cat} {name} instance in session.".\
                    format(cat=cls.category, name=fullname)
            )

        return cls(name, session, instance)

    # -------------------------------------------------------------------------
    # import_file

    # -------------------------------------------------------------------------
    @classmethod
    def list(cls, session):
        """Retrieve all entities of this type from the supplied session."""

        entities = []

        set_names = cls.get_export_sets(session)

        for set_name in set_names:

            name_parts = cls.export_set_regex.match(set_name)
            if not name_parts:
                continue

            (name, instance) = name_parts.groups()

            if not instance:
                instance=None
        
            entities.append(cls(name, session, instance))

        return entities

    # -------------------------------------------------------------------------
    def export(self, product_desc=None, version_note=None, fbx_export=False,
        fbx_options=None, abc_export=False, abc_options=None):
        """Export this entity to a product."""

        product_reprs = []

        if fbx_export:
            product_reprs.extend(
                self._fbx_export(fbx_options, product_desc, version_note)
            )

        if abc_export:
            product_reprs.extend(
                self._abc_export(abc_options, product_desc, version_note)
            )

        return product_reprs

    # -------------------------------------------------------------------------
    def _abc_export(self, options, product_desc, version_note):

        # ensure abc plugin in is loaded
        if not self.session.cmds.pluginInfo(
            'AbcExport', query=True, loaded=True):
            raise EntityError(
                "Unable to export '{pn}'. Maya abc plugin not loaded!".format(
                    pn=self.product_name)
            )

        file_ext = 'abc'

        product_repr = self._create_product(product_desc, version_note, file_ext)
        product_repr_dir = product_repr.directory

        export_path = os.path.join(product_repr_dir, 
            self.display_name + "." + file_ext)

        export_set = self._get_export_set()
        export_objs = self.session.cmds.sets(export_set, query=True)
        export_roots = ""
        for export_obj in export_objs:
            dag_path = self.session.cmds.ls(export_obj, l=True)[0]
            export_roots += "-root " + dag_path + " "

        frame_start = self.session.cmds.playbackOptions(query=True, minTime=True)
        frame_end = self.session.cmds.playbackOptions(query=True, maxTime=True)

        cmd = 'AbcExport -j "{roots} -fr {fs} {fe} -file {path}"'.format(
            roots=export_roots, fs=frame_start, fe=frame_end, path=export_path)

        self.session.mel.eval(cmd)

        product_repr.area.set_permissions(0660)
        
        return [product_repr]

    # -------------------------------------------------------------------------
    def _fbx_export(self, options, product_desc, version_note):

        # ensure fbx plugin in is loaded
        if not self.session.cmds.pluginInfo(
            'fbxmaya', query=True, loaded=True):
            raise EntityError(
                "Unable to export '{pn}'. Maya fbx plugin not loaded!".format(
                    pn=self.product_name)
            )

        file_ext = 'fbx'

        product_repr = self._create_product(product_desc, version_note, file_ext)
        product_repr_dir = product_repr.directory

        export_set = self._get_export_set()
        export_objs = self.session.cmds.sets(export_set, query=True)

        export_path = os.path.join(product_repr_dir, self.display_name)

        with self.session.selected(export_objs, dependencies=True):
            self.session.mel.eval(
                'FBXExport -f "{path}" -s'.format(path=export_path))

        product_repr.area.set_permissions(0660)

        return [product_repr]
    
    # -------------------------------------------------------------------------
    def _create_product(self, product_desc, version_note, file_ext):

        # use the product create action to create the product if it doesn't
        # exist.
        create_action_cls = ActionRegistry().get_action('create', 'product')
        if not create_action_cls:
            raise EntityError("Unable to find product creation action.")

        create_action = create_action_cls(
            product=self.display_name,
            ptask=self.session.ptask_version.ptask_spec,
            version=self.session.ptask_version.number,
            category=self.category,
            description=product_desc,
            file_type=file_ext,
            resolution="none",
            note=version_note,
        )

        try:
            create_action()
        except ActionError as e:
            raise EntityError("Unable to export entity: " + str(e))

        product_repr = create_action.product_repr

        return product_repr

    # -----------------------------------------------------------------------------
    def _get_export_set(self):

        # make sure the name exists. 
        set_names = self.__class__.get_export_sets(self.session)
        matches = [s for s in set_names if s.endswith(self.display_name)]

        if not matches and len(matches) != 1:
            raise EntityError("Unable to identify export set for entity!")

        return matches[0]

    # -----------------------------------------------------------------------------
    @classmethod
    def get_export_sets(cls, session):

        export_sets = []
        maya_sets = session.cmds.ls(sets=True)
        for maya_set in maya_sets:
            match = cls.export_set_regex.match(maya_set)
            if match:
                export_sets.append(maya_set)

        return export_sets

# -----------------------------------------------------------------------------
EntityRegistry().register('maya', GeomcacheEntity)


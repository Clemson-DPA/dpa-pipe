
import os.path
import re

from dpa.action import ActionError
from dpa.action.registry import ActionRegistry
from dpa.app.entity import Entity, EntityRegistry, EntityError

# options: 
# export types: obj

# -----------------------------------------------------------------------------
class GeomEntity(Entity):

    category = "geom"
    export_set_regex = re.compile(
        "^export_{cat}$".format(cat=category), re.IGNORECASE)
    name_regex = re.compile("^([^\d]+)(\d*)$")

    # -------------------------------------------------------------------------
    @classmethod
    def get(cls, name, session, instance=None):
        """Retrieve an entity instance from the supplied session."""

        # make sure the name exists. 
        obj_names = cls.get_all_objects(session)

        fullname = name
        if instance:
            fullname += instance

        if not fullname in obj_names:
            raise EntityError(
                "Could not find {cat} {name} instance in session.".format(
                    cat=cls.category, name=fullname)
            )

        return cls(name, session, instance)

    # -------------------------------------------------------------------------
    # import_file

    # -------------------------------------------------------------------------
    @classmethod
    def list(cls, session):
        """Retrieve all entities of this type from the supplied session."""

        entities = []

        obj_names = cls.get_all_objects(session)

        for obj_name in obj_names:

            name_parts = cls.name_regex.match(obj_name)
            if not name_parts:
                continue

            (name, instance) = name_parts.groups()

            if not instance:
                instance=None
        
            entities.append(cls(name, session, instance))

        return entities

    # -------------------------------------------------------------------------
    def export(self, product_desc=None, version_note=None, obj_export=False,
        obj_options=None):
        """Export this entity to a product."""

        product_reprs = []

        if obj_export:
            product_reprs.extend(
                self._obj_export(obj_options, product_desc, version_note)
            )

        return product_reprs

    # -------------------------------------------------------------------------
    def _obj_export(self, options, product_desc, version_note):

        # ensure obj plugin in is loaded
        if not self.session.cmds.pluginInfo(
            'objExport', query=True, loaded=True):
            raise EntityError(
                "Unable to export '{pn}'. Maya objExport plugin not loaded!".format(
                    pn=self.product_name)
            )

        file_ext = 'obj'

        product_repr = self._create_product(product_desc, version_note, file_ext)
        product_repr_dir = product_repr.directory

        export_path = os.path.join(product_repr_dir, 
            self.display_name + "." + file_ext)

        with self.session.selected([self.display_name], dependencies=True):
            self.session.mel.eval('CreatePolyFromPreview;')
            self.session.cmds.file(export_path, force=True, type='OBJexport', exportSelected=True,
                options='groups=0;ptgroups=0;materials=0;smoothing=1;normals=0')
            self.session.cmds.undo()

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
    @classmethod
    def get_all_objects(cls, session):

        geom_set = None
        maya_sets = session.cmds.ls(sets=True)
        for maya_set in maya_sets:
            match = cls.export_set_regex.match(maya_set)
            if match:
                geom_set = maya_set                
                break

        if not geom_set:
            return []

        entities = []

        return session.cmds.sets(geom_set, query=True)

# -----------------------------------------------------------------------------
EntityRegistry().register('maya', GeomEntity)


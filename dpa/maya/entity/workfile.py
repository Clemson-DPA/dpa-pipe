
import os.path
import re

from dpa.action import ActionError
from dpa.action.registry import ActionRegistry
from dpa.app.entity import Entity, EntityRegistry, EntityError
from dpa.maya.session import MayaSession

# -----------------------------------------------------------------------------
class WorkfileEntity(Entity):

    category = "workfile"

    export_set_regex = re.compile(
        "^export_{cat}_([^_]+)_?(\d+)?$".format(cat=category), re.IGNORECASE)

    # -------------------------------------------------------------------------
    @staticmethod
    def _get_file_base_name(session, file_path=None):

        if not file_path:
            file_path = session.cmds.file(q=True, sceneName=True)

        (file_base, file_ext) = os.path.splitext(os.path.split(file_path)[-1])

        return file_base

    # -------------------------------------------------------------------------
    @classmethod
    def get(cls, name, session, instance=None):
        """Retrieve an entity instance from the supplied session."""
    
        file_base = cls._get_file_base_name(session)

        # name has to match the base name of the file for the default
        # 'workfile' entity
        if name == file_base and not instance:
            return cls(name, session)

        # doesn't match. look for a matching export group
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
    @classmethod
    def import_file(cls, file_path, session, options=None):
        """Import a file into the session.
        
        Returns the newly imported file as an entity.
        """
        raise EntityError("Can't import workfile entity.")

    # -------------------------------------------------------------------------
    @classmethod
    def list(cls, session):
        """Retrieve all entities of this category from the supplied session."""

        entities = []

        # get the default workfile entity
        file_base = cls._get_file_base_name(session)
        entities.append(cls.get(file_base, session))

        # get the export sets
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
    def export(self, product_desc=None, version_note=None, bake_references=True):
        """Export this entity to a product."""

        file_type = 'ma'

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
            file_type=file_type,
            resolution="none",
            note=version_note,
        )

        try:
            create_action()
        except ActionError as e:
            raise EntityError("Unable to export entity: " + str(e))

        product_repr = create_action.product_repr
        product_repr_dir = product_repr.directory

        product_repr_file = os.path.join(
            product_repr_dir, self.display_name + "." + file_type)

        if self.display_name == self.__class__._get_file_base_name(self.session):
            self.session.cmds.file(
                product_repr_file, 
                type='mayaAscii', 
                exportAll=True, 
                force=True, 
                preserveReferences=(not bake_references),
            )
        else:
            export_set = self._get_export_set()
            export_objs = self.session.cmds.sets(export_set, query=True)
            with self.session.selected(export_objs, dependencies=False):
                self.session.cmds.file(
                    product_repr_file, 
                    type='mayaAscii', 
                    exportSelected=True,
                    force=True, 
                    preserveReferences=(not bake_references),
                )

        product_repr.area.set_permissions(0660)

        return [product_repr]

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
class WorkfileReferenceEntity(WorkfileEntity):

    # XXX do we need this?

    # -------------------------------------------------------------------------
    @classmethod
    def get(cls, name, session, instance=None):
        """Retrieve an entity instance from the supplied session."""

        # listing is fast, so just do that and check the name
        entities = cls.list(session)
        for entity in entities:
            if entity.name == name:
                return entity

        return None

    # -------------------------------------------------------------------------
    @classmethod
    def import_file(cls, file_path, session, options=None):
        """Import a file into the session.
        
        Returns the newly imported file as an entity.
        """

        # XXX try/except
        session.cmds.file(file_path, reference=True, prompt=False)
        name = cls._get_file_base_name(session)

        return cls.get(name, session)

    # -------------------------------------------------------------------------
    @classmethod
    def list(cls, session):
        """Retrieve all entities of this category from the supplied session."""

        entities = []
        
        referenced_files = session.cmds.file(
            list=True, reference=True, query=True)
        for ref_file in referenced_files:

            try:
                session.cmds.referenceQuery(ref_file, filename=True)
            except RuntimeError:
                continue

            name = cls._get_file_base_name(session, file_path=ref_file)
            entities.append(cls(name, session))

        return entities

    # -------------------------------------------------------------------------
    def export(self, options=None):
        """Export this entity to a product."""
        raise EntityError("Can not export reference workfile entity .")
        
    # -------------------------------------------------------------------------
    @property
    def exportable(self):
        return False

# -----------------------------------------------------------------------------
EntityRegistry().register('maya', WorkfileEntity)
EntityRegistry().register('maya', WorkfileReferenceEntity)


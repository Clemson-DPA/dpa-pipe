
import os.path

from dpa.action import ActionError
from dpa.action.registry import ActionRegistry
from dpa.app.entity import Entity, EntityRegistry, EntityError
from dpa.maya.session import MayaSession

# -----------------------------------------------------------------------------
class WorkfileEntity(Entity):

    category = "workfile"

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

        # name has to match the base name of the file for 'workfile' entities.

        if name == file_base:
            return cls(name, session)
        else:
            return None

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

        file_base = cls._get_file_base_name(session)

        # there can be only one workfile, so just use get
        entity = cls.get(file_base, session)

        if entity:
            return [entity]
        else:
            return []

    # -------------------------------------------------------------------------
    def export(self, product_desc=None, version_note=None, bake_references=True):
        """Export this entity to a product."""

        session_file = self.session.file_path

        (file_base, file_ext) = os.path.splitext(
            os.path.split(session_file)[-1])

        file_type = file_ext.lstrip(".")

        # use the product create action to create the product if it doesn't
        # exist.
        create_action_cls = ActionRegistry().get_action('create', 'product')
        if not create_action_cls:
            raise EntityError("Unable to find product creation action.")

        create_action = create_action_cls(
            product=self.name,
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
            product_repr_dir, self.name + file_ext)

        self.session.save(file_path=product_repr_file, overwrite=True)

        # XXX WTF??? rpyc + Maya == suck apparently. possibly due to maya's
        # python api not being thread safe. need to investigate, but no time
        # now. 
        """
        if bake_references:

            with MayaSession(file_path=product_repr_file, remote=True) \
                as remote_session:

                remote_session.save(bake_references=True, overwrite=True)
        """

        product_repr.area.set_permissions(0660)

        return [product_repr]

# -----------------------------------------------------------------------------
class WorkfileReferenceEntity(WorkfileEntity):

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


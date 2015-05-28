
import os.path
import re

from dpa.app.entity import EntityRegistry, EntityError
from dpa.maya.entity.base import SetBasedEntity

# -----------------------------------------------------------------------------
class WorkfileEntity(SetBasedEntity):

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

        # name has to match the base name of the file for the default
        # 'workfile' entity
        if name == file_base and not instance:
            return cls(name, session)

        # doesn't match. look for a matching export group
        return super(WorkfileEntity, cls).get(name, session, instance=instance)

    # -------------------------------------------------------------------------
    @classmethod
    def list(cls, session):
        """Retrieve all entities of this category from the supplied session."""

        entities = super(WorkfileEntity, cls).list(session)

        # get the default workfile entity
        file_base = cls._get_file_base_name(session)
        entities.append(cls.get(file_base, session))

        return entities

    # -------------------------------------------------------------------------
    def export(self, product_desc=None, version_note=None, bake_references=True):
        """Export this entity to a product."""

        file_type = 'ma'

        product_repr = self._create_product(product_desc, version_note, 
            file_type)

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
            export_objs = self.get_export_objects()
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
EntityRegistry().register('maya', WorkfileEntity)


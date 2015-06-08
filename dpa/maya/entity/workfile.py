
import os
import re

from dpa.app.entity import EntityRegistry, EntityError
from dpa.maya.entity.base import SetBasedEntity
from dpa.ptask.area import PTaskArea, PTaskAreaError

# -----------------------------------------------------------------------------
class WorkfileEntity(SetBasedEntity):

    category = "workfile"

    # -------------------------------------------------------------------------
    @staticmethod
    def _name_from_context(session):

        ptask = session.ptask
        type_lookup = ptask.types

        # hardcoding knowledge of the pipeline hierarchy here which is, in
        # general, a bad idea. However, it makes things much cleaner/easier to
        # read as far as the output products, so we'll go with it for now.
        if 'build' in type_lookup and 'stage' in type_lookup:
            base_name = type_lookup['build'] + "_" + type_lookup['stage']
        elif 'shot' in type_lookup and 'stage' in type_lookup:
            base_name = type_lookup['shot'] + "_" + type_lookup['stage']

        # fall back to the file name
        else:
            file_path = session.cmds.file(q=True, sceneName=True)
            (base_name, file_ext) = os.path.splitext(
                os.path.split(file_path)[-1])

        return base_name

    # -------------------------------------------------------------------------
    @classmethod
    def get(cls, name, session, instance=None):
        """Retrieve an entity instance from the supplied session."""
    
        base_name = cls._name_from_context(session)

        # name has to match the base name of the file for the default
        # 'workfile' entity
        if name == base_name and not instance:
            return cls(name, session)

        # doesn't match. look for a matching export group
        return super(WorkfileEntity, cls).get(name, session, instance=instance)

    # -------------------------------------------------------------------------
    @classmethod
    def list(cls, session):
        """Retrieve all entities of this category from the supplied session."""

        entities = super(WorkfileEntity, cls).list(session)

        # get the default workfile entity
        base_name = cls._name_from_context(session)
        entities.append(cls.get(base_name, session))

        return entities

    # -------------------------------------------------------------------------
    @classmethod
    def import_product_representation(cls, session, representation, *args,
        **kwargs):

        product = representation.product_version.product

        if representation.type != "ma":
            raise EntityError(
                "Don't know how to import {cat} of type {typ}".format(
                    cat=cls.category, type=representation.type)
            )

        session_file_path = session.cmds.file(q=True, sceneName=True)

        ptask_area = PTaskArea.current()
        try:
            import_dir = ptask_area.dir(dir_name='import', path=True)
        except PTaskAreaError:
            raise EntityError("Could not find import directory!")

        repr_dir = os.path.join(
            import_dir, 'global', product.name, product.category,
            representation.type, representation.resolution
        )

        # get the .ma file in the repr_dir
        repr_files = os.listdir(repr_dir)
        ma_files = [f for f in repr_files if f.endswith('.ma')]
        if len(ma_files) != 1:
            raise EntityError("Could not identify .ma file for import.")

        repr_path = os.path.join(repr_dir, ma_files[0])
        repr_path = os.path.relpath(repr_path, 
            os.path.dirname(session_file_path))

        name = representation.product_version.product.name
        instances = kwargs.get('instances', 1)
        instance_start = kwargs.get('instance_start', 0)
        exportable = kwargs.get('exportable', True)

        entities_to_create = []        

        if instances == 1 and instance_start == 0:
            session.cmds.file(
                repr_path,
                reference=True,
                groupReference=True,
                groupName=name,
                mergeNamespacesOnClash=1, 
                namespace=":"
            )
            if exportable:
                entities_to_create.append((name, name, None))
        else:
            for inst in range(instance_start, instance_start + instances):
                inst_name = name + "_" + str(inst)
                session.cmds.file(
                    repr_path,
                    reference=True,
                    groupReference=True,
                    groupName=inst_name,
                    mergeNamespacesOnClash=1, 
                    namespace=":"
                )
                if exportable:
                    entities_to_create.append((inst_name, name, inst))

        entities = []
        
        if exportable:
            for (obj_name, name, inst) in entities_to_create:
                set_name = cls.get_set_name(name, inst)
                session.cmds.sets(obj_name, name=set_name)

                entities.append(cls.get(name, session, instance=inst))
            
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

        if self.display_name == self.__class__._name_from_context(self.session):
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


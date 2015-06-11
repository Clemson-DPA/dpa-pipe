
import os.path
import re

from dpa.action import ActionError
from dpa.action.registry import ActionRegistry
from dpa.app.entity import Entity, EntityRegistry, EntityError
from dpa.ptask.area import PTaskArea, PTaskAreaError

# -----------------------------------------------------------------------------
class MayaEntity(Entity):

    # -------------------------------------------------------------------------
    @classmethod
    def get_import_file(cls, session, name, category, representation,
        relative=True):

        session_file_path = session.cmds.file(q=True, sceneName=True)

        ptask_area = PTaskArea.current()
        try:
            import_dir = ptask_area.dir(dir_name='import', path=True)
        except PTaskAreaError:
            raise EntityError("Could not find import directory!")

        import_dir = os.path.join(
            import_dir, 'global', name, category, representation.type, 
            representation.resolution
        )

        # get the file in the import_dir
        import_files = os.listdir(import_dir)
        type_files = [f for f in import_files 
            if f.endswith('.' + representation.type)]
        if len(type_files) != 1:
            raise EntityError(
                "Could not identify .{typ} file for import.".format(
                    typ=representation.type))

        import_path = os.path.join(import_dir, type_files[0])

        if relative:
            import_path = os.path.relpath(import_path, 
                os.path.dirname(session_file_path))

        return import_path

    # -------------------------------------------------------------------------
    @classmethod
    def _abc_import(cls, session, representation, *args, **kwargs):

        # XXX
        product = representation.product_version.product

        # AbcImport, for some ridiculous reason, treats imports as being 
        # relative to the project rather than the actual file that you're 
        # working in. This may bite us depending on how alembics are loaded
        # from disk, but just to get something working, don't use a relative
        # path.
        abc_file = cls.get_import_file(session, product.name, 
            product.category, representation, relative=False)
        session.mel.eval('AbcImport -m "import" "{path}"'.format(path=abc_file))

    # -------------------------------------------------------------------------
    @classmethod
    def _fbx_import(cls, session, representation, *args, **kwargs):
        
        # XXX needs to be revisitied. just making this work for now...

        product = representation.product_version.product
        fbx_file = cls.get_import_file(session, product.name, 
            product.category, representation)
        session.mel.eval('FBXImport -f "{path}" -s'.format(path=fbx_file))

# -----------------------------------------------------------------------------
class SetBasedEntity(MayaEntity):

    category = None

    # -------------------------------------------------------------------------
    @classmethod
    def set_regex(cls):

        return re.compile(
            "^export_{cat}_([\w]+)_?(\d+)?$".format(cat=cls.category),
            re.IGNORECASE
        )

    # -------------------------------------------------------------------------
    @classmethod
    def get_set_name(cls, name, inst=None):

        if inst is not None:
            set_name = "export_{cat}_{name}_{inst}".format(
                cat=cls.category,
                name=name,
                inst=inst,
            )
        else:
            set_name = "export_{cat}_{name}".format(
                cat=cls.category,
                name=name,
            )

        return set_name

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
    @classmethod
    def list(cls, session):
        """Retrieve all entities of this type from the supplied session."""

        entities = []

        set_names = cls.get_export_sets(session)

        for set_name in set_names:

            name_parts = cls.set_regex().match(set_name)
            if not name_parts:
                continue

            (name, instance) = name_parts.groups()

            if not instance:
                instance=None
        
            entities.append(cls(name, session, instance))

        return entities

    # -------------------------------------------------------------------------
    @classmethod
    def get_export_sets(cls, session):

        export_sets = []
        maya_sets = session.cmds.ls(sets=True)
        for maya_set in maya_sets:
            match = cls.set_regex().match(maya_set)
            if match:
                export_sets.append(maya_set)

        return export_sets

    # -------------------------------------------------------------------------
    def get_export_objects(self):
        
        export_set = self._get_export_set()
        return self.session.cmds.sets(export_set, query=True)

    # -----------------------------------------------------------------------------
    def _get_export_set(self):

        # make sure the name exists. 
        set_names = self.__class__.get_export_sets(self.session)
        matches = [s for s in set_names if s.endswith(self.display_name)]

        if not matches and len(matches) != 1:
            raise EntityError("Unable to identify export set for entity!")

        return matches[0]

# -----------------------------------------------------------------------------
class SetBasedWorkfileEntity(SetBasedEntity):

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

        repr_path = cls.get_import_file(session, product.name, 
            product.category, representation)

        name = product.name
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
                mergeNamespacesOnClash=True, 
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
                    mergeNamespacesOnClash=True, 
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


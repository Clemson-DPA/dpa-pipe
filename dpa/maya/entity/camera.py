
import os.path
import re

from dpa.app.entity import EntityRegistry, EntityError
from dpa.maya.entity.base import SetBasedWorkfileEntity

# -----------------------------------------------------------------------------
class CameraEntity(SetBasedWorkfileEntity):

    category = "camera"

    # -------------------------------------------------------------------------
    @classmethod
    def import_product_representation(cls, session, representation, *args,
        **kwargs):

        if representation.type == 'ma':
            super(CameraEntity, cls).import_product_representation(
                session, representation, *args, **kwargs)    
        else:
            if representation.type != 'fbx':
                raise EntityError(
                    "Unknown type for camera import: {typ}".format(
                        representation.type))

            cls._fbx_import(session, representation, *args, **kwargs)

    # -------------------------------------------------------------------------
    @classmethod
    def _fbx_import(cls, session, representation, *args, **kwargs):
        
        # XXX needs to be revisitied. just making this work for now...

        product = representation.product_version.product
        fbx_file = cls.get_import_file(session, product.name, 
            product.category, representation)
        session.mel.eval('FBXImport -f "{path}" -s'.format(path=fbx_file))

    # -------------------------------------------------------------------------
    def export(self, product_desc=None, version_note=None, fbx_export=False,
        fbx_options=None, ma_export=False, ma_options=None):
    
        product_reprs = []

        if fbx_export:
            product_reprs.extend(
                self._fbx_export(fbx_options, product_desc, version_note)
            )

        if ma_export:
            product_reprs.extend(
                self._ma_export(ma_options, product_desc, version_note)
            )

        return product_reprs

    # -------------------------------------------------------------------------
    def _fbx_export(self, options, product_desc, version_note):

        # ensure fbx plugin in is loaded
        if not self.session.cmds.pluginInfo(
            'fbxmaya', query=True, loaded=True):
            raise EntityError(
                "Unable to export '{pn}'. Maya fbx plugin not loaded!".format(
                    pn=self.product_name)
            )

        file_type = 'fbx'

        product_repr = self._create_product(product_desc, version_note,
            file_type)
        product_repr_dir = product_repr.directory

        export_objs = self.get_export_objects()

        export_path = os.path.join(product_repr_dir, self.display_name)

        with self.session.selected(export_objs, dependencies=False):
            self.session.mel.eval(
                'FBXExport -f "{path}" -s'.format(path=export_path))

        product_repr.area.set_permissions(0660)

        return [product_repr]
    
    # -------------------------------------------------------------------------
    def _ma_export(self, options, product_desc, version_note):

        file_type = 'ma'

        product_repr = self._create_product(product_desc, version_note,
            file_type)
        product_repr_dir = product_repr.directory
        product_repr_file = os.path.join(
            product_repr_dir, self.display_name + "." + file_type)

        export_objs = self.get_export_objects()

        with self.session.selected(export_objs, dependencies=False):
            self.session.cmds.file(
                product_repr_file, 
                type='mayaAscii', 
                exportSelected=True,
                force=True, 
                preserveReferences=False,
            )

        product_repr.area.set_permissions(0660)

        return [product_repr]

# -----------------------------------------------------------------------------
EntityRegistry().register('maya', CameraEntity)


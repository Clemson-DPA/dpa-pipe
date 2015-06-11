
import os.path
import re

from dpa.app.entity import EntityRegistry, EntityError
from dpa.maya.entity.base import SetBasedEntity

# options: 
# export types: obj

# -----------------------------------------------------------------------------
class GeomEntity(SetBasedEntity):

    category = "geom"

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
                "Unable to export '{pn}'. " + \
                "Maya objExport plugin not loaded!".format(
                    pn=self.product_name)
            )

        file_ext = 'obj'

        product_repr = self._create_product(product_desc, version_note, 
            file_ext)
        product_repr_dir = product_repr.directory

        export_objs = self.get_export_objects()
        export_path = os.path.join(product_repr_dir, self.display_name)

        with self.session.selected(export_objs):
            self.session.mel.eval('CreatePolyFromPreview;')
            self.session.cmds.file(export_path, force=True, type='OBJexport', exportSelected=True,
                options='groups=0;ptgroups=0;materials=0;smoothing=1;normals=0')
            self.session.cmds.undo()

        product_repr.area.set_permissions(0660)
        
        return [product_repr]

# -----------------------------------------------------------------------------
EntityRegistry().register('maya', GeomEntity)


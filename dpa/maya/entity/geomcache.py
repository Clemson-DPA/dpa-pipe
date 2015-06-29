
import os.path
import re

from dpa.app.entity import EntityRegistry, EntityError
from dpa.maya.entity.base import SetBasedEntity

# -----------------------------------------------------------------------------
class GeomcacheEntity(SetBasedEntity):

    category = "geomcache"

    # -------------------------------------------------------------------------
    @classmethod
    def import_product_representation(cls, session, representation, *args,
        **kwargs):

        if representation.type == 'fbx':
            cls._fbx_import(session, representation, *args, **kwargs)
        elif representation.type == 'abc':
            cls._abc_import(session, representation, *args, **kwargs)
        else:
            raise EntityError(
                "Unknown type for {cat} import: {typ}".format(
                    cat=cls.category, typ=representation.type))

    # -------------------------------------------------------------------------
    def export(self, product_desc=None, version_note=None, fbx_export=False,
        abc_export=False, **kwargs):
        """Export this entity to a product."""

        abc_options = kwargs.pop('abc_options', {})
        fbx_options = kwargs.pop('fbx_options', {})

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

        self.session.require_plugin('AbcExport')

        file_ext = 'abc'

        product_repr = self._create_product(product_desc, version_note, file_ext)
        product_repr_dir = product_repr.directory

        export_path = os.path.join(product_repr_dir, 
            self.display_name + "." + file_ext)

        export_objs = self.get_export_objects()

        export_roots = ""
        for export_obj in export_objs:
            dag_path = self.session.cmds.ls(export_obj, l=True)[0]
            export_roots += "-root " + dag_path + " "

        uv_write = options.pop('uv_write', True)
        if uv_write:
            uv_write_flag = "-uvWrite"
        else:
            uv_write_flag = ""

        world_space = options.pop('world_space', True)
        if world_space:
            world_space_flag = "-worldSpace"
        else:   
            world_space_flag = ""

        frame_start = self.session.cmds.playbackOptions(query=True, minTime=True)
        frame_end = self.session.cmds.playbackOptions(query=True, maxTime=True)

        cmd = 'AbcExport -j "{roots} {uw} {ws} -fr {fs} {fe} -file {path}"'.\
            format(roots=export_roots, fs=frame_start, fe=frame_end,
                path=export_path, uw=uv_write_flag, ws=world_space_flag,
            )

        self.session.mel.eval(cmd)

        product_repr.area.set_permissions(0660)
        
        return [product_repr]

    # -------------------------------------------------------------------------
    def _fbx_export(self, options, product_desc, version_note):

        self.session.require_plugin('fbxmaya')

        file_ext = 'fbx'

        product_repr = self._create_product(product_desc, version_note, file_ext)
        product_repr_dir = product_repr.directory

        export_objs = self.get_export_objects()

        export_path = os.path.join(product_repr_dir, self.display_name)

        with self.session.selected(export_objs):
            self.session.mel.eval(
                'FBXExport -f "{path}" -s'.format(path=export_path))

        product_repr.area.set_permissions(0660)

        return [product_repr]
    
# -----------------------------------------------------------------------------
EntityRegistry().register('maya', GeomcacheEntity)


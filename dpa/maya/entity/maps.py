
from dpa.app.entity import Entity, EntityError, EntityRegistry

# -----------------------------------------------------------------------------
class MapsEntity(Entity):

    category = 'maps'

    # -------------------------------------------------------------------------
    @classmethod
    def import_product_representation(cls, session, representation, *args, 
        **kwargs):
        """Import maps into the session."""

        product_version = representation.product_version
        product = product_version.product

        product_name_parts = product.name.split("_")
        maps_type = product_name_parts.pop()

        # create renderman file node
        shader_type = 'RMSGPSurface'
        shader_name = "shader_{pn}_".format(pn=product.name)
        session.cmds.shadingNode(shader_type, asShader=True, name=shader_name)

        # add renderman attributes
        add_attr = 'rmanAddAttr {sn} {attr} "";')
        session.mel.eval(add_attr.format(sn=shader_name, attr='rman__tx2dFilter')
        session.mel.eval(add_attr.format(sn=shader_name, attr='rman__tx2dSwidth')
        session.mel.eval(add_attr.format(sn=shader_name, attr='rman__tx2dTwidth')
        session.mel.eval(add_attr.format(sn=shader_name, attr='rman__tx2dLerp')
        session.mel.eval(add_attr.format(sn=shader_name, attr='rman__applysRGB')
        session.mel.eval(add_attr.format(sn=shader_name, attr='rman__udim')
        session.mel.eval(add_attr.format(sn=shader_name, attr='rman__unpremultiply')

        # type specific attributes
        if map_type in ['diff', 'diffuse', 'diffMap', 'diffuseMap']:
            # XXX
        elif map_type in ['spec', 'specular', 'specMap', 'specularMap']:
            # XXX
        elif map_type in ['bump', 'bumpMap']:
            # XXX
        elif map_type in ['disp', 'displacement', 'dispMap', 'displacementMap']:
            # XXX
        elif map_type in ['trans', 'transparency', 'transMap', 'transparencyMap']:
            # XXX
        else:
            raise EntityError("Don't know how to process map type: " + map_type)

        # set attr syntax
        set_attr = '{sn}.{attr}'

        # linearize?
        session.cmds.setAttr(
            set_attr.format(sn=shader_name, attr='rman__applysRGB'),
            kwargs.get('linearize', False)
        )

        # XXX config options:
        disable_file_load = kwargs.get('disable_file_load', False)

        # ensure filter type off
        session.cmds.setAttr(
            set_attr.format(sn=shader_name, attr='rman__tx2dFilter'), # XXX
            False, 
        )

        # set UDIM/ATLAS support to mari
        # set image path to: <import_dir>/file_base.__MAPID__.<ext>

        # hook file nodes to shader

    # -------------------------------------------------------------------------
    def export(self, *args, **kwargs):
        raise EntityError("Maya maps export not implemented.") 

# -----------------------------------------------------------------------------
EntityRegistry().register('maya', MapsEntity)


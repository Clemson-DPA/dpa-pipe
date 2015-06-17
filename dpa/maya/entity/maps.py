
from dpa.app.entity import EntityError, EntityRegistry
from dpa.maya.entity.base import MayaEntity

# -----------------------------------------------------------------------------
class MapsEntity(MayaEntity):

    category = 'maps'

    # -------------------------------------------------------------------------
    @classmethod
    def import_product_representation(cls, session, representation, *args, 
        **kwargs):
        """Import maps into the session."""

        session.require_plugin('RenderMan_for_Maya')

        product_version = representation.product_version
        product = product_version.product

        product_name_parts = product.name.split("_")
        maps_type = product_name_parts.pop()

        # ---- file read node

        file_node_name = "file_{pn}".format(pn=product.name)
        file_node = session.cmds.shadingNode('file', asTexture=True,
            name=file_node_name)

        # set UDIM/ATLAS support to mari
        current_file = session.cmds.file(q=True, sceneName=True)
        import_base = cls.get_import_file_common_base(session, 
            product.name, product.category, representation,
            relative_to=current_file
        )
        map_path = import_base + '._MAPID_.' + representation.type
        session.cmds.setAttr(file_node + '.fileTextureName', map_path,
            type="string")
        session.cmds.setAttr(file_node + '.filterType', 0)
        session.cmds.setAttr(file_node + '.colorProfile', 2) 

        # add renderman attributes
        add_attr = 'rmanAddAttr {fn} {attr} "";'
        session.mel.eval(add_attr.format(fn=file_node, attr='rman__tx2dFilter'))
        session.mel.eval(add_attr.format(fn=file_node, attr='rman__tx2dSwidth'))
        session.mel.eval(add_attr.format(fn=file_node, attr='rman__tx2dTwidth'))
        session.mel.eval(add_attr.format(fn=file_node, attr='rman__tx2dLerp'))
        session.mel.eval(add_attr.format(fn=file_node, attr='rman__applysRGB'))
        session.mel.eval(add_attr.format(fn=file_node, attr='rman__udim'))
        session.mel.eval(add_attr.format(fn=file_node,
            attr='rman__unpremultiply'))

        # set udim lookup to 'mari'
        session.cmds.setAttr(file_node + '.rman__udim', 'mari', type='string')

        # ---- config options

        # linearize?
        session.cmds.setAttr(file_node + '.rman__applysRGB',
            kwargs.get('linearize', False))

        # disable file load 
        session.cmds.setAttr(file_node + '.disableFileLoad',
            kwargs.get('disable_file_load', False))

        # ---- create surface shader 

        shader_type = 'RMSGPSurface'
        shader_name = "shader_{pn}".format(pn=product.name)
        session.cmds.shadingNode(shader_type, asShader=True, name=shader_name)

        # ---- type specific attributes and connections

        connect = kwargs.get('connect', True)

        # DIFFUSE
        if maps_type in ['diff', 'diffuse', 'diffMap', 'diffuseMap']:

            if connect:
                session.cmds.connectAttr(file_node + '.outColor',
                    shader_name + '.surfaceColor')

        # SPECULAR
        elif maps_type in ['spec', 'specular', 'specMap', 'specularMap']:

            if connect:
                session.cmds.connectAttr(file_node + '.outColor',
                    shader_name + '.specularColor')

        # BUMP
        elif maps_type in ['bump', 'bumpMap']:

            session.cmds.setAttr(file_node + '.alphaIsLuminance', 1)

            session.mel.eval('rmanSetAttr {sn} {attr} 0'.format(
                sn=shader_name, attr='enableDisplacement'))

            session.cmds.setAttr(shader_name + '.bumpAmount', 1.0)

            if connect:
                session.cmds.connectAttr( file_node + '.outColor.outColorR', 
                    shader_name + '.bumpScalar')

        # TRANSPARENCY
        elif maps_type in ['trans', 'transparency', 'transMap',
            'transparencyMap']:

            session.cmds.setAttr(file_node + '.alphaIsLuminance', 1)

            if connect:
                session.cmds.connectAttr(file_node + '.outColor',
                    shader_name + '.transparency')

        # DISPLACEMENT
        elif maps_type in ['disp', 'displacement', 'dispMap', 'displacementMap']:

            add_attr = 'rmanAddAttr {sn} {attr} "";'
            session.mel.eval(add_attr.format(sn=shader_name, 
                    attr='rman__riattr__displacementbound_sphere'))

            session.mel.eval(add_attr.format(sn=shader_name,
                    attr='rman__riattr__displacementbound_coordinatesystem'))

            session.mel.eval(add_attr.format(sn=shader_name,
                    attr='rman__riattr__trace_displacements'))

            if connect:
                session.cmds.connectAttr(file_node + '.outColor.outColorR',
                    shader_name + '.displacementScalar')

            session.cmds.setAttr(shader_name + '.displacementAmount', 1.0)

            session.cmds.setAttr(
                shader_name + ".rman__riattr__displacementbound_sphere", 1.0)

            session.mel.eval('rmanSetAttr {sn} {val} 0;'.format(sn=shader_name,
                    val='enableDisplacement'))

        # UNKNOWN
        else:
            raise EntityError("Don't know how to process map type: " + maps_type)

    # -------------------------------------------------------------------------
    def export(self, *args, **kwargs):
        raise EntityError("Maya maps export not implemented.") 

# -----------------------------------------------------------------------------
EntityRegistry().register('maya', MapsEntity)


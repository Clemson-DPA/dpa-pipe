
import os.path
import re

from dpa.app.entity import Entity, EntityRegistry, EntityError

# -----------------------------------------------------------------------------
class GeomcacheEntity(Entity):

    category = "geomcache"

    # -------------------------------------------------------------------------
    @classmethod
    def import_product_representation(cls, session, representation, *args,
        **kwargs):
        """Import this entity to the session.""" 

        if representation.type == 'abc':
            cls._abc_import(session, representation, *args, **kwargs)
        else:
            raise EntityError(
                "Unknown type for {cat} import: {typ}".format(
                    cat=cls.category, typ=representation.type))

    # -------------------------------------------------------------------------
    @classmethod
    def _abc_import(cls, session, representation, *args, **kwargs):

        product = representation.product_version.product
        abc_file = cls.get_import_file(session, product.name, 
            product.category, representation)

        alembic_node = session.hou.node('obj').createNode('alembicarchive')
        alembic_node.setParms({"fileName": abc_file})
        alembic_node.parm('buildHierarchy').pressButton()


    # -------------------------------------------------------------------------
    def export(self, *args, **kwargs):
        """Export this entity to a product.""" 
        
        raise EntityError("Houdini geom export not yet supported.")

# -----------------------------------------------------------------------------
EntityRegistry().register('houdini', GeomcacheEntity)


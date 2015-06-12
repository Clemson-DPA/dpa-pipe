
from dpa.app.entity import Entity, EntityError

# -----------------------------------------------------------------------------
class GeomEntity(Entity):

    category = 'geom'

    # -------------------------------------------------------------------------
    @classmethod
    def import_product_representation(cls, session, representation, *args, 
        **kwargs):

        if self.session.mari.projects.current():
            raise EntityError("Cannot have a project open when importing.")

        # XXX import config - config/mari/geom/import_obj.cfg

        project = self._create_project()   
        self._save_archive_reopen(project)

    # -------------------------------------------------------------------------
    def export(self, *args, **kwargs):
        """Export this entity to a product.""" 
        
        raise EntityError("Mari geom export not supported.")

    # -------------------------------------------------------------------------
    def _create_project(self, 

# -----------------------------------------------------------------------------
EntityRegistry().register('mari', GeomEntity)


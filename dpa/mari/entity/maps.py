
import os.path
import re

from dpa.action import ActionError
from dpa.action.registry import ActionRegistry
from dpa.app.entity import Entity, EntityRegistry, EntityError

# -----------------------------------------------------------------------------
class MapsEntity(Entity):

    category = "maps"

    #-------------------------------------------------------------------------
    def export(self, product_desc=None, version_note=None, tif_export=True,
        tif_options=None, tex_export=False, tex_options=None):
        """Export this entity to a product."""

        product_reprs = []

        if tif_export:
            product_reprs.extend(
                self._tif_export(tif_options, product_desc, version_note)
            )

        if tex_export:
            product_reprs.extend(
                self._tex_export(tex_options, product_desc, version_note)
            )

        return product_reprs

    # -------------------------------------------------------------------------
    def _tif_export(self, options, product_desc, version_note):

        file_ext = 'tif'

        product_repr = self._create_product(product_desc, version_note, file_ext)
        product_repr_dir = product_repr.directory

        export_objs = self.get_export_channels()

        export_path = os.path.join(product_repr_dir, self.display_name)

        product_repr.area.set_permissions(0660)
        
        return [product_repr]  

    # -------------------------------------------------------------------------
    def _tex_export(self, options, product_desc, version_note):

        file_ext = 'tif'

        product_repr = self._create_product(product_desc, version_note, file_ext)
        product_repr_dir = product_repr.directory

        export_objs = self.get_export_channels()

        export_path = os.path.join(product_repr_dir, self.display_name)

        product_repr.area.set_permissions(0660)
        
        return [product_repr]  

    # -------------------------------------------------------------------------
    # Really only implemented...for the instance stuff...which I'm unclear of atm
    @classmethod
    def set_regex(cls):
        return re.compile("^([^_]+)_?(\d+)?$",re.IGNORECASE)

    # -------------------------------------------------------------------------
    @classmethod
    def get(cls, name, session, instance=None):
        """Retrieve an entity instance from the supplied session."""

        # make sure the name exists. 
        channels = cls.get_export_channels(session)

        fullname = name
        if instance:
            fullname += "_" + str(instance)

        matches = [s for s in channels if s.endswith(fullname)]

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

        channels = cls.get_export_channels(session)

        for ch in channels:
            print ch
            print ch.name()
            name_parts = cls.set_regex().match(ch.name())
            if not name_parts:
                continue

            (name, instance) = name_parts.groups()

            if not instance:
                instance=None
        
            entities.append(cls(name, session, instance))

        return entities

    # -------------------------------------------------------------------------
    @classmethod
    def get_export_channels(cls, session):

        geo = session.mari.geo.current()

        if geo is None:
            raise EntityError("Please select an object to export a channel from for this entity.")

        export_channels = geo.channelList()

        if not export_channels:
            raise EntityError("There are no channels to export for this entity.")

        return export_channels


# -----------------------------------------------------------------------------
EntityRegistry().register('mari', MapsEntity)


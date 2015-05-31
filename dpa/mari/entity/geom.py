
import os.path
import re

from dpa.action import ActionError
from dpa.action.registry import ActionRegistry
from dpa.app.entity import Entity, EntityRegistry, EntityError

# -----------------------------------------------------------------------------
class GeomEntity(Entity):

    category = "geom"

    # -------------------------------------------------------------------------
    @classmethod
    def get(cls, name, session, instance=None):
        """Retrieve an entity instance from the supplied session."""

        # make sure the name exists. 
        set_names = cls.get_export_sets(session)

        fullname = name
        if instance:
            fullname += "_" + str(instance)

        if not set_names:
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
        """Retrieve all entities of this type from available products"""

        entities = []

        set_names = cls.get_export_sets(session)

        if not set_names: 
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
        return []
    # -------------------------------------------------------------------------
    def get_export_objects(self):
        return []
    # -----------------------------------------------------------------------------
    def _get_import_set(self):
        return []

# -----------------------------------------------------------------------------
EntityRegistry().register('mari', GeomEntity)

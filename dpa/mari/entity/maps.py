
import os
import re
import sys

from dpa.action import ActionError
from dpa.action.registry import ActionRegistry
from dpa.app.entity import Entity, EntityRegistry, EntityError

# -----------------------------------------------------------------------------
class MapsEntity(Entity):

    category = "maps"
    importable = False

    #-------------------------------------------------------------------------
    def export(self, product_desc=None, version_note=None, tif_export=True,
        tif_options=None, tex_export=False, tex_options=None):
        """Export this entity to a product."""

        product_reprs = []

        # should ALWAYS be called
        if tif_export:
            product_reprs.extend(
                self._tif_export(tif_options, product_desc, version_note)
            )

        # this is actually optional, reliant on tifs
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

        export_path = os.path.join(product_repr_dir, self.display_name + 
            '.$UDIM.' + file_ext)

        self.__class__.do_export(self.session, self.display_name, export_path)

        product_repr.area.set_permissions(0660)
        
        return [product_repr]  

    # -------------------------------------------------------------------------
    def _tex_export(self, options, product_desc, version_note):

        file_ext = 'tex'

        product_repr = self._create_product(product_desc, version_note, file_ext)
        product_repr_dir = product_repr.directory

        self.__class__.convert_to_tex(self.session, product_repr_dir)

        product_repr.area.set_permissions(0660)
        
        return [product_repr]  

    # -------------------------------------------------------------------------
    @classmethod
    def get(cls, name, session, instance=None):
        """Retrieve an entity instance from the supplied session."""

        # make sure the name exists. 
        channels = cls.get_export_channels(session)
        matches = [s for s in channels if s.endswith(name)]

        if not matches and len(matches) != 1:
            raise EntityError(
                "Could not find unique channel {name} instance in session.".\
                    format(cat=cls.category, name=name)
            )

        return cls(name, session, instance)

    # -------------------------------------------------------------------------
    @classmethod
    def list(cls, session):
        """Retrieve all entities of this type from the supplied session."""

        entities = []

        channels = cls.get_export_channels(session)

        for ch in channels:
            entities.append(cls(ch.name(), session))

        return entities

    # -------------------------------------------------------------------------
    @classmethod
    def get_export_channels(cls, session):
        try:
            geo = session.mari.geo.current()
        except:
            raise EntityError("No project open; please open one.")
        else:
            if geo is None:
                raise EntityError("Please select an object to export a "
                    "channel from for this entity.")

            export_channels = geo.channelList()

            if not export_channels:
                raise EntityError("There are no channels to export for "
                    "this entity.")

            return export_channels

    # -------------------------------------------------------------------------
    @classmethod
    def do_export(cls, session, name, export_path):
        # mari specific
        session.mari.history.startMacro('Exporting ' + name + ' Channel')

        try:
            ch = session.mari.geo.current().channel(name)
            snapshot = ch.createSnapshot('Backup pre-flattening', name)
            layer = ch.flatten()
            imgset = layer.imageSet()
            imgset.exportImages(export_path)

            session.mari.history.stopMacro()

            ch.revertToSnapshot(snapshot)
            ch.deleteSnapshot(snapshot)

        except:
            session.mari.history.stopMacro()
            session.mari.history.undo()
            session.mari.utils.message("Error with tif texture export.")

        # -------------------------------------------------------------------------
    @classmethod
    def convert_to_tex(cls, session, export_path):
        tif_dir = export_path.replace('/tex/', '/tif/')
        if not os.path.exists(tif_dir):
            raise EntityError("TIF files must exist prior to TEX conversion.")

        i = 1 # processing index
        try:
        # read directory of existing 
            tif_files = [f for f in os.listdir(tif_dir) if f.endswith('.tif')]
            session.mari.app.startProcessing('Converting existing tif to tex', 
                len(tif_files) + 1, True)
            session.mari.app.setProgress(0)

            for tif in tif_files:
                session.mari.app.setProgress(i)
                i += 1

                tex = tif.replace('.tif', '.tex')
                txcmd = 'txmake -mode periodic %s %s' % (os.path.join(tif_dir, tif), 
                    os.path.join(export_path, tex))

                os.system(txcmd)

            session.mari.app.stopProcessing()

        except:
            session.mari.app.stopProcessing()
            session.mari.utils.message("Error with conversion. "
                "Please make sure folders are chmodded correctly/files exist.")

    # -------------------------------------------------------------------------
    @classmethod
    def get_resolution(cls, session, imgset):
        # this would be nice, but the issue is that mari patches
        # can have various sizes, so it cant be applied globally to a channel
        pass

    # -------------------------------------------------------------------------
    def get_export_objects(self):
        return self._get_export_channels()

    # -------------------------------------------------------------------------
    def _get_export_channels(self):
        return self.__class__.get_export_channels(self.session)

# -----------------------------------------------------------------------------
EntityRegistry().register('mari', MapsEntity)


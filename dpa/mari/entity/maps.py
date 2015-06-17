
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
    def export(self, product_desc=None, version_note=None, **kwargs):
        """Export this entity to a product."""
    
        tex_convert = kwargs.get('tex_convert', True)
        tex_queue = kwargs.get('tex_queue', True)
        
        tif_product_repr = self._tif_export(product_desc, version_note)
        product_reprs = [tif_product_repr]

        if tex_convert:
            product_reprs.extend(
                self._tex_convert(product_desc, version_note, tif_product_repr, 
                    tex_queue)
            )

        return product_reprs

    # -------------------------------------------------------------------------
    def _tif_export(self, product_desc, version_note):

        file_ext = 'tif'
        product_repr = self._create_product(product_desc, version_note, file_ext)
        product_repr_dir = product_repr.directory
        name = self.display_name

        export_path = os.path.join(product_repr_dir, name + '.$UDIM.' + file_ext)

        # mari specific
        self.session.mari.history.startMacro('Exporting ' + name + ' Channel')

        try:
            channel = self.session.mari.geo.current().channel(name)
            snapshot = channel.createSnapshot('Backup pre-flattening', name)
            layer = channel.flatten()
            imgage_set = layer.imageSet()
            imgage_set.exportImages(export_path)

            self.session.mari.history.stopMacro()

            channel.revertToSnapshot(snapshot)
            channel.deleteSnapshot(snapshot)
        except Exception as e:
            print "ERROR: " + str(e)
            self.session.mari.history.stopMacro()
            self.session.mari.history.undo()
            self.session.mari.utils.message("Error with tif texture export.")

        product_repr.area.set_permissions(0660)
        
        return product_repr  

    # -------------------------------------------------------------------------
    def _tex_convert(self, product_desc, version_note, tif_product_repr, queue):

        tex_product_repr = self._create_product(
            product_desc, version_note, 'tex')

        tex_dir = tex_product_repr.directory
        tif_dir = tif_product_repr.directory

        if not os.path.exists(tif_dir):
            raise EntityError("TIF files must exist prior to TEX conversion.")

        try:
            tif_files = [f for f in os.listdir(tif_dir) if f.endswith('.tif')]
            self.session.mari.app.startProcessing(
                'Converting existing .tif to .tex', len(tif_files) + 1, True)
            self.session.mari.app.setProgress(0)

            for (count, tif_file) in enumerate(tif_files):
                self.session.mari.app.setProgress(i)
                (file_base, tif_ext) = os.path.splitext(tif_file)
                tex_file = os.path.join(file_base, '.tex')

                txcmd = 'txmake -mode periodic {tif} {tex}'.format(
                    os.path.join(tif_dir, tif_file), 
                    os.path.join(tex_dir, tex_file)
                )

                os.system(txcmd)

            self.session.mari.app.stopProcessing()
        except:
            self.session.mari.app.stopProcessing()
            self.session.mari.utils.message("Error with conversion. "
                "Please make sure folders are chmodded correctly/files exist.")

        tex_product_repr.area.set_permissions(0660)
        
        return [tex_product_repr]  

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


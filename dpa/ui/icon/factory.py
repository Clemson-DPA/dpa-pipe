
import os

from dpa.ptask.area import PTaskArea

# -----------------------------------------------------------------------------
class IconFactory(object):

    ICON_SCHEME = "icon:///"

    # -------------------------------------------------------------------------
    @classmethod
    def is_icon_path(cls, path):
        return path.startswith(cls.ICON_SCHEME)        

    # -------------------------------------------------------------------------
    def disk_path(self, uri):

        if not uri:
            return ""
        
        # XXX need to properly parse uri
        rel_path = uri.replace(self.__class__.ICON_SCHEME, "")

        image_paths = self.ptask_area.ancestor_paths(
            relative_file=rel_path, include_install=True)

        for image_path in image_paths:
            if os.path.exists(image_path):
                return image_path

        return rel_path    

    # -------------------------------------------------------------------------
    @property
    def ptask_area(self):

        if not hasattr(self, '_ptask_area'):
            self._ptask_area = PTaskArea.current()

        return self._ptask_area


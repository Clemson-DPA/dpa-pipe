import re
import os.path

from dpa.action import ActionError
from dpa.action.registry import ActionRegistry
from dpa.app.entity import Entity, EntityRegistry, EntityError
from dpa.config import Config


# -----------------------------------------------------------------------------
class GeomEntity(Entity):

    category = "geom"
    exportable = False

    # -------------------------------------------------------------------------
    # I'm hacking this until we get a proper subscribe and import dialogue
    def export(self):
        pass

    # -------------------------------------------------------------------------
    def import_product(self, file_name, file_path):
        # if OBJ file....
        if self.session.mari.projects.current():
            raise EntityError("Cannot have a project open when importing.")

        self.create_project(file_name, file_path)

    # -------------------------------------------------------------------------
    def create_project(self, file_name, file_path):
        # very mari specific
        add_channels = []
        self._read_cfg('channels')

        for (ch_name, opts) in self.opts.channels.iteritems():
            c = opts.get('color', [0.5,0.5,0.5,1.0])
            color = self.session.mari.Color(c[0], c[1], c[2], c[3])

            alpha = opts.get('alpha', True)

            # create channels
            ch = self.session.mari.ChannelInfo(ch_name, use_alpha=alpha,
                fill_color=color)

            d = opts.get('depth', 16)
            ch.setDepth(d)

            add_channels.append(ch)

        # creates project
        self.session.mari.projects.create(file_name, file_path, 
            add_channels)

        # add layers doug wanted (srgb2linear)
        for (ch_name, opts) in self.opts.channels.iteritems():
            if 'layer' in opts:
                for (ltype, vals) in opts.layer.iteritems():
                    if ltype == 'adjustment':
                        for (lname, pkey) in vals.iteritems():
                            geo = self.session.mari.geo.current()
                            geoch = geo.channel(ch_name)
                            adj = geoch.createAdjustmentLayer(lname,pkey)
                            adj.setVisibility(False)

        # close and archive...just because
        proj = self.session.mari.projects.current()
        uuid = proj.uuid()
        proj.save(force_save=True)
        proj.close(confirm_if_modified=False)

        # i need a file path....
        ptask_dir = self.session.ptask_area.dir()
        mari_proj = os.path.join(ptask_dir, self.session.app_name, 
            self.session.ptask.name) + '.mra'

        self.session.mari.projects.archive(uuid,mari_proj)
        self.session.ptask_area.set_permissions(0660)
        self.session.mari.projects.open(uuid)

    # -------------------------------------------------------------------------
    def _read_cfg(self, action):
        app_name = self.session.app_name
        
        rel_cfg = os.path.join('config', app_name, self.category, action)
        rel_cfg += '.cfg'

        ptask_area = self.session.ptask_area
        action_cfg = ptask_area.config(rel_cfg, composite_ancestors=True)

        if not action_cfg or not hasattr(action_cfg, 'channels'):
            raise ActionError(
                "Cannot create mari project without set config.")

        self._opts = action_cfg

    #  -------------------------------------------------------------------------
    @property
    def opts(self):
        if not hasattr(self, '_opts'):
            return None

        return self._opts

# -----------------------------------------------------------------------------
EntityRegistry().register('mari', GeomEntity)

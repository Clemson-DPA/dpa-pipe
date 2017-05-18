import os

from dpa.app.entity import Entity, EntityRegistry, EntityError

# -----------------------------------------------------------------------------
class GeomEntity(Entity):

    category = 'geom'

    CHANNEL_CONFIG = 'config/mari/geom/channels.cfg'

    # -------------------------------------------------------------------------
    @classmethod
    def import_product_representation(cls, session, representation, *args,
        **kwargs):

        if session.mari.projects.current():
            raise EntityError("Cannot have a project open when importing.")

        channel_config = session.ptask_area.config(cls.CHANNEL_CONFIG,
            composite_ancestors=True)

        force_ptex = kwargs.get('force_ptex', False)

        if not channel_config or not hasattr(channel_config, 'channels'):
            raise EntityError(
                "Unable to find channel config for {cat} import.".format(
                    cat=cls.category))

        product_name = representation.product_version.product.name

        channels = []

        # create the channels
        for (channel_name, channel_options) in channel_config.channels.iteritems():

            # prepend the product name to the channel
            channel_name = product_name + '_' + channel_name

            # retrieve the channel options
            color_values = channel_options.get('color', [0.5, 0.5, 0.5, 1.0])
            color = session.mari.Color(*color_values[0:3])
            use_alpha = channel_options.get('alpha', True)
            depth = channel_options.get('depth', 16)

            channel = session.mari.ChannelInfo(channel_name,
                use_alpha=use_alpha, fill_color=color)
            channel.setDepth(depth)

            channels.append(channel)

        mari_dir = session.ptask_area.dir(dir_name='mari')

        # get a path to the geom product via the import directory
        geom_file = cls.get_import_file(session, product_name, cls.category,
            representation)

        # create the project
        if force_ptex:
            #session.mari.utils.message("Using Ptex!")
            EmptyChannels = []
            project_meta_options = dict()
            project_meta_options["MappingScheme"] = session.mari.projects.FORCE_PTEX
            project_meta_options["MultipleGeometries"] = session.mari.projects.MERGE_GEOMETRIES
            project_meta_options["PtexFaceSizeScheme"] = session.mari.projects.PTEX_WORLD_SPACE_DENSITY_SIZE
            project_meta_options["PtexFaceSize"] = 16
            project_meta_options["PtexImageFormat"] = session.mari.projects.PTEXFORMAT_BYTE
            project_meta_options["PtexFaceColor"] = session.mari.Color(0.5, 0.5, 0.5, 1)
            project_meta_options["MergeType"] = session.mari.geo.MERGETYPE_SINGLE_MESH
            project_meta_options["CreateSelectionSets"] = session.mari.geo.SELECTION_GROUPS_CREATE_FROM_FACE_GROUPS
            session.mari.projects.create(product_name, geom_file, EmptyChannels, EmptyChannels, project_meta_options)
        else:
            session.mari.projects.create(product_name, geom_file, channels)

            # now account for adjustment layers, etc.
            for (channel_name, channel_options) in channel_config.channels.iteritems():

                # prepend the product name to the channel
                channel_name = product_name + '_' + channel_name

                # layers
                if 'layers' in channel_options:

                    for (layer_type, layer_options) in \
                        channel_options.layers.iteritems():

                        # adjustment layer
                        if layer_type == 'adjustment':
                            for (layer_name, adjustment_key) in \
                                layer_options.iteritems():

                                geo = session.mari.geo.current()
                                geo_channel = geo.channel(channel_name)
                                adjustment_layer = \
                                    geo_channel.createAdjustmentLayer(
                                        layer_name, adjustment_key)
                                adjustment_layer.setVisibility(False)

                        # other layer types...

        # close and archive the new project
        project = session.mari.projects.current()
        uuid = project.uuid()
        project.save(force_save=True)
        project.close(confirm_if_modified=False)

        # archive
        mari_file = os.path.join(mari_dir, product_name + '.mra')
        session.mari.projects.archive(uuid, mari_file)
        os.chmod(mari_file, 0770)
        session.mari.projects.open(uuid)

    # -------------------------------------------------------------------------
    def export(self, *args, **kwargs):
        """Export this entity to a product."""

        raise EntityError("Mari geom export not supported.")

# -----------------------------------------------------------------------------
EntityRegistry().register('mari', GeomEntity)

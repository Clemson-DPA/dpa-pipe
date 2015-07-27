"""A collection of dpa-specific nuke nodes."""

from collections import defaultdict
import os
import re

import nuke

from dpa.ptask import PTask
from dpa.ptask.area import PTaskArea, PTaskAreaError
from dpa.ptask.spec import PTaskSpec

# -----------------------------------------------------------------------------

# subscribed product representation cache
SUBD_REPR_CACHE = []
PRODUCT_REPR_STR_TO_PATH = {}

DEFAULT_REPR_STR = 'Please select a subscription...'

# -----------------------------------------------------------------------------
def get_default_product_name():

    name = "Comp"

    ptask_area = PTaskArea.current()
    if ptask_area:
        name = PTaskSpec.name(ptask_area.spec) + name

    return name

# -----------------------------------------------------------------------------
def create_write_product_node():

    node = nuke.createNode('Write', inpanel=True)

    node_name = 'WriteProduct'
    node_inst = 1

    while nuke.exists(node_name + str(node_inst)):
        node_inst += 1

    node_name += str(node_inst)

    node.knob('name').setValue(node_name)
    node.knob('beforeRender').setValue(
        'dpa.nuke.utils.create_product_before_render()')
    node.knob('afterFrameRender').setValue(
        'dpa.nuke.utils.set_permissions_after_frame()')

    products_tab = nuke.Tab_Knob("Product")
    node.addKnob(products_tab)
    node.addKnob(nuke.EvalString_Knob('product_desc', 'description', ""))
    node.addKnob(nuke.EvalString_Knob('product_name', 'name', 
        get_default_product_name()))
    node.addKnob(nuke.EvalString_Knob('product_ver_note', 'description', ""))

    # hide the file knob
    node.knob('file').setVisible(False)
    node.knob('file_type').setValue('exr')
    node.knob('product_ver_note').setVisible(False)

# -----------------------------------------------------------------------------
def get_import_dir(product_repr, product=None, area=None, relative_to=None):

    if not area:
        area = PTaskArea.current()

    if not product:
        product = product_repr.product_version.product

    try:
        import_dir = area.dir(dir_name='import', path=True)
    except PTaskAreaError:
        raise Exception("Could not find import directory!")

    import_dir = os.path.join(
        import_dir, 'global', product.name, product.category, 
        product_repr.type, product_repr.resolution
    )

    if relative_to:
        import_dir = os.path.relpath(import_dir, relative_to)

    return import_dir

# -----------------------------------------------------------------------------
def populate_sub_cache(ptask_version=None, refresh=False):

    if not ptask_version:

        ptask_area = PTaskArea.current()
        ptask = PTask.get(ptask_area.spec)

        if ptask_area.version:
            ptask_version = ptask.version(ptask_area.version)
        else:
            ptask_version = ptask.latest_version

    nuke_file = nuke.root().name()
    nuke_dir = os.path.dirname(nuke_file)

    if refresh or not SUBD_REPR_CACHE:

        for sub in ptask_version.subscriptions:
            for product_repr in sub.product_version.representations:

                product = product_repr.product_version.product

                if product.category != 'imgseq':
                    continue

                product_repr_str = product.name_spec + ' @ ' + \
                    product_repr.type

                if product_repr.resolution != 'none':
                    product_repr_str += PTaskSpec.SEPARATOR + \
                    product_repr.resolution 

                sub_import_dir = get_import_dir(product_repr,
                    product=product, area=ptask_area, relative_to=nuke_dir)

                # populate cache lookups
                SUBD_REPR_CACHE.append(product_repr)
                PRODUCT_REPR_STR_TO_PATH[product_repr_str] = \
                    sub_import_dir
        
# -----------------------------------------------------------------------------
def read_sub_knob_changed(node=None, knob=None):

    if not node:
        node = nuke.thisNode()

    if not knob:
        knob = nuke.thisKnob()

    if knob.name() == 'product_repr_select':
        product_repr_str = node['product_repr_select'].value()

        if (product_repr_str == DEFAULT_REPR_STR or 
            product_repr_str not in PRODUCT_REPR_STR_TO_PATH):
            node['product_seq_select'].setValues([])
            node['file'].setValue('')
            return

        repr_dir = PRODUCT_REPR_STR_TO_PATH[product_repr_str]

        # populate the possible file names
        file_specs = {}
        frame_regex = re.compile('(\w+).(\d{4})\.(\w+)')
        for file_name in os.listdir(repr_dir):
            
            matches = frame_regex.search(file_name)
            if matches:
                (file_base, frame_num, file_ext) = matches.groups()
                spec = file_base + '.####.' + file_ext
                file_specs[spec] = None

        file_specs = sorted(file_specs.keys())
        node['product_seq_select'].setValues(file_specs)

        file_str = os.path.join(repr_dir, file_specs[0]) 
        node['file'].setValue(file_str)

    if knob.name() == 'product_seq_select':
        
        repr_dir = os.path.dirname(node['file'].value())
        file_spec = node['product_seq_select'].value()

        file_str = os.path.join(repr_dir, file_spec)
        
        node['file'].setValue(file_str)

# -----------------------------------------------------------------------------
def create_read_sub_node():

    node = nuke.createNode('Read', inpanel=True)

    node_name = 'ReadSub'
    node_inst = 1

    while nuke.exists(node_name + str(node_inst)):
        node_inst += 1

    node_name += str(node_inst)

    node.knob('name').setValue(node_name)
    
    sub_tab = nuke.Tab_Knob("Sub")

    # make sure the product reprs are cached
    populate_sub_cache(refresh=False)

    repr_str_list = [DEFAULT_REPR_STR]
    repr_str_list.extend(sorted(PRODUCT_REPR_STR_TO_PATH.keys()))

    product_repr_select = nuke.Enumeration_Knob(
        'product_repr_select',
        'subscription',
        repr_str_list,
    )

    product_seq_select = nuke.Enumeration_Knob(
        'product_seq_select',
        'files',
        [],
    )

    nuke.callbacks.addKnobChanged(read_sub_knob_changed,
        nodeClass='Read', node=node)

    node.addKnob(sub_tab)
    node.addKnob(product_repr_select)
    node.addKnob(product_seq_select)

    node.knob('file').setVisible(False)

    # make the tab pop to front
    node['Sub'].setFlag(0) 

    read_sub_knob_changed(node=node, knob=node.knob('product_repr_select'))

# -----------------------------------------------------------------------------
def update_all_read_sub_nodes():

    read_sub_nodes = [node for node in nuke.allNodes(
            filter='Read') if node.knob('product_repr_select')]

    repr_str_list = [DEFAULT_REPR_STR]
    repr_str_list.extend(sorted(PRODUCT_REPR_STR_TO_PATH.keys()))

    for node in read_sub_nodes:

        product_repr_select = node.knob('product_repr_select')
        product_seq_select = node.knob('product_seq_select')

        cur_repr_value = product_repr_select.value()
        cur_seq_value = product_seq_select.value()

        product_repr_select.setValues(repr_str_list)

        if cur_repr_value in repr_str_list:
            product_repr_select.setValue(cur_repr_value)

            read_sub_knob_changed(node=node, knob=product_repr_select)

            seq_values = product_seq_select.value()
            if cur_seq_value in seq_values:
                product_seq_select.setValue(cur_seq_value)

        else:
            product_repr_select.setValue(DEFAULT_REPR_STR)

# -----------------------------------------------------------------------------
def add_commands():

    nuke.menu('Nodes').addCommand(
        name='Image/WriteProduct',
        command=create_write_product_node,
        shortcut='w',
    )

    nuke.menu('Nodes').addCommand(
        name='Image/ReadSub',
        command=create_read_sub_node,
    )


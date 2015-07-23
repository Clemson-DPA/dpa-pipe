"""A collection of dpa-specific nuke nodes."""

import os

import nuke

from dpa.action.registry import ActionRegistry
from dpa.ptask import PTask, PTaskError
from dpa.ptask.area import PTaskArea
from dpa.ptask.spec import PTaskSpec

# -----------------------------------------------------------------------------
def create_product_before_render():

    # make sure name/description are entered

    node = nuke.thisNode()
    print "Creating product for write node... " + str(node)

    ptask_area = PTaskArea.current()
    ptask = PTask.get(ptask_area.spec)

    if ptask_area.version:
        ptask_version = ptask.version(ptask_area.version)
    else:
        ptask_version = ptask.latest_version

    category = 'imgseq'

    file_type = node['file_type'].value()
    if not file_type:
        file_type = 'exr'

    product_name = node['product_name'].value()
    product_desc = node['product_desc'].value()
    product_ver_note = node['product_ver_note'].value()

    if not product_desc:
        raise Exception("Please enter a product description.")

    width = nuke.value(node.name() + '.width')
    height = nuke.value(node.name() + '.height')
    resolution = width + 'x' + height
        
    create_action_cls = ActionRegistry().get_action('create', 'product')
    if not create_action_cls:
        raise Exception("Unable to find product creation action.")

    create_action = create_action_cls(
        product=product_name,
        ptask=ptask.spec,
        version=ptask_version.number,
        category=category,
        description=product_desc,
        file_type=file_type,
        resolution=resolution,
        note=product_ver_note,
    )

    try:
        create_action()
    except ActionError as e:
        raise Exception("Unable to create product: " + str(e))

    out_path = os.path.join(create_action.product_repr.area.path,
        product_name + '.####.' + file_type)

    node['file'].setValue(out_path)

# -----------------------------------------------------------------------------
def set_permissions_after_frame():

    node = nuke.thisNode()
    frame_path = nuke.filename(node, nuke.REPLACE)
    os.chmod(frame_path, 0660)

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
        'dpa.nuke.nodes.create_product_before_render()')
    node.knob('afterFrameRender').setValue(
        'dpa.nuke.nodes.set_permissions_after_frame()')

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
# Adding the custom nodes here...

# XXX needs to go into a function
nuke.menu('Nodes').addCommand(
    name='Image/WriteProduct',
    command=create_write_product_node,
    shortcut='w',
)


"""A collection of dpa-specific nuke nodes."""

import nuke

from dpa.ptask.area import PTaskArea
from dpa.ptask.spec import PTaskSpec

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
def add_commands():

    nuke.menu('Nodes').addCommand(
        name='Image/WriteProduct',
        command=create_write_product_node,
        shortcut='w',
    )


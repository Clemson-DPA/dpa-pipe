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


# -----------------------------------------------------------------------------
def read_sub_knob_changed(node=None, knob=None):

    if not node:
        node = nuke.thisNode()

    if not knob:
        knob = nuke.thisKnob()

    if knob.name() == 'product_repr_select':
        sub_display_str = node['product_repr_select'].value()

        # XXX populate the file parameter with the import path
        # for the sub matching the string

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

    # XXX create this one empty
    # XXX write a method to populate that can be called to refresh list too
    product_repr_select = nuke.Enumeration_Knob(
        'product_repr_select',
        'subscription',
        # XXX sub -> display string
        # XXX display string -> sub
        # XXX name=category @ type=resolution
        [
            'envRockyAlcove=workfile @ exr=1920x1080',
            'envRockyAlcove=workfile @ exr=960x540',
            'envRockyAlcoveObj=geom @ exr=1920x1080',
            'envRockyAlcoveObj=geom @ exr=960x540',
            'envRockyAlcoveObj_bump=maps @ exr=1920x1080',
            'envRockyAlcoveObj_bump=maps @ exr=960x540',
            'envRockyAlcoveObj_diffuse=maps @ exr=1920x1080',
            'envRockyAlcoveObj_diffuse=maps @ exr=960x540',
            'envRockyAlcoveObj_displacement=maps @ exr=1920x1080',
            'envRockyAlcoveObj_displacement=maps @ exr=960x540',
            'LayoutCam1=camera=0200 @ exr=1920x1080',
            'LayoutCam1=camera=0200 @ exr=960x540',
        ]
    )

    nuke.callbacks.addKnobChanged(read_sub_knob_changed,
        nodeClass='Read', node=node)

    # XXX subs cache in utils

    # XXX button to force reload of 

    # XXX button to requery subs and repopulate selections in all read nodes
    # XXX if text in 'file' knob does't exist in subs list, error, clear 'file'

    # XXX on startup, need to go through read nodes and set file

    node.addKnob(sub_tab)
    node.addKnob(product_repr_select)

    node.knob('file').setVisible(False)

    # make the tab pop to front
    node['Sub'].setFlag(0) 

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

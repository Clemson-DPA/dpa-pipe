
import os

import nuke

from dpa.action.registry import ActionRegistry
from dpa.ptask import PTask, PTaskError
from dpa.ptask.area import PTaskArea

# -----------------------------------------------------------------------------
def create_product_before_render(node=None):

    if not node:
        node = nuke.thisNode()

    if not node.knob('product_name') or not node.knob('product_desc'):
        raise Exception("The supplied node is not a WriteProduct node.")

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

    return create_action.product_repr

# -----------------------------------------------------------------------------
def set_permissions_after_frame():

    node = nuke.thisNode()
    frame_path = nuke.filename(node, nuke.REPLACE)
    os.chmod(frame_path, 0660)


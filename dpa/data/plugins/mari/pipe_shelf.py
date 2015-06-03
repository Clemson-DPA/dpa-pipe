
from dpa.mari.shelf import MariShelf
from dpa.ptask.area import PTaskArea

# -----------------------------------------------------------------------------

CONFIG_FILE = 'config/mari/shelves.cfg'
INITIALIZED_SHELVES = []

# -----------------------------------------------------------------------------
def initializePlugin():

    # read the config, get all the shelf definitions
    ptask_area = PTaskArea.current()
    mari_shelves_config = ptask_area.config(
        config_file=CONFIG_FILE, composite_ancestors=True)

    for (shelf_name, shelf_config) in mari_shelves_config.iteritems():

        shelf = MariShelf(shelf_name)
        if shelf.exists:
            shelf.delete()

        shelf.create()

        # add all the shelf buttons
        for (button_key, button_config) in shelf_config.iteritems():
            shelf.add_button(**button_config)

        INITIALIZED_SHELVES.append(shelf)
    
# -----------------------------------------------------------------------------
def uninitializePlugin():

    for shelf in INITIALIZED_SHELVES:
        if shelf.exists:
            shelf.delete()


initializePlugin()
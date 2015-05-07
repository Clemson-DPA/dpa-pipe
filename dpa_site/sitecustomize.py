

# The dpa import hook creates special behavior for python imports within the
# dpa namespace. It allows python packages to be spread out across the
# production hierarchy. This makes it possible to test python modules at the
# shot level before forcing the code onto the entire production. Because the
# dpa_import hook is limited to the 'dpa' namespace, it will not affect
# built-in or 3rd party python package imports.
import dpa_import_hook


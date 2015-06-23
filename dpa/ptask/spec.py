
# -----------------------------------------------------------------------------
# Imports:
# -----------------------------------------------------------------------------

import os.path
import re

# -----------------------------------------------------------------------------
# Globals:
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# Classes:
# -----------------------------------------------------------------------------
class PTaskSpec(str):
    """A string representing a PTask.

    A PTaskSpec is not guaranteed to match a single PTask within the pipeline.
    This is simply a string specification used to identify one or more Ptasks.

    """

    CURRENT = '.'
    PARENT = '..'
    ROOT = '^' 
    SEPARATOR = '='
    WILDCARD = '%'
    VERSION = '@'

    # separates the ptask spec from an additional product specification. the
    # additional product spec will be stored as a property on the spec object.
    PRODUCT_SEPARATOR = "products"

    # this will be used to essentially split the spec on the product separator.
    PRODUCT_REGEX = re.compile(
        "^((\w+{sep})*)({psep}({sep}\w+)*)$".format(
            sep=SEPARATOR,
            psep=PRODUCT_SEPARATOR,
        )
    )

    # -------------------------------------------------------------------------
    # Class methods:
    # -------------------------------------------------------------------------
    @classmethod
    def get(cls, in_str, relative_to=None):
        """Evaluate the input string to a PTaskSpec object.

        A relative_to PTaskSpec/str may also be supplied for evaluating partial
        input specs.

        """

        if os.path.sep in in_str:
            raise PTaskSpecError(
                "Invalid character in ptask spec: '" + os.path.sep + "'")

        if relative_to and os.path.sep in relative_to:
            raise PTaskSpecError(
                "Invalid character in relative_to ptask spec: '" + \
                os.path.sep + "'"
            )

        # remove whitespace and separators from head/tail
        in_str = in_str.strip().strip(PTaskSpec.SEPARATOR)

        if in_str.lower() == "none":
            return PTaskSpec("")

        # if the spec string starts with PTaskSpec.ROOT, it eliminates the
        # relative part (it implies that what follows is relative to the top
        # level).
        if in_str.startswith(PTaskSpec.ROOT):
            relative_to = ""
            in_str = in_str.lstrip(PTaskSpec.ROOT)

        in_str = in_str.strip(PTaskSpec.SEPARATOR)
        in_str_parts = in_str.strip().split(PTaskSpec.SEPARATOR)

        # if relative_to has a value, use it as the base for full output spec
        if relative_to:
            full_spec_parts = relative_to.strip().split(PTaskSpec.SEPARATOR)
        else:
            full_spec_parts = []

        # expand full spec by evaluating each bit of the input spec in order
        while len(in_str_parts) > 0:
        
            part = in_str_parts.pop(0)

            # if the part is the parent string, go up one level in the spec
            if part == PTaskSpec.PARENT:
                try:
                    full_spec_parts.pop()
                except IndexError:
                    raise PTaskSpecError(
                        "Could not find parent task name for: '" + \
                        PTaskSpec.SEPARATOR.join(full_spec_parts) + "'"
                    )

            # if the part is the current level, just ignore it
            elif part == PTaskSpec.CURRENT:
                continue

            # next level of the spec, add it to the full spec parts
            else:
                full_spec_parts.append(part)

        # join the parts and make sure there aren't any colons on either end.
        full_spec_str = PTaskSpec.SEPARATOR.join(full_spec_parts).\
            lstrip(PTaskSpec.SEPARATOR).rstrip(PTaskSpec.SEPARATOR)

        return PTaskSpec(full_spec_str)

    # -------------------------------------------------------------------------
    @classmethod
    def name(cls, spec):
        """Similar to os.path.basename(), return the name portion of the spec.

        This would be the name attribute of the ptask this spec represents.

        """

        return cls(spec.strip().split(PTaskSpec.SEPARATOR)[-1])

    # -------------------------------------------------------------------------
    @classmethod
    def parent(cls, spec):
        """Similar to os.path.dirname, return the parent spec."""

        # return none if the spec is None or the empty string
        if not spec:
            return None
        
        spec_parts = spec.strip().split(PTaskSpec.SEPARATOR)
        spec_parts.pop()
        return cls(PTaskSpec.SEPARATOR.join(spec_parts))

    # -------------------------------------------------------------------------
    # Instance methods:
    # -------------------------------------------------------------------------
    def __new__(cls, spec_str):

        match = cls.PRODUCT_REGEX.match(spec_str)
        if match:
            base_spec_str = match.group(1).strip(cls.SEPARATOR)
            product_spec_str = match.group(3).strip(cls.SEPARATOR)
        else:
            base_spec_str = spec_str
            product_spec_str = ""

        # allow people to avoid typing 4 digit padded version numbers in specs
        product_parts = product_spec_str.split(cls.SEPARATOR)
        if len(product_parts) > 3:
            product_parts[3] = product_parts[3].zfill(4)
            product_spec_str = cls.SEPARATOR.join(product_parts)
            spec_str = cls.SEPARATOR.join([base_spec_str, product_spec_str])

        instance = str.__new__(cls, spec_str)
        instance._base_spec = base_spec_str
        instance._product_spec = product_spec_str

        return instance

    # -------------------------------------------------------------------------
    # Properties:
    # -------------------------------------------------------------------------
    @property
    def base_spec(self):
        return self._base_spec

    # -------------------------------------------------------------------------
    @property
    def product_spec(self):
        return self._product_spec

# -----------------------------------------------------------------------------
class PTaskSpecError(Exception):
    pass


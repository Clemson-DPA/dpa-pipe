# -----------------------------------------------------------------------------
# Module: dpa.imgres
# Author: Chuqiao Wang (chuqiaw)
# -----------------------------------------------------------------------------
"""An image resolution API

An image resolution API that handles resolution change.

Classes
-------
ImgRes
    A class that represents an image resolution
ImgResError
    Syntax error when parsing an image resolution

Examples
--------
    >>> from dpa.imgres import ImgRes
    >>> ir = ImgRes(width=1920, height=1080)
    >>> ir.width 
    1920
    >>> ir.height
    1080
    >>> ir.aspect
    1.7777777777777
    >>> ir.pixels
    2073600
    >>> ir_half = ir / 2
    >>> ir_half.width
    960
    >>> ir_half.height
    540
    >>> ir_double = ir.double
    >>> ir_double.width 
    3840
    >>> ir_double.height
    2160
    >>> ir > ir_double
    False
    >>> ir > ir_half
    True
    >>> ImgRes.get("1920x1080")
    1920x1080

"""

# -----------------------------------------------------------------------------
# Imports:
# -----------------------------------------------------------------------------

import re
import sys

# -----------------------------------------------------------------------------
# Public Classes: 
# -----------------------------------------------------------------------------
class ImgRes(object):
    """An image resolution API that handles resolution change. """

    # -------------------------------------------------------------------------
    # Class attributes:
    # -------------------------------------------------------------------------
    _pattern = re.compile("^([0-9]+)(x)([0-9]+)$")

    # -------------------------------------------------------------------------
    # Special methods:
    # -------------------------------------------------------------------------
    def __init__(self, width, height):
        """Constructor. 

        :arg str res: The original image resolution
        :keyword int width: image width
        :keyword int height: image height

        """
        super(ImgRes, self).__init__()
        self._width = width
        self._height = height

    def __str__(self):
        return str(self._width) + "x" + str(self._height)

    def __mul__(self, factor):
        """ Multiplication operator overloading 

        :arg int factor: The multiplication factor

        """
        new_width = self.width * factor
        new_height = self.height * factor
        return ImgRes(new_width, new_height)

    def __div__(self, factor):
        """ Division operator overloading 

        :arg int factor: The division factor

        """
        new_width = self.width / factor
        new_height = self.height / factor
        return ImgRes(new_width, new_height)

    def __lt__(self, other_img_res):
        """ Less than comparison operator overloading 

        :arg ImgRes other_img_res: The ImgRes object to be compared with

        """
        return self.pixels < other_img_res.pixels

    def __gt__(self, other_img_res):
        """ Greater than comparison operator overloading 

        :arg ImgRes other_img_res: The ImgRes object to be compared with

        """
        return self.pixels > other_img_res.pixels

    def __eq__(self, other_img_res):
        """ Equal to comparison operator overloading 

        :arg ImgRes other_img_res: The ImgRes object to be compared with

        """
        return self._width == other_img_res.width and self.height == other_img_res.height

    # -------------------------------------------------------------------------
    # Static methods:
    # -------------------------------------------------------------------------
    @staticmethod
    def get(input_res):
        """ Return an ImgRes object with specified resolution

        :arg str input_res: image resolution

        """
        match = ImgRes._pattern.match(input_res)

        if not match:    
            raise ImgResError("invalid syntax for image resolution")
        else: 
            groups = match.groups() 
            width = int(groups[0])
            height = int(groups[2])

        return ImgRes(width, height)

    # -------------------------------------------------------------------------
    # Properties:
    # -------------------------------------------------------------------------
    @property
    def width(self):
        """width of the image"""
        return self._width

    @property
    def height(self):
        """height of the image"""
        return self._height

    @property
    def aspect(self):
        """aspect ratio of the image"""
        return self._width / float(self._height)

    @property
    def pixels(self):
        """number of piexels"""
        return self._width * self._height

    @property
    def half(self):
        """new ImgRes object with half resolution"""
        return self.__div__(2)

    @property
    def double(self):
        """new ImgRes object with double resolution"""
        return self.__mul__(2)

# -----------------------------------------------------------------------------
# Exceptions:
# -----------------------------------------------------------------------------
class ImgResError(Exception):
    """Invalid image resolution syntax """
    pass

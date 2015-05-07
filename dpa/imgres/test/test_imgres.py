# -----------------------------------------------------------------------------
# Module: dpa.imgres.tests.test_imgres
# Author: Chuqiao Wang (chuqiaw)
# -----------------------------------------------------------------------------
"""Unit tests for dpa imgres.

Still testing.

"""
 
# -----------------------------------------------------------------------------
# Imports:
# -----------------------------------------------------------------------------
 
import unittest

from dpa.imgres import ImgRes
# from dpa.imgres import ImgResError

# -----------------------------------------------------------------------------
# Suite for all test cases defined:
# -----------------------------------------------------------------------------
def suite():
    """Returns a test suite for all frange tests."""
    
    return unittest.TestSuite([
        ImgResInstanceTestCase,
    ])

# -----------------------------------------------------------------------------
# Test Cases:
# -----------------------------------------------------------------------------
class ImgResInstanceTestCase(unittest.TestCase):
    """ImgRes class method tests."""

    # -------------------------------------------------------------------------
    # setup/teardown:
    # -------------------------------------------------------------------------
    def setUp(self):
        """Get a new ImgRes object for each test."""
        self.ir = ImgRes(width=1920, height=1080)

    # -------------------------------------------------------------------------
    def tearDown(self):
        """Clean up the ImgRes instance after each test method."""
        del self.ir
 
    # -------------------------------------------------------------------------
    # Tests:
    # -------------------------------------------------------------------------
    def test_property_width(self):
        """ImgRes 'width' property is int and read only"""

        width = self.ir.width
        self.assertEqual(start, 1920)

if __name__ == '__main__':
    unittest.main()


# -----------------------------------------------------------------------------
# Module: dpa.frange.tests.test_frange
# Author: Chuqiao Wang (chuqiaw)
# -----------------------------------------------------------------------------
"""Unit tests for dpa frange."""
 
# -----------------------------------------------------------------------------
# Imports:
# -----------------------------------------------------------------------------
 
import unittest

from dpa.frange import Frange
from dpa.frange import FrangeError
 
# -----------------------------------------------------------------------------
# Suite for all test cases defined:
# -----------------------------------------------------------------------------
def suite():
    """Returns a test suite for all frange tests."""
    
    return unittest.TestSuite([
        FrangeInstanceTestCase,
    ])

# -----------------------------------------------------------------------------
# Test Cases:
# -----------------------------------------------------------------------------
class FrangeInstanceTestCase(unittest.TestCase):
    """Frange class method tests."""

    # -------------------------------------------------------------------------
    # setup/teardown:
    # -------------------------------------------------------------------------
    def setUp(self):
        """Get a new location object for each test."""
        self.f1 = Frange()
        self.f2 = Frange("1")
        self.f3 = Frange("-1, 0, 1")
        self.f4 = Frange("-5-5")
        self.f5 = Frange("-10-10:2")
        self.f6 = Frange("10-20:3, 1, 4-7")
        self.f7 = Frange(["4, 7", "10-20:3", "1"])

    # -------------------------------------------------------------------------
    def tearDown(self):
        """Clean up the location instance after each test method."""
        del self.f1
        del self.f2
        del self.f3
        del self.f4
        del self.f5
        del self.f6
        del self.f7
 
    # -------------------------------------------------------------------------
    # Tests:
    # -------------------------------------------------------------------------
    def test_method_add(self):
        """Add specified frames to the range"""
        self.f1.add("1-5")
        for i in range(1, 6):
            self.assertTrue(i in self.f1.frames)

        self.f1.add("10-20:2")
        for i in range(1, 6) and range(10, 21, 2):
            self.assertTrue(i in self.f1.frames)

        self.f1.add("30, 32, 34-36")
        for i in range(1, 6) and range(10, 21, 2) and range(30, 37, 2):
            self.assertTrue(i in self.f1.frames)

        self.f1.add(["40-50, 60"])
        for i in [range(1, 6) and range(10, 21, 2) and range(30, 35, 2) and range(40, 51) and 60]:
            self.assertTrue(i in self.f1.frames)

        self.assertRaises(FrangeError, self.f1.add("4, 7-"))


    def test_method_remove(self):
        """Remove specified frames to the range"""
        self.f7.remove("1")
        for i in [1]:
            self.assertFalse(i in self.f7.frames)

        self.f7.remove("10-15:3")
        for i in range(10, 15, 3):
            self.assertFalse(i in self.f7.frames)

        self.f7.remove("16, 19-20")
        for i in [16 and range(19, 21)]:
            self.assertFalse(i in self.f7.frames)

        self.f7.remove(["4, 7"])
        for i in [4, 7]:
            self.assertFalse(i in self.f7.frames)

        self.assertRaises(FrangeError, self.f7.remove("4, 7-"))

    def test_property_start(self):
        """Frange 'start' property is int and read only"""

        start = self.f1.start
        self.assertEqual(start, None)

        start = self.f2.start
        self.assertIsInstance(start, int)
        self.assertEqual(start, 1)

        start = self.f3.start
        self.assertIsInstance(start, int)
        self.assertEqual(start, -1)
        
        start = self.f4.start
        self.assertIsInstance(start, int)
        self.assertEqual(start, -5)

        start = self.f5.start
        self.assertIsInstance(start, int)
        self.assertEqual(start, -10)
        
        start = self.f6.start
        self.assertIsInstance(start, int)
        self.assertEqual(start, 1)
        
        start = self.f7.start
        self.assertIsInstance(start, int)
        self.assertEqual(start, 1)

    def test_property_end(self):
        """Frange 'end' property is int and read only"""

        end = self.f1.end
        self.assertEqual(end, None)

        end = self.f2.end
        self.assertIsInstance(end, int)
        self.assertEqual(end, 1)

        end = self.f3.end
        self.assertIsInstance(end, int)
        self.assertEqual(end, 1)
        
        end = self.f4.end
        self.assertIsInstance(end, int)
        self.assertEqual(end, 5)

        end = self.f5.end
        self.assertIsInstance(end, int)
        self.assertEqual(end, 10)
        
        end = self.f6.end
        self.assertIsInstance(end, int)
        self.assertEqual(end, 19)
        
        end = self.f7.end
        self.assertIsInstance(end, int)
        self.assertEqual(end, 19)

    def test_property_first(self):
        """Frange 'first' property is int and read only"""

        first = self.f1.first
        self.assertEqual(first, None)

        first = self.f2.first
        self.assertIsInstance(first, int)
        self.assertEqual(first, 1)

        first = self.f3.first
        self.assertIsInstance(first, int)
        self.assertEqual(first, -1)
        
        first = self.f4.first
        self.assertIsInstance(first, int)
        self.assertEqual(first, -5)

        first = self.f5.first
        self.assertIsInstance(first, int)
        self.assertEqual(first, -10)
        
        first = self.f6.first
        self.assertIsInstance(first, int)
        self.assertEqual(first, 10)
        
        first = self.f7.first
        self.assertIsInstance(first, int)
        self.assertEqual(first, 4)

    def test_property_last(self):
        """Frange 'last' property is int and read only"""

        last = self.f1.last
        self.assertEqual(last, None)

        last = self.f2.last
        self.assertIsInstance(last, int)
        self.assertEqual(last, 1)

        last = self.f3.last
        self.assertIsInstance(last, int)
        self.assertEqual(last, 1)
        
        last = self.f4.last
        self.assertIsInstance(last, int)
        self.assertEqual(last, 5)

        last = self.f5.last
        self.assertIsInstance(last, int)
        self.assertEqual(last, 10)
        
        last = self.f6.last
        self.assertIsInstance(last, int)
        self.assertEqual(last, 7)
        
        last = self.f7.last
        self.assertIsInstance(last, int)
        self.assertEqual(last, 1)

    def test_property_step(self):
        """Frange 'step' property is int and read only"""

        step = self.f1.step
        self.assertEqual(step, None)

        step = self.f2.step
        self.assertIsInstance(step, int)
        self.assertEqual(step, 1)

        step = self.f3.step
        self.assertIsInstance(step, int)
        self.assertEqual(step, 1)
        
        step = self.f4.step
        self.assertIsInstance(step, int)
        self.assertEqual(step, 1)

        step = self.f5.step
        self.assertIsInstance(step, int)
        self.assertEqual(step, 2)
        
        step = self.f6.step
        self.assertEqual(step, None)
        
        step = self.f7.step
        self.assertIsInstance(step, int)
        self.assertEqual(step, 3)

    def test_property_count(self):
        """Frange 'count' property is int and read only"""

        count = self.f1.count
        self.assertIsInstance(count, int)
        self.assertEqual(count, 0)

        count = self.f2.count
        self.assertIsInstance(count, int)
        self.assertEqual(count, 1)

        count = self.f3.count
        self.assertIsInstance(count, int)
        self.assertEqual(count, 3)
        
        count = self.f4.count
        self.assertIsInstance(count, int)
        self.assertEqual(count, 11)

        count = self.f5.count
        self.assertIsInstance(count, int)
        self.assertEqual(count, 11)
        
        count = self.f6.count
        self.assertIsInstance(count, int)
        self.assertEqual(count, 9)
        
        count = self.f7.count
        self.assertIsInstance(count, int)
        self.assertEqual(count, 7)

if __name__ == '__main__':
    unittest.main()
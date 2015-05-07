# -----------------------------------------------------------------------------
# Module: dpa.location.tests.test_location
# Author: Josh Tomlinson (jtomlin)
# -----------------------------------------------------------------------------
"""Unit tests for dpa locations."""
 
# -----------------------------------------------------------------------------
# Imports:
# -----------------------------------------------------------------------------
 
import unittest

from dpa.location import Location
from dpa.restful import DataObjectError
 
# -----------------------------------------------------------------------------
# Globals:
# -----------------------------------------------------------------------------

TEST_LOCATION = 'CU_MCADAMS_DPA'
 
# -----------------------------------------------------------------------------
# Suite for all test cases defined:
# -----------------------------------------------------------------------------
def suite():
    """Returns a test suite for all location tests."""
    
    return unittest.TestSuite([
        LocationClassTestCase,
        LocationInstanceTestCase,
    ])

# -----------------------------------------------------------------------------
# Test Cases:
# -----------------------------------------------------------------------------
class LocationClassTestCase(unittest.TestCase):
    """Location class method tests."""
 
    # -------------------------------------------------------------------------
    # Tests:
    # -------------------------------------------------------------------------
    def test_method_list_all(self):
        """Location class list all dpa locations"""

        locations_list = Location.list()

        # returned object should be a list
        self.assertIsInstance(locations_list, list)

        # make sure items returned are not duplicated. 
        location_set = set(locations_list)
        self.assertEqual(len(locations_list), len(location_set))
        
        # ensure the types of the returned items are all 'Location'
        types = [type(location) for location in locations_list]
        self.assertEqual(len(set(types)), 1)
        self.assertEqual(types[0], Location)
        
    # -------------------------------------------------------------------------
    def test_method_get_instance(self):
        """Location instance get single location by primary key"""

        location = Location.get(TEST_LOCATION)

        # make sure one location is returned
        self.assertIsInstance(location, Location)

# -----------------------------------------------------------------------------
# Test Cases:
# -----------------------------------------------------------------------------
class LocationInstanceTestCase(unittest.TestCase):
    """Location class method tests."""

    # -------------------------------------------------------------------------
    # setup/teardown:
    # -------------------------------------------------------------------------
    def setUp(self):
        """Get a new location object for each test."""
        self.location = Location.get(TEST_LOCATION)
 
    # -------------------------------------------------------------------------
    def tearDown(self):
        """Clean up the location instance after each test method."""
        del self.location
 
    # -------------------------------------------------------------------------
    # Tests:
    # -------------------------------------------------------------------------
    def test_property_active(self):
        """Location 'active' property is boolean and read only"""

        active = self.location.active

        self.assertIsInstance(active, bool)
        self.assertRaises(DataObjectError,
            setattr(self, "active", False)
        )
 
    # -------------------------------------------------------------------------
    def test_property_code(self):
        """Location 'code' property is a string and read only"""

        code = self.location.code

        self.assertIsInstance(code, str)
        self.assertRaises(DataObjectError,
            setattr(self, "code", "NEW_LOCATION_CODE")
        )

    # -------------------------------------------------------------------------
    def test_property_description(self):
        """Location 'description' property is a string and read only"""

        description = self.location.description

        self.assertIsInstance(description, str)
        self.assertRaises(DataObjectError,
            setattr(self, "description", "Bogus location description")
        )

    # -------------------------------------------------------------------------
    def test_property_invalid(self):
        """Location invalid property not settable"""

        self.assertRaises(DataObjectError,
            setattr(self, "foobar", "some value")
        )

    # -------------------------------------------------------------------------
    def test_property_latitude(self):
        """Loation 'latitude' property is a float and read only"""

        latitude = self.location.latitude

        self.assertIsInstance(latitude, float)
        self.assertRaises(DataObjectError,
            setattr(self, "latitude", 12.34567)
        )

    # -------------------------------------------------------------------------
    def test_property_longitude(self):
        """Location 'longitude' property is a float and read only"""

        longitude = self.location.longitude

        self.assertIsInstance(longitude, float)
        self.assertRaises(DataObjectError, 
            setattr(self, "longitude", 76.54321)
        )

    # -------------------------------------------------------------------------
    def test_property_name(self):
        """Location 'name' property is a string and read only"""
        
        name = self.location.name

        self.assertIsInstance(name, str)
        self.assertRaises(DataObjectError, 
            setattr(self, "name", "Bogus Location name")
        )

    # -------------------------------------------------------------------------
    def test_property_timezone(self):
        """Location 'timezone' property is a string and read only"""

        timezone = self.location.timezone

        self.assertIsInstance(timezone, str)
        self.assertRaises(DataObjectError, 
            setattr(self, "timezone", "US/Nowhere")
        )


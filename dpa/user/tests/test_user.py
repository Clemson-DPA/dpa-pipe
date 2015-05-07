# -----------------------------------------------------------------------------
# Module: dpa.user.tests.test_user
# Author: Josh Tomlinson (jtomlin)
# -----------------------------------------------------------------------------
"""Unit tests for dpa users."""
 
# -----------------------------------------------------------------------------
# Imports:
# -----------------------------------------------------------------------------
 
import unittest

from dpa.user import User
from dpa.restful import DataObjectError
 
# -----------------------------------------------------------------------------
# Globals:
# -----------------------------------------------------------------------------

TEST_USERNAME = 'jtomlin'
 
# -----------------------------------------------------------------------------
# Suite for all test cases defined:
# -----------------------------------------------------------------------------
def suite():
    """Returns a test suite for all user tests."""
    
    return unittest.TestSuite([
        UserClassTestCase,
        UserInstanceTestCase,
    ])

# -----------------------------------------------------------------------------
# Test Cases:
# -----------------------------------------------------------------------------
class UserClassTestCase(unittest.TestCase):
    """User class method tests."""
 
    # -------------------------------------------------------------------------
    # Tests:
    # -------------------------------------------------------------------------
    def test_method_list_all(self):
        """User class list all dpa users"""

        user_list = User.list()

        # returned object should be a list
        self.assertIsInstance(user_list, list)

        # make sure items returned are not duplicated. 
        user_set = set(user_list)
        self.assertEqual(len(user_list), len(user_set))
        
        # ensure the types of the returned items are all 'User'
        types = [type(user) for user in user_list]
        self.assertEqual(len(set(types)), 1)
        self.assertEqual(types[0], User)
        
    # -------------------------------------------------------------------------
    def test_method_get_instance(self):
        """User instance get single user by primary key"""

        user = User.get(TEST_USERNAME)

        # make sure one user is returned
        self.assertIsInstance(user, User)

# -----------------------------------------------------------------------------
# Test Cases:
# -----------------------------------------------------------------------------
class UserInstanceTestCase(unittest.TestCase):
    """User class method tests."""

    # -------------------------------------------------------------------------
    # setup/teardown:
    # -------------------------------------------------------------------------
    def setUp(self):
        """Get a new user object for each test."""
        self.user = User.get(TEST_USERNAME)
 
    # -------------------------------------------------------------------------
    def tearDown(self):
        """Clean up the user instance after each test method."""
        del self.user
 
    # -------------------------------------------------------------------------
    # Tests:
    # -------------------------------------------------------------------------
    def test_property_is_active(self):
        """User 'is_active' property is boolean and read only"""

        is_active = self.user.is_active

        self.assertIsInstance(is_active, bool)
        self.assertRaises(DataObjectError,
            setattr(self, "is_active", False)
        )
 
    # -------------------------------------------------------------------------
    def test_property_email(self):
        """User 'email' property is a string and read only"""
        
        email = self.user.email

        self.assertIsInstance(email, str)
        self.assertRaises(DataObjectError, 
            setattr(self, "email", "foo@bar.com")
        )

    # -------------------------------------------------------------------------
    def test_property_first_name(self):
        """User 'first_name' property is a string and read only"""
        
        first_name = self.user.first_name

        self.assertIsInstance(first_name, str)
        self.assertRaises(DataObjectError, 
            setattr(self, "first_name", "John")
        )

    # -------------------------------------------------------------------------
    def test_property_last_name(self):
        """User 'last_name' property is a string and read only"""
        
        last_name = self.user.last_name

        self.assertIsInstance(last_name, str)
        self.assertRaises(DataObjectError, 
            setattr(self, "last_name", "Doe")
        )

    # -------------------------------------------------------------------------
    def test_property_username(self):
        """User 'username' property is a string and read only"""
        
        username = self.user.username

        self.assertIsInstance(username, str)
        self.assertRaises(DataObjectError, 
            setattr(self, "username", "foobar")
        )


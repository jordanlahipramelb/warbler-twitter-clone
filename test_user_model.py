"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase

from sqlalchemy import exc

from models import db, User, Message, Follows

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ["DATABASE_URL"] = "postgresql:///warbler-test"


# Now we can import app

from app import app

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()


class UserModelTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        db.drop_all()
        db.create_all()

        # USER 1
        u1 = User.signup("test1", "email1@email.com", "password", None)
        uid1 = 1111
        u1.id = uid1

        # USER 2
        u2 = User.signup("test2", "email2@email.com", "password", None)
        uid2 = 2222
        u2.id = uid2

        # QUERY EACH USER
        u1 = User.query.get(uid1)
        u2 = User.query.get(uid2)

        # SET UP THE USERS IN THE SESSION
        self.u1 = u1
        self.uid1 = uid1

        self.u2 = u2
        self.uid2 = uid2

        self.client = app.test_client()

    def tearDown(self):
        response = super().tearDown()
        db.session.rollback()
        return response

    def test_user_model(self):
        """Does basic model work?"""

        u = User(email="test@test.com", username="testuser", password="HASHED_PASSWORD")

        db.session.add(u)
        db.session.commit()

        # User should have no messages & no followers
        self.assertEqual(len(u.messages), 0)
        self.assertEqual(len(u.followers), 0)

    ###########################################
    # is_following tests ##################
    #######################################

    def test_user_follows_user(self):

        # following method
        #  { user }.following.append( { user2 })
        # user1 follow user2
        self.u1.following.append(self.u2)
        db.session.commit()

        # user2 follows should increase to 1
        self.assertEqual(len(self.u2.following), 0)
        self.assertEqual(len(self.u2.followers), 1)

        # user1 following should increase to 1
        self.assertEqual(len(self.u1.followers), 0)
        self.assertEqual(len(self.u1.following), 1)

        # user2 0 index if followers should be user1
        self.assertEqual(self.u2.followers[0].id, self.u1.id)
        self.assertEqual(self.u1.following[0].id, self.u2.id)

    def test_is_following(self):
        self.u1.following.append(self.u2)
        db.session.commit()

        self.assertTrue(self.u1.is_following(self.u2))
        # u2 is not following back u1, so it should return False
        self.assertFalse(self.u2.is_following(self.u1))

    def test_is_followed_by(self):
        self.u1.following.append(self.u2)
        db.session.commit()

        # return True: u1 is following u2
        self.assertTrue(self.u2.is_followed_by(self.u1))
        # return False: u2 is following u1
        self.assertFalse(self.u1.is_followed_by(self.u2))

    #########################
    ####sign up
    #############################################

    def test_signup(self):
        created_u = User.signup("signuptest", "signup@signup.com", "password", None)
        uid = 999999
        created_u.id = uid
        db.session.commit()

        created_user = User.query.get(uid)

        self.assertEqual(created_u.email, "signup@signup.com")
        self.assertEqual(created_u.username, "signuptest")

        # password tests due to hashing
        self.assertNotEqual(created_u.password, "password")
        self.assertTrue(created_u.password.startswith("$2b$"))

    def test_invalid_username(self):
        """Test for empty username field."""
        invalid_username = User.signup(None, "signup@gmail.com", "password", None)
        uid = 23456

        # set id to invalid_username
        invalid_username.id = uid

        with self.assertRaises(exc.IntegrityError) as context:
            db.session.commit()

    def test_invalid_email(self):
        """Test for empty email field."""
        invalid_email = User.signup("testname", None, "password", None)
        uid = 51655

        # set id to invalid_username
        invalid_email.id = uid

        with self.assertRaises(exc.IntegrityError) as context:
            db.session.commit()

    def test_invalid_password(self):
        """Test empty password"""

        with self.assertRaises(ValueError) as context:
            User.signup("testname", "email@signup.com", "", None)
        with self.assertRaises(ValueError) as context:
            User.signup("testname", "email@signup.com", None, None)

    #########################
    #### Authentication tests
    #############################################

    def test_valid_authentication(self):
        u = User.authenticate(self.u1.username, "password")

        self.assertIsNotNone(u)

        # checks if username is username
        self.assertEqual(u.username, self.u1.username)

        # checks if id is id
        self.assertEqual(u.id, self.uid1)

    def test_invalid_username_authentication(self):
        self.assertFalse(User.authenticate("wrongusername", "password"))

    def test_invalid_password_authentication(self):
        self.assertFalse(User.authenticate(self.u1.username, "wrongpassword"))
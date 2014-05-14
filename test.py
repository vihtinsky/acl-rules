import unittest
from acl import permissions, predicates

class User(object):
    def __init__(self, roles = []):
        self.roles = roles

    def is_superuser(self):
        return "superuser" in self.roles

class Book(object):
    def __init__(self, author):
        self.author = author

@predicates.predicate
def is_author(user, target):
    return target.author == user

class TestAcl(unittest.TestCase):

    def setUp(self):
        self.superuser = User(['superuser'])
        self.manager = User(['manager'])
        self.staff = User(['staff'])
        self.permissions = permissions.Permissions()

    def test_superuser_has_all(self):
        # make sure the shuffled sequence does not lose any elements
        self.assertTrue(self.permissions.has("books.edit", self.superuser))
        self.assertTrue(self.permissions.has("books.delete", self.superuser))
        #unset permission
        self.assertTrue(self.permissions.has("stuff.delete", self.superuser))

    def test_has_role(self):
        self.permissions.add("books.edit", predicates.has_roles(["manager"]))
        self.assertTrue(self.permissions.has("books.edit", self.superuser))
        self.assertTrue(self.permissions.has("books.edit", self.manager))
        self.assertFalse(self.permissions.has("books.edit", self.staff))

    def test_has_roles(self):
        self.permissions.add("books.edit", predicates.has_roles(["manager", "developer", "other", "r"]))
        self.assertTrue(self.permissions.has("books.edit", self.superuser))
        self.assertTrue(self.permissions.has("books.edit", self.manager))
        self.assertFalse(self.permissions.has("books.edit", self.staff))

    def test_is_author(self):
        user = User()
        user_two = User()
        book = Book(user)
        self.permissions.add("books.edit", predicates.has_roles(["manager"]) | is_author)
        self.assertTrue(self.permissions.has("books.edit", self.superuser, book))
        self.assertTrue(self.permissions.has("books.edit", self.manager, book))
        self.assertFalse(self.permissions.has("books.edit", self.staff))
        self.assertTrue(self.permissions.has("books.edit",user, book,  a="33"))
        self.assertFalse(self.permissions.has("books.edit",user_two, book))
        self.assertFalse(self.permissions.has("books.edit",user))

    def test_adding_multiple(self):
        user = User()
        user_two = User()
        book = Book(user)
        self.permissions.add("books.edit", predicates.has_roles(["manager"]))
        self.permissions.add("books.edit", is_author)
        self.assertTrue(self.permissions.has("books.edit", self.superuser, book))
        self.assertTrue(self.permissions.has("books.edit", self.manager, book))
        self.assertFalse(self.permissions.has("books.edit", self.staff))
        self.assertTrue(self.permissions.has("books.edit",user, book))
        self.assertFalse(self.permissions.has("books.edit",user_two, book))
        self.assertFalse(self.permissions.has("books.edit",user))

    def test_with_kwargs(self):
        user = User()
        user_two = User()
        book = Book(user)
        @predicates.predicate_context_only
        def allow_all(project_id=None):
            return project_id == 8
        self.permissions.add("books.edit", predicates.has_roles(["manager"]))
        self.permissions.add("books.edit", is_author)
        self.permissions.add("books.edit", allow_all)
        self.assertTrue(self.permissions.has("books.edit", self.superuser, book))
        self.assertTrue(self.permissions.has("books.edit", self.manager, book))
        self.assertFalse(self.permissions.has("books.edit", self.staff))
        self.assertTrue(self.permissions.has("books.edit",user, book))
        self.assertFalse(self.permissions.has("books.edit",user_two, book))
        self.assertFalse(self.permissions.has("books.edit",user))
        self.assertTrue(self.permissions.has("books.edit",user, project_id=8))
        self.assertTrue(self.permissions.has("books.edit",user_two, book, project_id=8))

    def test_add_and(self):
        @predicates.predicate_context_only
        def allow_all(project_id=None):
            return project_id == 8
        self.permissions.add("books.edit", predicates.has_roles(["manager"]))
        pd = predicates.has_roles(["manager"])
        self.permissions.add_and("books.edit", allow_all)
        #self.assertTrue(self.permissions.has("books.edit", self.superuser))
        #self.assertFalse(self.permissions.has("books.edit", self.manager))
        #self.assertFalse(self.permissions.has("books.edit", self.staff))
        self.assertTrue(self.permissions.has("books.edit", self.manager, project_id=8))
        self.assertFalse(self.permissions.has("books.edit", self.staff, project_id=8))


if __name__ == '__main__':
    unittest.main()


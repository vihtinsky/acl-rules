from functools import update_wrapper


class Predicate(object):
    def __init__(self, fn, name=None, num_args=1, with_kwargs=False):
        # fn can be a callable with any of the following signatures:
        #   - fn(obj=None, target=None)
        #   - fn(obj=None)
        #   - fn()
        assert callable(fn), 'The given predicate is not callable.'
        self.with_kwargs = with_kwargs
        if isinstance(fn, Predicate):
            fn, num_args, name = fn.fn, fn.num_args, name or fn.name

        self.fn = fn
        self.num_args = num_args
        self.name = name or fn.__name__

    def __repr__(self):
        return '<%s:%s object at %s>' % (
            type(self).__name__, str(self), hex(id(self)))

    def __str__(self):
        return self.name

    def __call__(self, *args, **kwargs):
        # this method is defined as variadic in order to not mask the
        # underlying callable's signature that was most likely decorated
        # as a predicate. internally we consistently call ``test`` that
        # provides a single interface to the callable.
        return self.fn(*args, **kwargs)

    def __and__(self, other):
        def AND(obj=None, target=None, **kwargs):
            return self.test(obj, target, **kwargs) and other.test(obj, target, **kwargs)
        return type(self)(AND, '(%s & %s)' % (self.name, other.name), num_args=2, with_kwargs=True)

    def __or__(self, other):
        def OR(obj=None, target=None, **kwargs):
            return self.test(obj, target, **kwargs) or other.test(obj, target, **kwargs)
        return type(self)(OR, '(%s | %s)' % (self.name, other.name), num_args=2, with_kwargs=True)

    def __xor__(self, other):
        def XOR(obj=None, target=None, **kwargs):
            return self.test(obj, target, **kwargs) ^ other.test(obj, target, **kwargs)
        return type(self)(XOR, '(%s ^ %s)' % (self.name, other.name), num_args=2, with_kwargs=True)

    def __invert__(self):
        def INVERT(obj=None, target=None, **kwargs):
            return not self.test(obj, target, **kwargs)
        if self.name.startswith('~'):
            name = self.name[1:]
        else:
            name = '~' + self.name
        return type(self)(INVERT, name, num_args=2, with_kwargs=True)

    def test(self, obj=None, target=None, **kwargs):
        # we setup a list of function args depending on the number of
        # arguments accepted by the underlying callback.
        if self.num_args == 2:
            args = (obj, target)
        elif self.num_args == 1:
            args = (obj,)
        else:
            args = ()
        if not self.with_kwargs:
            kwargs = {}
        try:
            return bool(self.fn(*args, **kwargs))
        except:
            return False


def predicate(fn=None, name=None, num_args=2, with_kwargs=False):
    """
    Decorator that constructs a ``Predicate`` instance from any function::

        >>> @predicate
        ... def is_book_author(user, book):
        ...     return user == book.author
        ...
    """
    if not name and not callable(fn):
        name = fn
        fn = None

    def inner(fn):
        if isinstance(fn, Predicate):
            return fn
        p = Predicate(fn, name, num_args=num_args, with_kwargs=with_kwargs)
        update_wrapper(p, fn)
        return p

    if fn:
        return inner(fn)
    else:
        return inner


# Predefined predicates
def predicate_user_only(fn=None, name=None):
    return predicate(fn=fn, name=name, num_args=1)

def predicate_context_only(fn=None, name=None):
    def inner_context(user, target, **kwargs):
        return fn(**kwargs)
    return predicate(fn=inner_context, name=name, num_args=2, with_kwargs=True)

def predicate_with_context(fn=None, name=None):
    return predicate(fn=fn, name=name, num_args=2, with_kwargs=True)

always_allow = predicate(lambda: True, name='always_allow')
always_deny  = predicate(lambda: False, name='always_deny')


@predicate_user_only
def is_authenticated(user):
    if not hasattr(user, 'is_authenticated'):
        return False  # not a user model
    return user.is_authenticated()


@predicate_user_only
def is_superuser(user):
    if not hasattr(user, 'is_superuser'):
        return False  # swapped user model, doesn't support is_superuser
    return user.is_superuser


@predicate_user_only
def is_staff(user):
    if not hasattr(user, 'is_staff'):
        return False  # swapped user model, doesn't support is_staff
    return user.is_staff


@predicate_user_only
def is_active(user):
    if not hasattr(user, 'is_active'):
        return False  # swapped user model, doesn't support is_active
    return user.is_active


def has_roles(roles):
    assert len(roles) > 0, 'You must provide at least one group name'

    if len(roles) > 3:
        r = roles[:3] + ('...',)
    else:
        r = roles

    name = 'has_roles:%s' % ','.join(r)

    @predicate_user_only(name)
    def fn(user):
        if not hasattr(user, 'roles'):
            return False  # swapped user model, doesn't support groups
        return set(roles).issubset(user.roles)

    return fn


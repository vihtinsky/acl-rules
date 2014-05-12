class Permissions(dict):

    def add(self, name, predicate):
        if name in self:
            self[name] = self[name] | predicate
        else:
            self[name] = predicate

    def add_and(self, name, predicate):
        if name in self:
            self[name] = self[name] & predicate
        else:
            self[name] = predicate

    def has(self, name, user, target=None, **kwargs):
        if user.is_superuser():
            return True
        return name in self and self[name].test(user, target, **kwargs)

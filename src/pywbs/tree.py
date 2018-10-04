class DuplicateViolationError(RuntimeError):
    pass


class UniformityViolationError(RuntimeError):
    pass


class NotFound(RuntimeError):
    pass


class FunctionEvaluationError(RuntimeError):
    pass


class BreakdownStructure:
    class TreeNavigationError(RuntimeError):
        pass

    @property
    def level(self):
        def _l(node):
            return 0 if node.is_root else 1 + _l(node.parent)
        return _l(self)

    def __hash__(self) -> int:
        return hash(f'{self.level}:{self.name}')

    def __init__(self, name=None, uniform=False, attributes=None, allow_duplicates=False) -> None:
        """If name is None then this is a root node. If uniform then only children of exactly same
        class will be allowed"""
        attributes = attributes or {}
        self.name = name
        self.parent = None
        self.children = []
        self.allow_duplicates = allow_duplicates
        self.uniform = uniform
        for k, v in attributes.items():
            setattr(self, k, v)

    def get_or_create_child(self, name, attributes=None):
        attributes = attributes or {}
        existing = self.find_by_name(name, fail=False, direct_children=not self.allow_duplicates)
        if existing:
            return existing
        return self.add_child(self.__class__(name, attributes=attributes))

    def add_child(self, child, skip=False):
        """Adds a BreakdownStructure object as a child
            If existing and skip=True then return the existing node rather than raising the exception
        """
        if type(child) == str:
            child = self.__class__(child)
        if self.uniform and type(child) != type(self):
            raise UniformityViolationError(f"Can only add a {type(self)} child object")
        elif not isinstance(child, BreakdownStructure):
            raise UniformityViolationError("Can only add a BreakdownStructure child object")
        found = self.find_by_name(child.name, fail=False, direct_children=self.allow_duplicates)
        if found:
            if skip:
                return found
            else:
                raise DuplicateViolationError(f"Child '{child.name}' already exists")
        self.children.append(child)
        child.parent = self
        child.allow_duplicates = self.allow_duplicates
        child.uniform = self.uniform
        return child

    def add_children(self, children):
        for child in children:
            if isinstance(child, BreakdownStructure):
                self.add_child(child)
            else:
                self.add_child(BreakdownStructure(child))

    @property
    def children_names(self):
        return self.get_children_names()

    def get_children_names(self, upper=False):
        if upper:
            return [c.name.upper() for c in self.children]
        else:
            return [c.name for c in self.children]

    def __str__(self) -> str:
        return self.name if self.name else ''

    @property
    def root(self):
        return self if not self.name else self.parent.root

    @property
    def is_root(self):
        return self.parent is None

    @property
    def is_leaf(self):
        return len(self.children) == 0

    @property
    def is_top(self):
        return bool(self.parent and self.parent.parent is None)

    @property
    def top(self):
        assert not self.is_root, BreakdownStructure.TreeNavigationError("Can't navigate to top from root")
        return self if self.is_top else self.parent.top

    def get_ancestors(self, include_self=False):
        if self.is_root:
            return []
        elif self.is_top:
            if include_self:
                return [self, ]
            else:
                return []
        else:
            if include_self:
                return [self, ] + self.parent.get_ancestors(include_self=True,)
            else:
                return self.parent.get_ancestors(include_self=True,)

    @property
    def ancestors(self):
        return self.get_ancestors()

    @property
    def is_empty(self):
        return self.root.children == []

    def find_by_name(self, name, fail=True, direct_children=False):
        return self.find_by_func(lambda x: x.name == name, fail=fail, direct_children=direct_children)

    def find_item(self, item, fail=True, direct_children=False):
        self.find_by_name(item.name, fail=fail, direct_children=direct_children)

    def find_by_func(self, func, fail=True, direct_children=False, skip_errors=False):
        try:
            if not self.is_root and func(self):
                return self
            elif direct_children:
                for x in self.children:
                    if func(x):
                        return x
            else:
                for x in self.root:
                    if func(x):
                        return x
        except Exception as e:
            if not skip_errors:
                raise FunctionEvaluationError(e)
        if fail:
            raise NotFound(f"Node could not be found")
        return None


    def tree(self, level=0):
        """returns a tree representation of the tree"""
        nl, root = '\n', '\\'

        return f"{nl if level > 0 else ''}" + \
               '  '*level + '\\' + \
               f"{self.name if self and self.name else ''}" + \
               ''.join([x.tree(level=level + 1) for x in self.children])

    def __iter__(self):
        self._i = -1
        self._elements = self._visit()
        return self

    def _visit(self):
        ret = [] if self.is_root else [self, ]
        for z in [x._visit() for x in self.children]:
            ret.extend(z)
        return ret

    def __next__(self):
        if self._i == len(self._elements) - 1:
            raise StopIteration()
        self._i += 1
        return self._elements[self._i]

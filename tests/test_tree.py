import pytest
from pytest import raises

from pywbs.tree import BreakdownStructure, NotFound, DuplicateViolationError, UniformityViolationError, \
    FunctionEvaluationError


@pytest.fixture
def empty_tree():
    return BreakdownStructure()


@pytest.fixture
def dummy_tree(empty_tree):
    a = empty_tree.add_child(BreakdownStructure('a'))
    b = empty_tree.add_child(BreakdownStructure('b'))
    c = empty_tree.add_child(BreakdownStructure('c'))
    a1 = a.add_child(BreakdownStructure('a.1'))
    a2 = a.add_child(BreakdownStructure('a.2'))
    a2.add_child(BreakdownStructure('a.2.1'))
    c1 = c.add_child(BreakdownStructure('c.1'))
    return empty_tree


@pytest.fixture
def empty_tree_dup_ok():
    return BreakdownStructure(allow_duplicates=True)


@pytest.fixture
def empty_uniform_tree():
    return BreakdownStructure(uniform=True)


@pytest.fixture
def single_node_tree():
    ret = BreakdownStructure()
    ret.get_or_create_child("son")
    return ret


class TestEmptyTree:
    def test_empty_is___(self, empty_tree):
        assert empty_tree.is_root, "Empty tree node should be 'root'"
        assert empty_tree.is_leaf, "Empty tree node should be 'leaf'"
        assert not empty_tree.is_top, "Empty tree node should not be 'top'"
        assert empty_tree.parent is None

    def test_get_or_create__is___(self, empty_tree):
        obj = empty_tree.get_or_create_child("son")
        assert empty_tree.is_root, "Root should still be 'root'"
        assert not empty_tree.is_leaf, "Root should not be 'leaf' anymore"
        assert not empty_tree.is_top, "Root should still not be 'top'"
        assert not obj.is_root, "Child should not be 'root'"
        assert obj.is_leaf, "Child hould be 'leaf'"
        assert obj.is_top, "Child should be 'top'"
        assert empty_tree.parent is None

    def test_get_or_create__children(self, empty_tree):
        obj = empty_tree.get_or_create_child("son")
        assert type(obj) == type(empty_tree), "Child should be object just created"
        assert obj.parent == empty_tree, "Parent mismatch"

    def test_fx_tree_empty(self, empty_tree):
        assert empty_tree.tree() == '\\'

    def test_add_first_child(self, empty_tree):
        son = BreakdownStructure("1st_son")
        assert len(empty_tree.children) == 0
        empty_tree.add_child(son)
        assert len(empty_tree.children) == 1
        assert son.parent == empty_tree

    def test_find_by_func_empty(self, empty_tree):
        with raises(NotFound):
            empty_tree.find_by_func(lambda x: True)
        assert empty_tree.find_by_func(lambda x: True, fail=False) is None
        with raises(NotFound):
            empty_tree.find_by_func(lambda x: 1/0)
        assert empty_tree.find_by_func(lambda x: 1 / 0, fail=False, skip_errors=True) is None

    def test_find_by_func_non_empty(self, dummy_tree):
        assert dummy_tree.find_by_func(lambda x: x.name.endswith('1')).name == "a.1"
        with raises(NotFound):
            dummy_tree.find_by_func(lambda x: x.name.endswith('z'))
        assert dummy_tree.find_by_func(lambda x: x.name.endswith('z'), fail=False) is None
        with raises(FunctionEvaluationError):
            dummy_tree.find_by_func(lambda x: x.name.endswith(str(1/0)))
        assert dummy_tree.find_by_func(lambda x: x.name.endswith(str(1/0)), fail=False, skip_errors=True) is None
        with raises(NotFound):
            assert dummy_tree.find_by_func(lambda x: x.name.endswith(str(1/0)), skip_errors=True) is None


class TestSingleNode:
    def test_fx_tree_empty(self, single_node_tree):
        assert single_node_tree.tree() == "\\\n  \\son"

    def test_root_is___(self, single_node_tree):
        assert single_node_tree.is_root, "Root should be 'root'"
        assert not single_node_tree.is_leaf, "Root  should be 'leaf'"
        assert not single_node_tree.is_top, "Root  should not be 'top'"

    def test_leaf_is___(self, single_node_tree):
        assert not single_node_tree.children[0].is_root, "Child should not be 'root'"
        assert single_node_tree.children[0].is_leaf, "Child should be 'leaf'"
        assert single_node_tree.children[0].is_top, "1st level children should be 'top'"

    def test_leaf_has_no_children(self, single_node_tree):
        assert single_node_tree.children[0].children == [], "Leaf should have no children"


class TestTreeVisit:
    def test_preorder(self, dummy_tree):
        assert [x.name for x in dummy_tree] == ['a', 'a.1', 'a.2', 'a.2.1', 'b', 'c', 'c.1']

    def test_preorder_empty(self, empty_tree):
        assert [x for x in empty_tree] == []


class TestFinders:
    def test_find_by_name(self, dummy_tree):
        assert dummy_tree.find_by_name('a.2.1').name == 'a.2.1'
        assert dummy_tree.find_by_name('a.2').find_by_name('c.1').name == 'c.1'
        with raises(NotFound):
            dummy_tree.find_by_name('a.2').find_by_name('c.1', direct_children=True).name
        ret = dummy_tree.find_by_name('a.2').find_by_name('c.1', direct_children=True, fail=False)
        assert ret is None


class TestLevel:
    def test_level(self, empty_tree, dummy_tree):
        assert empty_tree.level == 0
        assert dummy_tree.level == 0
        assert dummy_tree.find_by_name("b").level== 1
        assert dummy_tree.find_by_name('a.2.1').level== 3
        assert dummy_tree.find_by_name('c.1').level== 2


class TestAncestors:
    def test_ancestors_empty(self, empty_tree):
        assert empty_tree.ancestors == []
        assert empty_tree.get_ancestors(include_self=True) == []

    def test_ancestors_tree(self, dummy_tree):
        assert dummy_tree.ancestors == []
        assert dummy_tree.get_ancestors(include_self=True) == []
        assert dummy_tree.children[2].ancestors == []
        assert dummy_tree.children[2].get_ancestors(include_self=True) == [dummy_tree.children[2], ]
        assert dummy_tree.children[2].children[0].get_ancestors(include_self=True) == \
               [dummy_tree.children[2].children[0], dummy_tree.children[2]]

class TestTreeDuplicates:
    def test_dupnok(self, empty_tree):
        a, b = empty_tree.add_child(BreakdownStructure('A')), empty_tree.add_child(BreakdownStructure('B'))
        with raises(DuplicateViolationError, message="DUPNOK Cannot add duplicate in same level"):
            empty_tree.add_child(BreakdownStructure('A'))
        with raises(DuplicateViolationError, message="DUPNOK Cannot add duplicate in other level"):
            b.add_child(BreakdownStructure('A'))

    def test_dupok(self, empty_tree_dup_ok):
        a, b = empty_tree_dup_ok.add_child(BreakdownStructure('A')), empty_tree_dup_ok.add_child(BreakdownStructure('B'))
        with raises(DuplicateViolationError, message="DUPOK Cannot add duplicate in same level"):
            empty_tree_dup_ok.add_child(BreakdownStructure('A'))
        try:
            b.add_child(BreakdownStructure('A'))
        except DuplicateViolationError:
            assert False, "Should be able to add duplicate in other level"


class TestTreeUniformity:
    def test_uniform(self, empty_uniform_tree):
        class K(BreakdownStructure):
            pass
        tree = K(uniform=True)
        with raises(UniformityViolationError, message="Should raise UniformityViolationError"):
            tree.add_child(BreakdownStructure('dummy'))
        with raises(UniformityViolationError, message="Should raise UniformityViolationError"):
            empty_uniform_tree.add_child(K('dummy'))

    def test_non_uniform(self, empty_uniform_tree):
        class K(BreakdownStructure):
            pass
        tree = K(uniform=True)
        try:
            tree.add_child(BreakdownStructure('dummy'))
        except UniformityViolationError:
            "Should NOT raise UniformityViolationError"
        try:
            empty_uniform_tree.add_child(K('dummy'))
        except UniformityViolationError:
            "Should NOT raise UniformityViolationError"

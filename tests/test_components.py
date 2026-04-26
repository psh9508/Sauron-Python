from sauron_python.core.grouping.component import GroupingComponent


class TestGroupingComponent:
    def test_leaf_component_hash(self):
        c = GroupingComponent(id="type", values=["ValueError"])
        h = c.get_hash()
        assert h is not None
        assert len(h) == 32

    def test_same_values_same_hash(self):
        c1 = GroupingComponent(id="type", values=["ValueError"])
        c2 = GroupingComponent(id="type", values=["ValueError"])
        assert c1.get_hash() == c2.get_hash()

    def test_different_values_different_hash(self):
        c1 = GroupingComponent(id="type", values=["ValueError"])
        c2 = GroupingComponent(id="type", values=["TypeError"])
        assert c1.get_hash() != c2.get_hash()

    def test_non_contributing_returns_none(self):
        c = GroupingComponent(
            id="value", values=["some error"], contributes=False, hint="ignored"
        )
        assert c.get_hash() is None

    def test_empty_values_returns_none(self):
        c = GroupingComponent(id="empty", values=[])
        assert c.get_hash() is None

    def test_nested_iter_values(self):
        child1 = GroupingComponent(id="filename", values=["app.py"])
        child2 = GroupingComponent(id="function", values=["main"])
        parent = GroupingComponent(id="frame", values=[child1, child2])

        assert parent.iter_values() == ["app.py", "main"]

    def test_nested_non_contributing_child_excluded(self):
        child1 = GroupingComponent(id="filename", values=["app.py"])
        child2 = GroupingComponent(
            id="function", values=["internal"], contributes=False
        )
        parent = GroupingComponent(id="frame", values=[child1, child2])

        assert parent.iter_values() == ["app.py"]

    def test_non_contributing_parent_excludes_all(self):
        child = GroupingComponent(id="filename", values=["app.py"])
        parent = GroupingComponent(id="frame", values=[child], contributes=False)

        assert parent.iter_values() == []
        assert parent.get_hash() is None

    def test_deeply_nested_tree(self):
        frame1 = GroupingComponent(
            id="frame",
            values=[
                GroupingComponent(id="filename", values=["app.py"]),
                GroupingComponent(id="function", values=["handle"]),
            ],
        )
        frame2 = GroupingComponent(
            id="frame",
            values=[
                GroupingComponent(id="filename", values=["views.py"]),
                GroupingComponent(id="function", values=["index"]),
            ],
        )
        stacktrace = GroupingComponent(id="stacktrace", values=[frame1, frame2])
        exception_type = GroupingComponent(id="type", values=["ValueError"])
        root = GroupingComponent(
            id="exception", values=[exception_type, stacktrace]
        )

        values = root.iter_values()
        assert values == ["ValueError", "app.py", "handle", "views.py", "index"]
        assert root.get_hash() is not None

    def test_as_dict_serialization(self):
        child = GroupingComponent(id="type", values=["ValueError"])
        parent = GroupingComponent(
            id="exception", values=[child], hint="test hint"
        )

        d = parent.as_dict()
        assert d["id"] == "exception"
        assert d["contributes"] is True
        assert d["hint"] == "test hint"
        assert len(d["values"]) == 1
        assert d["values"][0]["id"] == "type"
        assert d["values"][0]["values"] == ["ValueError"]

    def test_as_dict_with_non_contributing(self):
        c = GroupingComponent(
            id="value",
            values=["ignored msg"],
            contributes=False,
            hint="stacktrace takes precedence",
        )
        d = c.as_dict()
        assert d["contributes"] is False
        assert d["hint"] == "stacktrace takes precedence"

    def test_repr(self):
        c = GroupingComponent(id="type", values=["ValueError"])
        r = repr(c)
        assert "type" in r
        assert "ValueError" in r

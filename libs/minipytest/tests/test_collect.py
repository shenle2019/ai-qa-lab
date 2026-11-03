def test_collects_functions_in_source_order(run_suite):
    result = run_suite(
        {
            "test_order.py": """
                def test_second():
                    pass

                def test_first():
                    pass
            """
        }
    )
    assert [item.case.name for item in result.tests] == ["test_second", "test_first"]


def test_collects_classes_and_skips_helpers(run_suite):
    result = run_suite(
        {
            "test_classes.py": """
                def helper():
                    pass

                def test_plain():
                    pass

                class TestGroup:
                    def test_b(self):
                        pass

                    def test_a(self):
                        pass

                    def not_a_test(self):
                        pass
            """
        }
    )
    ids = ["::".join(item.case.nodeid.split("::")[1:]) for item in result.tests]
    assert ids == ["test_plain", "TestGroup::test_b", "TestGroup::test_a"]


def test_stacked_parametrize_uses_signature_order(run_suite):
    result = run_suite(
        {
            "test_params.py": """
                from libs.minipytest import parametrize

                @parametrize("x", [1, 2], ids=["one", "two"])
                @parametrize("y", ["a", "b"])
                def test_combo(x, y):
                    pass
            """
        }
    )
    assert [item.case.param_id for item in result.tests] == ["one-a", "one-b", "two-a", "two-b"]


def test_duplicate_param_ids_are_disambiguated(run_suite):
    result = run_suite(
        {
            "test_dupes.py": """
                from libs.minipytest import parametrize

                @parametrize("x", [1, 1])
                def test_dupe(x):
                    pass
            """
        }
    )
    assert [item.case.param_id for item in result.tests] == ["1", "1_1"]


def test_collection_error_is_reported(run_suite):
    result = run_suite({"test_broken.py": "raise RuntimeError('broken import')"})
    assert result.exit_code == 2
    assert len(result.collection_errors) == 1
    assert "broken import" in result.collection_errors[0].message


def test_parametrize_name_must_exist(run_suite):
    result = run_suite(
        {
            "test_bad_param.py": """
                from libs.minipytest import parametrize

                @parametrize("missing", [1])
                def test_bad(value):
                    pass
            """
        }
    )
    assert result.exit_code == 2
    assert "missing" in result.collection_errors[0].message

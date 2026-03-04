import os

import pytest


@pytest.fixture()
def switch_tmp_path(tmp_path):
    """
    Switch to temporary path

    Args:
        tmp_path: pytest includes a very useful built-in function-scoped Fixture,
                  which provides a temporary and independent directory for each test case.
    """
    cwd = os.getcwd()
    os.chdir(tmp_path)
    yield tmp_path
    os.chdir(cwd)

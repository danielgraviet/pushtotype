import pushtotype


def test_import():
    assert pushtotype is not None


def test_version():
    assert isinstance(pushtotype.__version__, str)

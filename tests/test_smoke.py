import whisperflow


def test_import():
    assert whisperflow is not None


def test_version():
    assert isinstance(whisperflow.__version__, str)

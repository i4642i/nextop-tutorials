"""get_paper.py says what went wrong (service and reason) and exits 1; it never leaves a half file behind."""
import importlib
import io
import urllib.error
import urllib.request

import pytest


@pytest.fixture()
def get_paper(monkeypatch, tmp_path):
    import sys
    root = str(__import__("pathlib").Path(__file__).resolve().parent.parent)
    monkeypatch.syspath_prepend(root)
    sys.modules.pop("get_paper", None)
    mod = importlib.import_module("get_paper")
    monkeypatch.setattr(mod, "OUT", tmp_path / "input" / "paper.pdf")
    return mod


def _raise(exc):
    def urlopen(*a, **k):
        raise exc
    return urlopen


def test_an_http_error_names_the_service_and_the_status(get_paper, monkeypatch, capsys):
    err = urllib.error.HTTPError(get_paper.URL, 503, "Service Unavailable", {}, io.BytesIO(b""))
    monkeypatch.setattr(urllib.request, "urlopen", _raise(err))
    assert get_paper.main() == 1
    msg = capsys.readouterr().err
    assert "arXiv" in msg and "503" in msg and "make_sample_pdf.py" in msg
    assert not get_paper.OUT.exists()


def test_a_timeout_and_a_connection_failure_are_reported(get_paper, monkeypatch, capsys):
    monkeypatch.setattr(urllib.request, "urlopen", _raise(TimeoutError("timed out")))
    assert get_paper.main() == 1 and "arXiv" in capsys.readouterr().err
    monkeypatch.setattr(urllib.request, "urlopen", _raise(urllib.error.URLError("no route")))
    assert get_paper.main() == 1
    msg = capsys.readouterr().err
    assert "arXiv" in msg and "no route" in msg


def test_an_answer_that_is_not_a_pdf_is_a_failure(get_paper, monkeypatch, capsys):
    class Res(io.BytesIO):
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False
    monkeypatch.setattr(urllib.request, "urlopen", lambda *a, **k: Res(b"<html>blocked</html>"))
    assert get_paper.main() == 1 and "arXiv" in capsys.readouterr().err
    assert not get_paper.OUT.exists()


def test_a_real_pdf_is_saved(get_paper, monkeypatch):
    class Res(io.BytesIO):
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False
    monkeypatch.setattr(urllib.request, "urlopen", lambda *a, **k: Res(b"%PDF-1.7 test"))
    assert get_paper.main() == 0 and get_paper.OUT.read_bytes().startswith(b"%PDF")

"""Downloads the example paper "Attention Is All You Need" into input/ (it is not part of this tutorial).

Run:  python get_paper.py

Vaswani, Shazeer, Parmar, Uszkoreit, Jones, Gomez, Kaiser, Polosukhin: "Attention Is All You Need", 2017,
https://arxiv.org/abs/1706.03762. The PDF is fetched from arXiv to your computer only; it is never committed or shared
by this tutorial (input/*.pdf is in .gitignore). The paper itself says: "Provided proper attribution is provided, Google
hereby grants permission to reproduce the tables and figures in this paper solely for use in journalistic or scholarly works."
"""
import pathlib
import sys
import urllib.error
import urllib.request

URL = "https://arxiv.org/pdf/1706.03762"
OUT = pathlib.Path(__file__).resolve().parent / "input" / "attention_is_all_you_need.pdf"


def fail(why: str) -> int:
    """Say what went wrong (the service and the reason) and how to get the file by hand; the exit code is 1."""
    print(f"論文をダウンロードできませんでした: {why}. " + f"{URL} から手でダウンロードして {OUT} として保存するか、代わりにサンプル PDF を使ってください: python make_sample_pdf.py", file=sys.stderr)
    return 1


def main() -> int:
    if OUT.is_file():
        print(f"already there: {OUT}")
        return 0
    OUT.parent.mkdir(exist_ok=True)
    print(f"downloading {URL} ...")
    try:
        req = urllib.request.Request(URL, headers={"User-Agent": "nextop-tutorial-5 (downloads one PDF)"})
        with urllib.request.urlopen(req, timeout=60) as r:
            data = r.read()
    except urllib.error.HTTPError as e:                 # the server answered with an error status
        return fail(f"arXiv が HTTP {e.code} {e.reason} で答えました")
    except TimeoutError:
        return fail("arXiv が 60 秒以内に答えませんでした")
    except (urllib.error.URLError, OSError) as e:
        return fail(f"arXiv につながりませんでした（{getattr(e, 'reason', e)}）")
    if not data.startswith(b"%PDF"):
        return fail(f"arXiv（{URL}）が PDF ではないものを返しました")
    OUT.write_bytes(data)
    print(f"saved {OUT} ({len(data):,} bytes)")
    print('Paper: Vaswani et al., "Attention Is All You Need" (2017), https://arxiv.org/abs/1706.03762. Credit the authors when you show it.')
    return 0


if __name__ == "__main__":
    sys.exit(main())

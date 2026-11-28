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
    print(f"논문을 내려받지 못했습니다: {why}. " + f"{URL} 에서 직접 받아 {OUT} 로 저장하거나, 예제 PDF를 대신 쓰세요: python make_sample_pdf.py", file=sys.stderr)
    return 1


def main() -> int:
    if OUT.is_file():
        print(f"already there: {OUT}")
        return 0
    OUT.parent.mkdir(exist_ok=True)
    print(f"downloading {URL} ...")
    try:
        req = urllib.request.Request(URL, headers={"User-Agent": "nextop-tutorial-3 (downloads one PDF)"})
        with urllib.request.urlopen(req, timeout=60) as r:
            data = r.read()
    except urllib.error.HTTPError as e:                 # the server answered with an error status
        return fail(f"arXiv가 HTTP {e.code} {e.reason} 로 답했습니다")
    except TimeoutError:
        return fail("arXiv가 60초 안에 답하지 않았습니다")
    except (urllib.error.URLError, OSError) as e:
        return fail(f"arXiv에 연결하지 못했습니다 ({getattr(e, 'reason', e)})")
    if not data.startswith(b"%PDF"):
        return fail(f"arXiv ({URL}) 가 PDF가 아닌 것을 돌려줬습니다")
    OUT.write_bytes(data)
    print(f"saved {OUT} ({len(data):,} bytes)")
    print('Paper: Vaswani et al., "Attention Is All You Need" (2017), https://arxiv.org/abs/1706.03762. Credit the authors when you show it.')
    return 0


if __name__ == "__main__":
    sys.exit(main())

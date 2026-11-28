"""Draws a saved deck again with another theme, without any model.

Run:  python render_deck.py output/attention_is_all_you_need_deck.json dark
The deck (output/<name>_deck.json) is saved by the flow's last block; it holds every slide's text and the values the
program placed (table cells, figure pictures, captions, pages). The fit check measured the text in every theme, so the
same slides fit in any of them.
"""
import json
import pathlib
import sys

from functions._deck import THEMES, theme_code
from functions._render import save_deck


def main(argv: list[str]) -> int:
    if len(argv) != 2 or theme_code(argv[1]) is None:
        print(f"usage: python render_deck.py <output/name_deck.json> <{' | '.join(THEMES)}>")
        return 2
    path = pathlib.Path(argv[0])
    deck = json.loads(path.read_text(encoding="utf-8"))          # figure pictures: relative to output/
    stem = path.name.removesuffix("_deck.json")
    saved = save_deck(deck, theme_code(argv[1]), stem)
    print(f"saved {saved['pptx']}, {len(saved['previews'])} previews and {saved['overview']}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

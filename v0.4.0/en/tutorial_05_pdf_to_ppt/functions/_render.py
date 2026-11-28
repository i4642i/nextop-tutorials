"""Saving a deck: the .pptx, one PNG per slide, an overview picture, and the deck itself (JSON) for re-rendering."""
import copy
import json
import pathlib
import shutil

from functions._common import data_dir
from functions._deck import THEMES
from functions._pptx import build_pptx
from functions._preview import contact_sheet, render_all


def save_deck(deck: dict, theme: str, stem: str) -> dict:
    """Writes output/<stem>_<theme>.pptx, output/<stem>_<theme>/slide_NN.png, output/<stem>_<theme>_overview.png and
    output/<stem>_deck.json (with the figure pictures copied next to it). Returns the paths."""
    if theme not in THEMES:
        raise ValueError(f"unknown theme {theme!r}; one of {', '.join(THEMES)}")
    out = data_dir() / "output"
    assets = out / f"{stem}_assets"
    assets.mkdir(parents=True, exist_ok=True)
    deck = copy.deepcopy(deck)
    stored = copy.deepcopy(deck)
    for s, kept in zip(deck["slides"], stored["slides"]):
        f = s.get("figure")
        if not f:
            continue
        source = pathlib.Path(f["image"]) if pathlib.Path(f["image"]).is_absolute() else out / f["image"]
        target = assets / source.name             # keep the picture: a run's file server is gone after the run
        if source.resolve() != target.resolve():
            shutil.copyfile(source, target)
        f["image"] = str(target)
        kept["figure"]["image"] = f"{assets.name}/{target.name}"      # the saved deck names it relative to output/
    deck_file = out / f"{stem}_deck.json"
    deck_file.write_text(json.dumps(stored, ensure_ascii=False, indent=1), encoding="utf-8")
    pptx = out / f"{stem}_{theme}.pptx"
    pptx.write_bytes(build_pptx(deck, theme))
    folder = out / f"{stem}_{theme}"
    folder.mkdir(exist_ok=True)
    for old in folder.glob("slide_*.png"):
        old.unlink()
    pngs = render_all(theme, deck)
    previews = []
    for n, data in enumerate(pngs, 1):
        path = folder / f"slide_{n:02d}.png"
        path.write_bytes(data)
        previews.append(path)
    overview = out / f"{stem}_{theme}_overview.png"
    overview.write_bytes(contact_sheet(pngs))
    return {"pptx": pptx, "previews": previews, "overview": overview, "deck": deck_file}

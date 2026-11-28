"""Fill the file server bookings with the example bookings of data/seed_bookings.json (flow `seed`), counted from
tomorrow, and write schedule.html.

    python seed.py          add them (a booking that already exists is left alone)
    python seed.py --reset  start empty first: delete the stores of bookings and consult
                            (customers is kept; delete file_servers/customers/store by hand to clear it too)
"""
import pathlib
import shutil
import sys

from nextop.core.load import load_project
from nextop.runtime.flow import run_flow

from functions._salon import ROOT, data_dir

RESET = ("bookings", "consult")


def main(reset: bool = False, project: str | None = None) -> int:
    root = pathlib.Path(project or ROOT)
    if reset:
        for name in RESET:
            shutil.rmtree(root / "file_servers" / name / "store", ignore_errors=True)
    res = run_flow(load_project(str(root)), "seed", {"seed": "examples"})
    if not res.ok:
        print(f"seed failed: {res.reason}")
        return 1
    got = res.outputs["seed_bookings"]["seeded"]
    print(f"{got['new']} example bookings written ({got['kept']} were there); schedule: {data_dir() / 'schedule.html'}")
    return 0


if __name__ == "__main__":
    sys.exit(main("--reset" in sys.argv))

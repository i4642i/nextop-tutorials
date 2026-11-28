"""Answer a booking from the command line (when the chat server is not reachable from the designer's phone).

    python approve.py <booking id>             approve: confirmed, the customer gets the confirmation text
    python approve.py <booking id> --decline   decline: the slot is free again, the customer gets a short text
"""
import sys

from functions._approval import decide


def main(argv: list[str]) -> int:
    ids = [a for a in argv if not a.startswith("--")]
    if len(ids) != 1:
        print(__doc__)
        return 2
    code, message = decide(ids[0], approve="--decline" not in argv, check_token=False)
    print(message)
    return 1 if code == "refused" else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

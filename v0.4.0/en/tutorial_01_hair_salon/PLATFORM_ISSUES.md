# Platform issues found while building tutorial 1 (US edition)

This edition is a port of the Korean edition's navigator design (`../../ko/tutorial_01_hair_salon`). The issues found while that design was built, and how each was fixed or left, are in `../../ko/tutorial_01_hair_salon/PLATFORM_ISSUES.md` (T1-T6 for nextop 0.4.0). This file lists only what the port itself showed.

## nextop 0.4.0 from PyPI (2026-11-28)

Checked with nextop 0.4.0 installed from PyPI by `setup.bat` into a fresh `.venv` (no platform checkout on the path). `nextop check`: OK; offline tests: 45 passed. Real chats: a local model with thinking on, 4 chats (booking with a style and a taken time, two requests in one message, see / change / cancel with a wrong phone first, a refused phone). Nothing was worked around by changing the platform.

### P1. The flow check needs the LLM key for a flow of functions only (low; same as ko T4)
- `python seed.py --reset` (flow `seed`, one function, no worker) stops with `FlowError: the flow check failed` while `LLM_API_KEY` is empty, and `nextop check` reports `[error] adapter llm.default: API key missing`. Nothing in the flow calls a model.
- Effect: a reader who seeds before filling `.env` gets a failure that does not name the cause. setup.bat already tells them to fill `.env` first.

### Fixed since earlier editions
- The `country` setting of the `phone` field type (0.3.1) is accepted in a type folder's `type.json`: the bookings and customers phone fields use `"country": "US"`, and the edition no longer ejects its own phone part.

### Notes (model, not platform)
- No reply mixed another language. The English-only reply check refused 0 drafts; the reply LLM checker refused 2 and the rewrites passed (an invented "no charge for canceling"; a phone explanation that did not say the booking cannot go on without it).
- The model sometimes offered two or three times where the step asks for one, and once suggested a morning time before the designer's start.

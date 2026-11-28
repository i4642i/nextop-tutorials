# Platform issues found while building tutorial 1

Found with the platform checkout on branch naw-steps (nextop 0.2.0). Nothing was worked around by changing the platform.

## 1. The installed "nextop 0.2.0" wheel has no tables, access or bm25 (blocker for readers)
- Tried: `python -m pytest` with the system Python 3.11, where `pip` gave nextop 0.2.0 (C:\...\Python311\Lib\site-packages\nextop).
- Happened: `ModuleNotFoundError: No module named 'nextop.file_server.table'` (also no `nextop.core.access`, `nextop.parts.index.bm25`). The branch calls itself 0.2.0 too, and its guides describe these features.
- Expected: a different version number for a different feature set, or the guides saying which release has tables.
- Reproduce: `python -c "import nextop.file_server.table"` with the PyPI wheel.
- Tutorial impact: high. A reader who runs `pip install nextop` follows the tutorial and fails at the first table. The tutorial's tests fall back to the platform checkout (NEXTOP_SRC) only for our own development.

## 2. Worker knowledge cannot be built without an LLM key
- Tried: `knowledge: {"index": "bm25"}` on a worker, then `nextop index --worker reception`.
- Happened: `[error] worker reception: saving failed, the previous index is kept (LLMError: API key missing: set LLM_API_KEY in the environment or .env)`, and `nextop check`: `the domain knowledge index is missing; save the worker again or run 'nextop index'`.
- Expected: like a file server without `map_llm` (which warns and uses first sentences), a worker without LLM access still gets plain maps, or the guide says the build needs the model.
- Reproduce: new project, worker with `knowledge/x.md` and `"knowledge": {"index": "bm25"}`, empty key, `nextop index --worker w`.
- Tutorial impact: medium. The tutorial uses a text file server (`shop_info`, `nextop index --file-server shop_info`) instead, which builds without a model.

## 3. A chat (`run_ask`) shows no file server list or card
- Tried: guide says "every block with a tool on a file server gets a card after the list in its input". Asked `reception` (tools on `customers` and `shop_info`) through `run_ask`.
- Happened: the input holds only `## 질문 ...`; no rows, no card. The worker must call `customers_list` to see its rows.
- Expected: the same card as in an assigned task, or the guide saying open questions do not get it.
- Reproduce: a table file server with a `read: "subject"` worker, one row, `run_ask(..., subject=...)`, read `calls.jsonl`.
- Tutorial impact: medium. The persona tells the worker to call `customers_list` first.

## 4. A `.env` with a UTF-8 BOM is silently ignored
- Tried: `.env` written by Windows PowerShell 5.1 `Set-Content -Encoding utf8` (or Notepad "UTF-8 with BOM").
- Happened: `read_env` returns `{}` for the whole file (first key becomes `\ufeffNAME`, and nothing is reported). `nextop check` then says only `API key missing`.
- Expected: BOM stripped (`utf-8-sig`), or a message naming the file.
- Reproduce: `printf '\xef\xbb\xbfA=1\nB=2\n' > x.env; python -c "from nextop.adapters.openai_compat import read_env; print(read_env('x.env'))"` prints `{}`.
- Tutorial impact: medium for Windows beginners (the tutorial tells them to use `copy .env.example .env`).

## 5. `nextop check` warns about every text file server without `map_llm`
- Happened: `[warning] File server shop_info: no map_llm, so text files get a plain map (first sentences) instead of one written by a model` although the file server is two short files.
- Expected: no warning for a small file server, or a way to say "plain map is fine".
- Tutorial impact: low (the tutorial explains the line).

## Fixes (platform branch naw-steps)
- Issue 1: fixed in c595098 (the branch is now version 0.3.0; not published yet).
- Issue 2: fixed in c595098 (worker.json knowledge `"map": "first_sentence"` builds without an LLM key; the tutorial was not changed).
- Issue 3: fixed in c595098 (run_ask input has the file server card and rows, with the subject scope).
- Issue 4: fixed in c595098 (read_env reads utf-8-sig).
- Issue 5: fixed in c595098 (no warning for a file server without map_llm).

## nextop 0.4.0 (branch fs-graph, wheel 0.4.0.dev5 at 1f6768a + 6808f87 + c9a3cf3, 2026-11-26)

The tutorial now uses file servers with type folders (`types/customers/type.json` table type, `types/guide/type.json`
text type with `"splitter": "headings"`) and the common tools (`list`, `put`, `find`, `query`, `get`). Checked with the
compiled wheel 0.4.0.dev5 in a fresh venv (no source on the path): `nextop check` OK, `21 passed`, two real chats with
gpt-5.4-mini. Tutorial bug T1 (the `book` tool took answer ids that are not checklist questions and the mail printed
them) is fixed in `tools/book.py`; in the second real chat the worker sent an unknown id (`hair_note`) once, was refused
with the list of question ids, and booked correctly the next turn.

### 6. An empty model reply makes the next request fail with HTTP 400 (high)
- Happened: in the first real chat, message 3 failed: `LLM transport failed: HTTP 400 ... "Invalid value for 'content':
  expected a string, got null." "param": "messages.[13].content"`. The model's 4th reply was empty text and no tool
  call (`calls.jsonl` reply 4: `"content": ""`, `"tool_calls": []`); the loop put it back as
  `{"role": "assistant", "content": null}` without tool calls, which the API refuses. The customer saw "답을 만들지 못했습니다".
- Evidence: scratchpad `phase9\realrun\t01_first\runs\20261126-223855-593b\status.json` and
  `blocks\reception\attempt-1\calls.jsonl` (reply no 4).
- Cause: `nextop/runtime/react.py:1020` `_assistant`: `"content": reply.text or None` also when there are no tool calls.
- Suggested fix: `None` only together with `tool_calls`; otherwise `""` (or skip an empty assistant turn and send the
  nudge alone). Test: an empty reply followed by a second call keeps every message content a string.
- Not new in 0.4.0 (the line is older); found now.

### 7. `list` on the file server address of a table type answers table cards, not rows (medium)
- Happened: in a new chat the worker called `list {"address": "fs://customers"}`, got the card of table
  `fs://customers/001` (rows 1) and did not list that table, so it missed the customer's own note (first real chat, run
  `20261126-223911-2c83`, `tools.jsonl`). The persona says to list the table address from the input card.
- Cause: `nextop/file_server/tools.py` `_list` (the `is_server(addr)` branch, about line 302): a server address always
  gives `cards_under`.
- Suggested fix: when the server has exactly one table the worker may read, `list` on the server address lists that
  table's rows (as `find` already does with `fs://customers`: it found the one table); or the answer carries a note "list
  fs://customers/001 to see its rows".

### 8. Synced documents repeat the file server's description as their purpose on every card (low)
- Happened: each `shop_info` card repeats "the salon's guide: services, designers, opening hours, parking, cancellation
  and payment" (the server card has it already).
- Cause: `nextop/file_server/sync.py:251` (plan decision 9.7: a synced document's purpose is the server's description).
- Suggested fix: leave a synced document's purpose empty (the card then has none), or let a type say a default purpose.

### 9. `nextop index` still says "regions" for a server with type folders (low)
- Happened: `added: menu.md (fs://shop_info/001, 0 regions)`.
- Cause: `nextop/file_server/sync.py:275` counts region records, which a typed server does not make (its parts are in
  the part tree).
- Suggested fix: for a typed unit print its part count (`3 parts`).

### Notes (not platform problems)
- Model variance: in the second chat the worker booked but never called `put`, so the next chat had no note to show.
  In the first chat it did `put` (row `fs://customers/001/002`). The persona asks for it; left as it is.

## nextop 0.4.0.dev6 (branch fs-graph `044087f`, R1-R8 fixed, 2026-11-27)

Checked with the compiled wheel 0.4.0.dev6 in a fresh venv (nextop imported from the installed `.pyd`, no source on the path): `nextop check` OK, tests pass, one real run with gpt-5.4-mini (evidence in scratchpad `phase10ko`).

- 6 (empty reply, HTTP 400): fixed in `6f1ae6d` (R2; an empty reply is not sent back). This run had no empty reply, so
  it was not met live; the platform test `test_step2.test_an_empty_reply_is_not_sent_back` covers it.
- 7 (`list` on a table server): fixed in `21dae16` (R4), confirmed live. The persona now says to `list` the server
  address `fs://customers`, and the test lists the server address too. In the new chat of the same customer the worker
  called `list fs://customers`, got her row (`fs://customers/001/002`, "작년에 탈색 한 번 했어요. 밝은 갈색 염색 원해요.") and
  greeted her with it (run `20261127-000744-3747`). Before the first `put` the answer is "파일 서버 customers에는 아직 list로
  쓸 수 있는 표가 없습니다." (run `20261127-000729-7640`).
- 8 (purpose on synced documents): fixed in `f20b5b7` (R7), confirmed: the `shop_info` cards have no purpose; the server
  card has the description once (`inputs.md` of the runs above).
- 9 ("regions"): fixed in `f20b5b7` (R8), confirmed: `added: menu.md (fs://shop_info/001, 3 parts)`.
- Run: 3 customer messages (10 model calls, 42,905 tokens) to a pending booking (지수 원장, 2026-11-28 15:00); booking
  flow 2 calls, 4,215 tokens, 5.0 s, mail sent; approval sent the text to `outbox`. Tests `21 passed`.
- Tutorial note (not platform): the worker booked without asking two required checklist questions and wrote
  "말씀 안 하셨어요." as their answers (`book` args in run `20261127-000732-a05b`). `book` only checks that required answers
  are not empty, so it took them. In the 0.4.0.dev5 run the worker asked both. Left for the owner to decide (a program
  check that an answer comes from the customer's words would need the chat text in the tool).
- Persona change: `put` the customer's note before calling `book` (in the 0.4.0.dev5 run the note was never saved, so
  the next chat had nothing to show).
- No new platform problem.

## nextop 0.4.0.dev7 (branch fs-graph, F1-F6 fixed, 2026-11-27)

Checked with the compiled wheel 0.4.0.dev7 in a fresh venv (nextop imported from the installed `.pyd`, version
0.4.0.dev7, no source on the path): `nextop check` OK (`tools 4`), `26 passed`, real chats with gpt-5.4-mini
(evidence in scratchpad `phase11ko\realrun`).

- The dev6 tutorial note (the worker booked without asking two required questions and filled "말씀 안 하셨어요.") is
  now handled by the tutorial, not the platform: `tools/answer.py` records each answer as the customer gives it
  (`services`, `question`, `words`) and returns the live checklist (`✔ <words>` / `✘ 아직`, `open_required`); `book` has
  no answers argument, uses only the recorded answers of the chosen services and refuses while a required question is
  open, naming the open ones. Unknown question ids are refused by `answer` (T1 stays). The recorded answers are the
  chat's state: the chat page keeps them with the chat and sends them with every message; `chat_server.py` writes them
  to `chats/<run id>.json` for that run (the tools find it by `ctx["run_id"]`), reads them back after the run and
  deletes the file.
- Run 1 (`t01_first`): the worker never called `price_quote`, so it never saw the checklist; it called `book` once
  with phone "unknown", got only "ask for a valid mobile number", and after the customer gave the number it saved the
  customer row with `put` but did not call `book` again (no booking). Tutorial change: `book` now names everything
  missing at once (phone, date, open required questions with the checklist).
- Run 2: 6 customer messages (22 model calls, 113,760 tokens; the customer was a separate model call with fixed facts)
  to a pending booking (지수 원장, 2026-11-28 15:00). One question per message; all four required color questions were
  answered by the customer and recorded before `book`, which passed on its first call. `answer` refused three made-up
  ids (`bleach_history`, `color_hair_length`, `color_hair_history`) and the worker used the right ones. When the
  customer answered three questions in one message, the worker recorded that whole message for each of the three
  (the customer's words, not split per question). Booking flow 2 calls, 5,000 tokens, 5.0 s, mail sent; approval
  texted `outbox`. New chat of the same customer: `list` found her row and the worker greeted her with it (4 calls,
  18,333 tokens).
- In ask mode a tool's `ctx` has no subject (`nextop/runtime/flow.py:818`: run_id, block, project, files_dir,
  index_tools, file_servers; a function block gets `"subject"` at `:886`). Not a problem for this tutorial (the chat
  state is keyed by the run id the chat server chooses), noted because a tool that wants per-customer state in a chat
  cannot read the subject.
- No new platform problem.

## nextop 0.4.0.dev8 (branch fs-graph, tools get the subject, 2026-11-27)

Checked with the compiled wheel 0.4.0.dev8 in a fresh venv (53 `.pyd`, version 0.4.0.dev8, no source on the path):
`nextop check` OK (`workers 2, tools 3, flows 1, file servers 3`), `29 passed`, one real chat with gpt-5.4-mini through
the chat server's `POST /api/chat` (evidence in scratchpad `phase12\realrun`).

- Platform fix (from the dev7 note above): a worker's tools get the run's subject as `ctx["subject"]` in an open
  question and in a worker block of a flow, as a function does (`""` without one; the studio's ASK sends none).
- Tutorial change: the chat answers moved from `chats/<run id>.json` (carried by the chat page and the chat server) to
  the persistent file server `consult` (`"expire_after": "1d"`, access `reception: write + read subject`). A tool
  cannot write a file server (its view is read-only), so the worker writes each answer itself with the common `put`
  (`to: fs://consult`, row `question`, `service`, `words`); `price_quote` and `book` read the rows through
  `ctx["file_servers"]["consult"]`. `question` and `service` are `choice` fields, so the core refuses a made-up id (the
  job of the removed `answer` tool; T1 stays). The tool `answer` and the `answers` the page carried are gone.
- The subject stays the browser's customer id (the same for every message of a chat and for the customer's next
  chats), not a new id per chat: a run has one subject, and `customers` (kept notes, read by subject) must find the
  customer again in a new chat. So the conversation is the customer: another customer never sees the rows; the same
  customer sees her rows for one day (a reload keeps the answers). A field `conversation` filled by the worker was not
  used: the worker never sees the id, and the core already stamps the subject on every row.
- Two table file servers on one worker: `put` without `to` now answers "several file servers have put: fs://consult,
  fs://customers"; the persona gives the server address for each. No platform change needed.
- A table unit (`fs://consult/001`) gets no `expires`; only rows do (checked in the store), so one customer's rows
  expiring never removes another's.
- Run: 11 customer messages (38 model calls, 197,899 tokens) to a pending booking (지수 원장, 2026-12-01 13:30).
  All four required color answers were put as the customer gave them (`color_want`, `color_bleach`, `color_last` in one
  put; `color_allergy` next), each row stamped with the subject and `expires` one day later; `book` took exactly
  those four. A second customer's chat at the same time saw no consult row. Booking flow 2 calls, 6,697 tokens,
  5.1 s, mail sent; approval texted `outbox`.
- Worker mistake (not platform): when the customer gave "윤서연, 010-0000-7777", the worker took "서연" for the
  designer 서연 and called `find_times` for seoyeon, then lost the Saturday 15:00 it had offered and booked Tuesday
  13:30 (the customer had said another day was fine). Left as it is; a fix would be in the persona (the customer's
  name is not a designer choice) and needs the owner's decision.

## nextop 0.4.0.dev9 (branch fs-graph, consult clean-up and studio subject, 2026-11-27)

Checked with the compiled wheel 0.4.0.dev9 in a fresh venv (53 `.pyd`, no source on the path): `nextop check` OK on
all 15 tutorials (ko/en/ja x 5), `30 passed`, four real chats with gpt-5.4-mini through the chat server's
`POST /api/chat` on one fixed 11-message customer script (evidence in scratchpad `phase13
ealrun`).

- Tutorial change: after a booking the booking flow's first function `take_booking` deletes the customer's consult rows
  (the booking already holds the answers), so the next consult of that customer starts empty. It uses existing APIs:
  `FILES_IN = True` gives it `files/consult` (the rows it may read; access `take_booking: read subject, delete`), and
  `_deletes` removes the row addresses. Rows left by a chat without a booking still expire after one day.
- Platform fix found doing it: a function that reads by subject sees the table unit (`fs://consult/001`, every reader
  does), and deleting the unit took every row in it, so one customer's clean-up removed the other customers' rows.
  Now a scoped delete must be able to read everything the delete takes with it; the unit is refused with the usual
  words and the function deletes only its own subject's rows (`fs://consult/001/002`). `take_booking` names rows only.
- Platform fix: the studio's ASK sends a subject per chat (`studio-<id>`; New chat, another worker or a reload makes a
  new one), so ask-mode tools get a non-empty `ctx["subject"]` there too.
- Tutorial change: the persona says a name the customer gives for themselves is not a designer choice; several answers
  of one message go in one `put` (the common `put` already took up to 20 rows; no platform change); `price_quote` is
  called at most once in a message (not again after a put); its checklist no longer repeats the words to ask for
  questions already answered, and `open_required` carries ids only.
- Before (0.4.0.dev8, the tutorial before these changes) and after (0.4.0.dev9), two runs each, same script:
  before 39 and 36 model calls, 196,727 and 188,169 tokens (`price_quote` 4 and 5, `put` 7 and 5); after 31 and 31
  calls, 156,418 and 154,982 tokens (`price_quote` 3 and 3, `put` 4 and 5). Booking flow 2 calls, about 5,500 tokens.
  In the booked after-run the four consult rows were deleted by `take_booking` (access log: `delete`, reason
  `function`) and the table unit stayed; the booking (지수 원장, 2026-11-28 15:00, color medium, 70,000) carried the
  four answers. No run took "윤서연" for the designer 서연.
- Worker mistakes left (not platform): in one after-run the worker did not record "밝은 갈색" from the second message
  and asked for it again later; the fixed script never answered again, so `book` refused (the program guard worked)
  and there was no booking. In one before-run the worker booked the same customer twice (15:00 and 17:00 pending).
- Seen while measuring (not changed): in an open question the model sometimes writes its answer as plain text without
  `save_output`; the core then nudges it and the next call repeats work (2 to 4 such replies per 11-message chat,
  about 10 % of the tokens). Taking a plain-text reply as the answer in ask mode would save those calls; it is a
  platform decision for the owner.

## nextop 0.4.0.dev12 (branch fs-graph `0ad0364`, conversation navigator, 2026-11-27)

Checked with the compiled wheel 0.4.0.dev12 built from `0ad0364` (git-archive export, version set only in the copy;
56 compiled modules, 0 `.py`; compiled suite `855 passed, 1 skipped`), installed with pip in a fresh Python 3.11 venv
and through `setup.bat <wheel>` (`Setup OK`; the tutorial tests are `26 passed` now). Real runs on the local qwen
model: 8 simulated chats (the customer played by the same model from a short profile), three rounds, the last one on
the final tutorial (table in the README). `nextop check` OK (workers 3, tools 5, flows 9, file servers 6). One worker
definition check per worker (reception, summarizer) on qwen; only the important findings were fixed. The model
address and key stayed in memory; a scrub of the run records, mails and memos found 0 hits.
Nothing in the platform was changed from here.

### T1. A tool cannot write a file server, and it reads only with its worker's rights (high, design)
- Needed: the book tool must hold a slot when the customer agrees; the change tool must write the changed booking;
  the identity check must look at every booking (another browser's too) while the reception sees none of them.
- Happened: `ctx["file_servers"]` is a read-only view with the worker's rights (view.py: "a tool can never see more
  than its worker"); no tool result key writes (`_uploads` and `_deletes` are for functions only).
- Done in the tutorial: the tools run small flows of functions from inside the tool (`functions/_salon.run_flow`:
  `book` -> `booked` -> `verify`, `change` -> `changed` -> `verify`, `verify`), and those functions read and write with
  their own access entries. It works (the outer run's navigator sees the new rows after the tool round), but each tool
  call makes two or three extra run folders, and the program's write path lives in user code the platform does not
  know about (the flow check cannot see that `book` writes bookings).
- Proposal: an access entry for a tool (a tool as a principal: `"tool:book": {"read": "all", "write": true}`), or a
  tool result key like a function's (`_uploads`, `_puts`, `_deletes`) checked against such an entry, with the result
  hidden from the worker where the entry says so. Then `match_customer` could be a plain tool that reads all bookings
  and returns only the match.

### T2. A function writes table rows only by uploading a file (medium)
- Happened: a function has `_uploads` (a `.json` file of rows into a table with `to`) but no row put. Every write keeps
  the file as one more original of the table unit (`originals`, `files/<table>-o<k>.json`), and a second upload with the
  same title and content is skipped silently (`keep_original` returns False, no rows written).
- Done in the tutorial: every upload title carries a timestamp (`functions/_salon.uploads`); the type folders take
  `"extensions": ["json"]`; the function finds the table unit address in its FILES_IN by the record without `fields`.
- Proposal: `_puts` for functions (rows with `to`, the same write modes and history as the worker's `put`), and a
  marker on the table unit record in FILES_IN (`"kind": "table"`).

### T3. No conditional write: two chats can take the same slot (medium)
- Happened: `take_booking` reads the calendar in FILES_IN before its code runs, then uploads. Two runs at the same time
  both see the slot free; the key (booking id) cannot stop it either, because the key includes the run's subject and
  these runs have none, but a slot of another id is another row.
- Proposal: a unique constraint on a table (e.g. `"unique": ["designer", "date", "time"]` refused by the core inside the
  store lock), or a "put if" (a field value expected) for functions.

### T4. The flow check needs the LLM key even for a flow of functions only (low)
- Happened: `python seed.py --reset` on a fresh copy without `LLM_API_KEY` stopped with `the flow check failed`
  (`adapter llm.default: API key missing`), although the flow `seed` has no worker.
- Done in the tutorial: README says to fill `.env` before `seed.py` (any value works for seeding).
- Proposal: check the LLM adapter only when the flow has a worker block.

### T5. The navigator cannot tell when a purpose row was first written (low)
- Happened: a table row carries `updated` (seconds) but no `created` in the view's rows, so the order of purposes uses
  the row address (number order) and the agreement check compares `updated` to the second.
- Proposal: `created` in the plain row; a finer `updated`.

### T6. After a step switch the worker does not know what the left step just did (medium, by design)
- Happened (real chats, run 1): `book` / `change_booking` finish the purpose (a flow function marks it done), the
  next navigate returns `consult`, and the question restarts in the consult step without the tool transcript. The
  worker then saw only the new state and said "your booking is already at that time" after a change and "it is
  already cancelled" after a cancel.
- Done in the tutorial: the navigator reads `ctx["entered"]` and, for a purpose finished in this question, adds a
  "just done" line with the bookings as identity holds them now (checklists.json `texts.just_done`). Run 2 and 3: the
  change and the cancel were reported as done.
- Proposal (owner decision): the platform could carry one line per tool call of the left step into the new step
  (name and ok/refused), or document that a navigator should say what a switch just finished.

### Notes (model, not platform)
- The local qwen model mixes other languages into Korean answers now and then ("锁骨", "用到", "goes요", "沙龙"),
  and sometimes adds an unknown key (`sources`) to `save_output` (refused by the program, one more call).
- In the consult step it once answered "11:30 is possible" without a free-time tool (fixed in the step text: the
  consult step cannot see free times); in run 2 it still said "Saturday morning is fine" from the shop guide's working
  hours (no slot was promised; the booking step then refused the taken time and proposed 13:00).
- A cancel is done as soon as the booking and "cancel" are recorded; the owner's checklist has no confirmation item for
  a cancel (a change has `change_agree`). Open: add a cancel confirmation item if wanted.

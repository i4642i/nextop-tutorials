# Tutorial 1. A hair salon booking chatbot

A customer talks to the salon in a chat. The front-desk worker "Riley" finds out what the customer wants (salon info, a booking, checking a booking, changing or canceling a booking, or something else), asks for what that request needs, and writes down what it hears, one row at a time, in a table. What is still missing and which step the chat is in are not decided by the worker. A program (the **conversation navigator**) reads the records and decides. When a booking is made, the designer gets a consultation summary by mail (the whole chat is attached, and there are approve and decline links). When the designer approves, the customer gets a confirmation text.

## What you will have

Willow Hair Studio (an example salon) has three designers (Jordan, Maya and Alex), and some bookings are already in the calendar.

A consultation goes like this:

```
greet -> find the request -> for each request, Riley does this:
                    - salon info: find the answer in the salon guide and give it
                    - booking: name, mobile number, service, style, wished day and time, designer (optional),
                               the questions of that service (salon.json), one free time and the customer's "yes" -> book
                    - checking my booking: check name and mobile number -> tell the customer their bookings
                    - change or cancel: identity check -> which booking, change or cancel, the new time
                               (a reason for canceling is optional)
                    - something else: what it is about (mobile number optional) -> the salon calls back
      -> "Is there anything else I can help with?" (find the next request) -> goodbye
When the chat ends, the flow deletes the chat's consult rows.
```

- Riley talks with the customer and writes what it hears into the consult notes table (`consult`) with the save tool (`put`). Writing the same item again replaces that row with the new value, and the old value stays in the row's history. If a customer changes from color to a perm, one `service` row changes.
- Before every question, the **conversation navigator** (`workers/reception/navigator.py`) compares the records with the checklists (`checklists.json`, `salon.json`). It picks the step (`consult`, `booking` or `manage`) and writes the **step notice**. The notice lists what is still missing and what is recorded, for example "booking: talk with the customer and collect what the booking needs. Still missing: ...". When Riley calls `put`, the navigator runs again, so the notice changes in the same turn.
- The booking tool (`book`) is offered only in the booking step. That step opens when every booking item except the agreement is recorded. If the wished time is taken, or the designer does not work that day, the notice says so. Riley then finds close free times with the free-times tool (`find_times`) and asks again. An agreement counts only if it was recorded after the last change of time or designer.
- Checking, changing and canceling start with an **identity check**. The program matches the name and mobile number the customer gave with the booking records (not the browser's customer id). Only if they match does the customer see their bookings. If the number is wrong, nothing is said, not even whether a booking exists.

**A real run** (a local model, nextop 0.4.0 from PyPI, a person played the customer; a model's wording differs from run to run. More runs are in "Results of real runs" below). The customer wants a time that is already taken:

```
Customer  Hi! I'd like to book a taper fade with Jordan this Tuesday at 2 PM.
Riley     Hi! Riley here at Willow Hair Studio — a taper fade with Jordan, got it. That's $40 and about 30 minutes. Tuesday Dec 1 at 2:00 PM is noted, and I'll check open times once I have everything the booking needs.

          First, what name should I put the booking under?
Customer  Ryan Cooper
Riley     Thanks, Ryan Cooper — got it. Can I get your mobile number? I text the confirmation there and use it to look you up later.
Customer  It's 312-555-0142
Riley     Thanks Ryan, got it. Last quick thing for the cut: do you want your bangs trimmed with the taper fade, or left as they are?
Customer  Just a little trim on the bangs, keep them longish.
Riley     A little trim, keeping them longish — noted. One snag: Jordan already has a client at 2:00 PM Tuesday, so that slot's taken.

          The closest I can do with Jordan that same day is 2:30 PM on Tuesday Dec 1 (1:30 PM is open too). Does 2:30 PM work for you?
Customer  Hmm, 1:30 would actually be better for me.
Riley     1:30 PM is open with Jordan on Tuesday Dec 1 — I've switched you over. Taper fade, $40, about 30 minutes. Shall I book that?
Customer  Yes please, book it.
Riley     You're all set, Ryan. Here's what I have:

          - Tuesday, December 1 at 1:30 PM
          - Jordan, taper fade with a light trim on the bangs
          - $40, about 30 minutes

          That's a pending booking — the slot is held for you, and you'll get a confirmation text once Jordan signs off on it.

          Anything else I can help with today?
```

When a booking is made, its slot is held as "pending" (nobody else can book it). The designer gets a mail and approves or declines. The customer's text goes out only after that.

**The mail to the designer** (subject: `[booking TEST] [new booking, please approve] <date> <time> <name> · <style>`. `[booking TEST]` appears only in test mode, `MAIL_TEST_MODE=1`. Attachment: `chat_<booking id>.txt`, the whole chat. The same text is saved as `memos/<booking id>.memo.md`.) This is the memo of the run above, without the approve and decline link lines:

```
# 2026-12-01 (Tuesday) 1:30 PM · Jordan
- Customer: Ryan Cooper · (312) 555-0142
- Services: Haircut (Taper fade) · 30 min · $40

## Consultation summary
Ryan Cooper wants a Taper fade Haircut and is booked with Jordan on 2026-12-01 (Tuesday) at 13:30.

## Answered in advance
- what to do with the bangs: just a little trim on the bangs, keep them longish

## To prepare
- Set Jordan's chair for a taper fade: clippers with guards for the taper/sides, trimmer/edger, scissors, comb, clips, cape, blow dryer, and finishing product.
- Have thinning/texturizing shears ready in case the top or bangs need light blending rather than a blunt cut.
- Keep the station ready for a fast turnaround because the appointment is only 30 minutes.

## To ask first
- Confirm how high the taper fade should start and whether the sides should be a skin fade, #1, #2, or another guard length.
- Confirm the bangs are only a little trim and should stay longish — agree on the exact length before cutting.
- Confirm whether he wants the edges/neckline cleaned up and whether he will style it with product.

## Be careful about
- Be conservative with the bangs: Ryan asked for only a small trim and wants them left longish.
- Schedule is tight: the 1:30 appointment finishes at 2:00, and Jordan originally had a client at 2:00, so avoid running over.
- Booking is pending until Jordan signs off; verify the time change to 1:30 is confirmed before starting.

## Your answer
(The mail ends here with the approve link and the decline link.)
```

Jamie (the summary worker) writes the "Consultation summary", and Sam (the prep worker) writes the "To prepare", "To ask first" and "Be careful about" parts. Their wording comes from the model, so it varies. The times shown to people are 12-hour (1:30 PM), while the program and the records keep 24-hour `HH:MM` (13:30).

**The text to the customer** (after the designer approves; the format comes from `functions/_approval.py`)

```
[Willow Hair Studio] Your booking is confirmed.
2026-12-01 (Tuesday) 1:30 PM with Jordan
Haircut (Taper fade) $40 before tip · about 30 min
Please change or cancel at least 24 hours ahead.
```

## Time and what you need

About 1 hour. You read a finished project, fill in the settings and run it.

- Python 3.11 to 3.13 and nextop 0.4.0: `setup.bat` in step 0 installs all of it (by hand: `pip install -r requirements.txt`). `requirements.txt` pins nextop 0.4.0 from PyPI, and `"nextop": ">=0.4,<0.5"` in `project.json` tells which versions this project needs (with another version, `nextop check` tells you what to do). To try a nextop build that is not on PyPI, install from a wheel file: `setup.bat <path to the .whl>`.
- An OpenAI API key (the default; any OpenAI-compatible API also works, see Settings below)
- SMTP details of a mail account (optional; without them only the mail step is skipped, and the memo is still written to `memos/`)
- No text message service is needed. The default `outbox` mode writes each text to a file.

Steps 0 to 3 need no model. The program parts (navigator, time checks, double-booking refusal, identity check, texts, mail) are checked by tests with a fake model.

## What this tutorial teaches (nextop features)

- Worker modes (`"mode"`): a free-question worker that chats with the customer (Riley, `"ask"`) and fixed-task workers (Jamie, Sam, `"task"`)
- The conversation navigator (`navigator.py`) and the step notice: your own code looks at the records before every question and picks the step and the notice. Each step has its own tools and file servers (the booking tool is only in the booking step)
- The mission (`mission.md`, the same rules in every step), step texts (`steps/<id>.md`) and the persona (`persona.md`, who the worker is and how it talks)
- Checklists in spec files, not in code (`checklists.json`, `salon.json`). The table's choice field (`choice`) reads item ids from the same files through a project part (`parts/field_type/choice.py`)
- Phone numbers with nextop's `phone` field type (`"country": "US"`): any way of writing a US number becomes one E.164 key (`+13125550142`), so a recorded number and a booking's number compare equal
- Table file servers and keys: writing the same item again replaces the row and keeps the old value in its history (`consult`); the show depth (`"show": 2`) puts the rows straight into the worker's input
- Rights and scope: a chat reads only its own rows (`_subject`). The reception's model never gets the bookings; only the program (navigator and tools) reads them, and filters what goes into the notice
- Function blocks and small flows: the flows `booking_notes`, `decide`, `chat_end` and `seed` hold the model-free work. The tools `book` and `change_booking` write to the tables with the reception's own write right
- Expiry (`expire_after`): rows of a chat that never ended are deleted by the core after one day
- Text type and bm25 search: answering from the salon guide (`shop_info`, tools `query` and `get`)
- Reply checks: a program check (`workers/reception/reply_check.py`, no letters of another script) and two LLM checks in `worker.json` (`reply_checks`), with a fallback reply (`reply_fallback`)
- Tests without a model: a fake LLM checks whole chats and flows

## Step by step

Open PowerShell in this folder (`en/tutorial_01_hair_salon`).

### 0. Install: run setup.bat

Double-click `setup.bat` in this folder, or run `.\setup.bat` in PowerShell. It installs everything you need, once.

- It looks for Python 3.11 to 3.13. If there is none, it installs Python 3.12 with winget (then open a new terminal and run `setup.bat` again).
- It creates a virtual environment `.venv` in this folder and installs `requirements.txt` (nextop and pytest). With a wheel path (`setup.bat C:\downloads\nextop-0.4.0...whl`, or the environment variable `NEXTOP_WHEEL`) it installs nextop from that file instead. The wheel must match your Python version (`cp311` means Python 3.11).
- If there is no `.env`, it copies `.env.example` to `.env` and shows the names you have to fill in.
- It runs the tests without a model. If all pass, the last lines are `Setup OK` and the installed nextop version.

You can run it again at any time (an existing `.venv` and `.env` are kept). Turn on the virtual environment before the commands below:

```powershell
.venv\Scripts\activate
```

### 1. Look at the folders

```
project.json          project settings (the LLM connection, the nextop version this project needs)
salon.json            the designers (days and hours), the menu with prices and minutes, and each service's
                      checklist (what to ask before the visit)
checklists.json       the checklist of each request (salon info, booking, checking my booking,
                      change or cancel, something else) and every sentence of the step notice (texts).
                      The code has neither the checklists nor the sentences
data/seed_bookings.json   the example bookings (made relative to today)
workers/reception     Riley (free-question worker, "mode": "ask")
  persona.md            who Riley is and how Riley talks
  mission.md            the rules for every step (how to record, facts only from tools)
  steps/consult.md      consult step: find the request, salon info, collect the booking items
  steps/booking.md      booking step: propose a free time, get the "yes", book
  steps/manage.md       check and change step: identity check, check, change, cancel
  navigator.py          the conversation navigator: reads the records, picks the step and the step notice (no LLM)
  reply_check.py        the reply check: refuses a reply with letters of another script
workers/summarizer    Jamie: consultation summary (fixed-task worker, "mode": "task")
workers/stylist       Sam: prep memo for the designer (fixed task)
tools/                tools Riley calls: price_quote, find_times, book, verify_customer, change_booking
functions/            blocks without a model: seed_bookings, load_visit, mail_designer, decide_booking, close_chat
                      _salon.py (the rules), _approval.py (approve links and texts), _notify.py (text, mail)
flows/                booking_notes (summary and mail after a booking), decide (the designer's answer),
                      chat_end (the chat ended), seed (the example bookings)
file_servers/consult     consult notes table: request rows and checklist answers (Riley writes them with put,
                         one set per customer, deleted when the chat ends, expire after one day)
file_servers/bookings    booking records table: read by the program and the tools; Riley's model never gets it
file_servers/customers   customer table: hair history and wishes (written by the book tool; the phone is a
                         sensitive field)
file_servers/shop_info   the salon guide: documents/ (menu.md, shop.md)
parts/field_type/choice.py   the choice field part: in consult, item and style accept only the ids and menu names
                             of checklists.json and salon.json
chat_server.py        the customer chat page + the designer's approve and decline links
chat.html             the chat page
approve.py            approve or decline from the command line, without the server
seed.py               writes the example bookings
setup.bat             first-run setup
tests/                tests without a model
```

(When you run things, these appear: `schedule.html` (the booking table), `memos/`, `outbox/`, `runs/`, `bookings/`.)

### 2. Fill in the settings

```powershell
copy .env.example .env
```

(If you create `.env` in Notepad, save it as UTF-8 without BOM.) Put your OpenAI API key after `LLM_API_KEY=`, and put any long random text after `APPROVE_SECRET=`. More in "Settings" below. The next step's `seed.py` runs a flow, so it stops at the flow check if `LLM_API_KEY` is empty (it does not call a model).

### 3. Write the example bookings and run the tests

```powershell
python seed.py --reset
python -m pytest -q tests
```

You should see `9 example bookings written` and `45 passed`. Open `schedule.html` in a browser: confirmed bookings are blue cells, and bookings waiting for approval are dashed cells. The tests check:

- With no request recorded, the step is `consult` and the notice says to ask how to help
- For a booking request, the notice names what is missing by item id (`name`, `phone`, `service`, `style`, `wish_time`, and the questions of the chosen service such as `color_want`), and only the chosen service's questions count
- When everything but the agreement is recorded, the step is `booking`. If the wished time is free, the notice says to propose it and get a "yes". After the agreement, it says to book with the booking tool
- If the wished time is taken, the notice says to find another time, and the booking tool refuses even with an agreement. An agreement given before a later change of time counts for nothing
- Writing the same item again keeps the last value (the old one stays in the history), and changing the service switches to that service's questions
- A style that is not on the menu is refused, one style per service, and "recommend" tells Riley to ask what look the customer wants and suggest two or three styles from the menu
- Price and minutes come from the chosen styles, and a wished time too short for the style is not free
- Two requests in one message both appear in the notice
- A wrongly formed answer (a phone number, a date, a name like "I'm Emma") is asked again, and the core refuses an item id that is not in the spec files
- Another customer's chat sees none of these rows
- The booking tool is not offered in the consult step. A booking in the chat writes the booking, the customer table row, and the schedule, and finishes the request
- Identity check: with a wrong number nothing is said. A correct name and number finds the booking from any browser. A verified customer sees only their own bookings
- Change and cancel: refused before the identity check, and refused for another customer's booking. Canceling frees the slot, and changing the time makes the booking pending again
- Jamie's summary and Sam's memo are in the designer's mail, and an approve link works once
- In the turn where a booking or a cancellation was just handled, the notice says "just handled" with the current bookings
- When the chat ends, only that chat's consult rows are deleted
- The reply check passes English with numbers, prices and accents, and refuses letters of another script (the menu's own names excepted). A refused reply is written again with the reason, and a second refusal sends the fallback reply

### 4. Index the salon guide

```powershell
nextop index --file-server shop_info
```

You should see `added 2 ... 2 files in the store`. Run it again after you edit the documents.

### 5. Check the flows

```powershell
nextop check
```

You should see a line starting with `OK: hair salon booking`, followed by the counts (3 workers, 5 tools, 4 flows, 4 file servers).

### 6. Open the chat

```powershell
python chat_server.py
```

Open http://127.0.0.1:8771 in a browser and talk to Riley. `http://127.0.0.1:8771/schedule` shows the booking table. The "end chat" button deletes that chat's consult rows. Stop the server with Ctrl+C.

Things to try:
- "I'd like to book a haircut": Riley asks for what is missing, one thing at a time, and when everything is there, proposes one free time with the designer's name
- Choose a time that is already taken (a blue cell in `schedule.html`) on purpose: Riley says it is not available and proposes a close free time
- Halfway through: "Actually, make it a perm": the questions change to the perm's
- "I'd like a taper fade, and is there parking?": both requests are handled
- Say "I don't know what style I want": Riley asks what look you want and suggests styles from the menu
- In another browser (or a private window): "Can you check my booking?" Riley asks for a name and number, and tells you the booking if they match. With a wrong number, nothing is told

### 7. Check the results

When a booking is made, the flow `booking_notes` runs in the background. A few seconds later you can check:

- `memos/<booking id>.memo.md`: the same text as the designer's mail. `memos/<booking id>.chat.txt`: the whole chat, which is attached to the mail
- The designer's inbox (in test mode, `OFFICE_EMAIL`): the approve and decline links
- `runs/<run id>/`: the run records. One chat message is one run, and `navigator.jsonl` in a block's folder keeps the step and notice the navigator chose

Now answer as the designer. Open the approve link from the mail in a browser (the chat server must be running). To skip the server, use the command:

```powershell
python approve.py 2026-12-01-1330-jordan              # approve: confirmed, the customer gets the confirmation text
python approve.py 2026-12-01-1330-jordan --decline    # decline: the slot is free again, the customer gets a short text
```

(The booking id is the date, the time and the designer's id. With a changed or canceled booking, a memo `memos/<booking id>.change.md` is written for the designer.)

After that, the customer's text is in `outbox/sms_<time>.txt`, and in `schedule.html` the dashed cell turns into a blue one (a declined booking disappears).

## How it works

```
[customer chat page] --message--> chat_server.py --> Riley (reception, ask)
 (the chat + a customer id)                           |
                            navigator.py: reads consult and bookings, picks the step and the step notice
                                                      |
          consult step   tools: price_quote, put, get, query
          booking step   tools: find_times, book, price_quote, put, get, query
          manage step    tools: verify_customer, find_times, change_booking, put, get, query

book            --> writes bookings, customers and schedule.html, finishes the request in consult
                --> chat_server runs the flow booking_notes in the background:
                    load_visit --> nuri (Jamie, summary) --> duri (Sam, prep memo) --> mail_designer
change_booking  --> identity check again, then writes bookings and schedule.html, mails the designer,
                    finishes the request in consult
verify_customer --> the identity check (the program matches name and phone with the bookings)
end of the chat --> flow chat_end (close_chat: deletes this customer's consult rows)
designer's link --> flow decide (decide_booking: confirmed or declined, text to the customer)
```

(`nuri` and `duri` are the block ids in the flow `booking_notes`; the workers are Jamie and Sam.)

- **Records and decisions are split.** Understanding what the customer means and writing it down is Riley's job (the LLM). What is left, whether a time is free, whether the customer is who they say, and which step the chat is in are decided by the program. That is why Riley's text has no patched-on rules such as "call the price tool only once".
- **Request rows**: for each request Riley writes a `purpose_<id>` row (`words`: what the customer said, `state`: `open`). Two requests in one message make two rows. The booking tool and the change tool mark the booking and change requests `done`, and Riley marks salon info, checking my booking and something else as `done` after answering. The first open booking, checking or change request picks the step. Salon info and other requests appear in the notice in every step.
- **Overwrite and history**: the key of `consult` is `item`, so writing an item again replaces the row and the old value stays in the row's `history`. Each customer has their own rows (the customer id is part of the key), so they never mix with another customer's.
- **Show depth**: `consult` and `customers` have `"show": 2` in the access line for the reception, so the rows appear in Riley's input with their field values. Riley sees the records without calling `list`.
- **The agreement**: in the booking step, `agree` counts only if it was recorded after the last change of `wish_time` and `designer` (compared by the row's `updated` time). If the time is not free, the agreement does not count, and the notice tells Riley to find another time. The booking tool checks the same rules again, and checks the free time once more just before writing.
- **The model never gets the bookings.** The reception's model has no common tool on `bookings`, and its notice shows only what the program lets through. Free times are given with no names (a taken time is simply not in the list), and a customer's own bookings are shown only after the identity check.
- **Identity check** (the method of this tutorial): the customer's name and mobile number are written into `consult`. Then the program (`verified_bookings` in `functions/_salon.py`, used by the navigator and the tools) reads every booking and finds those whose name (spaces ignored) and phone (as the same E.164 key) are exactly the same. If there is a match, the notice lists that customer's bookings. If not, it tells Riley to say nothing about bookings. The decision is the program's and does not depend on the browser's customer id, so another device that passes the check can see and change the booking. `change_booking` repeats the check just before it acts. **A real service needs a real identity check (for example a code sent to the phone). That is future work.** A name and a number do not stop another person who knows both.
- **Writing**: the tools `book` and `change_booking` write to `bookings` and `customers` themselves, with the reception's write right (the view's `put`, which checks the fields and keeps old values in the history). The flow functions read with their own access line (`FILES_IN`), write rows by uploading a `.json` file into the table (`_uploads`), and delete rows (`_deletes`). A worker never deletes anything.
- **End of a chat**: "end chat" (`POST /api/end` on the chat server) runs the flow `chat_end`, which deletes this customer's `consult` rows. Rows of a chat that is never ended are deleted by the core one day later (`expire_after`).
- **Words come from the records.** Names, dates, times and prices are not made up by the model: they come from the booking record and the menu. The text to the customer is sent after the designer's answer (approve or decline). The links carry a signed value (HMAC) of the booking id made with `APPROVE_SECRET`, so only the person who got the mail can answer.
- **Reply checks**: before a reply is sent, the program check (`workers/reception/reply_check.py`) refuses any letter that is not Latin (Hangul, Han characters, kana, Cyrillic, Arabic and so on; accented Latin such as café passes, and so do digits, prices, times and phone numbers). The salon's own style names are exempt. Two more checks in `reply_checks` of `worker.json` are judged by a model: a price or a salon rule must come from a tool result, the notice or the facts written there, and a customer who refuses a required item must be told why it is needed. A refused reply is written again with the reason. A second refusal sends `reply_fallback`. The facts written into `reply_checks` (hours, designers, the deadline for changes) are copied from the salon guide, so change them too when the guide changes.
- **Two kinds of time**: the program and the records keep 24-hour `HH:MM` (`salon.json`, tools, tables). Customers read 12-hour times with AM and PM ("2:30 PM"). Riley writes `wish_time` as `YYYY-MM-DD HH:MM`, and the program turns times into 12-hour form where a person reads them.

## Results of real runs

Four chats, run on 2026-11-28 with nextop 0.4.0 installed from PyPI (by `setup.bat`, in a fresh `.venv` on Windows 10 with Python 3.11). All three workers (Riley, Jamie and Sam) used the same local model, with its thinking mode on. A person played the customer and sent one message at a time through the chat server's `answer()`. Mail was not set up in these runs, so after each booking the flow `booking_notes` wrote the memo to `memos/` and reported that the mail was not sent. That is expected. The offline tests gave `45 passed`.

| Chat | Customer messages | What happened |
|---|---|---|
| 1. Booking with a taken time | 6 | Taper fade with Jordan on Tuesday at 2 PM. 2 PM was taken by a booking in the calendar, so Riley offered 2:30 PM. The customer asked for 1:30 PM, Riley recorded it again and booked it, pending. (The chat is at the top of this README.) |
| 2. Two requests in one message | 5 | A parking question and a balayage with Maya next Saturday afternoon. Riley answered the parking question from the salon guide and went on with the booking: Saturday, December 5 at 1:00 PM, pending. |
| 3. Check, change, cancel | 7 | A wrong number: Riley said the name and number did not match and told nothing. The right number: the booking was shown. A move to Wednesday at the same time: Jordan was busy, and Riley gave three options. The customer picked 1 PM with Jordan (pending again), then canceled after one confirmation question, and the reason was noted. |
| 4. A customer who will not give a phone number | 2 | Riley explained why the number is needed, said the chat could not go on to picking a time without it, and offered booking by phone. |

Chat 2, the first turns, word for word:

```
Customer  Hi, is there parking near you? Also I'd like to book a balayage with Maya next Saturday afternoon.
Riley     Yes! Free parking in the lot behind the building at 214 Main Street, Suite 2 — street parking is metered if the lot's full.

          Balayage with Maya, got it. Let's get you set up — what name should I put the booking under?
Customer  Hannah Price, my cell is (646) 555-0123.
Riley     Thanks, Hannah — got your number down.

          Heads up: a balayage runs about 3 hours here ($250), so an afternoon start needs to be early-ish. Do you have a time in mind for Saturday, December 5th?
```

Chat 3, with turns left out (the wrong number, then the right one, then the move):

```
Customer  Hi, can you tell me when my appointment is?
Riley     Hi! I can check that for you. First I need to make sure I'm looking at the right person — what's your full name (e.g. Emma Johnson)?
Customer  Emily Carter, 212-555-0199
Riley     Hmm, that name and number don't match what I have here, so I can't pull anything up yet. Could you double-check them? Sometimes it's a middle name in the booking or a different mobile number (like a work phone) — let me know what you'd like to try and I'll look again.
Customer  Oh sorry, it's 212-555-0101.
Riley     Got it, that one matches! Here's what I have:

          - Tuesday, December 1, 2026 at 10:00 AM with Jordan
          - Beach wave perm (perm/texture), $150, about 2 hours 30 minutes
          - Status: confirmed

          Anything else I can help with today?
Customer  Actually, can I move it to Wednesday, same time?
Riley     Wednesday, December 2 at 10:00 AM isn't open for Jordan, unfortunately. Here's what I can do that day:

          - 10:00 AM with Maya (same time, different designer)
          - 10:00 AM with Alex
          - 1:00 PM with Jordan (same designer, later start)

          Which one works for you? Once you pick, I'll move it and it'll just need a quick okay from the designer.
```

Chat 4, word for word:

```
Customer  I want a buzz cut Monday morning with Alex. Name's Tom Baker.
Riley     Hi Tom, thanks! Buzz cut with Alex is $25, about 30 minutes.

          Monday would be Nov 30 — what morning time works best, like 9:00 AM or 10:30 AM? Also, want the bangs trimmed too, or all one length?
Customer  I'd rather not give out my phone number.
Riley     No problem at all, Tom. We only use it to text your confirmation and to check who you are if you need to change the booking later.

          Without it though, I can't go on to pick your time here in the chat — there'd be no way to send the confirmation. If you'd rather not share it, call the salon and we'll finish the booking over the phone instead.

          If you're willing to send it, I'll still need your exact Monday morning time (like 9:00 AM) and whether to trim the bangs.
```

Reply checks in these runs: the program check refused 0 of 23 drafts. The model check refused 2 drafts, and the rewrites passed: one had invented "no charge for canceling", and one was an explanation that did not say the booking cannot go on without the phone. No reply had letters of another script.

Slips of the small model that remain: Riley sometimes proposed two or three times in one message instead of one, and once called 9:00 AM a possible morning time when Alex opens at 10:00 AM. (In chat 4 above, that is the "9:00 AM" example. No booking was made in that chat.)

## Settings

### LLM (`project.json`, `workers/*/worker.json`, `.env`)

The default is the OpenAI API. `base_url` in `project.json` is `https://api.openai.com/v1`, and `"model"` in each `workers/*/worker.json` is `gpt-5.4-mini`. Put your OpenAI API key after `LLM_API_KEY=` in `.env`. Another OpenAI-compatible API works too: change `base_url` and the model names.

### Text messages (SMS)

The default is `SMS_MODE=outbox` in `.env`. No text service is used, and each text is written to `outbox/sms_<time>.txt`.

To send real texts:
1. Sign up for a text service and get a sender number. The code is ready for Twilio.
2. In `.env`, set `SMS_MODE=twilio` and fill `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN` and `TWILIO_FROM` (your Twilio number, like `+15550100000`).
3. Note: `sms_twilio` in `functions/_notify.py` is written from Twilio's documentation and has not been tried against the real service. First send one to your own number.
4. For another service (Vonage, Amazon SNS and so on), write a function `def sms_vonage(to, text)` in `functions/_notify.py`, add it to `PROVIDERS = {..., "vonage": sms_vonage}` and set `SMS_MODE=vonage`.

### Approve links (`APPROVE_SECRET`, `PUBLIC_URL`)

- Put any long random text after `APPROVE_SECRET=` in `.env`. It signs the links, so keep it private. If it is empty, no designer mail is sent, and the notice tells you to fill it in.
- `PUBLIC_URL` is where the links in the mail start. The default `http://127.0.0.1:8771` opens only on this computer. If the designer will tap the link on a phone, set an address the phone can reach and start the server with `python chat_server.py --host 0.0.0.0`. With no public server, use `python approve.py <booking id>` instead.

### Mail (SMTP)

Fill `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER` and `SMTP_PASS` in `.env`. Port 587 uses STARTTLS and 465 uses SSL (any other port sends without encryption, so use it only for a test server on your own computer).

- `MAIL_TEST_MODE=1` (default): every designer mail goes to the one address `OFFICE_EMAIL`. Keep this at first.
- For real use: set `MAIL_TEST_MODE=0` and change each designer's `email` in `salon.json` (now `example.com` placeholders) to a real address.

Write passwords only in `.env`, and never upload or share `.env` (it is in `.gitignore`).

## What to try next

- A real identity check: send a code to the phone and check it (now only the name and number are compared)
- When a booking waits too long for approval (for example one day), remind the designer or release the slot: a separate flow that looks at the date
- Days off and lunch breaks for each designer (`salon.json` and the `free_starts` function)
- A reminder text the day before a booking
- Add events and a price list to the salon guide (`file_servers/shop_info/documents/`)
- Real concurrent booking: now two chats booking the same slot at the same moment are checked just before the write, in one process only. A real service keeps bookings in a database that refuses the second one

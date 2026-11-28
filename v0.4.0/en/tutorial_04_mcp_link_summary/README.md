# Tutorial 4. A "link summary assistant" built from well-known MCP servers

Give it 1 to 3 web page addresses. It reads the pages, picks 3 key points from each, saves an English summary report (Markdown) in `reports/` and mails it. Two workers (reader, writer) do the work, and **every tool they use comes from official MCP reference servers**. Not one line of tool code was written, and no API key is needed for the tools.

This is the English edition: the report, the headline and the mail are in English. The Korean edition (`../../ko/tutorial_04_mcp_link_summary`) writes the same report in Korean.

## MCP in three lines

- MCP (Model Context Protocol) is an open standard for how AI programs use outside tools and data.
- An MCP server offers tools (for example: fetch a web page, write a file), and an MCP client such as nextop takes those tools and gives them to workers.
- So by writing one entry in `project.json` for a server that already exists, a worker gets its tools without any tool file.

## What this tutorial shows

- Connecting three existing MCP servers by name and start command only (`mcp_servers` in `project.json`)
  - `fetch`: fetches a web page and turns it into Markdown text (`mcp-server-fetch` 2026.11.4, Python, run with `uvx`)
  - `time`: tells today's date and weekday in a time zone (`mcp-server-time` 2026.11.4, Python, run with `uvx`)
  - `filesystem`: reads and writes files. In this tutorial it may write in **one folder only**, `reports/` (`@modelcontextprotocol/server-filesystem` 2.2.0, Node.js, run with `npx`)
- A server's tools are registered as `<server name>__<tool name>`: `fetch__fetch`, `time__get_current_time`, `filesystem__write_file` ... A worker gets them by listing those names in `tools` of its `worker.json`.
- A project note on a server's tool when its own description is not enough (`notes`): `write_file` of `filesystem` gets "write a bare file name" (see the Korean edition's first real run for why).
- Secret values as `{env:NAME}`: these servers need no key, but for a server that does, write only the name of the `.env` variable, as in `"env": {"API_KEY": "{env:MY_KEY}"}`. The value never shows in records, check messages or tool results.
- What a worker copies is checked by the program: the program reads the saved report file and checks that every address is there word for word, that today's date is there, and that it is English (`workers/writer/checks.py`). No check is judged by a model.

## What you will have at the end

Avery (reader) fetches each address with `fetch__fetch` and writes its title and 3 key points. Pages are named by **number**, not by address (the program carries the addresses). Blake (writer) gets today's date with `time__get_current_time`, writes the report and saves it in `reports/` with `filesystem__write_file`. Finally the program (`mail_report`) **reads the saved file** and mails it as the body and as an attachment. A failed mail does not stop the flow: the reason is kept in the result, and the report stays in `reports/`.

### A real run (2026-11-26)

Model: gpt-5.4-mini through the OpenAI API, nextop 0.4.0.dev6 (a pre-release build of 0.4.0, installed from a wheel). Input: the two pages of `input.json` (the MCP introduction of the official docs and the English Wikipedia article on the Model Context Protocol). The sentences change with the model and the pages every time.

Mail subject: `[Link summary TEST] MCP links summarize the standard and its purpose (2 links)` (`[Link summary TEST]` is there only in test mode, `MAIL_TEST_MODE=1`). The body and the attachment are this file exactly, `reports/links_20261126-235429.md`:

```
# Link summary · 2026-11-26 (Thu)

## 1. What is the Model Context Protocol (MCP)?
URL: https://modelcontextprotocol.io/docs/getting-started/intro
- MCP is an open-source standard for connecting AI applications to external systems.
- It lets AI applications connect to data sources, tools, and workflows to access information and perform tasks.
- The page says MCP can help developers, AI applications, and end-users, and it lists build servers, build clients, and build MCP apps as starting points.

## 2. Model Context Protocol - Wikipedia
URL: https://en.wikipedia.org/wiki/Model_Context_Protocol
- The page says Model Context Protocol is an open standard and open-source framework introduced by Anthropic in November 2024.
- It says MCP standardizes how AI systems integrate and share data with external tools, systems, and data sources.
- It says the protocol was created to address information silos and legacy systems, and that developers often had to build custom connectors before MCP.

## In one line
Both pages describe MCP as a standard for connecting AI systems to external data and tools, and explain why it was created.
```

What I checked: the points say what the pages say (the open standard, Anthropic and November 2024, the information silos and custom connectors), both addresses are word for word the input's, and the date is the one the time server gave, 2026-11-26 (Thursday). There are no Chinese, Japanese or Korean letters. The mail server took the mail. Nothing was sent back by the program: Avery saved the notes at the first try, and Blake wrote the bare file name at once (thanks to the `notes` on `write_file`).

**The reader reads at most the first 5,000 characters of a page.** Avery calls `fetch__fetch` once per page with `max_length` 5000 and does not page on with `start_index`. In the first run of the day the mission only said "Do not page on with start_index", and the model fetched the second part of the Wikipedia article anyway after the result's note that the content was cut (6 model calls, 14,987 tokens); the mission now says not to page on even when the result ends with that note, and in the run above each page was fetched once.

**Time and cost** (gpt-5.4-mini; it changes with the model and the internet):

| Work | Model calls | Time |
|---|---|---|
| Avery: fetching 2 pages + writing the key points | 2 | 7.4 s (5,182 tokens) |
| Blake: date + writing and saving the report + saving the result | 3 | 4.4 s (5,174 tokens) |
| Mail (a local test mail server) | 0 | 0.3 s |
| Whole flow (5 model calls, 10,356 tokens) | 5 | about 12 s |

Checked again with nextop 0.4.0.dev9 (2026-11-27, gpt-5.4-mini, a fresh venv with only the wheel installed): the same two pages, Avery 2 calls (5,172 tokens, `fetch__fetch` twice), Blake 3 calls (5,092 tokens), 5 model calls, 10,264 tokens, 18.0 s, report and mail as above. No tutorial file changed for this version.

## Time and what you need

About 30 minutes. You read a finished project, fill in the settings and run it.

- Python 3.11 to 3.13 and nextop 0.4.0 with MCP: `setup.bat` in step 0 below installs everything (by hand: `pip install -r requirements.txt`). `requirements.txt` pins nextop 0.4.0 and `"nextop": ">=0.4,<0.5"` in `project.json` says which versions this project needs (with another version, `nextop check` tells you how to fix it). If another nextop is already installed, `setup.bat` installs 0.4.0 in its place and shows the installed version at the end.
- [uv](https://docs.astral.sh/uv/) (in `requirements.txt`, so `setup.bat` installs it): `uvx` downloads the Python MCP servers (fetch, time) and runs each in its own environment
- Node.js 24 or newer: `npx` downloads and runs the filesystem server
- An OpenAI API key (the default; any other OpenAI-compatible API that supports tool calls works too, see Settings below)
- SMTP settings of a mail account (optional; without them only the mail is not sent and the report stays in `reports/`)
- The internet the first time (`uvx` and `npx` download the servers); after that they come from the local cache.

You could also install the servers with `pip install mcp-server-fetch`, but they need `mcp` 2.3 or newer and would upgrade the `mcp` nextop itself uses. With `uvx` every server has its own environment and an exact version.

## nextop features you learn here

- `mcp_servers` in `project.json`: three stdio servers (command, arguments, time limit)
- The MCP tool name rule `<server>__<tool>` and a worker's `tools` list
- Project notes (`notes`): adding how to use a server's tool in this project to the server's own description
- Narrowing a server's rights: the filesystem server can write only in the folder given as its argument (`reports`)
- The flow check (`nextop check`) starts the servers, gets their tool lists and checks that every tool a worker names exists
- A program check (`checks.py`) that reads the file an MCP server wrote
- An end block (`mail_report`) whose failed mail does not stop the flow
- Tests without a model: a fake model + the three real MCP servers + a test web page and a test mail server on this computer

## Step by step

Open PowerShell in this folder (`en/tutorial_04_mcp_link_summary`).

### 0. Install: run setup.bat

Double-click `setup.bat` in this folder, or run `.\setup.bat` in PowerShell. On the first run it installs everything this tutorial needs.

- It finds Python 3.11 to 3.13. If there is none, it installs Python 3.12 with winget (then open a new terminal and run `setup.bat` again)
- It makes a virtual environment `.venv` in this folder and installs `requirements.txt` (nextop[mcp] 0.4.0, uv, pytest and the rest). To try a nextop that is not on PyPI yet, give it the path of a wheel file, like `setup.bat C:\downloads\nextop-....whl` (or set the environment variable `NEXTOP_WHEEL`), and only nextop is installed from that file. The wheel must match your Python version (`cp311` means Python 3.11)
- When there is no `.env`, it copies `.env.example` to `.env` and lists the names to fill. You type the key values into `.env` yourself
- It runs the tests that need no model and ends with `Setup OK` when they all pass

This tutorial also needs Node.js (the filesystem server runs with `npx`). `setup.bat` does not install Node.js: when `npx` is missing it tells you to run `winget install -e --id OpenJS.NodeJS.LTS` and stops. After installing, open a new terminal and run `setup.bat` again. The first test run needs the internet, because `uvx` and `npx` download the servers.

You can run it again at any time (an existing `.venv` and `.env` are kept). Run the commands below with the virtual environment on:

```powershell
.venv\Scripts\activate
```

To install by hand instead:

```powershell
py -3.12 -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

### 1. Look at the folders

```
project.json             project settings (LLM connection, three MCP servers)
input.json               the run input: {"links": "address1\naddress2"} (one address per line, 1 to 3)
workers/reader           Avery: fetching pages (fetch__fetch), 3 key points
workers/writer           Blake: the date (time__get_current_time), saving the report (filesystem__write_file)
functions/intake.py      start block: reads the addresses, numbers them and names the report file
functions/mail_report.py end block: reads the saved report and mails it (the flow goes on when the mail fails)
functions/_links.py      settings, reading addresses, the date in the time zone, mail (helpers)
flows/link_summary.json  intake -> Avery -> Blake -> mail_report
reports/                 where reports are saved (the only folder the filesystem server may write in)
tests/                   tests without a model
```

There is no `tools/` folder. All tools come from the MCP servers.

### 2. Test without a model

```powershell
python -m pytest -q tests
```

You should see `14 passed` (the first time takes a little longer while the servers are downloaded). The tests check that:
- the three MCP servers start and their tools are registered as `fetch__fetch`, `time__get_current_time`, `filesystem__write_file` and so on, and the flow check has no errors or warnings
- fetch reads a page, time gives the date in the time zone, and filesystem writes only in `reports/` (writing to `project.json` is refused)
- reading addresses (1 to 3, http/https, no repeats), Avery's check (each page once, 3 key points, English only) and Blake's check (the saved file has the addresses and the date)
- the whole flow runs with a fake model: the real fetch server reads the test pages on this computer, the real filesystem server saves the report, and the mail reaches the test mail server. A report that misses an address is sent back once. Without mail settings the flow still ends well

### 3. Fill in the settings

```powershell
copy .env.example .env
```

(If you make `.env` in Notepad, save it as "UTF-8".) See "Settings" below.

### 4. Check the flow

```powershell
nextop check
```

You should see `OK: mcp link summary (workers 2, tools 20, flows 1, file servers 0)`. The 20 tools are 1 from fetch, 3 from time and 16 from filesystem (the workers get only 3 of them). When a server cannot start you see why, and what the server wrote to its standard error is in `runs/mcp/<server name>.log`.

### 5. Run it

```powershell
nextop run --flow link_summary --input input.json
```

After about 20 seconds (it depends on the model) you see `run <id>: done`. At first `MAIL_TEST_MODE=1`, so the mail goes only to `OFFICE_EMAIL`. To summarize other pages, change `links` in `input.json` (one address per line, separated by `\n`, at most 3).

### 6. Look at the results

- the `OFFICE_EMAIL` inbox: a mail whose subject starts with `[Link summary TEST]`; the body and the attachment (.md) are the report
- `reports/links_<date-time>.md`: the report
- `runs/<run id>/blocks/<block>/attempt-1/`: `inputs.md` (what the model got), `calls.jsonl` (model calls), `tools.jsonl` (MCP tool calls and results, and the sentences the checks sent back)
- `runs/<run id>/blocks/mail_report/attempt-1/output.json`: whether the mail went (`sent`) and why (`note`)

### 7. Look at it in the studio

```powershell
nextop studio
```

Pick the flow `link_summary` in the browser to see intake → Avery → Blake → mail_report. The TOOLS tab lists the MCP tools with their server (`MCP server fetch` and so on) and each server's state (its number of tools, or why it cannot be used). A tool test run sends the server one call (for example `time__get_current_time` with `{"timezone": "Asia/Seoul"}`). Restart the studio after changing a server's settings (the studio keeps its connections while it runs).

## How it works

```
intake (program)   numbers the addresses (1, 2, 3) and names the report file
   |
   +--> Avery (reader)   <-- MCP: fetch__fetch (once per page)
   |        per page number: title and 3 key points (no addresses)
   |        checks.py: each page once, 3 key points, English only
   |        v   notes
   +--> Blake (writer)   <-- MCP: time__get_current_time (today's date), filesystem__write_file (saves in reports/)
   |        the report: date, per page the title, address, key points, one line for all
   |        checks.py: reads the saved file: every address, today's date, English only
   |        v   report (file name, one-line headline)
   +--> mail_report (program)  reads the file in reports/ and mails it; a failure only leaves the reason
```

- Avery names pages only by number. The addresses are in the list intake made, and Blake copies them from that list. Whether the copied addresses are right, letter for letter, the program checks in the saved file.
- The program (intake) names the report file. Blake saves it under that name, and the mail block reads the file of that name. What goes into the mail is the file saved on disk, not text a model put in its output.
- The filesystem server cannot read or write outside the `reports` folder it was given as an argument. The worker got only one of its tools, the write tool.
- **The time zone is Asia/Seoul**, as in the Korean edition (this edition changes only the language). To use your own, change it in three places that must agree: `--local-timezone` of the time server in `project.json`, `timezone` in `workers/writer/mission.md`, and `SEOUL` in `functions/_links.py` (the date the check expects).

## Settings

### LLM (`project.json`, `workers/*/worker.json`, `.env`)

The default is the OpenAI API: `base_url` in `project.json` is `https://api.openai.com/v1` and `"model"` in each `workers/*/worker.json` is `gpt-5.4-mini`. Put your OpenAI API key after `LLM_API_KEY=` in `.env`. Any other OpenAI-compatible API works too: change `base_url` and the model names.

### MCP servers (`mcp_servers` in `project.json`)

```json
"mcp_servers": {
  "fetch": {"transport": "stdio", "command": "uvx",
            "args": ["--from", "mcp-server-fetch==2026.11.4", "mcp-server-fetch"], "timeout": 120},
  "time": {"transport": "stdio", "command": "uvx",
           "args": ["--from", "mcp-server-time==2026.11.4", "mcp-server-time", "--local-timezone", "Asia/Seoul"],
           "timeout": 120},
  "filesystem": {"transport": "stdio", "command": "npx",
                 "args": ["-y", "@modelcontextprotocol/server-filesystem@2.2.0", "reports"], "timeout": 120,
                 "notes": {"write_file": "..."}}
}
```

- The versions are pinned exactly (`==2026.11.4`, `@2.2.0`). Without a pin, a new version may be downloaded one day and behave differently.
- `timeout` 120 seconds: room for downloading the server on the first run.
- The commands run in this folder (the default `cwd`), so `reports` is this folder's `reports/`.
- The fetch server follows each site's robots.txt by default and does not read addresses on this computer or a private network (127.0.0.1, 192.168.x.x). Only the tests add `--allow-private-ips` to read the test pages on this computer.

### Mail (SMTP)

Fill in `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS` and `OFFICE_EMAIL` in `.env`. Port 587 uses STARTTLS and 465 uses SSL (any other port sends without encryption, so use it only for a test server on your own computer).

- `MAIL_TEST_MODE=1` (default): the mail goes only to `OFFICE_EMAIL` and the subject starts with `[Link summary TEST]`.
- For real use: set `MAIL_TEST_MODE=0` and fill in `MAIL_TO=a@example.com,b@example.com` (several, comma separated).

Passwords and keys go only in `.env`. Never commit or share `.env` (it is in `.gitignore`).

## Adding another MCP server

Most well-known MCP servers connect with one line of "start command + arguments". The steps are always the same.

1. In `mcp_servers` of `project.json`, write a name (lower-case letters, digits, `_`) and how to start it. Pin the version exactly.
2. Run `nextop check` to see the tool names (`<server name>__<tool name>`; the studio's TOOLS tab shows them too).
3. Write the name in `tools` of the `worker.json` of the worker that uses it, and say when to use it in that worker's `mission.md`. When the server's description does not say enough about how to use it, add `notes`.

Example 1. A stdio server that needs a key (the value in `.env`, only the variable name in `project.json`):

```json
"github": {"transport": "stdio", "command": "npx",
           "args": ["-y", "@modelcontextprotocol/server-github@<version>"],
           "env": {"GITHUB_PERSONAL_ACCESS_TOKEN": "{env:GITHUB_TOKEN}"}}
```

Example 2. Connecting over http (Streamable HTTP) to a server that already runs somewhere. If a place offers the same fetch tool over http (for example a company MCP gateway that wraps the fetch server):

```json
"fetch": {"transport": "http", "url": "https://<server host>/mcp",
          "headers": {"Authorization": "Bearer {env:FETCH_TOKEN}"}}
```

With the same server name the tool name (`fetch__fetch`) stays the same, so the workers need no change. nextop does not start an http server, it only connects (the server has to be running already).

## Try next

- Take search words instead of addresses: add a search MCP server (Brave Search, for example) and let Avery read the addresses it finds
- Get the same pages summed up every day: register `nextop run --flow link_summary --input input.json` in Windows Task Scheduler (or cron)
- Compare with earlier reports: give Blake `filesystem__read_text_file` and let it write what changed since yesterday's report in `reports/`

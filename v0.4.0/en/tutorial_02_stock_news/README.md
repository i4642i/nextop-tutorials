# Tutorial 2. A "tomorrow's stock outlook" mail every morning

> **Not investment advice · an outlook made from the news**

The flow collects the latest articles about NVIDIA, Apple, Micron and SpaceX from US financial news sites, writes for each company a direction for the next trading day (up, flat, down) and the reasons, each reason backed by a paragraph of an article, and sends it all in one mail. Two workers do the work (collect, analyze); the program writes the mail.

This is the US edition: four US stocks, English articles from US news sites only, English mail, and US colors (green up, red down). The Korean edition (`../../ko/tutorial_02_stock_news`) covers Samsung Electronics, SK hynix, NVIDIA and SpaceX in Korean.

## What you will have at the end

Quinn (news collector) searches the news once per company, keeps only real articles and uploads them to the file server `news` (tagged with the company name; an article whose address is already stored is never uploaded again). Dana (stock outlook analyst) talks about one company at a time (only that company's articles are visible), writes the direction and the reasons, and gives every reason the address of the article paragraph that shows it (for example `fs://news/003#1.2`). The paragraph text in the mail is copied from the article by **the program, not a model** (a model cannot change a letter while copying). The program also checks that the address is a body paragraph of an article Dana may read; when it is not, Dana gets it back. The program writes the mail: titles, dates and addresses come from the stored article files (it never trusts an address a model typed).

SpaceX listed on Nasdaq in June 2026 (SPCX). If you add a company that is not listed, the mail says it has no share price and writes the direction as news mood only (mostly good news, mixed or quiet, mostly bad news).

**A real run (model: gpt-5.4-mini through the OpenAI API, nextop 0.4.0.dev9, a pre-release build of 0.4.0).** This mail came from a real Tavily search and a real model on 2026-11-27 (a Friday, so the next trading day is Monday, Nov 30). It changes with the articles and the model every time.

Subject: `[Stock outlook TEST] 2026-11-30 (Mon) NVIDIA Down, Apple Flat, Micron Down, SpaceX Up` (`[Stock outlook TEST]` is there only in test mode, `MAIL_TEST_MODE=1`. The mail goes as plain text and HTML, and the same content is saved as `outlooks/2026-11-30.txt` and `.html`.)

```
* Not investment advice · an outlook made from the news

Stock outlook for 2026-11-30 (Mon) (news collected 2026-11-27 (Fri))

▼ NVIDIA: Down
▶ Apple: Flat
▼ Micron: Down
▲ SpaceX: Up

## NVIDIA (NVDA (Nasdaq)) · Down
In the news: Recent articles focus on Nvidia falling again as investors pull back from the AI trade, with worries about valuation, leadership, and governance weighing on sentiment.
1. Nvidia shares fell again as investors pulled back from the AI trade, which points to continued selling pressure into the next session.
   Article: Nvidia, AMD, and Micron stocks sink as investors flee AI trade - Yahoo Finance (2026-11-25)
   https://finance.yahoo.com/markets/article/nvidia-amd-micron-stocks-sink-as-investors-flee-ai-trade-134518921.html
   Cited paragraph: "# Nvidia, AMD, and Micron stocks sink as investors flee AI trade. Nvidia (NVDA) stock retreated another 5% on Wednesday, following a 6% decline in the prior session as ch ..."
2. The article says investors are questioning whether spending on advanced chips and data-center infrastructure can generate enough returns, which can keep confidence in the stock weak.
   Article: Nvidia Stock Falls Again as AI Fears and CEO Questions Weigh on Shares - Yahoo Finance (2026-11-25)
   https://finance.yahoo.com/markets/stocks/articles/nvidia-stock-falls-again-ai-151733005.html
   Cited paragraph: "The board reversed course after reviewing concerns about his conduct and leadership, leaving investors to assess whether his return settles questions or creates new conce ..."
3. The story says concerns about inflation and debt are deepening the AI stock sell-off, which adds a broad negative backdrop for Nvidia.
   Article: Why Nvidia Stock Is Falling Again - Yahoo Finance (2026-11-25)
   https://finance.yahoo.com/markets/stocks/articles/why-nvidia-stock-falling-again-185302235.html
   Cited paragraph: "**Nvidia Corporation** (NASDAQ:NVDA) stock is down 5.4% as of 1:29 p.m. ET on Wednesday, Nov. 25, as the sell-off in AI stocks deepens on worries over inflation and debt. ..."

## Apple (AAPL (Nasdaq)) · Flat
In the news: The only available article is a general Apple market page, so there is no fresh company-specific news thread.
1. The only available item is a general market page with a company description and financial tables, so it does not provide fresh news that clearly points the stock up or down.
   Article: Apple Inc. (AAPL) Stock Price, News, Quote & History - Yahoo Finance (2026-11-26)
   https://finance.yahoo.com/quote/AAPL
   Cited paragraph: "Apple Inc. designs, manufactures, and markets smartphones, personal computers, tablets, wearables, and accessories. The company offers iPhone, a line of smartphones; Mac, ..."

## Micron (MU (Nasdaq)) · Down
In the news: Recent articles focus on Micron under pressure from weaker DRAM pricing, tariffs, and a new Huawei-related competitive threat, even though long-term HBM demand remains a positive backdrop.
1. A softer DRAM pricing outlook and new tariffs are hitting memory stocks, which can pressure Micron shares into the next session.
   Article: Micron Falls 7% as a Weaker DRAM Outlook and New Tariffs Hit Memory Stocks; SanDisk Drops 7%: Are Micron and Memory Stocks Now a Value Play? (2026-11-25)
   https://finance.yahoo.com/markets/stocks/articles/micron-falls-7-weaker-dram-141311449.html
   Cited paragraph: "- Micron (MU) has dropped 33% in a month despite record revenue, as softer DRAM pricing forecasts and new tariffs ignite a memory-stock selloff. - SanDisk (SNDK) has plun ..."
2. The article says Huawei's progress adds another long-term risk to Micron's investment thesis by raising the chance of more advanced memory competition from China.
   Article: Micron Stock Faces Surprising New Threat From Huawei (2026-11-26)
   https://finance.yahoo.com/markets/stocks/articles/micron-stock-faces-surprising-threat-180348513.html
   Cited paragraph: "Micron is America's largest memory chip manufacturer, producing DRAM, NAND flash and high-bandwidth memory (NYSE:HBM) products used in data centers, smartphones, computer ..."
3. The bearish view is reinforced by the note that memory investors are already wrestling with elevated valuations and doubts about the sustainability of data center spending.
   Article: Micron Stock Faces Surprising New Threat From Huawei (2026-11-26)
   https://finance.yahoo.com/markets/stocks/articles/micron-stock-faces-surprising-threat-180348513.html
   Cited paragraph: "The development comes at a particularly sensitive time for memory chip investors, who are already grappling with concerns over elevated valuations and the sustainability ..."

## SpaceX (SPCX (Nasdaq)) · Up
In the news: Recent articles focus on SpaceX getting regulatory approval for its space data-center plans while also drawing attention from share giveaways and merger talk.
1. The FCC approved SpaceX's request for one million satellites to create data centers in space, which is a clear regulatory green light for the company's planned business expansion.
   Article: FCC Authorizes SpaceX to Build 1 Million Data Centers in Space - WSJ (2026-11-25)
   https://www.wsj.com/business/fcc-authorizes-spacex-to-build-1-million-data-centers-in-space-0eb20ee7
   Cited paragraph: "The Federal Communications Commission has approved SpaceX’s SPCX 1.74%increase; green up pointing triangle request for one million satellites to create data centers in sp ..."
2. The company said it will give one share of its Class A stock to every active Trump Account, and Elon Musk will personally match the company's contribution, which may support investor sentiment.
   Article: SpaceX, Elon Musk to give one share each to active Trump accounts - Yahoo Finance (2026-11-25)
   https://finance.yahoo.com/markets/article/spacex-elon-musk-to-give-one-share-each-to-active-trump-accounts-205719872.html
   Cited paragraph: "2. Best 0% APR Cards. # SpaceX, Elon Musk to give one share each to active Trump Accounts. SpaceX (SPCX) said Wednesday it will give one share of its Class A stock to eve ..."
3. Talk of a potential all-stock merger with Tesla keeps SpaceX in the market spotlight and could lift attention to the name if deal talks progress.
   Article: SpaceX and Tesla Directors Hold Talks Over Potential US$3.5 Trillion Merger - Yahoo Finance (2026-11-24)
   https://finance.yahoo.com/markets/stocks/articles/spacex-tesla-directors-hold-talks-111930850.html
   Cited paragraph: "# SpaceX and Tesla Directors Hold Talks Over Potential US$3.5 Trillion Merger. Space Exploration Technologies (NASDAQ:SPCX) and Tesla Inc (NASDAQ:TSLA) are exploring a po ..."

* Not investment advice · an outlook made from the news. The cited paragraphs are the article paragraphs the worker chose, copied word for word by the program.
```

(Each cited paragraph is cut after about 170 characters here; the mail has it whole, and the program copies it from the article.)

What I checked in this sample mail: every cited paragraph is the stored article's own text (the program copied it by address), every address and title comes from the article file, and there are no Chinese, Japanese or Korean letters in the sentences. Every cited article is from the US news sites of `stocks.json` (Yahoo Finance, WSJ). What a person may not like: Apple's only "article" is Yahoo Finance's quote page (`/quote/AAPL`: a company description and tables, not news), so Apple is Flat with one reason saying there is no news; and a paragraph can still start with page furniture ("2. Best 0% APR Cards.") or carry a line of the site ("GuruFocus has detected 3 Warning Signs"), because the search gives the page text as it is.

Articles are cut into paragraphs by the splitter part (`parts/splitter/paragraphs.py`, the example part of nextop). The search text often has no blank lines, so a block over 800 characters is cut at sentence ends into paragraphs of about 400 characters (a sentence is never cut), a piece under 15 characters that ends no sentence joins its neighbour, and a "#" line over 200 characters counts as text. In this run's 11 articles: 42 paragraphs, the longest 710 characters, none over 800, none under 15; so a cited paragraph is a few sentences, not a whole article.

**What Dana does with the tools** (from the run's `tools.jsonl`): the 17 model calls of the analyst gave 30 `get` calls and 7 `query` calls (each with an article address and a question). `get` on an article answered its paragraphs with their addresses and text together (`fs://news/005#1.2`, ...). In three of the company conversations the model first tried to save the items of all four companies, and the program refused it (`This conversation is only about NVIDIA; save only its share. ...`), so no conversation overwrote another's items; the final result has 4 items (NVIDIA 3 reasons, Apple 1, Micron 3, SpaceX 3).

**How the program checks a cited paragraph.** When a reason cites a whole article instead of one of its paragraphs, the check sends back a sentence like this (from the tests):

```
NVIDIA: source "fs://news/001" is a whole article; cite one of its paragraphs (an address like fs://news/003#1.2 from a query or get result)
```

The check also sends back reason counts that do not fit the collection status, and sentences with Chinese, Japanese or Korean letters in them (a model sometimes slips them into English): `NVIDIA: point "The unit's 单独 value rises...." has Chinese, Japanese or Korean letters (单独); write it again in English only`.

**Time and cost** (gpt-5.4-mini through the OpenAI API and Tavily; it changes a lot with the model and the internet):

| Work | Result |
|---|---|
| Quinn: 4 searches + choosing articles + uploading 11 of them (5 model calls) | 21,409 tokens |
| Dana: scan + one outlook per company (17 model calls) | 71,990 tokens |
| Whole run (22 model calls) | 64.3 s, 93,399 tokens (0.4.0.dev6: 22 calls, 92,739 tokens, about 50 s) |

## Time and what you need

About an hour. You read a finished project, fill in the settings and run it.

- Python 3.11 to 3.13 and nextop 0.4.0: `setup.bat` in step 0 below installs everything (by hand: `pip install -r requirements.txt`). This tutorial was written for the file servers of nextop 0.4.0 (type folders, common tools). Until 0.4.0 is on PyPI, install from a wheel file you were given: `setup.bat <path to the .whl>` `requirements.txt` pins nextop 0.4.0 and `"nextop": ">=0.4,<0.5"` in `project.json` says which versions this project needs (with another version, `nextop check` tells you how to fix it). If another nextop is already installed, `setup.bat` installs 0.4.0 in its place and shows the installed version at the end.
- An OpenAI API key (the default; any other OpenAI-compatible API works too, see Settings below)
- A web search key: `TAVILY_API_KEY` from [Tavily](https://tavily.com) (4 searches per run)
- SMTP settings of a mail account (optional; without them only the mail step fails and the outlook stays in `outlooks/`)

You can do steps 1 to 3 right away without a model or a search key: the tests use a fake model and a fake search service.

## nextop features you learn here

- A flow that mixes two workers (Quinn, Dana) and program blocks (`plan`, `mail_outlook`)
- Getting things from outside with a tool: the web search is a project tool (`news_search`), not a file server, and the worker only uploads the articles it chose
- A file server that lasts (`lifetime: project`) with tags and expiry (`expire_after`): articles are kept 7 days and get the company name as a tag
- Steps and `for_each`: Dana first scans the news of every company (scan), then talks about each company separately (judge). One conversation sees only that company's articles
- A file server as a type folder (`types/articles/type.json`: md articles, the `paragraphs` splitter from `parts/splitter/paragraphs.py`, a first-sentence map) and the common tools `upload`, `query` and `get`
- Citing one paragraph by its address (`fs://news/003#1.2`): the program checks the address (`checks.py`) and copies the paragraph into the mail
- A function that receives files (`FILES_IN`): the mail function reads the article files itself to get titles and addresses
- Never storing the same article twice (dedupe by page address)
- Tests without a model or a search: a fake model and a fake search server run the whole flow

## Step by step

Open PowerShell in this folder (`en/tutorial_02_stock_news`).

### 0. Install: run setup.bat

Double-click `setup.bat` in this folder, or run `.\setup.bat` in PowerShell. On the first run it installs everything this tutorial needs.

- It finds Python 3.11 to 3.13. If there is none, it installs Python 3.12 with winget (then open a new terminal and run `setup.bat` again)
- It makes a virtual environment `.venv` in this folder and installs `requirements.txt` (nextop, pytest and the rest). Give it the path of a wheel file, like `setup.bat C:\downloads\nextop-0.4.0...whl` (or set the environment variable `NEXTOP_WHEEL`), and only nextop is installed from that file. The wheel must match your Python version (`cp311` means Python 3.11)
- When there is no `.env`, it copies `.env.example` to `.env` and lists the names to fill. You type the key values into `.env` yourself
- It runs the tests that need no model and ends with `Setup OK` when they all pass

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
project.json          project settings (LLM connection)
stocks.json           the four companies (name, ticker, listed or not, search words) and the search settings
workers/collector     Quinn: news search, choosing articles, uploading
workers/analyst       Dana: direction and reasons per company (with the paragraph check)
tools/news_search.py  web search tool (Tavily); saves only new articles as files and lists them
functions/plan.py     start block: which day the outlook is for (Monday after a weekend) and the companies
functions/mail_outlook.py   end block: builds the mail (plain text + HTML) and sends it
functions/_news.py    settings, search, mail (helpers)
file_servers/news     the article store (kept 7 days): file_server.json + types/articles/type.json
parts/splitter/paragraphs.py   the splitter that cuts each article into paragraphs (an example part of this project)
flows/daily_outlook.json    plan -> Quinn -> Dana -> mail
tests/                tests without a model or a search
```

### 2. Test the program parts without a model

```powershell
python -m pytest -q tests
```

You should see `20 passed`. The tests check that:
- the next trading day is right (Friday and Saturday give Monday), addresses are cleaned up (`?utm_...` and a trailing `/` are ignored), dates have one form
- the search tool never stores the same address twice, leaves out articles already stored, social media and sites outside the US news list, asks the search service only for those sites, and returns an error the model can read when the search fails
- a reason that cites a whole article, a section, the date and URL lines or an address that is not an article paragraph is sent back by the paragraph check, and the address of one body paragraph passes; a wrong number of reasons and sentences with Chinese, Japanese or Korean letters are sent back too
- the whole flow runs with a fake model: uploads carry the company tag, each company gets its own conversation (no other company's articles), a reason that cites a whole article is refused once and then fixed, the mail has the cited paragraphs copied by the program and reaches a test mail server
- the mail has the disclaimer, the clean article addresses and the US colors

### 3. Fill in the settings

```powershell
copy .env.example .env
```

(If you make `.env` in Notepad, save it as "UTF-8".) Then fill it in as described in "Settings" below.

### 4. Check the flow

```powershell
nextop check
```

Before the LLM key is filled in you see:

```
[error] adapter llm.default: API key missing: set LLM_API_KEY in the environment or .env
```

With the model address, key and name filled in: `OK: stock news outlook (workers 2, tools 1, flows 1, file servers 1)`.

### 5. Run it

```powershell
nextop run --flow daily_outlook
```

After a minute or two you see `run <id>: done`. At first `MAIL_TEST_MODE=1`, so the mail goes only to `OFFICE_EMAIL`.

### 6. Look at the results

- the `OFFICE_EMAIL` inbox: a mail like the one above (the subject starts with `[Stock outlook TEST]`)
- `outlooks/<date>.txt` and `.html`: the same content
- `file_servers/news/store/`: the stored articles (`items/` are the records, `files/` the article texts), tagged with the company name
- `runs/<run id>/`: the flow's record. Every block has `inputs.md` (what the model got), `calls.jsonl` (model calls) and `tools.jsonl` (tool calls and the sentences the checks sent back). What the paragraph check sent back is in the `save_output` lines of `tools.jsonl` with `refused_by: program`

Run it once more. Articles whose address is already stored are left out by the tool (`skipped_known`), and only new ones are uploaded. Each run makes 4 searches (one per company).

### 7. Change it yourself

- Change or add companies in `stocks.json` (name, ticker, listed, search words) and Quinn and Dana cover them; the tool and the workers stay the same
- Change the news sites in `stocks.json` `search.include_domains` (the search keeps to them, and the tool drops any page from another site)
- Change Dana's rules (what makes up versus flat) in `workers/analyst/mission.md`

## How it works

```
plan (program)  today, the next trading day (Monday after a weekend), the companies
   |
   +--> Quinn (collector)  <-- tool: news_search (Tavily, once per company, US news sites only, new articles saved as files)
   |        uploads only real articles to the news file server (tag: company name)
   |        v   coverage: ok / thin / none per company
   +--> Dana (analyst)     <-- the articles Quinn uploaded (news)
   |        step 1 scan: the main thread of each company's news
   |        step 2 judge (for_each): one conversation per company, only that company's articles
   |             asks each article with query, then writes direction + reasons (the address of one paragraph per reason)
   |             checks.py: each source is one body paragraph (fs://news/003#1.2), reason count, English only
   |        v   outlook
   +--> mail_outlook (program)  reads titles, dates and addresses from the article files, writes the mail --> sends it
```

- Quinn gives the tool only the company name. The search words and the news sites are in `stocks.json`; Quinn only reads the results and chooses.
- The tool writes the article files (title, date, address, text). Quinn uploads them unchanged.
- The tool filters out addresses already stored. It does not open the store folder; it asks the file server through its view (`ctx["file_servers"]["news"].sources()`). The same article under another spelling of its address (`?utm_...`, a trailing `/`) is one address.
- Dana gives every reason the address of one body paragraph. The program checks that the address is such a paragraph of an article Dana may read (not a whole article, not the date and URL lines) and sends it back when it is not; then it copies that paragraph from the article into the mail, so no model ever retypes a quote. There is no check that a model judges.
- The article titles, dates and addresses in the mail are read from the article files by the program. Addresses a model typed are never used.
- In one run the model gets the articles of one company at a time (`for_each`), so the input stays small and no other company's articles slip in.

## Settings

### LLM (`project.json`, `workers/*/worker.json`, `.env`)

The default is the OpenAI API: `base_url` in `project.json` is `https://api.openai.com/v1` and `"model"` in each `workers/*/worker.json` is `gpt-5.4-mini`. Put your OpenAI API key after `LLM_API_KEY=` in `.env`. Any other OpenAI-compatible API works too: change `base_url` and the model names.

When `nextop check` says `OK`, you are done.

### Web search (Tavily)

Put your key after `TAVILY_API_KEY=` in `.env`. Each run makes 4 searches, so check the key's remaining credit now and then. The search settings (how many recent days, results per company, the news sites to keep to and the sites to leave out) are in `search` in `stocks.json`.

### Mail (SMTP)

Fill in `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER` and `SMTP_PASS` in `.env`. Port 587 uses STARTTLS and 465 uses SSL (any other port sends without encryption, so use it only for a test server on your own computer).

- `MAIL_TEST_MODE=1` (default): the mail goes only to `OFFICE_EMAIL` and the subject starts with `[Stock outlook TEST]`. Keep it like this at first.
- For real use: set `MAIL_TEST_MODE=0` and fill in `MAIL_TO=a@example.com,b@example.com` (several, comma separated). The subject then starts with `[Stock outlook]`.

Passwords and keys go only in `.env`. Never commit or share `.env` (it is in `.gitignore`).

### Companies (`stocks.json`)

- `listed`: with `false` the mail says the company has no share price and writes the direction as "Mostly good news / Mixed or quiet / Mostly bad news". SpaceX listed in June 2026, so it is `listed: true`, `SPCX (Nasdaq)`. Use `listed: false` for a company that is not listed.
- The next trading day skips weekends only. It does not know US market holidays (Thanksgiving, for example).

## Try next

- Get it every day at the same time: register `nextop run --flow daily_outlook` in Windows Task Scheduler (or cron) for a time after the US market close
- Add companies (`stocks.json`): the same flow runs unchanged
- Compare yesterday's outlook with today's moves: a separate flow that reads `outlooks/` and the real price changes
- Read whole articles: a tool that fetches the full article text gives more paragraphs to cite (check each site's terms)
- Send each reader only their companies: let the mail function split by `MAIL_TO`

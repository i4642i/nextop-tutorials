# nextop tutorials

Step-by-step projects for [nextop](https://pypi.org/project/nextop/), the framework for agentic workers. Every tutorial is a complete project folder: read it, fill in `.env` and the model settings, run its tests without a model, then run it for real.

한국어 안내: [README.ko.md](README.ko.md)

## Editions

| Edition | Folder | nextop | Language of workers, mail and output |
|---|---|---|---|
| English | [`en/`](en/) | 0.4.0 (`pip install nextop==0.4.0`) | English (`"language": "en"`) |
| Korean | [`ko/`](ko/) | 0.4.0 | Korean (`"language": "ko"`) |
| Japanese | [`ja/`](ja/) | 0.4.0 | Japanese (`"language": "ja"`) |

The editions are not word-for-word translations. Where a tutorial depends on a country, the edition is localised:

| # | Tutorial | English edition | Korean edition | Japanese edition |
|---|---|---|---|---|
| 1 | Hair salon booking chat | [US salon](en/tutorial_01_hair_salon/) (USD, US phone numbers, US designers) | [Korean salon](ko/tutorial_01_hair_salon/) (won, Korean phone numbers) | [Japanese salon](ja/tutorial_01_hair_salon/) (yen, Japanese phone numbers) |
| 2 | Daily stock outlook mail | [US stocks](en/tutorial_02_stock_news/): NVIDIA, Apple, Micron, SpaceX | [Korean and US stocks](ko/tutorial_02_stock_news/): Samsung Electronics, SK hynix, NVIDIA, SpaceX | [US stocks](ja/tutorial_02_stock_news/): NVIDIA, Apple, Micron, SpaceX |
| 3 | PDF to a one-page A4 summary | [English summary](en/tutorial_03_pdf_summary/) | [Korean summary](ko/tutorial_03_pdf_summary/) | [Japanese summary](ja/tutorial_03_pdf_summary/) |
| 4 | Link summary with well-known MCP servers | [English report](en/tutorial_04_mcp_link_summary/) | [Korean report](ko/tutorial_04_mcp_link_summary/) | [Japanese report](ja/tutorial_04_mcp_link_summary/) |
| 5 | PDF to a themed PowerPoint deck | [English slides](en/tutorial_05_pdf_to_ppt/) | [Korean slides](ko/tutorial_05_pdf_to_ppt/) | [Japanese slides](ja/tutorial_05_pdf_to_ppt/) |

## What you need

- Windows: run `setup.bat` in the tutorial folder first. It finds (or installs with winget) Python 3.11 to 3.13, makes `.venv`, installs the folder's `requirements.txt` (nextop 0.4.0 with the extras that tutorial uses), creates `.env` from `.env.example` and runs the tests that need no model
- By hand (any OS): Python 3.11 to 3.13 and `pip install -r requirements.txt` in the tutorial folder
- Tutorial 4 also needs Node.js (`npx`), which `setup.bat` does not install: `winget install -e --id OpenJS.NodeJS.LTS`
- An LLM API key. The default is OpenAI (`https://api.openai.com/v1`, model `gpt-5.4-mini`): put your key in `.env` as `LLM_API_KEY`. Any OpenAI-compatible API works: change `base_url` in `project.json` and the model names in `workers/*/worker.json`
- Optional: an SMTP account for the mails

Start with tutorial 1. Each tutorial folder has a `README.md` (the walk-through) and a `PLATFORM_ISSUES.md` (nextop problems found while building it, with how to reproduce them).

## License

The tutorial files in this repository are under the [MIT License](LICENSE): copy them, change them and use them, also commercially. The nextop platform they run on is a separate package with its own license (see [nextop on PyPI](https://pypi.org/project/nextop/)).

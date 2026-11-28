# nextop tutorials

Step-by-step projects for [nextop](https://pypi.org/project/nextop/), the framework for agentic workers. Each version folder holds the tutorials made for that nextop version, in English, Korean and Japanese; every tutorial pins the nextop it was tested with.

한국어 안내: [README.ko.md](README.ko.md)

| Version | nextop | Tutorials |
|---|---|---|
| [`v0.4.0/`](v0.4.0/) | 0.4.0 (`pip install nextop==0.4.0`) | [English](v0.4.0/en/), [Korean](v0.4.0/ko/), [Japanese](v0.4.0/ja/): hair salon booking chat, daily stock outlook mail, PDF to an A4 summary, link summary with MCP servers, PDF to a PowerPoint deck |

Start with [`v0.4.0/README.md`](v0.4.0/README.md). On Windows, run `setup.bat` in a tutorial folder: it installs that tutorial's libraries (with the pinned nextop) into `.venv` and creates `.env` from `.env.example`, where you put your own API key.

## License

The tutorial files in this repository are under the [MIT License](LICENSE). The nextop platform they run on is a separate package with its own license (see [nextop on PyPI](https://pypi.org/project/nextop/)).

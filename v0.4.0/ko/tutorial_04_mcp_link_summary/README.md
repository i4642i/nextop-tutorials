# 튜토리얼 4. 잘 알려진 MCP 서버로 만드는 "링크 요약 비서"

웹 페이지 주소를 1~3개 주면, 페이지를 읽고 핵심을 3개씩 뽑아 한국어 요약 보고서(Markdown)를 `reports/`에 저장하고 메일로 보내 줍니다. 직원은 둘(읽기, 정리)이고, 직원이 쓰는 도구는 **모두 공식 MCP 참고 서버**입니다. 도구 코드는 한 줄도 쓰지 않았고, API 키도 필요 없습니다.

## MCP를 세 줄로

- MCP(Model Context Protocol)는 AI 프로그램이 바깥 도구와 데이터를 쓰는 방법을 정한 공개 표준입니다.
- MCP 서버는 도구(예: 웹 페이지 가져오기, 파일 쓰기)를 내주고, nextop 같은 MCP 클라이언트가 그 도구를 받아 직원에게 줍니다.
- 그래서 이미 만들어진 MCP 서버를 `project.json`에 한 줄 적기만 하면, 도구 파일을 쓰지 않고도 직원이 그 도구를 씁니다.

## 이 튜토리얼이 보여 주는 것

- 이미 있는 MCP 서버 세 개를 이름과 실행 명령만 적어 연결하기 (`project.json`의 `mcp_servers`)
  - `fetch`: 웹 페이지를 가져와 Markdown 글로 바꿉니다 (`mcp-server-fetch` 2026.11.4, Python, `uvx`로 실행)
  - `time`: 오늘 날짜와 요일을 서울 시간으로 알려 줍니다 (`mcp-server-time` 2026.11.4, Python, `uvx`로 실행)
  - `filesystem`: 파일을 읽고 씁니다. 이 튜토리얼에서는 `reports/` 폴더 **한 곳에만** 쓸 수 있게 열었습니다 (`@modelcontextprotocol/server-filesystem` 2.2.0, Node.js, `npx`로 실행)
- 서버의 도구는 `서버 이름__도구 이름`으로 등록됩니다: `fetch__fetch`, `time__get_current_time`, `filesystem__write_file` ... 직원은 `worker.json`의 `tools`에 이 이름을 적어 받습니다.
- 서버 도구 설명이 모자랄 때 프로젝트가 덧붙이는 설명(`notes`): `filesystem`의 `write_file`에 "파일 이름만 쓰세요"를 붙였습니다(아래 "실제 실행 예" 참고).
- 비밀 값은 `{env:NAME}`으로: 이 튜토리얼의 서버는 키가 필요 없지만, 키가 필요한 서버는 `"env": {"API_KEY": "{env:MY_KEY}"}`처럼 `.env`의 변수 이름만 적습니다. 값은 기록, 검사 알림, 도구 결과 어디에도 나오지 않습니다.
- 직원이 옮겨 쓴 것은 프로그램이 확인합니다: 저장된 보고서 파일을 프로그램이 읽어 모든 주소가 글자 그대로 있는지, 오늘(서울) 날짜가 있는지, 한자가 섞이지 않았는지 봅니다(`workers/writer/checks.py`). 모델이 판단하는 검사는 쓰지 않았습니다.

## 완성하면 이렇게 됩니다

누리(읽기 담당)가 주소마다 `fetch__fetch`로 페이지를 가져와 제목과 핵심 3개를 씁니다. 페이지는 주소가 아니라 **번호**로 가리킵니다(주소는 프로그램이 가지고 다닙니다). 가람(정리 담당)은 `time__get_current_time`으로 오늘 날짜를 확인하고, 보고서를 써서 `filesystem__write_file`로 `reports/`에 저장합니다. 마지막으로 프로그램(`mail_report`)이 **저장된 파일을 읽어** 메일 본문과 첨부로 보냅니다. 메일이 실패해도 흐름은 끝까지 가고, 실패 이유가 결과에 남습니다. 보고서는 `reports/`에 그대로 있습니다.

### 실제 실행 예 (2026-11-25)

모델: 이 컴퓨터에서 쓰는 로컬 모델(OpenAI 호환 API). 입력은 `input.json`의 두 페이지(MCP 공식 문서의 소개 페이지, 영어 위키백과의 Model Context Protocol 문서). 모델과 페이지에 따라 문장은 매번 달라집니다.

메일 제목: `[링크 요약·시험] MCP 두 페이지 요약: AI와 외부 도구·데이터를 잇는 개방 표준의 개요와 탄생 배경 (링크 2개)` (앞의 `[링크 요약·시험]`은 시험 모드(`MAIL_TEST_MODE=1`)일 때만 붙습니다.) 본문과 첨부는 아래 파일 그대로입니다. `reports/links_20261125-024105.md`:

```
# 링크 요약 · 2026-11-25 (수)

## 1. What is the Model Context Protocol (MCP)?
주소: https://modelcontextprotocol.io/docs/getting-started/intro
- MCP는 AI 애플리케이션을 로컬 파일, 데이터베이스 같은 데이터 원천과 검색 엔진 같은 도구, 그리고 워크플로에 연결하는 오픈소스 표준이다.
- 문서는 MCP를 AI 애플리케이션용 USB-C 단자에 비유하며, 전자 기기 연결을 표준화한 것처럼 AI와 외부 시스템 연결을 표준화한다고 설명한다.
- 캘린더·노션 접근, Figma 디자인으로 웹앱 생성, 여러 데이터베이스를 잇는 엔터프라이즈 챗봇 등 가능 사례를 들고 개발자·AI 애플리케이션·최종 사용자 각각의 이점과 클라이언트 지원 범위를 소개한다.

## 2. Model Context Protocol
주소: https://en.wikipedia.org/wiki/Model_Context_Protocol
- MCP는 앤트로픽이 2024년 11월 공개한 개방 표준이자 오픈소스 프레임워크로, LLM 같은 AI 시스템이 외부 도구·시스템·데이터 원천과 데이터를 공유하는 방식을 표준화한다.
- 파일 읽기, 함수 실행, 맥락용 프롬프트 처리를 위한 표준화된 인터페이스를 제공하며, OpenAI와 Google DeepMind를 비롯한 주요 AI 제공 업체가 채택했다.
- 앤트로픽 엔지니어 David Soria Parra와 Justin Spahr-Summers가 만든 이 프로토콜은 정보 사일리와 레거시 시스템, 각 데이터 원천마다 커넥터를 따로 만들던 'N×M' 데이터 통합 문제를 풀기 위해 설계되었고, 2025년 12월 앤트로픽은 MCP를 리눅스 재단 산하 Agentic AI Foundation에 기부했다.

## 한 줄 정리
두 페이지 모두 MCP를 AI와 외부 도구·데이터를 잇는 개방 표준으로 소개하며, 공식 문서는 연결 방식과 활용 사례를, 위키백과는 탄생 배경과 확산·기부까지의 흐름을 보여준다.
```

확인한 것: 핵심 6개의 사실(USB-C 비유, Figma, 2024년 11월, OpenAI·Google DeepMind 채택, 두 설계자 이름, N×M 문제, 2025년 12월 Agentic AI Foundation)은 모두 가져온 페이지 글에 있습니다. 주소 두 개는 입력과 글자 그대로 같고, 날짜는 시간 서버가 준 2026-11-25(수요일)입니다. 한자는 없습니다. "정보 사일리"는 모델의 오타입니다(원문 information silos, "사일로"). 메일은 SMTP 서버가 받았습니다(`mail.sent: true`).

**걸린 시간** (모델 한 대와 이 컴퓨터에서 잰 값입니다. 모델과 인터넷에 따라 크게 달라집니다.)

| 일 | 모델 호출 |
|---|---|
| 누리: 페이지 2개 가져오기 + 핵심 쓰기 | 2번 |
| 가람: 날짜 확인 + 보고서 쓰기와 저장 + 결과 저장 | 3번 |
| 흐름 전체 (모델 호출 5번) | 약 15초 |
| 명령 전체 (MCP 서버 세 개 띄우기와 흐름 검사 포함) | 약 19초 |

**바로 앞의 첫 실행에서 프로그램이 돌려보낸 것.** 같은 입력으로 한 번 먼저 돌렸을 때(모델 호출 7번, 약 25초) 두 번 고쳐졌습니다.

- 누리가 핵심에 한자("例")를 섞고 한 페이지에 핵심을 4개 써서, 검사(`workers/reader/checks.py`)가 돌려보냈습니다: `notes.pages[0].points[2] has Chinese characters (例); write it in Korean only`, `notes.pages[1].points has 4 points; write 3`. 누리가 고쳐 다시 저장했습니다.
- 가람이 파일 경로를 `reports/links_....md`로 써서 filesystem 서버가 거절했습니다(이 서버는 상대 경로를 허락한 폴더 `reports/` 안에서 시작하므로 `reports/reports/...`가 됩니다). 가람은 오류를 읽고 파일 이름만으로 다시 썼습니다. 그 뒤 `project.json`에 이 서버의 `write_file` 설명을 덧붙였고(`notes`), 위 실행에서는 처음부터 파일 이름만 썼습니다.

**PyPI의 nextop 0.3.0으로 다시 확인 (2026-11-25)**: 새 가상 환경에 `pip install "nextop[mcp]==0.3.0"`만 설치하고(플랫폼 소스 없이) 같은 두 페이지로 다시 돌렸습니다. MCP 서버 세 개가 그대로 떴고, 모델 호출 6번(누리 2번, 가람 4번), 흐름 15.2초(명령 전체 약 19초)에 보고서가 `reports/`에 저장되고 메일이 갔습니다(`mail.sent: true`). 이번에는 가람의 한 줄 제목에 중국어 글자(历来)가 섞여 프로그램이 한 번 돌려보냈습니다. 시험은 `14 passed`입니다.

**nextop 0.4.0(개발판 0.4.0.dev6)으로 다시 확인 (2026-11-27)**: 이 튜토리얼은 파일 서버를 쓰지 않아요. 토큰을 아끼려고 누리의 임무를 "페이지마다 앞 5,000자만 한 번 읽기"(`max_length` 5000, 뒷부분 `start_index`는 부르지 않음)로 바꿨어요. 새 가상 환경에 휠만 설치하고 같은 두 페이지로 돌렸더니 MCP 서버 세 개가 그대로 떴고, 누리는 페이지마다 가져오기를 한 번씩만 불렀어요. 모델 호출 5번(누리 2번, 가람 3번), 11,371 토큰, 흐름 13.9초에 보고서가 저장되고 메일이 갔어요. 개발판 0.4.0.dev5 때는 위키백과 페이지를 5,000자씩 네 번 읽어서 8번(누리 5번), 30,380 토큰, 28.7초였어요. 앞 5,000자만 읽어도 두 페이지의 핵심 세 개씩(정의, 하는 일, 등장 배경과 채택)은 그대로 나왔어요.

## 만드는 데 걸리는 시간과 준비물

약 30분. 이미 만들어진 프로젝트를 읽고 설정을 채워 돌려 보는 튜토리얼입니다.

- Python 3.11~3.13과 nextop 0.4.0(MCP 기능 포함): 아래 0단계의 `setup.bat`이 모두 설치합니다(직접 하려면 `pip install -r requirements.txt`). `requirements.txt`가 nextop 0.4.0을 고정하고 `project.json`의 `"nextop": ">=0.4,<0.5"`가 이 프로젝트에 필요한 버전을 알립니다(다른 버전이면 `nextop check`가 어떻게 고치는지 알려 줍니다). 이미 다른 nextop이 깔려 있으면 `setup.bat`이 0.4.0으로 맞추고, 끝에 깔린 버전을 보여 줍니다.
- [uv](https://docs.astral.sh/uv/) (`requirements.txt`에 들어 있어 `setup.bat`이 설치합니다): `uvx`가 Python MCP 서버(fetch, time)를 각자 따로 된 환경에 받아 실행합니다
- Node.js 24 이상: `npx`가 filesystem 서버를 받아 실행합니다
- OpenAI API 키 (기본값입니다. 도구 호출을 지원하는 다른 OpenAI 호환 API도 됩니다. 아래 설정 참고)
- 메일 보내는 계정의 SMTP 정보 (선택. 없으면 메일만 안 가고 보고서는 `reports/`에 남습니다)
- 처음 한 번은 인터넷이 필요합니다(`uvx`, `npx`가 서버를 내려받습니다). 그다음부터는 저장해 둔 것을 씁니다.

서버를 `pip install mcp-server-fetch`로 설치해도 되지만, 이 서버들은 `mcp` 2.3 이상을 요구해 nextop이 쓰는 `mcp`를 올리게 됩니다. `uvx`로 실행하면 서버마다 따로 된 환경을 쓰고 버전도 정확히 고정됩니다.

## 이 튜토리얼로 배우는 nextop 기능

- `project.json`의 `mcp_servers`: stdio 서버 세 개(명령, 인자, 시간 제한)
- MCP 도구 이름 규칙 `<server>__<tool>`과 직원의 `tools` 목록
- 프로젝트 보충 설명 `notes`: 서버의 도구 설명에 우리 프로젝트에 맞는 쓰는 법 덧붙이기
- 서버의 권한 좁히기: filesystem 서버는 인자로 준 폴더(`reports`)에만 쓸 수 있습니다
- 흐름 검사(`nextop check`)가 서버를 띄워 도구 목록을 받아 보고, 직원이 적은 도구가 서버에 있는지 확인합니다
- 프로그램 검사(`checks.py`)가 MCP 서버가 쓴 파일을 직접 읽어 확인하기
- 메일 실패가 흐름을 멈추지 않는 끝 블록(`mail_report`)
- 모델 없이 하는 시험: 가짜 모델 + 진짜 MCP 서버 세 개 + 내 컴퓨터의 시험 웹 페이지와 시험 메일 서버

## 단계별 따라 하기

PowerShell에서 이 폴더(`ko/tutorial_04_mcp_link_summary`)로 이동해 시작합니다.

### 0. 설치: setup.bat 실행

이 폴더의 `setup.bat`을 두 번 클릭하거나, PowerShell에서 `.\setup.bat`을 실행합니다. 처음 한 번 필요한 것을 모두 자동으로 설치합니다.

- Python 3.11~3.13을 찾습니다. 없으면 winget으로 Python 3.12를 설치합니다(설치 뒤 터미널을 새로 열고 `setup.bat`을 다시 실행)
- 이 폴더에 가상 환경 `.venv`를 만들고 `requirements.txt`(nextop[mcp] 0.4.0, uv, pytest 등)를 설치합니다. 아직 PyPI에 없는 nextop을 시험할 때는 `setup.bat C:\받은폴더\nextop-....whl`처럼 휠 파일 경로를 주면(또는 환경 변수 `NEXTOP_WHEEL`) nextop만 그 파일로 설치합니다. 휠 파일은 파이썬 버전에 맞아야 합니다(`cp311`이면 Python 3.11)
- `.env`가 없으면 `.env.example`을 복사해 만들고, 채워야 할 이름만 보여 줍니다. 키 값은 직접 `.env`에 적습니다
- 모델 없이 하는 시험을 돌리고, 모두 통과하면 마지막에 `Setup OK`가 나옵니다

이 튜토리얼은 Node.js도 필요합니다(filesystem 서버를 `npx`로 실행). `setup.bat`은 Node.js를 설치하지 않습니다. `npx`가 없으면 `winget install -e --id OpenJS.NodeJS.LTS`로 설치하라고 알려 주고 멈춥니다. 설치한 뒤 터미널을 새로 열고 `setup.bat`을 다시 실행합니다. 첫 시험은 `uvx`와 `npx`가 서버를 내려받으므로 인터넷이 필요합니다.

여러 번 실행해도 됩니다(이미 있는 `.venv`와 `.env`는 그대로 둡니다). 아래 명령은 가상 환경을 켠 뒤 실행합니다.

```powershell
.venv\Scripts\activate
```

직접 설치하려면:

```powershell
py -3.12 -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

### 1. 폴더 구조 보기

```
project.json             프로젝트 설정 (LLM 연결, MCP 서버 세 개)
input.json               실행에 넘기는 값: {"links": "주소1\n주소2"} (한 줄에 주소 하나, 1~3개)
workers/reader           누리: 페이지 가져오기(fetch__fetch), 핵심 3개
workers/writer           가람: 날짜(time__get_current_time), 보고서 저장(filesystem__write_file)
functions/intake.py      시작 블록: 주소를 읽어 번호를 붙이고 보고서 파일 이름을 정함
functions/mail_report.py 끝 블록: 저장된 보고서를 읽어 메일로 보냄 (실패해도 흐름은 계속)
functions/_links.py      설정, 주소 읽기, 서울 날짜, 메일 보내기 (도우미)
flows/link_summary.json  intake -> 누리 -> 가람 -> mail_report
reports/                 보고서가 저장되는 곳 (filesystem 서버가 쓸 수 있는 유일한 폴더)
tests/                   모델 없이 하는 시험
```

도구 파일(`tools/`)이 없습니다. 도구는 모두 MCP 서버가 내줍니다.

### 2. 모델 없이 시험하기

```powershell
python -m pytest -q tests
```

`14 passed`가 보이면 됩니다(처음에는 서버를 내려받느라 조금 더 걸립니다). 이 시험이 확인하는 것:
- MCP 서버 세 개가 뜨고 도구가 `fetch__fetch`, `time__get_current_time`, `filesystem__write_file` 같은 이름으로 등록된다. 흐름 검사에 오류와 경고가 없다
- fetch가 페이지를 읽고, time이 서울 날짜를 주고, filesystem은 `reports/`에만 쓴다(`project.json`에 쓰려 하면 거절)
- 주소 읽기(1~3개, http/https, 중복 제거), 누리의 검사(페이지마다 한 번, 핵심 3개, 한자), 가람의 검사(저장된 파일에 주소와 날짜가 있나)
- 가짜 모델로 흐름 전체가 돈다: 진짜 fetch 서버가 내 컴퓨터의 시험 페이지를 읽고, 진짜 filesystem 서버가 보고서를 저장하고, 메일이 시험 메일 서버에 도착한다. 주소를 빠뜨린 보고서는 한 번 돌려보내진다. 메일 설정이 없어도 흐름은 성공으로 끝난다

### 3. 설정 채우기

```powershell
copy .env.example .env
```

(메모장으로 `.env`를 새로 만들 때는 "UTF-8"(BOM 없음)로 저장하세요.) 자세한 내용은 아래 "설정 채우기" 절을 보세요.

### 4. 흐름 검사

```powershell
nextop check
```

`OK: mcp link summary (workers 2, tools 20, flows 1, file servers 0)`가 나오면 됩니다. 도구 20개는 fetch 1개, time 3개, filesystem 16개입니다(직원은 그중 3개만 받습니다). 서버를 띄우지 못하면 이유가 나오고, 서버가 표준 오류에 쓴 것은 `runs/mcp/<서버 이름>.log`에 남습니다.

### 5. 실행

```powershell
nextop run --flow link_summary --input input.json
```

20초쯤 뒤(모델에 따라 다릅니다) `run <번호>: done`이 나옵니다. 처음에는 `MAIL_TEST_MODE=1`이라 메일이 `OFFICE_EMAIL` 한 곳으로만 갑니다. 다른 페이지를 요약하려면 `input.json`의 `links`를 바꿉니다(한 줄에 주소 하나, `\n`으로 나눔, 최대 3개).

### 6. 결과 확인

- `OFFICE_EMAIL`의 메일함: 제목이 `[링크 요약·시험]`으로 시작하는 메일, 본문과 첨부(.md)가 보고서
- `reports/links_<날짜-시각>.md`: 보고서
- `runs/<실행 번호>/blocks/<블록>/attempt-1/`: `inputs.md`(모델이 받은 것), `calls.jsonl`(모델 호출), `tools.jsonl`(MCP 도구 호출과 결과, 검사가 돌려보낸 문장)
- `runs/<실행 번호>/blocks/mail_report/attempt-1/output.json`: 메일이 갔는지(`sent`)와 이유(`note`)

### 7. 스튜디오에서 보기

```powershell
nextop studio
```

브라우저에서 흐름 `link_summary`를 고르면 intake → 누리 → 가람 → mail_report가 보입니다. TOOLS 탭에는 MCP 도구가 서버 이름(`MCP server fetch` 등)과 함께 나오고, 서버마다 상태(도구 수 또는 쓸 수 없는 이유)가 나옵니다. 도구 시험 실행은 서버에 호출을 한 번 보냅니다(예: `time__get_current_time`에 `{"timezone": "Asia/Seoul"}`). 서버 설정을 바꾼 뒤에는 스튜디오를 다시 켜세요(스튜디오가 켜져 있는 동안 연결을 유지합니다).

## 어떻게 동작하나

```
intake (프로그램)   주소에 번호(1, 2, 3)를 붙이고 보고서 파일 이름을 정함
   |
   +--> 누리 (reader)   <-- MCP: fetch__fetch (페이지마다 1번)
   |        페이지 번호마다 제목과 핵심 3개 (주소는 쓰지 않음)
   |        checks.py: 페이지마다 한 번, 핵심 3개, 한자 없음
   |        v   notes
   +--> 가람 (writer)   <-- MCP: time__get_current_time (서울 날짜), filesystem__write_file (reports/에 저장)
   |        보고서: 날짜, 페이지마다 제목, 주소, 핵심, 한 줄 정리
   |        checks.py: 저장된 파일을 읽어 주소 전부, 오늘 날짜, 한자 없음
   |        v   report (파일 이름, 한 줄 제목)
   +--> mail_report (프로그램)  reports/의 파일을 읽어 메일로 보냄. 실패해도 이유만 남기고 끝
```

- 누리는 페이지를 번호로만 가리킵니다. 주소는 intake가 만든 목록에 있고, 가람은 그 목록에서 주소를 옮겨 씁니다. 옮긴 주소가 글자 그대로 맞는지는 프로그램이 저장된 파일에서 확인합니다.
- 보고서 파일 이름은 프로그램(intake)이 정합니다. 가람은 그 이름으로 저장하고, 메일 블록은 같은 이름의 파일을 읽습니다. 메일에 들어가는 것은 모델이 출력에 적은 글이 아니라 디스크에 저장된 파일입니다.
- filesystem 서버는 실행 인자로 받은 `reports` 폴더 밖으로는 읽지도 쓰지도 못합니다. 직원에게는 쓰기 도구 하나만 주었습니다.

## 설정 채우기

### LLM (`project.json`, `workers/*/worker.json`, `.env`)

기본값은 OpenAI API입니다. `project.json`의 `base_url`은 `https://api.openai.com/v1`, 각 `workers/*/worker.json`의 `"model"`은 `gpt-5.4-mini`입니다. `.env`의 `LLM_API_KEY=` 뒤에 OpenAI API 키를 넣으세요. 다른 OpenAI 호환 API도 됩니다. `base_url`과 모델 이름을 바꾸세요.

### MCP 서버 (`project.json`의 `mcp_servers`)

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

- 버전은 정확히 고정했습니다(`==2026.11.4`, `@2.2.0`). 고정하지 않으면 어느 날 새 판이 받아져 동작이 바뀔 수 있습니다.
- `timeout` 120초: 처음 실행할 때 서버를 내려받는 시간까지 넉넉히 줍니다.
- 명령은 이 폴더에서 실행됩니다(`cwd`의 기본값). 그래서 `reports`는 이 폴더의 `reports/`입니다.
- fetch 서버는 기본으로 사이트의 robots.txt를 따르고, 내 컴퓨터나 사내망 주소(127.0.0.1, 192.168.x.x)는 읽지 않습니다. 시험(`tests/`)에서만 `--allow-private-ips`를 붙여 내 컴퓨터의 시험 페이지를 읽습니다.

### 메일 (SMTP)

`.env`의 `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`, `OFFICE_EMAIL`을 채웁니다. 포트 587은 STARTTLS, 465는 SSL입니다(그 밖의 포트는 암호화 없이 보내므로 내 컴퓨터의 시험 서버에만 쓰세요).

- `MAIL_TEST_MODE=1`(기본): 메일이 `OFFICE_EMAIL` 한 곳으로만 가고 제목이 `[링크 요약·시험]`으로 시작합니다.
- 실제 운영: `MAIL_TEST_MODE=0`으로 바꾸고 `MAIL_TO=a@example.com,b@example.com`(쉼표로 여러 명)을 채웁니다.

비밀번호와 키는 `.env`에만 쓰고, `.env`는 올리거나 공유하지 마세요(`.gitignore`에 들어 있습니다).

## 다른 MCP 서버 더하기

잘 알려진 MCP 서버는 대부분 "실행 명령 + 인자" 한 줄로 붙습니다. 순서는 늘 같습니다.

1. `project.json`의 `mcp_servers`에 이름(소문자, 숫자, `_`)과 실행 방법을 적습니다. 버전은 정확히 고정합니다.
2. `nextop check`로 도구 이름을 봅니다(`<서버 이름>__<도구 이름>`, 스튜디오 TOOLS 탭에서도 보입니다).
3. 쓸 직원의 `worker.json` `tools`에 그 이름을 적고, 언제 쓰는지는 그 직원의 `mission.md`에 씁니다. 어떻게 쓰는지가 서버 설명으로 모자라면 `notes`에 덧붙입니다.

예 1. 키가 필요한 stdio 서버 (값은 `.env`에, `project.json`에는 변수 이름만):

```json
"github": {"transport": "stdio", "command": "npx",
           "args": ["-y", "@modelcontextprotocol/server-github@<버전>"],
           "env": {"GITHUB_PERSONAL_ACCESS_TOKEN": "{env:GITHUB_TOKEN}"}}
```

예 2. 이미 어딘가에서 돌고 있는 서버에 http(Streamable HTTP)로 붙기. 같은 fetch 도구를 http로 내주는 곳(예: 사내 MCP 게이트웨이가 fetch 서버를 감싸 내주는 경우)이 있다면:

```json
"fetch": {"transport": "http", "url": "https://<서버 주소>/mcp",
          "headers": {"Authorization": "Bearer {env:FETCH_TOKEN}"}}
```

서버 이름이 같으면 도구 이름(`fetch__fetch`)도 같으니, 직원 설정은 바꿀 필요가 없습니다. http 서버는 nextop이 띄우지 않고 연결만 합니다(서버는 따로 켜 두어야 합니다).

## 다음에 해 볼 것

- 주소 대신 검색어를 받기: 검색 MCP 서버(예: Brave Search)를 더하고, 누리가 검색해 나온 주소를 읽게 하기
- 매일 같은 페이지 요약 받기: Windows 작업 스케줄러에 `nextop run --flow link_summary --input input.json` 등록
- 지난 보고서와 비교하기: 가람에게 `filesystem__read_text_file`을 주고 `reports/`의 어제 보고서와 무엇이 바뀌었는지 쓰게 하기

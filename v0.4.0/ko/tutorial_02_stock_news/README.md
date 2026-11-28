# 튜토리얼 2. 매일 아침 받는 "내일 주가 전망" 메일

> **투자 권유가 아닙니다 · 뉴스로 만든 전망입니다**

삼성전자, SK하이닉스, NVIDIA, SpaceX의 최신 기사를 모으고, 회사마다 내일 방향(오름, 보합, 내림)과 이유를 쓰고 이유마다 근거가 된 기사 문단을 붙인 뒤, 한 통의 메일로 보내 줍니다. 일하는 직원은 둘(수집, 분석)이고 메일은 프로그램이 만듭니다.

## 완성하면 이렇게 됩니다

한결(수집 담당)이 회사마다 뉴스를 한 번씩 검색해 진짜 기사만 골라 파일 서버(`news`)에 올립니다(태그는 회사 이름, 이미 저장된 기사 주소는 다시 올리지 않습니다). 다온(분석 담당)은 회사 하나씩 따로 대화하며(그 회사의 기사만 보입니다) 방향과 이유를 쓰고, 이유마다 근거가 된 기사 문단의 주소(예: `fs://news/003#1.2`)를 붙입니다. 메일에 실리는 문단의 원문은 **모델이 아니라 프로그램이** 기사에서 그대로 옮깁니다(모델이 옮겨 쓰다 글자를 바꿀 일이 없습니다). 그 주소가 다온이 읽을 수 있는 기사의 본문 문단인지는 프로그램이 검사하고, 아니면 다온에게 돌려보냅니다. 메일은 프로그램이 기사 파일에서 제목, 날짜, 주소를 읽어 만듭니다(모델이 쓴 주소를 믿지 않습니다).

SpaceX는 2026년 6월 나스닥에 상장했습니다(SPCX). 상장하지 않은 회사를 넣으면 메일이 "주가가 없다"고 밝히고, 방향을 "뉴스 분위기"(호재 중심, 섞임·잠잠, 악재 중심)로만 씁니다.

**실제 실행 예 (모델: OpenAI 호환 API)** 아래는 실제 검색과 실제 모델로 만든 메일이에요. 기사와 모델에 따라 매번 달라져요. 기사는 2026년 11월 27일(금)에 검색한 것이고(nextop 0.4.0 개발판 0.4.0.dev7, 모델 gpt-5.4-mini), 금요일에 돌려서 다음 거래일은 월요일(11월 30일)이에요. SpaceX는 상장 회사라 다른 회사처럼 상승, 보합, 하락으로 씁니다.

제목: `[주가 전망·시험] 2026-11-30(월) 삼성전자 상승 · SK하이닉스 보합 · NVIDIA 하락 · SpaceX 상승` (앞의 `[주가 전망·시험]`은 시험 모드(`MAIL_TEST_MODE=1`)일 때만 붙습니다. 메일은 글자판과 HTML 두 가지로 가고, 같은 내용이 `outlooks/2026-11-30.txt`와 `.html`로도 남습니다.)

```
※ 투자 권유가 아닙니다 · 뉴스로 만든 전망입니다

2026-11-30 (월) 주가 전망 (뉴스 수집일 2026-11-27 (금))

▲ 삼성전자: 상승
▶ SK하이닉스: 보합
▼ NVIDIA: 하락
▲ SpaceX: 상승

## 삼성전자 (005930 (KOSPI)) · 상승
뉴스 흐름: 삼성디스플레이의 Ams OSRAM 지분 투자와 microLED 협력 소식이 중심이다.
1. 삼성디스플레이가 Ams OSRAM과 전략적 파트너십을 맺고 지분 투자를 하면서 microLED 협력이 강화돼 사업 기대감이 커질 수 있다.
   기사: Samsung Display agrees to buy 9% stake in Ams OSRAM under microLED partnership - electronics.economictimes.indiatimes.com (2026-11-26)
   https://electronics.economictimes.indiatimes.com/news/components-hardware/samsung-display-agrees-to-buy-9-stake-in-ams-osram-under-microled-partnership/136176209
   근거 문단: "After years of policy push, infrastructure investments, and growing global interest, the country is no longer just an emerging manufacturing destination.## ETElectronics Newsletters. # Samsung Display agrees to buy 9% stake in Ams OSRAM under microLED partnership. Shares in ams OSRAM were up 15% on Wednesday, having jumped as much as 25% earlier in the session, after it said Samsung Display would invest €210 million ($230 million) for a 9.1% stake in the Austrian semiconductor supplier under a strategic partnership. Samsung Display's multi-year development funding is expected to generate high-double-digit-million-euro annual revenue, supporting development costs and helping absorb fixed costs at the facility."
2. 기사에 따르면 삼성디스플레이의 다년간 개발 자금 지원은 파트너사의 개발비와 고정비 부담을 덜어주는 구조라 협력 안정성이 높아 보인다.
   기사: Samsung Display agrees to buy 9% stake in Ams OSRAM under microLED partnership - electronics.economictimes.indiatimes.com (2026-11-26)
   https://electronics.economictimes.indiatimes.com/news/components-hardware/samsung-display-agrees-to-buy-9-stake-in-ams-osram-under-microled-partnership/136176209
   근거 문단: "After years of policy push, infrastructure investments, and growing global interest, the country is no longer just an emerging manufacturing destination.## ETElectronics Newsletters. # Samsung Display agrees to buy 9% stake in Ams OSRAM under microLED partnership. Shares in ams OSRAM were up 15% on Wednesday, having jumped as much as 25% earlier in the session, after it said Samsung Display would invest €210 million ($230 million) for a 9.1% stake in the Austrian semiconductor supplier under a strategic partnership. Samsung Display's multi-year development funding is expected to generate high-double-digit-million-euro annual revenue, supporting development costs and helping absorb fixed costs at the facility."

## SK하이닉스 (000660 (KOSPI)) · 보합
뉴스 흐름: HBM 수요와 메모리 업황 둔화 가능성을 둘러싼 전망이 중심이다.
1. AI 데이터센터 건설이 늦어지고 AI 인프라 투자 속도가 둔화될 수 있다는 우려가 있어 수급이 약해질 수 있다.
   기사: “400만원 간다더니 장난하나” SK하이닉스 주가 이번엔 105만원까지 낮췄다는데 | 레쓰쌤의 경제리포트 (2026-11-22)
   https://v.daum.net/v/uAwTqn4qvw
   근거 문단: "비관론은 미국 데이터센터 건설이 늦어지고 AI 인프라 투자 속도가 둔화될 수 있다는 데서 출발합니다."
2. 대형 고객사가 설비투자를 줄이면 HBM 주문 증가율이 낮아지고 범용 DRAM 가격에도 부담이 생길 수 있다.
   기사: “400만원 간다더니 장난하나” SK하이닉스 주가 이번엔 105만원까지 낮췄다는데 | 레쓰쌤의 경제리포트 (2026-11-22)
   https://v.daum.net/v/uAwTqn4qvw
   근거 문단: "대형 고객사가 설비투자를 줄이면 HBM 주문 증가율이 낮아지고 범용 DRAM 가격에도 부담이 생길 수 있습니다."

## NVIDIA (NVDA (NASDAQ)) · 하락
뉴스 흐름: AI 관련 기대가 식으면서 반도체주가 함께 약세를 보인다는 내용이 중심이다.
1. Nvidia 주가가 크게 밀렸고 AI 반도체 기대가 다시 약해졌다고 적혀 있어 다음 거래일에도 약세가 이어질 수 있다.
   기사: Nvidia, AMD, Broadcom lead chip stocks lower as AI trade comes under pressure (2026-11-24)
   https://finance.yahoo.com/markets/article/nvidia-amd-broadcom-lead-chip-stocks-lower-as-ai-trade-comes-under-pressure-141635463.html
   근거 문단: "Nvidia (NVDA) stock retreated 6% on Tuesday, giving back some of its 31% surge from the prior session after the board of the AI chip giant reinstated Jensen Huang as CEO. Peers AMD (AMD) and Broadcom (AVGO) also declined from Monday's rebound as the overall AI trade came under renewed pressure."
2. AMD와 Broadcom도 함께 내렸고 전체 AI 거래가 압력을 받았다고 해 개별 종목보다 업종 전반의 부담이 더 크다.
   기사: Nvidia, AMD, Broadcom lead chip stocks lower as AI trade comes under pressure (2026-11-24)
   https://finance.yahoo.com/markets/article/nvidia-amd-broadcom-lead-chip-stocks-lower-as-ai-trade-comes-under-pressure-141635463.html
   근거 문단: "Nvidia (NVDA) stock retreated 6% on Tuesday, giving back some of its 31% surge from the prior session after the board of the AI chip giant reinstated Jensen Huang as CEO. Peers AMD (AMD) and Broadcom (AVGO) also declined from Monday's rebound as the overall AI trade came under renewed pressure."

## SpaceX (SPCX (NASDAQ)) · 상승
뉴스 흐름: Starlink 같은 기존 사업에서 꾸준한 현금이 들어오는 점과 사업 가치 평가가 중심이다.
1. 기사는 SpaceX가 이미 매달 임대료처럼 현금을 받고 있다고 해서, 투자자들이 아직 실현되지 않은 기대보다 현재의 현금 유입을 더 높게 볼 수 있다고 말한다.
   기사: Not Starlink. Not Starship. This SpaceX Business Could Be Worth $80 Billion on Its Own. (2026-11-24)
   https://finance.yahoo.com/markets/stocks/articles/not-starlink-not-starship-spacex-055002627.html
   근거 문단: "Still, I keep coming back to that first-of-the-month check. While investors argue over Starship's next flight, SpaceX is already collecting rent, and in a market this nervous about AI, cash coming in every month is worth more than another promise."
2. 공개된 SpaceX 계약 두 건의 월간 규모가 크게 제시돼 있어, 사업 가치가 다시 높게 평가될 여지가 있다.
   기사: Not Starlink. Not Starship. This SpaceX Business Could Be Worth $80 Billion on Its Own. (2026-11-24)
   https://finance.yahoo.com/markets/stocks/articles/not-starlink-not-starship-spacex-055002627.html
   근거 문단: "The two disclosed SpaceX contracts total $2.17 billion a month. That's a conservative enterprise value because it ignores every other cloud customer and uses a multiple from one of the most hated stocks in cloud computing right now."

※ 투자 권유가 아닙니다 · 뉴스로 만든 전망입니다. 근거 문단은 직원이 고른 기사 문단을 프로그램이 원문 그대로 옮긴 것입니다.
```

이유마다 붙은 "근거 문단"은 다온이 고른 문단 주소(예: `fs://news/002#1.2`)를 보고 **프로그램이** 기사 파일에서 그 문단을 그대로 옮긴 거예요. 다온은 회사 하나씩 따로 대화했고, 대화마다 자기 회사 몫만 저장했어요. NVIDIA 대화에서 다온이 처음에 네 회사를 한꺼번에 저장하려 하자 플랫폼이 "이 대화는 NVIDIA만 다룹니다. 그 몫만 저장하세요"라고 돌려보냈고, 다온이 그 회사 몫만 다시 저장했어요(그래서 앞 대화의 이유가 덮어써지지 않아요). 한결이 회사마다 기사를 하나씩 골라 상태가 thin이라 이유는 1~2개인데, 다온이 3개를 쓴 회사(SK하이닉스, NVIDIA, SpaceX)는 프로그램이 "thin이니 1~2개"라고 돌려보냈어요.

기사는 문단 쪼개기 부품(`parts/splitter/paragraphs.py`)이 문단으로 나눠요. 검색(Tavily)이 준 본문에는 빈 줄이 없는 경우가 많아서, 800자가 넘는 덩어리는 문장 끝에서 400자쯤마다 나눠요(문장은 자르지 않아요). 그래서 근거 문단이 기사 한 덩어리가 아니라 몇 문장짜리 문단이에요. 이번 기사 네 개는 문단 38개, 가장 긴 문단 718자, 800자 넘는 문단 0개였어요(같은 기사를 예전 부품으로 나누면 가장 긴 문단 1,218자). 삼성전자의 근거 문단 앞부분에는 아직 기사 사이트의 메뉴 글 한 줄이 남아 있어요(메뉴와 기사 첫 문장 사이에 문장 끝이 없어서 함께 묶였어요). 프로그램은 문단을 고치지 않고 그대로 옮겨요. 또 삼성전자와 NVIDIA는 두 이유가 같은 문단을 근거로 썼어요(임무는 같은 기사를 두 번 쓰면 다른 문단을 고르라고 하지만, 프로그램이 검사하지는 않아요).

**프로그램이 근거 문단을 검사하는 모습.** 이유의 주소가 기사 전체(`fs://news/001`)나 여러 문단이 든 부분(`#1`), 날짜·주소 줄이면 프로그램이 이렇게 돌려보냅니다(시험에서 나온 문장).

```
삼성전자: source "fs://news/001" is a whole article; cite one of its paragraphs (an address like fs://news/003#1.2 from a query or get result)
```

**걸린 시간과 토큰** (gpt-5.4-mini와 이 컴퓨터에서 잰 값이에요. 모델과 인터넷에 따라 크게 달라져요.) 전체 61.5초, 모델 호출 26번(한결 4번, 다온 22번), 98,961 토큰. 개발판 0.4.0.dev6 때(24번, 93,452 토큰, 59.7초)와 비슷해요. 이번에는 다온의 저장이 9번 중 4번 돌려보내졌어요(남의 몫 1번, 이유 개수 3번). 다온의 입력에는 기사 내용 대신 카드(주소, 제목, 태그)만 들어가고, 다온은 `get`으로 기사를 열면 문단마다 주소와 글을 함께 받아요(이번에는 `get` 17번).

**PyPI의 nextop 0.3.0으로 다시 확인 (2026-11-25)**: 새 가상 환경에 `pip install nextop==0.3.0`만 설치하고(플랫폼 소스 없이) 다시 돌렸습니다. 모델 호출 24번(한결 4번, 다온 20번), 약 102초에 메일이 갔습니다(전망: 삼성전자 보합, SK하이닉스 상승, NVIDIA 보합, SpaceX 보합). 이번에도 다온이 SpaceX의 뉴스 흐름에 중국어 글자(单独的)를 섞어 프로그램이 한 번 돌려보냈고, 고친 문장이 메일에 실렸습니다. 시험은 `19 passed`입니다. (그때는 다온이 인용문을 글자 그대로 옮겨 썼고, 프로그램이 한 글자씩 맞춰 봤습니다.)

## 만드는 데 걸리는 시간과 준비물

약 1시간. 이미 만들어진 프로젝트를 읽고 설정을 채워 돌려 보는 튜토리얼입니다.

- Python 3.11~3.13과 nextop 0.4.0: 아래 0단계의 `setup.bat`이 모두 설치합니다(직접 하려면 `pip install -r requirements.txt`). 이 튜토리얼은 nextop 0.4.0의 파일 서버(유형 폴더, 공통 도구, 문단 주소)로 쓰였습니다. 0.4.0이 PyPI에 올라가기 전에는 받은 휠 파일로 설치합니다: `setup.bat <휠 파일 경로>` `requirements.txt`가 nextop 0.4.0을 고정하고 `project.json`의 `"nextop": ">=0.4,<0.5"`가 이 프로젝트에 필요한 버전을 알립니다(다른 버전이면 `nextop check`가 어떻게 고치는지 알려 줍니다). 이미 다른 nextop이 깔려 있으면 `setup.bat`이 0.4.0으로 맞추고, 끝에 깔린 버전을 보여 줍니다.
- OpenAI API 키 (기본값입니다. 다른 OpenAI 호환 API도 됩니다. 아래 설정 참고)
- 웹 검색 키: [Tavily](https://tavily.com)에서 받은 `TAVILY_API_KEY` (한 번 실행에 검색 4번)
- 메일 보내는 계정의 SMTP 정보 (선택, 없으면 메일 단계만 실패하고 전망은 `outlooks/`에 남습니다)

모델과 검색 키가 없어도 3단계까지는 지금 바로 할 수 있습니다. 모델과 검색은 가짜로 바꿔서 시험합니다.

## 이 튜토리얼로 배우는 nextop 기능

- 일하는 직원 둘(한결, 다온)과 프로그램 블록(`plan`, `mail_outlook`)이 섞인 흐름 만들기
- 도구(tool)로 바깥에서 가져오기: 웹 검색은 파일 서버가 아니라 프로젝트 도구(`news_search`)가 하고, 직원은 고른 기사만 올립니다
- 파일 서버를 유형 폴더로 정의하기: `file_servers/news/file_server.json`(이름, 설명, 수명, 공유 선)과 `types/articles/type.json`(md 기사, 문단 쪼개기, 첫 문장 요약)
- 문단 쪼개기 부품(`parts/splitter/paragraphs.py`, nextop 예시 부품을 복사한 것): 기사를 문단으로 나눠 문단마다 주소(`fs://news/003#1.2`)를 줍니다
- 공통 파일 서버 도구 `upload`, `query`, `get`: 도구 이름에 파일 서버 이름이 없고, 주소가 무엇을 다룰지 고릅니다
- 오래 남는 파일 서버(`lifetime: project`)와 태그, 만료(`expire_after`): 기사는 7일 동안 남고, 올릴 때 회사 이름을 태그로 붙입니다
- 단계(steps)와 `for_each`: 다온은 먼저 회사별 뉴스를 훑고(scan), 그다음 회사마다 따로 대화합니다(judge). 한 대화에는 그 회사의 기사만 보입니다
- 문단 단위 근거: 다온은 문단 주소만 고르고, 문단의 원문은 프로그램이 메일에 옮깁니다. 주소가 본문 문단인지 모델 없이 확인합니다 (`checks.py`)
- 파일을 받는 함수(`FILES_IN`): 메일 함수가 기사와 그 문단 나무(`parts`)를 데이터로 받아 제목, 주소, 근거 문단을 읽습니다
- 같은 주소의 기사를 두 번 저장하지 않기(중복 제거)
- 모델과 검색 없이 하는 시험: 가짜 모델과 가짜 검색 서버로 흐름 전체 검증

## 단계별 따라 하기

PowerShell에서 이 폴더(`ko/tutorial_02_stock_news`)로 이동해 시작합니다.

### 0. 설치: setup.bat 실행

이 폴더의 `setup.bat`을 두 번 클릭하거나, PowerShell에서 `.\setup.bat`을 실행합니다. 처음 한 번 필요한 것을 모두 자동으로 설치합니다.

- Python 3.11~3.13을 찾습니다. 없으면 winget으로 Python 3.12를 설치합니다(설치 뒤 터미널을 새로 열고 `setup.bat`을 다시 실행)
- 이 폴더에 가상 환경 `.venv`를 만들고 `requirements.txt`(nextop, pytest 등)를 설치합니다. `setup.bat C:\받은폴더\nextop-0.4.0...whl`처럼 휠 파일 경로를 주면(또는 환경 변수 `NEXTOP_WHEEL`) nextop만 그 파일로 설치합니다. 휠 파일은 파이썬 버전에 맞아야 합니다(`cp311`이면 Python 3.11)
- `.env`가 없으면 `.env.example`을 복사해 만들고, 채워야 할 이름만 보여 줍니다. 키 값은 직접 `.env`에 적습니다
- 모델 없이 하는 시험을 돌리고, 모두 통과하면 마지막에 `Setup OK`가 나옵니다

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
project.json          프로젝트 설정 (LLM 연결)
stocks.json           회사 네 곳(이름, 종목 코드, 상장 여부, 검색어)과 검색 설정
workers/collector     한결: 뉴스 검색, 기사 고르기, 올리기
workers/analyst       다온: 회사별 방향과 이유 (근거 문단 검사 포함)
tools/news_search.py  웹 검색 도구 (Tavily). 새 기사만 파일로 저장해서 알려 줌
functions/plan.py     시작 블록: 내일이 며칠인지(주말이면 월요일)와 회사 목록
functions/mail_outlook.py   끝 블록: 메일(글자판 + HTML)을 만들어 보냄
functions/_news.py    설정, 검색, 메일 보내기 (도우미)
file_servers/news     기사 저장소 (7일 보관): file_server.json + types/articles/type.json
parts/splitter/paragraphs.py   문단 쪼개기 부품 (기사를 제목 아래 문단으로 나눔)
flows/daily_outlook.json    plan -> 한결 -> 다온 -> 메일
tests/                모델과 검색 없이 하는 시험
```

### 2. 모델 없이 프로그램 부분 시험하기

```powershell
python -m pytest -q tests
```

`19 passed`가 보이면 됩니다. 이 시험이 확인하는 것:
- 내일 날짜 계산(금요일과 토요일은 월요일), 주소 정리(`?utm_...`, 끝의 `/` 무시), 날짜 모양
- 검색 도구는 같은 주소를 두 번 저장하지 않고, 이미 저장된 기사와 SNS 글은 빼고, 검색이 실패하면 모델이 읽을 수 있는 오류를 돌려준다
- 이유의 주소가 본문 문단이 아니면(기사 전체, 여러 문단이 든 부분, 날짜·주소 줄, 없는 문단) 검사가 돌려보낸다. 기사 수에 맞지 않는 이유 개수와 한자 섞인 문장도 돌려보낸다
- 가짜 모델로 흐름 전체가 돈다: 회사 이름 태그로 올리고, 회사마다 따로 대화하며(다른 회사 기사가 안 보임), 기사 전체를 가리킨 이유는 한 번 거절된 뒤 문단으로 고쳐지고, 메일이 시험 서버에 도착한다(근거 문단은 프로그램이 기사에서 옮김)
- 메일에 투자 권유 아님 문구와 정리된 기사 주소가 들어 있다

### 3. 설정 채우기

```powershell
copy .env.example .env
```

(메모장으로 `.env`를 새로 만들 때는 "UTF-8"(BOM 없음)로 저장하세요.) 열어서 아래를 채웁니다. 자세한 내용은 "설정 채우기" 절을 보세요.

### 4. 흐름 검사

```powershell
nextop check
```

LLM 키를 채우기 전에는 이렇게 나옵니다.

```
[error] adapter llm.default: API key missing: set LLM_API_KEY in the environment or .env
```

모델 주소, 키, 이름을 채우면 `OK: stock news outlook (workers 2, tools 1, flows 1, file servers 1)`이 나옵니다.

### 5. 실행

```powershell
nextop run --flow daily_outlook
```

1~2분 뒤 `run <번호>: done`이 나옵니다. 처음에는 `MAIL_TEST_MODE=1`이라 메일이 `OFFICE_EMAIL` 한 곳으로만 갑니다.

### 6. 결과 확인

- `OFFICE_EMAIL`의 메일함: 위 예시 같은 메일(제목은 `[주가 전망·시험]`으로 시작)
- `outlooks/<날짜>.txt`와 `.html`: 같은 내용
- `file_servers/news/store/`: 저장된 기사(`items/`는 기록과 문단 나무, `files/`는 기사 본문). 올릴 때 회사 이름이 태그로 붙었습니다
- `runs/<실행 번호>/`: 흐름의 기록. 블록마다 `inputs.md`(모델이 받은 것), `calls.jsonl`(모델 호출), `tools.jsonl`(도구 호출과 검사가 돌려보낸 문장)이 있습니다. 검사가 돌려보낸 것은 `tools.jsonl`의 `save_output` 줄에 `refused_by: program`으로 남습니다

한 번 더 실행해 보세요. 이미 저장된 기사 주소는 도구가 알아서 빼고(`skipped_known`), 새 기사만 올라갑니다. 검색은 한 번 실행에 4번(회사마다 1번) 나갑니다.

### 7. 직접 바꿔 보기

- `stocks.json`의 회사를 바꾸거나 더하면(이름, 종목 코드, 상장 여부, 검색어) 한결과 다온이 그 회사를 다룹니다. 도구와 직원 설정은 그대로입니다
- 다온의 `mission.md`에서 판단 기준(오름과 보합을 가르는 기준)을 고쳐 보세요

## 어떻게 동작하나

```
plan (프로그램)  오늘 날짜, 내일(주말이면 월요일), 회사 목록
   |
   +--> 한결 (collector)  <-- 도구: news_search (Tavily, 회사마다 1번, 새 기사만 파일로 저장)
   |        |   진짜 기사만 골라 news 파일 서버에 올림 (태그: 회사 이름)
   |        v   coverage: 회사마다 ok / thin / none
   +--> 다온 (analyst)    <-- 한결이 올린 기사(news)의 카드, 도구 query와 get으로 문단을 읽음
   |        1단계 scan: 회사별 뉴스 큰 줄기
   |        2단계 judge (for_each): 회사 하나씩 따로 대화, 그 회사 기사만 보임
   |             방향 + 이유(근거 문단의 주소)
   |             checks.py: 주소가 읽을 수 있는 기사의 본문 문단인가, 이유 개수, 한자
   |        v   outlook
   +--> mail_outlook (프로그램)  기사에서 제목, 날짜, 주소, 근거 문단을 읽어 메일 작성 --> 보냄
```

- 한결은 회사 이름만 도구에 넘깁니다. 검색어는 `stocks.json`에 있고, 한결은 결과를 읽고 고르기만 합니다.
- 기사 파일은 도구가 씁니다(제목, 날짜, 주소, 본문). 한결은 파일을 고치지 않고 그대로 올립니다.
- 이미 저장된 주소는 도구가 걸러 냅니다. 도구는 저장소 폴더를 열지 않고 파일 서버 보기(`ctx["file_servers"]["news"].sources()`)로 파일 서버에 물어봅니다. 같은 기사가 검색마다 다른 주소 표기(`?utm_...`, 끝의 `/`)로 와도 한 주소로 봅니다.
- 기사는 올릴 때 문단으로 나뉘어 저장됩니다(`types/articles/type.json`의 `"splitter": "paragraphs"`). 기사 `fs://news/003`의 제목 아래 첫 문단이 `#1.1`(날짜와 주소 줄), 그다음 본문 문단이 `#1.2`, `#1.3` …입니다. 다온은 `query`에 기사 주소와 질문을 넣어 문단을 주소와 함께 받거나, `get`으로 기사와 문단을 엽니다.
- 다온은 이유마다 근거 문단의 주소만 씁니다. 문단의 글은 프로그램이 메일에 옮기므로, 모델이 글자를 바꿔 옮길 일이 없습니다. 주소가 본문 문단이 아니면 프로그램이 돌려보냅니다. 모델이 판단하는 검사는 쓰지 않았습니다.
- 메일의 기사 제목, 날짜, 주소, 근거 문단은 기사에서 프로그램이 읽습니다. 모델이 타자로 옮긴 주소나 문장은 쓰지 않습니다.
- 한 번의 실행에서 모델이 받는 기사는 회사 하나씩이라(`for_each`) 입력이 작고, 다른 회사 기사가 섞이지 않습니다.

## 설정 채우기

### LLM (`project.json`, `workers/*/worker.json`, `.env`)

기본값은 OpenAI API입니다. `project.json`의 `base_url`은 `https://api.openai.com/v1`, 각 `workers/*/worker.json`의 `"model"`은 `gpt-5.4-mini`입니다. `.env`의 `LLM_API_KEY=` 뒤에 OpenAI API 키를 넣으세요. 다른 OpenAI 호환 API도 됩니다. `base_url`과 모델 이름을 바꾸세요.

그다음 `nextop check`가 `OK`를 말하면 끝입니다.

### 웹 검색 (Tavily)

`.env`의 `TAVILY_API_KEY=` 뒤에 키를 넣습니다. 한 번 실행에 검색 4번이 나가니, 키의 남은 한도를 가끔 확인하세요. 검색 설정(최근 며칠, 회사당 결과 수, 뺄 사이트)은 `stocks.json`의 `search`에 있습니다.

### 메일 (SMTP)

`.env`의 `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`를 채웁니다. 포트 587은 STARTTLS, 465는 SSL입니다(그 밖의 포트는 암호화 없이 보내므로 내 컴퓨터의 시험 서버에만 쓰세요).

- `MAIL_TEST_MODE=1`(기본): 메일이 `OFFICE_EMAIL` 한 곳으로만 가고 제목이 `[주가 전망·시험]`으로 시작합니다. 처음에는 이대로 두세요.
- 실제 운영: `MAIL_TEST_MODE=0`으로 바꾸고 `MAIL_TO=a@example.com,b@example.com`(쉼표로 여러 명)을 채웁니다. 제목은 `[주가 전망]`으로 시작합니다.

비밀번호와 키는 `.env`에만 쓰고, `.env`는 올리거나 공유하지 마세요(`.gitignore`에 들어 있습니다).

### 회사 (`stocks.json`)

- `listed`: `false`이면 메일이 "비상장 회사라 주가가 없습니다"라고 말하고 방향을 "호재 중심 / 섞임·잠잠 / 악재 중심"으로 씁니다. SpaceX는 2026년 6월 상장해 `listed: true`, `SPCX (NASDAQ)`입니다. 상장하지 않은 회사(예: 다른 비상장 기업)를 넣을 때 `listed: false`를 씁니다.
- `search.exclude_domains`: 뉴스가 아닌 사이트(소셜 미디어 등)는 검색에서 빼고, 검색 도구도 한 번 더 걸러요. `tavily.com`은 검색이 가끔 돌려주는 회사 소개 페이지(기사가 아님)를 빼려고 넣었어요.
- 내일 날짜는 주말만 건너뜁니다. 공휴일은 모릅니다.

## 다음에 해 볼 것

- 매일 같은 시각에 받기: Windows 작업 스케줄러에 `nextop run --flow daily_outlook`을 매일 장 마감 뒤 시각으로 등록
- 회사를 더 넣기(`stocks.json`): 같은 흐름이 그대로 돌아갑니다
- 어제 전망과 오늘 결과 맞춰 보기: 어제의 전망(`outlooks/`)과 오늘의 실제 등락을 비교하는 별도 흐름
- 기사 본문 전체 읽기: 검색 도구에 본문 가져오기를 더하면 근거로 쓸 문단이 늘어납니다(이용 약관 확인)
- 받는 사람마다 관심 회사만 보내기: 메일 함수가 `MAIL_TO`별로 나누어 보내기

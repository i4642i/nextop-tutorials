# nextop 튜토리얼

[nextop](https://pypi.org/project/nextop/)으로 일하는 직원(agentic worker)을 만드는 단계별 튜토리얼입니다. 튜토리얼마다 완성된 프로젝트 폴더가 하나씩 있습니다. 읽고, `.env`와 모델 설정을 채우고, 모델 없이 시험을 돌린 뒤 실제로 실행해 봅니다.

English: [README.md](README.md)

## 언어판

| 언어판 | 폴더 | nextop | 직원, 메일, 결과의 언어 |
|---|---|---|---|
| 한국어 | [`ko/`](ko/) | 0.4.0 (`pip install nextop==0.4.0`) | 한국어 (`"language": "ko"`) |
| 영어 | [`en/`](en/) | 0.4.0 | 영어 (`"language": "en"`) |
| 일본어 | [`ja/`](ja/) | 0.4.0 | 일본어 (`"language": "ja"`) |

언어판은 글자만 옮긴 번역이 아닙니다. 나라에 따라 달라지는 튜토리얼은 그 나라에 맞췄습니다.

| 번호 | 튜토리얼 | 한국어판 | 영어판 | 일본어판 |
|---|---|---|---|---|
| 1 | 헤어샵 예약 상담 챗봇 | [한국 미용실](ko/tutorial_01_hair_salon/) (원, 한국 휴대폰 번호) | [미국 미용실](en/tutorial_01_hair_salon/) (달러, 미국 전화번호, 미국 디자이너) | [일본 미용실](ja/tutorial_01_hair_salon/) (엔, 일본 휴대폰 번호) |
| 2 | 매일 아침 주가 전망 메일 | [한국·미국 주식](ko/tutorial_02_stock_news/): 삼성전자, SK하이닉스, NVIDIA, SpaceX | [미국 주식](en/tutorial_02_stock_news/): NVIDIA, Apple, Micron, SpaceX | [미국 주식](ja/tutorial_02_stock_news/): NVIDIA, Apple, Micron, SpaceX |
| 3 | PDF를 A4 한 장으로 요약 | [한국어 요약](ko/tutorial_03_pdf_summary/) | [영어 요약](en/tutorial_03_pdf_summary/) | [일본어 요약](ja/tutorial_03_pdf_summary/) |
| 4 | 잘 알려진 MCP 서버로 만드는 링크 요약 | [한국어 보고서](ko/tutorial_04_mcp_link_summary/) | [영어 보고서](en/tutorial_04_mcp_link_summary/) | [일본어 보고서](ja/tutorial_04_mcp_link_summary/) |
| 5 | PDF로 테마가 입혀진 PPT 만들기 | [한국어 슬라이드](ko/tutorial_05_pdf_to_ppt/) | [영어 슬라이드](en/tutorial_05_pdf_to_ppt/) | [일본어 슬라이드](ja/tutorial_05_pdf_to_ppt/) |

## 준비물

- Windows: 튜토리얼 폴더의 `setup.bat`을 먼저 실행합니다. Python 3.11~3.13을 찾고(없으면 winget으로 설치), `.venv`를 만들어 그 폴더의 `requirements.txt`(nextop 0.4.0과 그 튜토리얼이 쓰는 도구)를 설치하고, `.env.example`로 `.env`를 만든 뒤 모델 없이 하는 시험을 돌립니다
- 직접 설치(모든 OS): Python 3.11~3.13과 튜토리얼 폴더에서 `pip install -r requirements.txt`
- 튜토리얼 4는 Node.js(`npx`)도 필요합니다. `setup.bat`은 설치하지 않습니다: `winget install -e --id OpenJS.NodeJS.LTS`
- LLM API 키. 기본값은 OpenAI(`https://api.openai.com/v1`, 모델 `gpt-5.4-mini`)입니다. 키는 `.env`의 `LLM_API_KEY`에 넣으세요. OpenAI 호환 API면 어느 것이든 됩니다. `project.json`의 `base_url`과 `workers/*/worker.json`의 모델 이름을 바꾸세요
- 선택: 메일을 보낼 SMTP 계정

튜토리얼 1부터 시작하세요. 폴더마다 `README.md`(따라 하기)와 `PLATFORM_ISSUES.md`(만들면서 찾은 nextop 문제와 재현 방법)가 있습니다.

## 라이선스

이 저장소의 튜토리얼 파일은 [MIT 라이선스](LICENSE)입니다. 상업적 용도를 포함해 자유롭게 복사하고 고쳐 쓸 수 있습니다. 튜토리얼이 실행되는 nextop 플랫폼은 별도 패키지이며 자체 라이선스를 따릅니다([PyPI의 nextop](https://pypi.org/project/nextop/) 참고).

# dsh-locale-pack

<p align="right"><a href="README.md">English</a> | <strong>한국어</strong></p>

<p align="center"><img src="docs/banner.jpg" alt="DeepSeek Harness 다국어 팩: 29개 언어" width="100%"></p>

DeepSeek Harness 데스크톱 앱을 위한 로케일 팩입니다. 언어 선택 목록에 29개 언어를 등록하고 각 언어의 사전을 함께 싣습니다. 번역이 아직 없는 문구는 영어로 표시되므로 화면을 읽을 수 있는 상태가 유지됩니다. DeepSeek Harness가 기본으로 싣는 영어와 간체 중국어까지 합치면 화면에서 고를 수 있는 언어는 31개입니다.

## 만든 이유

DeepSeek Harness는 코딩 도구입니다. 할 일을 넘기면 에이전트가 파일을 읽고 고치고 터미널 명령을 실행합니다. 화면은 대화, 설정, 플러그인 관리, 하위 에이전트, 작업 기록, 승인, 음성 입력, 예약 작업으로 구성됩니다.

이 화면은 영어와 간체 중국어로만 제공되었습니다. 다른 언어를 쓰는 개발자는 모든 낱말을 두 번째 언어로 읽어야 했습니다. 이 프로젝트는 그 자리를 채웁니다. 넓이를 우선해 언어 수를 늘렸습니다. 선택 목록에 언어가 뜨고 주요 화면을 읽을 수 있으면 그 언어는 쓸 수 있는 상태입니다.

## 지원 언어

| 언어 | 코드 | 언어 | 코드 |
|---|---|---|---|
| 한국어 | `ko` | Polski | `pl` |
| 日本語 | `ja` | Русский | `ru` |
| 繁體中文 (台灣) | `zh-tw` | Українська | `uk` |
| 繁體中文 (香港) | `zh-hk` | Svenska | `sv` |
| Deutsch | `de` | Türkçe | `tr` |
| Français | `fr` | Bahasa Indonesia | `id` |
| Español | `es` | Tiếng Việt | `vi` |
| Português (Brasil) | `pt-br` | ไทย | `th` |
| Italiano | `it` | हिन्दी | `hi` |
| Nederlands | `nl` | العربية | `ar` |
| Filipino | `tl` | Română | `ro` |
| বাংলা | `bn` | اردو | `ur` |
| עברית | `he` | فارسی | `fa` |
| Português (Portugal) | `pt` | Kiswahili | `sw` |
| Yorùbá | `yo` | | |

29개 언어 × 2,528키 = 73,312개 문구입니다. 사전은 DeepSeek Harness `0.2.0-rc.2` 기준으로 맞췄습니다.

## 설치

DeepSeek Harness 데스크톱 앱이 먼저 설치되어 있어야 합니다. 그다음 저장소를 내려받아 플러그인 링크로 등록합니다.

macOS·Linux (bash):

```bash
# 1) 저장소 내려받기
git clone https://github.com/sayho-pm/dsh-locale-pack.git
cd dsh-locale-pack

# 2) 폴더를 데스크톱 프로필에 등록
dsh plugin --profile desktop add link:$(pwd)
```

Windows (PowerShell):

```powershell
# 1) 저장소 내려받기
git clone https://github.com/sayho-pm/dsh-locale-pack.git
cd dsh-locale-pack

# 2) 폴더를 데스크톱 프로필에 등록
dsh plugin --profile desktop add link:(Get-Location).Path
```

이후 **설정 → 언어**에서 쓸 언어를 고르면 됩니다.

### AI 어시스턴트로 설치하기

개발 환경이 없으면 AI 어시스턴트가 설치를 대신 진행합니다. 어시스턴트를 열고 아래 문장을 붙여넣습니다.

```
이 깃헙 저장소를 설치해줘: https://github.com/sayho-pm/dsh-locale-pack
설치 과정에서 내가 직접 입력해야 하는 부분은 **** 로 표시해주고,
어디에 입력해야 하는지 알려줘. 나머지는 네가 알아서 진행해줘.
```

어시스턴트가 명령을 실행하고, 직접 입력해야 하는 자리에서만 멈춥니다.

## 구조

```text
locale/<언어>/*.json   언어별 사전 원본 — 여기서 작업
locale/_policy/       영어로 두는 용어 목록
lib/client.js         생성된 번들 (사전에서 만듦)
tools/build-client.mjs  사전 → lib/client.js 생성
tools/smoke.mjs         스모크 테스트
tools/check-keep.mjs    번역 품질 점검
tools/translate_worker.py  번역 워커(대화 세션과 분리되어 동작)
tools/clean-romanized.py   로마자 표기 오류 정리
tools/en.baseline.json  영문 기준선 (DeepSeek Harness 0.2.0-rc.2)
```

## 문구를 고치는 방법

```bash
node tools/build-client.mjs   # lib/client.js 재생성
node tools/smoke.mjs          # 자가 점검 (사전 로드·폴백·멱등성)
node tools/check-keep.mjs     # 번역 품질 점검
```

`{name}` 같은 `{…}` 표시는 반드시 그대로 유지해야 합니다. 순서나 표기가 바뀌면 화면에서 문장이 깨집니다.

### 필요한 언어만 묶어 만들기

전체를 설치하는 것이 기본이며, 설치한 뒤 언어를 바꾸는 일은 설정 화면에서 끝납니다. 전체 번들이 부담스러운 경우 필요한 언어만 묶어 만들 수 있습니다.

```bash
node tools/build-client.mjs --langs ko,ja   # 한국어와 일본어만
```

언어 두 개를 묶으면 4.2MB가 아니라 약 320KB가 됩니다. 위 표의 언어 코드를 쉼표로 이어 넣으면 됩니다. 옵션을 빼면 전체 언어를 다시 묶습니다.

## 번역 품질 점검

`tools/check-keep.mjs`가 각 언어의 값을 영문 기준선과 대조해 다섯 가지를 확인합니다.

1. `{name}` 같은 표시가 원문과 같은 개수로 있는가
2. 제품명과 프로토콜명(DeepSeek Harness, MCP, JSON, OpenAI Responses 등)이 그대로 남아 있는가
3. 한자와 가나를 쓰지 않는 언어에 한자가 섞이지 않았는가
4. 한국어 문장에 줄표가 들어가지 않았는가
5. 값이 비어 있지 않은가, 기준선에 없는 키가 섞이지 않았는가

영어로 두기로 한 용어는 `locale/_policy/keep-english.json`에 모아 두었습니다. 새 용어를 영어로 유지하려면 이 파일에 추가합니다.

## 번역을 다시 돌리는 방법

번역은 대화 세션과 분리된 별도 프로세스에서 진행합니다. 세션 모델이나 대화 기록이 번역 요청에 실리지 않으며, 번역 대상인 영문 문구만 나갑니다.

```bash
python3 tools/translate_worker.py --langs ja,de      # 지정 언어만
python3 tools/translate_worker.py --all              # 전체
```

요청은 네 단계 모델을 순서대로 거칩니다. 첫 모델이 실패하면 같은 성격의 다른 경로로, 이어서 이전 버전으로, 마지막에는 학습에 쓰이지 않는 모델로 진행합니다. 어느 모델이 처리했는지는 `번역_로그`의 기록에서 확인할 수 있습니다.

## 사용자 유의사항

- 아랍어·우르두어·히브리어·페르시아어는 표기 방향이 오른쪽에서 왼쪽입니다. 사전은 준비되어 있으며 화면 레이아웃은 DeepSeek Harness가 처리합니다
- 메뉴 표시줄, 마우스 오른쪽 메뉴, 업데이트 확인 창은 데스크톱 프로그램 부분이라 이 플러그인이 바꾸지 못합니다
- DeepSeek Harness가 새 버전을 내면 문구가 늘어납니다. 늘어난 문구는 번역 전까지 영어로 표시됩니다
- 한국어는 사람이 확인했고, 나머지 언어는 기계 번역 결과입니다. 표현을 다듬으려면 해당 언어 사전 파일에서 고치면 됩니다

## 기여

추가 언어 요청을 받습니다. 이 저장소에 이슈로 언어 이름을 남겨 주시면 다음 작업에 포함합니다. 이미 있는 언어의 표현을 고치는 일은 `locale/<언어>/` 아래 사전 파일에서 바로 고치고 풀 리퀘스트로 보내 주시면 됩니다.

## 라이선스

MIT

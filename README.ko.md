# dsh-locale-pack

<p align="right"><a href="README.md">English</a> | <strong>한국어</strong> | <a href="README.zh-TW.md">繁體中文</a> | <a href="README.id.md">Bahasa Indonesia</a> | <a href="README.vi.md">Tiếng Việt</a> | <a href="README.tr.md">Türkçe</a></p>

<p align="center"><img src="docs/pack-overview.png" alt="dsh-locale-pack 소개: 추가한 언어 23개, 번역 문구 102,767개, DeepSeek Harness 0.2.2-rc.2, 지원 언어 목록과 git clone 설치 명령" width="100%"></p>

DeepSeek Harness 데스크톱 앱과 브라우저 웹판을 함께 지원하는 로케일 팩입니다. 언어 선택 목록에 사전 23개와 번역 문구 102,767개를 얹습니다. 23개는 모두 DeepSeek Harness가 제공하지 않는 언어입니다. 아직 번역되지 않은 문구는 영어로 보여 화면이 읽히도록 유지합니다. 기본 제공인 영어와 간체 중국어까지 합치면 설치 후 선택할 수 있는 언어는 25개가 됩니다. DeepSeek Harness 최신 버전에 맞게 사전을 계속 갱신합니다. 커뮤니티 목록인 [awesome-deepseek-harness](https://github.com/0xsline/awesome-deepseek-harness)에도 올라 있습니다.

## 만든 이유

DeepSeek Harness는 코딩 도구입니다. 할 일을 넘기면 에이전트가 파일을 읽고 고치고 터미널 명령을 실행합니다. 화면은 대화, 설정, 플러그인 관리, 하위 에이전트, 작업 기록, 승인, 음성 입력, 예약 작업으로 이루어져 있습니다.

DeepSeek Harness는 최초에는 영어와 간체 중국어로만 제공되었는데, 다른 언어 사용자는 모든 UI를 주로 영어로 읽어야 했을 것입니다. 이 프로젝트는 전 세계 DeepSeek Harness 사용자의 사용 편의를 위해 언어를 최대한 넓게 커버하는 데 초점을 맞추었습니다.

현재 최신 버전이 지원하는 공식 배포는 8개 언어이지만, 본 플러그인이 다루는 한국어, 튀르키예어, 베트남어, 인도네시아어를 기준으로 이 언어들을 직접 지원하기 시작하면, 업데이트를 늦추거나 플러그인의 업데이트를 하지 않고 종료할 생각을 가지고 있습니다.

## 지원 언어

| 언어 | 코드 | 언어 | 코드 |
|---|---|---|---|
| 한국어 | `ko` | Polski | `pl` |
| 繁體中文 (台灣) | `zh-tw` | Українська | `uk` |
| 繁體中文 (香港) | `zh-hk` | Svenska | `sv` |
| Türkçe | `tr` | Bahasa Indonesia | `id` |
| Tiếng Việt | `vi` | Português (Brasil) | `pt-br` |
| ไทย | `th` | Italiano | `it` |
| हिन्दी | `hi` | Nederlands | `nl` |
| العربية | `ar` | Filipino | `tl` |
| Română | `ro` | বাংলা | `bn` |
| اردو | `ur` | עברית | `he` |
| فارسی | `fa` | Kiswahili | `sw` |
| Yorùbá | `yo` |  |  |

언어 23개, 키 4,468개, 문구 102,767개가 들어 있습니다. DeepSeek Harness가 새 버전을 낼 때마다 문구를 다시 맞추고 있고, 지금은 `0.2.2-rc.2`까지 대응합니다.

## 설치

먼저 DeepSeek Harness 데스크톱 앱이 설치되어 있어야 합니다. 그다음 저장소를 내려받고 플러그인 링크로 데스크톱 프로필에 등록합니다.

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

등록이 끝나면 **설정 → 언어**에서 사용할 언어를 고르면 됩니다.

### 웹판(브라우저)에 등록

데스크톱 앱 대신 브라우저에서 여는 웹판도 같은 방식으로 등록합니다. 프로필 이름만 `web`으로 바꾸면 됩니다.

```bash
# 웹 프로필에 등록한 뒤 서버를 띄운다
dsh plugin --profile web add link:$(pwd)
dsh web
```

`dsh web`이 출력하는 주소를 브라우저에서 열고 **설정 → 언어**에서 언어를 고르면 됩니다. 웹 프로필은 처음 등록할 때 자동으로 만들어집니다.

### AI 어시스턴트로 설치하기

개발 환경이 없으면 AI 어시스턴트가 설치를 도와줍니다. 어시스턴트를 열고 아래 문장을 붙여넣습니다.

```
이 깃헙 저장소를 설치해줘: https://github.com/sayho-pm/dsh-locale-pack
설치 과정에서 내가 직접 입력해야 하는 부분은 **** 로 표시해주고,
어디에 입력해야 하는지 알려줘. 나머지는 네가 알아서 진행해줘.
```

어시스턴트가 명령을 실행하고, 직접 입력해야 하는 자리에서만 멈춥니다.

## 구조

파일 구성은 다음과 같습니다.

```text
locale/<언어>/*.json   언어별 사전 원본 — 여기서 작업
locale/<언어>.json     언어별 플러그인 표시 문구(제목/설명)
locale/_policy/       영어로 두는 용어 목록
lib/client.js              생성된 번들(사전에서 만들어짐)
styles/locale-fonts.css    언어별 글꼴 보정(빌드 시 번들에 인라인됨)
tools/build-client.mjs     사전 → lib/client.js
tools/smoke.mjs         스모크 테스트
tools/check-keep.mjs    번역 품질 점검
tools/translate_worker.py  번역 워커(대화 세션과 분리되어 동작)
tools/clean-romanized.py   로마자 표기 오류 정리
tools/en.baseline.json  영문 기준선 (DeepSeek Harness 0.2.2-rc.1)
```

## 문구를 고치는 방법

여기서는 다음 순서로 명령을 실행하면 됩니다.

```bash
node tools/build-client.mjs   # lib/client.js 재생성
node tools/smoke.mjs          # 자가 점검 (사전 로드·폴백·멱등성)
node tools/check-keep.mjs     # 번역 품질 점검
```

`{name}` 같은 `{…}` 표기는 반드시 그대로 유지해야 합니다. 순서나 표기가 바뀌면 화면에서 문장이 깨집니다.

### 필요한 언어만 묶어 만들기

전체를 설치하는 것이 기본이며, 설치한 뒤 언어를 바꾸는 일은 설정 화면에서 끝납니다. 전체 번들이 부담스러운 경우 필요한 언어만 묶어 만들 수 있습니다.

```bash
node tools/build-client.mjs --langs ko,ja   # 한국어와 일본어만
```

언어 두 개를 묶으면 8.3MB가 아니라 약 575KB가 됩니다. 위 표의 언어 코드를 쉼표로 이어 넣으면 됩니다. 옵션을 빼면 전체 언어를 다시 묶습니다.

## 사용자 유의사항

- 아랍어·우르두어·히브리어·페르시아어는 표기 방향이 오른쪽에서 왼쪽입니다. 사전은 준비되어 있으며 화면 레이아웃은 DeepSeek Harness가 처리합니다
- 메뉴 표시줄, 마우스 오른쪽 메뉴, 업데이트 확인 창은 데스크톱 프로그램 부분이라 이 플러그인이 바꾸지 못합니다
- DeepSeek Harness가 새 버전을 내면 문구가 늘어납니다. 늘어난 문구는 번역 전까지 영어로 표시됩니다
- 한국어는 사람이 확인했고, 나머지 언어는 기계 번역 결과입니다. 표현을 다듬으려면 해당 언어 사전 파일에서 고치면 됩니다
- 일본어와 중국어 번체는 각자의 글자 모양을 유지합니다. 하니스 기본 글꼴 목록이 중국어 간체 글꼴을 다른 CJK 글꼴보다 앞에 두어, 규격끼리 공유하는 한자가 간체 모양으로 그려지던 부분을 이 팩이 `ja`·`zh-tw`·`zh-hk` 로케일에 한해 바로잡습니다

## 기여

추가 언어 요청은 이 저장소에 이슈로 언어 이름을 남기면 다음 작업에 포함합니다. 이미 있는 언어의 표현을 고치려면 `locale/<언어>/` 아래 사전 파일을 수정해 풀 리퀘스트로 보내 주시면 됩니다.

번역 파이프라인을 돌리는 관리자는 [MAINTAINING.md](MAINTAINING.md)에서 명령을 확인할 수 있습니다.

## 라이선스

MIT

<!-- pack-facts: version=0.9.0 dsh=0.2.2-rc.2 languages=23 keys=4,468 entries=102,767 bundle="7.4 MB" -->

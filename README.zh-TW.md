# dsh-locale-pack

<p align="right"><strong>English</strong> | <a href="README.ko.md">한국어</a> | <a href="README.zh-TW.md">繁體中文</a> | <a href="README.id.md">Bahasa Indonesia</a> | <a href="README.vi.md">Tiếng Việt</a> | <a href="README.tr.md">Türkçe</a></p>

<p align="center"><img src="docs/pack-overview.png" alt="dsh-locale-pack overview: 23 language dictionaries, 102,767 translated entries, DeepSeek Harness 0.2.2-rc.2, the supported languages, and the git clone install command" width="100%"></p>

一個為 DeepSeek Harness 打造的語系包，同時涵蓋桌面應用程式和瀏覽器版本。它會在語言選擇器中註冊 23 份字典，每一份都對應一種 DeepSeek Harness 未提供的語言。尚未翻譯的字串會退回顯示英文，因此在涵蓋範圍逐步擴大期間，畫面依然保持可讀。加上內建的英文與簡體中文，安裝後可選擇 25 種語言。此語系包會與最新版 DeepSeek Harness 保持同步更新。它也被收錄於 [awesome-deepseek-harness](https://github.com/0xsline/awesome-deepseek-harness)，也就是 DSH 外掛與工具的社群索引。

## 為什麼存在

DeepSeek Harness 是一款程式設計工具：您指派一項任務給它，代理人便會讀取檔案、編輯檔案並執行終端機指令。其桌面介面以聊天、設定、外掛程式管理、子代理人、任務歷史記錄、核准提示、語音輸入及排程工作為核心。

That interface was available in English and Simplified Chinese. Developers who prefer to work in another language had to read every label in a second language. This project fills that gap by adding the dictionaries, and by keeping the number of languages wide rather than deep: a language is usable once the picker offers it and the common screens are readable.

DeepSeek Harness 最初只提供英文與簡體中文，到了 0.2.2-rc.1 已提供八種語言。若它開始提供韓文、土耳其文、越南文、印尼文等本語言包涵蓋的語言，本語言包會放慢或停止該語言的更新，不另外保留一份相同的字典。

## 支援的語言

| Language | Code | Language | Code |
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

23 種語言，每種 4,468 個鍵 — 總計 102,767 個已翻譯條目。字典會在 DeepSeek Harness 發布新版本時更新，目前涵蓋最新版本 `0.2.2-rc.2`。

## 安裝

必須先安裝 DeepSeek Harness 桌面應用程式。然後複製儲存庫並將其註冊為外掛連結。

macOS 和 Linux (bash)：

```bash
# 1) Get the sources
git clone https://github.com/sayho-pm/dsh-locale-pack.git
cd dsh-locale-pack

# 2) Register the folder with the desktop profile
dsh plugin --profile desktop add link:$(pwd)
```

Windows (PowerShell)：

```powershell
# 1) Get the sources
git clone https://github.com/sayho-pm/dsh-locale-pack.git
cd dsh-locale-pack

# 2) Register the folder with the desktop profile
dsh plugin --profile desktop add link:(Get-Location).Path
```

然後開啟 **設定 → 語言** 並選擇您想要的語言。

### 在網頁版註冊

瀏覽器版本（`web` 設定檔）的註冊方式相同。只有設定檔名稱不同。

```bash
# register in the web profile, then start the server
dsh plugin --profile web add link:$(pwd)
dsh web
```

開啟 `dsh web` 所顯示的網址，然後在 **設定 → 語言** 下選擇語言。網頁設定檔會在首次註冊時自動建立。

### 使用 AI 助理安裝

如果您沒有開發環境，AI 助理可以幫您完成設定。請開啟助理並貼上以下內容：

```
Install this GitHub repository: https://github.com/sayho-pm/dsh-locale-pack
Wherever I have to type something myself, such as a token or a path,
mark it with **** and tell me exactly where it goes. Handle the rest.
```

The assistant runs the commands and stops only at the points that need your input.

## 儲存庫結構

```text
locale/<language>/*.json   Dictionary sources — edit here
locale/<language>.json     Plugin display text per language (title/description)
locale/_policy/            Terms kept in English
lib/client.js              Generated bundle (from the dictionaries)
styles/locale-fonts.css    Locale-scoped font corrections (inlined at build)
tools/build-client.mjs     Dictionaries → lib/client.js
tools/smoke.mjs            Smoke test
tools/check-keep.mjs       Translation quality check
tools/translate_worker.py  Translation worker (runs outside the chat session)
tools/clean-romanized.py   Fixes transliteration slips
tools/en.baseline.json     English baseline (DeepSeek Harness 0.2.2-rc.1)
```

## 編輯字串

```bash
node tools/build-client.mjs   # rebuild lib/client.js
node tools/smoke.mjs          # self-check: loading, fallback, idempotence
node tools/check-keep.mjs     # translation quality check
```

Placeholders such as `{name}` must be kept exactly as they are. If the order or the spelling changes, the sentence breaks at runtime.

### 僅打包您需要的語言

安裝完整套件是預設選項，之後若要切換語言，只需在設定畫面中操作即可。若完整套件超出您的需求，可改為建立子集：

```bash
node tools/build-client.mjs --langs ko,ja   # Korean and Japanese only
```

雙語言組合包的大小約為 575 KB，而非 8.3 MB。此旗標接受上表中語言代碼的任意逗號分隔清單。若省略此旗標，則會重新建置所有語言。

## 使用者注意事項

- 阿拉伯語、烏都語、希伯來語和波斯語由右至左書寫。字典已備妥；畫面版面配置由 DeepSeek Harness 自行處理。
- 選單列、右鍵選單和更新對話方塊屬於桌面殼層，因此此語言包不會變更它們。
- 當 DeepSeek Harness 發布新版本時，新增的字串在翻譯完成前會以英文顯示。
- 韓文由人工審校。其他語言來自機器翻譯，各語言的字典檔即為調整用詞之處。
- 日文和繁體中文保留各自的字形。Harness 的字型堆疊將簡體中文字型列在其他 CJK 字型之前，因此共用的漢字若未修正，將會以簡體字形顯示。此語言包將修正後的堆疊套用至 `ja`、`zh-tw` 和 `zh-hk`，並會跟隨語言選擇器。

## 貢獻

歡迎請求新增其他語言。請在此儲存庫中開啟一個 issue 並註明語言名稱，將會在下一輪中處理。現有語言的修正請直接修改 `locale/<language>/` 下該語言的字典檔，最簡單的方式是提交 pull request。

負責執行翻譯流程的維護者可在 [MAINTAINING.md](MAINTAINING.md) 找到指令。

## 授權

MIT

<!-- pack-facts: version=0.9.0 dsh=0.2.2-rc.2 languages=23 keys=4,468 entries=102,767 bundle="7.4 MB" -->

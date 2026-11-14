# dsh-locale-pack

<p align="right"><a href="README.md">English</a> | <a href="README.ko.md">한국어</a> | <a href="README.zh-TW.md">繁體中文</a> | <a href="README.id.md">Bahasa Indonesia</a> | <strong>Tiếng Việt</strong> | <a href="README.tr.md">Türkçe</a></p>

<p align="center"><img src="docs/pack-overview.png" alt="dsh-locale-pack overview: 23 language dictionaries, 102,767 translated entries, DeepSeek Harness 0.2.2-rc.2, the supported languages, and the git clone install command" width="100%"></p>

Gói ngôn ngữ cho DeepSeek Harness, bao gồm cả ứng dụng máy tính và phiên bản trình duyệt. Nó đăng ký 23 từ điển trong trình chọn ngôn ngữ, mỗi từ điển cho một ngôn ngữ mà DeepSeek Harness chưa cung cấp. Các chuỗi chưa được dịch sẽ dùng tiếng Anh, vì vậy màn hình vẫn dễ đọc trong khi độ phủ bản dịch tiếp tục tăng. Cùng với tiếng Anh và tiếng Trung Giản thể có sẵn, sau khi cài đặt có 25 ngôn ngữ để chọn. Gói này luôn được cập nhật theo bản phát hành DeepSeek Harness mới nhất. Nó cũng được liệt kê trong [awesome-deepseek-harness](https://github.com/0xsline/awesome-deepseek-harness), chỉ mục cộng đồng gồm các plug-in và công cụ DSH.

## Tại sao điều này tồn tại

DeepSeek Harness là một công cụ lập trình: bạn giao cho nó một nhiệm vụ và agent đọc tệp, chỉnh sửa chúng và chạy các lệnh terminal. Giao diện desktop của nó được xây dựng xung quanh chat, cài đặt, quản lý plugin, sub-agent, lịch sử nhiệm vụ, lời nhắc phê duyệt, nhập giọng nói và các công việc đã lên lịch.

Giao diện đó có sẵn bằng tiếng Anh và tiếng Trung Giản thể. Các nhà phát triển muốn làm việc bằng ngôn ngữ khác phải đọc mọi nhãn bằng ngôn ngữ thứ hai. Dự án này lấp đầy khoảng trống đó bằng cách bổ sung các từ điển, và bằng cách giữ số lượng ngôn ngữ rộng thay vì sâu: một ngôn ngữ có thể dùng được khi bộ chọn cung cấp nó và các màn hình phổ biến có thể đọc được.

DeepSeek Harness ban đầu chỉ có tiếng Anh và tiếng Trung Giản thể, đến 0.2.2-rc.1 đã có tám ngôn ngữ. Nếu sau này nó cung cấp tiếng Hàn, tiếng Thổ Nhĩ Kỳ, tiếng Việt, tiếng Indonesia hoặc ngôn ngữ khác mà gói này đang bao phủ, gói này sẽ chậm lại hoặc dừng cập nhật ngôn ngữ đó thay vì giữ thêm một bản sao.

## Các ngôn ngữ được hỗ trợ

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

23 ngôn ngữ, 4,468 khóa mỗi ngôn ngữ — 102,767 mục đã dịch tổng cộng. Các từ điển được làm mới mỗi khi DeepSeek Harness phát hành bản mới; hiện theo sát `0.2.2-rc.2`.

## Cài đặt

Ứng dụng DeepSeek Harness dành cho máy tính để bàn phải được cài đặt trước. Sau đó nhân bản kho lưu trữ và đăng ký nó dưới dạng liên kết plugin.

macOS và Linux (bash):

```bash
# 1) Get the sources
git clone https://github.com/sayho-pm/dsh-locale-pack.git
cd dsh-locale-pack

# 2) Register the folder with the desktop profile
dsh plugin --profile desktop add link:$(pwd)
```

Windows (PowerShell):

```powershell
# 1) Get the sources
git clone https://github.com/sayho-pm/dsh-locale-pack.git
cd dsh-locale-pack

# 2) Register the folder with the desktop profile
dsh plugin --profile desktop add link:(Get-Location).Path
```

Sau đó mở **Cài đặt → Ngôn ngữ** và chọn ngôn ngữ bạn muốn.

### Đăng ký trong phiên bản web

Phiên bản trình duyệt (hồ sơ `web`) đăng ký theo cùng cách. Chỉ tên hồ sơ thay đổi.

```bash
# register in the web profile, then start the server
dsh plugin --profile web add link:$(pwd)
dsh web
```

Mở địa chỉ do `dsh web` in ra, sau đó chọn ngôn ngữ trong **Cài đặt → Ngôn ngữ**. Hồ sơ web được tạo tự động khi đăng ký lần đầu.

### Cài đặt với trợ lý AI

Nếu bạn không có môi trường phát triển, trợ lý AI có thể thiết lập giúp bạn. Mở trợ lý và dán nội dung này:

```
Install this GitHub repository: https://github.com/sayho-pm/dsh-locale-pack
Wherever I have to type something myself, such as a token or a path,
mark it with **** and tell me exactly where it goes. Handle the rest.
```

Trợ lý chạy các lệnh và chỉ dừng lại ở những điểm cần bạn nhập.

## Bố cục kho lưu trữ

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

## Chỉnh sửa chuỗi

```bash
node tools/build-client.mjs   # rebuild lib/client.js
node tools/smoke.mjs          # self-check: loading, fallback, idempotence
node tools/check-keep.mjs     # translation quality check
```

Các placeholder như `{name}` phải được giữ nguyên chính xác như vậy. Nếu thứ tự hoặc chính tả thay đổi, câu sẽ bị lỗi khi chạy.

### Chỉ đóng gói những ngôn ngữ bạn cần

Cài đặt toàn bộ gói là mặc định, và việc chuyển đổi ngôn ngữ sau đó là vấn đề của màn hình cài đặt. Khi gói đầy đủ nhiều hơn mức bạn muốn, hãy tạo một tập hợp con thay thế:

```bash
node tools/build-client.mjs --langs ko,ja   # Korean and Japanese only
```

Gói hai ngôn ngữ có dung lượng khoảng 575 KB thay vì 8.3 MB. Cờ này chấp nhận bất kỳ danh sách phân tách bằng dấu phẩy nào gồm các mã ngôn ngữ trong bảng trên. Bỏ qua cờ này sẽ xây dựng lại mọi ngôn ngữ.

## Ghi chú cho người dùng

- Tiếng Ả Rập, tiếng Urdu, tiếng Hebrew và tiếng Ba Tư được viết từ phải sang trái. Các từ điển đã sẵn sàng; bố cục màn hình do chính DeepSeek Harness xử lý.
- Thanh menu, menu chuột phải và hộp thoại cập nhật thuộc về shell desktop, vì vậy gói này không thay đổi chúng.
- Khi DeepSeek Harness phát hành phiên bản mới, các chuỗi mới sẽ hiển thị bằng tiếng Anh cho đến khi được dịch.
- Tiếng Hàn được rà soát thủ công. Các ngôn ngữ khác đến từ bản dịch máy, và tệp từ điển của từng ngôn ngữ là nơi để điều chỉnh cách diễn đạt.
- Tiếng Nhật và tiếng Trung phồn thể giữ hình dạng chữ riêng của chúng. Ngăn xếp phông chữ của harness liệt kê các phông Trung giản thể trước các phông CJK khác, vì vậy các ký tự Hán dùng chung giữa các chuẩn nếu không sẽ được vẽ ở dạng giản thể. Gói này giới hạn ngăn xếp đã sửa cho `ja`, `zh-tw`, và `zh-hk`, và nó tuân theo bộ chọn ngôn ngữ.

## Đóng góp

Các yêu cầu về ngôn ngữ bổ sung luôn được chào đón. Mở một issue trong repository này nêu tên ngôn ngữ, và nó sẽ được tiếp nhận trong vòng tiếp theo. Các chỉnh sửa cho ngôn ngữ hiện có sẽ được đưa thẳng vào tệp từ điển của ngôn ngữ đó trong `locale/<language>/`, và pull request là cách dễ nhất.

Người bảo trì chạy quy trình dịch có thể xem lệnh trong [MAINTAINING.md](MAINTAINING.md).

## Giấy phép

MIT

<!-- pack-facts: version=0.9.1 dsh=0.2.2-rc.3 languages=23 keys=4,491 entries=103,296 bundle="7.4 MB" -->

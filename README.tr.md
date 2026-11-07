# dsh-locale-pack

<p align="right"><a href="README.md">English</a> | <a href="README.ko.md">한국어</a> | <a href="README.zh-TW.md">繁體中文</a> | <a href="README.id.md">Bahasa Indonesia</a> | <a href="README.vi.md">Tiếng Việt</a> | <strong>Türkçe</strong></p>

<p align="center"><img src="docs/pack-overview.png" alt="dsh-locale-pack overview: 29 language dictionaries, 116,467 translated entries, DeepSeek Harness 0.2.2-rc.1, the supported languages, and the git clone install command" width="100%"></p>

DeepSeek Harness için hem masaüstü uygulamasını hem de tarayıcı sürümünü kapsayan bir yerel ayar paketi. Dil seçicide 29 sözlük kaydeder: DeepSeek Harness'in sunmadığı 23 dil ve resmi 8 dilin 6'sı (Japonca, İspanyolca, Fransızca, Almanca, Rusça, Portekizce) için yenilenmiş dosyalar. Henüz çevrilmemiş dizeler İngilizce'ye geri döner, böylece kapsam genişlerken ekran okunabilir kalır. Yerleşik İngilizce ve Basitleştirilmiş Çince ile birlikte kurulumdan sonra 31 dil seçilebilir. Paket, en son DeepSeek Harness sürümüyle güncel tutulur. Ayrıca DSH eklentileri ve araçlarının topluluk dizini olan [awesome-deepseek-harness](https://github.com/0xsline/awesome-deepseek-harness) içinde de listelenmiştir.

## Bu neden var

DeepSeek Harness bir kodlama aracıdır: ona bir görev verirsiniz ve ajan dosyaları okur, düzenler ve terminal komutları çalıştırır. Masaüstü arayüzü sohbet, ayarlar, eklenti yönetimi, alt ajanlar, görev geçmişi, onay istemleri, sesli giriş ve zamanlanmış işler etrafında yapılandırılmıştır.

Bu arayüz İngilizce ve Basitleştirilmiş Çince olarak mevcuttu. Başka bir dilde çalışmayı tercih eden geliştiriciler her etiketi ikinci bir dilde okumak zorundaydı. Bu proje bu boşluğu sözlükleri ekleyerek ve dil sayısını derin değil geniş tutarak dolduruyor: bir dil, seçicide sunulduğunda ve yaygın ekranlar okunabilir olduğunda kullanılabilir olur.

## Desteklenen diller

| Language | Code | Language | Code |
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

29 dil, her biri 4,016 anahtar — toplamda 116,467 çevrilmiş girdi. Sözlükler, DeepSeek Harness yeni bir sürüm yayınladığında yenilenir ve şu anda en son sürümü, `0.2.2-rc.1` kapsar.

## Yükle

DeepSeek Harness masaüstü uygulaması önce kurulmalıdır. Ardından depoyu klonlayın ve eklenti bağlantısı olarak kaydedin.

macOS ve Linux (bash):

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

Ardından **Ayarlar → Dil**'i açın ve istediğiniz dili seçin.

### Web sürümünde kaydolun

Tarayıcı sürümü (`web` profili) aynı şekilde kaydedilir. Yalnızca profil adı değişir.

```bash
# register in the web profile, then start the server
dsh plugin --profile web add link:$(pwd)
dsh web
```

`dsh web` tarafından yazdırılan adresi açın, ardından **Ayarlar → Dil** altında bir dil seçin. Web profili ilk kayıtta otomatik olarak oluşturulur.

### Yapay zeka asistanı ile yükleyin

Geliştirme ortamınız yoksa, bir yapay zeka asistanı kurulumu sizin için yapabilir. Asistanı açın ve şunu yapıştırın:

```
Install this GitHub repository: https://github.com/sayho-pm/dsh-locale-pack
Wherever I have to type something myself, such as a token or a path,
mark it with **** and tell me exactly where it goes. Handle the rest.
```

Asistan komutları çalıştırır ve yalnızca girdinize ihtiyaç duyulan noktalarda durur.

## Depo düzeni

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

## Dize düzenleme

```bash
node tools/build-client.mjs   # rebuild lib/client.js
node tools/smoke.mjs          # self-check: loading, fallback, idempotence
node tools/check-keep.mjs     # translation quality check
```

`{name}` gibi yer tutucular tam olarak oldukları gibi korunmalıdır. Sıra veya yazım değişirse cümle çalışma zamanında bozulur.

### Yalnızca ihtiyacınız olan dilleri paketleme

Tüm paketi yüklemek varsayılandır ve sonrasında dil değiştirmek ayarlar ekranından yapılır. Tam paket ihtiyacınızdan fazlaysa, bunun yerine bir alt küme oluşturun:

```bash
node tools/build-client.mjs --langs ko,ja   # Korean and Japanese only
```

İki dilli paket 8.3 MB yerine kabaca 575 KB olur. Bayrak, yukarıdaki tablodaki dil kodlarının virgülle ayrılmış herhangi bir listesini kabul eder. Atlanırsa her dil yeniden oluşturulur.

## Çeviri kalite kontrolleri

`tools/check-keep.mjs` her dili İngilizce temelle karşılaştırır ve beş şeyi raporlar:

1. `{name}` gibi yer tutucular kaynak metindekiyle aynı sayıda görünür
2. Ürün ve protokol adları (DeepSeek Harness, MCP, JSON, OpenAI Responses ve diğerleri) çevrilmeden bırakılır
3. Çin karakteri kullanmayan dillerde hiç Çin karakteri bulunmaz
4. Korece cümleler em tire içermez
5. Hiçbir değer boş değildir ve temelin tanımlamadığı hiçbir anahtar bulunmaz

İngilizce kalan terimler `locale/_policy/keep-english.json` içinde toplanır. Çevrilmeden kalması için oraya bir terim ekleyin.

## Çeviriyi yeniden çalıştırma

Çeviri, sohbet oturumundan ayrı bir işlem olarak çalışır. Varsayılan olarak bu makinede çalışır: çalışan, 18081 bağlantı noktasındaki yerel bir Hy-MT2 7B sunucusunu çağırır, böylece hiçbir dize bilgisayardan ayrılmaz. Oturum iletileri ve konuşma geçmişi hiçbir zaman bir isteğin parçası değildir.

```bash
python3 tools/translate_worker.py --langs ja,de      # specific languages
python3 tools/translate_worker.py --all              # everything
```

Kalite kapısından geçemeyen dizeler veya yerel sunucunun kullanılamadığı çalıştırmalar, `--cloud` ile barındırılan dört modelli zinciri kullanabilir. `번역_로그` her grubun hangi model tarafından işlendiğini kaydeder.

## Kullanıcılar için notlar

- Arapça, Urduca, İbranice ve Farsça sağdan sola yazılır. Sözlükler hazır; ekran düzeni DeepSeek Harness'in kendisi tarafından yönetilir.
- Menü çubuğu, sağ tıklama menüsü ve güncelleme iletişim kutusu masaüstü kabuğuna aittir, bu nedenle bu paket bunları değiştirmez.
- DeepSeek Harness yeni bir sürüm yayınladığında, yeni dizgiler çevrilene kadar İngilizce görünür.
- Korece el ile gözden geçirilir. Diğer diller makine çevirisinden gelir ve her dilin sözlük dosyası, ifadelerin düzeltileceği yerdir.
- Japonca ve Geleneksel Çince kendi glif biçimlerini korur. Harness yazı tipi yığını Basitleştirilmiş Çince yüzleri diğer CJK yüzlerinin önüne koyar, bu yüzden iki standardın paylaştığı Han karakterleri aksi halde Basitleştirilmiş biçimde çizilir. Paket düzeltilmiş yığını `ja`, `zh-tw` ve `zh-hk` ile sınırlar ve dil seçicisini izler.

## Katkıda Bulunma

Ek diller için talepler memnuniyetle karşılanır. Bu depoda dili belirten bir issue açın, bir sonraki turda ele alınır. Mevcut bir dile yönelik düzeltmeler doğrudan `locale/<language>/` altındaki o dilin sözlük dosyasına işlenir ve pull request en kolay yöntemdir.

## Lisans

MIT

<!-- pack-facts: version=0.6.2 dsh=0.2.2-rc.1 languages=29 keys=4,016 entries=116,467 bundle="8.3 MB" -->

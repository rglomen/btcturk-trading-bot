# BTCTurk Trading Bot

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://github.com/yourusername/btcturk-trading-bot)
[![Python](https://img.shields.io/badge/python-3.8+-green.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-orange.svg)](LICENSE)
[![BTCTurk](https://img.shields.io/badge/exchange-BTCTurk-red.svg)](https://btcturk.com)

> **⚠️ Risk Uyarısı**: Bu bot finansal yatırım aracıdır. Kullanmadan önce riskleri anlayın ve sadece kaybetmeyi göze alabileceğiniz miktarlarla işlem yapın.

## 🎯 Özellikler

✅ **Otomatik Alım-Satım**: Belirlediğiniz kar yüzdesine göre otomatik işlem yapar  
✅ **Gerçek Zamanlı Fiyat Takibi**: Anlık fiyat değişimlerini izler  
✅ **Modern GUI Arayüzü**: Kullanıcı dostu grafik arayüzü  
✅ **API Anahtarı Yönetimi**: Güvenli şifreleme ile anahtarlarınızı saklar  
✅ **Demo Modu**: API anahtarları olmadan test edebilirsiniz  
✅ **Hata Yönetimi**: Kapsamlı hata takibi ve loglama  
✅ **Risk Yönetimi**: Güvenli işlem limitleri  

## 🚀 Kurulum

### Ön Gereksinimler
- Python 3.8 veya üzeri
- Git (opsiyonel, GitHub'dan klonlamak için)
- BTCTurk Pro hesabı ve API anahtarları

### Kurulum Adımları

1. **Projeyi İndirin**:
   ```bash
   git clone https://github.com/yourusername/btcturk-trading-bot.git
   cd btcturk-trading-bot
   ```
   
   veya ZIP olarak indirip çıkarın.

2. **Sanal Ortam Oluşturun** (önerilen):
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # Linux/Mac
   source venv/bin/activate
   ```

3. **Gerekli Paketleri Yükleyin**:
   ```bash
   pip install -r requirements.txt
   ```
   
   veya setup.py ile:
   ```bash
   pip install -e .
   ```

4. **Uygulamayı Çalıştırın**:
   ```bash
   # GUI versiyonu
   python gui_main.py
   
   # Komut satırı versiyonu
   python main.py
   
   # Setup.py ile kurduysanız
   btcturk-bot
   ```

### Git Kurulumu (Windows)
Eğer Git kurulu değilse:
1. [Git for Windows](https://git-scm.com/download/win) indirin
2. Kurulumu tamamlayın
3. Terminal/PowerShell'i yeniden başlatın

## 🔧 Kullanım

### API Anahtarları
- BTCTurk Pro hesabınızdan API anahtarlarınızı alın
- GUI'de "API Anahtarları" bölümüne girin
- "Kaydet" butonuyla anahtarlarınızı güvenli şekilde saklayın
- Uygulama başlatıldığında otomatik olarak yüklenir

### Demo Modu
- API anahtarları olmadan da test edebilirsiniz
- Demo modda gerçek işlem yapılmaz, sadece simülasyon çalışır
- Grafik ve performans takibi demo verilerle çalışır

### Trading Ayarları
- **Coin Çifti**: İşlem yapmak istediğiniz coin (örn: ASRTRY)
- **Hedef Kar %**: Satış için hedef kar yüzdesi
- **İşlem Miktarı**: TRY cinsinden işlem tutarı

## 🛠️ Son Güncellemeler

### v1.2 - Yeni Trading Stratejisi
- ✅ **Yeni Strateji**: Alım işleminden hemen sonra hedef kar yüzdesine göre satış emri açılır
- ✅ **Otomatik Satış Takibi**: Satış emrinin gerçekleşmesi sürekli takip edilir
- ✅ **Sıralı İşlemler**: İlk satış tamamlandıktan sonra otomatik olarak 2. işleme geçilir
- ✅ **Gelişmiş Kar Hesaplama**: Her işlem sonunda detaylı kar raporu
- ✅ **Demo Modu Desteği**: Gerçek API olmadan test edilebilir

### v1.1 - Hata Düzeltmeleri
- ✅ "Geçersiz fiyat: 0.0" hatası çözüldü
- ✅ API bağlantı sorunları düzeltildi
- ✅ Demo modu eklendi
- ✅ Ticker veri formatı sorunu çözüldü
- ✅ API anahtarı kaydetme sistemi eklendi
- ✅ Grafik güncelleme sorunu düzeltildi

## ⚠️ Önemli Notlar

- Bu bot eğitim amaçlıdır
- Gerçek para ile işlem yapmadan önce demo modda test edin
- Risk yönetimini ihmal etmeyin
- API anahtarlarınızı güvenli tutun

## 🔄 Yeni Trading Stratejisi Nasıl Çalışır?

### 1️⃣ İlk İşlem
1. **Alım Emri**: Belirlenen miktarda coin alınır
2. **Hemen Satış Emri**: Alış fiyatı + hedef kar yüzdesi ile satış emri açılır
3. **Satış Takibi**: Fiyat hedef seviyeye ulaşana kadar takip edilir
4. **Satış Gerçekleşmesi**: Hedef fiyata ulaşıldığında otomatik satış

### 2️⃣ İkinci İşlem
1. **5 Saniye Bekleme**: İlk işlem tamamlandıktan sonra kısa bekleme
2. **Otomatik 2. Alım**: Aynı miktar ile yeni alım emri
3. **Yeni Satış Emri**: Yeni alış fiyatı + hedef kar yüzdesi
4. **Sürekli Döngü**: Bu işlem sürekli tekrarlanır

### 💡 Avantajlar
- ⚡ **Hızlı İşlem**: Alım sonrası hemen satış emri
- 🎯 **Kesin Hedef**: Belirlenen kar yüzdesinde otomatik satış
- 🔄 **Sürekli İşlem**: Bir işlem bitince diğeri başlar
- 📊 **Detaylı Rapor**: Her işlem sonunda kar/zarar raporu

## 📊 Teknik Detaylar

- **Limit Order**: Güvenli işlem için limit emirleri kullanır
- **Gerçek Zamanlı**: 2 saniyede bir fiyat güncellemesi
- **Şifreleme**: API anahtarları AES şifreleme ile korunur
- **Loglama**: Tüm işlemler detaylı olarak loglanır

Otomatik alım-satım yapabilen BTCTurk trading botu. Modern GUI arayüzü ile kolay kullanım sağlar.

## Özellikler

### 🚀 Yeni Trading Stratejisi (v1.2)
- **Hızlı İşlem**: Alım sonrası hemen hedef fiyatla satış emri açılır
- **Otomatik Satış Takibi**: Fiyat hedef seviyeye ulaştığında otomatik satış
- **Sıralı İşlemler**: İlk işlem tamamlandıktan sonra otomatik 2. işlem
- **Gelişmiş Kar Takibi**: Her işlem sonunda detaylı kar/zarar raporu

### 🔧 Temel Özellikler
- 🚀 **Otomatik Trading**: Belirlediğiniz hedef kar yüzdesine göre otomatik alım-satım
- 📊 **Risk Yönetimi**: Pozisyon büyüklüğü ve günlük kayıp limitleri
- 💻 **Modern GUI**: Kolay kullanım için grafik arayüz
- 📈 **Fiyat Takibi**: Gerçek zamanlı fiyat grafiği
- 🔒 **Güvenli**: API anahtarları şifrelenmiş olarak saklanır
- 📝 **Detaylı Loglama**: Tüm işlemler loglanır

## 📋 Gereksinimler

### Sistem Gereksinimleri
- **Python**: 3.8 veya üzeri
- **İşletim Sistemi**: Windows 10/11, macOS, Linux
- **RAM**: Minimum 4GB (8GB önerilen)
- **Disk Alanı**: 500MB boş alan

### BTCTurk API
- BTCTurk hesabı
- API Key ve Secret (BTCTurk Pro hesabından alınabilir)
- API izinleri: Okuma ve İşlem yapma

## 🚀 Kurulum

### 1. Projeyi İndirin
```bash
git clone https://github.com/your-username/btcturk-trading-bot.git
cd btcturk-trading-bot
```

### 2. Sanal Ortam Oluşturun (Önerilen)
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 3. Gerekli Kütüphaneleri Yükleyin
```bash
pip install -r requirements.txt
```

### 4. BTCTurk API Anahtarlarını Alın
1. [BTCTurk Pro](https://pro.btcturk.com) hesabınıza giriş yapın
2. Ayarlar > API Yönetimi bölümüne gidin
3. Yeni API anahtarı oluşturun
4. **Okuma** ve **İşlem** izinlerini verin
5. API Key ve Secret'ı güvenli bir yerde saklayın

## 🎯 Kullanım

### İlk Çalıştırma
```bash
python main.py
```

### Temel Adımlar

1. **API Ayarları**
   - Ayarlar menüsünden API Key ve Secret'ınızı girin
   - Bağlantıyı test edin

2. **Trading Parametreleri**
   - Coin seçin (örn: BTCTRY)
   - Hedef kar yüzdesini belirleyin (örn: %2)
   - İşlem miktarını girin (TRY cinsinden)

3. **Bot'u Başlatın**
   - "Trading Başlat" butonuna tıklayın
   - Bot otomatik olarak fiyat takibine başlar

4. **İzleme**
   - Real-time fiyat grafiğini takip edin
   - Bot durumunu kontrol edin
   - İşlem geçmişini inceleyin

### Örnek Senaryo
```
Coin: BTCTRY
Hedef Kar: %3
İşlem Miktarı: 1000 TRY
Mevcut Fiyat: 850,000 TRY

1. Bot 850,000 TRY'den Bitcoin alır
2. Fiyat 875,500 TRY'ye çıkınca (%3 kar) otomatik satar
3. İşlem tamamlanır ve kar elde edilir
```

## ⚙️ Yapılandırma

### Ayarlar Dosyası
Bot ayarları `bot_settings.json` dosyasında saklanır:

```json
{
  "default_coin": "BTCTRY",
  "default_target_percentage": 2.0,
  "default_trade_amount": 1000.0,
  "max_daily_loss": 5.0,
  "stop_loss_percentage": -3.0,
  "price_check_interval": 1,
  "theme": "dark"
}
```

### Risk Yönetimi Ayarları
- **Maksimum Günlük Kayıp**: Günde kaybedilebilecek maksimum yüzde
- **Stop Loss**: Pozisyon kapatılacak zarar yüzdesi
- **Maksimum Pozisyon**: Tek seferde açılabilecek maksimum pozisyon büyüklüğü

### Strateji Ayarları
- **Fiyat Kontrol Aralığı**: Fiyat kontrolü yapma sıklığı (saniye)
- **Trend Analiz Süresi**: Trend analizi için kullanılacak süre (dakika)
- **Volatilite Eşiği**: İşlem yapılacak minimum volatilite seviyesi

## 📊 Özellikler Detayı

### Trading Stratejisi
Bot gelişmiş bir trading stratejisi kullanır:

1. **Fiyat Analizi**: Sürekli fiyat takibi ve trend analizi
2. **Teknik Göstergeler**: Hareketli ortalama ve volatilite hesaplamaları
3. **Sinyal Üretimi**: Alım/satım sinyalleri oluşturma
4. **Risk Kontrolü**: Her işlem öncesi risk değerlendirmesi

### Hata Yönetimi
- **Otomatik Hata Yakalama**: Tüm hatalar otomatik olarak yakalanır ve loglanır
- **Yeniden Deneme**: Network hataları durumunda otomatik yeniden deneme
- **Acil Durum**: Kritik hatalar durumunda güvenli durdurma
- **Log Sistemi**: Detaylı log kayıtları ve hata raporları

### Güvenlik Önlemleri
- **API Key Şifreleme**: Tüm hassas veriler şifrelenerek saklanır
- **Bağlantı Kontrolü**: Sürekli API bağlantı durumu kontrolü
- **İşlem Doğrulama**: Her işlem öncesi doğrulama kontrolü
- **Limit Kontrolü**: Günlük ve işlem bazlı limitler

## 🧪 Test Etme

### Unit Testler
```bash
python test_bot.py
```

### Test Kapsamı
- Trading Bot fonksiyonları
- Strateji algoritmaları
- Risk yönetimi
- Ayar yönetimi
- Hata işleme
- Entegrasyon testleri

### Performans Testleri
Test dosyası ayrıca performans ve stres testleri de içerir:
- Fiyat işleme hızı
- Çoklu thread performansı
- Bellek kullanımı
- Hata işleme hızı

## 📁 Proje Yapısı

```
btcturk-trading-bot/
├── main.py                 # Ana uygulama dosyası
├── trading_bot.py          # Trading bot sınıfı
├── trading_strategy.py     # Trading stratejisi ve risk yönetimi
├── gui_main.py            # Ana GUI arayüzü
├── settings_manager.py     # Ayar yönetimi
├── error_handler.py        # Hata yönetimi ve loglama
├── test_bot.py            # Test senaryoları
├── requirements.txt        # Python bağımlılıkları
├── README.md              # Bu dosya
├── logs/                  # Log dosyaları
│   ├── bot_YYYY-MM-DD.log
│   ├── errors_YYYY-MM-DD.log
│   ├── trading_YYYY-MM-DD.log
│   └── api_YYYY-MM-DD.log
└── bot_settings.json      # Bot ayarları (otomatik oluşur)
```

## 🔧 Sorun Giderme

### Yaygın Sorunlar

#### 1. API Bağlantı Hatası
```
Hata: API bağlantısı kurulamadı
Çözüm: 
- API Key ve Secret'ı kontrol edin
- BTCTurk API durumunu kontrol edin
- İnternet bağlantınızı kontrol edin
```

#### 2. Yetersiz Bakiye
```
Hata: Yetersiz bakiye
Çözüm:
- BTCTurk hesabınızda yeterli TRY bakiyesi olduğundan emin olun
- İşlem miktarını azaltın
```

#### 3. Kütüphane Hatası
```
Hata: ModuleNotFoundError
Çözüm:
- pip install -r requirements.txt komutunu çalıştırın
- Python sürümünüzü kontrol edin (3.8+)
```

### Log Dosyaları
Sorun yaşadığınızda log dosyalarını kontrol edin:
- `logs/bot_YYYY-MM-DD.log`: Genel bot logları
- `logs/errors_YYYY-MM-DD.log`: Hata logları
- `logs/trading_YYYY-MM-DD.log`: İşlem logları
- `logs/api_YYYY-MM-DD.log`: API çağrı logları

## ⚠️ Önemli Uyarılar

### Risk Uyarısı
- **Kripto para ticareti yüksek risklidir**
- **Kaybetmeyi göze alabileceğiniz miktarla işlem yapın**
- **Bot'u kullanmadan önce test edin**
- **Piyasa koşulları hızla değişebilir**

### Güvenlik Uyarıları
- API anahtarlarınızı kimseyle paylaşmayın
- Bot'u güvenilir bir bilgisayarda çalıştırın
- Düzenli olarak API anahtarlarınızı yenileyin
- Bot'u sürekli izleyin

### Yasal Uyarı
- Yerel yasalarınızı kontrol edin
- Vergi yükümlülüklerinizi unutmayın
- Bot'un performansı garanti edilmez
- Kendi sorumluluğunuzda kullanın

## 🔄 Güncelleme

### Bot Güncellemeleri
```bash
git pull origin main
pip install -r requirements.txt --upgrade
```

### Ayar Yedekleme
Önemli güncellemeler öncesi ayarlarınızı yedekleyin:
- Ayarlar > Dışa Aktar menüsünü kullanın
- `bot_settings.json` dosyasını kopyalayın

## 🤝 Katkıda Bulunma

### Geliştirme
1. Projeyi fork edin
2. Feature branch oluşturun (`git checkout -b feature/amazing-feature`)
3. Değişikliklerinizi commit edin (`git commit -m 'Add amazing feature'`)
4. Branch'i push edin (`git push origin feature/amazing-feature`)
5. Pull Request oluşturun

### Bug Raporu
Bug bulduğunuzda lütfen şunları ekleyin:
- Detaylı açıklama
- Adım adım tekrarlama yöntemi
- Beklenen ve gerçek sonuç
- Log dosyaları (logs/ klasöründen)
- Sistem bilgileri (OS, Python versiyonu)

## 📋 Version Bilgisi

Mevcut version bilgisini görmek için:
```bash
python __version__.py
# veya
btcturk-version
```

### Version Geçmişi
- **v1.0.0** (2025-01-08): İlk stabil sürüm
  - GUI tabanlı trading bot
  - Çoklu API anahtarı desteği
  - Otomatik alış/satış sistemi
  - Gerçek zamanlı bakiye takibi
  - Hızlı alış emri algılama

Detaylı değişiklikler için [CHANGELOG.md](CHANGELOG.md) dosyasına bakın.

## 📄 Lisans

Bu proje MIT lisansı altında lisanslanmıştır. Detaylar için [LICENSE](LICENSE) dosyasına bakın.

## 🔗 Bağlantılar

- **GitHub Repository**: [btcturk-trading-bot](https://github.com/yourusername/btcturk-trading-bot)
- **Issues**: [Bug Reports & Feature Requests](https://github.com/yourusername/btcturk-trading-bot/issues)
- **Wiki**: [Documentation](https://github.com/yourusername/btcturk-trading-bot/wiki)
- **BTCTurk API**: [Official Documentation](https://docs.btcturk.com/)

## ⭐ Destek

Eğer bu proje işinize yaradıysa, lütfen ⭐ vererek destek olun!

---

**Yasal Uyarı**: Bu yazılım eğitim ve araştırma amaçlıdır. Finansal kayıplardan yazılım geliştiricileri sorumlu değildir. Kullanım riski tamamen kullanıcıya aittir.
- Detaylı açıklama
- Hata mesajları
- Log dosyaları
- Sistem bilgileri
- Tekrar etme adımları

## 📞 Destek

### İletişim
- **GitHub Issues**: Bug raporu ve özellik istekleri için
- **Email**: support@example.com
- **Discord**: Trading Bot Community

### Dokümantasyon
- [API Dokümantasyonu](https://docs.btcturk.com/)
- [Trading Rehberi](https://github.com/your-username/btcturk-trading-bot/wiki)
- [Video Eğitimler](https://youtube.com/playlist)

## 📄 Lisans

Bu proje MIT lisansı altında lisanslanmıştır. Detaylar için [LICENSE](LICENSE) dosyasına bakın.

## 🙏 Teşekkürler

- BTCTurk API ekibine
- CustomTkinter geliştiricilerine
- Açık kaynak topluluğuna
- Beta test kullanıcılarına

## 📈 Sürüm Geçmişi

### v1.0.0 (2024-01-XX)
- ✅ İlk stabil sürüm
- ✅ Temel trading fonksiyonları
- ✅ Modern GUI arayüzü
- ✅ Risk yönetimi
- ✅ Hata yönetimi
- ✅ Ayar sistemi
- ✅ Test senaryoları

### Gelecek Sürümler
- 🔄 v1.1.0: Gelişmiş teknik analiz
- 🔄 v1.2.0: Çoklu exchange desteği
- 🔄 v1.3.0: Mobil uygulama
- 🔄 v2.0.0: AI destekli trading

---

**⚡ BTCTurk Trading Bot ile akıllı trading deneyimi yaşayın!**

*Bu bot eğitim ve araştırma amaçlıdır. Finansal tavsiye değildir. Kendi riskinizle kullanın.*
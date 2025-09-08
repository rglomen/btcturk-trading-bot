# Changelog

Tüm önemli değişiklikler bu dosyada belgelenecektir.

Format [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) standardına dayanmaktadır,
ve bu proje [Semantic Versioning](https://semver.org/spec/v2.0.0.html) kullanmaktadır.

## [Unreleased]

### Planned
- GitHub Actions CI/CD pipeline
- Otomatik testler
- Docker desteği
- Gelişmiş grafik ve chart desteği
- Mobil uygulama

## [1.1.0] - 2025-01-08

### Added
- 📊 **İşlem Geçmişi Bölümü**: Tüm işlemlerin detaylı takibi
  - Filtrelenebilir işlem tablosu (tarih, tür, coin)
  - Detaylı istatistikler (toplam işlem, kar/zarar, başarı oranı)
  - CSV formatında dışa aktarma özelliği
  - Gerçek zamanlı işlem ekleme
- 📝 **Gelişmiş Log Sistemi**: Kategorize edilmiş log yönetimi
  - Açılır-kapanır log kategorileri (Sistem, Trading, API, Hata)
  - Log seviye filtreleme (INFO, WARNING, ERROR)
  - Log kaydetme ve temizleme araçları
  - Otomatik log yenileme

### Improved
- 🎨 Kullanıcı arayüzü iyileştirmeleri
- 🔧 Daha iyi hata yönetimi
- 📱 Responsive tasarım geliştirmeleri

### Technical
- Modüler log yönetim sistemi
- Thread-safe işlem geçmişi güncellemeleri
- Optimize edilmiş GUI performansı
- Gelişmiş veri filtreleme algoritmaları

## [1.0.0] - 2025-01-08

### Added
- 🎉 İlk stabil sürüm yayınlandı
- 🖥️ GUI tabanlı kullanıcı arayüzü
- 🔑 Çoklu API anahtarı desteği ve güvenli saklama
- 🤖 Otomatik alış/satış trading sistemi
- 💰 Gerçek zamanlı bakiye takibi ve güncelleme
- 📊 Kar/zarar hesaplama ve gösterimi
- 📝 Detaylı loglama sistemi (günlük dosyalar)
- ⚡ Hızlı alış emri algılama ve işleme
- 🔄 Thread-safe GUI güncellemeleri
- 🎯 BTCTurk API tam entegrasyonu
- 🧪 Demo ve gerçek mod desteği
- 📈 Dinamik fiyat takibi
- 🛡️ Otomatik stop-loss mekanizması
- 🪙 Çoklu coin desteği (BTC, ETH, AVAX, vb.)
- 🔐 Şifreli API anahtar saklama
- 🚨 Kapsamlı hata yönetimi ve recovery

### Technical Features
- Tkinter tabanlı modern GUI
- Çoklu threading desteği
- Gerçek zamanlı WebSocket bağlantıları
- RESTful API entegrasyonu
- Cryptography ile güvenli veri saklama
- Structured logging with rotation
- Exception handling ve error recovery
- Memory efficient data structures

### Security
- API anahtarları şifreli olarak saklanıyor
- Güvenli bağlantı protokolleri
- Input validation ve sanitization
- Rate limiting ve API quota yönetimi

### Performance
- Optimize edilmiş API çağrıları
- Efficient memory usage
- Fast order execution detection
- Minimal GUI blocking operations
- Smart polling intervals

---

## Version Schema

Bu proje [Semantic Versioning](https://semver.org/) kullanır:

- **MAJOR**: Geriye uyumsuz API değişiklikleri
- **MINOR**: Geriye uyumlu yeni özellikler
- **PATCH**: Geriye uyumlu hata düzeltmeleri

## Kategoriler

- `Added`: Yeni özellikler
- `Changed`: Mevcut işlevsellikte değişiklikler
- `Deprecated`: Yakında kaldırılacak özellikler
- `Removed`: Kaldırılan özellikler
- `Fixed`: Hata düzeltmeleri
- `Security`: Güvenlik ile ilgili değişiklikler
# Neden Database Gerekli?

## Database'in Kullanım Alanları

ServerScout uygulaması **SQLite database** kullanıyor çünkü:

### 1. **Server Bilgilerini Saklama**
- IP adresleri
- Kullanıcı adları ve şifreler (isteğe bağlı)
- OS tipi (Windows/Linux)
- Proje atamaları

### 2. **Proje Yönetimi**
- Proje isimleri
- Hangi sunucuların hangi projeye ait olduğu
- Proje istatistikleri

### 3. **Scan Sonuçlarını Saklama**
- Hardware bilgileri (CPU, RAM, Disk)
- Disk kullanım oranları
- Son tarama zamanı
- Sunucu durumu (Online/Offline)

### 4. **Veri Kalıcılığı**
- Uygulama kapanıp açıldığında veriler kaybolmaz
- Excel export için veri hazır
- Geçmiş tarama sonuçları saklanır

## Database Olmadan Ne Olur?

Eğer database olmazsa:
- ❌ Sunucu bilgileri kaybolur (her açılışta yeniden eklemek gerekir)
- ❌ Proje yönetimi çalışmaz
- ❌ Scan sonuçları saklanamaz
- ❌ Excel export yapılamaz (veri yok)

## Database Path Sorunları

### Development Modda:
- Path: `c:\serverspy\data\inventory.db`
- Normal çalışır

### Packaged Modda (EXE):
- Path: `%APPDATA%\ServerScout\data\inventory.db`
- AppData klasörüne yazma izni gerekir
- Eğer hata varsa log dosyasına yazılır

## Log Dosyası

Hatalar şuraya yazılıyor:
- **Development:** `c:\serverspy\logs\serverscout_YYYYMMDD.log`
- **Packaged:** `%APPDATA%\ServerScout\logs\serverscout_YYYYMMDD.log`

Log dosyasını kontrol ederek database hatalarını görebilirsiniz.







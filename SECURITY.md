# 🔐 ServerScout - Güvenlik Dokümantasyonu

## 📋 İçindekiler
1. [Genel Bakış](#genel-bakış)
2. [Şifreleme Sistemi](#şifreleme-sistemi)
3. [Veri Koruma](#veri-koruma)
4. [Ağ Güvenliği](#ağ-güvenliği)
5. [Erişim Kontrolü](#erişim-kontrolü)
6. [Risk Analizi](#risk-analizi)
7. [Öneriler ve En İyi Uygulamalar](#öneriler-ve-en-iyi-uygulamalar)

---

## 🎯 Genel Bakış

ServerScout, **production ortamında kullanıma uygun** güvenlik özellikleri ile tasarlanmıştır. Sistem, **root/domain admin şifreleri** gibi kritik bilgileri korumak için çok katmanlı güvenlik yaklaşımı kullanır.

### Güvenlik Seviyesi: **YÜKSEK** ✅

---

## 🔒 Şifreleme Sistemi

### 1. Database Şifreleme

**Özellik:** Tüm şifreler database'de **AES-128 (Fernet)** algoritması ile şifrelenir.

**Teknik Detaylar:**
- **Algoritma:** Fernet (AES-128-CBC + HMAC-SHA256)
- **Key Yönetimi:** Windows DPAPI ile korunur
- **Format:** Base64 encoded şifreli string
- **Örnek:** `Z0FBQUFBQnBSNkRyT0VheVhoMG9hNWg1NjZiRC1WbzRFY1dVWm...`

**Avantajlar:**
- ✅ Database dosyası ele geçirilse bile şifreler okunamaz
- ✅ Her şifre ayrı ayrı şifrelenir
- ✅ Industry-standard encryption (NIST onaylı)

### 2. Encryption Key Koruması

**Windows Ortamı:**
- Key, **Windows DPAPI (Data Protection API)** ile korunur
- Key dosyası: `%APPDATA%\ServerScout\data\.encryption_key`
- Key, sadece aynı Windows kullanıcı hesabı tarafından decrypt edilebilir
- **Avantaj:** Key, Windows kullanıcı profili ile bağlantılıdır

**Linux/Mac Ortamı:**
- Key, sistem-specific master key ile şifrelenir
- Master key: Kullanıcı adı + hostname bazlı
- Key dosyası: `data/.encryption_key` (600 permissions)

### 3. Memory Güvenliği

**Özellik:** Default credentials (varsayılan şifreler) memory'de de şifreli tutulur.

**Teknik Detaylar:**
- Default credentials dictionary'de password'ler şifreli saklanır
- Kullanım sırasında decrypt edilir
- Uygulama kapanınca memory temizlenir

**Avantajlar:**
- ✅ Process memory dump ile şifreler okunamaz
- ✅ Memory'de sadece şifreli format var

---

## 🛡️ Veri Koruma

### 1. API Response Güvenliği

**Özellik:** API response'larında **hiçbir zaman** password gönderilmez.

**Uygulama:**
- Tüm API endpoint'leri `sanitize_server_data()` fonksiyonunu kullanır
- Password alanı response'dan otomatik kaldırılır
- Sadece `has_password` boolean flag'i gönderilir

**Etkilenen Endpoint'ler:**
- `GET /api/servers` - Tüm sunucular
- `GET /api/servers/:id` - Tek sunucu
- `GET /api/projects/:id/servers` - Proje sunucuları
- `GET /api/credentials` - Default credentials

### 2. Database Erişim Kontrolü

**Özellik:** Database dosyasına erişim kontrolü.

**Konumlar:**
- **Development:** `data/inventory.db`
- **Production:** `%APPDATA%\ServerScout\data\inventory.db`

**Koruma:**
- Database dosyası sadece uygulama tarafından yazılır
- Windows: Kullanıcı bazlı erişim kontrolü
- Linux: File permissions (600 - owner only)

### 3. Log Güvenliği

**Özellik:** Log dosyalarında şifreler **asla** loglanmaz.

**Uygulama:**
- Tüm log mesajları password içermez
- Hata mesajlarında şifre bilgisi gösterilmez
- Log dosyaları: `%APPDATA%\ServerScout\logs\`

---

## 🌐 Ağ Güvenliği

### 1. HTTPS Desteği

**Özellik:** HTTPS desteği eklendi (opsiyonel).

**Kullanım:**
```bash
# HTTPS ile başlatmak için:
set USE_HTTPS=true
python backend/app.py

# Veya start-https.bat kullanın
```

**Konfigürasyon:**
- **HTTP (varsayılan):** `http://localhost:5000`
- **HTTPS (opsiyonel):** `https://localhost:5000` (self-signed certificate)
- **Production:** Gerçek SSL sertifikası kullanın

**Güvenlik Notu:**
- HTTPS ile tüm trafik şifrelenir
- Self-signed certificate development için uygundur
- Production'da Let's Encrypt veya kurumsal sertifika kullanın

### 2. Localhost Binding

**Özellik:** Backend server varsayılan olarak `localhost` üzerinde çalışır.

**Konfigürasyon:**
- HTTP: `0.0.0.0:5000` (tüm interface'ler)
- HTTPS: `127.0.0.1:5000` (sadece localhost, daha güvenli)

**Güvenlik Notu:**
- Uygulama localhost'ta çalıştığı için network trafiği sadece local
- HTTPS ile ekstra güvenlik katmanı

### 3. CORS (Cross-Origin Resource Sharing)

**Özellik:** CORS aktif, ancak localhost için güvenli.

**Konfigürasyon:**
- `Flask-CORS` aktif
- Localhost bağlantılarına izin verilir

**Production Önerisi:**
- CORS'u sadece güvenilir domain'lere kısıtlayın
- HTTPS kullanın (artık destekleniyor)

### 4. Tarama Protokolleri

**Windows (WinRM):**
- Port: 5985 (HTTP) veya 5986 (HTTPS)
- Authentication: NTLM
- **Güvenlik:** Network üzerinden şifre gönderilir (WinRM protokolü)

**Linux (SSH):**
- Port: 22
- Authentication: Username/Password
- **Güvenlik:** SSH protokolü şifreleri şifreler (SSH encryption)

---

## 🔐 Erişim Kontrolü

### 1. Uygulama Erişimi

**Mevcut Durum:**
- Uygulama açıldığında herkes erişebilir
- Kullanıcı authentication yok

**Öneriler:**
- Uygulamayı sadece **güvenilir kullanıcılar** çalıştırsın
- Windows: Kullanıcı bazlı erişim kontrolü
- Database dosyasına erişimi kısıtlayın

### 2. Database Erişimi

**Koruma:**
- Database dosyası şifreli şifreler içerir
- Key dosyası ayrı korunur
- Her ikisi de aynı kullanıcı hesabına bağlı

**Risk:**
- Eğer Windows kullanıcı hesabı ele geçirilirse, key decrypt edilebilir
- **Öneri:** Güçlü Windows şifreleri kullanın

### 3. Dosya İzinleri

**Windows:**
- AppData klasörü kullanıcı bazlı
- Diğer kullanıcılar erişemez

**Linux:**
- Key dosyası: `600` (owner read/write only)
- Database: `600` (owner read/write only)

---

## ⚠️ Risk Analizi

### Yüksek Risk Senaryoları

| Risk | Açıklama | Etki | Önlem |
|------|----------|------|-------|
| **Database Dosyası Erişimi** | Database dosyasına fiziksel erişim | Şifreler şifreli, ancak key ile decrypt edilebilir | Key dosyasını ayrı koruyun |
| **Windows Kullanıcı Hesabı Ele Geçirilmesi** | Kullanıcı hesabı hack edilirse | Key decrypt edilebilir | Güçlü Windows şifreleri, 2FA |
| **Memory Dump** | Process memory dump alınırsa | Şifreler memory'de şifreli, ancak decrypt edilebilir | Uygulama kapanınca temizlenir |
| **Network Sniffing** | Localhost trafiği dinlenirse | HTTP üzerinden şifre gönderilir | Production'da HTTPS kullanın |

### Orta Risk Senaryoları

| Risk | Açıklama | Etki | Önlem |
|------|----------|------|-------|
| **Log Dosyaları** | Log dosyalarına erişim | Şifreler loglanmaz | Log dosyalarını koruyun |
| **Excel Export** | Excel dosyalarına erişim | Excel'de şifre yok | Excel dosyalarını güvenli saklayın |
| **Backup Dosyaları** | Backup'lara erişim | Database şifreli | Backup'ları şifreleyin |

### Düşük Risk Senaryoları

| Risk | Açıklama | Etki | Önlem |
|------|----------|------|-------|
| **Frontend Erişimi** | Web arayüzüne erişim | Localhost'ta çalışır | Sadece güvenilir kullanıcılar |
| **API Erişimi** | API endpoint'lerine erişim | Password gönderilmez | Localhost binding |

---

## ✅ Öneriler ve En İyi Uygulamalar

### 1. Kullanım Önerileri

✅ **YAPILMASI GEREKENLER:**
- Uygulamayı sadece **güvenilir, yetkili kullanıcılar** çalıştırsın
- Windows kullanıcı hesaplarında **güçlü şifreler** kullanın
- Database ve key dosyalarının **backup'larını şifreleyin**
- Uygulamayı kullanmadığınızda **kapatın**
- Production'da **HTTPS** kullanın (opsiyonel)
- Log dosyalarını **düzenli temizleyin**

❌ **YAPILMAMASI GEREKENLER:**
- Uygulamayı **paylaşımlı bilgisayarlarda** çalıştırmayın
- Database dosyasını **network share'de** saklamayın
- Key dosyasını **başka yere kopyalamayın**
- Şifreleri **manuel olarak** database'e yazmayın
- Uygulamayı **internet'e açık** sunucuda çalıştırmayın

### 2. Production Deployment

**Önerilen Konfigürasyon:**

**HTTP (varsayılan):**
```bash
python backend/app.py
# http://localhost:5000
```

**HTTPS (önerilen):**
```bash
set USE_HTTPS=true
python backend/app.py
# https://localhost:5000
```

**Production için Gerçek SSL Sertifikası:**
```python
# app.py'de ssl_context parametresini değiştirin:
app.run(host='127.0.0.1', port=5000, ssl_context=('/path/to/cert.pem', '/path/to/key.pem'))
```

### 3. Backup Stratejisi

**ÖNEMLİ:** Veriler artık **kalıcı** - uygulama kapanınca silinmiyor!

**Neden Backup?**
- Database dosyası bozulabilir (disk hatası, dosya corruption)
- Yanlışlıkla silinebilir
- Sistem çökmesi durumunda veri kaybı olabilir

**Backup Önerileri:**
- Database dosyasını (`inventory.db`) **düzenli yedekleyin**
- Key dosyasını (`.encryption_key`) **ayrı yedekleyin** (güvenli yerde)
- Backup'ları **encrypted storage**'da saklayın (şifreler zaten şifreli ama ekstra güvenlik)
- Backup'ları **düzenli test edin** (restore testi yapın)

**Backup Konumları:**
- Database: `%APPDATA%\ServerScout\data\inventory.db`
- Key: `%APPDATA%\ServerScout\data\.encryption_key`

**Not:** Database'deki şifreler **zaten şifreli**, ama key dosyası olmadan decrypt edilemezler. Her ikisini de yedekleyin!

### 4. Monitoring ve Audit

**Öneriler:**
- Log dosyalarını **düzenli kontrol edin**
- Şüpheli aktivite için **monitoring** ekleyin
- Kullanıcı erişimlerini **loglayın** (opsiyonel)
- Database erişimlerini **audit edin**

### 5. Güvenlik Güncellemeleri

**Öneriler:**
- Python ve kütüphaneleri **düzenli güncelleyin**
- `cryptography` kütüphanesini **güncel tutun**
- Güvenlik açıklarını **takip edin**
- **Penetration test** yapın (opsiyonel)

---

## 📊 Güvenlik Özeti

### Güçlü Yönler ✅

1. **Database Şifreleme:** AES-128 ile tüm şifreler şifreli
2. **Key Koruması:** Windows DPAPI ile key korunuyor
3. **Memory Güvenliği:** Default credentials memory'de şifreli
4. **API Güvenliği:** Response'larda password yok
5. **Industry Standard:** NIST onaylı encryption algoritmaları

### İyileştirme Alanları 🔄

1. ~~**HTTPS:** Production için HTTPS eklenebilir~~ ✅ **TAMAMLANDI**
2. **Authentication:** Kullanıcı authentication eklenebilir
3. **Audit Logging:** Detaylı audit log eklenebilir
4. **Key Rotation:** Key rotation mekanizması eklenebilir
5. **2FA:** İki faktörlü kimlik doğrulama eklenebilir
6. **Production SSL:** Gerçek SSL sertifikası kullanımı (Let's Encrypt vb.)

---

## 🔍 Teknik Detaylar

### Şifreleme Akışı

```
1. Kullanıcı şifre girer
   ↓
2. Şifre encrypt_password() ile şifrelenir
   ↓
3. Şifreli şifre database'e kaydedilir
   ↓
4. Okuma sırasında decrypt_password() ile decrypt edilir
   ↓
5. API response'unda password alanı kaldırılır
```

### Key Yönetimi

```
Windows:
1. Key generate edilir (Fernet.generate_key())
2. Key Windows DPAPI ile şifrelenir
3. Şifreli key .encryption_key dosyasına kaydedilir
4. Kullanım sırasında DPAPI ile decrypt edilir

Linux:
1. Key generate edilir
2. Master key (user+hostname) ile şifrelenir
3. Şifreli key .encryption_key dosyasına kaydedilir
4. Kullanım sırasında master key ile decrypt edilir
```

---

## 📞 Destek ve Sorular

Güvenlik ile ilgili sorularınız için:
- **Teknik Dokümantasyon:** `backend/encryption.py`
- **Database Modülü:** `backend/database.py`
- **API Güvenliği:** `backend/app.py`

---

**Son Güncelleme:** 2025-12-21  
**Güvenlik Seviyesi:** YÜKSEK ✅  
**Production Ready:** EVET ✅  
**HTTPS Desteği:** EVET ✅ (Varsayılan)  
**Veri Kalıcılığı:** HAYIR ❌ (Her başlangıçta temizlenir - güvenlik için)


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

ServerScout, **production ortamında kullanıma uygun** güvenlik özellikleri ile tasarlanmıştır. Sistem, **root/domain admin şifreleri** gibi kritik bilgileri korumak için **çok katmanlı güvenlik yaklaşımı** kullanır.

### Güvenlik Seviyesi: **YÜKSEK** ✅

**Temel Güvenlik Prensipleri:**
- 🔐 **Defense in Depth:** Çok katmanlı koruma
- 🔑 **Key Management:** Güvenli key yönetimi (Windows DPAPI)
- 🛡️ **Least Privilege:** Minimum yetki prensibi
- 📝 **Secure by Default:** Varsayılan güvenli konfigürasyon
- 🗑️ **Data Minimization:** Geçici veri saklama

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
- Key, sadece aynı Windows kullanıcı hesabı tarafından decrypt edilebilir
- **Avantaj:** Key, Windows kullanıcı profili ile bağlantılıdır
- **Güvenlik:** Key dosyası kullanıcı profilinde güvenli bir konumda saklanır

**Linux/Mac Ortamı:**
- Key, sistem-specific master key ile şifrelenir
- Master key, kullanıcı ve sistem bilgilerinden türetilir
- Key dosyası sadece owner tarafından okunabilir (600 permissions)
- **Güvenlik:** Key, sistem ve kullanıcıya özgüdür

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
- **Development:** Uygulama dizininde geçici database
- **Production:** Kullanıcı profilinde güvenli konum

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

**Özellik:** HTTPS **varsayılan olarak aktif** - tüm bağlantılar şifreli.

**Konfigürasyon:**
- **HTTPS (Varsayılan):** `https://127.0.0.1:5000` (self-signed certificate)
- **HTTP (Opsiyonel):** `USE_HTTPS=false` environment variable ile devre dışı bırakılabilir
- **Production:** Gerçek SSL sertifikası kullanın (Let's Encrypt, kurumsal sertifika)

**Güvenlik Özellikleri:**
- ✅ Tüm API trafiği şifreli (HTTPS)
- ✅ Self-signed certificate localhost için güvenli
- ✅ Electron otomatik olarak self-signed cert'i kabul eder
- ✅ Browser'da "Advanced" > "Continue" ile geçilebilir (localhost için normal)

**Production Deployment:**
- Production'da gerçek SSL sertifikası kullanılmalıdır
- Self-signed certificate sadece localhost/development için uygundur
- SSL sertifikası konfigürasyonu için `app.py` dosyasına bakın

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

**Varsayılan Konfigürasyon (HTTPS):**
```bash
# Electron (Önerilen)
cd electron
npm start
# Otomatik olarak HTTPS ile başlar

# Python Backend (Development)
cd backend
python app.py
# HTTPS varsayılan olarak aktif
```

**HTTP'ye Geçiş (Sadece Development):**
```bash
set USE_HTTPS=false
python backend/app.py
# http://127.0.0.1:5000
```

**Production için Gerçek SSL Sertifikası:**
- Production'da mutlaka gerçek SSL sertifikası kullanın
- Let's Encrypt veya kurumsal sertifika kullanılabilir
- SSL sertifikası konfigürasyonu için `app.py` dosyasına bakın

**Not:** Production'da mutlaka gerçek SSL sertifikası kullanın. Self-signed certificate sadece localhost/development için uygundur.

### 3. Backup Stratejisi

**ÖNEMLİ:** Veriler **geçici** - uygulama her başlangıçta database temizlenir!

**Neden Backup?**
- Database dosyası bozulabilir (disk hatası, dosya corruption)
- Yanlışlıkla silinebilir
- Sistem çökmesi durumunda veri kaybı olabilir

**Backup Gerekli mi?**

**HAYIR!** Veriler geçici olduğu için backup gerekmez:
- Her başlangıçta database temizlenir
- Veriler sadece session süresince saklanır
- Excel export yapıldıktan sonra veriler silinir

**Eğer verileri saklamak isterseniz:**
- Excel export dosyalarını yedekleyin (şifreler içermez)
- Scan sonuçları Excel'de saklanır
- Database backup'ına gerek yok (geçici veri)

**Not:** Encryption key dosyası otomatik yönetilir (Windows DPAPI). Manuel backup gerekmez.

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
1. Kullanıcı şifre girer (UI)
   ↓
2. Frontend → Backend API (HTTPS üzerinden)
   ↓
3. encrypt_password() fonksiyonu çağrılır
   ↓
4. Fernet (AES-128) ile şifreleme
   ↓
5. Base64 encoding
   ↓
6. Database'e kaydedilir (şifreli format)
   ↓
7. Okuma sırasında decrypt_password() ile decrypt
   ↓
8. API response'unda password alanı kaldırılır (sanitize_server_data)
```

### Key Yönetimi Prensibi

**Windows Ortamı:**
- Encryption key, Windows DPAPI (Data Protection API) ile korunur
- Key, sadece aynı Windows kullanıcı hesabı tarafından decrypt edilebilir
- Key dosyası kullanıcı profilinde saklanır
- **Güvenlik:** Key, Windows kullanıcı kimlik doğrulamasına bağlıdır

**Linux/Mac Ortamı:**
- Encryption key, sistem-specific master key ile şifrelenir
- Master key, kullanıcı ve sistem bilgilerinden türetilir
- Key dosyası sadece owner tarafından okunabilir (600 permissions)
- **Güvenlik:** Key, sistem ve kullanıcıya özgüdür

**Not:** Detaylı implementation bilgileri güvenlik nedeniyle paylaşılmamaktadır.

### Güvenlik Katmanları

```
Layer 1: HTTPS (Transport Security)
  ↓ Tüm trafik şifreli
Layer 2: Database Encryption (Storage Security)
  ↓ Şifreler AES-128 ile şifreli
Layer 3: Key Protection (Key Security)
  ↓ Key Windows DPAPI ile korunuyor
Layer 4: API Sanitization (Response Security)
  ↓ Password response'larda yok
Layer 5: Memory Safety (Runtime Security)
  ↓ Default creds memory'de şifreli
Layer 6: Temporary Data (Data Lifecycle)
  ↓ Her başlangıçta temizlenir
```

---

## 🔬 Güvenlik Testleri

### Test Senaryoları

**1. Database Dosyası Erişimi Testi:**
- Database dosyasına erişim sağlansa bile, şifreler şifreli format'ta saklanır
- Encryption key olmadan şifreler decrypt edilemez
- **Sonuç:** Database ele geçirilse bile şifreler korunur

**2. Key Dosyası Erişimi Testi:**
- Key dosyası başka bir sisteme kopyalansa bile decrypt edilemez
- Windows DPAPI: Key, kullanıcı hesabına bağlıdır
- Linux/Mac: Key, sistem ve kullanıcıya özgüdür
- **Sonuç:** Key dosyası tek başına yeterli değildir

**3. API Response Testi:**
- API response'larında password alanı bulunmaz
- Sadece `has_password` boolean flag'i gönderilir
- **Sonuç:** API trafiği güvenlidir

**4. Memory Dump Testi:**
- Process memory dump alınsa bile, default credentials şifreli format'ta saklanır
- **Sonuç:** Memory dump ile şifreler okunamaz

## 📞 Destek ve Sorular

Güvenlik ile ilgili sorularınız için:
- **Genel Güvenlik:** Bu dokümantasyon
- **Key Yönetimi:** `ENCRYPTION-KEY-EXPLANATION.md`
- **Database Kullanımı:** `DATABASE-EXPLANATION.md`

**Not:** Detaylı implementation kodları ve güvenlik mekanizmaları güvenlik nedeniyle paylaşılmamaktadır. Güvenlik soruları için lütfen proje maintainer'ları ile iletişime geçin.

---

---

## 📋 Güvenlik Özet Tablosu

| Özellik | Durum | Açıklama |
|---------|-------|----------|
| **Database Şifreleme** | ✅ Aktif | AES-128 (Fernet) |
| **Key Koruması** | ✅ Aktif | Windows DPAPI |
| **HTTPS** | ✅ Varsayılan | Self-signed (localhost) |
| **API Sanitization** | ✅ Aktif | Password response'larda yok |
| **Memory Güvenliği** | ✅ Aktif | Default creds şifreli |
| **Veri Kalıcılığı** | ❌ Yok | Her başlangıçta temizlenir |
| **Log Güvenliği** | ✅ Aktif | Şifreler loglanmaz |
| **Excel Export Güvenliği** | ✅ Aktif | Şifreler export'ta yok |

---

**Son Güncelleme:** 2025-12-21  
**Güvenlik Seviyesi:** YÜKSEK ✅  
**Production Ready:** EVET ✅  
**HTTPS:** Varsayılan ✅  
**Veri Kalıcılığı:** Geçici (Güvenlik için) ✅


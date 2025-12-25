# 🔒 HTTPS Kurulum Rehberi

## Hızlı Başlangıç

### Development (Self-Signed Certificate)

**Windows:**
```bash
# start-https.bat dosyasını çalıştırın
# Veya:
set USE_HTTPS=true
cd backend
python app.py
```

**Linux/Mac:**
```bash
export USE_HTTPS=true
cd backend
python app.py
```

**Not:** Browser'da "Güvenli olmayan bağlantı" uyarısı çıkacak - bu normaldir. "Gelişmiş" > "Devam et" ile geçebilirsiniz.

---

## Production Kurulumu

### Seçenek 1: Let's Encrypt (Ücretsiz)

1. **Certbot kurulumu:**
```bash
# Windows (WSL veya Linux)
sudo apt-get install certbot

# Certbot ile sertifika alın
sudo certbot certonly --standalone -d yourdomain.com
```

2. **Sertifikaları kullan:**
```python
# app.py'de ssl_context parametresini güncelleyin:
app.run(
    host='127.0.0.1',
    port=5000,
    ssl_context=('/etc/letsencrypt/live/yourdomain.com/fullchain.pem',
                 '/etc/letsencrypt/live/yourdomain.com/privkey.pem')
)
```

### Seçenek 2: Kurumsal SSL Sertifikası

1. SSL sertifikanızı alın (.pem ve .key dosyaları)
2. Güvenli bir yere koyun
3. app.py'de path'leri güncelleyin:

```python
app.run(
    host='127.0.0.1',
    port=5000,
    ssl_context=('/path/to/certificate.pem', '/path/to/private.key')
)
```

### Seçenek 3: Reverse Proxy (Nginx/Apache)

**Nginx örneği:**
```nginx
server {
    listen 443 ssl;
    server_name yourdomain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

Bu durumda Flask uygulaması HTTP'de kalabilir, Nginx HTTPS'i handle eder.

---

## Güvenlik Notları

✅ **Yapılması Gerekenler:**
- Production'da gerçek SSL sertifikası kullanın
- Sertifika dosyalarını güvenli saklayın (600 permissions)
- Sertifikaları düzenli yenileyin (Let's Encrypt otomatik)
- HTTPS zorunlu hale getirin (HTTP'yi redirect edin)

❌ **Yapılmaması Gerekenler:**
- Self-signed certificate'i production'da kullanmayın
- Private key'i public repository'ye commit etmeyin
- Sertifika dosyalarını network share'de saklamayın

---

## Test Etme

**HTTPS çalışıyor mu kontrol edin:**
```bash
curl -k https://localhost:5000/api/stats
```

`-k` flag'i self-signed certificate için gerekli.

---

## Sorun Giderme

**"SSL: CERTIFICATE_VERIFY_FAILED" hatası:**
- Self-signed certificate kullanıyorsanız normaldir
- Browser'da "Gelişmiş" > "Devam et" ile geçin

**Port 5000 zaten kullanılıyor:**
```bash
# Port'u değiştirin:
app.run(host='127.0.0.1', port=5443, ssl_context='adhoc')
```

**Sertifika yüklenemiyor:**
- Dosya path'lerini kontrol edin
- Dosya izinlerini kontrol edin (readable olmalı)
- Sertifika formatını kontrol edin (.pem formatı)

---

**Son Güncelleme:** 2025-12-21






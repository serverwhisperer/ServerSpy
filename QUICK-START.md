# 🚀 ServerScout - Hızlı Başlangıç

## ⚡ En Hızlı Yol (Desktop App)

1. **Node.js kurulumu** (eğer yoksa): https://nodejs.org
2. **Bağımlılıkları yükle:**
   ```bash
   cd electron
   npm install
   ```
3. **Çalıştır:**
   ```bash
   npm start
   ```
   Veya Windows'ta `start.bat` dosyasına çift tıklayın

**Hepsi bu kadar!** Uygulama otomatik olarak:
- ✅ Backend server'ı başlatır
- ✅ HTTPS ile güvenli bağlantı kurar
- ✅ Desktop window'u açar
- ✅ Browser'a gerek yok

## 📋 Özellikler

- **Desktop App:** Electron tabanlı, browser gerekmez
- **HTTPS:** Varsayılan olarak şifreli bağlantı
- **Geçici Veri:** Her başlangıçta temiz database
- **Güvenli:** Şifreler AES-128 ile şifreli
- **Hızlı:** Paralel tarama (100+ sunucu destekler)

## 🔧 Gereksinimler

- **Python 3.11+** (backend için)
- **Node.js 18+** (Electron için)
- **Windows/Linux/Mac** (Windows öncelikli)

## 📖 Detaylı Dokümantasyon

- **README.md** - Genel bilgiler
- **SECURITY.md** - Güvenlik detayları
- **PROJECT-STRUCTURE.md** - Kod yapısı
- **BUILD.md** - Build rehberi

## ❓ Sorun Giderme

**Electron başlamıyor:**
- Node.js kurulu mu kontrol edin
- `npm install` çalıştırın
- Backend bağımlılıklarını kontrol edin (`pip install -r backend/requirements.txt`)

**HTTPS uyarısı:**
- Normal! Self-signed certificate için
- Electron otomatik kabul eder
- Browser'da "Gelişmiş" > "Devam et"

**Backend hatası:**
- Python kurulu mu?
- Bağımlılıklar yüklü mü? (`pip install -r backend/requirements.txt`)
- Port 5000 kullanımda mı?

---

**Hızlı yardım:** GitHub Issues veya dokümantasyon dosyalarına bakın.





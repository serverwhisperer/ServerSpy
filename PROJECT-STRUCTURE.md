# 📁 ServerScout - Proje Yapısı

## 🎯 Genel Bakış

ServerScout, modüler ve organize bir yapıya sahiptir. Her modül kendi sorumluluğunu üstlenir.

## 📂 Dizin Yapısı

```
serverspy/
├── backend/                 # Backend (Python/Flask)
│   ├── app.py              # Ana Flask uygulaması (API routes)
│   ├── config.py           # Konfigürasyon ayarları
│   ├── database.py         # Database işlemleri (SQLite)
│   ├── encryption.py       # Şifreleme modülü (AES-128)
│   ├── scanner.py          # Tarama modülü (Windows/Linux)
│   ├── excel_export.py     # Excel export modülü
│   └── requirements.txt    # Python bağımlılıkları
│
├── frontend/               # Frontend (HTML/CSS/JS)
│   ├── index.html          # Ana sayfa
│   ├── style.css           # Stil dosyası
│   └── script.js           # JavaScript logic
│
├── electron/               # Electron Desktop App
│   ├── main.js             # Electron main process
│   ├── package.json        # Node.js dependencies
│   └── icon.ico            # Uygulama ikonu
│
├── data/                   # Database dosyaları (gitignore)
│   └── inventory.db        # SQLite database
│
├── logs/                   # Log dosyaları (gitignore)
│   └── serverscout_*.log   # Günlük log dosyaları
│
└── docs/                   # Dokümantasyon
    ├── README.md           # Ana dokümantasyon
    ├── SECURITY.md         # Güvenlik dokümantasyonu
    ├── BUILD.md            # Build rehberi
    └── PROJECT-STRUCTURE.md # Bu dosya
```

## 🔧 Modül Açıklamaları

### Backend Modülleri

#### `app.py` - Ana Flask Uygulaması
**Sorumluluk:** API endpoint'leri, routing, request handling

**İçerik:**
- Flask app initialization
- API routes (servers, projects, scan, export)
- Static file serving
- Error handling

**Bağımlılıklar:**
- `database.py` - Veri işlemleri
- `scanner.py` - Tarama işlemleri
- `excel_export.py` - Excel export
- `encryption.py` - Şifreleme

#### `config.py` - Konfigürasyon
**Sorumluluk:** Tüm konfigürasyon ayarları

**İçerik:**
- Path configurations
- Server settings
- Database settings
- Scanning parameters

#### `database.py` - Database İşlemleri
**Sorumluluk:** SQLite database işlemleri

**İçerik:**
- Database initialization
- CRUD operations (servers, projects)
- Data encryption/decryption integration
- Query functions

**Özellikler:**
- Veriler geçici (her başlangıçta temizlenir)
- Şifreler şifreli saklanır
- Transaction support

#### `encryption.py` - Şifreleme Modülü
**Sorumluluk:** Password encryption/decryption

**İçerik:**
- AES-128 (Fernet) encryption
- Windows DPAPI key protection
- Key management
- Password sanitization

**Özellikler:**
- Industry-standard encryption
- Windows DPAPI integration
- Memory-safe operations

#### `scanner.py` - Tarama Modülü
**Sorumluluk:** Server tarama işlemleri

**İçerik:**
- WindowsScanner (WinRM)
- LinuxScanner (SSH)
- OS detection
- Parallel scanning

**Özellikler:**
- Multi-threaded scanning
- Timeout handling
- Error recovery

#### `excel_export.py` - Excel Export
**Sorumluluk:** Excel rapor oluşturma

**İçerik:**
- Excel file generation
- Report formatting
- Comparison reports
- Multi-sheet support

### Frontend Modülleri

#### `index.html` - Ana Sayfa
**Sorumluluk:** UI structure

#### `style.css` - Stil Dosyası
**Sorumluluk:** Görsel tasarım

#### `script.js` - JavaScript Logic
**Sorumluluk:**
- API calls
- UI interactions
- Data rendering
- Event handling

### Electron Modülleri

#### `main.js` - Electron Main Process
**Sorumluluk:**
- Backend server başlatma
- Window management
- Process lifecycle
- Certificate handling

## 🔄 Veri Akışı

```
User Action (Frontend)
    ↓
API Request (HTTP/HTTPS)
    ↓
Flask Route Handler (app.py)
    ↓
Business Logic (database.py, scanner.py, etc.)
    ↓
Database (SQLite) - Geçici
    ↓
Response (JSON)
    ↓
Frontend Update
```

## 🔐 Güvenlik Katmanları

1. **HTTPS** - Tüm trafik şifreli
2. **Database Encryption** - Şifreler AES-128 ile şifreli
3. **Key Protection** - Windows DPAPI ile key korunuyor
4. **API Sanitization** - Response'larda password yok
5. **Memory Safety** - Default credentials memory'de şifreli

## 📊 Veri Yaşam Döngüsü

```
1. Uygulama Başlar
   ↓
2. Database Temizlenir (clear_all_data)
   ↓
3. Kullanıcı Sunucu Ekler → Database'e Kaydedilir (şifreli)
   ↓
4. Tarama Yapılır → Sonuçlar Database'e Kaydedilir
   ↓
5. Excel Export → Database'den Veri Okunur
   ↓
6. Uygulama Kapanır → Bir Sonraki Başlangıçta Temizlenir
```

## 🛠️ Geliştirme Notları

### Yeni Özellik Ekleme

1. **Backend:** `app.py`'ye yeni route ekle
2. **Business Logic:** İlgili modüle fonksiyon ekle
3. **Frontend:** `script.js`'e API call ekle
4. **UI:** `index.html` ve `style.css`'i güncelle

### Modül Bağımlılıkları

```
app.py
├── config.py
├── database.py
│   └── encryption.py
├── scanner.py
├── excel_export.py
└── encryption.py
```

### Test Etme

```bash
# Backend test
cd backend
python app.py

# Electron test
cd electron
npm start

# Build
npm run build
```

## 📝 Notlar

- **Veriler Kalıcı Değil:** Her başlangıçta database temizlenir
- **HTTPS Varsayılan:** Tüm bağlantılar şifreli
- **Electron Desktop App:** Browser gerekmez
- **Modüler Yapı:** Her modül bağımsız test edilebilir

---

**Son Güncelleme:** 2025-12-21





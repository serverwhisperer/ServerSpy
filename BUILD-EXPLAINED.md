# ServerScout Build Açıklamaları

## 📦 Build Çıktıları

### 1. **ServerScout-Portable-1.2.0.exe** ✅ (KULLANILACAK)
- **Ne bu?** Portable (taşınabilir) versiyon
- **Nasıl çalışır?** Tek EXE dosyası, kurulum gerektirmez
- **Neden EXE?** Electron-builder portable'ı Windows'ta tek EXE olarak paketler
- **Kullanım:** USB'ye kopyalayıp çalıştırabilirsiniz
- **Veri:** AppData'da saklanır (kullanıcı verileri)

### 2. **ServerScout-Setup-1.2.0.exe** ✅ (KULLANILACAK)
- **Ne bu?** Windows Installer
- **Nasıl çalışır?** Kurulum sihirbazı ile Program Files'a kurar
- **Kullanım:** Çift tıklayıp kurulum yapın
- **Özellikler:** Desktop shortcut, Start Menu shortcut oluşturur

### 3. **win-unpacked/** ❌ (SİLİNEBİLİR)
- **Ne bu?** Electron-builder'ın ara çıktısı (intermediate output)
- **Neden var?** Builder önce tüm dosyaları buraya çıkarır, sonra EXE'ye paketler
- **Kullanım:** Gerekmez, silebilirsiniz
- **Not:** İçinde `ServerScout.exe` var, çalıştırılabilir ama dağıtım için kullanılmaz

### 4. **Diğer dosyalar** (.blockmap, .yml)
- Build metadata dosyaları
- Gerekli değil, silebilirsiniz

## 🔄 Build Süreci

```
1. Backend Build (Python → EXE)
   └─> backend/dist/serverscout-backend.exe

2. Electron Build
   ├─> win-unpacked/ (ara çıktı - silinebilir)
   ├─> ServerScout-Portable-1.2.0.exe ✅
   └─> ServerScout-Setup-1.2.0.exe ✅
```

## ❓ Sık Sorulan Sorular

### Q: Portable neden EXE?
**A:** Windows'ta portable uygulamalar genelde tek EXE olarak dağıtılır. EXE çalıştırıldığında:
- Kendini geçici bir yere çıkarır
- Uygulamayı başlatır
- Kapanınca temizler (bazı dosyalar kalabilir)

### Q: win-unpacked nedir?
**A:** Builder'ın ara çıktısı. Tüm dosyalar buraya çıkarılır, sonra EXE'ye paketlenir. Silebilirsiniz.

### Q: Version 1.0.0 görünüyor?
**A:** Eski build kalmış olabilir. `clean-build.bat` çalıştırıp yeniden build edin.

### Q: Hangi dosyayı dağıtmalıyım?
**A:** 
- **Portable:** `ServerScout-Portable-1.2.0.exe` (tek dosya, kurulum yok)
- **Installer:** `ServerScout-Setup-1.2.0.exe` (kurulumlu versiyon)

## 🧹 Temizlik

Eski build'leri temizlemek için:
```batch
clean-build.bat
```

Veya manuel olarak:
- `electron\dist\` klasörünü silin
- `backend\dist\` klasörünü silin


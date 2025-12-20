# 🚀 GitHub Push Rehberi

## Sorun
GitHub'da build dosyaları (116MB) var ve bu yüzden push yapılamıyor (100MB limit).

## Çözüm: GitHub Web'den Dosya Silme

### Adım 1: GitHub'a Git
1. https://github.com/serverwhisperer/ServerSpy adresine gidin
2. `electron/dist/` klasörüne gidin

### Adım 2: Build Dosyalarını Sil
1. `ServerScout-Portable-1.2.0.exe` dosyasına tıklayın
2. Sağ üstte **"..."** (üç nokta) menüsüne tıklayın
3. **"Delete file"** seçeneğini seçin
4. Commit mesajı: `Remove build file (too large for GitHub)`
5. **"Commit changes"** butonuna tıklayın

6. Aynı işlemi `ServerScout-Setup-1.2.0.exe` için de yapın

### Adım 3: Local'den Push Et
```bash
cd c:\serverspy
git pull origin main  # GitHub'daki değişiklikleri al
git push origin main  # Local commit'leri push et
```

---

## Alternatif: Direkt Upload (Git History Kaybolur)

Eğer git history'yi kaybetmek istemiyorsanız yukarıdaki yöntemi kullanın.

Eğer direkt upload yapmak isterseniz:

1. GitHub'da repository'yi silin (veya yeni branch oluşturun)
2. Tüm dosyaları ZIP olarak hazırlayın
3. GitHub'da "Upload files" butonuna tıklayın
4. Dosyaları sürükleyip bırakın

**⚠️ UYARI:** Bu yöntem git history'yi kaybettirir!

---

## Önerilen Yöntem

**GitHub web'den dosya silme** yöntemini kullanın - git history korunur.

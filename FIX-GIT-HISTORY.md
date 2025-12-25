# 🔧 Git History'den Build Dosyalarını Kaldırma

## Sorun
Git history'de build dosyaları (116MB) var ve GitHub push reddediyor.

## Çözüm: Git History Temizleme

### Yöntem 1: Git Filter-Repo (Önerilen - Modern)

```bash
# Git filter-repo kurulumu (ilk kez)
pip install git-filter-repo

# Build dosyalarını history'den kaldır
git filter-repo --path electron/dist/ServerScout-Portable-1.2.0.exe --invert-paths
git filter-repo --path electron/dist/ServerScout-Setup-1.2.0.exe --invert-paths

# Force push (dikkatli!)
git push origin main --force
```

### Yöntem 2: BFG Repo-Cleaner (Kolay)

1. BFG indir: https://rtyley.github.io/bfg-repo-cleaner/
2. Çalıştır:
```bash
java -jar bfg.jar --delete-files "ServerScout-*.exe" .
git reflog expire --expire=now --all
git gc --prune=now --aggressive
git push origin main --force
```

### Yöntem 3: GitHub'da Sil + Force Push (Basit)

1. **GitHub'da dosyaları sil:**
   - https://github.com/serverwhisperer/ServerSpy
   - `electron/dist/` klasörüne git
   - Her iki .exe dosyasını sil

2. **Local'de history temizle:**
```bash
cd c:\serverspy
git filter-branch --force --index-filter "git rm --cached --ignore-unmatch electron/dist/*.exe" --prune-empty --tag-name-filter cat -- --all
git push origin main --force
```

⚠️ **UYARI:** Force push git history'yi değiştirir! Ekip çalışması varsa dikkatli olun.

---

## En Basit Çözüm (Önerilen)

**GitHub'da dosyaları silin, sonra:**

```bash
cd c:\serverspy
git pull origin main
git push origin main
```

Eğer hala hata verirse, o zaman history temizleme gerekir.





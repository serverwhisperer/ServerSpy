# 🔑 Encryption Key Açıklaması

## Key Nasıl Oluşuyor?

### Otomatik Oluşuyor - Kullanıcı Müdahalesi GEREKMEZ! ✅

**İlk Çalıştırmada:**
1. Uygulama ilk kez çalıştığında otomatik olarak yeni bir key oluşturur
2. Key rastgele (random) oluşturulur - Fernet.generate_key()
3. Key Windows DPAPI ile şifrelenir ve kaydedilir
4. **Kullanıcı hiçbir şey yapmaz, her şey otomatik!**

### Key Nerede Saklanıyor?

**Windows:**
- Konum: `%APPDATA%\ServerScout\data\.encryption_key`
- Koruma: Windows DPAPI ile şifreli
- Sadece aynı Windows kullanıcı hesabı decrypt edebilir

**Linux/Mac:**
- Konum: `data/.encryption_key`
- Koruma: Sistem bazlı master key ile şifreli

### Key'i Kullanıcı Oluşturuyor mu?

**HAYIR!** Tamamen otomatik:
- İlk çalıştırmada otomatik oluşturulur
- Her kullanıcı için farklı key (Windows kullanıcı bazlı)
- Key'i manuel oluşturmanıza gerek yok
- Key'i hatırlamanıza gerek yok
- Key'i yedeklemenize gerek yok (Windows DPAPI otomatik yönetiyor)

### Key Kaybolursa Ne Olur?

**Windows'ta:**
- Key Windows kullanıcı profili ile bağlantılı
- Kullanıcı değişirse → Yeni key oluşturulur (eski şifreler decrypt edilemez)
- Kullanıcı aynı kalırsa → Key otomatik decrypt edilir

**Önemli:**
- Key dosyasını silerseniz → Yeni key oluşturulur, eski şifreler decrypt edilemez
- Key dosyasını kopyalarsanız → Başka bilgisayarda çalışmaz (Windows DPAPI farklı)

### Kullanıcının Yapması Gereken Bir Şey Var mı?

**HAYIR!** Hiçbir şey yapmanıza gerek yok:
- ✅ Key otomatik oluşturulur
- ✅ Key otomatik korunur
- ✅ Key otomatik yüklenir
- ✅ Key otomatik decrypt edilir

**Sadece dikkat edin:**
- Key dosyasını silmeyin
- Key dosyasını başka yere taşımayın
- Windows kullanıcı hesabınızı değiştirmeyin (key o kullanıcıya bağlı)

---

**Özet:** Key tamamen otomatik, kullanıcı müdahalesi gerektirmez. Sadece uygulamayı çalıştırın, gerisi otomatik!


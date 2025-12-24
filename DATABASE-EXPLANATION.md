# 📊 Database Kullanımı Açıklaması

## Neden Database Kullanılıyor?

ServerScout, **geçici** bir database kullanıyor. Veriler **kalıcı değil**, sadece uygulama çalışırken geçici olarak saklanıyor.

### Database'in Kullanım Amacı:

1. **Sunucu Listesi Yönetimi**
   - Kullanıcı sunucu eklerken (IP, credentials)
   - Sunucuları düzenleme/silme
   - Proje bazlı gruplama

2. **Tarama Sonuçlarını Saklama**
   - Her sunucu için tarama sonuçları (CPU, RAM, Disk, vb.)
   - Son tarama zamanı
   - Online/Offline durumu

3. **Excel Export İçin Veri Toplama**
   - Tüm sunucuların bilgilerini bir araya getirme
   - İstatistikler (toplam, online, offline sayıları)
   - Karşılaştırma raporları için

### Veri Yaşam Döngüsü:

```
1. Uygulama başlar
   ↓
2. Database temizlenir (clear_all_data())
   ↓
3. Kullanıcı sunucu ekler → Database'e kaydedilir
   ↓
4. Tarama yapılır → Sonuçlar database'e kaydedilir
   ↓
5. Excel export yapılır → Database'den veri okunur
   ↓
6. Uygulama kapanır → Database temizlenir (bir sonraki başlangıçta)
```

### Güvenlik:

- ✅ **Veriler kalıcı değil** - Her başlangıçta silinir
- ✅ **Şifreler şifreli** - Database'de AES-128 ile şifreli
- ✅ **Sadece localhost** - Sadece yerel erişim
- ✅ **HTTPS** - Tüm trafik şifreli

### Alternatif: In-Memory Storage

Eğer database kullanmak istemiyorsanız, in-memory (RAM'de) saklama yapabiliriz:

**Avantajlar:**
- Database dosyası oluşturulmaz
- Daha hızlı (RAM'de)
- Uygulama kapanınca otomatik silinir

**Dezavantajlar:**
- Uygulama çökerse veriler kaybolur
- Çok fazla sunucu varsa RAM kullanımı artar
- Excel export için verileri toplamak daha karmaşık

### Mevcut Durum:

**Database kullanılıyor çünkü:**
- Çok sayıda sunucu için daha verimli
- Excel export için kolay veri toplama
- Proje bazlı yönetim için uygun
- Veriler zaten geçici (her başlangıçta siliniyor)

**İsterseniz in-memory'ye geçebiliriz**, ama şu anki yapı production için uygun.

---

**Sonuç:** Database sadece **geçici veri saklama** için kullanılıyor. Veriler **kalıcı değil**, her uygulama başlangıcında temizleniyor. Güvenlik açısından sorun yok.





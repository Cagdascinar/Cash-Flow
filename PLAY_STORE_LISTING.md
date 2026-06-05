# Kirpi Finans — Play Store Mağaza Metinleri

## Uygulama Adı (30 karakter maks)
Kirpi Finans

## Kısa Açıklama (80 karakter maks)
Gelir, gider, yatırım ve bütçenizi tek uygulamada kolayca takip edin.

## Tam Açıklama (4000 karakter maks)

Kirpi Finans, kişisel ve kurumsal nakit akışınızı yönetmenin en akıllı yolu.

**💰 Temel Özellikler**
• Gelir ve gider takibi — kategori bazlı, anlık
• Çoklu hesap yönetimi (banka, nakit, döviz)
• Kredi kartı borç ve ekstre takibi
• Bütçe limitleri ve uyarıları
• Aylık / yıllık finansal özet

**📈 Yatırım Portföyü**
• Hisse senedi, yatırım fonu, döviz ve altın takibi
• TEFAS fon kodu ile otomatik fiyat çekme
• Kar/zarar hesaplama
• Temettü ve gelir kayıt

**🏢 Kurumsal Özellikler**
• Tedarikçi yönetimi
• Fatura takibi ve vade analizi
• Varlık (demirbaş) kaydı ve amortisman hesaplama
• Bakım gider takibi

**🤖 Akıllı Özellikler**
• AI destekli harcama analizi ve tasarruf önerileri
• Telegram botu ile konuşarak işlem girme
• Tekrarlayan işlem otomasyonu
• Kur takibi (USD, EUR, Altın ve daha fazlası)
• Günlük hatırlatıcılar

**🔒 Güvenlik & Gizlilik**
• Verileriniz şifreli ve güvende
• KVKK uyumlu
• Hesap silme hakkı
• Açık kaynak sunucu kodu

**📱 Çoklu Profil**
• Hem kişisel hem şirket hesabınızı ayrı profillerle yönetin
• Veriler profiller arasında tamamen bağımsız

**📤 Dışa Aktarma**
• Excel ve PDF rapor çıktısı (Premium)

---

## Kategoriler
- Finans

## İçerik Derecelendirmesi
- Herkes (Everyone)
- Şiddet: Yok
- Yetişkin içerik: Yok

## Gizlilik Politikası URL
https://web-production-ba700.up.railway.app/gizlilik

## Uygulama Erişim Bilgileri (Review için)
Bir test hesabı oluşturarak giriş yapabilirsiniz.
Kayıt olmak için e-posta ve şifre gerekmektedir.

---

## Sürüm Notları (1.0.0 için)
İlk sürüm. Tüm temel özellikler kullanıma hazır.

---

## Görseller Gerekenler (Manuel yapılacak)
- [ ] Uygulama ikonu: 512×512 px PNG (mevcut: assets/icon.png)
- [ ] Feature Graphic: 1024×500 px JPG/PNG
- [ ] Telefon ekran görüntüleri: En az 2, en fazla 8 (1080×1920 px)
  - Ekran 1: Ana Sayfa — kişisel karşılama + bakiye
  - Ekran 2: İşlem Ekleme
  - Ekran 3: Bütçe & Hedefler
  - Ekran 4: Yatırımlar
  - Ekran 5: Kredi Kartları

---

## EAS Build Adımları
```bash
# 1. EAS login
eas login

# 2. Test APK (internal test)
cd mobile
eas build --profile preview --platform android

# 3. Production AAB (Play Store)
eas build --profile production --platform android

# 4. Submit to Play Store (otomatik)
eas submit --profile production --platform android
# NOT: google-service-account.json gerekli (Play Console > API access)
```

## Play Console Adımları
1. play.google.com/console → Uygulama Oluştur
2. Paket adı: com.kirpi.cashflow
3. AAB yükle (Internal testing)
4. Mağaza listesini doldur (bu dosyadan)
5. İçerik derecelendirmesi anketi (Finance, no violence)
6. Gizlilik politikası URL gir
7. Fiyatlandırma: Ücretsiz
8. Production'a geçmeden önce internal test yap

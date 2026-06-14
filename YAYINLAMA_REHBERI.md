# Kirpi Finans — App Store Yayınlama Rehberi

## Ön Koşullar

| Gereksinim | Maliyet | Link |
|---|---|---|
| Apple Developer Hesabı | $99/yıl | developer.apple.com/enroll |
| Mac veya EAS Build (cloud) | Ücretsiz (EAS Free tier) | expo.dev |
| Expo hesabı | Ücretsiz | expo.dev/signup |

---

## ADIM 1 — Apple Developer Hesabı Aç

1. https://developer.apple.com/enroll adresine git
2. "Enroll" → Individual (şahıs) veya Company seç
3. $99 ödeme yap (yıllık otomatik yenilenir)
4. Apple ID ile giriş yap → D-U-N-S numarası (şirket için) veya kimlik doğrulama

---

## ADIM 2 — App Store Connect'te Uygulama Oluştur

1. https://appstoreconnect.apple.com adresine git
2. "My Apps" → "+" → "New App"
3. Şunları doldur:
   - **Name:** Kirpi Finans
   - **Primary Language:** Turkish
   - **Bundle ID:** com.kirpi.cashflow ← Apple Developer'dan oluşturulacak
   - **SKU:** KIRPI001

### Bundle ID oluşturma:
1. https://developer.apple.com/account → Certificates, IDs & Profiles
2. Identifiers → "+" → App IDs
3. Bundle ID: `com.kirpi.cashflow`
4. Capabilities: Push Notifications, Sign In with Apple (opsiyonel)

---

## ADIM 3 — EAS Build ile iOS .ipa Oluştur

Terminalde (bilgisayarında):

```bash
cd /path/to/cash-flow/mobile

# EAS CLI kur (bir kez)
npm install -g eas-cli

# Expo hesabına giriş yap
eas login

# iOS production build başlat
eas build --platform ios --profile production
```

Bu komut:
- Expo'nun cloud sunucularında (~20-30 dk) build alır
- Apple kimlik bilgilerini sorar (Xcode hesabı yoksa EAS yönetebilir)
- Biten build'i Expo dashboard'da görebilirsin

---

## ADIM 4 — App Store Connect'e Gönder

Build bittikten sonra:

```bash
# TestFlight'a yükle (önce iç test)
eas submit --platform ios --profile production

# eas.json'daki appleId doğru olmalı: cagdascnr2441@gmail.com
# ascAppId: App Store Connect'teki uygulama ID'si (10 haneli sayı)
```

Ya da Expo dashboard'dan manuel upload:
1. expo.dev → Builds → iOS build'e tıkla
2. "Submit to App Store" butonuna bas

---

## ADIM 5 — App Store Connect'te Metadata Doldur

APPSTORE_LISTING.md dosyasındaki içerikleri kopyala:
- Açıklama, anahtar kelimeler
- Destek URL, gizlilik politikası URL
- Yaş sınırı ayarları
- Kategori seç

---

## ADIM 6 — Ekran Görüntüleri Hazırla

### Seçenek A: Gerçek cihazda
iPhone Pro Max alarak ekran görüntüsü al (1320×2868px)

### Seçenek B: Simulator (ücretsiz, Mac gerekli)
```bash
# Xcode Simulator aç
# iPhone 16 Pro Max seç
# Uygulamayı çalıştır
# Hardware → Screenshot (Cmd+S)
```

### Seçenek C: AppMockUp / Shottr gibi araç
- canva.com/mockups veya AppLaunchpad'de şablon kullan
- Ekran görüntüsüne çerçeve ekle

En az **3 adet** 6.9" ekran görüntüsü zorunlu.

---

## ADIM 7 — TestFlight ile İç Test

1. App Store Connect → TestFlight sekmesi
2. "Internal Testing" → "Add Testers"
3. kendi e-postanı ekle
4. iPhone'a TestFlight indir → davet mailini kabul et
5. Uygulamayı test et

---

## ADIM 8 — İncelemeye Gönder

1. App Store Connect → "App Store" sekmesi
2. "Submit for Review" butonuna bas
3. İnceleme notlarını doldur (APPSTORE_LISTING.md'den)
4. Ortalama **24-48 saat** içinde onaylanır

---

## Sık Reddedilme Sebepleri ve Önlemleri

| Red Sebebi | Önlem |
|---|---|
| Gizlilik politikası yok | ✅ /gizlilik sayfası mevcut |
| Test hesabı eksik | ✅ İnceleme notlarına ekledik |
| Kırık linkler | Railway app aktif olmalı |
| Eksik işlevsellik | Tüm özellikler çalışır olmalı |
| Sahte para transferi | Uygulama sadece takip yapıyor, transfer etmiyor ✅ |

---

## eas.json'da Doldurulması Gereken Alanlar

```json
"ios": {
  "appleId": "cagdascnr2441@gmail.com",  ← ✅ dolu
  "ascAppId": "BURAYA_APP_ID",           ← App Store Connect'ten al
  "appleTeamId": "BURAYA_TEAM_ID"        ← developer.apple.com'dan al
}
```

Team ID: https://developer.apple.com/account → Membership → Team ID

---

## Tahmini Süre

| Adım | Süre |
|---|---|
| Apple Developer kayıt | 1-3 gün (kimlik doğrulama) |
| Build | 20-30 dakika |
| Metadata + ekran görüntüleri | 2-3 saat |
| App Store incelemesi | 24-48 saat |
| **Toplam** | **~4-5 gün** |

---

## Google Play (Bonus)

```bash
# Android AAB build (aynı anda yapılabilir)
eas build --platform android --profile production

# Play Console'a gönder
eas submit --platform android --profile production
# google-service-account.json gerekli (Play Console → Setup → API access)
```

Google Play incelemesi genellikle **3-7 gün** sürer.

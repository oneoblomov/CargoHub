# 🚚 FastShip Kargo Takip Sistemi

Modern, AI destekli kargo takip sistemi. Gemma-2B-IT modeli ile akıllı müşteri hizmetleri asistanı.

## ✨ Özellikler

### 🎯 Ana Özellikler

- **🔐 Güvenli Kullanıcı Girişi** - Kişisel hesap sistemi
- **🤖 AI Müşteri Hizmetleri** - Gemma AI ile akıllı yanıtlar
- **📦 Detaylı Kargo Takibi** - Gerçek zamanlı durum güncellemeleri
- **🔄 İade & İptal İşlemleri** - AI ile kolay iade ve iptal
- **📊 İstatistik Dashboard** - Kargo analizi ve raporlar
- **🔍 Akıllı Arama** - Ürün adı veya takip numarası ile arama
- **📱 Mobil Uyumlu** - Responsive tasarım
- **💬 Chat Geçmişi** - Sohbet kayıtları ve dışa aktarma
- **🗃️ Veritabanı Görüntüleyici** - Admin paneli ile veri yönetimi

### 🏢 Gerçek Dünya Uygunluğu

- **Türkiye Odaklı** - Yerel kargo firmaları ve şehirler
- **Çoklu Kullanıcı** - Farklı müşteri profilleri
- **Detaylı Kargo Bilgileri** - Ağırlık, boyut, sigorta durumu
- **Tracking History** - Kargo hareket geçmişi
- **Müşteri Hizmetleri** - 7/24 destek bilgileri

## 🚀 Kurulum ve Çalıştırma

### 1. Gereksinimler

```bash
# Ana ortam
conda create -n rapids-25.08 python=3.12
conda activate rapids-25.08

# Gerekli paketler
pip install streamlit transformers huggingface_hub faker
```

### 2. Veritabanı Kurulumu

```bash
# SQLite veritabanını oluştur ve örnek verilerle doldur
python setup_database.py
```

Bu komut:
- Rastgele 20 kullanıcı ve 57 kargo ile örnek veri üretir
- SQLite veritabanını oluşturur (`cargo_database.db`)
- Verileri aktarır

### 3. HuggingFace Token Ayarlama

```bash
# Terminal/Command Prompt
export HF_TOKEN='your_huggingface_token_here'

# Veya .env dosyası oluşturun
echo "HF_TOKEN=your_token" > .env
```

### 4. Uygulamayı Çalıştırma

#### Ana Uygulama

##### VS Code Görevi ile

1. `Ctrl+Shift+P` → "Tasks: Run Task"
2. "Run Streamlit App" seçin

##### Manuel Çalıştırma

```bash
conda activate rapids-25.08
cd /path/to/project
streamlit run cargo_app.py
```

#### Veritabanı Görüntüleyici

##### VS Code Görevi ile

1. `Ctrl+Shift+P` → "Tasks: Run Task"
2. "Run Database Viewer" seçin

##### Manuel Çalıştırma

```bash
conda activate rapids-25.08
cd /path/to/project
streamlit run db_viewer.py
```

### 5. Tarayıcıda Erişim

- **Local URL:** <http://localhost:8501>
- **Network URL:** <http://10.209.149.74:8501>

## 👥 Demo Kullanıcıları

Veritabanında rastgele üretilmiş 20 demo kullanıcı bulunmaktadır. `setup_database.py` çalıştırılarak yeni veriler üretilebilir.

**Örnek Kullanıcı ID'leri:**
- `user100` - `user999` arası (örnek: user123, user456, user789, user999)

Her kullanıcı için:
- Rastgele isim, email, telefon
- 1-5 arası rastgele kargo
- Farklı durumlar (Hazırlanıyor, Yolda, Teslim edildi, İade İşlemi)
- Detaylı tracking history

## 📋 Kullanım Kılavuzu

### 🔐 Giriş Yapma

1. Ana sayfada kullanıcı ID'nizi girin
2. Demo kullanıcılarından birini seçin
3. Dashboard'a yönlendirileceksiniz

### 📦 Kargo Takibi

- **Kargolarım** sekmesinde tüm kargolarınızı görün
- **Arama** ile spesifik kargo bulun
- **Filtre** ile duruma göre ayırın
- **Detay** butonuna tıklayarak geçmiş hareketleri görün

### 🔄 İade & İptal İşlemleri

- **İade:** Teslim edilmiş kargoları 14 gün içinde iade edebilirsiniz
- **İptal:** Hazırlanıyor durumundaki kargoları iptal edebilirsiniz
- AI asistanına mesaj göndererek işlem başlatın
- Onay verdikten sonra işlem otomatik olarak gerçekleştirilir
- Tüm işlemler takip geçmişi'ne kaydedilir

### 💬 AI Asistan

- Türkçe sorular sorun
- Takip numarası belirtin (örn: "TR123456789 nerede?")
- **İade talebi:** "TR123456789 iade et" veya "TR123456789 döndür"
- **İptal talebi:** "TR123456789 iptal et" (sadece hazırlanıyor durumunda)
- AI size detaylı yanıt verecek ve onayınızı isteyecek

### 📊 İstatistikler

- Toplam kargo sayısı
- Teslim edilme oranları
- Kargo firması dağılımı

### 🗃️ Veritabanı Görüntüleyici

Veritabanı yönetim ve görüntüleme uygulaması (`db_viewer.py`):

#### Özellikler

- **📈 Dashboard** - Genel istatistikler ve özet bilgiler
- **👥 Kullanıcı Yönetimi** - Tüm kullanıcıları görüntüleme ve filtreleme
- **📦 Kargo Takibi** - Kargo detayları ve durum takibi
- **📋 Geçmiş Kayıtları** - Tracking history görüntüleme
- **📥 Veri Dışa Aktarma** - CSV formatında veri indirme
- **🔍 Akıllı Filtreleme** - Durum, tarih ve diğer kriterlere göre filtre

#### Kullanım

1. `db_viewer.py` dosyasını çalıştırın
2. Sol panelden görüntülemek istediğiniz veriyi seçin
3. Filtreler ile veriyi daraltın
4. İndirme butonları ile veriyi dışa aktarın

## 🏗️ Teknik Detaylar

### 🗂️ Proje Yapısı

```
FastShip-Kargo/
├── cargo_app.py          # Ana Streamlit UI uygulaması
├── cargo_chat.py         # Chat bot ve veri erişim modülü
├── db_viewer.py          # Veritabanı görüntüleme ve yönetim uygulaması
├── setup_database.py     # SQLite veritabanı kurulum scripti
├── cargo_database.db     # SQLite veritabanı dosyası
├── cargo_data.json       # Örnek veri dosyası (yedek)
├── .vscode/
│   └── tasks.json        # VS Code görev tanımları
└── README.md            # Bu dosya
```

### 🗃️ Veritabanı Şeması

#### Users Tablosu
```sql
CREATE TABLE users (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT,
    phone TEXT,
    member_since DATE
);
```

#### Cargos Tablosu
```sql
CREATE TABLE cargos (
    tracking_number TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    status TEXT NOT NULL,
    location TEXT,
    last_update DATETIME,
    estimated_delivery DATE,
    description TEXT,
    weight TEXT,
    dimensions TEXT,
    carrier TEXT,
    insurance TEXT,
    return_reason TEXT,
    FOREIGN KEY (user_id) REFERENCES users (id)
);
```

#### Tracking History Tablosu
```sql
CREATE TABLE tracking_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tracking_number TEXT NOT NULL,
    date DATETIME NOT NULL,
    status TEXT NOT NULL,
    location TEXT,
    FOREIGN KEY (tracking_number) REFERENCES cargos (tracking_number)
);
```

### 🤖 AI Model

- **Model:** Google Gemma-2B-IT
- **Dil:** Türkçe
- **Özellik:** Bağlam farkında yanıtlar
- **Token Limit:** 250 token

### 🎨 UI/UX

- **Framework:** Streamlit
- **Tema:** Modern, profesyonel
- **Renkler:** Mavi gradyan teması
- **İkonlar:** Emoji ve SVG
- **Responsive:** Mobil uyumlu

## 🔧 Gelişmiş Özellikler

### 🔍 Akıllı Arama

- Ürün adı ile arama
- Takip numarası ile arama
- Büyük/küçük harf duyarsız

### 📈 Veri Görselleştirme

- Durum dağılımı grafikleri
- İlerleme çubukları
- Metrik kartları

### 💾 Veri Yönetimi

- **Veritabanı:** SQLite3
- **ORM:** Doğrudan SQL sorguları
- **Cache:** Streamlit @st.cache_data decorator
- **Migration:** JSON'dan SQLite'e otomatik geçiş
- **Backup:** Veritabanı dosyasını kopyalayarak yedekleme

### 🔒 Güvenlik

- Kullanıcı bazlı veri izolasyonu
- Güvenli token yönetimi
- Session timeout

## 📞 İletişim

### FastShip Kargo

- 📧 [destek@fastship.com.tr](mailto:destek@fastship.com.tr)
- 📱 0850 123 45 67
- 🕒 08:00 - 24:00 (7/24)
- 📍 İstanbul, Türkiye

## 📝 Lisans

Bu proje eğitim amaçlı geliştirilmiştir.

## 🤝 Katkıda Bulunma

1. Fork edin
2. Feature branch oluşturun (`git checkout -b feature/amazing-feature`)
3. Commit edin (`git commit -m 'Add amazing feature'`)
4. Push edin (`git push origin feature/amazing-feature`)
5. Pull Request açın

---

**🚚 FastShip ile kargolarınız güvende!**

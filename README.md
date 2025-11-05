# 🚚 CargoHub - AI Destekli Kargo Takip Sistemi

Modern, yapay zeka destekli kargo takip sistemi. Google Gemma-2B-IT modeli ile akıllı müşteri hizmetleri asistanı.

## ✨ Özellikler

### 🎯 Ana Özellikler

- **🔐 Güvenli Kullanıcı Girişi** - Kişisel hesap sistemi
- **🤖 AI Müşteri Hizmetleri** - Gemma-2B-IT ile akıllı Türkçe yanıtlar
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
# Ana ortam oluşturma
conda create -n rapids-25.08 python=3.12
conda activate rapids-25.08

# Gerekli paketleri yükleme
pip install -r requirements.txt
```

### 2. HuggingFace Token Ayarlama

```bash
# Terminal/Command Prompt
export HF_TOKEN='your_huggingface_token_here'

# Veya Python ile kontrol
python -c "from huggingface_hub import HfFolder; print('Token:', HfFolder.get_token())"
```

### 3. Veritabanı Kurulumu

```bash
# SQLite veritabanını oluştur ve örnek verilerle doldur
python setup_database.py
```

Bu komut:

- Rastgele 20 kullanıcı ve 57 kargo ile örnek veri üretir
- SQLite veritabanını oluşturur (`cargo_database.db`)
- Verileri aktarır

### 4. Uygulamayı Çalıştırma

#### Ana Uygulama (cargo_app.py)

##### Ana Uygulama için VS Code Görevi

1. `Ctrl+Shift+P` → "Tasks: Run Task"
2. "Run Streamlit App" seçin

##### Ana Uygulama için Manuel Çalıştırma

```bash
conda activate rapids-25.08
cd /path/to/project
streamlit run cargo_app.py
```

#### Veritabanı Görüntüleyici (db_viewer.py)

##### Veritabanı Görüntüleyici için VS Code Görevi

1. `Ctrl+Shift+P` → "Tasks: Run Task"
2. "Run Database Viewer" seçin

##### Veritabanı Görüntüleyici için Manuel Çalıştırma

```bash
conda activate rapids-25.08
cd /path/to/project
streamlit run db_viewer.py
```

### 5. Testleri Çalıştırma

```bash
# Tüm testleri çalıştır (pytest.ini konfigürasyonu ile)
pytest

# Manuel olarak test çalıştır
pytest tests/ -v --tb=short --cov=. --cov-report=xml

# Coverage ile HTML rapor oluştur
pytest tests/ --cov=. --cov-report=html
```

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
CargoHub/
├── cargo_app.py              # Ana Streamlit UI uygulaması
├── cargo_chat.py             # AI chatbot ve veri erişim modülü
├── db_viewer.py              # Veritabanı görüntüleme uygulaması
├── setup_database.py         # SQLite veritabanı kurulum scripti
├── requirements.txt           # Python bağımlılıkları
├── pytest.ini                # Test konfigürasyonu
├── cargo_database.db          # SQLite veritabanı dosyası
├── cargo_data.json            # Örnek veri dosyası (yedek)
├── tests/                     # Test dosyaları
│   ├── conftest.py            # Test fixtures ve mock'lar
│   ├── test_cargo_chat.py     # Chat modülü testleri
│   └── test_setup_database.py # Veritabanı testleri
├── .github/
│   └── workflows/
│       └── ci.yml            # GitHub Actions CI/CD pipeline
└── README.md                 # Bu dosya
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
- **Gereksinim:** HuggingFace token

### 🎨 UI/UX

- **Framework:** Streamlit
- **Tema:** Modern, profesyonel
- **Renkler:** Mavi gradyan teması
- **İkonlar:** Emoji ve SVG
- **Responsive:** Mobil uyumlu

### 🧪 Test Altyapısı

- **Framework:** pytest
- **Konfigürasyon:** pytest.ini
- **Coverage:** pytest-cov
- **Mocking:** unittest.mock, conftest.py
- **CI/CD:** GitHub Actions
- **Test Dosyaları:** `tests/test_*.py`

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
- Güvenli token yönetimi (HF_TOKEN)
- Session timeout

### 🚀 CI/CD Pipeline

GitHub Actions ile otomatik test ve kalite kontrolü:

- **Test Job:** pytest (pytest.ini konfigürasyonu ile)
- **Lint Job:** flake8, black, isort ile kod kalitesi
- **Build Job:** Uygulama build kontrolü
- **Coverage:** Kod coverage raporu (XML + terminal)
- **Secrets:** HF_TOKEN güvenli saklama
- **Python Path:** Otomatik ayarlanır

## 📝 Lisans

Bu proje eğitim amaçlı geliştirilmiştir.

## 🤝 Katkıda Bulunma

1. Fork edin
2. Feature branch oluşturun (`git checkout -b feature/amazing-feature`)
3. Commit edin (`git commit -m 'Add amazing feature'`)
4. Push edin (`git push origin feature/amazing-feature`)
5. Pull Request açın

---

**🚚 CargoHub ile kargolarınız güvende!**

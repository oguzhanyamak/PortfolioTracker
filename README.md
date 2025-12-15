# 📈 TEFAS Portföy Takipçisi

Türkiye Elektronik Fon Alım Satım Platformu (TEFAS) fonlarınızı takip etmek için geliştirilmiş modern bir web uygulaması.

## 🌟 Özellikler

- 📊 **Gerçek Zamanlı Fon Takibi**: TEFAS'tan anlık fon fiyatları
- 💰 **Günlük Performans**: Her fonun günlük kazanç/kayıp analizi
- 🗂️ **Kategori Bazlı Analiz**: Fonları kategorilerine göre gruplandırma
- 📈 **Tarihsel Grafik**: Portföy değerinin zaman içindeki değişimi
- ⚡ **Paralel Veri Çekme**: Hızlı yükleme için optimize edilmiş
- 🎨 **Modern Arayüz**: Kullanıcı dostu ve responsive tasarım

## 🚀 Kurulum

### Gereksinimler
- Python 3.8+

### Yerel Kurulum

```bash
# Repoyu klonlayın
git clone <your-repo-url>
cd PortfolioTracker

# Bağımlılıkları yükleyin
pip install -r requirements.txt

# Uygulamayı başlatın
streamlit run app.py
```

## 📝 Kullanım

1. Sol panelden "Fon Yönetimi" bölümünü kullanarak fonlarınızı ekleyin
2. Fon kodu (örn: TTE, TP2) ve adet bilgilerini girin
3. "Değişiklikleri Kaydet" butonuna tıklayın
4. Portföyünüzün detaylı analizini görüntüleyin

## 🔒 Güvenlik Notu

Bu uygulama kişisel portföy verilerinizi içerir. Public deployment yaparken:
- `funds.json` dosyanızı `.gitignore` ile koruyun
- Private repository kullanın
- Veya authentication ekleyin

## 📦 Teknolojiler

- **Streamlit**: Web arayüzü
- **Pandas**: Veri işleme
- **Plotly**: İnteraktif grafikler
- **Requests + lxml**: Web scraping
- **ThreadPoolExecutor**: Paralel veri çekme

## 📄 Lisans

Bu proje kişisel kullanım içindir.

## 🤝 Katkıda Bulunma

Pull request'ler kabul edilir. Büyük değişiklikler için önce bir issue açın.

---

**Not**: Bu uygulama TEFAS web sitesinden veri çeker. TEFAS'ın kullanım koşullarına uygun kullanın.

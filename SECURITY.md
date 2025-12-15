# 🔐 Güvenlik Ayarları

## Yerel Kullanım

1. `.streamlit/secrets.toml` dosyasını açın
2. `password` değerini güçlü bir parola ile değiştirin:
   ```toml
   password = "sizin-guclu-parolaniz"
   ```

## Streamlit Cloud Deployment

1. Streamlit Cloud dashboard'unuzda uygulamanızı açın
2. "Settings" > "Secrets" bölümüne gidin
3. Şu satırı ekleyin:
   ```toml
   password = "sizin-guclu-parolaniz"
   ```
4. "Save" butonuna tıklayın

## ⚠️ Önemli Notlar

- `secrets.toml` dosyası `.gitignore` ile korunuyor - GitHub'a yüklenmeyecek
- Parolayı kimseyle paylaşmayın
- Güçlü bir parola seçin (en az 12 karakter, harf, rakam ve özel karakter)
- Streamlit Cloud'da secrets değiştiğinde uygulama otomatik yeniden başlar

## 🔄 Oturumu Kapatma

Tarayıcıyı kapatmak veya sayfayı yenilemek oturumu sonlandırır.

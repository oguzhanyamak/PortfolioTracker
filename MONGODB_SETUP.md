# MongoDB Configuration Guide

## Local Development

1. **MongoDB Atlas:**
   - Kullanıcı adı ve şifrenizi hazırlayın
   - Cluster: `cluster0.n4r0v.mongodb.net`
   - Database: `haberDB`

2. **`.streamlit/secrets.toml` dosyasına ekleyin:**
```toml
password = "your-app-password"
mongo_username = "your-mongodb-username"
mongo_password = "your-mongodb-password"
mongo_cluster = "cluster0.n4r0v.mongodb.net"
mongo_db_name = "haberDB"
```

## Streamlit Cloud Deployment

1. Streamlit Cloud Dashboard → Settings → Secrets
2. Aşağıdaki içeriği ekleyin:

```toml
password = "your-app-password"
mongo_username = "your-mongodb-username"
mongo_password = "your-mongodb-password"
mongo_cluster = "cluster0.n4r0v.mongodb.net"
mongo_db_name = "haberDB"
```

## MongoDB Collections

Uygulama otomatik olarak şu collection'ları oluşturacak:
- `funds` - Portföy fonları
- `portfolio_history` - Günlük toplam değer geçmişi

## Test

Yerel olarak test etmek için:
```bash
pip install -r requirements.txt
streamlit run app.py
```

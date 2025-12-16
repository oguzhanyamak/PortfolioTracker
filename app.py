# app.py
import streamlit as st
import pandas as pd
import plotly.express as px
from data_manager import get_portfolio_data, save_daily_total, get_history_df, load_funds, save_all_funds

st.set_page_config(page_title="Portföy Takip", page_icon="📈", layout="wide")

st.title("📈 TEFAS Portföy Takipçisi")

# Custom CSS for better mobile responsiveness
st.markdown(
    """
    <style>
    /* Desktop sidebar */
    @media (min-width: 769px) {
        [data-testid="stSidebar"] {
            min-width: 350px;
            max-width: 500px;
        }
    }
    
    /* Mobile optimizations */
    @media (max-width: 768px) {
        /* Smaller font sizes on mobile */
        .stMarkdown h1 {
            font-size: 1.5rem !important;
        }
        
        .stMarkdown h2 {
            font-size: 1.3rem !important;
        }
        
        .stMarkdown h3 {
            font-size: 1.1rem !important;
        }
        
        /* Better spacing */
        .element-container {
            margin-bottom: 0.5rem !important;
        }
        
        /* Responsive metrics */
        [data-testid="stMetricValue"] {
            font-size: 1.2rem !important;
        }
        
        /* Touch-friendly buttons */
        .stButton button {
            min-height: 44px !important;
            font-size: 0.9rem !important;
        }
        
        /* Compact data editor and tables */
        [data-testid="stDataFrame"] {
            font-size: 0.85rem !important;
        }
        
        /* Ensure sidebar doesn't interfere on mobile */
        [data-testid="stSidebar"] {
            width: auto !important;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Initialize Session State for caching data
if "portfolio_df" not in st.session_state:
    st.session_state.portfolio_df = None

# Initialize authentication state
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

# --- PASSWORD PROTECTION ---
def check_password():
    """Returns True if the user has entered the correct password."""
    
    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if st.session_state["password"] == st.secrets.get("password", "admin123"):
            st.session_state.authenticated = True
            del st.session_state["password"]  # Don't store password
        else:
            st.session_state.authenticated = False

    # Show password input if not authenticated
    if not st.session_state.authenticated:
        st.title("🔐 Portföy Takip Sistemi")
        st.markdown("### Giriş Yapın")
        st.text_input(
            "Parola", 
            type="password", 
            on_change=password_entered, 
            key="password",
            placeholder="Parolanızı girin"
        )
        
        st.info("💡 İpucu: Parolayı `.streamlit/secrets.toml` dosyasında ayarlayabilirsiniz.")
        return False
    else:
        return True

# Check authentication before showing the app
if not check_password():
    st.stop()

# --- MAIN APPLICATION (Only shown if authenticated) ---

with st.sidebar:
    st.header("🛠️ Fon Yönetimi")
    st.info("Aşağıdaki tablodan fonlarınızı düzenleyin, yeni ekleyin veya silin.")
    
    current_funds = load_funds()
    # Convert to DF for editor
    if current_funds:
        df_funds = pd.DataFrame(current_funds)
    else:
        df_funds = pd.DataFrame(columns=["kod", "adet"])

    # Data Editor
    edited_df = st.data_editor(
        df_funds,
        num_rows="dynamic",
        column_config={
            "kod": st.column_config.TextColumn("Fon Kodu", max_chars=3, help="TEFAS Kodu (Örn: TTE)"),
            "adet": st.column_config.NumberColumn("Adet", min_value=0, step=1, format="%d")
        },
        width="stretch",
        hide_index=True,
        key="fund_editor"
    )
    
    # Save Logic
    if st.button("💾 Değişiklikleri Kaydet", type="primary"):
        # Convert back to list of dicts
        new_funds_list = edited_df.to_dict(orient="records")
        save_all_funds(new_funds_list)
        
        # Invalidate cache / Refetch immediately to show new results
        with st.spinner('Yeni verilerle güncelleniyor...'):
            st.session_state.portfolio_df = get_portfolio_data(new_funds_list)
            
        st.success("Portföy güncellendi!")
        st.rerun()
    
    st.markdown("---")

# 1. Fetch Data (Only if not cached)
if st.session_state.portfolio_df is None:
    with st.spinner('Güncel fon fiyatları çekiliyor...'):
        funds_to_load = load_funds()
        if not funds_to_load:
            st.warning("Henüz fon eklenmemiş. Yandan ekleyebilirsiniz.")
            st.session_state.portfolio_df = pd.DataFrame()
        else:
            st.session_state.portfolio_df = get_portfolio_data(funds_to_load)

df_portfolio = st.session_state.portfolio_df

if df_portfolio.empty and not load_funds():
    # Only show error if we really tried to fetch something and failed, 
    # but here we handle "empty list" above. 
    # This block handles "list exists but fetch returned empty" which is error case.
    if load_funds(): 
         st.error("Veri çekilemedi! İnternet bağlantınızı kontrol edin veya TEFAS'a erişim sorunu olabilir.")
else:
    # Calculate Total
    current_total = df_portfolio["Toplam Değer"].sum()
    
    # Save/Update History
    df_history = save_daily_total(current_total)
    
    # --- METRICS SECTION ---
    st.markdown("### 📊 Özet Durum")
    col1, col2, col3 = st.columns(3)
    
    # Calculate daily change if possible
    delta_val = 0
    delta_percent = 0
    if len(df_history) >= 2:
        yesterday_val = df_history.iloc[-2]["TotalValue"]
        delta_val = current_total - yesterday_val
        delta_percent = (delta_val / yesterday_val) * 100
        
    col1.metric("Toplam Varlık", f"{current_total:,.2f} TL", f"{delta_val:,.2f} TL", delta_color="normal")
    col2.metric("Günlük Değişim (%)", f"%{delta_percent:.2f}")
    col3.metric("Fon Sayısı", len(df_portfolio))
    
    st.markdown("---")
    
    # --- CHARTS SECTION ---
    # Use single column on mobile (auto-detected by Streamlit)
    st.subheader("🍰 Fon Bazlı Dağılım")
    df_pie = df_portfolio.groupby("Fon Kodu")["Toplam Değer"].sum().reset_index()
    fig_pie = px.pie(df_pie, values='Toplam Değer', names='Fon Kodu', hole=0.4)
    fig_pie.update_layout(height=350, margin=dict(l=20, r=20, t=40, b=20))
    st.plotly_chart(fig_pie, width="stretch")
    
    st.subheader("📊 Kategori Dağılımı")
    if "Kategori" in df_portfolio.columns:
        df_cat = df_portfolio.groupby("Kategori")["Toplam Değer"].sum().reset_index()
        fig_cat = px.pie(df_cat, values='Toplam Değer', names='Kategori', hole=0.4)
        fig_cat.update_layout(height=350, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig_cat, width="stretch")
    else:
        st.info("Kategori verisi bulunamadı.")
            
    st.markdown("---")
    
    # --- HISTORY CHART ---
    st.subheader("🗓️ Tarihsel Gelişim")
    if not df_history.empty:
        df_history['Date'] = pd.to_datetime(df_history['Date'])
        fig_line = px.line(df_history, x='Date', y='TotalValue', markers=True)
        fig_line.update_layout(xaxis_title="Tarih", yaxis_title="Toplam Değer (TL)")
        st.plotly_chart(fig_line, width="stretch")
    else:
        st.info("Henüz tarihsel veri yok.")
    
    # --- DETAILED TABLE ---
    st.markdown("### 📋 Detaylı Portföy Tablosu")
    
    # 🔎 Category Filter
    categories = ["Tümü"] + sorted(df_portfolio["Kategori"].dropna().unique().tolist())
    selected_cat = st.selectbox("📂 Kategori Filtrele", categories)
    
    if selected_cat == "Tümü":
        df_filtered = df_portfolio
    else:
        df_filtered = df_portfolio[df_portfolio["Kategori"] == selected_cat]
    
    # Reorder columns to put Category early
    cols = ["Fon Kodu", "Kategori", "Adet", "Birim Fiyat", "Toplam Değer", "Günlük Getiri (%)", "Günlük Kazanç (TL)"]
    # Filter only existing cols just in case
    cols = [c for c in cols if c in df_filtered.columns]
    
    st.dataframe(
        df_filtered[cols],
        width="stretch",
        hide_index=True,
        column_config={
            "Fon Kodu": st.column_config.TextColumn("Fon Kodu"),
            "Kategori": st.column_config.TextColumn("Kategori"),
            "Adet": st.column_config.NumberColumn("Adet", format="%.0f"),
            "Birim Fiyat": st.column_config.NumberColumn("Birim Fiyat", format="%.6f"),
            "Toplam Değer": st.column_config.NumberColumn("Toplam Değer", format="%.2f TL"),
            "Günlük Getiri (%)": st.column_config.NumberColumn("Günlük Getiri (%)", format="%.4f %%"),
            "Günlük Kazanç (TL)": st.column_config.NumberColumn("Günlük Kazanç (TL)", format="%.2f TL"),
        }
    )
    
    # Reload Button
    if st.button("🔄 Verileri Yenile"):
        st.session_state.portfolio_df = None # Invalidate cache
        st.rerun()

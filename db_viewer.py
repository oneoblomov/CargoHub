import json
import sqlite3

import pandas as pd
import streamlit as st

# Sayfa konfigürasyonu
st.set_page_config(
    page_title="📊 CargoHub Database Viewer",
    page_icon="🗃️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# CSS stilleri
st.markdown(
    """
<style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        text-align: center;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
    }

    .stats-card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.07);
        border: 1px solid #e2e8f0;
        margin: 1rem 0;
    }

    .data-table {
        background: white;
        border-radius: 8px;
        padding: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
</style>
""",
    unsafe_allow_html=True,
)

# Veritabanı bağlantısı
DB_PATH = "cargo_database.db"


def get_db_connection():
    """SQLite veritabanı bağlantısı oluşturur"""
    return sqlite3.connect(DB_PATH)


def get_table_info():
    """Veritabanı istatistiklerini döndürür"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Tablo istatistikleri
    stats = {}

    # Users sayısı
    cursor.execute("SELECT COUNT(*) FROM users")
    stats["total_users"] = cursor.fetchone()[0]

    # Cargos sayısı
    cursor.execute("SELECT COUNT(*) FROM cargos")
    stats["total_cargos"] = cursor.fetchone()[0]

    # Tracking history sayısı
    cursor.execute("SELECT COUNT(*) FROM tracking_history")
    stats["total_history"] = cursor.fetchone()[0]

    # Durum dağılımı
    cursor.execute("SELECT status, COUNT(*) FROM cargos GROUP BY status")
    stats["status_distribution"] = dict(cursor.fetchall())

    # Carrier dağılımı
    cursor.execute(
        "SELECT carrier, COUNT(*) FROM cargos WHERE carrier IS NOT NULL GROUP BY carrier"
    )
    stats["carrier_distribution"] = dict(cursor.fetchall())

    conn.close()
    return stats


def get_users_data(search_term=None, limit=50):
    """Kullanıcı verilerini döndürür"""
    conn = get_db_connection()
    cursor = conn.cursor()

    query = """
        SELECT u.id, u.name, u.email, u.phone, u.member_since,
               COUNT(c.tracking_number) as cargo_count
        FROM users u
        LEFT JOIN cargos c ON u.id = c.user_id
    """

    if search_term:
        query += " WHERE u.name LIKE ? OR u.email LIKE ? OR u.id LIKE ?"
        params = (f"%{search_term}%", f"%{search_term}%", f"%{search_term}%")
    else:
        params = ()

    query += (
        " GROUP BY u.id, u.name, u.email, u.phone, u.member_since ORDER BY u.id LIMIT ?"
    )
    params = params + (limit,)

    cursor.execute(query, params)
    columns = [desc[0] for desc in cursor.description]
    data = cursor.fetchall()

    conn.close()
    return columns, data


def get_cargos_data(user_filter=None, status_filter=None, limit=100):
    """Kargo verilerini döndürür"""
    conn = get_db_connection()
    cursor = conn.cursor()

    query = """
        SELECT c.tracking_number, c.user_id, u.name as user_name,
               c.status, c.location, c.last_update, c.estimated_delivery,
               c.description, c.weight, c.carrier, c.insurance
        FROM cargos c
        JOIN users u ON c.user_id = u.id
    """

    conditions = []
    params = []

    if user_filter:
        conditions.append("c.user_id = ?")
        params.append(user_filter)

    if status_filter:
        conditions.append("c.status = ?")
        params.append(status_filter)

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " ORDER BY c.last_update DESC LIMIT ?"
    params.append(limit)

    cursor.execute(query, params)
    columns = [desc[0] for desc in cursor.description]
    data = cursor.fetchall()

    conn.close()
    return columns, data


def get_tracking_history(tracking_number=None, limit=200):
    """Tracking history verilerini döndürür"""
    conn = get_db_connection()
    cursor = conn.cursor()

    query = """
        SELECT th.date, th.status, th.location, c.user_id, u.name as user_name
        FROM tracking_history th
        JOIN cargos c ON th.tracking_number = c.tracking_number
        JOIN users u ON c.user_id = u.id
    """

    if tracking_number:
        query += " WHERE th.tracking_number = ?"
        params = (tracking_number, limit)
    else:
        params = (limit,)

    query += " ORDER BY th.date DESC LIMIT ?"

    cursor.execute(query, params)
    columns = [desc[0] for desc in cursor.description]
    data = cursor.fetchall()

    conn.close()
    return columns, data


def export_data(table_name, format_type="json"):
    """Tablo verilerini dışa aktarır"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(f"SELECT * FROM {table_name}")
    columns = [desc[0] for desc in cursor.description]
    data = cursor.fetchall()

    conn.close()

    if format_type == "json":
        result = []
        for row in data:
            result.append(dict(zip(columns, row)))
        return json.dumps(result, indent=2, ensure_ascii=False, default=str)
    elif format_type == "csv":
        df = pd.DataFrame(data, columns=columns)
        return df.to_csv(index=False)


# Ana uygulama
def main():
    # Başlık
    st.markdown(
        """
    <div class="main-header">
        <h1>🗃️ CargoHub Database Viewer</h1>
        <p>SQLite veritabanı içeriğini görüntüleme ve yönetme aracı</p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Sidebar - Navigasyon
    with st.sidebar:
        st.markdown("### 📊 Database Viewer")
        st.markdown("---")

        page = st.selectbox(
            "📋 Sayfa Seçin",
            [
                "Dashboard",
                "Kullanıcılar",
                "Kargolar",
                "Tracking History",
                "Dışa Aktarma",
            ],
            key="page_selector",
        )

        st.markdown("---")
        st.markdown("### 🔍 Filtreler")

        # Varsayılan değerler
        search_term = ""
        user_limit = 50
        user_filter = "Tümü"
        status_filter = "Tümü"
        cargo_limit = 100
        tracking_filter = ""
        history_limit = 200

        if page == "Kullanıcılar":
            search_term = st.text_input(
                "Kullanıcı ara...", placeholder="İsim, email veya ID"
            )
            user_limit = st.slider("Gösterilecek kayıt sayısı", 10, 200, 50)
        elif page == "Kargolar":
            user_filter = st.selectbox(
                "Kullanıcı filtresi",
                ["Tümü"] + [f"user{i}" for i in range(100, 1000, 100)],
            )
            status_filter = st.selectbox(
                "Durum filtresi",
                [
                    "Tümü",
                    "Hazırlanıyor",
                    "Yola çıktı",
                    "Yolda",
                    "Dağıtımda",
                    "Teslim edildi",
                    "İade İşlemi",
                ],
            )
            cargo_limit = st.slider("Gösterilecek kayıt sayısı", 10, 500, 100)
        elif page == "Tracking History":
            tracking_filter = st.text_input(
                "Takip numarası filtresi", placeholder="TR123456789"
            )
            history_limit = st.slider("Gösterilecek kayıt sayısı", 10, 1000, 200)

    # Ana içerik
    if page == "Dashboard":
        st.markdown("## 📈 Dashboard")

        # İstatistikler
        stats = get_table_info()

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Toplam Kullanıcı", stats["total_users"])

        with col2:
            st.metric("Toplam Kargo", stats["total_cargos"])

        with col3:
            st.metric("Toplam Hareket", stats["total_history"])

        # Durum dağılımı
        st.markdown("### 📊 Kargo Durum Dağılımı")
        status_df = pd.DataFrame(
            list(stats["status_distribution"].items()), columns=["Durum", "Adet"]
        )
        st.bar_chart(status_df.set_index("Durum"))

        # Carrier dağılımı
        st.markdown("### 🏢 Kargo Firması Dağılımı")
        if stats["carrier_distribution"]:
            carrier_df = pd.DataFrame(
                list(stats["carrier_distribution"].items()), columns=["Firma", "Adet"]
            )
            st.bar_chart(carrier_df.set_index("Firma"))
        else:
            st.info("Carrier bilgisi bulunamadı")

        # Tablo içerikleri
        st.markdown("---")
        st.markdown("## 📋 Tablo İçerikleri")

        # Users tablosu
        st.markdown("### 👥 Users Tablosu")
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users LIMIT 20")
        user_columns = [desc[0] for desc in cursor.description]
        user_data = cursor.fetchall()
        if user_data:
            user_df = pd.DataFrame(user_data, columns=user_columns)
            st.table(user_df)
        else:
            st.info("Users tablosunda veri bulunamadı")

        # Cargos tablosu
        st.markdown("### 📦 Cargos Tablosu")
        cursor.execute("SELECT * FROM cargos LIMIT 20")
        cargo_columns = [desc[0] for desc in cursor.description]
        cargo_data = cursor.fetchall()
        if cargo_data:
            cargo_df = pd.DataFrame(cargo_data, columns=cargo_columns)
            st.table(cargo_df)
        else:
            st.info("Cargos tablosunda veri bulunamadı")

        # Tracking History tablosu
        st.markdown("### 📋 Tracking History Tablosu")
        cursor.execute("SELECT * FROM tracking_history LIMIT 20")
        history_columns = [desc[0] for desc in cursor.description]
        history_data = cursor.fetchall()
        if history_data:
            history_df = pd.DataFrame(history_data, columns=history_columns)
            st.table(history_df)
        else:
            st.info("Tracking History tablosunda veri bulunamadı")

        conn.close()

    elif page == "Kullanıcılar":
        st.markdown("## 👥 Kullanıcılar")

        # Veri çekme
        columns, data = get_users_data(
            search_term=search_term if "search_term" in locals() else None,
            limit=user_limit if "user_limit" in locals() else 50,
        )

        if data:
            df = pd.DataFrame(data, columns=columns)
            st.markdown(f"### 📋 {len(data)} kullanıcı bulundu")

            # Tablo gösterimi
            st.table(df)

            # Detay görünümü
            st.markdown("### 👀 Detaylı Görüntüleme")
            selected_user = st.selectbox(
                "Kullanıcı seçin", [f"{row[0]} - {row[1]}" for row in data]
            )

            if selected_user:
                user_id = selected_user.split(" - ")[0]
                st.markdown(f"**Seçilen Kullanıcı:** {user_id}")

                # Kullanıcının kargolarını göster
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT tracking_number, status, description, last_update
                    FROM cargos WHERE user_id = ?
                """,
                    (user_id,),
                )
                user_cargos = cursor.fetchall()
                conn.close()

                if user_cargos:
                    cargo_df = pd.DataFrame(
                        user_cargos,
                        columns=["Takip No", "Durum", "Ürün", "Son Güncelleme"],
                    )
                    st.table(cargo_df)
                else:
                    st.info("Bu kullanıcının kargosu bulunmuyor")
        else:
            st.warning("Kullanıcı bulunamadı")

    elif page == "Kargolar":
        st.markdown("## 📦 Kargolar")

        # Filtreler
        user_filter_val = None if user_filter == "Tümü" else user_filter
        status_filter_val = None if status_filter == "Tümü" else status_filter

        # Veri çekme
        columns, data = get_cargos_data(
            user_filter=user_filter_val,
            status_filter=status_filter_val,
            limit=cargo_limit if "cargo_limit" in locals() else 100,
        )

        if data:
            df = pd.DataFrame(data, columns=columns)
            st.markdown(f"### 📋 {len(data)} kargo bulundu")

            # Tablo gösterimi
            st.table(df)

            # Özet istatistikler
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Farklı Kullanıcı", len(df["user_id"].unique()))
            with col2:
                st.metric(
                    "Aktif Kargo",
                    len(df[df["status"].isin(["Yolda", "Dağıtımda", "Yola çıktı"])]),
                )
            with col3:
                st.metric("Teslim Edildi", len(df[df["status"] == "Teslim edildi"]))
        else:
            st.warning("Kargo bulunamadı")

    elif page == "Tracking History":
        st.markdown("## 📋 Tracking History")

        # Veri çekme
        columns, data = get_tracking_history(
            tracking_number=(
                tracking_filter
                if "tracking_filter" in locals() and tracking_filter
                else None
            ),
            limit=history_limit if "history_limit" in locals() else 200,
        )

        if data:
            df = pd.DataFrame(data, columns=columns)
            st.markdown(f"### 📋 {len(data)} hareket bulundu")

            # Tablo gösterimi
            st.table(df)

            # Zaman çizelgesi
            if len(data) > 0:
                st.markdown("### ⏰ Zaman Çizelgesi")
                # Son 10 hareketi göster
                recent_data = data[:10]
                for i, row in enumerate(recent_data):
                    st.write(f"**{i+1}.** {row[0]} - {row[1]} - {row[2]} ({row[4]})")
        else:
            st.warning("Tracking history bulunamadı")

    elif page == "Dışa Aktarma":
        st.markdown("## 📤 Dışa Aktarma")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### 📊 Tablo Seçin")
            table_name = st.selectbox(
                "Dışa aktarılacak tablo", ["users", "cargos", "tracking_history"]
            )

            format_type = st.selectbox("Format", ["json", "csv"])

        with col2:
            st.markdown("### 💾 Dışa Aktarma")
            if st.button("📥 Veriyi Dışa Aktar", type="primary"):
                try:
                    data = export_data(table_name, format_type)

                    if data is None:
                        st.error("❌ Veri dışa aktarılamadı")
                        return

                    # Dosya indirme
                    file_name = f"CargoHub_{table_name}.{format_type}"
                    mime_type = (
                        "application/json" if format_type == "json" else "text/csv"
                    )

                    st.download_button(
                        label=f"📥 {file_name} İndir",
                        data=data,
                        file_name=file_name,
                        mime=mime_type,
                    )

                    st.success(
                        f"✅ {table_name} tablosu {format_type.upper()} formatında hazırlandı!"
                    )

                except Exception as e:
                    st.error(f"❌ Dışa aktarma hatası: {e}")

    # Footer
    st.markdown("---")
    st.markdown("*CargoHub Database Viewer - Geliştirme Aracı*")


if __name__ == "__main__":
    main()

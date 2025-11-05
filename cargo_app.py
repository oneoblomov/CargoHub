import streamlit as st
import time
from cargo_chat import load_model, cargo_status_bot, load_cargo_data, save_cargo_data, create_return_request, create_cancel_request

# Sayfa konfigürasyonu - Modern görünüm
st.set_page_config(
    page_title="🚚 FastShip Kargo Takip",
    page_icon="�",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS ile modern tasarım
st.markdown("""
<style>
    /* Ana tema renkleri */
    :root {
        --primary-color: #2563eb;
        --secondary-color: #64748b;
        --success-color: #10b981;
        --warning-color: #f59e0b;
        --error-color: #ef4444;
        --background-color: #f8fafc;
        --card-bg: #ffffff;
        --text-primary: #1e293b;
        --text-secondary: #64748b;
    }

    /* Genel stiller */
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        text-align: center;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
    }

    .cargo-card {
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.07);
        border: 1px solid #e2e8f0;
        transition: transform 0.2s ease;
    }

    .cargo-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.15);
    }

    .status-badge {
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.875rem;
        text-align: center;
        display: inline-block;
    }

    .status-delivered { background: #dcfce7; color: #166534; }
    .status-in-transit { background: #dbeafe; color: #1e40af; }
    .status-preparing { background: #fef3c7; color: #92400e; }
    .status-return { background: #fee2e2; color: #991b1b; }

    .chat-message {
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        max-width: 80%;
    }

    .chat-user {
        background: #3b82f6;
        color: white;
        margin-left: auto;
        text-align: right;
    }

    .chat-assistant {
        background: #f1f5f9;
        color: #334155;
        margin-right: auto;
    }

    .sidebar-card {
        background: #f8fafc;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
        border: 1px solid #e2e8f0;
    }

    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }

    /* Responsive tasarım */
    @media (max-width: 768px) {
        .cargo-card {
            padding: 1rem;
        }
        .main-header {
            padding: 1rem;
        }
    }

    /* Loading animasyonu */
    .loading-spinner {
        display: inline-block;
        width: 20px;
        height: 20px;
        border: 3px solid #f3f3f3;
        border-top: 3px solid #3498db;
        border-radius: 50%;
        animation: spin 1s linear infinite;
    }

    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
</style>
""", unsafe_allow_html=True)

# Kullanıcı girişi kontrolü
def check_user_login(user_id):
    cargo_data = load_cargo_data()
    return user_id in cargo_data

# Kullanıcının kargolarını getir
def get_user_cargos(user_id):
    cargo_data = load_cargo_data()
    if user_id in cargo_data:
        return cargo_data[user_id]
    return None

# Durum badge'i oluştur
def get_status_badge(status):
    status_classes = {
        "Teslim edildi": "status-delivered",
        "Yolda": "status-in-transit",
        "Hazırlanıyor": "status-preparing",
        "Dağıtımda": "status-in-transit",
        "İade İşlemi": "status-return"
    }

    status_icons = {
        "Teslim edildi": "✅",
        "Yolda": "🚚",
        "Hazırlanıyor": "📦",
        "Dağıtımda": "🚚",
        "İade İşlemi": "↩️"
    }

    css_class = status_classes.get(status, "status-preparing")
    icon = status_icons.get(status, "📦")

    return f'<span class="status-badge {css_class}">{icon} {status}</span>'

# Ana uygulama
def main():
    # Sidebar - Şirket bilgileri ve navigation
    with st.sidebar:
        st.image("https://via.placeholder.com/200x80/2563eb/white?text=FastShip", width=200)
        st.markdown("### 🚚 FastShip Kargo")
        st.markdown("Türkiye'nin en güvenilir kargo şirketi")

        st.markdown("---")
        # İletişim bilgileri
        st.markdown("### 📞 İletişim")
        st.markdown("📧 [destek@fastship.com.tr](mailto:destek@fastship.com.tr) ")
        st.markdown("📱 0850 123 45 67")
        st.markdown("🕒 08:00 - 24:00")

    # Ana başlık
    st.markdown("""
    <div class="main-header">
        <h1>🚚 FastShip Kargo Takip Sistemi</h1>
        <p>Gemma AI ile akıllı kargo durumu sorgulama</p>
    </div>
    """, unsafe_allow_html=True)

    # Modeli yükle
    pipe = load_model()

    # Session state yönetimi
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.user_id = None
        st.session_state.user_data = None
        st.session_state.current_page = "login"
        st.session_state.pending_actions = []  # Onay bekleyen işlemler

    # Giriş sayfası
    if not st.session_state.logged_in:
        st.markdown("## 🔐 Güvenli Giriş")

        col1, col2 = st.columns([2, 1])

        with col1:
            with st.form("login_form"):
                st.markdown("### Kullanıcı Bilgilerinizi Girin")
                user_id = st.text_input(
                    "Kullanıcı ID",
                    placeholder="örn: user123, user456, user789, user999",
                    help="Demo kullanıcıları: user123, user456, user789, user999"
                )

                submitted = st.form_submit_button("🚀 Giriş Yap", use_container_width=True)

                if submitted:
                    if check_user_login(user_id):
                        user_data = get_user_cargos(user_id)
                        if user_data:
                            st.session_state.logged_in = True
                            st.session_state.user_id = user_id
                            st.session_state.user_data = user_data
                            st.success(f"✅ Hoş geldiniz, {user_data['name']}!")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("❌ Kullanıcı verileri yüklenemedi.")
                    else:
                        st.error("❌ Geçersiz kullanıcı ID. Lütfen tekrar deneyin.")

        with col2:
            st.markdown("### 👥 Demo Kullanıcıları")
            st.info("""
            **user123** - Ahmet Yılmaz (2 kargo)
            **user456** - Ayşe Kaya (1 kargo)
            **user789** - Mehmet Demir (2 kargo)
            **user999** - Zeynep Öztürk (1 kargo - iade)
            """)

            st.markdown("### 📋 Özellikler")
            st.markdown("""
            - ✅ AI destekli sorgulama
            - ✅ Gerçek zamanlı takip
            - ✅ Detaylı kargo geçmişi
            - ✅ Mobil uyumlu tasarım
            """)

    # Ana dashboard
    else:
        # Kullanıcı verilerinin mevcut olup olmadığını kontrol et
        if st.session_state.user_data is None:
            st.error("Kullanıcı verileri yüklenemedi. Lütfen tekrar giriş yapın.")
            st.session_state.logged_in = False
            st.rerun()
        else:
            # Üst bar - kullanıcı bilgileri ve çıkış
            col1, col2, col3 = st.columns([2, 1, 1])

            with col1:
                st.markdown(f"### 👋 Hoş Geldiniz, {st.session_state.user_data['name']}")
                st.caption(f"📧 {st.session_state.user_data.get('email', 'N/A')} | 📱 {st.session_state.user_data.get('phone', 'N/A')}")

            with col2:
                # Kargo istatistikleri
                total_cargos = len(st.session_state.user_data['cargos'])
                delivered = sum(1 for c in st.session_state.user_data['cargos'].values() if c['status'] == 'Teslim edildi')
                st.metric("Toplam Kargo", total_cargos)
                st.metric("Teslim Edildi", delivered)

            with col3:
                if st.button("🚪 Çıkış Yap", use_container_width=True):
                    st.session_state.logged_in = False
                    st.session_state.user_id = None
                    st.session_state.user_data = None
                    st.session_state.pending_actions = []  # Onay bekleyen işlemleri temizle
                    if 'chat_history' in st.session_state:
                        st.session_state.chat_history = []
                    st.rerun()

            st.markdown("---")

            # Tab sistemi
            tab1, tab2, tab3, tab4 = st.tabs(["📦 Kargolarım", "💬 AI Asistan", "📊 İstatistikler", "❓ Yardım"])

            # Tab 1: Kargolar
            with tab1:
                st.markdown("### 📦 Kargolarınız")

                # Arama ve filtreleme
                col_search, col_filter = st.columns([2, 1])

                with col_search:
                    search_term = st.text_input("� Kargo ara...", placeholder="Ürün adı veya takip numarası")

                with col_filter:
                    status_filter = st.selectbox(
                        "📋 Durum Filtresi",
                        ["Tümü", "Teslim edildi", "Yolda", "Hazırlanıyor", "Dağıtımda", "İade İşlemi"]
                    )

                # Kargoları listele
                filtered_cargos = {}
                for tracking_num, cargo in st.session_state.user_data['cargos'].items():
                    # Arama filtresi
                    if search_term:
                        if not (search_term.lower() in cargo['description'].lower() or
                               search_term in tracking_num):
                            continue

                    # Durum filtresi
                    if status_filter != "Tümü" and cargo['status'] != status_filter:
                        continue

                    filtered_cargos[tracking_num] = cargo

                if not filtered_cargos:
                    st.info("🔍 Aramanızla eşleşen kargo bulunamadı.")
                else:
                    for tracking_num, cargo in filtered_cargos.items():
                        with st.expander(f"📦 {tracking_num} - {cargo['description']}", expanded=False):
                            col_a, col_b = st.columns([1, 1])

                            with col_a:
                                st.markdown("**📍 Durum ve Konum**")
                                st.markdown(get_status_badge(cargo['status']), unsafe_allow_html=True)
                                st.write(f"📍 **Konum:** {cargo['location']}")
                                st.write(f"⚖️ **Ağırlık:** {cargo.get('weight', 'Belirtilmemiş')}")
                                st.write(f"📏 **Boyutlar:** {cargo.get('dimensions', 'Belirtilmemiş')}")

                            with col_b:
                                st.markdown("**⏰ Zaman Bilgileri**")
                                st.write(f"📅 **Son Güncelleme:** {cargo['last_update']}")
                                st.write(f"🚚 **Tahmini Teslimat:** {cargo['estimated_delivery']}")
                                st.write(f"🏢 **Kargo Firması:** {cargo.get('carrier', 'FastShip')}")

                            # Tracking history
                            if 'tracking_history' in cargo and cargo['tracking_history']:
                                st.markdown("**📋 Kargo Geçmişi**")
                                history_df = []
                                for event in cargo['tracking_history']:
                                    history_df.append({
                                        "Tarih": event['date'],
                                        "Durum": event['status'],
                                        "Konum": event['location']
                                    })

                                st.table(history_df)

            # Tab 2: AI Asistan
            with tab2:
                st.markdown("### 💬 AI Müşteri Hizmetleri Asistanı")

                # Chat history
                if 'chat_history' not in st.session_state:
                    st.session_state.chat_history = []

                # Chat container
                st.markdown("#### 💬 Sohbet Geçmişi")

                chat_container = st.container(height=400)

                with chat_container:
                    if not st.session_state.chat_history:
                        st.info("💡 Henüz hiç mesaj göndermediniz. Aşağıdan soru sorun!")
                    else:
                        for message in st.session_state.chat_history:
                            if message['role'] == 'user':
                                st.markdown(f"""
                                <div class="chat-message chat-user">
                                    <strong>Siz:</strong> {message['content']}
                                </div>
                                """, unsafe_allow_html=True)
                            else:
                                st.markdown(f"""
                                <div class="chat-message chat-assistant">
                                    <strong>🤖 AI Asistan:</strong> {message['content']}
                                </div>
                                """, unsafe_allow_html=True)

                # Chat input
                st.markdown("#### 💭 Sorunuzu Sorun")
                with st.form("chat_form", clear_on_submit=True):
                    user_question = st.text_input(
                        "Kargo durumunuz hakkında soru sorun:",
                        placeholder="örn: TR123456789 numaralı kargom nerede?",
                        help="AI asistanımız Türkçe sorularınızı anlayabilir"
                    )
                    submitted = st.form_submit_button("📤 Gönder", use_container_width=True)

                    if submitted and user_question:
                        # Kullanıcı mesajını ekle
                        st.session_state.chat_history.append({
                            'role': 'user',
                            'content': user_question
                        })

                        # AI yanıtı al
                        with st.spinner("🤖 AI düşünüyor..."):
                            ai_response = cargo_status_bot(pipe, user_question, st.session_state.user_data)

                        # AI yanıtını ekle
                        st.session_state.chat_history.append({
                            'role': 'assistant',
                            'content': ai_response
                        })

                        st.rerun()

                # Onay bekleyen işlemler
                if st.session_state.pending_actions:
                    st.markdown("---")
                    st.markdown("### ⚠️ Onay Bekleyen İşlemler")

                    for i, action in enumerate(st.session_state.pending_actions[:]):  # Copy to avoid modification during iteration
                        with st.container():
                            # İşlem başlığı
                            action_type_text = "🔄 İade Talebi" if action['type'] == 'return' else "❌ İptal Talebi"
                            st.markdown(f"#### {action_type_text} - {action['tracking_number']}")

                            # Kargo bilgileri
                            col_info, col_confirm = st.columns([2, 1])

                            with col_info:
                                st.markdown("**📦 Ürün Bilgileri:**")
                                st.write(f"• Ürün: {action['cargo_info']['description']}")
                                st.write(f"• Mevcut Durum: {action['cargo_info']['status']}")
                                st.write(f"• Konum: {action['cargo_info']['location']}")
                                st.write(f"• Talep Tarihi: {action['created_at']}")

                                if action['type'] == 'return':
                                    st.info("ℹ️ Bu işlem sonrasında kargo iade merkezi tarafından alınacak ve iade süreci başlatılacaktır.")
                                else:
                                    st.warning("⚠️ Bu işlem sonrasında kargo tamamen iptal edilecek ve geri alınamayacaktır.")

                            with col_confirm:
                                st.markdown("**Onay Durumu**")

                                # Checkbox ile onay
                                checkbox_key = f"confirm_{action['id']}"
                                confirmed = st.checkbox(
                                    "İşlemi onaylıyorum",
                                    key=checkbox_key,
                                    help="Bu kutuyu işaretleyerek işlemi onayladığınızı belirtin"
                                )

                                # İşlem butonları
                                if confirmed:
                                    if st.button(f"✅ İşlemi Tamamla", key=f"execute_{action['id']}", use_container_width=True, type="primary"):
                                        # İşlemi gerçekleştir
                                        cargo_data = load_cargo_data()
                                        user_id = st.session_state.user_id

                                        if action['type'] == 'return':
                                            success, message = create_return_request(
                                                action['tracking_number'],
                                                cargo_data[user_id],
                                                action['reason']
                                            )
                                        else:  # cancel
                                            success, message = create_cancel_request(
                                                action['tracking_number'],
                                                cargo_data[user_id],
                                                action['reason']
                                            )

                                        if success:
                                            # Veritabanını güncelle
                                            save_cargo_data(cargo_data)
                                            # Session state'i güncelle
                                            st.session_state.user_data = cargo_data[user_id]
                                            # İşlemi listeden çıkar
                                            st.session_state.pending_actions.pop(i)

                                            st.success(f"✅ {message}")
                                            st.balloons()
                                            time.sleep(2)  # Başarı mesajını göster
                                        else:
                                            st.error(f"❌ İşlem başarısız: {message}")

                                        st.rerun()
                                else:
                                    st.info("📝 İşlemi tamamlamak için yukarıdaki onay kutusunu işaretleyin")

                                # İptal butonu (checkbox işaretlenmemiş olsa da)
                                if st.button(f"❌ Talebi İptal Et", key=f"cancel_{action['id']}", use_container_width=True):
                                    st.session_state.pending_actions.pop(i)
                                    st.info("📝 İade/iptal talebi iptal edildi.")
                                    st.rerun()

                            st.markdown("---")

                # Sohbet yönetimi
                col_clear, col_export = st.columns(2)

                with col_clear:
                    if st.button("�️ Sohbeti Temizle", use_container_width=True):
                        st.session_state.chat_history = []
                        st.success("✅ Sohbet geçmişi temizlendi!")
                        st.rerun()

                with col_export:
                    if st.button("📄 Sohbeti Dışa Aktar", use_container_width=True):
                        chat_text = "FastShip AI Asistan Sohbet Geçmişi\n\n"
                        for msg in st.session_state.chat_history:
                            role = "Siz" if msg['role'] == 'user' else "AI Asistan"
                            chat_text += f"{role}: {msg['content']}\n\n"

                        st.download_button(
                            label="📥 İndir",
                            data=chat_text,
                            file_name="fastship_chat_history.txt",
                            mime="text/plain"
                        )

            # Tab 3: İstatistikler
            with tab3:
                st.markdown("### � Kargo İstatistikleri")

                user_cargos = st.session_state.user_data['cargos']

                # İstatistik kartları
                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.metric("Toplam Kargo", len(user_cargos))

                with col2:
                    delivered = sum(1 for c in user_cargos.values() if c['status'] == 'Teslim edildi')
                    st.metric("Teslim Edildi", delivered)

                with col3:
                    in_transit = sum(1 for c in user_cargos.values() if c['status'] in ['Yolda', 'Dağıtımda'])
                    st.metric("Yolda", in_transit)

                with col4:
                    preparing = sum(1 for c in user_cargos.values() if c['status'] == 'Hazırlanıyor')
                    st.metric("Hazırlanıyor", preparing)

                # Durum dağılımı
                st.markdown("#### 📈 Kargo Durum Dağılımı")

                status_counts = {}
                for cargo in user_cargos.values():
                    status = cargo['status']
                    status_counts[status] = status_counts.get(status, 0) + 1

                # Basit bar chart
                for status, count in status_counts.items():
                    percentage = (count / len(user_cargos)) * 100
                    st.progress(percentage / 100, text=f"{status}: {count} kargo ({percentage:.1f}%)")

                # Kargo firması dağılımı
                st.markdown("#### 🏢 Kargo Firması Dağılımı")

                carrier_counts = {}
                for cargo in user_cargos.values():
                    carrier = cargo.get('carrier', 'FastShip')
                    carrier_counts[carrier] = carrier_counts.get(carrier, 0) + 1

                for carrier, count in carrier_counts.items():
                    st.write(f"**{carrier}:** {count} kargo")

            # Tab 4: Yardım
            with tab4:
                st.markdown("### ❓ Sık Sorulan Sorular")

                faq_data = [
                    {
                        "question": "Takip numaramı nasıl öğrenebilirim?",
                        "answer": "Sipariş onay mailinizde veya SMS'inizde takip numaranızı bulabilirsiniz. Ayrıca müşteri hizmetlerimizle iletişime geçebilirsiniz."
                    },
                    {
                        "question": "Kargom ne zaman teslim edilir?",
                        "answer": "Tahmini teslimat süresi kargo detaylarınızda belirtilmiştir. Trafik, hava koşulları gibi faktörler teslimatı etkileyebilir."
                    },
                    {
                        "question": "Kargomu iade edebilir miyim?",
                        "answer": "Evet, teslim edilmiş kargoları teslim tarihinden itibaren 14 gün içinde iade edebilirsiniz. AI asistanımıza 'TR123456789 iade et' şeklinde mesaj göndererek iade talebi oluşturabilirsiniz."
                    },
                    {
                        "question": "Kargomu iptal edebilir miyim?",
                        "answer": "Evet, henüz yola çıkmamış (Hazırlanıyor durumunda) kargoları iptal edebilirsiniz. AI asistanımıza 'TR123456789 iptal et' şeklinde mesaj göndererek iptal talebi oluşturabilirsiniz."
                    },
                    {
                        "question": "İade veya iptal işlemi nasıl yapılır?",
                        "answer": "AI asistanımıza kargo takip numaranızla birlikte 'iade et' veya 'iptal et' deyin. Sistem uygunluk kontrolü yapacak ve onayınızla işlemi başlatacaktır."
                    },
                    {
                        "question": "Kargo sigortalı mı?",
                        "answer": "Kargo sigorta durumu ürün detaylarınızda belirtilmiştir. Değerli ürünler için sigorta önerilir."
                    },
                    {
                        "question": "Müşteri hizmetleri nasıl çalışır?",
                        "answer": "7/24 canlı destek, e-posta ve telefon ile bize ulaşabilirsiniz. AI asistanımız da sorularınızı yanıtlayabilir."
                    }
                ]

                for faq in faq_data:
                    with st.expander(f"❓ {faq['question']}"):
                        st.write(faq['answer'])

                st.markdown("---")

                st.markdown("### 📞 İletişim Bilgileri")
                st.info("""
                **📧 E-posta:** destek@fastship.com.tr
                **📱 Telefon:** 0850 123 45 67
                **🕒 Çalışma Saatleri:** 08:00 - 24:00 (7/24)
                **📍 Adres:** İstanbul, Türkiye
                """)

                st.markdown("### 🏢 Hakkımızda")
                st.write("""
                FastShip, Türkiye'nin önde gelen kargo ve lojistik şirketidir.
                10 yılı aşkın tecrübemizle güvenli, hızlı ve güvenilir kargo hizmetleri sunuyoruz.
                """)

if __name__ == "__main__":
    main()
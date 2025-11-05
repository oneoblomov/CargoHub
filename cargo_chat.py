import logging
import os
import re
import sqlite3
from datetime import datetime

import streamlit as st
from huggingface_hub import login
from transformers import pipeline

# Veritabanı bağlantısı için global değişken
DB_PATH = "cargo_database.db"

# Logging ayarları
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def get_db_connection():
    """SQLite veritabanı bağlantısı oluşturur"""
    return sqlite3.connect(DB_PATH)


# Güvenli login - ortam değişkeni kullan
@st.cache_resource
def load_model():
    token = os.environ.get("HF_TOKEN")
    if not token:
        return None  # Token yoksa model yüklenmez

    try:
        login(token=token)
        # Gemma modelini yükle
        with st.spinner("🤖 AI modeli yükleniyor..."):
            pipe = pipeline("text-generation", model="google/gemma-2b-it")
        return pipe
    except Exception as e:
        st.error(f"❌ Model yüklenirken hata: {str(e)}")
        return None


# Kargo verilerini yükle
@st.cache_data
def load_cargo_data():
    """SQLite veritabanından tüm kargo verilerini yükler"""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()

            # Users ve cargos verilerini birleştir
            cursor.execute(
                """
                SELECT u.id, u.name, u.email, u.phone, u.member_since,
                       c.tracking_number, c.status, c.location, c.last_update,
                       c.estimated_delivery, c.description, c.weight, c.dimensions,
                       c.carrier, c.insurance, c.return_reason
                FROM users u
                LEFT JOIN cargos c ON u.id = c.user_id
                ORDER BY u.id, c.tracking_number
            """
            )

            data = {}
            for row in cursor.fetchall():
                user_id = row[0]
                if user_id not in data:
                    data[user_id] = {
                        "name": row[1],
                        "email": row[2],
                        "phone": row[3],
                        "member_since": row[4],
                        "cargos": {},
                    }

                if row[5]:  # tracking_number varsa
                    tracking_num = row[5]
                    data[user_id]["cargos"][tracking_num] = {
                        "status": row[6],
                        "location": row[7],
                        "last_update": row[8],
                        "estimated_delivery": row[9],
                        "description": row[10],
                        "weight": row[11],
                        "dimensions": row[12],
                        "carrier": row[13],
                        "insurance": row[14],
                        "return_reason": row[15],
                        "tracking_history": [],
                    }

            # Tracking history'leri ekle
            for user_id in data:
                for tracking_num in data[user_id]["cargos"]:
                    cursor.execute(
                        """
                        SELECT date, status, location
                        FROM tracking_history
                        WHERE tracking_number = ?
                        ORDER BY date
                    """,
                        (tracking_num,),
                    )

                    history = []
                    for h_row in cursor.fetchall():
                        history.append(
                            {"date": h_row[0], "status": h_row[1], "location": h_row[2]}
                        )
                    data[user_id]["cargos"][tracking_num]["tracking_history"] = history

        return data

    except Exception as e:
        logger.error(f"Veritabanı yükleme hatası: {e}")
        st.error(f"❌ Veritabanı yükleme hatası: {e}")
        return {}


# Kargo verilerini kaydet
def save_cargo_data(cargo_data):
    """
    Güncellenmiş kargo verilerini SQLite veritabanına kaydeder
    """
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()

            # Tüm verileri güncelle (basit yaklaşım - production'da daha akıllı yap)
            for user_id, user_data in cargo_data.items():
                # User güncelle
                cursor.execute(
                    """
                    UPDATE users SET name=?, email=?, phone=?, member_since=?
                    WHERE id=?
                """,
                    (
                        user_data["name"],
                        user_data.get("email"),
                        user_data.get("phone"),
                        user_data.get("member_since"),
                        user_id,
                    ),
                )

                # Cargos güncelle
                for tracking_num, cargo_info in user_data["cargos"].items():
                    cursor.execute(
                        """
                        UPDATE cargos SET
                            status=?, location=?, last_update=?, estimated_delivery=?,
                            description=?, weight=?, dimensions=?, carrier=?,
                            insurance=?, return_reason=?
                        WHERE tracking_number=?
                    """,
                        (
                            cargo_info["status"],
                            cargo_info.get("location"),
                            cargo_info.get("last_update"),
                            cargo_info.get("estimated_delivery"),
                            cargo_info.get("description"),
                            cargo_info.get("weight"),
                            cargo_info.get("dimensions"),
                            cargo_info.get("carrier"),
                            cargo_info.get("insurance"),
                            cargo_info.get("return_reason"),
                            tracking_num,
                        ),
                    )

                    # Tracking history güncelle (basit yaklaşım)
                    cursor.execute(
                        "DELETE FROM tracking_history WHERE tracking_number=?",
                        (tracking_num,),
                    )
                    if "tracking_history" in cargo_info:
                        for history_item in cargo_info["tracking_history"]:
                            cursor.execute(
                                """
                                INSERT INTO tracking_history (tracking_number, date, status, location)
                                VALUES (?, ?, ?, ?)
                            """,
                                (
                                    tracking_num,
                                    history_item["date"],
                                    history_item["status"],
                                    history_item.get("location"),
                                ),
                            )

            conn.commit()

        # Cache'i temizle
        load_cargo_data.clear()

        return True

    except Exception as e:
        logger.error(f"Veri kaydetme hatası: {str(e)}")
        st.error(f"❌ Veri kaydetme hatası: {str(e)}")
        return False


# Tracking number'ı prompt'tan çıkar
def extract_tracking_number(prompt):
    # TR ile başlayan 9 haneli tracking number ara
    match = re.search(r"\b(TR\d{9})\b", prompt)
    return match.group(1) if match else None


# İade veya iptal talebi var mı kontrol et
def detect_return_cancel_intent(prompt):
    """
    Kullanıcı mesajında iade veya iptal isteği var mı kontrol eder
    Returns: ('return', tracking_number) veya ('cancel', tracking_number) veya (None, None)
    """
    prompt_lower = prompt.lower()

    # İade anahtar kelimeleri
    return_keywords = [
        "iade",
        "döndür",
        "gönder geri",
        "geri gönder",
        "iptal et",
        "vazgeç",
    ]

    # İptal anahtar kelimeleri (henüz yola çıkmamış kargolar için)
    cancel_keywords = ["iptal", "iptal et", "vazgeç", "dur", "durdur"]

    tracking_number = extract_tracking_number(prompt)

    if not tracking_number:
        return None, None

    # İade isteği mi kontrol et
    if any(keyword in prompt_lower for keyword in return_keywords):
        # İade kelimeleri varsa ve iptal kelimeleri yoksa iade olarak kabul et
        if not any(keyword in prompt_lower for keyword in ["iptal et", "vazgeç"]):
            return "return", tracking_number
        # Hem iade hem iptal varsa, bağlama göre karar ver
        if "teslim" in prompt_lower or "aldım" in prompt_lower:
            return "return", tracking_number

    # İptal isteği mi kontrol et
    if any(keyword in prompt_lower for keyword in cancel_keywords):
        # İptal ama iade değilse
        if not any(keyword in prompt_lower for keyword in ["iade", "döndür"]):
            return "cancel", tracking_number

    return None, None


# İade uygunluğu kontrolü
def check_return_eligibility(cargo_info):
    """
    Kargonun iade için uygun olup olmadığını kontrol eder
    Returns: (eligible: bool, reason: str)
    """
    status = cargo_info["status"]

    # Teslim edilmiş kargolar iade edilebilir
    if status == "Teslim edildi":
        # Teslim tarihini kontrol et (14 gün içinde olmalı)
        try:
            last_update = cargo_info["last_update"]
            # Tarih formatını parse et
            delivery_date = datetime.strptime(last_update, "%Y-%m-%d %H:%M")
            current_date = datetime.now()
            days_since_delivery = (current_date - delivery_date).days

            if days_since_delivery <= 14:
                return True, f"İade için uygundur ({days_since_delivery} gün geçti)"
            else:
                return (
                    False,
                    f"İade süresi dolmuştur ({days_since_delivery} gün geçti, maksimum 14 gün)",
                )
        except ValueError as e:
            logger.warning(
                f"Tarih parse hatası: {e}, last_update: {cargo_info.get('last_update')}"
            )
            return True, "İade için uygundur (teslim tarihi kontrol edilemedi)"
        except Exception as e:
            logger.error(f"Beklenmeyen tarih hatası: {e}")
            return True, "İade için uygundur (teslim tarihi kontrol edilemedi)"

    # İade işlemi zaten başlatılmış
    elif status == "İade İşlemi":
        return False, "Bu kargo için zaten iade işlemi başlatılmış"

    # Diğer durumlar için iade uygun değil
    else:
        return False, f"İade için uygun değildir (durum: {status})"


# İptal uygunluğu kontrolü
def check_cancel_eligibility(cargo_info):
    """
    Kargonun iptal için uygun olup olmadığını kontrol eder
    Returns: (eligible: bool, reason: str)
    """
    status = cargo_info["status"]

    # Sadece hazırlanıyor durumundaki kargolar iptal edilebilir
    if status == "Hazırlanıyor":
        return True, "İptal için uygundur (henüz yola çıkmamış)"

    # Diğer durumlar için iptal uygun değil
    else:
        return False, f"İptal için uygun değildir (durum: {status})"


# İade talebi oluştur
def create_return_request(tracking_number, user_cargos, reason="Müşteri talebi"):
    """
    İade talebi oluşturur ve kargo durumunu günceller
    """
    if tracking_number not in user_cargos["cargos"]:
        return False, "Kargo bulunamadı"

    cargo_info = user_cargos["cargos"][tracking_number]

    # Uygunluk kontrolü
    eligible, reason_check = check_return_eligibility(cargo_info)
    if not eligible:
        return False, reason_check

    # İade talebi oluştur - durumu güncelle
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M")

    # Tracking history'e iade talebi ekle
    if "tracking_history" not in cargo_info:
        cargo_info["tracking_history"] = []

    cargo_info["tracking_history"].append(
        {
            "date": current_time,
            "status": "İade talebi alındı",
            "location": "İstanbul İade Merkezi",
        }
    )

    # Durumu güncelle
    cargo_info["status"] = "İade İşlemi"
    cargo_info["location"] = "İstanbul İade Merkezi"
    cargo_info["last_update"] = current_time
    cargo_info["return_reason"] = reason

    return True, "İade talebiniz başarıyla oluşturuldu"


# İptal talebi oluştur
def create_cancel_request(tracking_number, user_cargos, reason="Müşteri talebi"):
    """
    İptal talebi oluşturur ve kargo durumunu günceller
    """
    if tracking_number not in user_cargos["cargos"]:
        return False, "Kargo bulunamadı"

    cargo_info = user_cargos["cargos"][tracking_number]

    # Uygunluk kontrolü
    eligible, reason_check = check_cancel_eligibility(cargo_info)
    if not eligible:
        return False, reason_check

    # İptal talebi oluştur - durumu güncelle
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M")

    # Tracking history'e iptal talebi ekle
    if "tracking_history" not in cargo_info:
        cargo_info["tracking_history"] = []

    cargo_info["tracking_history"].append(
        {
            "date": current_time,
            "status": "İptal talebi alındı",
            "location": "İstanbul Depo",
        }
    )

    # Durumu güncelle
    cargo_info["status"] = "İptal Edildi"
    cargo_info["location"] = "İstanbul Depo - İptal"
    cargo_info["last_update"] = current_time
    cargo_info["cancel_reason"] = reason

    return True, "İptal talebiniz başarıyla gerçekleştirildi"


# Kargo durumu chatbot fonksiyonu
def cargo_status_bot(pipe, prompt, user_cargos):
    """
    Kargo durumu sorgulama ve iade/iptal işlemleri chatbot'u
    Kullanıcının kendi kargoları için sorgu yapabilir ve işlemler başlatabilir
    """

    # Session state başlatma
    if "pending_actions" not in st.session_state:
        st.session_state.pending_actions = []
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # Kullanıcı verilerinin mevcut olup olmadığını kontrol et
    if user_cargos is None:
        return "Kullanıcı verileri bulunamadı. Lütfen tekrar giriş yapın."

    # Önce iade veya iptal talebi var mı kontrol et
    action_type, tracking_number = detect_return_cancel_intent(prompt)

    if action_type and tracking_number:
        # İade veya iptal talebi var
        if tracking_number not in user_cargos["cargos"]:
            available_tracking = list(user_cargos["cargos"].keys())
            return f"Üzgünüm, takip numarası {tracking_number} sizin kargolarınız arasında bulunamadı. Mevcut kargolarınız: {', '.join(available_tracking)}"

        cargo_info = user_cargos["cargos"][tracking_number]

        if action_type == "return":
            # İade talebi
            eligible, reason = check_return_eligibility(cargo_info)
            if not eligible:
                return f"Üzgünüm {user_cargos['name']}, {tracking_number} numaralı kargonuz için iade işlemi başlatılamıyor. Nedeni: {reason}"

            # İade için onay bekleyen işlem oluştur
            action_id = f"return_{tracking_number}_{datetime.now().strftime('%H%M%S')}"
            pending_action = {
                "id": action_id,
                "type": "return",
                "tracking_number": tracking_number,
                "cargo_info": cargo_info,
                "reason": "Müşteri talebi",
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }

            st.session_state.pending_actions.append(pending_action)

            return f"""Merhaba {user_cargos['name']}, {tracking_number} numaralı kargonuz için iade talebinizi aldım.

**Kargo Bilgileri:**
- Ürün: {cargo_info['description']}
- Durum: {cargo_info['status']}
- Teslim Tarihi: {cargo_info['last_update']}

İade işlemini başlatmak için lütfen aşağıdaki onay bölümünden onaylayın. İade süresi kontrol edildi ve uygundur."""

        elif action_type == "cancel":
            # İptal talebi
            eligible, reason = check_cancel_eligibility(cargo_info)
            if not eligible:
                return f"Üzgünüm {user_cargos['name']}, {tracking_number} numaralı kargonuz için iptal işlemi gerçekleştirilemiyor. Nedeni: {reason}"

            # İptal için onay bekleyen işlem oluştur
            action_id = f"cancel_{tracking_number}_{datetime.now().strftime('%H%M%S')}"
            pending_action = {
                "id": action_id,
                "type": "cancel",
                "tracking_number": tracking_number,
                "cargo_info": cargo_info,
                "reason": "Müşteri talebi",
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }

            st.session_state.pending_actions.append(pending_action)

            return f"""Merhaba {user_cargos['name']}, {tracking_number} numaralı kargonuz için iptal talebinizi aldım.

**Kargo Bilgileri:**
- Ürün: {cargo_info['description']}
- Durum: {cargo_info['status']}

İptal işlemini başlatmak için lütfen aşağıdaki onay bölümünden onaylayın. Bu işlem geri alınamaz."""

    # Normal kargo durumu sorgulama
    tracking_number = extract_tracking_number(prompt)

    if not tracking_number:
        return "Üzgünüm, takip numaranızı bulamadım. Lütfen TR ile başlayan 9 haneli takip numaranızı belirtin (örn: TR123456789). İade veya iptal talepleriniz için de takip numaranızı belirtmeniz gerekir."

    # Kullanıcının kargolarında bu takip numarası var mı kontrol et
    if tracking_number not in user_cargos["cargos"]:
        available_tracking = list(user_cargos["cargos"].keys())
        return f"Takip numarası {tracking_number} sizin kargolarınız arasında bulunamadı. Mevcut kargolarınız: {', '.join(available_tracking)}"

    cargo_info = user_cargos["cargos"][tracking_number]

    # AI modelinin yüklenip yüklenmediğini kontrol et
    if pipe is None:
        # Basit template-based response - daha sohbet edici hale getir
        status_messages = {
            "Teslim edildi": [
                f"Merhaba {user_cargos['name']}, {tracking_number} numaralı kargonuz başarıyla teslim edilmiş! 🎉 Teslim tarihi: {cargo_info['last_update']}. Umarım memnun kaldınız, başka bir konuda yardıma ihtiyacınız var mı?",
                f"Harika haber {user_cargos['name']}! {tracking_number} kargonuz teslim edildi. {cargo_info['last_update']} tarihinde ulaştı. CargoHub olarak hizmetinizden memnuniyet duyuyoruz. Başka sorularınız var mı?",
            ],
            "Yolda": [
                f"Merhaba {user_cargos['name']}, {tracking_number} kargonuz şu anda yolda ve {cargo_info['location']} civarında ilerliyor. Tahmini teslimat: {cargo_info['estimated_delivery']}. Yolculuk nasıl gidiyor merak ediyorum, başka detay ister misiniz?",
                f"{user_cargos['name']}, kargonuz yolda! {tracking_number} şu anda {cargo_info['location']} konumunda ve {cargo_info['estimated_delivery']} tarihinde size ulaşması bekleniyor. Herhangi bir endişeniz var mı?",
            ],
            "Hazırlanıyor": [
                f"Merhaba {user_cargos['name']}, {tracking_number} kargonuz hazırlanıyor ve yakında yola çıkacak. 📦 Lütfen biraz daha sabır, en kısa sürede yola çıkaracağız. Bu arada başka kargolarınız var mı kontrol etmek ister misiniz?",
                f"{user_cargos['name']}, kargonuz hazırlık aşamasında! {tracking_number} yakında yola çıkacak. Her şey yolunda, endişelenmeyin. Başka sorularınız var mı?",
            ],
            "Dağıtımda": [
                f"Merhaba {user_cargos['name']}, {tracking_number} kargonuz dağıtım aşamasında ve {cargo_info['location']} konumunda! 🚚 Yakında kapınızda olacak. Heyecanlı mısınız? Başka bir şey öğrenmek ister misiniz?",
                f"{user_cargos['name']}, neredeyse bitti! {tracking_number} dağıtımda ve {cargo_info['location']} civarında. Yakında teslim edilecek. Umarım güzel bir sürpriz sizi bekliyor!",
            ],
            "İade İşlemi": [
                f"Merhaba {user_cargos['name']}, {tracking_number} için iade işlemi başlatılmış. İade merkezi: {cargo_info['location']}. Süreci takip etmek ister misiniz? Başka yardıma ihtiyacınız var mı?",
                f"{user_cargos['name']}, iade talebiniz işleme alındı. {tracking_number} şu anda {cargo_info['location']} merkezinde. Herhangi bir sorun yaşarsanız bize ulaşın.",
            ],
        }

        import random

        messages = status_messages.get(
            cargo_info["status"],
            [
                f"Merhaba {user_cargos['name']}, {tracking_number} kargonuzun durumu: {cargo_info['status']}. Konum: {cargo_info['location']}. Başka sorularınız var mı?"
            ],
        )
        response = random.choice(messages)

        # Sohbet geçmişine ekle
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        st.session_state.chat_history.append({"role": "assistant", "content": response})

        return response

    # Sohbet geçmişini hazırla
    chat_history_text = ""
    if st.session_state.chat_history:
        recent_messages = st.session_state.chat_history[-6:]  # Son 6 mesaj (3 sohbet)
        chat_history_text = "\nÖnceki sohbet:\n" + "\n".join(
            [
                f"{'Kullanıcı' if msg['role'] == 'user' else 'Asistan'}: {msg['content']}"
                for msg in recent_messages
            ]
        )

    # Gemma ile doğal cevap oluştur
    context = f"""
    Kargo bilgisi:
    - Takip Numarası: {tracking_number}
    - Durum: {cargo_info['status']}
    - Konum: {cargo_info['location']}
    - Son Güncelleme: {cargo_info['last_update']}
    - Tahmini Teslimat: {cargo_info['estimated_delivery']}
    - Ürün Açıklaması: {cargo_info.get('description', 'Belirtilmemiş')}
    - Ağırlık: {cargo_info.get('weight', 'Belirtilmemiş')}
    - Kargo Firması: {cargo_info.get('carrier', 'CargoHub')}
    {chat_history_text}
    """

    system_prompt = f"""Sen {user_cargos['name']} kullanıcısının CargoHub kargo şirketi müşteri hizmetleri asistanısın.

Görevlerin:
- Kargo durumunu Türkçe olarak nazik, profesyonel ve yardımcı bir şekilde açıkla
- Kullanıcıyı adıyla selamla ve kişisel bir tonda konuş
- Detaylı bilgi ver ve gerekirse ek yardım öner
- CargoHub'in kaliteli hizmet anlayışını vurgula
- İade veya iptal talepleri için kullanıcıyı yönlendir
- Kullanıcının sorularına doğrudan cevap ver (örneğin "ne zaman teslim edilecek?" sorusuna tahmini tarihi söyle)
- Sohbeti doğal tut, kısa ve samimi yanıtlar ver
- Önceki sohbet geçmişini dikkate al ve bağlamı sürdür
- Kullanıcıyı memnun etmek için ekstra bilgi veya öneriler sun"""

    full_prompt = (
        f"{system_prompt}\n\n{context}\n\nKullanıcı sorusu: {prompt}\n\nCevabın:"
    )

    output = pipe(
        full_prompt,
        max_new_tokens=300,
        do_sample=True,
        temperature=0.7,
        top_k=50,
        top_p=0.9,
        return_full_text=False,
    )

    result = output[0]["generated_text"].strip()

    # Sohbet geçmişine ekle
    st.session_state.chat_history.append({"role": "user", "content": prompt})
    st.session_state.chat_history.append({"role": "assistant", "content": result})

    return result


# Pending actions'ı işle
def process_pending_actions(user_cargos):
    """
    Bekleyen iade/iptal işlemlerini göster ve onay için butonlar ekle
    """
    if (
        "pending_actions" not in st.session_state
        or not st.session_state.pending_actions
    ):
        return

    st.subheader("🔔 Bekleyen İşlemler")

    for i, action in enumerate(st.session_state.pending_actions):
        with st.expander(
            f"{action['type'].title()} Talebi - {action['tracking_number']}",
            expanded=True,
        ):
            st.write(f"**İşlem:** {action['type'].title()}")
            st.write(f"**Takip Numarası:** {action['tracking_number']}")
            st.write(f"**Ürün:** {action['cargo_info']['description']}")
            st.write(f"**Durum:** {action['cargo_info']['status']}")
            st.write(f"**Talep Tarihi:** {action['created_at']}")

            col1, col2 = st.columns(2)

            with col1:
                if st.button("✅ Onayla", key=f"approve_{i}"):
                    # İşlemi onayla
                    success = False
                    message = "Bilinmeyen işlem tipi"

                    if action["type"] == "return":
                        success, message = create_return_request(
                            action["tracking_number"], user_cargos, action["reason"]
                        )
                    elif action["type"] == "cancel":
                        success, message = create_cancel_request(
                            action["tracking_number"], user_cargos, action["reason"]
                        )

                    if success:
                        st.success(message)
                        # Veritabanına kaydet
                        save_cargo_data(user_cargos)
                        # Pending action'ı kaldır
                        st.session_state.pending_actions.pop(i)
                        st.rerun()
                    else:
                        st.error(message)

            with col2:
                if st.button("❌ İptal Et", key=f"cancel_{i}"):
                    # İşlemi iptal et
                    st.session_state.pending_actions.pop(i)
                    st.info("İşlem iptal edildi.")
                    st.rerun()

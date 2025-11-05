import json
import sqlite3


def create_database():
    """SQLite veritabanını ve tabloları oluşturur"""
    conn = sqlite3.connect("cargo_database.db")
    cursor = conn.cursor()

    # Users tablosu
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT,
            phone TEXT,
            member_since DATE
        )
    """
    )

    # Cargos tablosu
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS cargos (
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
        )
    """
    )

    # Tracking history tablosu
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS tracking_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tracking_number TEXT NOT NULL,
            date DATETIME NOT NULL,
            status TEXT NOT NULL,
            location TEXT,
            FOREIGN KEY (tracking_number) REFERENCES cargos (tracking_number)
        )
    """
    )

    conn.commit()
    return conn


def migrate_json_to_sqlite(json_file="cargo_data.json"):
    """JSON verilerini SQLite veritabanına aktarır"""

    # JSON dosyasını oku
    try:
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"❌ {json_file} dosyası bulunamadı!")
        return False
    except json.JSONDecodeError as e:
        print(f"❌ JSON parse hatası: {e}")
        return False

    # Veritabanını oluştur
    conn = create_database()
    cursor = conn.cursor()

    try:
        # Mevcut verileri temizle (eğer varsa)
        cursor.execute("DELETE FROM tracking_history")
        cursor.execute("DELETE FROM cargos")
        cursor.execute("DELETE FROM users")

        # Verileri aktar
        for user_id, user_data in data.items():
            # User ekle
            cursor.execute(
                """
                INSERT INTO users (id, name, email, phone, member_since)
                VALUES (?, ?, ?, ?, ?)
            """,
                (
                    user_id,
                    user_data["name"],
                    user_data.get("email"),
                    user_data.get("phone"),
                    user_data.get("member_since"),
                ),
            )

            # Cargos ekle
            for tracking_num, cargo_info in user_data["cargos"].items():
                cursor.execute(
                    """
                    INSERT INTO cargos (
                        tracking_number, user_id, status, location, last_update,
                        estimated_delivery, description, weight, dimensions,
                        carrier, insurance, return_reason
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        tracking_num,
                        user_id,
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
                    ),
                )

                # Tracking history ekle
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
        print("✅ Veriler başarıyla SQLite veritabanına aktarıldı!")
        return True

    except Exception as e:
        conn.rollback()
        print(f"❌ Veri aktarımı sırasında hata: {e}")
        return False

    finally:
        conn.close()


def generate_sample_data(num_users=10, num_cargos_per_user=3):
    """Örnek veri üretir ve JSON dosyasına kaydeder"""

    import random

    from faker import Faker

    fake = Faker("tr_TR")

    # Durum seçenekleri
    statuses = [
        "Hazırlanıyor",
        "Yola çıktı",
        "Yolda",
        "Dağıtımda",
        "Teslim edildi",
        "İade İşlemi",
    ]
    carriers = ["Aras Kargo", "MNG Kargo", "Sürat Kargo", "UPS", "DHL"]
    locations = ["İstanbul", "Ankara", "İzmir", "Bursa", "Antalya", "Konya", "Adana"]

    sample_data = {}

    for i in range(num_users):
        user_id = f"user{random.randint(100, 999)}"

        # Benzersiz user_id garantisi
        while user_id in sample_data:
            user_id = f"user{random.randint(100, 999)}"

        user = {
            "name": fake.name(),
            "email": fake.email(),
            "phone": fake.phone_number(),
            "member_since": fake.date_between(
                start_date="-2y", end_date="today"
            ).isoformat(),
            "cargos": {},
        }

        # Her user için rastgele sayıda cargo oluştur
        num_cargos = random.randint(1, num_cargos_per_user)

        for j in range(num_cargos):
            tracking_num = f"TR{random.randint(100000000, 999999999)}"

            # Benzersiz tracking number garantisi
            existing_tracking = []
            for u in sample_data.values():
                existing_tracking.extend(u["cargos"].keys())
            while tracking_num in existing_tracking:
                tracking_num = f"TR{random.randint(100000000, 999999999)}"

            status = random.choice(statuses)
            created_date = fake.date_time_between(start_date="-30d", end_date="now")

            cargo = {
                "status": status,
                "location": f"{random.choice(locations)}, Türkiye",
                "last_update": created_date.strftime("%Y-%m-%d %H:%M"),
                "estimated_delivery": (
                    created_date.replace(
                        day=min(created_date.day + random.randint(1, 7), 28)
                    )
                ).strftime("%Y-%m-%d"),
                "description": fake.sentence(nb_words=4),
                "weight": f"{random.uniform(0.1, 5.0):.1f} kg",
                "dimensions": f"{random.randint(10, 50)}x{random.randint(5, 30)}x{random.randint(2, 20)} cm",
                "carrier": random.choice(carriers),
                "insurance": random.choice(["Evet", "Hayır"]),
            }

            # Sigorta varsa değer ekle
            if cargo["insurance"] == "Evet":
                cargo["insurance"] += f" - {random.randint(5, 100) * 1000} TL"

            # Tracking history oluştur
            history = []
            current_date = created_date

            # Başlangıç durumu
            history.append(
                {
                    "date": current_date.strftime("%Y-%m-%d %H:%M"),
                    "status": "Sipariş alındı",
                    "location": f"{random.choice(locations)} Depo",
                }
            )

            # Ara durumlar
            if status in [
                "Yola çıktı",
                "Yolda",
                "Dağıtımda",
                "Teslim edildi",
                "İade İşlemi",
            ]:
                current_date = fake.date_time_between(
                    start_date=current_date, end_date="now"
                )
                history.append(
                    {
                        "date": current_date.strftime("%Y-%m-%d %H:%M"),
                        "status": "Paket hazırlandı",
                        "location": f"{random.choice(locations)} Depo",
                    }
                )

            if status in [
                "Yola çıktı",
                "Yolda",
                "Dağıtımda",
                "Teslim edildi",
                "İade İşlemi",
            ]:
                current_date = fake.date_time_between(
                    start_date=current_date, end_date="now"
                )
                history.append(
                    {
                        "date": current_date.strftime("%Y-%m-%d %H:%M"),
                        "status": "Yola çıktı",
                        "location": f"{random.choice(locations)} Dağıtım",
                    }
                )

            if status in ["Yolda", "Dağıtımda", "Teslim edildi", "İade İşlemi"]:
                current_date = fake.date_time_between(
                    start_date=current_date, end_date="now"
                )
                history.append(
                    {
                        "date": current_date.strftime("%Y-%m-%d %H:%M"),
                        "status": "Yolda",
                        "location": f"{random.choice(locations)}, Türkiye",
                    }
                )

            if status in ["Dağıtımda", "Teslim edildi", "İade İşlemi"]:
                current_date = fake.date_time_between(
                    start_date=current_date, end_date="now"
                )
                history.append(
                    {
                        "date": current_date.strftime("%Y-%m-%d %H:%M"),
                        "status": "Dağıtıma çıktı",
                        "location": f"{random.choice(locations)} Şubesi",
                    }
                )

            if status == "Teslim edildi":
                current_date = fake.date_time_between(
                    start_date=current_date, end_date="now"
                )
                history.append(
                    {
                        "date": current_date.strftime("%Y-%m-%d %H:%M"),
                        "status": "Teslim edildi",
                        "location": f"{random.choice(locations)}, Türkiye",
                    }
                )

            if status == "İade İşlemi":
                current_date = fake.date_time_between(
                    start_date=current_date, end_date="now"
                )
                history.append(
                    {
                        "date": current_date.strftime("%Y-%m-%d %H:%M"),
                        "status": "İade talebi alındı",
                        "location": f"{random.choice(locations)} İade Merkezi",
                    }
                )

            cargo["tracking_history"] = history
            user["cargos"][tracking_num] = cargo

        sample_data[user_id] = user

    # JSON dosyasına kaydet
    with open("cargo_data.json", "w", encoding="utf-8") as f:
        json.dump(sample_data, f, ensure_ascii=False, indent=2)

    print(
        f"✅ {len(sample_data)} kullanıcı ve toplam {sum(len(u['cargos']) for u in sample_data.values())} kargo ile örnek veri üretildi!"
    )

    return sample_data


if __name__ == "__main__":
    # Örnek veri üret
    print("🔄 Örnek veri üretiliyor...")
    generate_sample_data(num_users=20, num_cargos_per_user=5)

    # SQLite'e aktar
    print("🔄 Veriler SQLite'e aktarılıyor...")
    migrate_json_to_sqlite()

    print("✅ İşlem tamamlandı!")

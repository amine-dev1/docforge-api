"""
seed_tenants.py
Seeds 10 realistic Moroccan test enterprises, each with:
  - Enterprise record (short_id T2 .. T11)
  - 1 Admin user
  - 1 Admin role
  - 1 API Key  (plaintext printed once, only hash stored)

Run:  python seed_tenants.py
"""
import uuid, secrets, hashlib
import bcrypt
import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime, timezone

DB_URL = (
    "postgresql://neondb_owner:npg_6MpPwzY0WEkC"
    "@ep-frosty-bonus-ajjt7gky-pooler.c-3.us-east-2.aws.neon.tech"
    "/neondb?sslmode=require&channel_binding=require"
)

# ── Helpers ───────────────────────────────────────────────────────────────
def hash_password(pw: str) -> str:
    return bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()

def make_api_key():
    plaintext = secrets.token_urlsafe(32)
    key_hash  = hashlib.sha256(plaintext.encode()).hexdigest()
    preview   = plaintext[:8]
    return plaintext, key_hash, preview

now = datetime.now(timezone.utc)

# ── Test enterprises data ─────────────────────────────────────────────────
ENTERPRISES = [
    {
        "slug": "techwave-ma",
        "legal_name": "TECHWAVE MAROC SARL",
        "trade_name": "TechWave",
        "sector": "Technologies de l'information",
        "legal_form": "SARL",
        "ice": "002000000000001",
        "rc": "RC-TW-001",
        "address_city": "Casablanca",
        "address_street": "Boulevard Anfa, 45",
        "address_zip": "20050",
        "email_general": "contact@techwave.ma",
        "phone_main": "+212 5 22 00 01 01",
        "plan": "pro",
        "primary_color": "#2563eb",
        "user_first": "Youssef", "user_last": "Benali",
        "user_email": "youssef@techwave.ma", "user_pw": "Test1234!",
    },
    {
        "slug": "atlas-consulting",
        "legal_name": "ATLAS CONSULTING SA",
        "trade_name": "Atlas Consulting",
        "sector": "Conseil et management",
        "legal_form": "SA",
        "ice": "002000000000002",
        "rc": "RC-AC-002",
        "address_city": "Rabat",
        "address_street": "Avenue Hassan II, 12",
        "address_zip": "10020",
        "email_general": "info@atlasconsulting.ma",
        "phone_main": "+212 5 37 00 02 02",
        "plan": "enterprise",
        "primary_color": "#7c3aed",
        "user_first": "Salma", "user_last": "El Idrissi",
        "user_email": "salma@atlasconsulting.ma", "user_pw": "Test1234!",
    },
    {
        "slug": "sofimaroc",
        "legal_name": "SOFIMAROC SARL AU",
        "trade_name": "SofiMaroc",
        "sector": "Finance et investissement",
        "legal_form": "SARL",
        "ice": "002000000000003",
        "rc": "RC-SM-003",
        "address_city": "Marrakech",
        "address_street": "Rue de la Liberté, 7",
        "address_zip": "40000",
        "email_general": "contact@sofimaroc.ma",
        "phone_main": "+212 5 24 00 03 03",
        "plan": "pro",
        "primary_color": "#059669",
        "user_first": "Hamza", "user_last": "Ziani",
        "user_email": "hamza@sofimaroc.ma", "user_pw": "Test1234!",
    },
    {
        "slug": "batiplus-ma",
        "legal_name": "BATIPLUS MAROC SA",
        "trade_name": "BatiPlus",
        "sector": "BTP et construction",
        "legal_form": "SA",
        "ice": "002000000000004",
        "rc": "RC-BP-004",
        "address_city": "Fès",
        "address_street": "Zone Industrielle Sud, Lot 22",
        "address_zip": "30050",
        "email_general": "info@batiplus.ma",
        "phone_main": "+212 5 35 00 04 04",
        "plan": "pro",
        "primary_color": "#d97706",
        "user_first": "Khadija", "user_last": "Moussaoui",
        "user_email": "khadija@batiplus.ma", "user_pw": "Test1234!",
    },
    {
        "slug": "greenlogistics",
        "legal_name": "GREEN LOGISTICS SARL",
        "trade_name": "GreenLogistics",
        "sector": "Transport et logistique",
        "legal_form": "SARL",
        "ice": "002000000000005",
        "rc": "RC-GL-005",
        "address_city": "Tanger",
        "address_street": "Port de Tanger Med, Bâtiment B",
        "address_zip": "90000",
        "email_general": "ops@greenlogistics.ma",
        "phone_main": "+212 5 39 00 05 05",
        "plan": "free",
        "primary_color": "#16a34a",
        "user_first": "Omar", "user_last": "Rahimi",
        "user_email": "omar@greenlogistics.ma", "user_pw": "Test1234!",
    },
    {
        "slug": "mediasphere-ma",
        "legal_name": "MEDIASPHERE MAROC SARL",
        "trade_name": "MediaSphere",
        "sector": "Médias et communication",
        "legal_form": "SARL",
        "ice": "002000000000006",
        "rc": "RC-MS-006",
        "address_city": "Casablanca",
        "address_street": "Twin Center, Tour B, 15e étage",
        "address_zip": "20100",
        "email_general": "hello@mediasphere.ma",
        "phone_main": "+212 5 22 00 06 06",
        "plan": "pro",
        "primary_color": "#db2777",
        "user_first": "Nadia", "user_last": "Chraibi",
        "user_email": "nadia@mediasphere.ma", "user_pw": "Test1234!",
    },
    {
        "slug": "pharmalink-ma",
        "legal_name": "PHARMALINK MAROC SA",
        "trade_name": "PharmaLink",
        "sector": "Santé et pharmacie",
        "legal_form": "SA",
        "ice": "002000000000007",
        "rc": "RC-PL-007",
        "address_city": "Rabat",
        "address_street": "Avenue Mehdi Ben Barka, 34",
        "address_zip": "10100",
        "email_general": "info@pharmalink.ma",
        "phone_main": "+212 5 37 00 07 07",
        "plan": "enterprise",
        "primary_color": "#0891b2",
        "user_first": "Imane", "user_last": "Tazi",
        "user_email": "imane@pharmalink.ma", "user_pw": "Test1234!",
    },
    {
        "slug": "agritech-souss",
        "legal_name": "AGRITECH SOUSS SARL",
        "trade_name": "AgriTech Souss",
        "sector": "Agriculture et agroalimentaire",
        "legal_form": "SARL",
        "ice": "002000000000008",
        "rc": "RC-AS-008",
        "address_city": "Agadir",
        "address_street": "Route d'Ait Melloul, Km 5",
        "address_zip": "80000",
        "email_general": "contact@agritech-souss.ma",
        "phone_main": "+212 5 28 00 08 08",
        "plan": "free",
        "primary_color": "#65a30d",
        "user_first": "Rachid", "user_last": "Ait Baha",
        "user_email": "rachid@agritech-souss.ma", "user_pw": "Test1234!",
    },
    {
        "slug": "energypro-ma",
        "legal_name": "ENERGYPRO MAROC SA",
        "trade_name": "EnergyPro",
        "sector": "Energie et développement durable",
        "legal_form": "SA",
        "ice": "002000000000009",
        "rc": "RC-EP-009",
        "address_city": "Ouarzazate",
        "address_street": "Zone Noor, Route de Zagora",
        "address_zip": "45000",
        "email_general": "info@energypro.ma",
        "phone_main": "+212 5 24 00 09 09",
        "plan": "enterprise",
        "primary_color": "#ea580c",
        "user_first": "Zineb", "user_last": "Bouzidi",
        "user_email": "zineb@energypro.ma", "user_pw": "Test1234!",
    },
    {
        "slug": "eduforma-ma",
        "legal_name": "EDUFORMA MAROC SARL",
        "trade_name": "EduForma",
        "sector": "Formation et education",
        "legal_form": "SARL",
        "ice": "002000000000010",
        "rc": "RC-EF-010",
        "address_city": "Meknes",
        "address_street": "Hay Hamria, Rue des Ecoles 3",
        "address_zip": "50000",
        "email_general": "admin@eduforma.ma",
        "phone_main": "+212 5 35 00 10 10",
        "plan": "pro",
        "primary_color": "#7c3aed",
        "user_first": "Mehdi", "user_last": "Oujda",
        "user_email": "mehdi@eduforma.ma", "user_pw": "Test1234!",
    },
]

# ── Main seeding ──────────────────────────────────────────────────────────
conn = psycopg2.connect(DB_URL)
cur  = conn.cursor()

# Find max existing T-number
cur.execute("SELECT short_id FROM enterprises WHERE short_id LIKE 'T%';")
existing = cur.fetchall()
used_nums = set()
for (sid,) in existing:
    try:
        used_nums.add(int(sid[1:]))
    except ValueError:
        pass
next_num = max(used_nums, default=0) + 1

results = []

print("\n" + "=" * 70)
print("  SEEDING 10 TEST ENTERPRISES")
print("=" * 70)

for ent in ENTERPRISES:
    short_id = f"T{next_num}"
    next_num += 1

    ent_id  = uuid.uuid4()
    user_id = uuid.uuid4()
    role_id = uuid.uuid4()
    key_id  = uuid.uuid4()
    plaintext, key_hash, preview = make_api_key()

    # ── Skip if slug already exists ──────────────────────────────────────
    cur.execute("SELECT id FROM enterprises WHERE slug = %s OR ice = %s;",
                (ent["slug"], ent["ice"]))
    if cur.fetchone():
        print(f"  [SKIP] {ent['legal_name']} already exists.")
        continue

    # ── 1. Enterprise ────────────────────────────────────────────────────
    cur.execute("""
        INSERT INTO enterprises
          (id, short_id, slug, legal_name, trade_name, legal_form, sector,
           ice, rc, address_city, address_street, address_zip,
           email_general, phone_main, plan,
           primary_color, is_active, is_verified, created_at, updated_at)
        VALUES
          (%s,%s,%s,%s,%s,%s,%s,
           %s,%s,%s,%s,%s,
           %s,%s,%s,
           %s, TRUE, TRUE, %s, %s)
    """, (
        str(ent_id), short_id, ent["slug"], ent["legal_name"], ent["trade_name"],
        ent["legal_form"], ent["sector"],
        ent["ice"], ent["rc"], ent["address_city"], ent["address_street"], ent["address_zip"],
        ent["email_general"], ent["phone_main"], ent["plan"],
        ent["primary_color"], now, now,
    ))

    # ── 2. User ──────────────────────────────────────────────────────────
    hashed_pw = hash_password(ent["user_pw"])
    cur.execute("""
        INSERT INTO users
          (id, enterprise_id, first_name, last_name, email,
           hashed_password, status, created_at, updated_at)
        VALUES (%s,%s,%s,%s,%s,%s,'active',%s,%s)
    """, (
        str(user_id), str(ent_id),
        ent["user_first"], ent["user_last"], ent["user_email"],
        hashed_pw, now, now,
    ))

    # ── 3. Admin Role ────────────────────────────────────────────────────
    cur.execute("""
        INSERT INTO roles (id, enterprise_id, name, description, is_system, created_at)
        VALUES (%s,%s,'Admin','Full access admin role', TRUE, %s)
    """, (str(role_id), str(ent_id), now))

    # ── 4. Assign role to user ───────────────────────────────────────────
    cur.execute("""
        INSERT INTO user_roles (id, user_id, role_id, assigned_at)
        VALUES (%s,%s,%s,%s)
    """, (str(uuid.uuid4()), str(user_id), str(role_id), now))

    # ── 5. API Key ───────────────────────────────────────────────────────
    cur.execute("""
        INSERT INTO api_keys
          (id, enterprise_id, created_by, name, key_hash, key_preview,
           scopes, is_active, created_at)
        VALUES (%s,%s,%s,'Default API Key',%s,%s,'{*}', TRUE, %s)
    """, (
        str(key_id), str(ent_id), str(user_id),
        key_hash, preview, now,
    ))

    results.append({
        "short_id": short_id,
        "legal_name": ent["legal_name"],
        "plan": ent["plan"],
        "user_email": ent["user_email"],
        "api_key": plaintext,
    })

conn.commit()
cur.close()
conn.close()

# ── Print summary table ───────────────────────────────────────────────────
print(f"\n{'ID':<5} {'Enterprise':<30} {'Plan':<12} {'User Email':<35} {'API Key'}")
print("-" * 130)
for r in results:
    print(f"{r['short_id']:<5} {r['legal_name']:<30} {r['plan']:<12} {r['user_email']:<35} {r['api_key']}")

print(f"\n[OK] {len(results)} enterprises seeded successfully.")
print("Save the API keys above -- they are NOT stored in plaintext and won't be shown again.")

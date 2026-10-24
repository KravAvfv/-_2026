"""Наповнення БД прототипу «Щит-Лінк» тестовими даними (детерміновано, random.Random(8)).

Основа — tspp_work/lab2/db/seed.py; для курсової роботи додано пароль облікових записів (DEMO_PASSWORD, хеш
werkzeug) і два пости візуального спостереження (для форми ручного донесення).

Довідники й основні таблиці вставляються напряму; операційні дані — через серверні функції та тригери
(fn_ingest_detection, переходи стану місії, звіти), тож разом із даними наповнюються хронологія подій і журнал
аудиту. Історія охоплює 30 діб до моменту запуску; 6 треків «живі» (останні хвилини) — для черги загроз.

    seed(conn)              # conn — psycopg.Connection до БД з виконаними schema.sql та impl.sql
    seed(conn, rich=True)   # + розширений набір для живої демонстрації (serve.py): ще 4 місяці історії,
                            #   місії, що чекають дії кожної ролі, ресурси в усіх станах (записка й тести — без нього)
"""
import math
import random
from datetime import datetime, timedelta, timezone

from psycopg.types.json import Jsonb
from werkzeug.security import generate_password_hash

DEMO_PASSWORD = "shchit-demo"                  # однаковий для всіх навчальних облікових записів

R = random.Random(8)
LAT0, LAT1, LON0, LON1 = 51.00, 52.20, 30.40, 32.80          # умовний район відповідальності

ROLES = [  # код, назва, бойові права, права
    ("R-01", "Оперативний черговий", True, "track.read track.classify mission.read mission.approve mission.reassign "
     "mission.abort "
     "resource.read analytics.read"),
    ("R-02", "Офіцер бойового управління", True, "track.read mission.read mission.propose mission.abort "
     "resource.read sector.manage"),
    ("R-03", "Аналітик повітряної обстановки", False, "track.read track.classify mission.read resource.read"),
    ("R-04", "Командир розрахунку", True, "track.read mission.read mission.accept mission.launch mission.report "
     "mission.abort resource.read"),
    ("R-05", "Оператор перехоплювача", True, "track.read mission.read mission.launch telemetry.write"),
    ("R-06", "Оператор сенсорного поста", False, "track.read detection.write"),
    ("R-07", "Технік", False, "resource.read interceptor.manage sensor.manage"),
    ("R-08", "Логіст", False, "resource.read interceptor.manage"),
    ("R-09", "Аналітик ефективності", False, "track.read mission.read analytics.read"),
    ("R-10", "Адміністратор системи", False, "user.manage role.manage"),
    ("R-11", "Офіцер кібербезпеки", False, "audit.read user.block"),
    ("R-12", "Начальник центру", False, "track.read mission.read resource.read analytics.read sector.manage"),
    ("R-13", "Інструктор", False, "track.read mission.read analytics.read"),
]
PERMS = {
    "track.read": "Перегляд повітряної обстановки", "track.classify": "Класифікація треків",
    "mission.read": "Перегляд місій", "mission.propose": "Пропозиція місії", "mission.reassign": "Перепризначення розрахунку місії",
    "mission.approve": "Санкціонування або відхилення місії", "mission.accept": "Прийняття місії розрахунком",
    "mission.launch": "Пуск перехоплювача", "mission.abort": "Скасування місії",
    "mission.report": "Доповідь про результат", "resource.read": "Перегляд готовності ресурсів",
    "interceptor.manage": "Облік перехоплювачів", "sensor.manage": "Облік сенсорів",
    "sector.manage": "Ведення секторів і об’єктів", "analytics.read": "Аналітика та звіти",
    "audit.read": "Перегляд журналу аудиту", "user.manage": "Керування користувачами",
    "role.manage": "Керування ролями та правами", "user.block": "Блокування облікових записів",
    "telemetry.write": "Передавання телеметрії", "detection.write": "Ручне донесення про виявлення",
}
SURN = ["Бондар", "Ткаченко", "Кравець", "Олійник", "Шевчук", "Коваль", "Мельник", "Лисенко", "Руденко", "Савчук",
        "Гончар", "Марченко", "Поліщук", "Ковальчук", "Мороз", "Павленко", "Литвин", "Карпенко", "Бойко",
        "Гнатюк", "Дяченко", "Остапчук", "Семенко", "Яковенко", "Петрук", "Гаврилюк", "Зінченко", "Тимошенко",
        "Козак", "Нестеренко"]
INIT = "АБВГДЄІКЛМОПРСТ"
CALL = ["Беркут", "Сокіл", "Яструб", "Орлан", "Кречет", "Шуліка"]
MODELS = [("Перехоплювач-А", 300, 12.0, 15, 12.0, True, False), ("Перехоплювач-Б", 250, 20.0, 25, 14.0, True, True),
          ("Перехоплювач-В", 330, 8.0, 10, 10.0, False, False), ("Перехоплювач-Г", 280, 15.0, 20, 13.0, True, True)]
OBJECTS = [("ТЕЦ-2", "I"), ("Підстанція 330 кВ «Північна»", "I"), ("Водоочисна станція", "I"),
           ("Залізничний вузол", "II"), ("Нафтобаза", "II"), ("Аеродром", "I"), ("Мостовий перехід", "II"),
           ("Телевежа", "III"), ("Лікарня обласна", "I"), ("Елеватор", "III"), ("Хлібозавод", "III"),
           ("Насосна станція", "II")]
NUM = {}                                      # лічильник номерів місій за добу
SIGS = ["ударний поршневий", "ударний реактивний", "розвідувальний", "квадрокоптер"]
EXTRA_OBJECTS = [("ТЕЦ-5", "I"), ("Газорозподільна станція", "I"), ("Підстанція 110 кВ «Лісова»", "II"),
                 ("Пологовий будинок", "I"), ("Водонапірна вежа", "III"), ("Автовокзал", "III"),
                 ("Склад пально-мастильних матеріалів", "II"), ("Цукровий завод", "III"), ("Річковий порт", "II"),
                 ("Обласний центр зв’язку", "I")]


def pt(lat, lon, km_n, km_e):
    return lat + km_n / 111.0, lon + km_e / (111.0 * math.cos(math.radians(lat)))


def seed(conn, now=None, rich=False):
    now = now or datetime.now(timezone.utc).replace(microsecond=0)
    cur = conn.cursor()
    q = lambda sql, *a: cur.execute(sql, a)                                    # noqa: E731
    one = lambda sql, *a: cur.execute(sql, a).fetchone()[0]                   # noqa: E731
    user = lambda uid: q("SELECT set_config('app.user_id', %s, false)", str(uid) if uid else "")   # noqa: E731
    at = lambda ts: q("SELECT set_config('app.event_at', %s, false)", ts.isoformat() if ts else "")  # noqa: E731

    # ------------------------------------------------------------------ довідники
    perm_id = {c: one("INSERT INTO permission (code, description) VALUES (%s, %s) RETURNING permission_id", c, d)
               for c, d in PERMS.items()}
    role_id = {}
    for code, name, combat, perms in ROLES:
        role_id[code] = one("INSERT INTO role (code, name, combat_rights) VALUES (%s, %s, %s) RETURNING role_id",
                            code, name, combat)
        for p in perms.split():
            q("INSERT INTO role_permission (role_id, permission_id) VALUES (%s, %s)", role_id[code], perm_id[p])
    sectors = []
    for i in range(12):
        r_, c_ = divmod(i, 4)
        la0, lo0 = LAT0 + r_ * 0.4, LON0 + c_ * 0.6
        poly = [[lo0, la0], [lo0 + 0.6, la0], [lo0 + 0.6, la0 + 0.4], [lo0, la0 + 0.4], [lo0, la0]]
        zt = "зона відповідальності" if i not in (5, 10) else ("заборона ураження" if i == 5 else
                                                              "коридор дружньої авіації")
        sectors.append((one("INSERT INTO sector (code, name, zone_type, boundary, valid_from) VALUES "
                            "(%s, %s, %s, %s, %s) RETURNING sector_id", f"С-{i + 1:02d}", f"Сектор {i + 1}", zt,
                            Jsonb({"type": "Polygon", "coordinates": [poly]}), now - timedelta(days=90)),
                        la0 + 0.2, lo0 + 0.3))
    sec_of = lambda la, lo: sectors[min(2, max(0, int((la - LAT0) / 0.4))) * 4 +              # noqa: E731
                                    min(3, max(0, int((lo - LON0) / 0.6)))][0]
    model_id = [one("INSERT INTO interceptor_model (name, max_speed_kmh, range_km, endurance_min, wind_limit_mps, "
                    "night_capable, reusable) VALUES (%s,%s,%s,%s,%s,%s,%s) RETURNING model_id", *m) for m in MODELS]

    # ------------------------------------------------------------------ основні
    objs = []
    for name, cat in OBJECTS:
        la, lo = R.uniform(51.05, 51.55), R.uniform(30.6, 32.6)
        objs.append((one("INSERT INTO protected_object (sector_id, name, category, lat, lon) VALUES "
                         "(%s,%s,%s,%s,%s) RETURNING object_id", sec_of(la, lo), name, cat, round(la, 6),
                         round(lo, 6)), la, lo))
    sensors = []
    kinds = ["акустичний"] * 24 + ["радіолокаційний"] * 6 + ["оптико-електронний"] * 6 + ["радіотехнічний"] * 4
    for i, k in enumerate(kinds):
        la, lo = R.uniform(51.3, 52.15), R.uniform(30.5, 32.7)
        st = "поза мережею" if i in (7, 19) else "деградований" if i in (3, 11, 28) else \
             "у карантині" if i == 33 else "у мережі"
        serial = {"акустичний": "AC", "радіолокаційний": "RD", "оптико-електронний": "EO",
                  "радіотехнічний": "RF"}[k] + f"-{i + 1:04d}"
        sensors.append((one("INSERT INTO sensor (sector_id, hw_serial, kind, status, lat, lon, height_m) VALUES "
                            "(%s,%s,%s,%s,%s,%s,%s) RETURNING sensor_id", sec_of(la, lo), serial, k, st,
                            round(la, 6), round(lo, 6), R.choice([4.0, 6.0, 8.0, 12.0])), serial, la, lo, st))
    for i in range(2):                                 # пости візуального спостереження (ручні донесення)
        la, lo = 51.62 + 0.21 * i, 31.05 + 0.9 * i
        one("INSERT INTO sensor (sector_id, hw_serial, kind, status, lat, lon, height_m) VALUES "
            "(%s,%s,%s,%s,%s,%s,%s) RETURNING sensor_id", sec_of(la, lo), f"OB-{i + 1:04d}", "пост спостереження",
            "у мережі", la, lo, 2.0)
    online = [s for s in sensors if s[4] in ("у мережі", "деградований")]
    positions = []
    for i in range(10):
        la, lo = R.uniform(51.2, 51.75), R.uniform(30.7, 32.5)
        positions.append((one("INSERT INTO position (sector_id, code, status, lat, lon, engagement_radius_m) VALUES "
                              "(%s,%s,%s,%s,%s,%s) RETURNING position_id", sec_of(la, lo), f"П-{i + 1:02d}",
                              "активна" if i != 9 else "передислокація", round(la, 6), round(lo, 6),
                              R.choice([8000, 10000, 12000])), la, lo))
    crews = []
    for i in range(18):
        pos = positions[i % 10]
        crews.append([one("INSERT INTO crew (position_id, call_sign, status) VALUES (%s,%s,%s) RETURNING crew_id",
                          pos[0], f"{CALL[i % 6]}-{i // 6 + 1}", "готовий" if i < 16 else "недоступний"), pos])
    pw_hash = generate_password_hash(DEMO_PASSWORD)
    names = iter(R.sample([f"{s} {a}. {b}." for s in SURN for a in INIT for b in INIT], 80))
    users = {}

    def person(code, login, crew=None, rank="лейтенант"):
        uid = one("INSERT INTO personnel (role_id, crew_id, full_name, rank, login, admission_valid_to, "
                  "password_hash) VALUES (%s,%s,%s,%s,%s,%s,%s) RETURNING user_id", role_id[code], crew, next(names),
                  rank, login, (now + timedelta(days=R.randint(60, 700))).date(), pw_hash)
        users.setdefault(code, []).append(uid)
        return uid

    for i in range(4):
        person("R-01", f"och{i + 1}", rank="майор")
        person("R-02", f"obu{i + 1}", rank="капітан")
        person("R-03", f"an{i + 1}", rank="старший лейтенант")
    cmd = {}
    for i, c in enumerate(crews):
        cmd[c[0]] = person("R-04", f"cmd{i + 1:02d}", c[0], "старший сержант")
        person("R-05", f"pilot{i + 1:02d}", c[0], "сержант")
    for code, n, rank in (("R-06", 2, "солдат"), ("R-07", 3, "сержант"), ("R-08", 2, "капітан"),
                          ("R-09", 1, "капітан"), ("R-10", 1, "капітан"), ("R-11", 1, "майор"),
                          ("R-12", 1, "полковник"), ("R-13", 1, "майор")):
        for i in range(n):
            person(code, f"{code.lower().replace('-', '')}_{i + 1}", rank=rank)
    q("UPDATE personnel SET mfa_enabled = false WHERE login = 'r06_2'")
    q("UPDATE personnel SET status = 'призупинений' WHERE login = 'r07_3'")
    ints = []
    for i in range(60):
        m = i % 4
        pos = positions[i % 10]
        ints.append(one("INSERT INTO interceptor (model_id, position_id, serial_no, state, firmware_version, "
                        "received_at) VALUES (%s,%s,%s,%s,%s,%s) RETURNING interceptor_id", model_id[m],
                        pos[0] if i < 56 else None, f"ПХ-{1100 + i:05d}", "готовий" if i < 56 else "на складі",
                        f"4.{R.randint(1, 3)}.{R.randint(0, 9)}", (now - timedelta(days=R.randint(20, 120))).date()))
    conn.commit()

    # ------------------------------------------------------------------ операційні: треки через fn_ingest_detection
    def fly(t0, n_steps, start, target, speed, sig, sensors_per_step=3):
        la, lo = start
        tla, tlo = target
        dn, de = (tla - la) * 111.0, (tlo - lo) * 111.0 * math.cos(math.radians(la))
        d = math.hypot(dn, de)
        un, ue = dn / d, de / d
        track = None
        for k in range(n_steps):
            ts = t0 + timedelta(seconds=5 * k)
            cla, clo = pt(la, lo, un * speed * 5 * k / 1000, ue * speed * 5 * k / 1000)
            near = sorted(online, key=lambda s: (s[2] - cla) ** 2 + (s[3] - clo) ** 2)[:4]
            for s in R.sample(near, sensors_per_step):
                nla, nlo = pt(cla, clo, R.gauss(0, 0.15), R.gauss(0, 0.15))
                track = cur.execute("SELECT track_id FROM fn_ingest_detection(%s, %s, %s::numeric, %s::numeric, %s::numeric, "
                                    "%s::numeric, %s::numeric, %s, %s::numeric)",
                                    (s[1], ts + timedelta(milliseconds=R.randint(0, 900)), round(nla, 6),
                                     round(nlo, 6), R.randint(80, 400), round(speed + R.gauss(0, 2), 1),
                                     round(R.uniform(0, 360), 2), sig, round(R.uniform(0.62, 0.97), 2))
                                    ).fetchone()[0]
        return track

    def classify(track, ts, ident="ворожа", ttype="ударний БпЛА"):
        user(R.choice(users["R-03"]))
        q("SELECT fn_classify_track(%s, %s, %s)", track, ident, ttype)

    def start_point(obj):
        ang = R.uniform(-0.9, 0.9)
        return pt(obj[1], obj[2], 45 * math.cos(ang), 45 * math.sin(ang))   # ≈ 45 км північніше об’єкта

    # історія: 30 діб, 34 треки; 28 з них отримують місії
    plan = (["hit"] * 17 + ["miss"] * 5 + ["abort"] * 2 + ["reject"] * 2 + ["reassign"] * 2 + [None] * 6)
    R.shuffle(plan)
    stats = {}
    for n, outcome in enumerate(plan):
        t0 = now - timedelta(days=30) + timedelta(hours=n * 21 + R.randint(0, 5), minutes=R.randint(0, 59))
        obj = R.choice(objs)
        track = fly(t0, R.randint(4, 7), start_point(obj), (obj[1], obj[2]), R.uniform(42, 58), R.choice(SIGS[:3]))
        t_cls = t0 + timedelta(seconds=40)
        classify(track, t_cls, "ворожа" if outcome else R.choice(["невідома", "дружня"]),
                 "ударний БпЛА" if outcome else "невстановлений")
        conn.commit()
        if outcome is None:
            q("UPDATE air_track SET state = 'втрачений' WHERE track_id = %s", track)
            conn.commit()
            continue
        mission_lifecycle(cur, q, one, user, at, users, cmd, crews, track, t_cls, outcome, n, R, ints)
        conn.commit()
        stats[outcome] = stats.get(outcome, 0) + 1

    # завершення історії: треки без результату «знищений» вийшли з району або втрачені
    q("UPDATE air_track SET state = 'втрачений' WHERE state NOT IN ('знищений', 'втрачений')")
    conn.commit()

    # «живі» треки: останні хвилини, утворюють чергу загроз
    live = []
    for n in range(6):
        obj = objs[n * 2]
        t0 = now - timedelta(seconds=40 + 25 * n)
        track = fly(t0, 5, start_point(obj), (obj[1], obj[2]), R.uniform(45, 55), SIGS[n % 3], 2 + n % 2)
        live.append(track)
    for tr in live[:4]:
        classify(tr, now)
    conn.commit()
    # дві активні місії: санкціонована та виконується
    for k, tr in enumerate(live[:2]):
        crew = crews[k * 5]
        user(users["R-02"][0]); at(None)
        mid = one("SELECT fn_propose_mission(%s, %s)", tr, crew[0])
        user(users["R-01"][0])
        q("UPDATE mission SET state = 'санкціонована' WHERE mission_id = %s", mid)
        if k == 1:
            user(cmd[crew[0]])
            q("UPDATE mission SET state = 'прийнята' WHERE mission_id = %s", mid)
            itc = one("SELECT interceptor_id FROM interceptor WHERE position_id = %s AND state = 'готовий' LIMIT 1",
                      crew[1][0])
            q("UPDATE mission SET state = 'виконується', interceptor_id = %s WHERE mission_id = %s", itc, mid)
        conn.commit()
    if rich:
        stats["демо"] = enrich(cur, q, one, user, at, conn, now, objs, positions, crews, users, cmd, model_id, sec_of,
                               live, fly, classify, start_point, person, ints)
    user(None); at(None)
    conn.commit()
    return stats


def enrich(cur, q, one, user, at, conn, now, objs, positions, crews, users, cmd, model_id, sec_of, live, fly,
           classify, start_point, person, ints):
    """Розширений набір для живої демонстрації: фільтри, сторінки списків і дії кожної ролі мають на чому працювати."""
    R2 = random.Random(26)
    for name, cat in EXTRA_OBJECTS:
        la, lo = R2.uniform(51.05, 51.55), R2.uniform(30.6, 32.6)
        objs.append((one("INSERT INTO protected_object (sector_id, name, category, lat, lon) VALUES "
                         "(%s,%s,%s,%s,%s) RETURNING object_id", sec_of(la, lo), name, cat, round(la, 6),
                         round(lo, 6)), la, lo))
    statuses = ["у мережі"] * 18 + ["деградований"] * 4 + ["поза мережею"] * 3 + ["у карантині"] * 2 + \
               ["зареєстрований"] * 2 + ["виведений"]
    kinds = ["акустичний", "радіолокаційний", "оптико-електронний", "радіотехнічний", "акустичний"]
    for i, st in enumerate(statuses):
        k = kinds[i % 5]
        la, lo = R2.uniform(51.1, 52.15), R2.uniform(30.5, 32.7)
        hb = None if st in ("зареєстрований", "виведений") else \
            now - (timedelta(hours=R2.randint(3, 72)) if st == "поза мережею" else timedelta(seconds=R2.randint(5, 600)))
        q("INSERT INTO sensor (sector_id, hw_serial, kind, status, lat, lon, height_m, last_heartbeat_at) VALUES "
          "(%s,%s,%s,%s,%s,%s,%s,%s)", sec_of(la, lo), {"акустичний": "AC", "радіолокаційний": "RD",
                                                       "оптико-електронний": "EO", "радіотехнічний": "RF"}[k] +
          f"-{41 + i:04d}", k, st, round(la, 6), round(lo, 6), R2.choice([4.0, 6.0, 8.0, 12.0]), hb)
    la, lo = 51.9, 30.9
    q("INSERT INTO position (sector_id, code, status, lat, lon, engagement_radius_m) VALUES (%s,%s,%s,%s,%s,%s)",
      sec_of(la, lo), "П-11", "неактивна", la, lo, 8000)
    no = 1200
    for pos in positions:                         # поповнення позицій: на них витрачатиметься історія
        for k in range(24):
            q("INSERT INTO interceptor (model_id, position_id, serial_no, state, firmware_version, received_at) "
              "VALUES (%s,%s,%s,'готовий',%s,%s)", model_id[(no + k) % 4], pos[0], f"ПХ-{no:05d}",
              f"4.{R2.randint(1, 3)}.{R2.randint(0, 9)}", (now - timedelta(days=R2.randint(130, 170))).date())
            no += 1
    for k in range(16):
        q("INSERT INTO interceptor (model_id, position_id, serial_no, state, firmware_version, received_at) "
          "VALUES (%s,NULL,%s,%s,%s,%s)", model_id[k % 4], f"ПХ-{no:05d}", "на складі" if k < 12 else "втрачений",
          f"4.{R2.randint(1, 3)}.{R2.randint(0, 9)}", (now - timedelta(days=R2.randint(5, 60))).date())
        no += 1
    conn.commit()

    # ще 120 треків за 34–124 доби до запуску; «живі» треки на цей час виведено з зіставлення
    saved = cur.execute("SELECT track_id, state FROM air_track WHERE track_id = ANY(%s)", (live,)).fetchall()
    q("UPDATE air_track SET state = 'переданий' WHERE track_id = ANY(%s)", live)
    pool = [c for i, c in enumerate(crews[:16]) if i not in (0, 5)]      # 0 і 5 зайняті активними місіями
    pool = (pool * 2)[:16]
    plan = ["hit"] * 60 + ["miss"] * 18 + ["abort"] * 8 + ["reject"] * 7 + ["reassign"] * 7 + [None] * 20
    R2.shuffle(plan)
    stats = {}
    for n, outcome in enumerate(plan):
        t0 = now - timedelta(days=124) + timedelta(hours=n * 18 + R2.randint(0, 5), minutes=R2.randint(0, 59))
        obj = R2.choice(objs)
        track = fly(t0, R2.randint(4, 7), start_point(obj), (obj[1], obj[2]), R2.uniform(42, 58), R2.choice(SIGS))
        t_cls = t0 + timedelta(seconds=40)
        classify(track, t_cls, "ворожа" if outcome else R2.choice(["невідома", "дружня", "нейтральна"]),
                 "ударний БпЛА" if outcome else R2.choice(["невстановлений", "розвідувальний БпЛА", "цивільний"]))
        conn.commit()
        if outcome is None:
            q("UPDATE air_track SET state = %s WHERE track_id = %s", R2.choice(["втрачений", "переданий", "скинутий"]),
              track)
        else:
            mission_lifecycle(cur, q, one, user, at, users, cmd, pool, track, t_cls, outcome, n, R2, ints)
            stats[outcome] = stats.get(outcome, 0) + 1
        conn.commit()
    q("UPDATE air_track SET state = 'втрачений' WHERE state NOT IN ('знищений', 'втрачений', 'переданий', 'скинутий') "
      "AND track_id <> ALL(%s)", live)
    for tid, st in saved:
        q("UPDATE air_track SET state = %s WHERE track_id = %s", st, tid)
    user(None); at(None)
    conn.commit()

    # ще 6 «живих» треків; місії, що чекають дії: санкції ОЧ, прийняття розрахунком, пуску
    new = []
    for n in range(6):
        obj = objs[n * 2 + 1]
        new.append(fly(now - timedelta(seconds=30 + 20 * n), 5, start_point(obj), (obj[1], obj[2]),
                       R2.uniform(45, 55), SIGS[(n + 1) % 4], 2 + n % 2))
    for tr in new[:4]:
        classify(tr, now)
    conn.commit()
    for k, (tr, crew, to) in enumerate(((new[0], crews[6], None), (new[1], crews[7], None),
                                        (new[2], crews[1], "санкціонована"), (new[3], crews[2], "прийнята"))):
        user(users["R-02"][1 + k % 3]); at(None)
        mid = one("SELECT fn_propose_mission(%s, %s)", tr, crew[0])
        if to:
            user(users["R-01"][k % 4])
            q("UPDATE mission SET state = 'санкціонована' WHERE mission_id = %s", mid)
        if to == "прийнята":
            user(cmd[crew[0]])
            q("UPDATE mission SET state = 'прийнята' WHERE mission_id = %s", mid)
        conn.commit()
    user(None)
    for code, login, status in (("R-03", "an5", "відкликаний"), ("R-06", "r06_3", "призупинений"),   # для фільтра
                                ("R-07", "r07_4", "відкликаний"), ("R-08", "r08_3", "активний")):     # «Стан»
        uid = person(code, login)
        q("UPDATE personnel SET status = %s WHERE user_id = %s", status, uid)
    conn.commit()
    return stats


def mission_lifecycle(cur, q, one, user, at, users, cmd, crews, track, t_cls, outcome, n, R, ints):
    """Повний життєвий цикл історичної місії через переходи стану (тригери перевіряють кожен крок)."""
    crew = crews[n % 16]
    obu, och = R.choice(users["R-02"]), R.choice(users["R-01"])
    t_prop = t_cls + timedelta(seconds=R.randint(30, 90))
    user(obu); at(t_prop)
    mid = one("INSERT INTO mission (mission_no, track_id, crew_id, proposed_by, proposed_at) VALUES "
              "(%s,%s,%s,%s,%s) RETURNING mission_id", f"М-{t_prop:%m%d}-{NUM.setdefault(t_prop.date(), 0) + 1:02d}", track, crew[0], obu,
              t_prop)
    NUM[t_prop.date()] += 1
    t = t_prop + timedelta(seconds=R.randint(12, 55))
    user(och); at(t)
    if outcome == "reject":
        q("UPDATE mission SET state = 'відхилена', closed_at = %s WHERE mission_id = %s", t, mid)
        return
    q("UPDATE mission SET state = 'санкціонована', approved_at = %s WHERE mission_id = %s", t, mid)
    if outcome == "reassign":                    # розрахунок не підтвердив за 15 с — перепризначення
        t += timedelta(seconds=16)
        user(och); at(t)                          # перепризначає ОЧ і стає автором нової пропозиції
        q("UPDATE mission SET state = 'перепризначена' WHERE mission_id = %s", mid)
        crew = crews[(n + 3) % 16]
        t += timedelta(seconds=8); at(t)
        q("UPDATE mission SET state = 'запропонована', crew_id = %s WHERE mission_id = %s", crew[0], mid)
        t += timedelta(seconds=R.randint(10, 30))
        user(next(u for u in users["R-01"] if u != och)); at(t)     # санкціонує інший ОЧ
        q("UPDATE mission SET state = 'санкціонована', approved_at = %s WHERE mission_id = %s", t, mid)
        outcome = "hit"
    t += timedelta(seconds=R.randint(4, 12))
    user(cmd[crew[0]]); at(t)
    q("UPDATE mission SET state = 'прийнята' WHERE mission_id = %s", mid)
    t += timedelta(seconds=R.randint(15, 50))
    itc = one("SELECT interceptor_id FROM interceptor WHERE position_id = %s AND state = 'готовий' "
              "ORDER BY serial_no LIMIT 1", crew[1][0])
    at(t)
    q("UPDATE mission SET state = 'виконується', interceptor_id = %s, launched_at = %s WHERE mission_id = %s",
      itc, t, mid)
    # телеметрія: кадр кожні 10 с від позиції до точки зустрічі
    la, lo = crew[1][1], crew[1][2]
    tla, tlo = one("SELECT lat FROM fn_track_pos(%s)", track), one("SELECT lon FROM fn_track_pos(%s)", track)
    dur = R.randint(120, 260)
    for k in range(0, dur, 10):
        f = k / dur
        q("INSERT INTO telemetry_frame (interceptor_id, ts, mission_id, lat, lon, alt_m, ground_speed_mps, "
          "battery_pct, link_quality_pct) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)", itc, t + timedelta(seconds=k), mid,
          round(la + (float(tla) - la) * f, 6), round(lo + (float(tlo) - lo) * f, 6), round(150 + 200 * f, 1),
          round(R.uniform(60, 85), 1), max(5, 100 - int(70 * f) - R.randint(0, 5)), R.randint(70, 99))
    t += timedelta(seconds=dur)
    at(t)
    if outcome == "abort":
        q("UPDATE mission SET state = 'скасована', abort_reason = 'ціль змінила курс за межі сектора' "
          "WHERE mission_id = %s", mid)
        return
    t += timedelta(seconds=R.randint(30, 90)); at(t)
    q("INSERT INTO engagement_report (mission_id, assessment, evidence, submitted_by, submitted_at, "
      "sent_to_higher_at) VALUES (%s,%s,%s,%s,%s,%s)", mid, "влучання" if outcome == "hit" else "промах",
      Jsonb({"відео": f"obj://video/{mid}.mp4", "підтвердження_сенсорів": R.randint(1, 3)}), cmd[crew[0]], t,
      t + timedelta(minutes=R.randint(3, 15)))

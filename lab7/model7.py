"""Lab 7: conceptual IoT architecture of IoT-платформа «Щит-Лінк» (hypothetical РЦПДО «Щит-Північ»).
Components follow DOMAIN_KNOWLEDGE_BASE.md §6; layers follow the brief (6 levels, top = business)."""

ARCH = {
    "kind": "layers", "slots": 5,
    "bands": [
        {"name": "6. Бізнес-рівень (управління)", "items": [
            {"id": "B0", "name": "Рішення на пуск", "slot": 0},
            {"id": "B1", "name": "Правила і зони заборони", "slot": 1},
            {"id": "B2", "name": "KPI і звітність", "slot": 2},
            {"id": "B3", "name": "Сценарії оповіщення", "slot": 3},
            {"id": "B4", "name": "Планування ресурсів", "slot": 4}],
         "side": {"id": "U_HQ", "name": "Начальник центру, вищий КП"}},
        {"name": "5. Прикладний рівень", "items": [
            {"id": "A0", "name": "АРМ командного пункту", "slot": 0, "sec": ["S1"]},
            {"id": "A1", "name": "Адмін-\nконсоль", "slot": 1, "sec": ["S1"]},
            {"id": "A2", "name": "Панель KPI", "slot": 2},
            {"id": "A3", "name": "Сервіс сповіщень", "slot": 3},
            {"id": "A4", "name": "Застосунок розрахунку", "slot": 4, "sec": ["S1"]}],
         "side": {"id": "U_ST", "name": "Персонал КП, розрахунки, аналітики"}},
        {"name": "4. Рівень оброблення і зберігання", "items": [
            {"id": "C0", "name": "API-шлюз", "slot": 0, "sec": ["S1", "S3"]},
            {"id": "C1", "name": "Брокер і шина подій", "slot": 1, "sec": ["S4"]},
            {"id": "C2", "name": "Бази даних", "slot": 2, "sec": ["S4", "S5"]},
            {"id": "C3", "name": "Сервіси обробки", "slot": 3, "sec": ["S5"]},
            {"id": "C4", "name": "Шлюз інтеграції", "slot": 4, "sec": ["S2"]}],
         "side": {"id": "X_EXT", "name": "DELTA, ПС ЗСУ, ДСНС, метеосервіс"}},
        {"name": "3. Рівень периферійного оброблення (Edge)", "items": [
            {"id": "E0", "name": "Протокольні адаптери", "slot": 0},
            {"id": "E1", "name": "Локальне злиття треків", "slot": 1},
            {"id": "E2", "name": "Edge-шлюз позиції", "slot": 2, "sec": ["S1", "S2"]},
            {"id": "E3", "name": "НСУ розрахунку", "slot": 3, "sec": ["S1"]}]},
        {"name": "2. Мережевий рівень", "items": [
            {"id": "N0", "name": "Ethernet, захищена ЛОМ", "slot": 0},
            {"id": "N1", "name": "LoRaWAN, LTE-M", "slot": 1, "sec": ["S2"]},
            {"id": "N2", "name": "Ethernet, Wi-Fi позиції", "slot": 2},
            {"id": "N3", "name": "Радіоканал БпЛА", "slot": 3, "sec": ["S2"]}]},
        {"name": "1. Фізичний рівень (сприйняття)", "items": [
            {"id": "P0", "name": "РЛС і оптичні пости", "slot": 0},
            {"id": "P1", "name": "Акустичні сенсори", "slot": 1},
            {"id": "P2", "name": "Сирени і табло позиції", "slot": 2},
            {"id": "P3", "name": "Дрони-\nперехоп-\nлювачі", "slot": 3}],
         "side": {"id": "X_TGT", "name": "Повітряні цілі (об’єкт моніторингу)"}},
    ],
    "links": [
        # physical → network → edge (data up)
        {"src": "P0", "dst": "N0", "label": "ASTERIX", "kind": "data"},
        {"src": "N0", "dst": "E0", "label": "UDP", "kind": "data", "dx2": -22},
        {"src": "P1", "dst": "N1", "label": "MQTT-SN", "kind": "data"},
        {"src": "N1", "dst": "E0", "label": "MQTT/TLS", "kind": "data", "dx2": 22},
        {"src": "P3", "dst": "N3", "label": "MAVLink 2", "kind": "both"},
        {"src": "N3", "dst": "E3", "kind": "both"},
        {"src": "N2", "dst": "P2", "kind": "cmd"},
        {"src": "E2", "dst": "N2", "label": "команди", "kind": "cmd"},
        {"src": "P3", "dst": "X_TGT", "label": "перехоплення", "kind": "cmd"},
        # edge
        {"src": "E0", "dst": "E1", "kind": "data"},
        {"src": "E1", "dst": "E2", "kind": "data"},
        {"src": "E3", "dst": "E2", "kind": "both"},
        {"src": "E2", "dst": "C1", "label": "MQTT-міст, VPN", "kind": "both", "dx": -24, "dx2": 24},
        # platform
        {"src": "C0", "dst": "C1", "label": "gRPC", "kind": "both"},
        {"src": "C1", "dst": "C2", "kind": "data"},
        {"src": "C2", "dst": "C3", "kind": "both"},
        {"src": "C3", "dst": "C4", "kind": "both"},
        {"src": "C4", "dst": "X_EXT", "label": "CoT", "kind": "both"},
        # application ↔ API (bus)
        {"src": "A0", "dst": "C0", "label": "HTTPS, WSS", "kind": "both"},
        {"src": "A1", "dst": "C0", "kind": "both"},
        {"src": "A2", "dst": "C0", "kind": "both"},
        {"src": "A3", "dst": "C0", "kind": "both"},
        {"src": "A4", "dst": "C0", "kind": "both"},
        # business ↔ application
        {"src": "B0", "dst": "A0", "kind": "both"},
        {"src": "B1", "dst": "A1", "kind": "cmd"},
        {"src": "A2", "dst": "B2", "kind": "data"},
        {"src": "B3", "dst": "A3", "kind": "cmd"},
        {"src": "A4", "dst": "B4", "kind": "data"},
    ],
}

SECURITY = [
    ("S1", "Автентифікація та авторизація", "API-шлюз, АРМ КП, консоль, застосунок розрахунку, периферійний шлюз, НСУ",
     "OIDC + MFA для користувачів, X.509-сертифікати пристроїв, RBAC/ABAC за роллю і сектором"),
    ("S2", "Шифрування передавання даних", "LoRaWAN/LTE-M, радіоканал БпЛА, периферійний шлюз, шлюз інтеграції",
     "TLS 1.3 / mTLS, тунель WireGuard між периферією і ядром, підписування повідомлень MAVLink 2"),
    ("S3", "Захист API", "API-шлюз",
     "Валідація схем запитів, обмеження частоти (rate limiting), короткоживучі токени, захист від повторів"),
    ("S4", "Контроль доступу до пристроїв і даних", "Брокер і шина подій, бази даних",
     "ACL на теми MQTT за ідентифікатором пристрою, розмежування доступу до таблиць, шифрування AES-256 на диску"),
    ("S5", "Журналювання подій", "Сервіси обробки, бази даних",
     "Незмінний журнал аудиту з ланцюгом хешів, централізований збір подій безпеки (SIEM), зберігання ≥ 3 років"),
]

FLOWS = {
    "kind": "dfd", "frame": False, "node": "", "title": "", "cw": 206, "pw": 150, "rh": 150,
    "columns": [{"name": "Фізичний", "cols": [0, 0]}, {"name": "Edge", "cols": [1, 1]},
                {"name": "Оброблення і зберігання", "cols": [2, 3]}, {"name": "Прикладний", "cols": [4, 4]}],
    "processes": [
        {"id": "E2", "name": "Edge-шлюз позиції", "col": 1, "row": 0},
        {"id": "E3", "name": "НСУ розрахунку", "col": 1, "row": 2},
        {"id": "C1", "name": "Брокер і шина подій", "col": 2, "row": 0},
        {"id": "C3", "name": "Сервіси злиття і класифікації", "col": 2, "row": 1},
        {"id": "C5", "name": "Сервіс призначень", "col": 2, "row": 2},
        {"id": "C6", "name": "Модуль аналітики KPI", "col": 3, "row": 0},
        {"id": "A0", "name": "АРМ командного пункту", "col": 4, "row": 1},
        {"id": "A2", "name": "Панель KPI і звіти", "col": 4, "row": 0},
    ],
    "stores": [{"id": "D1", "name": "Треки, телеметрія", "col": 3, "row": 1}],
    "externals": [
        {"id": "X1", "name": "Сенсори", "col": 0, "row": 0},
        {"id": "X2", "name": "Дрон-\nперехоплювач", "col": 0, "row": 2},
    ],
    "flows": [
        {"src": "X1", "dst": "E2", "label": "1. Виявлення (MQTT/TLS)", "route": "h"},
        {"src": "E2", "dst": "C1", "label": "2. Події / синхронізація", "route": "h", "bidir": True},
        {"src": "C1", "dst": "C3", "label": "3. Потік подій", "route": "v"},
        {"src": "C3", "dst": "D1", "label": "4. Треки", "route": "h"},
        {"src": "D1", "dst": "C6", "label": "5. Вибірки (SQL)", "route": "v"},
        {"src": "C6", "dst": "A2", "label": "6. Показники KPI", "route": "h"},
        {"src": "D1", "dst": "A0", "label": "7. Обстановка (WSS)", "route": "h"},
        {"src": "A0", "dst": "C5", "label": "8. Команда призначення (HTTPS)", "route": "vh"},
        {"src": "C5", "dst": "E3", "label": "9. Бойове завдання", "route": "h"},
        {"src": "E3", "dst": "X2", "label": "10. MAVLink 2", "route": "h", "bidir": True},
        {"src": "E3", "dst": "E2", "label": "11. Телеметрія місії", "route": "v"},
    ],
}

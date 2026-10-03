# DOMAIN KNOWLEDGE BASE
## Distributed IoT System for Telemetry Exchange and Coordination of Interceptor Drones
### (Розподілена IoT-система обміну телеметрією та координації дронів-перехоплювачів)

> **Purpose of this file.** A self-contained, plug-and-play reference for any human or AI session working on the
> "Information Systems Design" (ПІС) course project of Петро Кравченко (гр. ІР-31, КНУ ім. Тараса Шевченка, ФІТ,
> кафедра ІСТ; викладач — к.т.н. Гладка Мирослава Вікторівна). It fixes the **domain vocabulary, actors, processes,
> data model, architecture and Ukrainian terminology** so that all lab reports (BPMN, IDEF0/IDEF3/DFD, UML, architecture)
> stay mutually consistent.
>
> **Scope guard.** The system is modelled at the *information-system* level (who exchanges which data, which business
> rules apply, how the software is structured). Flight-control algorithms, guidance laws, warhead/effector engineering
> and electronic-warfare techniques are deliberately **out of scope** — they are neither needed for the course nor
> appropriate for an academic report. Engagements are always shown as **human-authorised** (human-in-the-loop).
>
> **Naming convention used everywhere:** the organisation is the fictional **Регіональний центр протидронової оборони
> «Щит-Північ» (РЦПДО «Щит-Північ»)**; the information system under design is **IoT-платформа «Щит-Лінк»**
> (*ShieldLink*). **Both are hypothetical (non-existent) entities created for this academic project; every report
> must say so explicitly.** Codes in brackets (e.g. `BP-04`, `E-07`, `R-03`) are stable identifiers — reuse them in diagrams.

---

## 0. Quick reference card

| Item | Value |
|---|---|
| Theme (verbatim, `My_theme.txt`) | Проєктування розподіленої IoT-системи обміну телеметрією та координації дронів-перехоплювачів |
| Object of research (об'єкт дослідження) | Діяльність РЦПДО «Щит-Північ» з виявлення, супроводу та перехоплення повітряних цілей (ударних БпЛА типу «Shahed/Герань», розвідувальних БпЛА) дронами-перехоплювачами |
| Subject of research (предмет дослідження) | Процеси збору, передачі, злиття телеметрії та координації розрахунків перехоплювачів, що підлягають автоматизації |
| System under design | IoT-платформа «Щит-Лінк» — розподілена інформаційно-управляюча система реального часу |
| System class (lecture terms) | Інформаційно-управляюча система; кіберфізична система (КФС); IIoT-система з периферійними обчисленнями; мультиагентна система (МАС) з інтерактивним супервізорним управлінням |
| Main value | Скорочення циклу «виявлення → рішення → перехоплення» з хвилин до десятків секунд; єдина ситуаційна картина; облік ресурсу перехоплювачів |
| Key NFRs | sensor→screen latency ≤ 2 s (p95); tasking command delivery ≤ 1 s (p95); availability 99.95 % core / autonomous edge operation ≥ 4 h offline; full audit trail |
| Notations used across labs | Дерево цілей, WBS (ЛР1) · BPMN 2.0 (ЛР2) · IDEF0, IDEF3, FEO, дерево вузлів (ЛР3) · DFD · UML 2.x · архітектурні схеми IoT |

---

## 1. Executive summary & domain scope

### 1.1 Operational context (real-world grounding, 2024–2026)
- Since 2022 Ukraine has been attacked nightly by long-range one-way attack drones (Shahed-136/«Герань-2», jet-powered
  «Герань-3»), decoys («Гербера») and reconnaissance UAVs. Many fly **extremely low**, which reduces radar visibility
  and increases dependence on short-range layers. [ISIS monthly analysis; Kyiv Post]
- Ukraine built a **layered air defence**: SAM systems, fighter aircraft, helicopters, **mobile fire groups (мобільні
  вогневі групи, МВГ)**, electronic warfare and — since 2025 at scale — **interceptor drones (дрони-перехоплювачі)**
  such as Wild Hornets *STING* (≈25 km reach, up to ≈315 km/h, deployable in ~15 min). Interceptor production exceeded
  1,000 units/day in 2026; intercept cost is a small fraction of a missile. [Kyiv Post; Defense News 2026; United24]
- The detection side is **distributed and heterogeneous**: the *Sky Fortress (Небесна фортеця)* network of
  >10,000–14,000 low-cost acoustic sensors (≈$400–1,000 each, total < $5 M), radars that feed NATO-compliant track data
  into the **DELTA** situational awareness ecosystem, visual observers, EO/IR cameras, RF sensors. [Wikipedia; United24]
- The typical kill chain: *acoustic early warning → radar tracking → EO/IR confirmation → cueing of an interceptor
  crew → launch → operator-confirmed terminal phase → result assessment* — within minutes. Interceptor operators work
  **shoulder-to-shoulder with the radar crew chief** and are "part FPV pilot, part air-defence crew". When the target is
  visually confirmed in the terminal phase, the operator confirms and the interceptor completes the approach
  autonomously. [Defense News; The Defender]
- The MoD is rolling out **Mission Control** within DELTA — a digital platform for drone operations with full
  analytics. Our system is modelled as a *regional* platform of the same class that interoperates with such
  national systems. [Rubryka 2026]

### 1.2 Core business problems solved
| # | Problem (AS-IS) | Consequence | TO-BE solution in «Щит-Лінк» |
|---|---|---|---|
| P1 | Detections from acoustic nodes, radars and observers arrive through different channels (radio, messengers, separate apps) | Duplicated/conflicting tracks, lost seconds | Unified ingestion via edge gateways + **track fusion** service |
| P2 | Manual voice cueing of crews ("ціль, азимут 120, 5 км") | 30–90 s delay, transcription errors | Digital **tasking** (призначення цілі) pushed to the crew tablet with track feed |
| P3 | No real-time view of which crews/interceptors are ready | Wrong crew tasked, idle reserves | **Readiness registry** with live states of crews, interceptors, batteries |
| P4 | Telemetry of interceptors not recorded centrally | No post-mission analytics, no learning loop | Time-series **telemetry archive**, mission replay |
| P5 | Risk of engaging friendly aircraft / falling debris over populated areas | Fratricide, civilian harm | **Deconfliction** with friendly flight plans, no-engagement zones, mandatory human authorisation |
| P6 | Communication jamming (РЕБ) disrupts links | Lost situational picture | Store-and-forward edge, link redundancy (mesh radio / LTE / satellite), degraded-mode procedures |
| P7 | Paper-based reporting of results and consumption | Slow resupply, disputed results (pay-per-intercept) | Automatic **engagement reports**, video evidence, consumption accounting |

### 1.3 High-level objectives (feed for the goal tree in ЛР1)
- **G0 (генеральна мета):** забезпечити своєчасне виявлення та ефективне перехоплення повітряних цілей у зоні
  відповідальності центру шляхом автоматизації обміну телеметрією та координації дронів-перехоплювачів.
- G1 Підвищити повноту та достовірність ситуаційної картини повітряного простору.
- G2 Скоротити час циклу «виявлення — рішення — перехоплення».
- G3 Забезпечити ефективне управління ресурсами (розрахунки, перехоплювачі, АКБ, позиції).
- G4 Гарантувати безпеку, надійність і кіберзахищеність функціонування системи.
- G5 Забезпечити аналітику, звітність та безперервне вдосконалення діяльності.

### 1.4 System boundaries
**In scope (автоматизується):** реєстрація сенсорів і периферійних вузлів; прийом/нормалізація телеметрії й виявлень;
злиття треків; класифікація та оцінка загрози (з підтвердженням людиною); облік готовності розрахунків і
перехоплювачів; підбір і призначення розрахунку; санкціонування пуску; моніторинг місії та телеметрії перехоплювача;
фіксація результату; оповіщення; деконфлікція з дружньою авіацією; аналітика, звіти, аудит; управління доступом.

**Out of scope (зовнішні системи/сутності):** національні системи ситуаційної обізнаності (DELTA / Mission Control),
система повітряної тривоги та оповіщення населення, мережа радарів ПС ЗСУ, постачальники перехоплювачів, системи
РЕБ, автопілоти та прошивки дронів (взаємодія лише через протокол телеметрії), складський облік МТЗ.

**Context-diagram view (IDEF0 A-0 / DFD level 0):**
- *Inputs (Входи):* сигнали акустичних сенсорів; радарні треки; донесення візуальних спостерігачів; відеопотоки EO/IR;
  телеметрія перехоплювачів; плани польотів дружньої авіації; дані про стан АКБ та техніки.
- *Controls (Управління):* накази та бойові розпорядження командування; правила застосування (ROE); Закон «Про
  оборону України»; Закон «Про захист інформації в інформаційно-комунікаційних системах»; вимоги КСЗІ; карта зон
  відповідальності та заборонених для ураження зон; інструкції з безпеки польотів; регламент координації з ПС ЗСУ.
- *Outputs (Виходи):* єдина повітряна обстановка; бойові завдання (призначення цілей) розрахункам; команди
  санкціонування; звіти про результати перехоплення; оповіщення; аналітичні звіти; заявки на поповнення ресурсу.
- *Mechanisms (Механізми):* черговий оперативний персонал (оперативний черговий, офіцер бойового управління);
  оператори перехоплювачів; технічний персонал; IoT-платформа «Щит-Лінк» (сервери, периферійні шлюзи, канали зв'язку);
  мережа сенсорів; дрони-перехоплювачі.

### 1.5 Regulatory & standards context (for "Управління" arrows and theory sections)
| Area | Document / standard | Use in project |
|---|---|---|
| Lifecycle & documentation | ДСТУ ISO/IEC/IEEE 12207:2018; ГОСТ 34.601-90 (стадії створення АС), ГОСТ 34.602-89 (ТЗ) | Stages in WBS, ТЗ structure |
| Report formatting | ДСТУ 3008:2015 «Звіти у сфері науки і техніки» | Reports layout |
| Information security | Закон України «Про захист інформації в інформаційно-комунікаційних системах»; НД ТЗІ (КСЗІ); ДСТУ ISO/IEC 27001:2015 | Security requirements |
| Industrial/IoT security | IEC 62443 (named in lecture 8–9), ISO/IEC 27001, IEC 61508 | Edge & OT security |
| UAS interoperability | NATO STANAG 4586 (UAS control system interoperability), STANAG 4609 (motion imagery/video) | Integration layer |
| Air track exchange | EUROCONTROL ASTERIX (CAT 048 radar plots, CAT 062 system tracks); Cursor-on-Target (CoT) XML | Radar/C2 interfaces |
| Drone telemetry | MAVLink 2 (with message signing) | Interceptor telemetry/commands |
| IoT messaging | MQTT 5 / MQTT-SN (OASIS) | Sensor & edge messaging |
| Symbology | NATO APP-6 / MIL-STD-2525 | Map symbology in UI |

---

## 2. Organisation model (object of research for ЛР1)

### 2.1 General information (загальні відомості)
**РЦПДО «Щит-Північ»** — регіональний центр протидронової оборони, що забезпечує прикриття критичної інфраструктури
та населених пунктів у зоні відповідальності (умовно: 3 райони області, ≈ 9 000 км², 14 об'єктів критичної
інфраструктури). Працює цілодобово у змінному режимі (3 зміни по 8 год або 2×12 год у періоди масованих атак).
Ресурс (умовно, для розрахунків): 120 акустичних сенсорів, 4 малогабаритні РЛС, 12 оптико-електронних постів, 18
розрахунків дронів-перехоплювачів на 9 позиціях, запас 300–600 перехоплювачів, ≈ 160 осіб особового складу.

### 2.2 Organisational structure (структурна схема)
```
Начальник центру
├── Заступник начальника з бойового управління
│   ├── Командний пункт (КП) / Оперативний черговий центр — 4 зміни
│   │   ├── Оперативний черговий (ОЧ)
│   │   ├── Офіцер бойового управління (ОБУ, «офіцер наведення»)
│   │   └── Оператор ситуаційної картини (аналітик повітряної обстановки)
│   ├── Відділ розвідки повітряного простору та сенсорних мереж
│   │   ├── Група акустичного моніторингу
│   │   ├── Розрахунки РЛС
│   │   └── Пости візуально-оптичного спостереження
│   └── Підрозділ дронів-перехоплювачів (18 розрахунків на 9 позиціях)
│       ├── Командир розрахунку
│       ├── Оператор (пілот) перехоплювача
│       └── Технік / штурман розрахунку
├── Заступник начальника з технічного забезпечення
│   ├── Служба зв'язку та ІТ (адміністратори «Щит-Лінк», мережі, кіберзахист)
│   ├── Технічна служба (ремонт і обслуговування БпЛА, АКБ, сенсорів)
│   └── Служба логістики (склад перехоплювачів, АКБ, ПММ, транспорт)
├── Відділ аналітики, планування та звітності
├── Навчально-тренувальний відділ (підготовка операторів, симулятор)
└── Сектор взаємодії (зв'язок з ПС ЗСУ, ДСНС, ОВА, суміжними центрами)
```

### 2.3 Departments: tasks & functions (таблиця «Задачі — функції»)
| Unit | Tasks (задачі) | Functions (функції) |
|---|---|---|
| КП / оперативний черговий центр | Цілодобове бойове управління; формування повітряної обстановки; прийняття рішень на перехоплення | Моніторинг треків; підтвердження класифікації; призначення цілей розрахункам; санкціонування пуску; координація з ПС ЗСУ; ведення журналу бойового чергування |
| Відділ розвідки повітряного простору | Своєчасне виявлення повітряних цілей | Експлуатація сенсорної мережі; верифікація виявлень; калібрування; контроль покриття; передача донесень |
| Підрозділ перехоплювачів | Перехоплення цілей | Підтримання готовності; підготовка до пуску; пілотування/супровід; доповідь про результат; повернення/евакуація |
| Служба зв'язку та ІТ | Безперервність зв'язку та роботи ІС | Адміністрування платформи; резервування каналів; PKI та ключі; моніторинг інцидентів кібербезпеки; оновлення ПЗ |
| Технічна служба | Справність техніки | Передпольотний/післяпольотний контроль; ремонт; облік ресурсу АКБ; списання |
| Служба логістики | Забезпеченість ресурсами | Облік запасів; розподіл по позиціях; заявки на поповнення; транспортування |
| Відділ аналітики та звітності | Оцінка ефективності, планування | Аналіз результатів; KPI; добові/місячні звіти; планування розташування позицій; уроки (lessons learned) |
| Навчально-тренувальний відділ | Підготовка кадрів | Курси операторів; тренування на симуляторі; атестація; допуск до чергування |
| Сектор взаємодії | Узгодженість дій | Обмін обстановкою з ПС ЗСУ/суміжними центрами; погодження польотів дружньої авіації; інформування ОВА/ДСНС |

### 2.4 Functional interconnections (таблиця взаємозв'язків: одержання ↔ надання) — core of ЛР1 table
| With unit | КП **receives** | КП **provides** |
|---|---|---|
| Відділ розвідки повітряного простору | виявлення та треки; стан і покриття сенсорів; донесення спостерігачів; відео | вимоги до зон спостереження; запити на доуточнення цілі; розпорядження щодо переміщення постів |
| Підрозділ перехоплювачів | доповіді про готовність; телеметрію; підтвердження прийняття завдання; доповіді про результат і витрату | бойові завдання (призначення цілей); дозвіл/заборону пуску; команди на скасування; дані цілевказання |
| Служба зв'язку та ІТ | стан каналів і вузлів; повідомлення про інциденти; графік оновлень | вимоги до пріоритету трафіку; заявки на відновлення зв'язку; права доступу персоналу |
| Технічна служба | стан справності перехоплювачів, АКБ, сенсорів; прогноз готовності | дані про відмови та втрати; наліт/ресурс за місію; заявки на ремонт |
| Служба логістики | залишки перехоплювачів та АКБ по позиціях; графік підвезення | фактичну витрату; заявки на перерозподіл; прогноз потреби |
| Відділ аналітики | аналітичні звіти, рекомендації з розміщення позицій, KPI | журнали бойового чергування; результати перехоплень; записи місій |
| Навчально-тренувальний відділ | списки допущених операторів, результати атестації | типові помилки, сценарії для тренувань, потреби в підготовці |
| Сектор взаємодії / ПС ЗСУ | плани польотів дружньої авіації; загальна повітряна обстановка; розпорядження вищого КП | донесення про обстановку та результати; запити на погодження |

---

## 3. Stakeholder & actor matrix

### 3.1 Human actors (ролі користувачів, RBAC)
| Code | Role (UA) | Role (EN) | Business goals | Key permissions | Usage frequency |
|---|---|---|---|---|---|
| R-01 | Оперативний черговий (ОЧ) | Duty Operations Officer | Цілісна обстановка, своєчасні рішення | Перегляд усього; підтвердження класифікації; санкціонування пуску; оголошення режимів готовності | Безперервно на зміні |
| R-02 | Офіцер бойового управління (ОБУ) | Fire Control / Tasking Officer | Оптимальне призначення розрахунків | Створення/зміна бойових завдань; пропозиція пуску; скасування місії | Безперервно, пікові навантаження під час атак |
| R-03 | Аналітик повітряної обстановки | Air Picture Analyst | Достовірні треки | Злиття/розділення треків; класифікація; позначення хибних цілей | Безперервно |
| R-04 | Командир розрахунку перехоплювачів | Interceptor Crew Commander | Готовність і виконання завдань | Прийняття/відхилення завдання; доповідь про готовність і результат | Десятки разів за ніч атаки |
| R-05 | Оператор (пілот) перехоплювача | Interceptor Pilot | Успішне перехоплення, збереження ресурсу | Перегляд цілевказання; керування місією через НСУ; підтвердження фази наведення | Під час місій |
| R-06 | Оператор сенсорного поста / спостерігач | Sensor Post Operator / Observer | Повні донесення | Створення ручних донесень; підтвердження виявлень | Періодично |
| R-07 | Технік (БпЛА / сенсори) | Maintenance Technician | Справність техніки | Облік обслуговувань, статуси справності, списання | Щоденно |
| R-08 | Логіст | Logistics Officer | Наявність ресурсу на позиціях | Облік запасів, переміщень, заявок | Щоденно |
| R-09 | Аналітик ефективності / офіцер звітності | Performance Analyst | Об'єктивна оцінка, звітність | Читання архіву, побудова звітів, повтор місій (replay) | Щоденно/щотижня |
| R-10 | Адміністратор системи | System Administrator | Доступність і безпека ІС | Управління користувачами, ролями, вузлами, ключами; без бойових прав | Щоденно |
| R-11 | Офіцер кібербезпеки | Security Officer | Захищеність | Читання журналів аудиту, реагування на інциденти, блокування облікових записів | Щоденно / за подіями |
| R-12 | Начальник центру | Centre Commander | Виконання завдань, ресурсна стратегія | Перегляд дашбордів, затвердження ROE/зон, звіти | Щоденно |
| R-13 | Інструктор | Instructor | Підготовка операторів | Сценарії симуляції, оцінювання | Щотижня |

**Separation of duties (розмежування обов'язків):** R-02 proposes, R-01 authorises launch (two-person rule for
engagements near no-engagement zones); R-10 has no operational rights; R-11 reads audit but cannot edit it.

### 3.2 System actors (системні ролі, M2M)
| Code | Actor | Interaction |
|---|---|---|
| S-01 | Акустичний сенсорний вузол | Publishes detections (bearing, signature class, confidence) via MQTT to edge gateway |
| S-02 | Малогабаритна РЛС | Streams plots/tracks (ASTERIX CAT048/062) to radar adapter |
| S-03 | Оптико-електронний пост (EO/IR камера) | Video stream (STANAG 4609 / RTSP) + detections |
| S-04 | Дрон-перехоплювач (автопілот) | MAVLink 2 telemetry (position, attitude, battery, link quality, mode); receives mission commands from GCS |
| S-05 | Наземна станція управління (НСУ / GCS) розрахунку | Relays telemetry to edge; displays tasking |
| S-06 | Периферійний шлюз позиції (edge gateway) | Aggregates local sensors & GCS, buffers when offline, runs local fusion |
| S-07 | Національна система ситуаційної обізнаності (DELTA / Mission Control) | Bidirectional exchange of air picture & reports (CoT / API) |
| S-08 | Система управління повітряним рухом / ПС ЗСУ | Friendly flight plans, airspace restrictions |
| S-09 | Система повітряної тривоги та оповіщення | Receives regional threat notifications |
| S-10 | Метеосервіс | Wind, visibility, precipitation (affects launch decisions) |
| S-11 | Таймер / планувальник (час як актор) | Triggers periodic health checks, reports, data retention |

---

## 4. End-to-end business processes

Process codes are reused by BPMN (pools/lanes), IDEF0 (blocks A1…A6) and UML (use cases).

### Process map (IDEF0 A0 decomposition proposal)
| IDEF0 | Process | Includes BP |
|---|---|---|
| A1 | Забезпечити функціонування сенсорної мережі та прийом телеметрії | BP-01, BP-02 |
| A2 | Сформувати єдину повітряну обстановку | BP-03, BP-04 |
| A3 | Спланувати та призначити перехоплення | BP-05, BP-09 |
| A4 | Виконати та супроводити місію перехоплення | BP-06 |
| A5 | Оцінити результати, звітувати та оповіщати | BP-07, BP-11 |
| A6 | Забезпечити готовність ресурсів та безпеку системи | BP-08, BP-10, BP-12 |

### BP-01 Реєстрація та контроль стану сенсорних вузлів (Sensor onboarding & health)
- **Trigger:** new sensor delivered / periodic heartbeat timer (30 s).
- **Pre:** sensor has hardware ID and certificate request; site coordinates surveyed.
- **Steps:** 1) technician registers node (type, coordinates, height, sector); 2) IT issues X.509 device certificate;
  3) node connects to edge gateway (mTLS) and publishes `birth` message; 4) platform validates calibration profile;
  5) node goes `Online`; 6) heartbeats monitored; missed 3 heartbeats → `Degraded`, 10 → `Offline` + alert to R-07.
- **Rules:** BR-01 a sensor without valid certificate cannot publish; BR-02 coordinates accuracy ≤ 5 m; BR-03 coverage
  gaps > 2 km² in a protected sector raise a coverage alert.
- **Post:** sensor visible on coverage map. **Exceptions:** certificate expiry (auto-renew 14 days before), tampering
  (sudden location change > 50 m → quarantine).

### BP-02 Прийом і нормалізація телеметрії та виявлень (Telemetry ingestion)
- **Trigger:** message from S-01…S-05.
- **Steps:** 1) edge gateway receives (MQTT / ASTERIX / MAVLink); 2) authenticates source; 3) validates schema & time
  (clock skew ≤ 200 ms via GNSS/PTP); 4) converts to canonical model (WGS-84, UTC, SI units); 5) de-duplicates; 6)
  publishes to event bus topic (`detections.raw`, `telemetry.interceptor`); 7) stores in time-series DB; 8) if uplink
  lost — buffers locally (store-and-forward) and replays with original timestamps.
- **Rules:** BR-04 messages older than 10 s are marked `late` and excluded from live fusion; BR-05 detections with
  confidence < 0.3 are stored but not displayed; BR-06 interceptor telemetry rate ≥ 5 Hz in flight.
- **Exceptions:** malformed message → dead-letter queue + counter; flood (> 10× normal rate) → rate limiting and
  security event.

### BP-03 Злиття виявлень і формування треків (Track fusion)
- **Trigger:** new detection event.
- **Steps:** 1) associate detection with existing track (gating by position/velocity/time); 2) if none — create
  `Tentative` track; 3) acoustic bearings from ≥ 2 nodes are triangulated; 4) radar/EO detections update kinematics;
  5) track becomes `Confirmed` after ≥ 3 consistent updates from ≥ 2 sensor types or 1 radar + 1 other; 6) predicted
  trajectory and ETA to protected objects computed; 7) track pushed to all subscribed UIs (WebSocket) and to S-07.
- **Rules:** BR-07 a track not updated for 60 s → `Lost`; BR-08 analyst R-03 may merge/split tracks — action audited;
  BR-09 track identity (своя/чужа/невідома) defaults to `Unknown` until classified.
- **Exceptions:** sensor spoofing suspicion (inconsistent physics) → flag `Suspect`, requires analyst review.

### BP-04 Класифікація та оцінка загрози (Classification & threat evaluation)
- **Trigger:** track `Confirmed`.
- **Steps:** 1) ML classifier suggests type (ударний БпЛА / розвідувальний / хибна ціль / дружній / невідомий) with
  confidence; 2) cross-check with friendly flight plans (S-08) and IFF data; 3) threat score computed from type, ETA to
  protected object, object priority, altitude band; 4) analyst R-03 confirms or corrects; 5) track gets priority rank
  in the engagement queue.
- **Rules:** BR-10 classification "hostile" requires human confirmation; BR-11 any track correlated with a friendly
  flight plan is locked from engagement; BR-12 priority = f(ETA, object category I–III, type).
- **Exceptions:** ambiguous identity near friendly aircraft → escalate to R-01 and Сектор взаємодії.

### BP-05 Підбір і призначення розрахунку (Crew/interceptor assignment — "tasking")
- **Trigger:** hostile track enters a crew's engagement envelope forecast, or R-02 request.
- **Steps:** 1) system lists candidate crews: status `Ready`, interceptor available, battery ≥ threshold, forecast
  intercept geometry feasible, weather within limits; 2) ranks by predicted time-to-intercept and resource balance;
  3) R-02 selects crew (or accepts recommendation); 4) a `Mission` is created in state `Proposed`; 5) R-01 authorises
  (`Approved`) — two-person rule if the predicted intercept point is near a no-engagement zone; 6) tasking pushed to
  crew tablet; 7) crew commander R-04 acknowledges within 15 s (else auto-escalation to next candidate).
- **Rules:** BR-13 one interceptor mission per track unless R-01 approves a second (salvo); BR-14 no tasking into
  no-engagement zones (над щільною забудовою, біля АЕС, аеродромів тощо); BR-15 crews with expired admission
  (допуск) cannot be tasked.
- **Exceptions:** crew rejects (technical fault) → next candidate; no feasible crew → hand-off to adjacent centre /
  MВГ via S-07.

### BP-06 Виконання та супровід місії перехоплення (Mission execution & monitoring)
- **Trigger:** mission `Approved` + crew acknowledged.
- **Steps:** 1) pre-launch checklist on GCS (link, GNSS, battery, video); 2) launch → state `Launched`; 3) en-route
  phase: interceptor telemetry and live target track displayed together; target updates relayed to GCS at ≥ 1 Hz;
  4) terminal phase: operator visually confirms target in video and confirms engagement (human-in-the-loop);
  5) outcome reported (`Hit` / `Miss` / `Aborted`); 6) recovery of reusable interceptor or record as expended;
  7) mission closed with telemetry and video attached.
- **Rules:** BR-16 abort is mandatory if the target is re-classified as friendly, enters a no-engagement zone, or R-01
  issues cancel; BR-17 link-loss behaviour follows pre-configured fail-safe (return/loiter/terminate in safe area);
  BR-18 every state change is time-stamped and audited.
- **Exceptions:** jamming (РЕБ) → switch channel, mark `LinkDegraded`; target lost → re-cue from fusion or abort;
  interceptor fault → abort, next candidate (BP-05).

### BP-07 Оцінка результату та звітність про перехоплення (Engagement assessment)
- **Trigger:** mission completed.
- **Steps:** 1) crew report (result, time, coordinates, video clip); 2) sensor confirmation (track terminated at
  intercept point / visual); 3) analyst sets assessment `Confirmed destroyed` / `Probable` / `Not confirmed`;
  4) debris/fall location forwarded to ДСНС if over populated area; 5) data sent to national system (S-07) and to
  pay-per-intercept accounting; 6) consumption written off in logistics.
- **Rules:** BR-19 a result is "confirmed" only with ≥ 2 independent evidences; BR-20 report to higher C2 within 15 min.

### BP-08 Облік готовності, обслуговування та логістика (Readiness, maintenance, logistics)
- Daily readiness reports per position; pre-/post-flight checks; battery cycle accounting (write-off at 300 cycles or
  capacity < 80 %); stock thresholds trigger replenishment requests; transfers between positions.
- **Rules:** BR-21 interceptor with open defect cannot be `Ready`; BR-22 minimum stock per position = 2 nights × average
  expenditure.

### BP-09 Деконфлікція повітряного простору (Airspace deconfliction)
- Import friendly flight plans and temporary restricted areas; display them; block engagements inside friendly
  corridors; notify own interceptor flights to adjacent units to avoid blue-on-blue.

### BP-10 Робота в деградованому режимі (Degraded / disconnected operations)
- Edge gateway continues local fusion and tasking for its sector when the core is unreachable; synchronises on
  reconnection (conflict resolution: last-writer-wins for telemetry; CP-authoritative for mission states).

### BP-11 Аналітика та звітність (Analytics & reporting)
- Nightly attack report; KPI dashboard: detection-to-tasking time, tasking-to-launch time, intercept rate, cost per
  intercept, sensor availability, false-alarm rate; mission replay; recommendations for repositioning crews.

### BP-12 Управління доступом і кібербезпека (Access & security management)
- User lifecycle (create → admit → suspend → revoke), MFA, role changes approved by commander; certificate rotation;
  security monitoring (SIEM) and incident response.

---

## 5. Domain data model

Types: `UUID`, `VARCHAR(n)`, `TEXT`, `INT`, `DECIMAL(p,s)`, `BOOL`, `TIMESTAMPTZ`, `GEOGRAPHY(POINT/POLYGON,4326)` (PostGIS),
`JSONB`, `ENUM`. PK = primary key, FK = foreign key, U = unique, NN = not null.

### E-01 ProtectedObject — Об'єкт прикриття
| Attribute | Type | Constraints | Notes |
|---|---|---|---|
| object_id | UUID | PK | |
| name | VARCHAR(200) | NN, U | «ТЕЦ-2», «Підстанція 330 кВ …» |
| category | ENUM(I,II,III) | NN | Пріоритет прикриття |
| location | GEOGRAPHY(POLYGON) | NN | |
| sector_id | UUID | FK → Sector | |

### E-02 Sector — Сектор / зона відповідальності
| sector_id UUID PK | name VARCHAR(100) NN U | boundary GEOGRAPHY(POLYGON) NN | type ENUM(responsibility, no_engagement, friendly_corridor, restricted) NN | valid_from/valid_to TIMESTAMPTZ |

### E-03 Sensor — Сенсорний вузол
| Attribute | Type | Constraints |
|---|---|---|
| sensor_id | UUID | PK |
| hw_serial | VARCHAR(64) | NN, U |
| type | ENUM(acoustic, radar, eo_ir, rf, observer) | NN |
| location | GEOGRAPHY(POINT) | NN |
| height_m | DECIMAL(6,1) | NN |
| sector_id | UUID | FK → Sector, NN |
| gateway_id | UUID | FK → EdgeGateway |
| status | ENUM(registered, online, degraded, offline, quarantined, decommissioned) | NN |
| cert_fingerprint | VARCHAR(128) | U |
| last_heartbeat_at | TIMESTAMPTZ | |
| calibration_profile | JSONB | |

### E-04 EdgeGateway — Периферійний шлюз
| gateway_id UUID PK | position_id UUID FK→Position | hostname VARCHAR(100) U | status ENUM(online, isolated, offline) | sw_version VARCHAR(30) | uplinks JSONB (mesh/LTE/sat) | buffer_fill_pct DECIMAL(5,2) |

### E-05 Detection — Виявлення (raw)
| Attribute | Type | Constraints |
|---|---|---|
| detection_id | UUID | PK |
| sensor_id | UUID | FK → Sensor, NN |
| detected_at | TIMESTAMPTZ | NN (UTC, ms) |
| received_at | TIMESTAMPTZ | NN |
| position | GEOGRAPHY(POINT) | NULL for bearing-only |
| bearing_deg / elevation_deg | DECIMAL(5,2) | 0–360 / −90–90 |
| altitude_m, speed_mps, heading_deg | DECIMAL | nullable |
| signature_class | VARCHAR(50) | «shahed_piston», «jet», «quadcopter», … |
| confidence | DECIMAL(3,2) | 0.00–1.00, NN |
| track_id | UUID | FK → AirTrack, nullable until associated |
*Stored in a time-series hypertable partitioned by `detected_at`.*

### E-06 AirTrack — Повітряний трек (ціль)
| Attribute | Type | Constraints |
|---|---|---|
| track_id | UUID | PK |
| track_number | VARCHAR(12) | NN, U per day (e.g. «ЩП-0412») |
| state | ENUM (see 5.3) | NN |
| identity | ENUM(hostile, suspect, unknown, friendly, false_target) | NN, default unknown |
| target_type | ENUM(oneway_attack_uav, recon_uav, decoy, missile, helicopter, aircraft, unknown) | |
| position / altitude_m / speed_mps / heading_deg | — | current kinematics |
| first_seen_at / last_update_at | TIMESTAMPTZ | NN |
| threat_score | DECIMAL(5,2) | 0–100 |
| predicted_object_id | UUID | FK → ProtectedObject |
| eta_s | INT | ETA to predicted object |
| classified_by | UUID | FK → User (human confirmation) |

### E-07 TrackPoint — Точка траєкторії
| track_id UUID FK | ts TIMESTAMPTZ | position GEOGRAPHY | altitude_m | speed_mps | source_mask INT (bitmask of sensor types) | PK(track_id, ts) |

### E-08 Position — Вогнева позиція
| position_id UUID PK | code VARCHAR(10) U («П-07») | location GEOGRAPHY(POINT) NN | sector_id FK | status ENUM(active, relocating, inactive) | engagement_radius_m INT |

### E-09 Crew — Розрахунок перехоплювачів
| crew_id UUID PK | call_sign VARCHAR(20) U | position_id FK→Position | status ENUM(off_duty, ready, tasked, in_mission, recovering, unavailable) NN | shift_id FK→Shift |

### E-10 Personnel — Особовий склад / User
| user_id UUID PK | full_name VARCHAR(150) NN | rank VARCHAR(40) | unit_id FK→Unit | role_id FK→Role NN | crew_id FK (nullable) | admission_valid_to DATE | mfa_enabled BOOL NN | status ENUM(active, suspended, revoked) |

### E-11 Role — Роль / E-12 Permission — Право (M:N via RolePermission)

### E-13 Interceptor — Дрон-перехоплювач (екземпляр)
| Attribute | Type | Constraints |
|---|---|---|
| interceptor_id | UUID | PK |
| serial_no | VARCHAR(40) | NN, U |
| model_id | UUID | FK → InterceptorModel, NN |
| state | ENUM (see 5.3) | NN |
| position_id | UUID | FK → Position (current location) |
| firmware_version | VARCHAR(20) | |
| flight_count | INT | ≥ 0 |
| reusable | BOOL | NN |
| received_at | DATE | NN |

### E-14 InterceptorModel — Модель перехоплювача
| model_id PK | name U | max_speed_kmh INT | range_km DECIMAL | endurance_min INT | wind_limit_mps DECIMAL | night_capable BOOL | telemetry_protocol ENUM(mavlink2, proprietary) |
*(Only performance envelope figures needed for feasibility checks; no payload data.)*

### E-15 BatteryPack — Акумуляторна батарея
| battery_id PK | serial U | capacity_mah INT | cycles INT | health_pct DECIMAL(5,2) | state ENUM(charged, charging, in_use, depleted, written_off) | position_id FK |

### E-16 Mission — Місія перехоплення (бойове завдання)
| Attribute | Type | Constraints |
|---|---|---|
| mission_id | UUID | PK |
| mission_no | VARCHAR(16) | NN, U |
| track_id | UUID | FK → AirTrack, NN |
| crew_id | UUID | FK → Crew, NN |
| interceptor_id | UUID | FK → Interceptor (set at launch) |
| state | ENUM (see 5.3) | NN |
| proposed_by / approved_by | UUID | FK → User; approved_by ≠ proposed_by when two-person rule applies |
| proposed_at, approved_at, acknowledged_at, launched_at, closed_at | TIMESTAMPTZ | ordered |
| result | ENUM(hit, miss, aborted, lost) | NULL until closed |
| abort_reason | VARCHAR(200) | |
| predicted_intercept_point | GEOGRAPHY(POINT) | |

### E-17 MissionEvent — Подія місії
| event_id PK | mission_id FK NN | ts TIMESTAMPTZ NN | type ENUM(state_change, link_loss, link_restored, target_update, operator_confirm, abort_cmd) | payload JSONB | actor_id FK→User (nullable for system) |

### E-18 TelemetryFrame — Кадр телеметрії перехоплювача
| interceptor_id FK | mission_id FK | ts TIMESTAMPTZ | lat, lon DECIMAL(9,6) | alt_m | ground_speed_mps | heading_deg | battery_pct | link_rssi_dbm | link_quality_pct | flight_mode VARCHAR(20) | gnss_fix ENUM | PK(interceptor_id, ts) — hypertable |

### E-19 EngagementReport — Звіт про перехоплення
| report_id PK | mission_id FK U | assessment ENUM(confirmed, probable, not_confirmed) | evidence JSONB (video refs, sensor confirmations) | impact_location GEOGRAPHY | civil_damage_reported BOOL | submitted_by FK | submitted_at | sent_to_higher_at |

### E-20 Alert — Сповіщення
| alert_id PK | type ENUM(threat, coverage_gap, sensor_offline, link_degraded, stock_low, security) | severity ENUM(info, warning, critical) | ref_entity / ref_id | created_at | acknowledged_by FK | acknowledged_at | state ENUM(open, acknowledged, resolved) |

### E-21 FriendlyFlightPlan — План польоту дружньої авіації
| plan_id PK | source ENUM(air_force, adjacent_centre, own) | corridor GEOGRAPHY(POLYGON) | alt_min_m, alt_max_m | valid_from, valid_to NN | callsign |

### E-22 MaintenanceRecord — Запис обслуговування
| record_id PK | asset_type ENUM(interceptor, battery, sensor, gateway) | asset_id UUID | type ENUM(preflight, postflight, repair, calibration, write_off) | result ENUM(ok, defect) | defect_description TEXT | technician_id FK | ts |

### E-23 StockMovement — Рух запасів
| movement_id PK | item_type ENUM(interceptor, battery, spare_part) | item_id | from_position_id / to_position_id FK | qty INT | reason ENUM(delivery, transfer, expenditure, write_off) | ts | approved_by FK |

### E-24 Shift — Зміна чергування
| shift_id PK | starts_at, ends_at NN | duty_officer_id FK | mode ENUM(normal, heightened, massive_attack) |

### E-25 AuditLogEntry — Запис журналу аудиту (append-only)
| entry_id BIGSERIAL PK | ts NN | actor_id | actor_type ENUM(user, service, device) | action VARCHAR(80) | entity / entity_id | before/after JSONB | ip / node | prev_hash, hash CHAR(64) (hash chain) |

### 5.2 Relationships & cardinalities
- Sector 1 — * ProtectedObject; Sector 1 — * Sensor; Sector 1 — * Position.
- EdgeGateway 1 — * Sensor; Position 1 — 1..* EdgeGateway.
- Sensor 1 — * Detection; AirTrack 1 — * Detection (0..1 track per detection); AirTrack 1 — * TrackPoint (composition).
- AirTrack 1 — 0..* Mission (normally 0..1; salvo allowed with approval).
- Crew 1 — * Mission; Position 1 — * Crew; Crew 1 — 2..4 Personnel.
- Interceptor 0..1 — 1 Mission (an interceptor is used in at most one *active* mission; reusable ones accumulate many over time: 1 — *).
- InterceptorModel 1 — * Interceptor; Mission 1 — * MissionEvent (composition); Mission 1 — * TelemetryFrame.
- Mission 1 — 0..1 EngagementReport.
- Role * — * Permission; Personnel * — 1 Role.
- Any entity 1 — * AuditLogEntry (polymorphic).

### 5.3 State machines

**AirTrack**
| From | Event / guard | To |
|---|---|---|
| — | first detection not associated | Tentative |
| Tentative | ≥ 3 consistent updates from ≥ 2 sources | Confirmed |
| Tentative | no update 20 s | Dropped |
| Confirmed | analyst confirms type & identity | Classified |
| Classified (hostile) | mission approved | Engaging |
| Engaging | result = hit & confirmed | Destroyed |
| Engaging | result = miss / aborted | Classified (re-queue) |
| Confirmed/Classified/Engaging | no update 60 s | Lost |
| any | leaves area of responsibility (handed off) | HandedOff |
| any | marked false target | Dropped |

**Mission**: `Proposed → Approved → Acknowledged → Launched → EnRoute → Terminal → Closed(hit|miss)`;
side exits: `Proposed → Rejected` (R-01 denies), `Approved → Reassigned` (crew no-ack 15 s),
`Launched/EnRoute/Terminal → Aborted` (BR-16/17), `EnRoute → LinkDegraded → EnRoute|Lost`.

**Interceptor**: `Received → Inspected → Ready ⇄ Reserved → InFlight → (Recovered → PostFlightCheck → Ready|Maintenance) | Expended | Lost`;
`Maintenance → Ready | WrittenOff`.

**Sensor**: `Registered → Online ⇄ Degraded → Offline → Online`; `any → Quarantined → Online|Decommissioned`.

**Crew**: `OffDuty → Ready → Tasked → InMission → Recovering → Ready`; `Ready → Unavailable → Ready`.

**Alert**: `Open → Acknowledged → Resolved`; auto-escalation if not acknowledged within SLA (critical 30 s, warning 5 min).

---

## 6. Architecture & integration landscape

### 6.1 Architectural style (justification for lectures 7–9)
- **Distributed, event-driven architecture with edge computing** — matches the 4-level IoT architecture from lecture 7:
  1. *Рівень сприйняття* (perception): sensors, interceptors' autopilots, firmware/RTOS.
  2. *Мережевий та периферійний рівень* (network/edge): edge gateways at positions — MQTT broker (Mosquitto/EMQX edge),
     MAVLink router, protocol adapters, local fusion, store-and-forward; containerised (Docker/Podman).
  3. *Прикладний / хмарний (ядро) рівень*: core services in a protected data centre (+ geo-redundant standby).
  4. *Рівень користувача*: CP operator workstation (SCADA-like HMI with map — «мнемосхема» повітряної обстановки),
     crew tablets, analytics dashboards.
- **Core as a modular monolith → selective microservices.** Recommended for a regional centre: a modular monolith for
  admin/logistics/reporting (simpler ops), with separately scaled real-time services (ingestion, fusion, tasking,
  telemetry) — the lecture's microservice model applied only where scaling/latency demands it.
- **Multi-agent view (lecture 8–9, МАС):** each edge gateway and each interceptor acts as an agent; the CP coordinates
  them (координована співпраця); hybrid MAS architecture (reactive edge rules + knowledge-based central planning).
- **Control-system classification (lecture 8–9):** *інтерактивна система супервізорного управління* — the operator
  issues target designations (цілевказівки), automation executes programmes; the human retains engagement authority.

### 6.2 Core services (logical components)
| Service | Responsibility | Tech suggestion |
|---|---|---|
| Device Registry & PKI | sensors, gateways, interceptors, certificates | PostgreSQL, step-ca/Vault PKI |
| Ingestion Gateway | protocol adapters MQTT/ASTERIX/MAVLink/CoT → canonical events | Go/Rust, MQTT 5 |
| Event Bus | durable streams `detections.*`, `tracks.*`, `missions.*`, `telemetry.*` | Apache Kafka or NATS JetStream |
| Track Fusion Service | association, triangulation, Kalman filtering, track lifecycle | stateful stream processing |
| Classification & Threat Service | ML suggestion + rules, threat score | Python model serving |
| Tasking (Mission) Service | candidate ranking, mission state machine, two-person rule | transactional, PostgreSQL |
| Telemetry Service | interceptor telemetry, mission replay | TimescaleDB hypertables |
| Geo Service | sectors, zones, deconfliction checks | PostGIS |
| Notification Service | alerts, escalation, external alert system | WebSocket / push |
| Reporting & Analytics | KPIs, reports, exports | OLAP views, BI |
| Integration Hub | DELTA/Mission Control, Air Force, weather | REST/gRPC, CoT, ASTERIX |
| IAM & Audit | users, roles, MFA, audit hash chain | Keycloak (OIDC), append-only store |
| Operator UI / Crew App | map HMI, tasking, video | Web (TypeScript), Android tablet app |

### 6.3 Protocols & data exchange
| Link | Protocol | QoS / notes |
|---|---|---|
| Acoustic node → edge | MQTT 5 over TLS (QoS 1), Sparkplug-style birth/death | low bandwidth, 1–5 msg/s |
| Radar → edge | ASTERIX CAT048/062 over UDP multicast in protected LAN | 1 Hz scan updates |
| Interceptor ↔ GCS | MAVLink 2 with message signing over the drone radio link | ≥ 5 Hz telemetry |
| GCS → edge | MAVLink router / MQTT bridge | |
| Edge ↔ core | MQTT bridge or gRPC streaming over mTLS VPN (WireGuard/IPsec); multi-path (mesh radio, LTE, satellite) | priority classes: tasking > tracks > telemetry > video |
| Core ↔ UIs | WebSocket (track/mission push), REST/JSON (CRUD) | delta updates |
| Core ↔ national C2 | CoT XML / REST API | NATO-compatible symbology |
| Video | RTSP/SRT, STANAG 4609 metadata | edge-side transcoding, on-demand uplink |

### 6.4 Caching & performance
- Live air picture held in memory (Redis / in-process) as materialised view (CQRS read model); UIs receive deltas only.
- Geo-fences pre-indexed (R-tree) for O(log n) deconfliction checks.
- Telemetry downsampled for archive (5 Hz raw for 30 days, 1 Hz for 1 year).
- Back-pressure: under massive attack prioritise tracks/tasking; degrade video first.

### 6.5 Reliability & degraded operation
- Core: active-standby across two sites, RPO ≤ 5 s (stream replication), RTO ≤ 60 s.
- Edge autonomy ≥ 4 h: local broker, local fusion of own-sector sensors, local tasking of own crews; reconciliation
  on reconnect (event-sourced mission log with vector timestamps).
- Time synchronisation: GNSS-disciplined clocks + PTP/NTP fallback; jamming-aware holdover.

### 6.6 Security requirements
- Zero-trust: mTLS for every device and service; X.509 per device; hardware-backed keys where possible.
- MAVLink 2 signing; replay protection; MQTT topic ACLs per device.
- IAM: OIDC + MFA; RBAC per §3 + ABAC by sector; session timeout 15 min idle on CP workstations.
- Audit: append-only, hash-chained log of all commands, classifications, approvals, logins; retention ≥ 3 years.
- Data classification: operational data marked «Для службового користування» or higher; encryption at rest (AES-256)
  and in transit (TLS 1.3).
- Threat model (lecture 8–9 vulnerabilities): OS vulnerabilities, SCADA/HMI vulnerabilities, communication channels,
  physical inaccessibility of field equipment, staff qualification → controls on physical, organisational and
  software-hardware levels; compliance with КСЗІ and IEC 62443 zones/conduits.

### 6.7 Key non-functional requirements (for ТЗ/UML/architecture labs)
| NFR | Target |
|---|---|
| Detection-to-display latency | ≤ 2 s p95 |
| Tasking delivery to crew | ≤ 1 s p95 |
| Concurrent tracks | ≥ 500 per region |
| Ingestion rate | ≥ 20,000 msg/s peak |
| Concurrent UI users | ≥ 150 |
| Core availability | 99.95 % (monthly) |
| Edge offline autonomy | ≥ 4 h |
| Telemetry retention | raw 30 days, aggregated 1 year; missions & reports 5 years |
| Audit coverage | 100 % of commands and state changes |

### 6.8 KPIs (for analytics, goal tree measurability)
detection-to-tasking time (target ≤ 30 s); tasking-to-launch time (≤ 90 s); intercept success rate (%);
cost per confirmed intercept; sensor availability (≥ 97 %); false-alarm rate (≤ 5 %); crew readiness ratio;
mean time to restore a link.

---

## 7. Mapping to the course labs (modelling hooks)

| Lab | Artefact | Domain content to use |
|---|---|---|
| ЛР1 | Загальні відомості, структурна схема, таблиці задач/функцій та взаємозв'язків, задачі автоматизації, дерево цілей, WBS | §2, §1.2–1.3, §4; WBS by product (subsystems) × phases (ГОСТ 34.601) |
| ЛР2 | BPMN 2.0 | Pools: КП, Розрахунок перехоплювачів, Відділ розвідки (сенсори), «Щит-Лінк» (system pool), Зовнішні (ПС ЗСУ/DELTA). Main process: BP-03→BP-07; message flows for tasking/acks |
| ЛР3 | IDEF0 A-0 (§1.4 ICOM), A0 = A1…A6 (§4 map), A3/A4 decomposition, дерево вузлів, FEO; IDEF3 for BP-05/BP-06 with junctions (X — вибір кандидата, & — паралельні перевірки) | §1.4, §4 |
| DFD (lecture 5) | Externals S-01…S-10, stores D1 Треки, D2 Місії, D3 Телеметрія, D4 Ресурси, D5 Журнал аудиту | §3.2, §5 |
| UML (lecture 6) | Use cases per R-xx; class diagram from §5; sequence for BP-05/06; state machines §5.3; component §6.2; deployment §6.1 | §3, §5, §6 |
| Architecture (lecture 7–9) | 4-level IoT, edge, security architecture | §6 |

**Tasks requiring automation (задачі, що потребують автоматизації — ЛР1):**
1. Автоматизований збір і нормалізація телеметрії з різнотипних сенсорів та перехоплювачів.
2. Автоматичне злиття виявлень у треки та прогноз траєкторій.
3. Підтримка класифікації та оцінки загрози (ML-підказки з підтвердженням людиною).
4. Автоматизований підбір розрахунку і доставка бойових завдань на планшет.
5. Моніторинг місії у реальному часі з об'єднаним відображенням цілі та перехоплювача.
6. Облік готовності розрахунків, перехоплювачів, АКБ і запасів.
7. Деконфлікція з дружньою авіацією та контроль заборонених зон.
8. Автоматичне формування звітів про перехоплення та аналітика KPI.
9. Оповіщення та ескалація подій.
10. Управління доступом, аудит та кіберзахист.

---

## 8. Domain glossary (EN ↔ UA, approved lecture terminology in **bold**)

| English | Українською | Note |
|---|---|---|
| Information system | **Інформаційна система (ІС)** | lecture 1, textbooks |
| Information-management system | **Інформаційно-управляюча система** | lecture 8–9 |
| Automated control system for technological processes | **АСК ТП** (автоматизована система керування технологічним процесом) | lecture 8–9 |
| Cyber-physical system | **Кіберфізична система (КФС)** | lecture 8–9 |
| Industrial Internet of Things | **Індустріальний (промисловий) Інтернет речей (IIoT)** | lecture 8–9 |
| Multi-agent system / agent | **Мультиагентна (багатоагентна) система (МАС) / агент** | lecture 8–9 |
| Supervisory control | **Супервізорне управління** | lecture 8–9 |
| Human–machine interface | **Людино-машинний інтерфейс (HMI)**, мнемосхема | lecture 8–9 |
| SCADA | **Диспетчерське управління і збір даних (SCADA)** | lecture 8–9 |
| Perception / network / application / user layer | **Рівень сприйняття / мережевий (периферійний) / прикладний (хмарний) / рівень користувача** | lecture 7 |
| Edge computing / gateway | **Периферійні обчислення / шлюз (Edge/Gateway)** | lecture 7 |
| Broker (message) | **Брокер повідомлень** | lecture 7 |
| Role-based access control | **Рольове управління доступом (RBAC)** | lecture 7 |
| Goal tree | **Дерево цілей** | ЛР1, lecture 2 |
| General goal / mission | **Генеральна мета / місія** | ЛР1 |
| Work Breakdown Structure | **Ієрархічна структура робіт (WBS), робоча структура проекту** | ЛР1, lecture 2 |
| Work package | **Робочий пакет (work package)** | ЛР1 |
| Organisational structure | **Організаційна структура; структурна схема підприємства** | ЛР1 |
| Context diagram | **Контекстна діаграма (рівень А-0)** | lecture 4 |
| Decomposition diagram | **Діаграма декомпозиції** | lecture 4 |
| Node tree | **Діаграма дерева вузлів** | ЛР3 |
| Input / Control / Output / Mechanism / Call arrow | **Вхід / Управління / Вихід / Механізм / Стрілка виклику** | lecture 4 |
| Tunnelled arrow | Тунельована стрілка | IDEF0 |
| Unit of Work (UOW) | **Одиниця роботи (UOW)** | lecture 5 |
| Junction (AND/OR/XOR) | **Перехрестя: кон'юнкція (асинхронне/синхронне «і»), диз'юнкція («або»), виключна диз'юнкція** | lecture 5 |
| Precedence link / object flow / referent | **Передування / потік об'єктів / об'єкт посилання** | lecture 5 |
| External entity / process / data store / data flow | **Зовнішня сутність / процес / накопичувач даних / потік даних** | lecture 5 |
| Event / activity / gateway (BPMN) | **Подія / дія (завдання, підпроцес) / логічний оператор (шлюз)** | lecture 3 |
| Pool / lane | **Пул / доріжка** | lecture 3 |
| Sequence flow / message flow / association | **Потік управління / потік повідомлень / асоціація** | lecture 3 |
| Use case / actor | **Прецедент (варіант використання) / актор** | lecture 6 |
| Class / association / aggregation / composition / generalisation | **Клас / асоціація / агрегація / композиція / узагальнення** | lecture 6 |
| Sequence / activity / state / component / deployment diagram | **Діаграма послідовності / діяльності / станів / компонентів / розгортання** | lecture 6 |
| Interceptor drone | Дрон-перехоплювач (БпЛА-перехоплювач) | domain |
| Unmanned aerial vehicle (UAV), one-way attack UAV | Безпілотний літальний апарат (БпЛА), ударний БпЛА | domain |
| Air track / target | Повітряний трек / повітряна ціль | domain |
| Air picture / situational awareness | Повітряна обстановка / ситуаційна обізнаність | domain |
| Detection | Виявлення | domain |
| Sensor fusion / track fusion | Злиття даних сенсорів / злиття треків | domain |
| Classification / identification (friend-or-foe) | Класифікація / ідентифікація (свій–чужий) | domain |
| Threat evaluation / priority | Оцінка загрози / пріоритет цілі | domain |
| Tasking / target designation | Постановка бойового завдання / цілевказання (призначення цілі) | domain |
| Launch authorisation | Санкціонування пуску | domain |
| Interceptor crew / pilot | Розрахунок перехоплювачів / оператор (пілот) | domain |
| Mobile fire group | Мобільна вогнева група (МВГ) | domain |
| Command post / duty officer | Командний пункт (КП) / оперативний черговий | domain |
| Ground control station (GCS) | Наземна станція управління (НСУ) | domain |
| Telemetry | Телеметрія | domain |
| Engagement result assessment | Оцінка результату перехоплення | domain |
| No-engagement zone | Зона заборони ураження | domain |
| Airspace deconfliction | Деконфлікція повітряного простору | domain |
| Electronic warfare (jamming) | Радіоелектронна боротьба (РЕБ), подавлення | domain |
| Store-and-forward | Буферизація з відкладеною передачею | architecture |
| Event bus / stream | Шина подій / потік подій | architecture |
| Time-series database | База даних часових рядів | architecture |
| Audit log | Журнал аудиту | security |
| Mutual TLS / certificate | Взаємна автентифікація TLS (mTLS) / сертифікат | security |
| Rules of engagement (ROE) | Правила застосування | controls |
| Readiness | Бойова готовність | domain |
| Battery pack | Акумуляторна батарея (АКБ) | domain |
| Key performance indicator | Ключовий показник ефективності (KPI) | lecture 1 |

---

## 9. Sources (verified during research, Oct 2026)
- Kyiv Post — *Ukraine Deploys Multi-Layer Drone Shield Against Shahed Attacks*: https://www.kyivpost.com/post/67170
- ISIS — *Monthly Analysis of Russian Shahed 136 Deployment*: https://isis-online.org/isis-reports/monthly-analysis-of-russian-shahed-136-deployment-against-ukraine
- Drone-Warfare.com — *Countering the Shahed-136: Detection, Intercept, Cost*: https://drone-warfare.com/counter-uas/countering-the-shahed-136/
- Defense News (2026-03-05) — *Novel interceptor drones bend air-defense economics*: https://www.defensenews.com/global/europe/2026/03/05/novel-interceptor-drones-bend-air-defense-economics-in-ukraines-favor/
- The Defender (2026-05) — *Terminal guidance on interceptors*: https://thedefender.media/en/2026/05/terminal-guidance-interceptor-drones/
- United24 — *Sky Fortress acoustic detection*: https://united24media.com/war-in-ukraine/sky-fortress-ukraines-acoustic-detection-system-that-tracks-drones-cheap-and-fast-9451
- Wikipedia — *Sky Fortress*, *Delta (situational awareness system)*, *Sting (drone)*, *Interceptor drone*
- NATO ACT — *DELTA at CWIX24*: https://www.act.nato.int/article/delta-system-cwix/
- Rubryka (2026-01-23) — *MoD deploys UAV control system within Delta*: https://rubryka.com/en/2026/01/23/systemu-upravlinnya-bpla/
- Frontliner — *Mobile fire groups need compact radars*: https://frontliner.ua/en/the-fight-against-shaheds-why-mobile-fire-groups-need-to-be-modernized/
- MAVLink / MAVROS docs: https://github.com/mavlink/mavros
- Course lectures ПІС_1…ПІС_8_9 (Гладка М.В.) and textbooks «Корисна інфа 1–5» (Марченко 2015; Пістунов 2008; Ременяк 2016; Ізмайлова 2022; Коваленко, Добровська 2020).

*Organisation figures (staff, sensors, positions, budgets) are illustrative assumptions for the academic model.*

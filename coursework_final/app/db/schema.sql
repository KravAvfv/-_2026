-- Схема бази даних IoT-платформи «Щит-Лінк» — прототип курсової роботи.
-- Основа — фізична модель БД з tspp_work/lab1/schema.sql; для курсової роботи додано стовпці автентифікації
-- (personnel.password_hash, personnel.failed_logins).

CREATE EXTENSION IF NOT EXISTS pgcrypto;  -- gen_random_uuid() для версій до 13

CREATE TYPE sector_zone AS ENUM (
    'зона відповідальності',
    'заборона ураження',
    'коридор дружньої авіації',
    'обмежена зона'
);
CREATE TYPE object_category AS ENUM (
    'I',
    'II',
    'III'
);
CREATE TYPE sensor_kind AS ENUM (
    'акустичний',
    'радіолокаційний',
    'оптико-електронний',
    'радіотехнічний',
    'пост спостереження'
);
CREATE TYPE sensor_status AS ENUM (
    'зареєстрований',
    'у мережі',
    'деградований',
    'поза мережею',
    'у карантині',
    'виведений'
);
CREATE TYPE position_status AS ENUM (
    'активна',
    'передислокація',
    'неактивна'
);
CREATE TYPE crew_status AS ENUM (
    'готовий',
    'на завданні',
    'недоступний'
);
CREATE TYPE personnel_status AS ENUM (
    'активний',
    'призупинений',
    'відкликаний'
);
CREATE TYPE interceptor_state AS ENUM (
    'на складі',
    'готовий',
    'застосований',
    'втрачений'
);
CREATE TYPE track_state AS ENUM (
    'попередній',
    'підтверджений',
    'класифікований',
    'перехоплюється',
    'знищений',
    'втрачений',
    'переданий',
    'скинутий'
);
CREATE TYPE air_track_identity AS ENUM (
    'ворожа',
    'дружня',
    'нейтральна',
    'невідома'
);
CREATE TYPE mission_state AS ENUM (
    'запропонована',
    'відхилена',
    'санкціонована',
    'перепризначена',
    'прийнята',
    'виконується',
    'скасована',
    'закрита'
);
CREATE TYPE mission_event_type AS ENUM (
    'зміна стану',
    'втрата зв’язку',
    'відновлення зв’язку',
    'оновлення цілі',
    'підтвердження оператора',
    'команда скасування'
);
CREATE TYPE engagement_assessment AS ENUM (
    'влучання',
    'промах',
    'скасовано'
);
CREATE TYPE actor_type AS ENUM (
    'користувач',
    'сервіс',
    'пристрій'
);

CREATE TABLE role (
    role_id SMALLINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    code VARCHAR(10) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL UNIQUE,
    combat_rights BOOLEAN NOT NULL DEFAULT false,
    description TEXT
);

CREATE TABLE permission (
    permission_id SMALLINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    code VARCHAR(50) NOT NULL UNIQUE,
    description VARCHAR(200) NOT NULL
);

CREATE TABLE role_permission (
    role_id SMALLINT NOT NULL
        REFERENCES role (role_id),
    permission_id SMALLINT NOT NULL
        REFERENCES permission (permission_id),
    granted_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (role_id, permission_id)
);

CREATE TABLE sector (
    sector_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(10) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL UNIQUE,
    zone_type sector_zone NOT NULL,
    boundary JSONB NOT NULL,
    valid_from TIMESTAMPTZ NOT NULL DEFAULT now(),
    valid_to TIMESTAMPTZ,
    CHECK (valid_to IS NULL OR valid_to > valid_from)
);

CREATE TABLE interceptor_model (
    model_id SMALLINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name VARCHAR(60) NOT NULL UNIQUE,
    max_speed_kmh SMALLINT NOT NULL,
    range_km DECIMAL(5,1) NOT NULL,
    endurance_min SMALLINT NOT NULL,
    wind_limit_mps DECIMAL(4,1) NOT NULL,
    night_capable BOOLEAN NOT NULL,
    reusable BOOLEAN NOT NULL,
    CHECK (max_speed_kmh > 0),
    CHECK (range_km > 0),
    CHECK (endurance_min > 0)
);

CREATE TABLE protected_object (
    object_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sector_id UUID NOT NULL
        REFERENCES sector (sector_id),
    name VARCHAR(200) NOT NULL UNIQUE,
    category object_category NOT NULL,
    lat DECIMAL(9,6) NOT NULL,
    lon DECIMAL(9,6) NOT NULL,
    CHECK (lat BETWEEN -90 AND 90),
    CHECK (lon BETWEEN -180 AND 180)
);

CREATE TABLE sensor (
    sensor_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sector_id UUID NOT NULL
        REFERENCES sector (sector_id),
    hw_serial VARCHAR(64) NOT NULL UNIQUE,
    kind sensor_kind NOT NULL,
    status sensor_status NOT NULL DEFAULT 'зареєстрований',
    lat DECIMAL(9,6) NOT NULL,
    lon DECIMAL(9,6) NOT NULL,
    height_m DECIMAL(6,1) NOT NULL,
    last_heartbeat_at TIMESTAMPTZ,
    calibration JSONB,
    CHECK (lat BETWEEN -90 AND 90),
    CHECK (lon BETWEEN -180 AND 180)
);

CREATE TABLE position (
    position_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sector_id UUID NOT NULL
        REFERENCES sector (sector_id),
    code VARCHAR(10) NOT NULL UNIQUE,
    status position_status NOT NULL DEFAULT 'активна',
    lat DECIMAL(9,6) NOT NULL,
    lon DECIMAL(9,6) NOT NULL,
    engagement_radius_m INTEGER NOT NULL,
    CHECK (engagement_radius_m > 0)
);

CREATE TABLE crew (
    crew_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    position_id UUID NOT NULL
        REFERENCES position (position_id),
    call_sign VARCHAR(20) NOT NULL UNIQUE,
    status crew_status NOT NULL DEFAULT 'недоступний'
);

CREATE TABLE personnel (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    role_id SMALLINT NOT NULL
        REFERENCES role (role_id),
    crew_id UUID
        REFERENCES crew (crew_id),
    full_name VARCHAR(150) NOT NULL,
    rank VARCHAR(40),
    login VARCHAR(40) NOT NULL UNIQUE,
    mfa_enabled BOOLEAN NOT NULL DEFAULT true,
    admission_valid_to DATE,
    status personnel_status NOT NULL DEFAULT 'активний',
    password_hash VARCHAR(255),
    failed_logins SMALLINT NOT NULL DEFAULT 0,
    CHECK (failed_logins >= 0)
);

CREATE TABLE interceptor (
    interceptor_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_id SMALLINT NOT NULL
        REFERENCES interceptor_model (model_id),
    position_id UUID
        REFERENCES position (position_id),
    serial_no VARCHAR(40) NOT NULL UNIQUE,
    state interceptor_state NOT NULL DEFAULT 'на складі',
    firmware_version VARCHAR(20),
    flight_count INTEGER NOT NULL DEFAULT 0,
    received_at DATE NOT NULL,
    CHECK (flight_count >= 0)
);

CREATE TABLE air_track (
    track_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    track_number VARCHAR(12) NOT NULL,
    track_date DATE NOT NULL DEFAULT CURRENT_DATE,
    state track_state NOT NULL DEFAULT 'попередній',
    identity air_track_identity NOT NULL DEFAULT 'невідома',
    target_type VARCHAR(40),
    threat_score DECIMAL(5,2) NOT NULL DEFAULT 0,
    predicted_object_id UUID
        REFERENCES protected_object (object_id),
    eta_s INTEGER,
    classified_by UUID
        REFERENCES personnel (user_id),
    first_seen_at TIMESTAMPTZ NOT NULL,
    last_update_at TIMESTAMPTZ NOT NULL,
    UNIQUE (track_number, track_date),
    CHECK (threat_score BETWEEN 0 AND 100),
    CHECK (last_update_at >= first_seen_at)
);

CREATE TABLE detection (
    detection_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    sensor_id UUID NOT NULL
        REFERENCES sensor (sensor_id),
    track_id UUID
        REFERENCES air_track (track_id),
    detected_at TIMESTAMPTZ NOT NULL,
    received_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    lat DECIMAL(9,6),
    lon DECIMAL(9,6),
    bearing_deg DECIMAL(5,2),
    altitude_m DECIMAL(7,1),
    speed_mps DECIMAL(6,1),
    signature_class VARCHAR(50),
    confidence DECIMAL(3,2) NOT NULL,
    CHECK (confidence BETWEEN 0 AND 1),
    CHECK (bearing_deg IS NULL OR bearing_deg BETWEEN 0 AND 360),
    CHECK (received_at >= detected_at)
);

CREATE TABLE mission (
    mission_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mission_no VARCHAR(16) NOT NULL UNIQUE,
    track_id UUID NOT NULL
        REFERENCES air_track (track_id),
    crew_id UUID NOT NULL
        REFERENCES crew (crew_id),
    interceptor_id UUID
        REFERENCES interceptor (interceptor_id),
    proposed_by UUID NOT NULL
        REFERENCES personnel (user_id),
    approved_by UUID
        REFERENCES personnel (user_id),
    state mission_state NOT NULL DEFAULT 'запропонована',
    proposed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    approved_at TIMESTAMPTZ,
    launched_at TIMESTAMPTZ,
    closed_at TIMESTAMPTZ,
    abort_reason VARCHAR(200),
    CHECK (approved_by IS NULL OR approved_by <> proposed_by),
    CHECK (approved_at IS NULL OR approved_at >= proposed_at),
    CHECK (launched_at IS NULL OR approved_at IS NOT NULL),
    CHECK (state <> 'скасована' OR abort_reason IS NOT NULL)
);

CREATE TABLE mission_event (
    event_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    mission_id UUID NOT NULL
        REFERENCES mission (mission_id),
    event_type mission_event_type NOT NULL,
    event_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    actor_id UUID
        REFERENCES personnel (user_id),
    payload JSONB
);

CREATE TABLE telemetry_frame (
    interceptor_id UUID NOT NULL
        REFERENCES interceptor (interceptor_id),
    ts TIMESTAMPTZ NOT NULL,
    mission_id UUID NOT NULL
        REFERENCES mission (mission_id),
    lat DECIMAL(9,6) NOT NULL,
    lon DECIMAL(9,6) NOT NULL,
    alt_m DECIMAL(7,1),
    ground_speed_mps DECIMAL(5,1),
    battery_pct SMALLINT,
    link_quality_pct SMALLINT,
    PRIMARY KEY (interceptor_id, ts),
    CHECK (battery_pct BETWEEN 0 AND 100),
    CHECK (link_quality_pct BETWEEN 0 AND 100)
);

CREATE TABLE engagement_report (
    report_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mission_id UUID NOT NULL UNIQUE
        REFERENCES mission (mission_id),
    assessment engagement_assessment NOT NULL,
    evidence JSONB,
    submitted_by UUID NOT NULL
        REFERENCES personnel (user_id),
    submitted_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    sent_to_higher_at TIMESTAMPTZ
);

CREATE TABLE audit_log (
    entry_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    logged_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    actor_id UUID
        REFERENCES personnel (user_id),
    actor_type actor_type NOT NULL,
    action VARCHAR(80) NOT NULL,
    entity VARCHAR(40) NOT NULL,
    entity_id VARCHAR(40) NOT NULL,
    details JSONB,
    prev_hash CHAR(64),
    hash CHAR(64) NOT NULL UNIQUE
);

CREATE INDEX ix_detection_sensor_time ON detection (sensor_id, detected_at DESC);
CREATE INDEX ix_detection_track ON detection (track_id);
CREATE INDEX ix_air_track_active ON air_track (threat_score DESC) WHERE state IN ('підтверджений', 'класифікований', 'перехоплюється');
CREATE INDEX ix_mission_track ON mission (track_id);
CREATE INDEX ix_mission_crew_state ON mission (crew_id, state);
CREATE INDEX ix_mission_event_mission ON mission_event (mission_id, event_at);
CREATE INDEX ix_telemetry_mission ON telemetry_frame (mission_id, ts);
CREATE INDEX ix_personnel_role ON personnel (role_id);
CREATE INDEX ix_audit_entity ON audit_log (entity, entity_id);
CREATE INDEX ix_audit_time ON audit_log (logged_at);

COMMENT ON TABLE role IS 'Роль: Ролі користувачів для розмежування доступу (RBAC)';
COMMENT ON TABLE permission IS 'Право доступу: Елементарні права на операції в системі';
COMMENT ON TABLE role_permission IS 'Право ролі: Асоціативна таблиця зв’язку «багато-до-багатьох» між ролями та правами';
COMMENT ON TABLE sector IS 'Сектор: Зони відповідальності, заборони ураження, коридори дружньої авіації';
COMMENT ON TABLE interceptor_model IS 'Модель перехоплювача: Тактико-технічні межі моделей дронів-перехоплювачів для перевірки здійсненності місії';
COMMENT ON TABLE protected_object IS 'Об’єкт прикриття: Критична інфраструктура, яку прикриває центр';
COMMENT ON TABLE sensor IS 'Сенсор: Сенсорні вузли мережі виявлення та їх технічний стан';
COMMENT ON TABLE position IS 'Вогнева позиція: Позиції розрахунків перехоплювачів';
COMMENT ON TABLE crew IS 'Розрахунок: Розрахунки перехоплювачів і їх готовність';
COMMENT ON TABLE personnel IS 'Користувач: Особовий склад — користувачі системи';
COMMENT ON TABLE interceptor IS 'Перехоплювач: Екземпляри дронів-перехоплювачів та їх стан';
COMMENT ON TABLE air_track IS 'Повітряний трек: Повітряні цілі: стан, належність, оцінка загрози';
COMMENT ON TABLE detection IS 'Виявлення: Первинні виявлення, отримані від сенсорів';
COMMENT ON TABLE mission IS 'Місія: Бойові завдання на перехоплення та їх життєвий цикл';
COMMENT ON TABLE mission_event IS 'Подія місії: Хронологія подій кожної місії';
COMMENT ON TABLE telemetry_frame IS 'Кадр телеметрії: Телеметрія перехоплювача під час місії';
COMMENT ON TABLE engagement_report IS 'Звіт про перехоплення: Оцінка результату завершеної місії';
COMMENT ON TABLE audit_log IS 'Запис журналу аудиту: Незмінний журнал дій користувачів, сервісів і пристроїв';

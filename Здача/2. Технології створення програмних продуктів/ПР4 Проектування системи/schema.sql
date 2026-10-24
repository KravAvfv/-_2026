-- Схема БД IoT-платформи «Щит-Лінк» (фрагмент).
-- Згенеровано з діаграми класів фізичного рівня;
-- не редагувати вручну.

CREATE TYPE air_track_identity AS ENUM (
    'ворожа',
    'дружня',
    'нейтральна',
    'невідома'
);
CREATE TYPE crew_status AS ENUM (
    'готовий',
    'на завданні',
    'недоступний'
);
CREATE TYPE interceptor_state AS ENUM (
    'на складі',
    'готовий',
    'застосований',
    'втрачений'
);
CREATE TYPE engagement_report_assessment AS ENUM (
    'влучання',
    'промах',
    'скасовано'
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

CREATE TABLE air_track (
    track_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    track_number VARCHAR(12) NOT NULL,
    identity air_track_identity NOT NULL,
    threat_score DECIMAL(5,2) NOT NULL
);

CREATE TABLE crew (
    crew_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    position_id UUID NOT NULL,
    call_sign VARCHAR(20) NOT NULL,
    status crew_status NOT NULL
);

CREATE TABLE interceptor (
    interceptor_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    position_id UUID NOT NULL,
    serial_no VARCHAR(40) NOT NULL,
    state interceptor_state NOT NULL
);

CREATE TABLE personnel (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    role_id UUID NOT NULL,
    full_name VARCHAR(150) NOT NULL,
    mfa_enabled BOOL NOT NULL
);

CREATE TABLE mission (
    mission_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    track_id UUID NOT NULL
        REFERENCES air_track (track_id),
    crew_id UUID NOT NULL REFERENCES crew (crew_id),
    interceptor_id UUID
        REFERENCES interceptor (interceptor_id),
    approved_by UUID REFERENCES personnel (user_id),
    state mission_state NOT NULL,
    launched_at TIMESTAMPTZ
);

CREATE TABLE engagement_report (
    report_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mission_id UUID NOT NULL
        REFERENCES mission (mission_id) UNIQUE,
    assessment engagement_report_assessment NOT NULL
);

-- crew.position_id: таблиця-ціль поза фрагментом діаграми
-- interceptor.position_id: таблиця-ціль поза фрагментом діаграми
-- personnel.role_id: таблиця-ціль поза фрагментом діаграми

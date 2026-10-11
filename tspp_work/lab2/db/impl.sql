-- Серверна логіка БД IoT-платформи «Щит-Лінк» (ЛР2, реалізація ФВ-БД-04 … ФВ-БД-12).
-- Виконується після tspp_work/lab1/schema.sql. Користувач застосунку передається в межах транзакції:
--   SELECT set_config('app.user_id', '<uuid>', true);

-- ============================================================================ допоміжні функції
CREATE FUNCTION fn_app_user() RETURNS uuid LANGUAGE sql STABLE AS $$
    SELECT nullif(current_setting('app.user_id', true), '')::uuid
$$;

-- Відстань між двома точками WGS 84, км (формула гаверсинусів)
CREATE FUNCTION fn_dist_km(lat1 numeric, lon1 numeric, lat2 numeric, lon2 numeric)
RETURNS numeric LANGUAGE sql IMMUTABLE AS $$
    SELECT (2 * 6371 * asin(sqrt(
        power(sin(radians((lat2 - lat1)::float8) / 2), 2) +
        cos(radians(lat1::float8)) * cos(radians(lat2::float8)) *
        power(sin(radians((lon2 - lon1)::float8) / 2), 2))))::numeric
$$;

-- Чи має користувач право (матриця «роль — право»)
CREATE FUNCTION fn_has_perm(p_user uuid, p_code text) RETURNS boolean LANGUAGE sql STABLE AS $$
    SELECT EXISTS (SELECT 1 FROM personnel u
                   JOIN role_permission rp ON rp.role_id = u.role_id
                   JOIN permission p ON p.permission_id = rp.permission_id
                   WHERE u.user_id = p_user AND u.status = 'активний' AND p.code = p_code)
$$;

-- Остання відома позиція треку (за виявленнями з координатами)
CREATE FUNCTION fn_track_pos(p_track uuid, OUT lat numeric, OUT lon numeric, OUT speed numeric)
LANGUAGE sql STABLE AS $$
    SELECT d.lat, d.lon, d.speed_mps FROM detection d
    WHERE d.track_id = p_track AND d.lat IS NOT NULL
    ORDER BY d.detected_at DESC LIMIT 1
$$;

-- ============================================================================ ФВ-БД-04: прийом виявлення
-- Оцінка загрози: найближчий об’єкт прикриття, час підльоту, вага категорії об’єкта
CREATE FUNCTION fn_eval_threat(p_track uuid) RETURNS void LANGUAGE plpgsql AS $$
DECLARE
    pos record; obj record; v_eta int; w numeric; v_score numeric;
BEGIN
    SELECT * INTO pos FROM fn_track_pos(p_track);
    IF pos.lat IS NULL THEN RETURN; END IF;
    SELECT o.object_id, o.category, fn_dist_km(pos.lat, pos.lon, o.lat, o.lon) AS km INTO obj
    FROM protected_object o ORDER BY 3 LIMIT 1;
    IF obj.object_id IS NULL THEN RETURN; END IF;
    v_eta := CASE WHEN coalesce(pos.speed, 0) > 0 THEN round(obj.km * 1000 / pos.speed) END;
    w := CASE obj.category WHEN 'I' THEN 1.0 WHEN 'II' THEN 0.8 ELSE 0.6 END;
    -- загроза зростає, коли час підльоту наближається до нуля (горизонт 30 хв)
    v_score := round(100 * w * (1 - least(coalesce(v_eta, 1800), 1800) / 1800.0), 2);
    UPDATE air_track SET predicted_object_id = obj.object_id, eta_s = v_eta,
                         threat_score = greatest(v_score, CASE WHEN identity = 'ворожа' THEN 50 ELSE 0 END)
    WHERE track_id = p_track;
END $$;

CREATE FUNCTION fn_ingest_detection(p_sensor_serial text, p_detected_at timestamptz, p_lat numeric,
        p_lon numeric, p_alt numeric, p_speed numeric, p_bearing numeric, p_signature text, p_conf numeric)
RETURNS TABLE (detection_id bigint, track_id uuid, track_number varchar) LANGUAGE plpgsql AS $$
DECLARE
    s sensor%ROWTYPE; v_track uuid; v_det bigint; n_det int; n_src int; v_no varchar;
BEGIN
    SELECT * INTO s FROM sensor WHERE hw_serial = p_sensor_serial;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Невідомий сенсор %', p_sensor_serial USING ERRCODE = 'P0001';
    END IF;
    IF s.status NOT IN ('у мережі', 'деградований') THEN
        RAISE EXCEPTION 'Сенсор % у стані «%» — виявлення не приймаються', p_sensor_serial, s.status
              USING ERRCODE = 'P0002';
    END IF;
    UPDATE sensor SET last_heartbeat_at = greatest(coalesce(last_heartbeat_at, p_detected_at), p_detected_at)
    WHERE sensor_id = s.sensor_id;

    IF p_lat IS NOT NULL THEN
        -- зіставлення: активний трек, оновлений не раніше ніж 20 с тому, у радіусі 3 км
        SELECT t.track_id INTO v_track
        FROM air_track t, LATERAL fn_track_pos(t.track_id) tp
        WHERE t.state IN ('попередній', 'підтверджений', 'класифікований', 'перехоплюється')
          AND t.last_update_at >= p_detected_at - interval '20 seconds'
          AND tp.lat IS NOT NULL AND fn_dist_km(tp.lat, tp.lon, p_lat, p_lon) <= 3
        ORDER BY fn_dist_km(tp.lat, tp.lon, p_lat, p_lon) LIMIT 1;
        IF v_track IS NULL THEN              -- нове виявлення без пари — новий попередній трек
            SELECT 'ЩП-' || lpad((count(*) + 1)::text, 4, '0') INTO v_no
            FROM air_track WHERE track_date = p_detected_at::date;
            INSERT INTO air_track (track_number, track_date, first_seen_at, last_update_at)
            VALUES (v_no, p_detected_at::date, p_detected_at, p_detected_at) RETURNING air_track.track_id INTO v_track;
        END IF;
    END IF;

    INSERT INTO detection (sensor_id, track_id, detected_at, lat, lon, bearing_deg, altitude_m, speed_mps,
                           signature_class, confidence)
    VALUES (s.sensor_id, v_track, p_detected_at, p_lat, p_lon, p_bearing, p_alt, p_speed, p_signature, p_conf)
    RETURNING detection.detection_id INTO v_det;

    IF v_track IS NOT NULL THEN
        UPDATE air_track SET last_update_at = greatest(last_update_at, p_detected_at) WHERE air_track.track_id = v_track;
        -- підтвердження: ≥ 3 виявлення від ≥ 2 сенсорів
        SELECT count(*), count(DISTINCT d.sensor_id) INTO n_det, n_src FROM detection d WHERE d.track_id = v_track;
        UPDATE air_track SET state = 'підтверджений'
        WHERE air_track.track_id = v_track AND state = 'попередній' AND n_det >= 3 AND n_src >= 2;
        PERFORM fn_eval_threat(v_track);
    END IF;
    RETURN QUERY SELECT v_det, v_track, (SELECT t.track_number FROM air_track t WHERE t.track_id = v_track);
END $$;

-- Класифікація треку аналітиком
CREATE FUNCTION fn_classify_track(p_track uuid, p_identity air_track_identity, p_type text) RETURNS void
LANGUAGE plpgsql AS $$
BEGIN
    IF NOT fn_has_perm(fn_app_user(), 'track.classify') THEN
        RAISE EXCEPTION 'Немає права track.classify' USING ERRCODE = '42501';
    END IF;
    UPDATE air_track SET identity = p_identity, target_type = p_type, classified_by = fn_app_user(),
           state = CASE WHEN state IN ('попередній', 'підтверджений') THEN 'класифікований' ELSE state END
    WHERE track_id = p_track;
    PERFORM fn_eval_threat(p_track);
END $$;

-- ============================================================================ ФВ-БД-05: черга загроз
CREATE VIEW v_threat_queue AS
SELECT t.track_id, t.track_number, t.state, t.identity, t.target_type, t.threat_score, t.eta_s,
       o.name AS object_name, o.category AS object_category, t.last_update_at,
       (SELECT count(*) FROM detection d WHERE d.track_id = t.track_id) AS detections,
       (SELECT m.mission_no FROM mission m WHERE m.track_id = t.track_id
          AND m.state NOT IN ('відхилена', 'скасована', 'закрита') LIMIT 1) AS active_mission
FROM air_track t LEFT JOIN protected_object o ON o.object_id = t.predicted_object_id
WHERE t.state IN ('підтверджений', 'класифікований', 'перехоплюється')
ORDER BY t.threat_score DESC, t.eta_s NULLS LAST;

-- Кандидати-розрахунки для треку: готові, з готовим перехоплювачем, за відстанню від позиції
CREATE FUNCTION fn_crew_candidates(p_track uuid)
RETURNS TABLE (crew_id uuid, call_sign varchar, position_code varchar, dist_km numeric, ready_interceptors bigint,
               in_range boolean)
LANGUAGE sql STABLE AS $$
    SELECT c.crew_id, c.call_sign, p.code,
           round(fn_dist_km(p.lat, p.lon, tp.lat, tp.lon), 1),
           (SELECT count(*) FROM interceptor i WHERE i.position_id = p.position_id AND i.state = 'готовий'),
           fn_dist_km(p.lat, p.lon, tp.lat, tp.lon) * 1000 <= p.engagement_radius_m
    FROM crew c JOIN position p ON p.position_id = c.position_id, fn_track_pos(p_track) tp
    WHERE c.status = 'готовий' AND p.status = 'активна'
    ORDER BY 6 DESC, 4
$$;

-- ============================================================================ ФВ-БД-06/07: життєвий цикл місії
CREATE FUNCTION fn_propose_mission(p_track uuid, p_crew uuid) RETURNS uuid LANGUAGE plpgsql AS $$
DECLARE v_id uuid; v_no varchar;
BEGIN
    IF NOT fn_has_perm(fn_app_user(), 'mission.propose') THEN
        RAISE EXCEPTION 'Немає права mission.propose' USING ERRCODE = '42501';
    END IF;
    IF EXISTS (SELECT 1 FROM mission WHERE track_id = p_track
               AND state NOT IN ('відхилена', 'скасована', 'закрита')) THEN
        RAISE EXCEPTION 'Для треку вже є активна місія' USING ERRCODE = 'P0003';
    END IF;
    SELECT 'М-' || to_char(now(), 'MMDD') || '-' || lpad((count(*) + 1)::text, 2, '0') INTO v_no
    FROM mission WHERE proposed_at::date = now()::date;
    INSERT INTO mission (mission_no, track_id, crew_id, proposed_by)
    VALUES (v_no, p_track, p_crew, fn_app_user()) RETURNING mission_id INTO v_id;
    RETURN v_id;
END $$;

-- Допустимі переходи — діаграма станів сутності «Місія» (ПР4)
CREATE TABLE mission_transition (
    from_state mission_state, to_state mission_state, perm varchar(50) NOT NULL,
    PRIMARY KEY (from_state, to_state)
);
INSERT INTO mission_transition VALUES
    ('запропонована', 'відхилена', 'mission.approve'),
    ('запропонована', 'санкціонована', 'mission.approve'),
    ('санкціонована', 'перепризначена', 'mission.propose'),
    ('перепризначена', 'запропонована', 'mission.propose'),
    ('санкціонована', 'прийнята', 'mission.accept'),
    ('прийнята', 'виконується', 'mission.launch'),
    ('виконується', 'скасована', 'mission.abort'),
    ('виконується', 'закрита', 'mission.report');

CREATE FUNCTION trg_mission_guard() RETURNS trigger
LANGUAGE plpgsql AS $$
DECLARE
    v_perm varchar;
    v_user uuid := fn_app_user();
BEGIN
    IF NEW.state = OLD.state THEN RETURN NEW; END IF;
    SELECT perm INTO v_perm FROM mission_transition
    WHERE from_state = OLD.state AND to_state = NEW.state;
    IF NOT FOUND THEN                     -- перехід поза діаграмою станів
        RAISE EXCEPTION 'Недопустимий перехід стану місії: «%» → «%»',
              OLD.state, NEW.state USING ERRCODE = 'P0004';
    END IF;
    IF v_user IS NOT NULL AND NOT fn_has_perm(v_user, v_perm) THEN
        RAISE EXCEPTION 'Немає права % для переходу «%» → «%»',
              v_perm, OLD.state, NEW.state USING ERRCODE = '42501';
    END IF;
    CASE NEW.state
        WHEN 'санкціонована' THEN
            NEW.approved_by := coalesce(NEW.approved_by, v_user);
            NEW.approved_at := coalesce(NEW.approved_at, now());
        WHEN 'запропонована' THEN               -- після перепризначення санкцію потрібно отримати знову
            NEW.approved_by := NULL; NEW.approved_at := NULL;
        WHEN 'виконується' THEN
            IF NEW.interceptor_id IS NULL OR NOT EXISTS (SELECT 1 FROM interceptor
                   WHERE interceptor_id = NEW.interceptor_id AND state = 'готовий') THEN
                RAISE EXCEPTION 'Для пуску потрібен перехоплювач у стані «готовий»' USING ERRCODE = 'P0005';
            END IF;
            NEW.launched_at := coalesce(NEW.launched_at, now());
        WHEN 'скасована', 'закрита', 'відхилена' THEN
            NEW.closed_at := coalesce(NEW.closed_at, now());
        ELSE NULL;
    END CASE;
    RETURN NEW;
END $$;
CREATE TRIGGER mission_guard BEFORE UPDATE OF state ON mission FOR EACH ROW EXECUTE FUNCTION trg_mission_guard();

-- Хронологія та узгодження стану ресурсів
CREATE FUNCTION trg_mission_after() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE v_at timestamptz;
BEGIN
    IF TG_OP = 'UPDATE' AND NEW.state = OLD.state THEN RETURN NEW; END IF;
    v_at := CASE NEW.state WHEN 'запропонована' THEN coalesce(CASE WHEN TG_OP = 'INSERT' THEN NEW.proposed_at END, now())
                           WHEN 'санкціонована' THEN NEW.approved_at WHEN 'виконується' THEN NEW.launched_at
                           WHEN 'скасована' THEN NEW.closed_at WHEN 'закрита' THEN NEW.closed_at
                           WHEN 'відхилена' THEN NEW.closed_at ELSE now() END;
    -- app.event_at дає змогу завантажувати історичні дані з фактичним часом подій
    v_at := coalesce(nullif(current_setting('app.event_at', true), '')::timestamptz, v_at, now());
    INSERT INTO mission_event (mission_id, event_type, event_at, actor_id, payload)
    VALUES (NEW.mission_id, 'зміна стану', v_at, fn_app_user(),
            jsonb_build_object('з', CASE WHEN TG_OP = 'UPDATE' THEN OLD.state END, 'до', NEW.state));
    -- стан розрахунку, перехоплювача та треку
    IF NEW.state = 'прийнята' THEN
        UPDATE crew SET status = 'на завданні' WHERE crew_id = NEW.crew_id;
    ELSIF NEW.state IN ('відхилена', 'скасована', 'закрита') THEN
        UPDATE crew SET status = 'готовий' WHERE crew_id = NEW.crew_id;
    END IF;
    IF NEW.state = 'виконується' THEN
        UPDATE interceptor SET state = 'застосований', flight_count = flight_count + 1
        WHERE interceptor_id = NEW.interceptor_id;
        UPDATE air_track SET state = 'перехоплюється' WHERE track_id = NEW.track_id;
    ELSIF NEW.state = 'скасована' THEN
        UPDATE air_track SET state = 'класифікований' WHERE track_id = NEW.track_id AND state = 'перехоплюється';
    END IF;
    RETURN NEW;
END $$;
CREATE TRIGGER mission_after AFTER INSERT OR UPDATE OF state ON mission
    FOR EACH ROW EXECUTE FUNCTION trg_mission_after();

-- ============================================================================ ФВ-БД-08: звіт про перехоплення
CREATE FUNCTION trg_report_after() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE m mission%ROWTYPE; v_reusable boolean;
BEGIN
    SELECT * INTO m FROM mission WHERE mission_id = NEW.mission_id;
    SELECT im.reusable INTO v_reusable FROM interceptor i JOIN interceptor_model im USING (model_id)
    WHERE i.interceptor_id = m.interceptor_id;
    -- багаторазовий перехоплювач після промаху повертається в готовність; інакше вважається витраченим
    IF v_reusable AND NEW.assessment <> 'влучання' THEN
        UPDATE interceptor SET state = 'готовий' WHERE interceptor_id = m.interceptor_id;
    END IF;
    UPDATE air_track SET state = CASE NEW.assessment WHEN 'влучання' THEN 'знищений'::track_state
                                                     ELSE 'класифікований'::track_state END
    WHERE track_id = m.track_id AND state = 'перехоплюється';
    IF m.state = 'виконується' THEN
        UPDATE mission SET state = CASE WHEN NEW.assessment = 'скасовано' THEN 'скасована'::mission_state
                                        ELSE 'закрита'::mission_state END,
                           abort_reason = CASE WHEN NEW.assessment = 'скасовано'
                                               THEN coalesce(abort_reason, 'скасовано за звітом') END,
                           closed_at = NEW.submitted_at
        WHERE mission_id = NEW.mission_id;
    END IF;
    RETURN NEW;
END $$;
CREATE TRIGGER report_after AFTER INSERT ON engagement_report FOR EACH ROW EXECUTE FUNCTION trg_report_after();

-- ============================================================================ ФВ-БД-09: готовність ресурсів
CREATE VIEW v_readiness AS
SELECT p.code AS position_code, s.name AS sector_name, p.status AS position_status,
       count(DISTINCT c.crew_id) FILTER (WHERE c.status = 'готовий') AS crews_ready,
       count(DISTINCT c.crew_id) FILTER (WHERE c.status = 'на завданні') AS crews_tasked,
       count(DISTINCT c.crew_id) AS crews_total,
       count(DISTINCT i.interceptor_id) FILTER (WHERE i.state = 'готовий') AS interceptors_ready,
       count(DISTINCT i.interceptor_id) AS interceptors_total
FROM position p JOIN sector s USING (sector_id)
LEFT JOIN crew c ON c.position_id = p.position_id
LEFT JOIN interceptor i ON i.position_id = p.position_id
GROUP BY p.code, s.name, p.status ORDER BY p.code;

-- ============================================================================ ФВ-БД-10: аналітика
CREATE FUNCTION fn_mission_stats(p_from timestamptz, p_to timestamptz)
RETURNS TABLE (missions bigint, hits bigint, misses bigint, aborted bigint, rejected bigint, hit_rate numeric,
               avg_approve_s numeric, avg_launch_s numeric)
LANGUAGE sql STABLE AS $$
    SELECT count(*),
           count(*) FILTER (WHERE r.assessment = 'влучання'),
           count(*) FILTER (WHERE r.assessment = 'промах'),
           count(*) FILTER (WHERE m.state = 'скасована'),
           count(*) FILTER (WHERE m.state = 'відхилена'),
           round(100.0 * count(*) FILTER (WHERE r.assessment = 'влучання')
                 / nullif(count(*) FILTER (WHERE r.assessment IN ('влучання', 'промах')), 0), 1),
           round(avg(extract(epoch FROM m.approved_at - m.proposed_at)), 1),
           round(avg(extract(epoch FROM m.launched_at - m.approved_at)), 1)
    FROM mission m LEFT JOIN engagement_report r ON r.mission_id = m.mission_id
    WHERE m.proposed_at >= p_from AND m.proposed_at < p_to
$$;

-- ============================================================================ ФВ-БД-11: журнал аудиту
CREATE FUNCTION trg_audit() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE v_prev char(64); v_row jsonb; v_old jsonb; v_id text; v_actor uuid := fn_app_user(); v_ts timestamptz := clock_timestamp();
        v_hash char(64); v_action text;
BEGIN
    v_row := CASE WHEN TG_OP = 'DELETE' THEN NULL ELSE to_jsonb(NEW) END;
    v_old := CASE WHEN TG_OP = 'INSERT' THEN NULL ELSE to_jsonb(OLD) END;
    v_id := coalesce(v_row, v_old) ->> (SELECT a.attname FROM pg_index i
              JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = i.indkey[0]
              WHERE i.indrelid = TG_RELID AND i.indisprimary);
    v_action := TG_TABLE_NAME || '.' || lower(TG_OP);
    PERFORM pg_advisory_xact_lock(4242);                  -- послідовний ланцюжок хешів
    SELECT hash INTO v_prev FROM audit_log ORDER BY entry_id DESC LIMIT 1;
    v_hash := encode(sha256(convert_to(concat_ws('|', v_prev, extract(epoch FROM v_ts), v_actor, v_action, TG_TABLE_NAME, v_id,
                     jsonb_build_object('до', v_old, 'після', v_row)::text), 'UTF8')), 'hex');
    INSERT INTO audit_log (logged_at, actor_id, actor_type, action, entity, entity_id, details, prev_hash, hash)
    VALUES (v_ts, v_actor, (CASE WHEN v_actor IS NULL THEN 'сервіс' ELSE 'користувач' END)::actor_type, v_action,
            TG_TABLE_NAME, v_id, jsonb_build_object('до', v_old, 'після', v_row), v_prev, v_hash);
    RETURN NULL;
END $$;
CREATE TRIGGER audit_mission AFTER INSERT OR UPDATE OR DELETE ON mission FOR EACH ROW EXECUTE FUNCTION trg_audit();
CREATE TRIGGER audit_personnel AFTER INSERT OR UPDATE OR DELETE ON personnel FOR EACH ROW EXECUTE FUNCTION trg_audit();
CREATE TRIGGER audit_role_permission AFTER INSERT OR UPDATE OR DELETE ON role_permission
    FOR EACH ROW EXECUTE FUNCTION trg_audit();
CREATE TRIGGER audit_report AFTER INSERT OR UPDATE OR DELETE ON engagement_report
    FOR EACH ROW EXECUTE FUNCTION trg_audit();

CREATE FUNCTION trg_audit_immutable() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION 'Журнал аудиту незмінний: операція % заборонена', TG_OP USING ERRCODE = '42501';
END $$;
CREATE TRIGGER audit_immutable BEFORE UPDATE OR DELETE ON audit_log FOR EACH ROW EXECUTE FUNCTION trg_audit_immutable();
CREATE TRIGGER audit_no_truncate BEFORE TRUNCATE ON audit_log FOR EACH STATEMENT EXECUTE FUNCTION trg_audit_immutable();

-- Перевірка цілісності ланцюжка: перерахунок хешу кожного запису
CREATE FUNCTION fn_audit_verify() RETURNS TABLE (checked bigint, broken bigint, first_broken bigint)
LANGUAGE sql STABLE AS $$
    WITH c AS (
        SELECT entry_id, hash, prev_hash, lag(hash) OVER (ORDER BY entry_id) AS real_prev,
               encode(sha256(convert_to(concat_ws('|', prev_hash, extract(epoch FROM logged_at), actor_id, action, entity, entity_id,
                      details::text), 'UTF8')), 'hex') AS recomputed
        FROM audit_log)
    SELECT count(*),
           count(*) FILTER (WHERE recomputed <> hash OR prev_hash IS DISTINCT FROM real_prev),
           min(entry_id) FILTER (WHERE recomputed <> hash OR prev_hash IS DISTINCT FROM real_prev)
    FROM c
$$;

-- ============================================================================ ФВ-БД-12: ролі СКБД
CREATE ROLE shch_analyst NOLOGIN;
CREATE ROLE shch_officer NOLOGIN;
CREATE ROLE shch_crew NOLOGIN;
CREATE ROLE shch_admin NOLOGIN;
CREATE ROLE shch_security NOLOGIN;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO shch_analyst, shch_officer, shch_crew;
REVOKE SELECT ON audit_log FROM shch_analyst, shch_officer, shch_crew;
GRANT UPDATE (identity, target_type, classified_by, state) ON air_track TO shch_analyst;
GRANT INSERT, UPDATE ON mission, mission_event TO shch_officer;
GRANT UPDATE (state, interceptor_id) ON mission TO shch_crew;
GRANT INSERT ON engagement_report, mission_event, telemetry_frame TO shch_crew;
GRANT SELECT, INSERT, UPDATE ON personnel, role, permission, role_permission TO shch_admin;
GRANT SELECT ON audit_log TO shch_security;
GRANT INSERT ON audit_log TO shch_analyst, shch_officer, shch_crew, shch_admin;

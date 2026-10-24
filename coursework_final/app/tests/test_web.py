"""Веб-застосунок: автентифікація, розмежування доступу за ролями, сценарії користувачів."""
import re
import time

import pytest

import seed
from conftest import login, one, post

LOGINS = {"R-01": "och1", "R-02": "obu1", "R-03": "an1", "R-04": "cmd01", "R-05": "pilot01", "R-06": "r06_1",
          "R-07": "r07_1", "R-08": "r08_1", "R-09": "r09_1", "R-10": "r10_1", "R-11": "r11_1", "R-12": "r12_1",
          "R-13": "r13_1"}
PAGES = {"/": (), "/search?q=ЩП": (), "/situation": ("track.read",), "/missions": ("mission.read",),
         "/resources": ("resource.read",), "/interceptors/new": ("interceptor.manage",),
         "/sensors": ("sensor.manage",), "/sensors/new": ("sensor.manage",), "/objects": ("sector.manage",),
         "/detections/new": ("detection.write",), "/analytics": ("analytics.read",), "/audit": ("audit.read",),
         "/users": ("user.manage", "user.block"), "/users/new": ("user.manage",), "/roles": ("role.manage",)}
PERMS = {code: set(perms.split()) for code, _name, _combat, perms in seed.ROLES}


def flash_text(resp):
    return " ".join(re.findall(r'<div class="flash [a-z]+">(.*?)</div>', resp.get_data(as_text=True)))


# ------------------------------------------------------------------ автентифікація
def test_login_page_and_redirect(client):
    assert client.get("/situation").status_code == 302
    r = client.get("/login")
    assert r.status_code == 200 and "Пароль" in r.get_data(as_text=True)


def test_login_success_and_wrong_password(client):
    assert login(client, "och1", "wrong-pass").status_code == 401
    r = login(client, "och1")
    assert r.status_code == 302 and r.headers["Location"].endswith("/")
    assert "Головна сторінка" in client.get("/").get_data(as_text=True)


def test_lockout_after_five_failures(client, conn):
    for _ in range(5):
        r = login(client, "an4", "bad")
    assert "заблоковано" in r.get_data(as_text=True)
    assert one(conn, "SELECT status FROM personnel WHERE login = 'an4'") == "призупинений"
    assert login(client, "an4").status_code == 401                 # правильний пароль уже не допомагає


def test_csrf_required(client):
    login(client, "obu1")
    assert client.post("/roles", data={"role_id": 1}).status_code == 400


def test_idle_timeout(client):
    login(client, "och1")
    with client.session_transaction() as s:
        s["seen"] = time.time() - 16 * 60
    r = client.get("/situation")
    assert r.status_code == 302 and "/login" in r.headers["Location"]


# ------------------------------------------------------------------ матриця доступу «роль × сторінка»
@pytest.mark.parametrize("role", sorted(LOGINS))
def test_access_matrix(client, role):
    login(client, LOGINS[role])
    for url, perms in PAGES.items():
        expected = 200 if not perms or PERMS[role].intersection(perms) else 403
        assert client.get(url).status_code == expected, (role, url)


def test_menu_matches_permissions(client):
    login(client, "r10_1")                                         # адміністратор: без бойових розділів
    html = client.get("/").get_data(as_text=True)
    assert "Користувачі" in html and "Ролі та права" in html
    assert ">Обстановка<" not in html and ">Місії<" not in html


# ------------------------------------------------------------------ сценарій бойової місії через інтерфейс
def test_full_mission_lifecycle(client, conn):
    tid = one(conn, "SELECT track_id FROM v_threat_queue WHERE identity = 'ворожа' AND active_mission IS NULL "
              "ORDER BY threat_score DESC LIMIT 1")
    login(client, "obu1")
    crew = one(conn, "SELECT crew_id FROM fn_crew_candidates(%s) LIMIT 1", tid)
    r = post(client, f"/tracks/{tid}", {"action": "propose", "crew_id": crew})
    mid = r.headers["Location"].rsplit("/", 1)[1]
    assert one(conn, "SELECT state FROM mission WHERE mission_id = %s", mid) == "запропонована"
    # автор пропозиції не бачить кнопки санкції; ОЧ — бачить
    assert "Санкціонувати" not in client.get(f"/missions/{mid}").get_data(as_text=True)
    login(client, "och1")
    assert "Санкціонувати" in client.get(f"/missions/{mid}").get_data(as_text=True)
    post(client, f"/missions/{mid}", {"action": "transition", "to_state": "санкціонована"})
    cmd = one(conn, "SELECT login FROM personnel u JOIN role r USING (role_id) WHERE r.code = 'R-04' AND crew_id = %s",
              crew)
    other = one(conn, "SELECT login FROM personnel u JOIN role r USING (role_id) WHERE r.code = 'R-04' "
                "AND crew_id <> %s LIMIT 1", crew)
    login(client, other)                                           # чужий розрахунок
    assert "Прийняти завдання" not in client.get(f"/missions/{mid}").get_data(as_text=True)
    r = post(client, f"/missions/{mid}", {"action": "transition", "to_state": "прийнята"}, follow_redirects=True)
    assert "іншому розрахунку" in flash_text(r)
    login(client, cmd)
    post(client, f"/missions/{mid}", {"action": "transition", "to_state": "прийнята"})
    itc = one(conn, "SELECT interceptor_id FROM interceptor i JOIN crew c USING (position_id) WHERE c.crew_id = %s "
              "AND i.state = 'готовий' LIMIT 1", crew)
    post(client, f"/missions/{mid}", {"action": "transition", "to_state": "виконується", "interceptor_id": itc})
    post(client, f"/missions/{mid}", {"action": "report", "assessment": "влучання"})
    assert one(conn, "SELECT state FROM mission WHERE mission_id = %s", mid) == "закрита"
    assert one(conn, "SELECT state FROM air_track WHERE track_id = %s", tid) == "знищений"
    # створення + 4 переходи: санкціонована, прийнята, виконується, закрита
    assert one(conn, "SELECT count(*) FROM mission_event WHERE mission_id = %s", mid) == 5
    assert one(conn, "SELECT broken FROM fn_audit_verify()") == 0


def test_invalid_transition_shows_reason(client, conn):
    mid = one(conn, "SELECT mission_id FROM mission WHERE state = 'закрита' LIMIT 1")
    login(client, "och1")
    r = post(client, f"/missions/{mid}", {"action": "transition", "to_state": "санкціонована"}, follow_redirects=True)
    assert "Недопустимий перехід" in flash_text(r)


def test_classify_track(client, conn):
    tid = one(conn, "SELECT track_id FROM v_threat_queue WHERE identity = 'невідома' LIMIT 1")
    login(client, "an1")
    post(client, f"/tracks/{tid}", {"action": "classify", "identity": "ворожа", "target_type": "ударний БпЛА"})
    assert one(conn, "SELECT identity FROM air_track WHERE track_id = %s", tid) == "ворожа"


# ------------------------------------------------------------------ форми введення, редагування, пошуку
def test_manual_detection(client, conn):
    login(client, "r06_1")
    n = one(conn, "SELECT count(*) FROM detection")
    r = post(client, "/detections/new", {"sensor": "OB-0001", "lat": "51.70", "lon": "31.20", "alt": "150",
                                          "speed": "45", "signature": "розвідувальний", "confidence": "0.8"})
    assert r.status_code == 302 and "/tracks/" in r.headers["Location"]
    assert one(conn, "SELECT count(*) FROM detection") == n + 1


def test_interceptor_crud(client, conn):
    login(client, "r08_1")
    model = one(conn, "SELECT model_id FROM interceptor_model LIMIT 1")
    post(client, "/interceptors/new", {"serial_no": "ПХ-T0001", "model_id": model, "position_id": "",
                                       "state": "на складі", "firmware_version": "4.1.0"})
    iid = one(conn, "SELECT interceptor_id FROM interceptor WHERE serial_no = 'ПХ-T0001'")
    post(client, f"/interceptors/{iid}/edit", {"serial_no": "ПХ-T0001", "model_id": model, "position_id": "",
                                                "state": "на складі", "firmware_version": "4.3.1"})
    assert one(conn, "SELECT firmware_version FROM interceptor WHERE interceptor_id = %s", iid) == "4.3.1"
    post(client, f"/interceptors/{iid}/delete")
    assert one(conn, "SELECT count(*) FROM interceptor WHERE interceptor_id = %s", iid) == 0
    used = one(conn, "SELECT interceptor_id FROM interceptor WHERE flight_count > 0 LIMIT 1")
    r = post(client, f"/interceptors/{used}/delete", headers={"Referer": "/resources"}, follow_redirects=True)
    assert "Неможливо видалити" in flash_text(r)


def test_sensor_register_and_transition(client, conn):
    login(client, "r07_1")
    sec = one(conn, "SELECT sector_id FROM sector LIMIT 1")
    post(client, "/sensors/new", {"hw_serial": "AC-T001", "kind": "акустичний", "sector_id": sec, "lat": "51.5",
                                  "lon": "31.5", "height_m": "6"})
    sid = one(conn, "SELECT sensor_id FROM sensor WHERE hw_serial = 'AC-T001'")
    assert one(conn, "SELECT status FROM sensor WHERE sensor_id = %s", sid) == "зареєстрований"
    form = {"lat": "51.5", "lon": "31.5", "height_m": "6", "sector_id": sec}
    r = post(client, f"/sensors/{sid}/edit", {**form, "status": "виведений"})
    assert "Недопустимий перехід стану сенсора" in r.get_data(as_text=True)
    post(client, f"/sensors/{sid}/edit", {**form, "status": "у мережі"})
    assert one(conn, "SELECT status FROM sensor WHERE sensor_id = %s", sid) == "у мережі"
    page = client.get("/sensors?kind=акустичний&status=у+мережі&q=AC-T").get_data(as_text=True)
    assert "AC-T001" in page and "RD-" not in page


def test_object_edit(client, conn):
    login(client, "r12_1")
    o = conn.execute("SELECT object_id, name, lat, lon FROM protected_object WHERE category = 'III' LIMIT 1").fetchone()
    post(client, f"/objects/{o['object_id']}/edit", {"name": o["name"], "category": "II", "lat": o["lat"],
                                                      "lon": o["lon"]})
    assert one(conn, "SELECT category FROM protected_object WHERE object_id = %s", o["object_id"]) == "II"
    html = client.get("/objects?cat=II").get_data(as_text=True)
    assert o["name"] in html and "<td>III</td>" not in html


def test_missions_filter(client, conn):
    login(client, "obu1")
    html = client.get("/missions?state=відхилена").get_data(as_text=True)
    n = one(conn, "SELECT count(*) FROM mission WHERE state = 'відхилена'")
    assert html.count('class="badge s-off">відхилена') == n
    no = one(conn, "SELECT mission_no FROM mission ORDER BY proposed_at LIMIT 1")
    html = client.get(f"/missions?q={no}").get_data(as_text=True)
    assert no in html and html.count("<tr>") == 2                   # заголовок + один рядок
    crew = one(conn, "SELECT c.call_sign FROM mission m JOIN crew c USING (crew_id) LIMIT 1")
    html = client.get(f"/missions?crew={crew}").get_data(as_text=True)
    others = [c for c in re.findall(r"<td>([А-ЯІЇЄҐ][а-яіїєґ’]+-\d)</td>", html) if c != crew]
    assert not others


def test_search_respects_permissions(client, conn):
    no = one(conn, "SELECT track_number FROM air_track LIMIT 1")
    login(client, "an1")
    assert f">{no}</a>" in client.get(f"/search?q={no}").get_data(as_text=True)
    login(client, "r10_1")                                         # адміністратор не бачить треків
    html = client.get(f"/search?q={no}").get_data(as_text=True)
    assert f">{no}</a>" not in html and "Знайдено: 0" in html


# ------------------------------------------------------------------ адміністрування
def test_user_create_block_and_own_status(client, conn):
    login(client, "r10_1")
    role = one(conn, "SELECT role_id FROM role WHERE code = 'R-09'")
    r = post(client, "/users/new", {"login": "new_an", "full_name": "Тестовий К. Л.", "rank": "", "role_id": role,
                                    "crew_id": "", "admission_valid_to": "", "password": "short"})
    assert "щонайменше 8" in r.get_data(as_text=True)
    post(client, "/users/new", {"login": "new_an", "full_name": "Тестовий К. Л.", "rank": "", "role_id": role,
                                "crew_id": "", "admission_valid_to": "", "mfa_enabled": "on", "password": "Strong-pass1"})
    assert login(client, "new_an", "Strong-pass1").status_code == 302
    login(client, "r11_1")
    uid = one(conn, "SELECT user_id FROM personnel WHERE login = 'new_an'")
    post(client, f"/users/{uid}/status", {"status": "призупинений"})
    assert login(client, "new_an", "Strong-pass1").status_code == 401
    login(client, "r11_1")
    me = one(conn, "SELECT user_id FROM personnel WHERE login = 'r11_1'")
    r = post(client, f"/users/{me}/status", {"status": "призупинений"}, follow_redirects=True)
    assert "власного" in flash_text(r)
    assert one(conn, "SELECT count(*) FROM audit_log WHERE entity = 'personnel' AND entity_id = %s", str(uid)) >= 2


def test_roles_matrix(client, conn):
    login(client, "r10_1")
    r12, r13 = (one(conn, "SELECT role_id FROM role WHERE code = %s", c) for c in ("R-12", "R-13"))
    approve = one(conn, "SELECT permission_id FROM permission WHERE code = 'mission.approve'")
    res = one(conn, "SELECT permission_id FROM permission WHERE code = 'resource.read'")
    r = post(client, "/roles", {"role_id": r12, "permission_id": approve, "grant": "1"}, follow_redirects=True)
    assert "не має бойових прав" in flash_text(r)
    post(client, "/roles", {"role_id": r13, "permission_id": res, "grant": "1"})
    assert one(conn, "SELECT count(*) FROM role_permission WHERE role_id = %s AND permission_id = %s", r13, res) == 1
    post(client, "/roles", {"role_id": r13, "permission_id": res, "grant": "0"})
    assert one(conn, "SELECT count(*) FROM role_permission WHERE role_id = %s AND permission_id = %s", r13, res) == 0


def test_pages_render(client, conn):
    login(client, "r09_1")
    assert "частка влучань" in client.get("/analytics?from=2000-01-01&to=2100-01-01").get_data(as_text=True)
    login(client, "r11_1")
    html = client.get("/audit?entity=mission").get_data(as_text=True)
    assert "порушень — 0" in html and "personnel." not in html
    login(client, "och1")
    assert client.get("/missions/00000000-0000-0000-0000-000000000000").status_code == 404
    assert "<svg class=\"map\"" in client.get("/situation").get_data(as_text=True)

# Курсова робота з ПІС — «Проєктування розподіленої IoT-системи обміну телеметрією та координації дронів-перехоплювачів»

| Файл / каталог | Вміст |
|---|---|
| `КР_Кравченко_ІР-31.docx`, `.pdf` | пояснювальна записка |
| `REQUIREMENTS.md` | усі вимоги методичних вказівок із номерами сторінок |
| `app/` | прототип: `db/schema.sql`, `db/impl.sql`, `db/seed.py`, `app.py`, `templates/`, `static/`, `tests/` |
| `app/serve.py` | живий запуск для захисту: http://127.0.0.1:5080 (пароль усіх облікових записів — `shchit-demo`) |
| `app/run_demo.py` | тимчасова БД → застосунок → знімки екрана → `demo.json` (факти для записки) → тести |
| `model/` | `cw_model.py` (дані КР), `make_diagrams.py`, `make_report.py`, `consistency.py` (діаграми ↔ код), `check_docx.py` |
| `diagrams/` | усі діаграми (джерела `.mmd`/`.puml`/`.bpmn`, PNG) і `screens/` — знімки з працюючого застосунку |
| `build_cw.py`, `report.yaml` | збирання .docx/.pdf за вимогами розд. 4.3 методичних вказівок |

## Відтворення

```sh
.venv/bin/python -m pytest -q coursework_final/app/tests        # 51 тест
.venv/bin/python coursework_final/app/run_demo.py               # знімки екрана + demo.json
.venv/bin/python coursework_final/model/make_diagrams.py        # діаграми
.venv/bin/python coursework_final/model/make_report.py          # report.yaml
.venv/bin/python coursework_final/build_cw.py coursework_final/report.yaml --pdf
.venv/bin/python coursework_final/model/consistency.py && .venv/bin/python coursework_final/model/check_docx.py
```

Потрібно: PostgreSQL 18 (`initdb`, `pg_ctl` у PATH), Python-середовище `.venv` (Flask, psycopg, pytest, python-docx),
`mmdc`, Java + `tools/plantuml/plantuml.jar`, `tools/bpmn/node_modules`, OnlyOffice x2t (PDF).

Обсяг записки — 50 сторінок разом із титульним аркушем, завданням, змістом і переліком джерел (вимога викладача);
додатків немає. Дерево цілей (рис. 1.2) і WBS узято з ЛР1 (`lab1/make_lab1.py`, `GOAL_TREE`) — одне джерело даних.
Застосунок підключається до PostgreSQL від ролі `shch_app` без прав суперкористувача (визначена в `db/impl.sql`);
без автентифікованого користувача стан місії змінити не можна (перевіряє тест `test_app_role_cannot_change_state_without_user`).

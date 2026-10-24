#!/usr/bin/env python3
"""Живий запуск прототипу АРМ «Щит-Лінк» для демонстрації на захисті: тимчасова БД PostgreSQL з тестовими
даними + веб-застосунок на http://127.0.0.1:5080 (зупинка — Ctrl+C, БД видаляється).

    .venv/bin/python coursework_final/app/serve.py           # розширений демонстраційний набір (seed rich=True)
    .venv/bin/python coursework_final/app/serve.py --basic   # набір, на якому зроблено знімки й факти записки
Облікові записи (пароль seed.DEMO_PASSWORD): och1 (ОЧ), obu1 (ОБУ), an1 (аналітик), cmd01… (командири), pilot01…
(оператори), r06_1 (пост спостереження), r07_1 (технік), r08_1 (логіст), r09_1 (аналітик ефективності),
r10_1 (адміністратор), r11_1 (офіцер кібербезпеки), r12_1 (начальник центру), r13_1 (інструктор).
"""
import os
import signal
import sys
from pathlib import Path

import psycopg

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE / "db"), str(HERE / "app")]
import pgtemp  # noqa: E402
import seed  # noqa: E402

PORT = int(os.environ.get("PORT", 5080))

if __name__ == "__main__":
    signal.signal(signal.SIGTERM, lambda *_: (_ for _ in ()).throw(KeyboardInterrupt))   # прибрати БД і при kill
    with pgtemp.TempCluster(port=54332) as pg:
        pg.psql_file(pgtemp.SCHEMA)
        pg.psql_file(pgtemp.IMPL)
        with psycopg.connect(pg.dsn) as c:
            seed.seed(c, rich="--basic" not in sys.argv)
        os.environ["SHCH_DSN"] = pg.dsn.replace("user=postgres", "user=shch_app")
        import app as webapp  # noqa: E402
        print(f"АРМ «Щит-Лінк»: http://127.0.0.1:{PORT}  пароль: {seed.DEMO_PASSWORD}  (Ctrl+C — зупинити)")
        try:
            webapp.app.run(host="127.0.0.1", port=PORT)
        except KeyboardInterrupt:
            pass

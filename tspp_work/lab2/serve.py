#!/usr/bin/env python3
"""Живий запуск АРМ «Щит-Лінк» для демонстрації на захисті: тимчасова БД PostgreSQL з тестовими даними +
веб-застосунок на http://127.0.0.1:5080 (зупинка — Ctrl+C, БД видаляється).

    .venv/bin/python tspp_work/lab2/serve.py
Облікові записи для входу: obu1 (ОБУ), och1 (ОЧ), an1 (аналітик), cmd01… (командири), r08_1 (логіст),
r09_1 (аналітик ефективності), r11_1 (офіцер кібербезпеки).
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
            seed.seed(c)
        os.environ["SHCH_DSN"] = pg.dsn
        import app as webapp  # noqa: E402
        print(f"АРМ «Щит-Лінк»: http://127.0.0.1:{PORT}  (Ctrl+C — зупинити)")
        try:
            webapp.app.run(host="127.0.0.1", port=PORT)
        except KeyboardInterrupt:
            pass

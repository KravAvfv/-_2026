"""Тимчасовий кластер PostgreSQL для розгортання, перевірки та демонстрації БД «Щит-Лінк».

    with TempCluster() as pg:
        pg.psql_file(SCHEMA); conn = psycopg.connect(pg.dsn)
"""
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SCHEMA = ROOT / "tspp_work/lab1/schema.sql"
IMPL = HERE / "db/impl.sql"


class TempCluster:
    def __init__(self, port=54331, keep=False):
        self.port, self.keep = port, keep
        self.dir = Path(tempfile.mkdtemp(prefix="shch_pg_"))
        self.data, self.sock = self.dir / "data", self.dir / "sock"
        self.env = {**os.environ, "LC_ALL": "C.UTF-8", "PGTZ": "Europe/Kyiv"}
        self.dsn = f"host={self.sock} port={port} user=postgres dbname=shchit"

    def _run(self, *args, **kw):
        r = subprocess.run(args, capture_output=True, text=True, env=self.env, **kw)
        if r.returncode:
            raise RuntimeError(f"{args[0]}: {r.stderr.strip()}")
        return r.stdout

    def __enter__(self):
        self.sock.mkdir()
        self._run("initdb", "-D", str(self.data), "-U", "postgres", "-E", "UTF8", "--locale=C.UTF-8",
                  "--auth=trust")
        self._run("pg_ctl", "-D", str(self.data), "-o",
                  f"-k {self.sock} -c listen_addresses='' -p {self.port} -c timezone=Europe/Kyiv", "-w", "start",
                  "-l", str(self.dir / "server.log"))
        self.psql("CREATE DATABASE shchit", db="postgres")
        return self

    def psql(self, sql, db="shchit", args=()):
        return self._run("psql", "-h", str(self.sock), "-p", str(self.port), "-U", "postgres", "-d", db, "-X",
                         "-v", "ON_ERROR_STOP=1", *args, input=sql)

    def psql_file(self, path):
        return self.psql(Path(path).read_text(encoding="utf-8"))

    def tool(self, name, *args):
        return self._run(name, "-h", str(self.sock), "-p", str(self.port), "-U", "postgres", *args)

    def __exit__(self, *exc):
        subprocess.run(["pg_ctl", "-D", str(self.data), "-m", "fast", "stop"], capture_output=True, env=self.env)
        if not self.keep:
            shutil.rmtree(self.dir, ignore_errors=True)

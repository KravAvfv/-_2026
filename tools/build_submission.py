#!/usr/bin/env python3
"""Збирає папку «Здача»: для кожної роботи кожної дисципліни — звіт (.docx + .pdf), додаткові матеріали, що здаються
разом зі звітом (draw.io, BPMN, Excel, PowerPoint, SQL, вихідний код прототипу, фото конспекту), і суфлери
(tools/make_speeches.py) — усе в одній папці роботи. Покажчик — Здача/README.md.

Робочі папки (lab*/, tspp_work/, tau_work/, …) лишаються джерелом: тут лише копії готових файлів, тому після
перебудови будь-якої роботи достатньо знову запустити цей скрипт.

    .venv/bin/python tools/build_submission.py
"""
import shutil
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import make_speeches as S  # noqa: E402
from uk_plural import n_uk  # noqa: E402

ROOT = S.ROOT
OUT = S.OUT
TAU = ROOT / "ТАУ"
BANK = ROOT / "Системи банкової безпеки"
NUFT = ROOT / "Технології створення програмних продуктів" / "НУХТ" / "Готово"
SKIP = {"__pycache__", ".pytest_cache", "node_modules"}


def pis_lab(n):
    lab = ROOT / f"lab{n}"
    files = [lab / f"ЛР{n}_Кравченко_ІР-31.docx", lab / f"ЛР{n}_Кравченко_ІР-31.pdf"]
    files += [("draw.io", p) for p in sorted((lab / "drawio").glob("*.drawio"))]
    if n == 2:  # BPMN 2.0 XML — ті самі моделі у форматі стандарту (відкриваються будь-яким BPMN-редактором)
        files += [("BPMN", p) for p in sorted((lab / "diagrams").glob("*.bpmn"))]
    return files


def zipdir(src, dst, include):
    """Архів вихідного коду: лише перелічені файли/каталоги, без кешів."""
    dst.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as z:
        for rel in include:
            p = src / rel
            items = [p] if p.is_file() else sorted(x for x in p.rglob("*") if x.is_file())
            for f in items:
                if not SKIP & set(f.relative_to(src).parts):
                    z.write(f, f.relative_to(src.parent))
    return dst


def materials(work):
    """Файли роботи: шлях або (підпапка, шлях); "zip" — (назва, джерело, перелік) для архіву коду."""
    subj, folder, *_ , report = work
    rep = ROOT / report
    pair = [rep, rep.with_suffix(".pdf")] if rep.suffix == ".docx" else [rep]
    if subj == "pis" and folder.startswith("ЛР"):
        return pis_lab(int(folder[2:]))
    if subj == "pis":                                    # курсова робота
        cw = ROOT / "coursework_final"
        return pair + [cw / "КР_Кравченко_ІР-31_презентація.pptx", cw / "КР_Кравченко_ІР-31_презентація.pdf",
                       ("zip", "Прототип_вихідний_код.zip", cw, ["app", "README.md"])]
    if subj == "tspp":
        extra = {"ПР4": [ROOT / "tspp_work/pract4/schema.sql"],
                 "ЛР1": [p for p in (ROOT / "tspp_work/lab1").glob("*.sql")],
                 "ЛР2": [("zip", "Програмний_продукт_вихідний_код.zip", ROOT / "tspp_work/lab2",
                          ["app", "db", "run_demo.py", "serve.py"]),
                         ROOT / "tspp_work/lab1/schema.sql"]}.get(folder, [])   # схема БД з ЛР1, на якій будується ЛР2
        return pair + extra
    if subj == "tau":
        n = folder[2:]
        photos = sorted((TAU / "Готові ПЗ (варіант 8)").glob(f"ПЗ{n}_стор*.jpg"),
                        key=lambda p: int(p.stem.split("стор")[1]))
        return pair + [("Фото конспекту", p) for p in photos] + \
            [("Фото конспекту", TAU / "Готові ПЗ (варіант 8)" / f"ПЗ{n}_Кравченко_варіант8.pdf")]
    if subj == "bank":
        n = folder[2:]
        return sorted((BANK / f"Практична {n}" / "Готово").glob("*"))
    return pair                                          # кібербезпека


def copy(src, dst):
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    return dst


def main():
    for sub in S.SUBJ_DIR.values():                      # повна перебудова: без застарілих копій
        shutil.rmtree(OUT / sub, ignore_errors=True)
    index = S.main([])
    lines = ["# Здача робіт — Кравченко П. О., гр. ІР-31", "",
             "Кожна папка роботи містить звіт (.docx для здачі і .pdf для перегляду), додаткові матеріали, що "
             "здаються разом зі звітом, і папку **Суфлер**: `00_Сценарій_демонстрації.docx` (що показати і що "
             "сказати на кожному кроці) та суфлери до кожного компонента роботи (схеми, таблиці, аркуші, слайди).",
             "", "Згенеровано `tools/build_submission.py` з робочих папок репозиторію; вручну тут нічого не "
             "редагується.", ""]
    missing = []
    current = None
    for work in S.WORKS:
        subj, folder, label, title, *_ = work
        wd = S.work_dir(work)
        if subj != current:
            current = subj
            lines += [f"## {S.SUBJ_DIR[subj]}", ""]
        got = []
        for m in materials(work):
            if isinstance(m, tuple) and m[0] == "zip":
                got.append(zipdir(m[2], wd / m[1], m[3]))
                continue
            sub, src = m if isinstance(m, tuple) else ("", m)
            if not src.exists():
                missing.append(str(src.relative_to(ROOT)))
                continue
            got.append(copy(src, wd / sub / src.name))
        rel = lambda p: str(p.relative_to(OUT)).replace(" ", "%20")
        lines.append(f"### {label} — {title}")
        lines.append("")
        top = [p for p in got if p.parent == wd]
        subs = sorted({p.parent for p in got if p.parent != wd})
        for p in top:
            lines.append(f"- [{p.name}]({rel(p)})")
        for d in subs:
            n = sum(1 for p in got if p.parent == d)
            lines.append(f"- [{d.name}/]({rel(d)}) — {n_uk(n, 'файл', 'файли', 'файлів')}")
        lines.append(f"- **Суфлер** — {n_uk(len(index[work]), 'документ', 'документи', 'документів')}:")
        for p, t in index[work]:
            lines.append(f"  - [{t}]({rel(p)})")
        lines.append("")
    if missing:
        raise SystemExit("Немає файлів (спершу зберіть роботи):\n  " + "\n  ".join(missing))
    (OUT / "README.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"Здача: {sum(1 for _ in OUT.rglob('*') if _.is_file())} файлів → {OUT.relative_to(ROOT)}/README.md")


if __name__ == "__main__":
    main()

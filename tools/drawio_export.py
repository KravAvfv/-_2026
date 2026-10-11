#!/usr/bin/env python3
"""Export every ПІС lab diagram to a native draw.io file: labN/drawio/NN_<назва>.drawio (defence order).

    .venv/bin/python tools/drawio_export.py            # all labs
    .venv/bin/python tools/drawio_export.py 3 5        # selected labs
    .venv/bin/python tools/drawio_export.py --png      # + PNG previews via draw.io desktop (labN/drawio/preview/)

Each file is validated (well-formed XML, unique ids, every edge terminal / parent exists).
"""
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from drawio_lib import bpmn_to_drawio, mermaid_to_drawio, svg_to_drawio  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent

# lab → [(source stem in labN/diagrams, output name, draw.io page name)], in the order of the report figures
MANIFEST = {
    1: [("01_org_structure", "01_Структурна_схема_РЦПДО", "Структурна схема"),
        ("02_kp_workflow", "02_Послідовність_робіт_КП", "Роботи командного пункту"),
        ("03_goal_tree_overview", "03_Дерево_цілей_рівні_0_1", "Дерево цілей (огляд)"),
        ("04_goal_tree_branch_1", "04_Дерево_цілей_гілка_1", "Гілка 1"),
        ("05_goal_tree_branch_2", "05_Дерево_цілей_гілка_2", "Гілка 2"),
        ("06_goal_tree_branch_3", "06_Дерево_цілей_гілка_3", "Гілка 3"),
        ("07_goal_tree_branch_4", "07_Дерево_цілей_гілка_4", "Гілка 4"),
        ("08_goal_tree_branch_5", "08_Дерево_цілей_гілка_5", "Гілка 5"),
        ("09_wbs_overview", "09_WBS_рівні_1_2", "WBS (огляд)"),
        ("10_wbs_1_1_1_2", "10_WBS_1.1_1.2", "WBS 1.1–1.2"),
        ("11_wbs_1_3", "11_WBS_1.3", "WBS 1.3"),
        ("12_wbs_1_4", "12_WBS_1.4", "WBS 1.4"),
        ("13_wbs_1_5_1_6", "13_WBS_1.5_1.6", "WBS 1.5–1.6"),
        ("14_wbs_1_7", "14_WBS_1.7", "WBS 1.7"),
        ("15_wbs_1_8", "15_WBS_1.8", "WBS 1.8")],
    2: [("00_interaction_map", "01_Взаємодія_функцій_верхній_рівень", "Взаємодія функцій"),
        ("01_p1_monitoring", "02_Пул_P1_Моніторинг_обстановки", "P1 Моніторинг"),
        ("02_p2_assignment_a", "03_Пул_P2_Призначення_цілі_ч1", "P2 Призначення (ч. 1)"),
        ("03_p2_assignment_b", "04_Пул_P2_Призначення_цілі_ч2", "P2 Призначення (ч. 2)"),
        ("04_p3_mission_a", "05_Пул_P3_Виконання_місії_ч1", "P3 Місія (ч. 1)"),
        ("05_p3_mission_b", "06_Пул_P3_Виконання_місії_ч2", "P3 Місія (ч. 2)"),
        ("06_p4_assessment", "07_Пул_P4_Оцінка_та_звітність", "P4 Оцінка"),
        ("07_p5_readiness", "08_Пул_P5_Готовність_ресурсів", "P5 Готовність")],
    3: [("01_context", "01_Контекстна_діаграма_А-0", "A-0"),
        ("02_a0", "02_Декомпозиція_А0", "A0"),
        ("03_a1", "03_Декомпозиція_А1", "A1"),
        ("04_a2", "04_Декомпозиція_А2", "A2"),
        ("05_node_tree", "05_Дерево_вузлів", "Дерево вузлів"),
        ("06_feo_a3", "06_FEO_А3", "FEO A0F"),
        ("07_split_a0", "07_А0_після_розділення_моделі", "A0 після розділення"),
        ("08_split_model", "08_Контекстна_відокремленої_моделі", "Відокремлена модель"),
        ("09_idef3", "09_IDEF3_А3", "IDEF3"),
        ("10_scenario", "10_Сценарій_IDEF3", "Сценарій")],
    4: [("01_dfd_a4", "01_DFD_А4", "DFD A4"),
        ("02_dfd_a5", "02_DFD_А5", "DFD A5"),
        ("03_a0_abc", "03_А0_ABC", "A0 ABC")],
    5: [("01_usecase_combat", "01_Варіанти_використання_бойове_управління", "Use case (бойове управління)"),
        ("02_usecase_support", "02_Варіанти_використання_забезпечення", "Use case (забезпечення)"),
        ("03_activity_a", "03_Діяльність_ч1", "Діяльність (ч. 1)"),
        ("04_activity_b", "04_Діяльність_ч2", "Діяльність (ч. 2)"),
        ("05_sequence", "05_Послідовність_Призначити_розрахунок", "Послідовність"),
        ("06_class_a", "06_Класи_Ситуаційна_обізнаність", "Класи (обізнаність)"),
        ("07_class_b", "07_Класи_Місії_та_ресурси", "Класи (місії)")],
    7: [("01_architecture", "01_Архітектура_IoT_платформи", "Архітектура"),
        ("02_flows", "02_Інформаційні_потоки", "Інформаційні потоки")],
}


def convert(lab, stem, page):
    d = ROOT / f"lab{lab}" / "diagrams"
    if (d / f"{stem}.bpmn").exists():
        return bpmn_to_drawio(d / f"{stem}.bpmn", page)
    if (d / f"{stem}.mmd").exists():
        return mermaid_to_drawio(d / f"{stem}.mmd", d / f"{stem}.svg", page)
    return svg_to_drawio(d / f"{stem}.svg", page)


def validate(path):
    root = ET.parse(path).getroot()
    cells = root.findall(".//mxCell")
    ids = [c.get("id") for c in cells]
    assert len(ids) == len(set(ids)), "duplicate ids"
    known = set(ids)
    for c in cells:
        for k in ("parent", "source", "target"):
            v = c.get(k)
            assert v is None or v in known, f"{c.get('id')}: dangling {k}={v}"
        if c.get("vertex") == "1" or c.get("edge") == "1":
            assert c.find("mxGeometry") is not None, f"{c.get('id')}: no geometry"
    return sum(c.get("vertex") == "1" for c in cells), sum(c.get("edge") == "1" for c in cells)


def main(argv):
    png = "--png" in argv
    labs = [int(a) for a in argv if a.isdigit()] or list(MANIFEST)
    for lab in labs:
        out_dir = ROOT / f"lab{lab}" / "drawio"
        for stem, out, page in MANIFEST[lab]:
            dw = convert(lab, stem, page)
            path = dw.save(out_dir / f"{out}.drawio")
            v, e = validate(path)
            print(f"lab{lab}/drawio/{out}.drawio  vertices={v} edges={e}")
            if png:
                prev = out_dir / "preview"; prev.mkdir(exist_ok=True)
                subprocess.run(["drawio", "-x", "-f", "png", "-s", "2", "-b", "10", "-o", str(prev / f"{out}.png"),
                                str(path), "--no-sandbox"], capture_output=True, check=True, timeout=180)


if __name__ == "__main__":
    main(sys.argv[1:])

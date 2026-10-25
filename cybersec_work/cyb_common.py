"""Спільне для ЛР2–ЛР4 «Кібернетична безпека підприємства»: шляхи, бібліографія, побудова report.yaml.

Джерела, позначені «дата звернення: 25.10.2026», перевірено на первинних сторінках у день складання;
решта — нормативні документи та лекції курсу. ЛР1 має власний перелік у cybersec_work/lab1/make_lab1.py.
"""
import re
import sys
from pathlib import Path

import yaml

CYB = Path(__file__).resolve().parent
ROOT = CYB.parent
for p_ in (CYB / "lab1", ROOT / "tspp_work", ROOT / "tools"):
    sys.path.insert(0, str(p_))
from tspp_common import block_helpers, number_citations  # noqa: E402,F401  (generic report helpers only)
from uk_plural import n_uk  # noqa: E402,F401

COURSE_DIR = "Кібернетична безпека підприємств"
SUBJECT = "Кібернетична безпека підприємства"
NOTE_TCK = ("Примітка. ТЦК та СП, його підрозділи, інформаційна система й усі числові оцінки в роботі є умовною "
            "навчальною моделлю, побудованою лише на відкритих нормативних джерелах.")

LECT = "з дисципліни «Кібернетична безпека підприємства». Київ : КНУ імені Тараса Шевченка, 2026."
ACC = "(дата звернення: 25.10.2026)"
REF = {
    "manual": "Борисенко І. І., Гладка М. В. Кібернетична безпека підприємства : рекомендації до виконання "
              "лабораторних робіт для здобувачів освітнього ступеня «бакалавр» спеціальності 126 «Інформаційні "
              "системи та технології». Київ : КНУ імені Тараса Шевченка, 2025. 33 с.",
    "l1": "Кібернетична безпека підприємства: поняття, принципи та сучасні виклики : лекція 1 " + LECT,
    "l2": "Архітектура кібербезпеки підприємства та захист IoT-інфраструктури : лекція 2 " + LECT,
    "l3": "Кіберзагрози, вразливості та моделювання атак на підприємство : лекція 3 " + LECT,
    "l4": "Порушник у системі кібернетичної безпеки підприємства : лекція 4 " + LECT,
    "l5": "Організаційний та процедурний рівень кібернетичної безпеки підприємства : лекція 5 " + LECT,
    "nosok": "Управління інформаційною безпекою : конспект лекцій / уклад.: С. О. Носок, О. М. Фаль, В. М. Ткач. "
             "Київ : КПІ ім. Ігоря Сікорського, 2021. 258 с.",
    "iso27001": "ISO/IEC 27001:2022. Information security, cybersecurity and privacy protection — Information "
                "security management systems — Requirements. Geneva : ISO, 2022.",
    "iso27005": "ISO/IEC 27005:2022. Information security, cybersecurity and privacy protection — Guidance on "
                "managing information security risks. Geneva : ISO, 2022.",
    "iso31000": "ISO 31000:2018. Risk management — Guidelines. Geneva : ISO, 2018.",
    "sp80030": "Guide for Conducting Risk Assessments : NIST Special Publication 800-30 Revision 1. Gaithersburg : "
               "National Institute of Standards and Technology, 2012. 95 p.",
    "csf": "The NIST Cybersecurity Framework (CSF) 2.0 : NIST CSWP 29. Gaithersburg : National Institute of "
           "Standards and Technology, 2024. 32 p.",
    "cobit": "COBIT 5 for Risk. Rolling Meadows : ISACA, 2013.",
    "enisa": "Risk Management: Implementation principles and Inventories for Risk Management/Risk Assessment "
             "methods and tools. Heraklion : ENISA, 2006. URL: https://www.enisa.europa.eu/sites/default/files/"
             "publications/D1_Inventory_of_Methods_Risk_Management_Final.pdf " + ACC + ".",
    "yazar": "Yazar Z. A qualitative risk analysis and management tool — CRAMM : GSEC practical assignment. "
             "SANS Institute, 2002. URL: https://www.giac.org/paper/gsec/1746/qualitative-risk-analysis-"
             "management-tool-cramm/103133 " + ACC + ".",
    "octave": "Alberts C., Dorofee A. Managing Information Security Risks: The OCTAVE Approach. Boston : "
              "Addison-Wesley, 2002. 471 p.",
    "allegro": "Caralli R. A., Stevens J. F., Young L. R., Wilson W. R. Introducing OCTAVE Allegro: Improving the "
               "Information Security Risk Assessment Process : CMU/SEI-2007-TR-012. Pittsburgh : Software "
               "Engineering Institute, 2007. 154 p. URL: https://courses.cs.ttu.ee/w/images/a/a3/OCTAVE.pdf "
               + ACC + ".",
    "peltier": "Peltier T. R. Information Security Risk Analysis. 3rd ed. Boca Raton : CRC Press, 2010.",
    "iec60812": "IEC 60812:2018. Failure modes and effects analysis (FMEA and FMECA). 3rd ed. Geneva : IEC, 2018. "
                "URL: https://webstore.iec.ch/publication/26359 " + ACC + ".",
    "law2163": "Про основні засади забезпечення кібербезпеки України : Закон України від 05.10.2017 № 2163-VIII. "
               "URL: https://zakon.rada.gov.ua/laws/show/2163-19 " + ACC + ".",
    "law2297": "Про захист персональних даних : Закон України від 01.06.2010 № 2297-VI. "
               "URL: https://zakon.rada.gov.ua/laws/show/2297-17 " + ACC + ".",
    "law1951": "Про Єдиний державний реєстр призовників, військовозобов’язаних та резервістів : Закон України від "
               "16.03.2017 № 1951-VIII. URL: https://zakon.rada.gov.ua/laws/show/1951-19 " + ACC + ".",
    "kmu154": "Про затвердження Положення про територіальні центри комплектування та соціальної підтримки : "
              "постанова Кабінету Міністрів України від 23.02.2022 № 154. "
              "URL: https://zakon.rada.gov.ua/laws/show/154-2022-п " + ACC + ".",
    "nd37": "НД ТЗІ 3.7-003-05. Порядок проведення робіт із створення комплексної системи захисту інформації "
            "в інформаційно-телекомунікаційній системі. Київ : ДСТСЗІ СБ України, 2005.",
    "dstu3008": "ДСТУ 3008:2015. Інформація та документація. Звіти у сфері науки і техніки. Структура та правила "
                "оформлювання. Київ : ДП «УкрНДНЦ», 2016. 26 с.",
}


def qa_blocks(B, p, qa):
    for k, (q, a) in enumerate(qa, 1):
        B.append({"p": f"Питання {k}. {q}"})
        p(f"Відповідь. {a}")


def write_spec(here, n, title, B, required):
    B.append({"h1": "Список використаних джерел", "new_page": True})
    used = set(re.findall(r"@(\w+)", yaml.safe_dump(B, allow_unicode=True)))
    unknown = used - set(REF)
    if unknown:
        sys.exit(f"Unknown reference keys: {sorted(unknown)}")
    order = number_citations(B, [k for k in REF if k in used])   # кожне з джерел ЛР процитовано
    B.append({"refs": [REF[k] for k in order]})
    spec = {
        "lab_number": n, "work_label": "Лабораторна робота №",
        "template": f"{COURSE_DIR}/Титульна сторінка для лб.docx",
        "subject": SUBJECT, "theme": title, "year": 2026,
        "output": f"cybersec_work/lab{n}/ЛР{n}_Кравченко_ІР-31.docx",
        "required_sections": required + ["ВИСНОВКИ", "СПИСОК ВИКОРИСТАНИХ ДЖЕРЕЛ"],
        "blocks": B,
    }
    (here / "report.yaml").write_text(yaml.safe_dump(spec, allow_unicode=True, sort_keys=False, width=120),
                                      encoding="utf-8")
    print(f"report.yaml: {len(B)} blocks, {len(order)} sources")

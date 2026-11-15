#!/usr/bin/env python3
"""ЛР2 «Багатокритеріальний аналіз та експертне оцінювання у системному моделюванні об'єктів інформаційної
безпеки ТКС» — дисципліна «Теорія систем», варіант 8 «Розумна енергомережа (Smart Grid)».

Об'єкт — той самий, що в ЛР1 і ПР1: АСКОЕ багатоквартирного будинку (початковий стан) → мікромережа будинку
(еволюційний розвиток). Скрипт виконує етапи 1–2 методичних вказівок (експертні ваги критеріїв, матриця кореляцій)
і розрахунок ієрархічного адитивного ризику з прикладу вказівок. Числові вихідні дані (бали експертів,
імовірності, частки збитку) — умовна навчальна модель. Запуск:  python mcda_l2.py
"""
import numpy as np
import pandas as pd
from scipy import stats

# ======================================================================= Етап 1. Критерії та експертні ваги
CRITERIA = ["Надійність", "Захищеність", "Масштабованість", "Вартість/Ефективність"]
EXPERTS = ["Інженер-енергетик ОСББ", "Фахівець з кібербезпеки", "Представник ОСР"]
# Бали важливості критеріїв (1–10), ті самі експерти й оцінки, що в ПР1 (розділ 7)
expert_1 = [9, 8, 6, 7]
expert_2 = [7, 10, 7, 6]
expert_3 = [9, 8, 7, 5]
SCORES = np.array([expert_1, expert_2, expert_3]).T          # рядки — критерії, стовпці — експерти
MEAN = SCORES.mean(axis=1)
W = MEAN / MEAN.sum()                                         # нормалізовані вагові коефіцієнти, ΣW = 1

# Кореляція критеріїв за методикою вказівок: np.corrcoef по рядках «критерій × експерт» (n = 3 спостереження)
CORR_BRIEF = np.corrcoef(SCORES)

# ======================================================================= Етап 2. Альтернативи та кореляції
# Щоб коефіцієнти кореляції мали статистичний зміст, ті самі експерти оцінили 7 альтернатив (станів і варіантів
# архітектури) за 4 критеріями. Шкала 1–10, більший бал — краще (для C4 — дешевше / вигідніше).
ALTS = [
    ("A0", "Початковий стан: АСКОЕ без змін"),
    ("A1", "Мікромережа лише з вбудованим захистом протоколів"),
    ("A2", "A1 + базовий захист (сегментація, VPN, міжмережевий екран)"),
    ("A3", "A1 + комплексний захист (A2 + сертифікати пристроїв, підпис команд, SIEM)"),
    ("A4", "A1 + максимальний захист (A3 + цілодобовий SOC, резервний контролер)"),
    ("A5", "Локальне керування без хмари + базовий захист"),
    ("A6", "Хмарне керування без автономного режиму + комплексний захист"),
]
# ALT_SCORES[експерт][альтернатива] = [C1, C2, C3, C4]
ALT_SCORES = np.array([
    [[6, 4, 3, 8], [7, 3, 8, 8], [8, 6, 7, 7], [9, 8, 8, 6], [10, 9, 7, 3], [8, 6, 4, 7], [6, 7, 9, 6]],
    [[5, 3, 3, 9], [6, 2, 8, 9], [7, 6, 8, 7], [9, 9, 8, 5], [9, 10, 6, 2], [8, 7, 4, 6], [5, 8, 9, 6]],
    [[6, 4, 2, 8], [7, 3, 7, 8], [8, 5, 7, 7], [8, 8, 8, 6], [10, 9, 7, 3], [7, 6, 5, 7], [6, 7, 8, 5]],
], dtype=float)
ALT_MEAN = ALT_SCORES.mean(axis=0)                            # узгоджена (середня) матриця 7 × 4
CORR = np.corrcoef(ALT_MEAN.T)                                # Пірсон між критеріями по 7 альтернативах
N_ALT = len(ALTS)
_t = stats.t.ppf(0.975, N_ALT - 2)                          # критичне |r| (α = 0,05, двобічний)
R_CRIT = float(_t / np.sqrt(_t ** 2 + N_ALT - 2))
_t3 = stats.t.ppf(0.975, 1)
R_CRIT3 = float(_t3 / np.sqrt(_t3 ** 2 + 1))                  # для n = 3 (методика вказівок)
P_VAL = np.array([[stats.pearsonr(ALT_MEAN[:, i], ALT_MEAN[:, j])[1] if i != j else 0.0 for j in range(4)]
                  for i in range(4)])
SPEARMAN = stats.spearmanr(ALT_MEAN).statistic                 # ранговий контроль

# Адитивна згортка (метод зваженої суми) та стійкість до ваг
UTIL = ALT_MEAN @ W
UTIL_BY_EXPERT = ALT_SCORES @ W                               # 3 × 7
BEST = int(UTIL.argmax())


def pareto(M):
    """Індекси недомінованих альтернатив (усі критерії — «більше краще»)."""
    keep = []
    for i in range(len(M)):
        if not any(np.all(M[j] >= M[i]) and np.any(M[j] > M[i]) for j in range(len(M)) if j != i):
            keep.append(i)
    return keep


PARETO = pareto(ALT_MEAN)


def sensitivity(delta=0.2):
    """Переможець при зміні кожної ваги на ±delta (з повторною нормалізацією)."""
    out = []
    for j in range(4):
        for s in (-1, 1):
            w = W.copy(); w[j] *= 1 + s * delta; w /= w.sum()
            out.append((CRITERIA[j], s * delta, int((ALT_MEAN @ w).argmax())))
    return out


SENS = sensitivity()


def kendall(R):
    """Коефіцієнт конкордації Кендалла для матриці оцінок m експертів × n об'єктів (без зв'язків)."""
    m, n = R.shape
    ranks = np.vstack([stats.rankdata(-r) for r in R])
    s = float(((ranks.sum(axis=0) - m * (n + 1) / 2) ** 2).sum())
    w = 12 * s / (m ** 2 * (n ** 3 - n))
    return w, m * (n - 1) * w


W_KEND_ALT, CHI2_ALT = kendall(UTIL_BY_EXPERT)
CHI2_CRIT_ALT = float(stats.chi2.ppf(0.95, N_ALT - 1))

# ======================================================================= Ієрархічна адитивна згортка ризику
# Рівні декомпозиції ТКС: вага рівня W_l (бали 3 експертів 1–10 → нормалізація), елементи з вагою w (Σw = 1 у
# межах рівня) та ризиком r = p · c, де p — імовірність успішної атаки на елемент за рік, c — частка
# максимального збитку системи. R_sub = Σ w·r, R_sys = Σ W_l · R_sub.
LEVELS = ["1. Рівень збору даних і виконання", "2. Рівень комунікації та мережі",
          "3. Рівень хмарної обробки та застосунків"]
LEVEL_SCORES = np.array([[7, 8, 7], [8, 9, 9], [9, 8, 9]])    # рядки — рівні, стовпці — експерти
W_LEVEL = LEVEL_SCORES.mean(axis=1) / LEVEL_SCORES.mean(axis=1).sum()

# (назва, w, p, c)
STAGE0 = {   # початковий стан — АСКОЕ
    LEVELS[0]: [("Лічильники (75), DLMS/COSEM", 0.60, 0.30, 0.40), ("УЗПД", 0.40, 0.35, 0.60)],
    LEVELS[1]: [("Шина RS-485 без шифрування", 0.50, 0.50, 0.40), ("Канал LTE до ППКО (APN)", 0.30, 0.20, 0.50),
                ("Ethernet УЗПД — сервер (TCP)", 0.20, 0.40, 0.40)],
    LEVELS[2]: [("Сервер АСКОЕ (локальний)", 0.50, 0.30, 0.60), ("АРМ управителя (HTTP)", 0.30, 0.45, 0.40),
                ("Застосунок мешканця (HTTPS)", 0.20, 0.20, 0.30)],
}
STAGE1 = {   # еволюційний розвиток — мікромережа до впровадження СЗІБ (вхідні дані ЛР3)
    LEVELS[0]: [("Лічильники, DLMS/COSEM HLS", 0.20, 0.25, 0.40), ("Датчики середовища, Modbus RTU", 0.15, 0.50, 0.30),
                ("Інвертори й УЗЕ, Modbus TCP", 0.30, 0.55, 0.80), ("Контролер мікромережі", 0.35, 0.45, 0.90)],
    LEVELS[1]: [("Шлюз безпеки (межа сегментів)", 0.35, 0.50, 0.90), ("MQTT/TLS у VPN: оптика + LTE", 0.25, 0.30, 0.70),
                ("Технологічний Ethernet (Modbus TCP)", 0.25, 0.70, 0.80), ("Zigbee та OCPP (бездротові)", 0.15, 0.40, 0.50)],
    LEVELS[2]: [("Хмарна платформа і цифровий двійник", 0.40, 0.45, 0.90), ("API агрегатора (OpenADR)", 0.25, 0.40, 0.70),
                ("Застосунок і АРМ (HTTPS, OAuth 2.0)", 0.20, 0.50, 0.50), ("SIEM", 0.15, 0.30, 0.40)],
}


def hierarchy(stage):
    rows, total = [], 0.0
    for wl, (lvl, elems) in zip(W_LEVEL, stage.items()):
        assert abs(sum(e[1] for e in elems) - 1) < 1e-9, lvl
        r_sub = sum(w * p * c for _, w, p, c in elems)
        total += wl * r_sub
        rows.append(dict(level=lvl, W=wl, R_sub=r_sub, contrib=wl * r_sub,
                         elems=[(n, w, p, c, p * c) for n, w, p, c in elems]))
    for r in rows:
        r["share"] = r["contrib"] / total
    return rows, total


H0, R_SYS0 = hierarchy(STAGE0)
H1, R_SYS1 = hierarchy(STAGE1)

# ======================================================================= Самоперевірки моделі
assert abs(W.sum() - 1) < 1e-12 and abs(W_LEVEL.sum() - 1) < 1e-12
assert CORR[0, 1] > 0.5 and CORR[1, 3] < -0.5, "очікувані знаки зв'язків C1–C2 (+) і C2–C4 (−)"
assert BEST == 3 and BEST in PARETO and all(b == BEST for *_, b in SENS)
assert R_SYS1 > R_SYS0 and max(H1, key=lambda r: r["contrib"])["level"] == LEVELS[1]


def report():
    pd.set_option("display.width", 140)
    df = pd.DataFrame({"Критерій": CRITERIA, "Експерт 1": expert_1, "Експерт 2": expert_2, "Експерт 3": expert_3,
                       "Середній бал": MEAN.round(3), "Ваговий коефіцієнт": W.round(4)})
    print("--- РЕЗУЛЬТАТИ ЕКСПЕРТНОГО ОЦІНЮВАННЯ ---")
    print(df.to_string(index=False))
    print("\n--- МАТРИЦЯ КОРЕЛЯЦІЙ (методика вказівок, n = 3) ---")
    print(pd.DataFrame(CORR_BRIEF, index=CRITERIA, columns=CRITERIA).round(2).to_string())
    print(f"критичне |r| (α = 0,05; n = 3) = {R_CRIT3:.3f}")
    print("\n--- УЗГОДЖЕНІ ОЦІНКИ АЛЬТЕРНАТИВ І ЗВАЖЕНА СУМА ---")
    da = pd.DataFrame(ALT_MEAN.round(2), index=[a for a, _ in ALTS], columns=CRITERIA)
    da["U = Σ W·s"] = UTIL.round(3)
    print(da.to_string())
    print(f"найкраща альтернатива: {ALTS[BEST][0]}; Парето-множина: {[ALTS[i][0] for i in PARETO]}")
    print(f"конкордація експертів щодо альтернатив W = {W_KEND_ALT:.3f}, χ² = {CHI2_ALT:.2f} "
          f"(χ²крит = {CHI2_CRIT_ALT:.2f})")
    print("\n--- МАТРИЦЯ КОРЕЛЯЦІЙ КРИТЕРІЇВ (по 7 альтернативах) ---")
    print(pd.DataFrame(CORR, index=CRITERIA, columns=CRITERIA).round(2).to_string())
    print(f"критичне |r| (α = 0,05; n = {N_ALT}) = {R_CRIT:.3f}")
    for name, H, R in (("ПОЧАТКОВИЙ СТАН", H0, R_SYS0), ("ЕВОЛЮЦІЙНИЙ РОЗВИТОК (до СЗІБ)", H1, R_SYS1)):
        print("\n" + "=" * 75 + f"\n РОЗРАХУНОК РИЗИКІВ: {name}\n" + "=" * 75)
        for r in H:
            print(f"[{r['level']}] (вага рівня {r['W']:.4f})")
            for n, w, p, c, rr in r["elems"]:
                print(f"  - {n}: w = {w}, p = {p}, c = {c}, r = {rr:.3f}")
            print(f"  --> R_sub = {r['R_sub']:.4f}; внесок W·R_sub = {r['contrib']:.4f} ({r['share']:.1%})")
        print(f"ІНТЕГРОВАНИЙ РИЗИК R_sys = {R:.4f} ({R:.1%})")


if __name__ == "__main__":
    report()

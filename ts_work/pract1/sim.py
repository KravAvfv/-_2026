"""Імітаційне моделювання накопичення інцидентів безпеки мікромережі будинку (варіант 8, Smart Grid).

Адаптація лістингу інфографіки з методичних вказівок ПР1: ті самі кроки (генерація входів, два стани системи,
накопичення зломів, звіт, графік), параметри — для умовної моделі варіанта (sa_model.SIM).
Запуск окремо:  .venv/bin/python ts_work/pract1/sim.py   (друкує звіт і зберігає графік)
"""
from pathlib import Path

import numpy as np
import pandas as pd

SEED, HOURS = 8, 1000
P_ATTACK = 0.06          # імовірність атаки або аномалії за годину
P_BREACH0 = 0.70         # початковий стан: RS-485/Modbus без шифрування, пароль за замовчуванням
P_BREACH1 = 0.04         # стан розвитку: сегментація, MQTT поверх TLS, підпис команд, SIEM


def simulate(seed=SEED, hours=HOURS, p_attack=P_ATTACK, p0=P_BREACH0, p1=P_BREACH1):
    rng = np.random.default_rng(seed)
    # 1. Вхідні впливи: телеметрія (потужність будинку, кВт) і потік атак
    load_kw = rng.normal(loc=55, scale=12, size=hours)          # u1–u2: дані лічильників та інверторів
    attacks = rng.choice([0, 1], size=hours, p=[1 - p_attack, p_attack])   # u10–u13: загрози
    # 2. Два стани системи: однакові атаки, різна ймовірність успіху
    breach0 = np.where(attacks == 1, rng.choice([1, 0], size=hours, p=[p0, 1 - p0]), 0)
    breach1 = np.where(attacks == 1, rng.choice([1, 0], size=hours, p=[p1, 1 - p1]), 0)
    # 3. Динаміка накопичення
    df = pd.DataFrame({"Година": np.arange(1, hours + 1), "Навантаження, кВт": load_kw, "Атаки": attacks,
                       "Зломи (початковий)": breach0, "Зломи (розвиток)": breach1})
    df["Накопичені (початковий)"] = df["Зломи (початковий)"].cumsum()
    df["Накопичені (розвиток)"] = df["Зломи (розвиток)"].cumsum()
    a, b0, b1 = int(attacks.sum()), int(breach0.sum()), int(breach1.sum())
    return df, dict(attacks=a, b0=b0, b1=b1, r0=b0 / a, r1=b1 / a, eff=1 - b1 / b0)


def report(s):
    line = "=" * 60
    return "\n".join([line, "   ЗВІТ СИСТЕМНОГО АНАЛІЗУ БЕЗПЕКИ МІКРОМЕРЕЖІ БУДИНКУ", line,
                      f"Всього зафіксовано атак/аномалій:           {s['attacks']}",
                      f"Успішних зломів (початковий стан):          {s['b0']} (ризик {s['r0']:.1%})",
                      f"Успішних зломів (стан розвитку, СЗІБ):      {s['b1']} (ризик {s['r1']:.1%})",
                      f"Ефективність впровадження СЗІБ:             {s['eff']:.1%} зниження ризику", line])


def plot(df, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.family": "Times New Roman", "font.size": 12})
    fig, ax = plt.subplots(figsize=(6.3, 3.4), dpi=300)
    ax.plot(df["Година"], df["Накопичені (початковий)"], color="black", lw=1.6,
            label="Початковий стан (АСКОЕ без шифрування)")
    ax.plot(df["Година"], df["Накопичені (розвиток)"], color="black", lw=1.6, ls="--",
            label="Стан розвитку (мікромережа + СЗІБ)")
    ax.set_xlabel("Час, год")
    ax.set_ylabel("Кількість успішних атак")
    ax.grid(True, color="#BBBBBB", lw=0.6)
    ax.legend(loc="upper left", frameon=True)
    ax.set_xlim(0, len(df))
    ax.set_ylim(bottom=0)
    fig.tight_layout()
    fig.savefig(path, dpi=300)
    plt.close(fig)


if __name__ == "__main__":
    df, s = simulate()
    print(report(s))
    out = Path(__file__).resolve().parent / "diagrams" / "05_simulation.png"
    out.parent.mkdir(exist_ok=True)
    plot(df, out)
    print("→", out)

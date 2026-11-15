#!/usr/bin/env python3
"""ЛР3 «Оптимізаційне моделювання та розподіл ресурсів у задачах забезпечення інформаційної безпеки ТКС» —
дисципліна «Теорія систем», варіант 8 «Розумна енергомережа (Smart Grid)».

Вихідні дані — результати ЛР2 (mcda_l2.py): ваги рівнів W_i і ризики рівнів R_i0 мікромережі до впровадження
СЗІБ; бюджет — вартість обраного в ПР1 варіанта комплексного захисту. Ефект вкладень — спадна експонента
(закон спадної віддачі): R_i(x_i) = R_i0 · exp(−k_i · x_i), k_i = ln 2 / h_i, де h_i — «напівперіод» вкладень
(сума, що вдвічі знижує ризик рівня; експертна оцінка). Розв'язок — SLSQP (scipy.optimize) і для контролю —
аналітичні умови Каруша — Куна — Таккера. Числові вихідні дані — умовна навчальна модель. Запуск: python optim_l3.py
"""
import numpy as np
import scipy.optimize as opt

LEVELS = ["Рівень 1 (збір даних і виконання)", "Рівень 2 (комунікація та мережа)",
          "Рівень 3 (хмарна обробка та застосунки)"]
W = np.array([22, 26, 26]) / 74                 # ваги рівнів з ЛР2 (середні бали експертів 7,33; 8,67; 8,67)
R0 = np.array([0.31625, 0.38, 0.30])            # R_sub рівнів з ЛР2 (стан розвитку до СЗІБ)
H = np.array([60_000, 30_000, 45_000])          # напівперіод вкладень h_i, грн
K = np.log(2) / H                               # коефіцієнти ефективності k_i, 1/грн
X_MIN = np.array([15_000, 20_000, 15_000])      # мінімальні вимоги до захисту рівнів, грн
B_TOTAL = 150_000                               # загальний бюджет СЗІБ, грн (варіант «Б» з ПР1)
LOSS = 1_500_000                                # максимальний збиток системи, грн (ПР1)


def risk(x):
    """Цільова функція: інтегрований зважений ризик системи R_sys(x1, x2, x3)."""
    return float(np.sum(W * R0 * np.exp(-K * np.asarray(x))))


def grad(x):
    return -W * R0 * K * np.exp(-K * np.asarray(x))


def solve_slsqp(budget=B_TOTAL, x0=None):
    """SLSQP у тисячах гривень (масштабування: градієнт у гривнях ~1e-6 зупиняє метод на старті)."""
    s = 1000.0
    cons = ({"type": "eq", "fun": lambda y: np.sum(y) - budget / s, "jac": lambda y: np.ones(3)},)
    bounds = [(m / s, budget / s) for m in X_MIN]
    y0 = np.full(3, budget / 3 / s) if x0 is None else np.asarray(x0) / s
    res = opt.minimize(lambda y: risk(y * s), y0, jac=lambda y: grad(y * s) * s, method="SLSQP",
                       bounds=bounds, constraints=cons, options={"ftol": 1e-14, "maxiter": 500})
    assert res.success, res.message
    res.x = res.x * s
    return res


def solve_kkt(budget=B_TOTAL):
    """Аналітичний розв'язок: x_i = max(x_min,i, ln(W_i·R_i0·k_i / λ) / k_i), λ — з умови Σx_i = B (бісекція)."""
    a = W * R0 * K

    def x_of(lam):
        return np.maximum(X_MIN, np.log(a / lam) / K)

    lo, hi = 1e-15, a.max()
    for _ in range(200):
        mid = np.sqrt(lo * hi)
        lo, hi = (mid, hi) if x_of(mid).sum() > budget else (lo, mid)
    lam = np.sqrt(lo * hi)
    return x_of(lam), lam


RES = solve_slsqp()
X_OPT, R_OPT = RES.x, RES.fun
X_KKT, LAM = solve_kkt()
R_START = risk(np.zeros(3))                                          # без вкладень (= R_sys ЛР2)
X_EQ = np.full(3, B_TOTAL / 3)
R_EQ = risk(X_EQ)                                                    # рівномірний розподіл
X_PROP = B_TOTAL * W * R0 / np.sum(W * R0)                           # пропорційно внеску рівня в ризик
R_PROP = risk(X_PROP)
MARGINAL = W * R0 * K * np.exp(-K * X_OPT)                           # −∂R/∂x_i в оптимумі (≈ λ для внутрішніх)
LEVEL_RISK = R0 * np.exp(-K * X_OPT)                                 # залишковий ризик кожного рівня

# Перевірка глобальності: задача опукла (сума опуклих експонент, лінійні обмеження) — старт з різних точок
STARTS = [np.array(s, float) for s in ([15_000, 20_000, 115_000], [115_000, 20_000, 15_000],
                                       [15_000, 115_000, 20_000], [50_000, 50_000, 50_000])]
MULTI = [solve_slsqp(x0=s).x for s in STARTS]

# Чутливість до бюджету: R*(B) і двокритеріальна згортка «вкладення + очікувані втрати» Z(B) = B + L·R*(B)
BUDGETS = np.arange(50_000, 400_001, 10_000)
CURVE = [(b, *solve_kkt(b)) for b in BUDGETS]
R_CURVE = np.array([risk(x) for _, x, _ in CURVE])
Z_CURVE = BUDGETS + LOSS * R_CURVE
B_BEST = int(BUDGETS[Z_CURVE.argmin()])

# Обернена задача: мінімальний бюджет, за якого R_sys ≤ R_target
R_TARGET = 0.10


def min_budget(target=R_TARGET):
    lo, hi = X_MIN.sum(), 2_000_000
    for _ in range(100):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if risk(solve_kkt(mid)[0]) > target else (lo, mid)
    return hi


B_TARGET = min_budget()

# ======================================================================= самоперевірки
assert abs(X_OPT.sum() - B_TOTAL) < 1e-3 and np.all(X_OPT >= X_MIN - 1e-6)
assert np.allclose(X_OPT, X_KKT, atol=5.0), (X_OPT, X_KKT)
assert all(np.allclose(m, X_OPT, atol=5.0) for m in MULTI)
assert R_OPT < R_PROP < R_START and R_OPT < R_EQ
assert int(np.argmax(X_OPT)) == 1                                    # найбільша частка — мережевий рівень


def report():
    print("=" * 65 + "\n    РЕЗУЛЬТАТИ ОПТИМІЗАЦІЙНОГО МОДЕЛЮВАННЯ СЗІБ\n" + "=" * 65)
    print(f"Загальний виділений бюджет: {B_TOTAL} грн")
    print(f"Ризик без вкладень: {R_START:.4f} ({R_START:.1%})")
    print("Оптимальний розподіл інвестицій по рівнях системи (SLSQP):")
    for name, x, xk, r in zip(LEVELS, X_OPT, X_KKT, LEVEL_RISK):
        print(f" - {name}: {x:10.2f} грн (ККТ: {xk:10.2f}); залишковий ризик рівня {r:.4f}")
    print(f"Мінімальний досяжний залишковий ризик: {R_OPT:.4f} ({R_OPT:.1%}); λ = {LAM:.3e} 1/грн")
    print(f"Рівномірний розподіл: {R_EQ:.4f}; пропорційний внеску: {R_PROP:.4f}")
    print(f"Бюджет мінімуму Z(B) = B + L·R*(B): {B_BEST} грн; бюджет для R_sys ≤ {R_TARGET}: {B_TARGET:.0f} грн")
    print("=" * 65)


if __name__ == "__main__":
    report()

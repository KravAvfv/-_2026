#!/usr/bin/env python3
"""LaTeX subset → Office Math (OMML) — native, editable Word equations without external converters.

Supported: groups {…}; ^ and _ (also combined); \\frac/\\dfrac{a}{b}; \\sqrt{x}; \\left( … \\right) with any
delimiters ( [ \\{ | . ); \\text{…}/\\mathrm{…} (upright text, Cyrillic indices such as W_{\\text{роз}});
functions \\sin \\cos \\lg \\ln \\arctg \\exp \\lim \\det \\min \\max \\operatorname{…} (upright);
\\lim_{p\\to 0} as a lower limit; \\begin{vmatrix}/\\begin{matrix}/\\begin{cases} … \\end{…} with & and \\\\;
greek letters, \\cdot \\times \\to \\approx \\le \\ge \\ne \\pm \\infty \\Rightarrow \\circ, spaces \\, \\; \\quad \\qquad.
Decimal numbers with a comma (0,02) are kept as one upright run so Word adds no list spacing after the comma.

    from omml import latex_to_omml
    el = latex_to_omml(r"W(p)=\\frac{p+1}{p(5p+1)}", size=14)   # → lxml <m:oMath>
"""
import re

from docx.oxml import parse_xml

M = "http://schemas.openxmlformats.org/officeDocument/2006/math"
W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS = f'xmlns:m="{M}" xmlns:w="{W}"'

SYMBOLS = {
    "alpha": "α", "beta": "β", "gamma": "γ", "delta": "δ", "Delta": "Δ", "epsilon": "ε", "zeta": "ζ",
    "eta": "η", "theta": "θ", "lambda": "λ", "mu": "μ", "nu": "ν", "xi": "ξ", "pi": "π", "rho": "ρ",
    "sigma": "σ", "tau": "τ", "varphi": "φ", "phi": "φ", "Phi": "Φ", "psi": "ψ", "omega": "ω", "Omega": "Ω",
    "cdot": "·", "times": "×", "to": "→", "rightarrow": "→", "Rightarrow": "⇒", "approx": "≈", "le": "≤",
    "leq": "≤", "ge": "≥", "geq": "≥", "ne": "≠", "neq": "≠", "pm": "±", "mp": "∓", "infty": "∞", "circ": "°",
    "cdots": "⋯", "ldots": "…", "dots": "…", "partial": "∂", "in": "∈", "equiv": "≡", "sim": "∼",
    "gg": "≫", "ll": "≪", "angle": "∠", "deg": "°", "ast": "∗", "prime": "′", "checkmark": "✓",
    ",": " ", ";": " ", ":": " ", " ": " ", "quad": " ", "qquad": "  ", "!": "",
    "{": "{", "}": "}", "|": "‖", "%": "%",
    "chi": "χ", "langle": "⟨", "rangle": "⟩", "cup": "∪", "cap": "∩", "parallel": "∥", "Gamma": "Γ", "Sigma": "Σ",
    "bigl": "", "bigr": "", "Bigl": "", "Bigr": "",
}
FUNCS = {"sin", "cos", "tg", "ctg", "arctg", "arcctg", "lg", "ln", "log", "exp", "lim", "det", "min", "max",
         "Re", "Im", "arg", "mod", "sign"}
TOKEN = re.compile(r"\\[A-Za-z]+|\\.|\d+(?:,\d+)?|\s+|.", re.S)


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


class Parser:
    def __init__(self, src, size):
        self.toks = [t for t in TOKEN.findall(src)]
        self.i = 0
        self.size = size

    # ---- low level
    def peek(self):
        while self.i < len(self.toks) and self.toks[self.i].isspace():
            self.i += 1
        return self.toks[self.i] if self.i < len(self.toks) else None

    def take(self):
        t = self.peek()
        self.i += 1
        self.prev, self.last = getattr(self, "last", None), t
        return t

    def run(self, text, upright=False, normal=False):
        if text == "":
            return ""
        sz = self.size * 2
        mpr = "<m:rPr><m:nor/></m:rPr>" if normal else ("<m:rPr><m:sty m:val=\"p\"/></m:rPr>" if upright else "")
        font = "Cambria Math"
        wpr = (f'<w:rPr><w:rFonts w:ascii="{font}" w:hAnsi="{font}" w:cs="{font}"/>'
               f'<w:sz w:val="{sz}"/><w:szCs w:val="{sz}"/></w:rPr>')
        return f'<m:r>{mpr}{wpr}<m:t xml:space="preserve">{esc(text)}</m:t></m:r>'

    def raw_group(self):
        """Text of a {…} group verbatim (for \\text, \\begin)."""
        assert self.take() == "{", "expected {"
        depth, out = 1, []
        while True:
            t = self.toks[self.i]; self.i += 1
            if t == "{":
                depth += 1
            elif t == "}":
                depth -= 1
                if depth == 0:
                    return "".join(out)
            out.append(t)

    # ---- grammar
    def expr(self, stop=("}",)):
        out = []
        while True:
            t = self.peek()
            if t is None or t in stop:
                return "".join(out)
            out.append(self.atom_with_scripts())

    def group_or_atom(self):
        if self.peek() == "{":
            self.take()
            body = self.expr()
            self.take()
            return body
        return self.atom()

    def atom_with_scripts(self):
        if self.peek() in ("\\int", "\\sum", "\\prod"):
            chr_ = {"\\int": "∫", "\\sum": "∑", "\\prod": "∏"}[self.take()]
            sub = sup = ""
            while self.peek() in ("^", "_"):
                op = self.take()
                arg = self.group_or_atom()
                if op == "^":
                    sup = arg
                else:
                    sub = arg
            body = self.expr(stop=("}", "=", ",", ".", "\\right", "\\qquad", "\\quad", "&", "\\\\"))
            hide = ('<m:subHide m:val="1"/>' if not sub else "") + ('<m:supHide m:val="1"/>' if not sup else "")
            return (f'<m:nary><m:naryPr><m:chr m:val="{chr_}"/><m:limLoc m:val="'
                    f'{"undOvr" if chr_ != "∫" else "subSup"}"/>{hide}</m:naryPr>'
                    f"<m:sub>{sub}</m:sub><m:sup>{sup}</m:sup><m:e>{body}</m:e></m:nary>")
        base = self.atom()
        sub = sup = None
        while self.peek() in ("^", "_"):
            op = self.take()
            arg = self.group_or_atom()
            if op == "^":
                sup = arg
            else:
                sub = arg
        if base.startswith("<!--lim-->"):
            body = base[len("<!--lim-->"):]
            if sub is not None:
                return (f"<m:limLow><m:e>{body}</m:e><m:lim>{sub}</m:lim></m:limLow>")
            return body
        if sub is not None and sup is not None:
            return f"<m:sSubSup><m:e>{base}</m:e><m:sub>{sub}</m:sub><m:sup>{sup}</m:sup></m:sSubSup>"
        if sub is not None:
            return f"<m:sSub><m:e>{base}</m:e><m:sub>{sub}</m:sub></m:sSub>"
        if sup is not None:
            return f"<m:sSup><m:e>{base}</m:e><m:sup>{sup}</m:sup></m:sSup>"
        return base

    def delim(self, tok):
        return {"\\{": "{", "\\}": "}", ".": "", "\\|": "‖", "\\langle": "⟨", "\\rangle": "⟩"}.get(tok, tok)

    def atom(self):
        t = self.take()
        if t is None:
            return ""
        if t == "{":
            body = self.expr()
            self.take()
            return body
        if re.fullmatch(r"\d+(?:,\d+)?", t):
            return self.run(t, normal="," in t, upright=True)
        if t == "-":
            # unary minus (start of a group or after an operator) → U+2212 without operator spacing
            if self.prev in (None, "{", "=", "+", "-", "(", "[", ",", ";", ":", "&", "\\\\", "^", "_",
                             "\\Rightarrow", "\\to", "\\approx", "\\le", "\\ge", "\\pm", "\\cdot",
                             "\\quad", "\\qquad", "\\left", "\\,", "\\;", "\\ ", "<", ">", "\\ne"):
                return self.run("−", upright=True)
            return self.run("-")
        if t == "'":
            return self.run("′", upright=True)
        if t == "*":
            return self.run("∗", upright=True)
        if t in "+=<>":
            return self.run(t)
        if t in "()[]|/!.,;:°":
            return self.run(t, upright=True)
        if not t.startswith("\\"):
            # Latin letters italic; Cyrillic / other symbols upright
            return self.run(t, upright=not re.fullmatch(r"[A-Za-z]", t))
        cmd = t[1:]
        if cmd in ("frac", "dfrac", "tfrac"):
            a = self.group_or_atom(); b = self.group_or_atom()
            typ = '<m:fPr><m:type m:val="lin"/></m:fPr>' if cmd == "tfrac" else ""
            return f"<m:f>{typ}<m:num>{a}</m:num><m:den>{b}</m:den></m:f>"
        if cmd == "sqrt":
            a = self.group_or_atom()
            return f'<m:rad><m:radPr><m:degHide m:val="1"/></m:radPr><m:deg/><m:e>{a}</m:e></m:rad>'
        if cmd in ("text", "mathrm", "textrm", "operatorname"):
            return self.run(self.raw_group(), upright=True)
        if cmd == "left":
            beg = self.delim(self.take())
            body = self.expr(stop=("\\right",))
            self.take()
            end = self.delim(self.take())
            return (f'<m:d><m:dPr><m:begChr m:val="{esc(beg)}"/><m:endChr m:val="{esc(end)}"/></m:dPr>'
                    f"<m:e>{body}</m:e></m:d>")
        if cmd == "begin":
            env = self.raw_group()
            rows, cur, cell_toks = [], [], []
            depth = 0
            while True:
                tok = self.toks[self.i]
                if tok == "\\end" and depth == 0:
                    self.i += 1
                    self.raw_group()
                    break
                self.i += 1
                if tok == "{":
                    depth += 1
                elif tok == "}":
                    depth -= 1
                if depth == 0 and tok == "&":
                    cur.append(cell_toks); cell_toks = []
                elif depth == 0 and tok == "\\\\":
                    cur.append(cell_toks); rows.append(cur); cur, cell_toks = [], []
                else:
                    cell_toks.append(tok)
            if cell_toks or cur:
                cur.append(cell_toks); rows.append(cur)
            sub = lambda toks: Parser("".join(toks), self.size).expr(stop=())
            if env == "cases":
                body = "".join(f"<m:e>{sub(sum(r, []))}</m:e>" for r in rows)
                return (f'<m:d><m:dPr><m:begChr m:val="{{"/><m:endChr m:val=""/></m:dPr>'
                        f'<m:e><m:eqArr>{body}</m:eqArr></m:e></m:d>')
            ncol = max(len(r) for r in rows)
            mpr = (f'<m:mPr><m:mcs><m:mc><m:mcPr><m:count m:val="{ncol}"/><m:mcJc m:val="center"/></m:mcPr>'
                   f'</m:mc></m:mcs><m:cGp m:val="4"/></m:mPr>')
            mat = "<m:m>" + mpr + "".join(
                "<m:mr>" + "".join(f"<m:e>{sub(c)}</m:e>" for c in r + [[]] * (ncol - len(r))) + "</m:mr>"
                for r in rows) + "</m:m>"
            bc = {"vmatrix": ("|", "|"), "pmatrix": ("(", ")"), "bmatrix": ("[", "]")}.get(env)
            if bc:
                return (f'<m:d><m:dPr><m:begChr m:val="{bc[0]}"/><m:endChr m:val="{bc[1]}"/></m:dPr>'
                        f"<m:e>{mat}</m:e></m:d>")
            return mat
        if cmd in FUNCS:
            r = self.run(cmd, upright=True)
            if cmd == "lim":
                return "<!--lim-->" + r
            return r + self.run(" ", upright=True) if cmd not in ("Re", "Im") else r
        if cmd in SYMBOLS:
            return self.run(SYMBOLS[cmd], upright=True)
        raise ValueError(f"omml: unsupported command \\{cmd}")


def latex_to_omml_xml(src, size=14):
    body = Parser(src, size).expr(stop=())
    return f"<m:oMath {NS}>{body}</m:oMath>"


def latex_to_omml(src, size=14):
    return parse_xml(latex_to_omml_xml(src, size))


def omml_para_xml(src, size=14, jc="center"):
    body = Parser(src, size).expr(stop=())
    return (f'<m:oMathPara {NS}><m:oMathParaPr><m:jc m:val="{jc}"/></m:oMathParaPr>'
            f"<m:oMath>{body}</m:oMath></m:oMathPara>")


if __name__ == "__main__":
    import sys
    print(latex_to_omml_xml(sys.argv[1] if len(sys.argv) > 1 else r"W(p)=\frac{p+1}{p(5p+1)}"))

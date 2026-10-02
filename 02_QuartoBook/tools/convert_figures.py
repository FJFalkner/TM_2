"""Konvertiert Inkscape-Abbildungen (SVG + LaTeX-Beschriftung) des LaTeX-Skripts in Web-SVGs.

Die Beschriftungen der Inkscape-SVGs enthalten LaTeX (z.B. $\\sigma$) und werden im Skript
über die extrahierten Dateien InkScape/ext/<name>_svg-tex.pdf(_tex) gesetzt. Dieses Skript
setzt jede Abbildung einzeln mit pdflatex (standalone) und wandelt das PDF mit pdftocairo
in ein SVG mit Glyphen als Pfade um.

Aufruf:
    python tools/convert_figures.py Abschleppstange Normalspannungen ...
    python tools/convert_figures.py --tikz axialForceRatio     (vorhandenes TikZ-PDF)
    python tools/convert_figures.py --all                       (alle ext/*.pdf_tex)
"""
import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT.parent / "01_LectureNotes"
EXT = SRC / "InkScape" / "ext"
LABELS = EXT              # Verzeichnis der .pdf_tex (Beschriftungen); für EN: ext-en
TIKZ = SRC / "tikz"
OUT = ROOT / "images"     # Ausgabeordner; für EN: images-en
BUILD = ROOT / "tools" / "_build"

PREAMBLE = r"""\documentclass[12pt,border=2pt]{standalone}
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage[ngerman]{babel}
\usepackage{xcolor,graphicx,transparent,tikz}
\usepackage{amsmath,mathtools,relsize,cancel,pifont,units}
\usepackage[minionint,openg,mathlf]{MinionPro}
\definecolor{myBlue}{RGB}{0,73,131}
\definecolor{myOrange}{RGB}{244,155,0}
\definecolor{myGreen}{RGB}{128,128,0}
\definecolor{myRed}{RGB}{170,0,0}
\definecolor{blueLink}{RGB}{0,73,131}
\colorlet{lightBlue}{myBlue!50}
\newcommand{\bs}[1]{\boldsymbol{#1}}
\newcommand{\pa}{\partial}
\newcommand{\vp}{\varphi}
\newcommand{\ve}{\varepsilon}
\newcommand{\dtp}{\dot{\varphi}}
\newcommand{\ddtp}{\ddot{\varphi}}
\newcommand{\myfrac}[2]{\frac{\displaystyle #1}{\displaystyle #2}}
\newcommand{\ol}[1]{\overline{#1}}
\newcommand*\circled[1]{\tikz[baseline=(char.base)]{\node[shape=circle,draw,inner sep=1.8pt] (char) {#1};}}
\newcommand{\cmark}{\ding{51}}
\newcommand{\xmark}{\ding{55}}
\newcommand{\bm}[1]{{\color{myBlue}{#1}}}
\newcommand{\bo}[1]{{\color{myOrange}{#1}}}
\newcommand*{\myprime}{^{\prime}\mkern-1.2mu}
\newcommand*{\mydprime}{^{\prime\prime}\mkern-1.2mu}
\graphicspath{{%s/}}
\begin{document}
\input{%s}
\end{document}
"""


def run(cmd, cwd):
    res = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, errors="replace")
    if res.returncode != 0:
        raise RuntimeError(f"{' '.join(cmd)} fehlgeschlagen:\n{res.stdout[-2000:]}\n{res.stderr[-2000:]}")


def pdf_to_svg(pdf: Path, name: str):
    OUT.mkdir(parents=True, exist_ok=True)
    run(["pdftocairo", "-svg", str(pdf), str(OUT / f"{name}.svg")], cwd=BUILD)


def pdf_page_count(pdf: Path) -> int:
    res = subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True, errors="replace")
    m = re.search(r"^Pages:\s+(\d+)", res.stdout, re.M)
    return int(m.group(1)) if m else 10**6


def sanitize_pdf_tex(name: str, graphics_dir: Path, pdf_tex: Path) -> Path:
    """Entfernt \\includegraphics-Aufrufe auf Seiten, die im PDF fehlen (Inkscape-Fehler:
    die .pdf_tex verweist teils auf eine leere letzte Seite, die nicht exportiert wurde)."""
    pages = pdf_page_count(graphics_dir / f"{name}_svg-tex.pdf")
    lines = pdf_tex.read_text(encoding="utf-8", errors="replace").splitlines()
    keep = [l for l in lines
            if not ((m := re.search(r"page=(\d+)", l)) and "includegraphics" in l and int(m.group(1)) > pages)]
    out = BUILD / f"{name}_clean.pdf_tex"
    out.write_text("\n".join(keep) + "\n", encoding="utf-8")
    return out


def compile_pdf_tex(name: str, graphics_dir: Path, pdf_tex: Path):
    BUILD.mkdir(parents=True, exist_ok=True)
    pdf_tex = sanitize_pdf_tex(name, graphics_dir, pdf_tex)
    tex = BUILD / f"{name}.tex"
    tex.write_text(PREAMBLE % (graphics_dir.as_posix(), pdf_tex.as_posix()), encoding="utf-8")
    run(["pdflatex", "-interaction=nonstopmode", "-halt-on-error", tex.name], cwd=BUILD)
    pdf_to_svg(BUILD / f"{name}.pdf", name)


def export_with_inkscape(name: str) -> Path:
    """Exportiert PDF + pdf_tex frisch aus InkScape/<name>.svg (falls ext/ veraltet ist)."""
    svg = SRC / "InkScape" / f"{name}.svg"
    if not svg.exists():
        raise FileNotFoundError(svg)
    fresh = BUILD / "inkscape"
    fresh.mkdir(parents=True, exist_ok=True)
    pdf = fresh / f"{name}_svg-tex.pdf"
    run(["inkscape", str(svg), "--export-type=pdf", "--export-latex",
         f"--export-filename={pdf}"], cwd=fresh)
    return fresh


def convert_inkscape(name: str):
    pdf_tex = LABELS / f"{name}_svg-tex.pdf_tex"   # Beschriftungen (DE: ext, EN: ext-en)
    try:
        if not pdf_tex.exists():
            raise FileNotFoundError(pdf_tex)
        compile_pdf_tex(name, EXT, pdf_tex)        # Zeichnung (PDF) immer aus ext
    except (RuntimeError, FileNotFoundError):
        # ext/ fehlt oder passt nicht mehr zum SVG -> frisch aus Inkscape exportieren
        fresh = export_with_inkscape(name)
        compile_pdf_tex(name, fresh, fresh / f"{name}_svg-tex.pdf_tex")


def convert_tikz(name: str):
    pdf = TIKZ / f"{name}.pdf"
    if not pdf.exists():
        raise FileNotFoundError(pdf)
    BUILD.mkdir(parents=True, exist_ok=True)
    pdf_to_svg(pdf, name)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("names", nargs="*")
    ap.add_argument("--tikz", nargs="*", default=[])
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--keep", action="store_true", help="Build-Ordner behalten")
    ap.add_argument("--labels-dir", help="Verzeichnis der .pdf_tex (z.B. ext-en für Englisch)")
    ap.add_argument("--out-dir", help="Ausgabeordner (z.B. images-en für Englisch)")
    args = ap.parse_args()

    global LABELS, OUT
    if args.labels_dir:
        LABELS = Path(args.labels_dir)
    if args.out_dir:
        OUT = Path(args.out_dir)

    names = list(args.names)
    if args.all:
        names = sorted(p.name[: -len("_svg-tex.pdf_tex")] for p in EXT.glob("*_svg-tex.pdf_tex"))

    failed = []
    for n in names:
        try:
            convert_inkscape(n)
            print(f"ok     {n}")
        except Exception as e:  # noqa: BLE001
            failed.append(n)
            print(f"FEHLER {n}: {e}", file=sys.stderr)
    for n in args.tikz:
        try:
            convert_tikz(n)
            print(f"ok     {n} (tikz)")
        except Exception as e:  # noqa: BLE001
            failed.append(n)
            print(f"FEHLER {n}: {e}", file=sys.stderr)

    if not args.keep and BUILD.exists():
        shutil.rmtree(BUILD, ignore_errors=True)
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()

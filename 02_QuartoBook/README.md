# TM2 – Quarto Book

Web-Version der Vorlesungsunterlagen aus `../01_LectureNotes` (LaTeX).

## Vorschau / Rendern

```sh
quarto preview      # Live-Vorschau im Browser
quarto render       # Ausgabe nach _book/
```

## Aufbau

- `_quarto.yml` – Buchstruktur (Kapitel), Querverweis-Präfixe, Theme
- `_macros.qmd` – LaTeX-Makros aus `header_FJ.tex` für MathJax; wird in jedes Kapitel eingebunden
- `styles.css` – Farben (myBlue, myOrange) und Beispiel-Layout
- `images/` – aus den Inkscape-Abbildungen erzeugte SVGs
- `tools/convert_figures.py` – setzt Inkscape-Abbildungen samt LaTeX-Beschriftung mit pdflatex
  (MinionPro) und konvertiert sie mit `pdftocairo` nach SVG

## Abbildungen für ein neues Kapitel erzeugen

```sh
python tools/convert_figures.py Name1 Name2 ...      # InkScape/ext/<Name>_svg-tex.pdf_tex
python tools/convert_figures.py --tikz axialForceRatio   # vorhandenes tikz/<Name>.pdf
python tools/convert_figures.py --all                # alle Inkscape-Abbildungen
```

## Umsetzung LaTeX → Quarto

| LaTeX                              | Quarto                                   |
|------------------------------------|------------------------------------------|
| `\label{fig:..}` / `Abb.~\ref{}`   | `{#fig-..}` / `@fig-..`                  |
| `\label{eq:..}` / `\eqref{}`       | `$$ … $$ {#eq-..}` / `([-@eq-..])`       |
| `example`-Umgebung                 | `::: {#exm-..}` (→ „Beispiel 1.x“)       |
| `empheq` mit `\myBox`              | `\myBox{…}` (MathJax `\bbox`)            |
| `\textsc{Hooke}`                   | `[Hooke]{.smallcaps}`                    |
| `\footnote{}`                      | `^[…]`                                   |

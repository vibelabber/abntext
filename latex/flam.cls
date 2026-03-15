% flam.cls — FLAM custom document class
% Inherits from abntex2 and applies FLAM institutional styles.
%
% Styles derived from:
%   hi2_entrega_03.tex — Gabriel Cardoso dos Santos Faleiro / FLAM

\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{flam}[2026/03/15 v0.1 FLAM class based on abntex2]

% Pass all options through to abntex2 (e.g. article, 12pt, a4paper, brazil).
\DeclareOption*{\PassOptionsToClass{\CurrentOption}{abntex2}}
\ProcessOptions\relax

\LoadClass{abntex2}

% ── FLAM CUSTOM STYLES ────────────────────────────────────────────────────────

% Margins: 3cm left/top, 2cm right/bottom (ABNT NBR 14724)
\setlrmarginsandblock{3cm}{2cm}{*}
\setulmarginsandblock{3cm}{2cm}{*}
\checkandfixthelayout

% Paragraph formatting
\setlength{\parindent}{1.25cm}
\setlength{\parskip}{0.5cm}
\setlength\afterchapskip{\lineskip}

% Chapter and section heading fonts
\renewcommand{\ABNTEXchapterfont}{\normalfont}
\renewcommand{\ABNTEXsectionfontsize}{\large\bfseries}
\renewcommand{\cftsectionfont}{\bfseries\MakeTextUppercase}
\renewcommand{\ABNTEXsubsectionfontsize}{\normalsize}
\renewcommand{\cftsubsectionfont}{\normalfont\MakeTextUppercase}
\renewcommand{\ABNTEXsubsubsectionfontsize}{\normalsize\bfseries}
\renewcommand{\cftsubsubsectionfont}{\bfseries}

% Custom cover page: institution → author → title → city → year
\renewcommand{\imprimircapa}{%
  \begin{capa}%
    \centering
    \ABNTEXchapterfont\large\imprimirinstituicao

    \ABNTEXchapterfont\large\imprimirautor

    \vfill
    \begin{center}
      \ABNTEXchapterfont\bfseries\large\imprimirtitulo
    \end{center}
    \vfill

    \large\imprimirlocal

    \large\imprimirdata

    \vspace*{1cm}
  \end{capa}
}

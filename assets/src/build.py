"""Build the animated profile SVGs (hero.svg, agents.svg) for github.com/th3r-dev.

Run: ~/.venvs/diagram-design/bin/python build.py <out_dir>
Palette: black + yellow. Font: JetBrains Mono (OFL), subset and embedded.
"""
import base64, io, math, sys
from html import escape
from fontTools import subset
from fontTools.ttLib import TTFont

OUT = sys.argv[1]
HERE = __file__.rsplit("/", 1)[0]

# tokens
BG, BAR, LINE, LINE2 = "#0A0A0A", "#141414", "#262626", "#3A3A3A"
Y, Y2, Y3 = "#FFD60A", "#C9A800", "#7A6600"      # yellow, dim, deep
TX, TX2, TX3 = "#F2F2F2", "#B8B8B8", "#7A7A7A"   # text, body, muted
CW = 0.6  # JetBrains Mono advance, em


def font_css(text):
    css = []
    for w in (500, 800):
        f = TTFont(f"{HERE}/fonts/jbm-{w}.woff2")
        s = subset.Subsetter()
        s.populate(text=text + " ")
        s.subset(f)
        f.flavor = "woff2"
        b = io.BytesIO()
        f.save(b)
        data = base64.b64encode(b.getvalue()).decode()
        css.append(f"@font-face{{font-family:J;font-weight:{w};src:url(data:font/woff2;base64,{data}) format('woff2')}}")
    return "".join(css)


def t(x, y, s, size=13, fill=TX2, w=500, cls="", anchor=None):
    a = f' text-anchor="{anchor}"' if anchor else ""
    c = f' class="{cls}"' if cls else ""
    wt = ' font-weight="800"' if w == 800 else ""
    return f'<text x="{x}" y="{y}" font-size="{size}" fill="{fill}"{wt}{a}{c}>{escape(s)}</text>'


def typed(x, y, s, size, start, dur, fill=TX):
    """Text revealed left to right by a background cover that steps away."""
    n = len(s)
    wpx = n * size * CW + 2
    return (t(x, y, s, size, fill)
            + f'<rect x="{x}" y="{y - size}" width="{wpx:.1f}" height="{size + 5}" fill="{BG}" '
              f'style="transform-origin:{x + wpx:.1f}px 0;animation:ty {dur}s steps({n}) {start}s both"/>')


def check(x, y, fill=Y):
    return f'<path d="M{x} {y}l3 3 6-7" fill="none" stroke="{fill}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>'


def diamond(x, y, r=3.2, fill=Y):
    return f'<path d="M{x} {y - r}l{r} {r}-{r} {r}-{r}-{r}z" fill="{fill}"/>'


def window(w, h, title):
    return (f'<rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" rx="14" fill="{BG}" stroke="{LINE}"/>'
            f'<path d="M0.5 14.5a14 14 0 0 1 14-14h{w - 29}a14 14 0 0 1 14 14v19h-{w - 1}z" fill="{BAR}"/>'
            f'<path d="M0.5 33.5h{w - 1}" stroke="{LINE}"/>'
            f'<circle cx="22" cy="17" r="5.5" fill="{Y}"/><circle cx="40" cy="17" r="5.5" fill="{LINE2}"/>'
            f'<circle cx="58" cy="17" r="5.5" fill="{LINE2}"/>'
            + t(w / 2, 21.5, title, 12, TX3, anchor="middle"))


BASE_CSS = (
    "text{font-family:J,ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;white-space:pre}"
    "@keyframes ty{from{transform:scaleX(1)}to{transform:scaleX(0)}}"
    "@keyframes in{from{opacity:0;transform:translateY(4px)}to{opacity:1;transform:none}}"
    "@keyframes bl{50%{opacity:0}}"
    "@keyframes dr{from{stroke-dashoffset:1}to{stroke-dashoffset:0}}"
    ".bl{animation:bl 1.05s steps(1) infinite}"
    ".dr{stroke-dasharray:1;animation:dr .7s cubic-bezier(.65,0,.35,1) both}"
)
RM_CSS = "@media (prefers-reduced-motion:reduce){*{animation:none!important}.f{opacity:0}.f0{opacity:1}}"


def appear(delay, inner, dur=0.45):
    return f'<g style="animation:in {dur}s cubic-bezier(.2,.7,.2,1) {delay:.2f}s both">{inner}</g>'


# ---------------------------------------------------------------- ASCII stack
RAMP = " .,:;=+*%#@"


def render_stack(angle, cols=44, rows=22):
    """Four stacked slabs (interface, services, data, platform), ray-cast to ASCII."""
    tilt = -math.radians(26)
    slabs = [(-1.2 + i * 0.72, -1.2 + i * 0.72 + 0.26) for i in range(4)]
    half = 0.8
    light = (-0.6, 0.3, -0.75)
    ln = math.sqrt(sum(c * c for c in light))
    light = tuple(c / ln for c in light)
    ca, sa, ct, st = math.cos(angle), math.sin(angle), math.cos(tilt), math.sin(tilt)

    def to_obj(v):  # camera -> object: undo tilt (x axis), then yaw (y axis)
        x, y, z = v
        y, z = y * ct + z * st, -y * st + z * ct
        x, z = x * ca - z * sa, x * sa + z * ca
        return x, y, z

    def to_cam(v):
        x, y, z = v
        x, z = x * ca + z * sa, -x * sa + z * ca
        y, z = y * ct - z * st, y * st + z * ct
        return x, y, z

    d = to_obj((0, 0, 1))
    out = []
    for r in range(rows):
        row = []
        for c in range(cols):
            sx = (c - cols / 2 + 0.5) / (cols / 2) * 2.0
            sy = -(r - rows / 2 + 0.5) / (rows / 2) * 2.0 * (rows / cols) / CW - 0.05
            o = to_obj((sx, sy, -5))
            best = None
            for li, (y0, y1) in enumerate(slabs):
                lo, hi = (-half, y0, -half), (half, y1, half)
                tmin, tmax, ax = -1e9, 1e9, None
                ok = True
                for k in range(3):
                    if abs(d[k]) < 1e-9:
                        if not lo[k] <= o[k] <= hi[k]:
                            ok = False
                        continue
                    t1, t2 = (lo[k] - o[k]) / d[k], (hi[k] - o[k]) / d[k]
                    sgn = -1 if t1 < t2 else 1
                    if t1 > t2:
                        t1, t2 = t2, t1
                    if t1 > tmin:
                        tmin, ax = t1, (k, sgn)
                    tmax = min(tmax, t2)
                if ok and tmin <= tmax and tmin > 0 and (best is None or tmin < best[0]):
                    best = (tmin, ax, li)
            if best is None:
                row.append((" ", 0))
                continue
            tm, (k, sgn), li = best
            p = [o[j] + tm * d[j] for j in range(3)]
            y0, y1 = slabs[li]
            near = [abs(abs(p[0]) - half) < 0.07, abs(p[1] - y0) < 0.05 or abs(p[1] - y1) < 0.05,
                    abs(abs(p[2]) - half) < 0.07]
            if sum(near[j] for j in range(3) if j != k):  # on a slab edge
                row.append(("@", li + 1))
                continue
            n = [0, 0, 0]
            n[k] = sgn
            nc = to_cam(n)
            lam = max(0.0, nc[0] * light[0] + nc[1] * light[1] + nc[2] * light[2])
            v = 0.3 + 0.7 * lam
            row.append((RAMP[min(len(RAMP) - 1, 1 + int(v * (len(RAMP) - 2)))], li + 1))
        out.append(row)
    return out


def stack_frames(x0, y0, n=48, period=4.8, size=7.8):
    lh = size
    cw = size * CW
    parts = []
    for i in range(n):
        g = render_stack(i / n * math.pi / 2)  # quarter turn = seamless loop (square slabs)
        lines = []
        for r, row in enumerate(g):
            spans, run, cur = [], "", None
            for ch, li in row:
                k = 0 if ch == " " else (3 if ch in "%#@" else 2 if ch in "=+*" else 1)
                if k != cur and run:
                    spans.append((cur, run))
                    run = ""
                cur = k
                run += ch
            if run:
                spans.append((cur, run))
            first = next((j for j, (k, _) in enumerate(spans) if k), None)
            if first is None:
                continue
            xs = x0 + sum(len(s) for _, s in spans[:first]) * cw
            body = "".join(f'<tspan class="c{k}">{escape(s)}</tspan>' if k else escape(s)
                           for k, s in spans[first:]).rstrip()
            lines.append(f'<tspan x="{xs:.1f}" y="{y0 + r * lh:.1f}">{body}</tspan>')
        cls = "f f0" if i == 0 else "f"
        parts.append(f'<text class="{cls}" style="animation-delay:{i * period / n - period:.3f}s">{"".join(lines)}</text>')
    css = (f".f{{font-size:{size}px;opacity:0;animation:fr {period}s step-end infinite}}.f0{{opacity:1}}"
           f"@keyframes fr{{0%{{opacity:1}}{100 / n:.3f}%{{opacity:0}}100%{{opacity:0}}}}"
           f".c1{{fill:{Y3}}}.c2{{fill:{Y2}}}.c3{{fill:{Y}}}")
    return "".join(parts), css


# ---------------------------------------------------------------- hero
def hero():
    W, H = 900, 418
    body, txt = [], []

    def T(*a, **k):
        s = t(*a, **k)
        txt.append(a[2])
        return s

    body.append(window(W, H, "~/th3r-dev"))

    cmd = "th3 agent --profile th3r-dev"
    txt.append("$ " + cmd)
    body.append(T(24, 60, "$", 13, Y, 800))
    body.append(typed(40, 60, cmd, 13, 0.3, 0.9))

    status = "11 skills loaded   design-core  qa  devops  poc-builder"
    body.append(appear(1.35, check(26, 79, Y) + T(42, 84, status, 12, TX3)))

    # left card: focal point
    cx, cy, cw_, ch_ = 24, 104, 286, 226
    card = (f'<rect x="{cx}" y="{cy}" width="{cw_}" height="{ch_}" rx="10" fill="none" stroke="{Y}" stroke-width="1.2"/>'
            f'<rect x="{cx + 14}" y="{cy - 8}" width="{len("th3r-dev") * 12 * CW + 12:.0f}" height="16" fill="{BG}"/>'
            + T(cx + 20, cy + 4, "th3r-dev", 12, Y, 800))
    frames, fcss = stack_frames(cx + cw_ / 2 - 44 * 7.8 * CW / 2, cy + 22)
    card += frames
    card += T(cx + cw_ / 2, cy + 200, "Theeraphat Chueanokkhum", 14.5, TX, 800, anchor="middle")
    card += T(cx + cw_ / 2, cy + 218, "Chaiyaphum, Thailand  UTC+7", 11.5, TX3, anchor="middle")
    body.append(appear(1.7, card, 0.6))

    # right column
    rx, d = 340, 2.0
    rows = [
        ("About", ["Full-stack + platform engineer.", "I build software from the interface down to the cluster."]),
        ("Now", ["Building OCM, a nationwide oil-control platform", "for Thailand's Excise Department."]),
        ("Layers", None),
        ("Elsewhere", ["me.th33raphat.dev  /  th33raphat@gmail.com"]),
    ]
    y = 118
    for head, lines in rows:
        body.append(appear(d, T(rx, y, head, 13, Y, 800)))
        d += 0.12
        if lines is None:  # layer chips, one lit at a time
            chips, x = "", rx
            for i, name in enumerate(["Interface", "Services", "Data", "Platform"]):
                wpx = len(name) * 12 * CW + 18
                chips += (f'<g><rect x="{x}" y="{y + 10}" width="{wpx:.0f}" height="22" rx="5" fill="{BAR}" stroke="{LINE2}"/>'
                          f'<rect x="{x}" y="{y + 10}" width="{wpx:.0f}" height="22" rx="5" fill="{Y}" class="lit" '
                          f'style="animation-delay:{3.2 + i * 1.2:.1f}s"/>'
                          f'<text x="{x + 9}" y="{y + 25}" font-size="12" class="lt" style="animation-delay:{3.2 + i * 1.2:.1f}s">{name}</text></g>')
                txt.append(name)
                x += wpx + 8
            body.append(appear(d, chips))
            y += 50
        else:
            for ln in lines:
                y += 20
                body.append(appear(d, T(rx, y, ln, 13, TX2)))
                d += 0.12
            y += 26
        if head == "Now":
            body.append(f'<path d="M{rx} {y - 18}H{W - 24}" stroke="{LINE}" pathLength="1" class="dr" style="animation-delay:{d:.2f}s"/>')
            y += 4

    # prompt
    py = 348
    hint = 'Try "review this PR, then ship it to nonprod"'
    prompt = (f'<rect x="24" y="{py}" width="{W - 48}" height="38" rx="7" fill="none" stroke="{LINE2}" stroke-width="1.2"/>'
              + T(38, py + 24, ">", 13.5, Y, 800)
              + f'<rect x="56" y="{py + 12}" width="8" height="16" fill="{Y}" class="bl"/>'
              + T(70, py + 24, hint, 13, TX3))
    body.append(appear(d + 0.3, prompt))
    body.append(appear(d + 0.45, T(38, py + 58, "/skills to list   ? for shortcuts", 11.5, TX3)))

    period = 4.8
    css = (BASE_CSS + fcss
           + f".lit{{opacity:0;animation:lit {period}s linear infinite}}"
           + f".lt{{fill:{TX2};animation:lt {period}s linear infinite}}"
           + f"@keyframes lit{{0%,25%{{opacity:1}}25.01%,100%{{opacity:0}}}}"
           + f"@keyframes lt{{0%,25%{{fill:{BG}}}25.01%,100%{{fill:{TX2}}}}}"
           + RM_CSS + ".lit{opacity:0}")
    label = ("A terminal styled like an AI coding agent. Welcome panel for Theeraphat Chueanokkhum, "
             "Chaiyaphum, Thailand, with a spinning ASCII stack of four layers. About: full-stack and platform "
             "engineer who builds software from the interface down to the cluster. Now: building OCM, a nationwide "
             "oil-control platform for Thailand's Excise Department. Layers: Interface, Services, Data, Platform.")
    return svg(W, H, label, "Theeraphat Chueanokkhum", css, body, "".join(txt) + RAMP)


# ---------------------------------------------------------------- agents
SKILLS = [
    ("Plan", "poc-spec-driven-builder", "Research, spec and a test matrix before any code"),
    ("Design", "design-core", "Layout, copy and accessibility review with scores"),
    ("", "design-flow", "Figma screens with their flowchart drawn beside them"),
    ("Build", "prompt-cache-kit", "Keep agent prompts cache-friendly to cut token cost"),
    ("", "thai-mock-naming", "Safe Thai mock names for seeds and fixtures"),
    ("Test", "qa", "Q&A review, test evidence and ticket reports"),
    ("", "dependency-vuln-explainer", "How a CVE works and whether it reaches your app"),
    ("Ship", "devops", "Infra changes in a fixed order, closed with a report"),
    ("", "doc-style-builder", "One Markdown source to matching PDF and DOCX"),
    ("", "pdf-operations", "Merge, split, reorder and stamp PDFs"),
    ("", "podman-disk-reclaim", "Shrink a Podman machine that ate the disk"),
]


def agents():
    W = 900
    stages = ["Plan", "Design", "Build", "Test", "Ship"]
    top, rh = 150, 21
    H = top + len(SKILLS) * rh + 56
    body, txt = [window(W, H, "th3-skills")], []

    def T(*a, **k):
        txt.append(a[2])
        return t(*a, **k)

    body.append(T(24, 60, "$", 13, Y, 800))
    body.append(typed(40, 60, "/skills", 13, 0.3, 0.35))
    txt.append("/skills")
    body.append(appear(0.8, T(24, 84, "Skills I give my coding agents, from idea to production.", 12, TX3)))

    # stage rail
    x, sx = 24, {}
    rail = ""
    t0 = 1.0
    first_row = {s: next(i for i, r in enumerate(SKILLS) if r[0] == s) for s in stages}
    for i, s in enumerate(stages):
        wpx = len(s) * 12 * CW + 22
        delay = t0 + first_row[s] * 0.22
        rail += (f'<rect x="{x}" y="100" width="{wpx:.0f}" height="24" rx="12" fill="{BAR}" stroke="{LINE2}"/>'
                 f'<rect x="{x}" y="100" width="{wpx:.0f}" height="24" rx="12" fill="{Y}" '
                 f'style="animation:in .3s ease {delay:.2f}s both"/>'
                 f'<text x="{x + 11}" y="116" font-size="12" font-weight="800" fill="{BG}" '
                 f'style="animation:in .3s ease {delay:.2f}s both">{s}</text>'
                 f'<text x="{x + 11}" y="116" font-size="12" fill="{TX3}" class="hd" style="animation-delay:{delay:.2f}s">{s}</text>')
        txt.append(s)
        sx[s] = x
        x += wpx
        if i < len(stages) - 1:
            rail += f'<path d="M{x + 6} 112h18" stroke="{LINE2}" stroke-width="1.2"/><path d="M{x + 20} 108l4 4-4 4" fill="none" stroke="{LINE2}" stroke-width="1.2"/>'
            x += 30
    body.append(appear(0.9, rail))

    # rows
    for i, (stage, name, desc) in enumerate(SKILLS):
        y = top + i * rh
        delay = t0 + i * 0.22
        row = ""
        if stage:
            row += T(24, y, stage, 12, TX3)
            if i:
                body.append(f'<path d="M24 {y - 15}H{W - 24}" stroke="{LINE}"/>')
        row += diamond(100, y - 4) + T(112, y, name, 12.5, TX, 800) + T(330, y, desc, 12.5, TX2)
        row += check(W - 42, y - 4, Y)
        body.append(appear(delay, row, 0.35))

    end = t0 + len(SKILLS) * 0.22 + 0.3
    fy = top + len(SKILLS) * rh + 12
    body.append(f'<path d="M24 {fy - 10}H{W - 24}" stroke="{LINE}" pathLength="1" class="dr" style="animation-delay:{end:.2f}s"/>')
    foot = "/plugin marketplace add th3r-dev/th3-skills"
    body.append(appear(end + 0.3, T(24, fy + 14, "$", 13, Y, 800)
                       + f'<rect x="40" y="{fy + 2}" width="8" height="16" fill="{Y}" class="bl"/>'
                       + T(W - 24, fy + 14, foot, 11.5, TX3, anchor="end")))

    css = (BASE_CSS + f".hd{{animation:hd .3s ease both}}@keyframes hd{{to{{opacity:0}}}}" + RM_CSS + ".hd{opacity:0}")
    label = ("A terminal listing the th3-skills a coding agent uses, grouped by stage: Plan, Design, Build, Test, Ship. "
             + " ".join(f"{n}: {d}." for _, n, d in SKILLS))
    return svg(W, H, label, "th3-skills", css, body, "".join(txt))


def svg(w, h, label, title, css, body, text):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
            f'role="img" aria-label="{escape(label)}"><title>{escape(title)}</title>'
            f'<style>{font_css(text)}{css}</style>{"".join(body)}</svg>')


if __name__ == "__main__":
    import os
    os.makedirs(OUT, exist_ok=True)
    for name, fn in (("hero.svg", hero), ("agents.svg", agents)):
        s = fn()
        open(f"{OUT}/{name}", "w").write(s)
        print(name, len(s) // 1024, "KB")

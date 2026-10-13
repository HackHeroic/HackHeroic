"""Build the animated terminal header for the GitHub profile README.

Pure SVG + CSS animations (no script, no external fonts), so it renders inside
GitHub's image sandbox. Every animated element's *base* style is its final state:
if animations are off (reduced motion, static renderers) the full session shows.

Usage: python3 make_terminal.py out.svg
"""
import sys
from html import escape

W = 760                     # viewBox width
PAD = 30                    # left/right text padding
FS = 20                     # body font size
CW = FS * 0.6               # monospace advance width (approx)
LH = 30                     # line height
TITLE_H = 40
TOP = TITLE_H + 34          # baseline of first line

BG = "#161b22"
BAR = "#21262d"
BORDER = "#30363d"
C = {
    "fg": "#e6edf3", "dim": "#8b949e", "green": "#3fb950", "blue": "#58a6ff",
    "purple": "#d2a8ff", "orange": "#ffa657", "red": "#ff7b72", "yellow": "#e3b341",
}
MONO = ("ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Monaco, Consolas, "
        "'Liberation Mono', 'DejaVu Sans Mono', 'Courier New', monospace")

PROMPT = [("~", "blue"), (" $ ", "green")]
PROMPT_LEN = sum(len(t) for t, _ in PROMPT)

# The session. ("cmd", text) is typed after a prompt; ("out", segments, opts)
# appears instantly; ("pause", seconds) adds a beat; ("end",) is the idle prompt.
SESSION = [
    ("cmd", "whoami"),
    ("out", [("C. Murali Madhav", "fg")], {"size": 36, "bold": True, "lh": 46}),
    ("out", [("i build for systems that break expensively.", "dim")], {}),
    ("cmd", "cat highlights.txt"),
    ("out", [("112x   ", "green", True), ("cuda kernels vs single-core numpy", "fg")], {}),
    ("out", [("2.50%  ", "orange", True), ("my grid forecast error. the grid's own: 3.51%", "fg")], {}),
    ("out", [("#8     ", "purple", True), ("hackmit puzzle contest, worldwide. was 17th.", "fg")], {}),
    ("cmd", "cat startup.json"),
    ("out", [('{', "dim"), ('"name"', "blue"), (': ', "dim"), ('null', "orange"), (', ', "dim"), ('"c_corp"', "blue"), (': ', "dim"), ('"in process"', "green"), (',', "dim")], {}),
    ("out", [(' ', "dim"), ('"clients"', "blue"), (': [', "dim"), ('"FL"', "green"), (', ', "dim"), ('"NY"', "green"), (']}', "dim")], {}),
    ("end",),
]

TYPE_DT = 0.075     # seconds per typed character
ENTER_PAUSE = 0.30  # after a command is typed, before its output
OUT_GAP = 0.13      # between output lines
START = 0.35


def tspan(segs, size=FS, bold=False):
    parts = []
    for seg in segs:
        text, color = seg[0], seg[1]
        seg_bold = bold or (len(seg) > 2 and seg[2])
        w = ' font-weight="700"' if seg_bold else ""
        parts.append(f'<tspan fill="{C[color]}"{w}>{escape(text)}</tspan>')
    return "".join(parts)


def build():
    css = [
        "text{font-family:" + MONO + ";white-space:pre}",
        "@keyframes show{from{opacity:0}to{opacity:1}}",
        "@keyframes blink{0%,49%{opacity:1}50%,100%{opacity:0}}",
        ".s{animation:show .01s linear both}",
    ]
    body = []
    y = TOP
    t = START
    n_type = 0
    for item in SESSION:
        kind = item[0]
        if kind == "pause":
            t += item[1]
            continue
        if kind in ("cmd", "end"):
            text = item[1] if kind == "cmd" else ""
            x_cmd = PAD + PROMPT_LEN * CW
            line = [f'<text x="{PAD}" y="{y}" font-size="{FS}">{tspan(PROMPT)}'
                    f'<tspan fill="{C["fg"]}">{escape(text)}</tspan></text>']
            if kind == "cmd":
                n_type += 1
                dist = len(text) * CW
                dur = len(text) * TYPE_DT
                t_type = t + 0.25           # tiny hesitation before typing
                t_enter = t_type + dur + ENTER_PAUSE
                k = f"t{n_type}"
                css.append(f"@keyframes {k}{{from{{transform:translateX(0)}}"
                           f"to{{transform:translateX({dist:.1f}px)}}}}")
                css.append(f".{k}{{transform:translateX({dist:.1f}px);"
                           f"animation:{k} {dur:.2f}s steps({len(text)},end) {t_type:.2f}s both}}")
                css.append(f".c{n_type}{{opacity:0;animation:blink .9s step-end {t:.2f}s "
                           f"{(t_enter - t) / 0.9:.3f}}}")
                # cover hides the command until typed; cursor rides its left edge
                line.append(
                    f'<g class="{k}"><rect x="{x_cmd:.1f}" y="{y - FS + 2}" width="{W}" '
                    f'height="{LH - 2}" fill="{BG}"/>'
                    f'<rect class="c{n_type}" x="{x_cmd:.1f}" y="{y - FS + 3}" width="{CW:.1f}" '
                    f'height="{FS + 3}" fill="{C["fg"]}" opacity="0"/></g>')
                body.append(f'<g class="s" style="animation-delay:{t:.2f}s">{"".join(line)}</g>')
                t = t_enter
                y += LH
            else:
                x_cur = PAD + PROMPT_LEN * CW
                css.append(f".cur{{animation:blink 1.1s step-end {t:.2f}s infinite}}")
                line.append(f'<rect class="cur" x="{x_cur:.1f}" y="{y - FS + 3}" '
                            f'width="{CW:.1f}" height="{FS + 3}" fill="{C["fg"]}"/>')
                body.append(f'<g class="s" style="animation-delay:{t:.2f}s">{"".join(line)}</g>')
                y += LH
        elif kind == "out":
            segs, opts = item[1], item[2]
            size = opts.get("size", FS)
            lh = opts.get("lh", LH)
            y_line = y + (lh - LH)            # taller lines push the baseline down
            body.append(f'<text class="s" style="animation-delay:{t:.2f}s" x="{PAD}" '
                        f'y="{y_line}" font-size="{size}">{tspan(segs, size, opts.get("bold", False))}</text>')
            t += OUT_GAP
            y = y_line + LH
    H = y + 6
    css.append("@media (prefers-reduced-motion: reduce){*{animation:none!important}}")

    transcript = []
    for item in SESSION:
        if item[0] == "cmd":
            transcript.append("$ " + item[1])
        elif item[0] == "out":
            transcript.append("".join(s[0] for s in item[1]))
    desc = escape(" / ".join(transcript))

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-labelledby="ttl dsc">
<title id="ttl">C. Murali Madhav: terminal introduction</title>
<desc id="dsc">{desc}</desc>
<style>{"".join(css)}</style>
<defs><clipPath id="card"><rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="12"/></clipPath></defs>
<rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="12" fill="{BG}"/>
<g clip-path="url(#card)">
<rect x="0" y="0" width="{W}" height="{TITLE_H}" fill="{BAR}"/>
<circle cx="24" cy="{TITLE_H / 2}" r="6.5" fill="#ff5f57"/><circle cx="46" cy="{TITLE_H / 2}" r="6.5" fill="#febc2e"/><circle cx="68" cy="{TITLE_H / 2}" r="6.5" fill="#28c840"/>
<text x="{W / 2}" y="{TITLE_H / 2 + 5}" font-size="14" fill="{C["dim"]}" text-anchor="middle">madhav@hackheroic: ~</text>
{chr(10).join(body)}
</g>
<rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="12" fill="none" stroke="{BORDER}" stroke-width="1.5"/>
</svg>
'''
    return svg


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "terminal.svg"
    with open(out, "w") as f:
        f.write(build())
    print("wrote", out)

"""Runs the simulation and writes sim/report.html (self-contained, charts first).

Usage:  python make_report.py [games_per_cell]
"""
import datetime
import hashlib
import html
import json
import os
import re
import shutil
import sys

import secret_onu_sim as sim

HERE = os.path.dirname(os.path.abspath(__file__))
G = int(sys.argv[1]) if len(sys.argv) > 1 else 2000
REPRO_OUT = os.environ.get("SECRET_ONU_OUT")      # set by reproduce.py: no snapshot, write here
INPUT_FILES = {                                   # label -> file name inside sim.ROOT
    "Design document": "secret_onu_design_document.md",
    "Quadrants": "test_quadrants.md",
    "Events": "test_events.md",
    "Objectives": "test_objectives.md",
}
CODE_FILES = ["secret_onu_sim.py", "make_report.py", "report_template.html"]
RULES = {
    "rounds": sim.ROUNDS, "loss_at_unhandled": sim.LOSS_UNHANDLED,
    "event_cost": dict(sim.EVENT_COST), "vote_cost": dict(sim.VOTE_COST),
    "hand": sim.HAND, "track_max": sim.TRACK_MAX, "sections": {k: list(v) for k, v in sim.SECTIONS.items()},
    "vote_deck_size": sim.VOTE_DECK_SIZE, "vote_magnitude_2_share": sim.P_MAG2,
}


def file_hash(path):
    data = open(path, "rb").read().replace(b"\r\n", b"\n")
    return hashlib.sha256(data).hexdigest()[:8]


def doc_mismatches():
    """Compare the costs / rounds / loss limit in the Italian design doc with the simulator constants."""
    warns = []
    path = os.path.join(sim.ROOT, INPUT_FILES["Design document"])
    if not os.path.exists(path):
        return ["Design document not found."]
    text = open(path, encoding="utf-8").read()
    sections = {s.split("\n", 1)[0].strip(): s for s in re.split(r"\n## ", text)}
    def costs(title_part):
        for t, body in sections.items():
            if title_part in t:
                m = re.search(r"sono (\d+)/(\d+)/(\d+)/(\d+)", body)
                return [int(x) for x in m.groups()] if m else None
        return None
    for label, key, table in (("Event", "Mazzo degli Eventi", sim.EVENT_COST), ("Vote", "Mazzo delle Votazioni", sim.VOTE_COST)):
        c = costs(key)
        want = [table[n] for n in (3, 4, 5, 6)]
        if c is None:
            warns.append(f"{label} costs not found in the design document.")
        elif c != want:
            warns.append(f"{label} costs differ: document says {'/'.join(map(str, c))}, simulator uses {'/'.join(map(str, want))}.")
    m = re.search(r"(\d+) round", text)
    if m and int(m.group(1)) != sim.ROUNDS:
        warns.append(f"Rounds differ: document says {m.group(1)}, simulator uses {sim.ROUNDS}.")
    ordinals = {"quarto": 4, "quinto": 5, "sesto": 6, "terzo": 3}
    m = re.search(r"al (\w+) evento non gestito", text)
    if m and ordinals.get(m.group(1)) not in (None, sim.LOSS_UNHANDLED):
        warns.append(f"Loss limit differs: document says the {m.group(1)} unhandled event, simulator uses #{sim.LOSS_UNHANDLED}.")
    return warns
PLAYERS = (3, 4, 5, 6)
STRATS = ("random", "cooperative", "mixed", "selfish")
STRAT_LABEL = {"random": "Random cards", "cooperative": "Cooperative", "mixed": "Mixed", "selfish": "Selfish"}

# ---------------------------------------------------------------- run
main = {(n, s): sim.run(n, s, G, seed=1000 * n + len(s)) for n in PLAYERS for s in STRATS}
lies = {(n, l): sim.run(n, "mixed", G, seed=77 * n, lies=l) for n in PLAYERS for l in (False, True)}
base_cost = sim.EVENT_COST[4]
sweep_costs = list(range(base_cost, base_cost + 6))
sweep = {}
for c in sweep_costs:
    sim.EVENT_COST[4] = c
    for s in ("cooperative", "mixed"):
        sweep[(c, s)] = sim.run(4, s, G, seed=9, )
sim.EVENT_COST[4] = base_cost


# ---------------------------------------------------------------- svg helpers
def esc(x):
    return html.escape(str(x))


def fnum(v):
    return f"{v:.0f}" if v >= 10 or v == 0 else f"{v:.1f}"


def axis(W, H, L, R, T, B, ymax, step, unit):
    out = []
    y = 0
    while y <= ymax + 1e-9:
        py = T + (H - T - B) * (1 - y / ymax)
        out.append(f'<line class="grid" x1="{L}" x2="{W - R}" y1="{py:.1f}" y2="{py:.1f}"/>')
        out.append(f'<text class="tick" x="{L - 8}" y="{py + 4:.1f}" text-anchor="end">{y:g}{unit}</text>')
        y += step
    return "".join(out)


def legend(items):
    return '<div class="legend">' + "".join(
        f'<span><i class="sw s{i}"></i>{esc(name)}</span>' for i, name in items) + "</div>"


def grouped_bars(cats, series, ymax, step, unit="%", W=680, H=300, label=True):
    """series: list of (slot, name, [values per cat])"""
    L, R, T, B = 44, 12, 16, 30
    pw = W - L - R
    gw = pw / len(cats)
    bw = min(34, (gw * 0.78) / len(series))
    out = [f'<svg viewBox="0 0 {W} {H}" role="img" class="chart">', axis(W, H, L, R, T, B, ymax, step, unit)]
    for ci, c in enumerate(cats):
        gx = L + gw * ci + (gw - bw * len(series)) / 2
        for si, (slot, name, vals) in enumerate(series):
            v = vals[ci]
            h = (H - T - B) * min(v, ymax) / ymax
            x = gx + si * bw
            y = H - B - h
            if h > 0.5:
                out.append(f'<rect class="f{slot}" x="{x + 1:.1f}" y="{y:.1f}" width="{bw - 2:.1f}" height="{h:.1f}" rx="3">'
                           f'<title>{esc(name)}, {esc(c)}: {v:.1f}{unit}</title></rect>')
            if label:
                out.append(f'<text class="val" x="{x + bw / 2:.1f}" y="{y - 4:.1f}" text-anchor="middle">{fnum(v)}</text>')
        out.append(f'<text class="cat" x="{L + gw * ci + gw / 2:.1f}" y="{H - 10}" text-anchor="middle">{esc(c)}</text>')
    out.append(f'<line class="base" x1="{L}" x2="{W - R}" y1="{H - B}" y2="{H - B}"/></svg>')
    return "".join(out)


def lines(xs, series, ymax, step, unit="%", W=680, H=300, xlabel="", mark=None):
    """series: list of (slot, name, [values per x]); mark = x value to highlight."""
    L, R, T, B = 44, 90, 16, 50
    pw, ph = W - L - R, H - T - B
    px = lambda i: L + pw * i / (len(xs) - 1)
    py = lambda v: T + ph * (1 - min(v, ymax) / ymax)
    out = [f'<svg viewBox="0 0 {W} {H}" role="img" class="chart">', axis(W, H, L, R, T, B, ymax, step, unit)]
    for i, x in enumerate(xs):
        out.append(f'<text class="cat" x="{px(i):.1f}" y="{H - 30}" text-anchor="middle">{esc(x)}</text>')
    if mark is not None:
        i = xs.index(mark)
        out.append(f'<line class="mark" x1="{px(i):.1f}" x2="{px(i):.1f}" y1="{T}" y2="{H - B}"/>')
        out.append(f'<text class="note" x="{px(i) + 6:.1f}" y="{T + 10}">current rules</text>')
    if xlabel:
        out.append(f'<text class="axlabel" x="{L + pw / 2:.1f}" y="{H - 6}" text-anchor="middle">{esc(xlabel)}</text>')
    for slot, name, vals in series:
        pts = " ".join(f"{px(i):.1f},{py(v):.1f}" for i, v in enumerate(vals))
        out.append(f'<polyline class="ln c{slot}" points="{pts}"/>')
        for i, v in enumerate(vals):
            out.append(f'<circle class="f{slot} dot" cx="{px(i):.1f}" cy="{py(v):.1f}" r="4.5"><title>{esc(name)}, {esc(xs[i])}: {v:.1f}{unit}</title></circle>')
        out.append(f'<text class="val" x="{px(len(xs) - 1) + 10:.1f}" y="{py(vals[-1]) + 4:.1f}">{vals[-1]:.0f}{unit}</text>')
    out.append(f'<line class="base" x1="{L}" x2="{W - R}" y1="{H - B}" y2="{H - B}"/></svg>')
    return "".join(out)


def hbars(rows, vmax, unit="%", W=680, slot=1, L=250):
    """rows: list of (label, value)"""
    R, rowh = 52, 30
    H = rowh * len(rows) + 28
    out = [f'<svg viewBox="0 0 {W} {H}" role="img" class="chart">']
    for t in range(0, int(vmax) + 1, 10):
        x = L + (W - L - R) * t / vmax
        out.append(f'<line class="grid" x1="{x:.1f}" x2="{x:.1f}" y1="0" y2="{H - 22}"/>')
        out.append(f'<text class="tick" x="{x:.1f}" y="{H - 6}" text-anchor="middle">{t}{unit}</text>')
    for i, (lab, v) in enumerate(rows):
        y = i * rowh + 4
        w = (W - L - R) * v / vmax
        out.append(f'<text class="cat" x="{L - 10}" y="{y + 14}" text-anchor="end">{esc(lab)}</text>')
        out.append(f'<rect class="f{slot}" x="{L}" y="{y}" width="{w:.1f}" height="20" rx="3"><title>{esc(lab)}: {v:.1f}{unit}</title></rect>')
        out.append(f'<text class="val" x="{L + w + 6:.1f}" y="{y + 14}">{v:.0f}{unit}</text>')
    out.append("</svg>")
    return "".join(out)


pc = lambda v: 100 * v

# ---------------------------------------------------------------- charts
cats = [f"{n} players" for n in PLAYERS]
slots = {"random": 4, "cooperative": 1, "mixed": 2, "selfish": 3}

chart_loss = grouped_bars(
    cats, [(slots[s], STRAT_LABEL[s], [pc(main[(n, s)]["loss"]) for n in PLAYERS]) for s in STRATS], 20, 5)
leg_strat = legend([(slots[s], STRAT_LABEL[s]) for s in STRATS])

chart_sweep = lines(
    [f"{c}" for c in sweep_costs],
    [(1, "Cooperative", [pc(sweep[(c, "cooperative")]["loss"]) for c in sweep_costs]),
     (2, "Mixed", [pc(sweep[(c, "mixed")]["loss"]) for c in sweep_costs])],
    80, 20, xlabel="Event cost (resources, 4 players)", mark=f"{base_cost}")
leg_sweep = legend([(1, "Cooperative"), (2, "Mixed")])

chart_votes = grouped_bars(
    [STRAT_LABEL[s] for s in STRATS],
    [(1, "Events handled", [pc(main[(4, s)]["handled"]) for s in STRATS]),
     (2, "Votes passed", [pc(main[(4, s)]["vote_pass"]) for s in STRATS])], 100, 25)
leg_votes = legend([(1, "Events handled"), (2, "Votes passed")])

chart_wins = lines(
    [f"{n}" for n in PLAYERS],
    [(1, "At least one winner", [pc(main[(n, "mixed")]["any_winner"]) for n in PLAYERS]),
     (2, "Win rate per player", [pc(main[(n, "mixed")]["win_per_player"]) for n in PLAYERS])],
    100, 25, xlabel="Players")
leg_wins = legend([(1, "At least one winner"), (2, "Win rate per player")])

r4 = main[(4, "mixed")]
obj_rows = sorted(((", ".join(f"{t} {s}" for t, s in k), 100 * w / c) for k, (w, c) in r4["obj_win"].items()),
                  key=lambda x: -x[1])
chart_obj = hbars(obj_rows, 50)

chart_tracks = grouped_bars(
    ["Environment", "Economy", "Social"],
    [(1, "Games where the track ends pinned at 0 or 20", [pc(r4["extreme"][t]) for t in sim.TRACKS])], 50, 10)
mean_end = ", ".join(f"{t} {r4['end'][t]:.1f}" for t in sim.TRACKS)

chart_lies = grouped_bars(
    cats,
    [(1, "President tells the truth", [pc(lies[(n, False)]["win_per_player"]) for n in PLAYERS]),
     (2, "President lies when hurt", [pc(lies[(n, True)]["win_per_player"]) for n in PLAYERS])], 40, 10)
leg_lies = legend([(1, "President tells the truth"), (2, "President lies when hurt")])

# ---- quadrants: start drift and per-quadrant results
import itertools
qopts = sim.QUAD_OPTIONS
qids = [q for sec in sorted(qopts) for q in sorted(qopts[sec])]
qinfo = lambda q: qopts[q[0]][q]


def tint(v):
    if not v:
        return "<td>0</td>"
    var = "--s3" if v > 0 else "--s2"
    return f'<td style="background:color-mix(in srgb, var({var}) {min(60, abs(v) * 18)}%, transparent)">{v:+d}</td>'


qrows = []
for q in qids:
    info = qinfo(q)
    e = info["spaces"][info["start"]]
    qrows.append(f"<tr><td>{q}</td><td>{esc(info['name'])}</td><td>{info['start']}</td>"
                 + "".join(tint(e.get(t, 0)) for t in sim.TRACKS) + "</tr>")
drifts = {t: [] for t in sim.TRACKS}
heavy = total = 0
for combo in itertools.product(*[sorted(qopts[sec]) for sec in sorted(qopts)]):
    d = {t: sum(qinfo(c)["spaces"][qinfo(c)["start"]].get(t, 0) for c in combo) for t in sim.TRACKS}
    for t in sim.TRACKS:
        drifts[t].append(d[t])
    heavy += max(abs(v) for v in d.values()) >= 4
    total += 1
drift_txt = ", ".join(f"{t} {sum(v) / len(v):+.1f} (range {min(v):+d} to {max(v):+d})" for t, v in drifts.items())
bq = r4["by_quad"]
short = lambda q: f"{q} {qinfo(q)['name']}"[:44]
chart_qwin = hbars([(short(q), 100 * bq[q]["win_per_player"]) for q in qids if q in bq], 40, L=300)
chart_qpin = hbars([(short(q), 100 * bq[q]["pinned"]) for q in qids if q in bq], 100, L=300, slot=2)
worst_q = min(bq, key=lambda q: bq[q]["win_per_player"])
best_q = max(bq, key=lambda q: bq[q]["win_per_player"])

# table
rows = []
for n in PLAYERS:
    for s in STRATS:
        r = main[(n, s)]
        rows.append(f"<tr><td>{n}</td><td>{STRAT_LABEL[s]}</td><td>{pc(r['loss']):.1f}%</td><td>{r['unhandled']:.2f}</td>"
                    f"<td>{pc(r['handled']):.1f}%</td><td>{pc(r['vote_pass']):.1f}%</td><td>{pc(r['win_per_player']):.1f}%</td>"
                    f"<td>{pc(r['any_winner']):.1f}%</td></tr>")
table = "".join(rows)

# headline numbers
coop4 = main[(4, "cooperative")]
mix4 = main[(4, "mixed")]
sw_c = lambda c, s: pc(sweep[(c, s)]["loss"])
best_cost = next((c for c in sweep_costs if sw_c(c, "mixed") >= 10), sweep_costs[-1])

TEMPLATE = open(os.path.join(HERE, "report_template.html"), encoding="utf-8").read()
vals = {
    "GAMES": f"{G:,}",
    "CHART_LOSS": chart_loss, "LEG_STRAT": leg_strat,
    "CHART_SWEEP": chart_sweep, "LEG_SWEEP": leg_sweep,
    "CHART_VOTES": chart_votes, "LEG_VOTES": leg_votes,
    "CHART_WINS": chart_wins, "LEG_WINS": leg_wins,
    "CHART_OBJ": chart_obj,
    "CHART_TRACKS": chart_tracks, "MEAN_END": mean_end,
    "CHART_LIES": chart_lies, "LEG_LIES": leg_lies,
    "TABLE": table,
    "K_LOSS": f"{pc(mix4['loss']):.1f}%",
    "K_UNH": f"{mix4['unhandled']:.1f}",
    "K_PASS": f"{pc(coop4['vote_pass']):.0f}%",
    "K_WIN3": f"{pc(main[(3, 'mixed')]['win_per_player']):.0f}%",
    "K_WIN6": f"{pc(main[(6, 'mixed')]['win_per_player']):.0f}%",
    "K_BASE": str(base_cost),
    "K_BEST": str(best_cost),
    "K_SW_BASE": f"{sw_c(base_cost, 'mixed'):.1f}%",
    "K_SW_BEST": f"{sw_c(best_cost, 'mixed'):.0f}%",
    "K_SW_COOP_BEST": f"{sw_c(best_cost, 'cooperative'):.0f}%",
    "K_SW_LAST": f"{sw_c(sweep_costs[-1], 'mixed'):.0f}%",
    "K_SW_LAST_COST": str(sweep_costs[-1]),
    "K_SW_LAST_COOP": f"{sw_c(sweep_costs[-1], 'cooperative'):.0f}%",
    "QUAD_ROWS": "".join(qrows), "DRIFT_TXT": drift_txt, "K_HEAVY": f"{heavy} of {total}",
    "CHART_QWIN": chart_qwin, "CHART_QPIN": chart_qpin,
    "K_WORST_Q": f"{worst_q} ({qinfo(worst_q)['name']})", "K_WORST_WIN": f"{100 * bq[worst_q]['win_per_player']:.0f}%",
    "K_BEST_Q": f"{best_q} ({qinfo(best_q)['name']})", "K_BEST_WIN": f"{100 * bq[best_q]['win_per_player']:.0f}%",
    "K_AVG_WIN": f"{pc(mix4['win_per_player']):.0f}%",
    "K_PIN_ANY": f"{pc(mix4['any_extreme']):.0f}%",
    "LOSS_TITLE": ("Nobody loses together, so the shared threat isn't felt" if pc(mix4["loss"]) < 3
                   else f"The whole table loses {pc(mix4['loss']):.0f}% of games"),
    "LOSS_TEXT": (f"At 4 players the table loses {pc(mix4['loss']):.1f}% of games with mixed bots, "
                  f"{pc(main[(4, 'cooperative')]['loss']):.1f}% with cooperative bots and "
                  f"{pc(main[(4, 'random')]['loss']):.1f}% when cards are played at random."),
    "SWEEP_TITLE": ("Raising the event cost by 2 or 3 gives the loss condition teeth" if sw_c(base_cost, "mixed") < 3
                    else "The current event cost already makes the loss condition matter"),
    "SWEEP_VERDICT": (f"The first cost where mixed bots lose at least 10% of games is {best_cost}."
                      if sw_c(best_cost, "mixed") >= 10 else "Even the highest cost tested stays under 10% for mixed bots."),
    "VOTES_TEXT": (f"With cooperative bots, {pc(coop4['handled']):.0f}% of events are handled and {pc(coop4['vote_pass']):.0f}% of votes pass. "
                   f"With random cards it is {pc(main[(4, 'random')]['handled']):.0f}% and {pc(main[(4, 'random')]['vote_pass']):.0f}%."),
    "OBJ_TITLE": f"{obj_rows[-1][0]} is the hardest objective ({obj_rows[-1][1]:.0f}%), {obj_rows[0][0]} the easiest ({obj_rows[0][1]:.0f}%)",
    "K_LIE_DELTA":f"{pc(lies[(4, False)]['win_per_player'] - lies[(4, True)]['win_per_player']):.1f}",
}

# ---------------------------------------------------------------- versioning
def summarize(r):
    return {k: (v if k != "obj_win" else {", ".join(f"{t} {s}" for t, s in kk): list(vv) for kk, vv in v.items()}) if v == v else None
            for k, v in r.items()}


results = {
    "main": {f"{n}p/{s}": summarize(r) for (n, s), r in main.items()},
    "lies": {f"{n}p/{'lies' if l else 'truth'}": summarize(r) for (n, l), r in lies.items()},
    "sweep": {f"cost{c}/{s}": summarize(r) for (c, s), r in sweep.items()},
}
hashes = {label: file_hash(os.path.join(sim.ROOT, f)) for label, f in INPUT_FILES.items()
          if os.path.exists(os.path.join(sim.ROOT, f))}
code_hashes = {f: file_hash(os.path.join(HERE, f)) for f in CODE_FILES}
combined = hashlib.sha256(json.dumps([hashes, code_hashes, RULES, G], sort_keys=True).encode()).hexdigest()[:8]
now = datetime.datetime.now()
run_id = f"{now:%Y%m%d-%H%M}-{combined}"
warns = doc_mismatches()

runs_dir = os.path.join(HERE, "runs")
prev = None
if not REPRO_OUT and os.path.isdir(runs_dir):
    for name in sorted(os.listdir(runs_dir), reverse=True):
        mp = os.path.join(runs_dir, name, "manifest.json")
        if os.path.exists(mp):
            prev = json.load(open(mp, encoding="utf-8"))
            break

rows_v = []
for label, h in hashes.items():
    if prev is None:
        status = "first run"
    else:
        status = "unchanged" if prev["inputs"].get(label) == h else "changed"
    rows_v.append(f"<tr><td>{esc(label)}</td><td><code>{h}</code></td><td>{status}</td></tr>")
for f, h in code_hashes.items():
    status = "first run" if prev is None else ("unchanged" if prev["code"].get(f) == h else "changed")
    rows_v.append(f"<tr><td>{esc(f)} (simulator)</td><td><code>{h}</code></td><td>{status}</td></tr>")
rules_txt = (f"{RULES['rounds']} rounds · loss at unhandled event #{RULES['loss_at_unhandled']} · "
             f"event cost {'/'.join(str(RULES['event_cost'][n]) for n in (3, 4, 5, 6))} · "
             f"vote cost {'/'.join(str(RULES['vote_cost'][n]) for n in (3, 4, 5, 6))} (3/4/5/6 players)")
changed = [r.split("</td>")[0][8:] for r in rows_v if ">changed<" in r]
warn_html = ("<div class=\"warn\"><b>Rules mismatch</b><ul>" + "".join(f"<li>{esc(w)}</li>" for w in warns) + "</ul></div>") if warns else ""

vals["RUN_ID"] = run_id
vals["RUN_DATE"] = now.strftime("%Y-%m-%d %H:%M")
vals["RULES_TXT"] = rules_txt
vals["VERSION_ROWS"] = "".join(rows_v)
vals["WARN"] = warn_html
vals["CHANGED"] = ("Changed since the previous run: " + ", ".join(changed)) if changed else (
    "Nothing changed since the previous run." if prev else "First recorded run.")
for k, v in vals.items():
    TEMPLATE = TEMPLATE.replace("{{" + k + "}}", v)

if REPRO_OUT:
    os.makedirs(REPRO_OUT, exist_ok=True)
    json.dump(results, open(os.path.join(REPRO_OUT, "results.json"), "w"), indent=1, sort_keys=True)
    open(os.path.join(REPRO_OUT, "report.html"), "w", encoding="utf-8").write(TEMPLATE)
    print("reproduced into", REPRO_OUT)
else:
    run_dir = os.path.join(runs_dir, run_id)
    os.makedirs(os.path.join(run_dir, "inputs"))
    os.makedirs(os.path.join(run_dir, "code"))
    for f in INPUT_FILES.values():
        if os.path.exists(os.path.join(sim.ROOT, f)):
            shutil.copy2(os.path.join(sim.ROOT, f), os.path.join(run_dir, "inputs", f))
    for f in CODE_FILES:
        shutil.copy2(os.path.join(HERE, f), os.path.join(run_dir, "code", f))
    manifest = {"run_id": run_id, "created": now.isoformat(timespec="seconds"), "games_per_cell": G,
                "inputs": hashes, "code": code_hashes, "rules": RULES, "doc_warnings": warns,
                "note": "Seeds are fixed in the code, so the same inputs and games give identical results."}
    json.dump(manifest, open(os.path.join(run_dir, "manifest.json"), "w"), indent=1)
    json.dump(results, open(os.path.join(run_dir, "results.json"), "w"), indent=1, sort_keys=True)
    open(os.path.join(run_dir, "report.html"), "w", encoding="utf-8").write(TEMPLATE)
    open(os.path.join(HERE, "report.html"), "w", encoding="utf-8").write(TEMPLATE)
    m4 = main[(4, "mixed")]
    with open(os.path.join(runs_dir, "index.md"), "a", encoding="utf-8") as f:
        if f.tell() == 0:
            f.write("# Simulation runs\n\n| Run | Games | Rules | 4p mixed: loss / win per player | Changed |\n|---|---|---|---|---|\n")
        f.write(f"| {run_id} | {G} | {rules_txt} | {pc(m4['loss']):.1f}% / {pc(m4['win_per_player']):.1f}% | "
                f"{', '.join(changed) if changed else ('first run' if prev is None else 'nothing')} |\n")
    print("wrote", os.path.join(run_dir, "report.html"), "and sim/report.html")

"""Monte Carlo playtest simulator for Secret ONU.

Reads the test_*.md files in the parent folder, so editing quadrants/events/objectives
and re-running is enough. Rules assumptions are listed in ASSUMPTIONS below and in the report.

Usage:  python secret_onu_sim.py [games_per_config]
"""
import os
import random
import re
import sys
from collections import defaultdict
from itertools import permutations

HERE = os.path.dirname(os.path.abspath(__file__))
# Folder holding the test_*.md data files. Normally the project root; a saved run
# is re-run against its own copy of the inputs through SECRET_ONU_ROOT (see reproduce.py).
ROOT = os.environ.get("SECRET_ONU_ROOT") or os.path.dirname(HERE)

TRACKS = ("environment", "economy", "social")
ABBR = {"ECO": "environment", "ECN": "economy", "SOC": "social"}

# ---- rules (from the design doc) -------------------------------------------------
ROUNDS = 12
LOSS_UNHANDLED = 5
EVENT_COST = {3: 6, 4: 8, 5: 10, 6: 12}
VOTE_COST = {3: 7, 4: 9, 5: 11, 6: 13}
HAND = list(range(6))            # one card each of 0..5
TRACK_MAX = 20
# ---- ASSUMPTIONS (not in the doc) --------------------------------------------------
SECTIONS = {"low": (0, 6), "medium": (7, 13), "high": (14, 20)}
VOTE_DECK_SIZE = 40
# a vote card affects 2 quadrants; magnitude 1 (70%) or 2 (30%), random sign
P_MAG2 = 0.3


# ---- data loading ----------------------------------------------------------------
def parse_effects(text):
    out = defaultdict(int)
    for val, name in re.findall(r"([+-]\d+)\s+(environment|economy|social)", text):
        out[name] += int(val)
    return dict(out)


def load_quadrants():
    """Returns {section letter: {quadrant id: {"spaces": {pos: effects}, "start": pos}}}.
    A header like '# Quadrant B2 (...)' is variant 2 of section B; a plain '# Quadrant B' is the only variant."""
    opts = {}
    cur = None
    for line in open(os.path.join(ROOT, "test_quadrants.md"), encoding="utf-8"):
        m = re.match(r"#\s*Quadrant\s+([A-D])(\d?)\s*(?:\((.*)\))?", line)
        if m:
            cur = m.group(1) + m.group(2)
            opts.setdefault(m.group(1), {})[cur] = {"spaces": {}, "start": None, "name": m.group(3) or cur}
            continue
        m = re.match(r"(\d)\.\s*(.*)", line)
        if m and cur:
            pos = int(m.group(1))
            q = opts[cur[0]][cur]
            q["spaces"][pos] = parse_effects(m.group(2))
            if "(start)" in m.group(2):
                q["start"] = pos
    return opts


# Active quadrants of the game being played (one variant per section), filled by choose_quadrants().
QUADS, QSTART, QCHOSEN = {}, {}, {}


def choose_quadrants(rng):
    QUADS.clear()
    QSTART.clear()
    QCHOSEN.clear()
    for letter in sorted(QUAD_OPTIONS):
        qid = rng.choice(sorted(QUAD_OPTIONS[letter]))
        QCHOSEN[letter] = qid
        QUADS[letter] = QUAD_OPTIONS[letter][qid]["spaces"]
        QSTART[letter] = QUAD_OPTIONS[letter][qid]["start"]


def load_events():
    events = []
    for line in open(os.path.join(ROOT, "test_events.md"), encoding="utf-8"):
        m = re.match(r"(\d+)\.\s+(.+?):\s+(.*)", line)
        if not m:
            continue
        name, body = m.group(2), m.group(3)
        ev = {"name": name, "fx": {}, "shift": None, "vote_extra": 0, "ban_B": False,
              "no_lie": False, "positive_if_handled": False}
        tr = {}
        for val, ab in re.findall(r"([+-]\d+)\s+(ECO|ECN|SOC)", body):
            tr[ABBR[ab]] = tr.get(ABBR[ab], 0) + int(val)
        ev["fx"] = tr
        s = re.search(r"Quadrant ([A-D]) moves 1 step toward 1", body)
        if s:
            ev["shift"] = s.group(1)
        if "Vote requires +2" in body:
            ev["vote_extra"] = 2
        if "Quadrant B" in body and "cannot choose" in body:
            ev["ban_B"] = True
        if "no lying" in body:
            ev["no_lie"] = True
        if "Breakthrough" in name:
            ev["positive_if_handled"] = True
        events.append(ev)
    return events


def load_objectives():
    objs = []
    for line in open(os.path.join(ROOT, "test_objectives.md"), encoding="utf-8"):
        pairs = re.findall(r"(ecolog\w*|economy|social)\s+(high|medium|low)", line)
        if pairs:
            objs.append([("environment" if p[0].startswith("ecolog") else p[0], p[1]) for p in pairs])
    return objs


QUAD_OPTIONS = load_quadrants()
EVENTS = load_events()
OBJECTIVES = load_objectives()


# ---- helpers -----------------------------------------------------------------------
def clamp(x, lo, hi):
    return max(lo, min(hi, x))


def dist(tracks, obj):
    d = 0
    for t, sec in obj:
        lo, hi = SECTIONS[sec]
        v = tracks[t]
        d += max(0, lo - v, v - hi)
    return d


def drift(qpos):
    out = dict.fromkeys(TRACKS, 0)
    for q, p in qpos.items():
        for t, v in QUADS[q][p].items():
            out[t] += v
    return out


def project(tracks, qpos, rounds_left):
    d = drift(qpos)
    return {t: clamp(tracks[t] + d[t] * rounds_left, 0, TRACK_MAX) for t in TRACKS}


def move(qpos, delta):
    q2 = dict(qpos)
    for q, dv in delta.items():
        q2[q] = clamp(q2[q] + dv, 1, 7)
    return q2


def make_vote_deck(rng):
    deck = []
    for _ in range(VOTE_DECK_SIZE):
        qs = rng.sample("ABCD", 2)
        d = {}
        for q in qs:
            m = 2 if rng.random() < P_MAG2 else 1
            d[q] = m * rng.choice((-1, 1))
        deck.append(d)
    return deck


def vote_gain(obj, tracks, qpos, delta, rounds_left):
    """Objective utility gain if the vote (with the given quadrant deltas) passes."""
    a = dist(project(tracks, move(qpos, delta), rounds_left), obj)
    b = dist(project(tracks, qpos, rounds_left), obj)
    return b - a      # >0 good for me


def event_gain(obj, tracks, qpos, ev, rounds_left):
    """Objective utility gain if the event is handled (vs not handled)."""
    t = dict(tracks)
    q = qpos
    if ev["positive_if_handled"]:
        h = {k: clamp(tracks[k] + v, 0, TRACK_MAX) for k, v in ev["fx"].items()}
        h = {**tracks, **h}
        return dist(project(tracks, qpos, rounds_left), obj) - dist(project(h, qpos, rounds_left), obj)
    for k, v in ev["fx"].items():
        t[k] = clamp(t[k] + v, 0, TRACK_MAX)
    if ev["shift"]:
        q = move(qpos, {ev["shift"]: -1})
    return dist(project(t, q, rounds_left), obj) - dist(project(tracks, qpos, rounds_left), obj)


# ---- strategies --------------------------------------------------------------------
STRATS = {
    # name: (coop weight, random play?)
    "random": (0.0, True),
    "cooperative": (1.0, False),
    "mixed": (0.5, False),
    "selfish": (0.0, False),
}


def choose_cards(hand, strat, s_e, s_v, rng):
    coop, rnd = STRATS[strat]
    if rnd:
        a, b = rng.sample(hand, 2)
        return a, b
    best, bs = None, -1e9
    for e, v in permutations(hand, 2):
        sc = s_e * e + s_v * v + rng.gauss(0, 0.6)
        if sc > bs:
            bs, best = sc, (e, v)
    return best


def play_game(n, strat, rng, lies=True, trust=0.6):
    coop, _ = STRATS[strat]
    ecost, vcost = EVENT_COST[n], VOTE_COST[n]
    tracks = {t: 10 for t in TRACKS}
    choose_quadrants(rng)
    qpos = dict(QSTART)
    quads_used = dict(QCHOSEN)
    objs = rng.sample(OBJECTIVES, n)
    events = EVENTS[:]
    rng.shuffle(events)
    votes = make_vote_deck(rng)
    hands = [HAND[:] for _ in range(n)]
    pres = rng.randrange(n)
    pend = {"extra": 0, "ban_B": False, "no_lie": False}
    unhandled = 0
    ev_handled = ev_total = vote_pass = 0
    lost = False
    lost_round = None
    lie_count = 0

    for r in range(ROUNDS):
        left = ROUNDS - r - 1
        ev = events.pop()
        # president draws 3 votes, picks best for themself (sees real values)
        drawn = [votes.pop() for _ in range(3)]
        allowed = [d for d in drawn if not (pend["ban_B"] and "B" in d)] or drawn
        pobj = objs[pres]
        gains = [vote_gain(pobj, tracks, qpos, d, left) for d in allowed]
        gi = max(range(len(allowed)), key=lambda i: gains[i] + rng.random() * 0.01)
        card, pg = allowed[gi], gains[gi]
        # one of the unchosen cards goes back on top, the other is discarded
        others = [d for d in drawn if d is not card]
        votes.append(others[0])
        # claim
        claim = card
        if lies and not pend["no_lie"] and pg < 0 and strat != "random":
            claim = {q: -v for q, v in card.items()}
            lie_count += 1
        # players choose cards
        e_sum = v_sum = 0
        for i in range(n):
            obj = objs[i]
            if i == pres:
                vg = vote_gain(obj, tracks, qpos, card, left)
            else:
                vg = trust * vote_gain(obj, tracks, qpos, claim, left)
            eg = event_gain(obj, tracks, qpos, ev, left)
            urgency = min(1.0, 0.5 + 0.12 * unhandled)
            s_v = clamp(vg / 3.0, -1, 1)
            s_e = coop * urgency + (1 - coop) * clamp(eg / 3.0, -1, 1)
            e, v = choose_cards(hands[i], strat, s_e, s_v, rng)
            hands[i].remove(e)
            hands[i].remove(v)
            e_sum += e
            v_sum += v
        # resolve
        passed = v_sum >= vcost + pend["extra"]
        handled = e_sum >= ecost
        pend = {"extra": 0, "ban_B": False, "no_lie": False}
        ev_total += 1
        if passed:
            vote_pass += 1
            qpos = move(qpos, card)
        if handled:
            ev_handled += 1
            if ev["positive_if_handled"]:
                for k, v in ev["fx"].items():
                    tracks[k] = clamp(tracks[k] + v, 0, TRACK_MAX)
        else:
            unhandled += 1
            if not ev["positive_if_handled"]:
                for k, v in ev["fx"].items():
                    tracks[k] = clamp(tracks[k] + v, 0, TRACK_MAX)
                if ev["shift"]:
                    qpos = move(qpos, {ev["shift"]: -1})
                pend["extra"] = ev["vote_extra"]
                pend["ban_B"] = ev["ban_B"]
                pend["no_lie"] = ev["no_lie"]
            if unhandled >= LOSS_UNHANDLED:
                lost, lost_round = True, r + 1
                break
        d = drift(qpos)
        for t in TRACKS:
            tracks[t] = clamp(tracks[t] + d[t], 0, TRACK_MAX)
        if r % 3 == 2:
            hands = [HAND[:] for _ in range(n)]
        pres = (pres + 1) % n

    wins = [(not lost) and dist(tracks, o) == 0 for o in objs]
    return {
        "lost": lost, "lost_round": lost_round, "unhandled": unhandled,
        "ev_handled": ev_handled, "ev_total": ev_total, "vote_pass": vote_pass,
        "rounds": ev_total, "wins": wins, "objs": objs, "tracks": tracks, "lies": lie_count, "quads": quads_used,
    }


def run(n, strat, games, seed, lies=True):
    rng = random.Random(seed)
    agg = defaultdict(float)
    obj_win = defaultdict(lambda: [0, 0])
    by_quad = defaultdict(lambda: [0, 0, 0, 0, 0])   # games, winners, players, lost, any track pinned
    for _ in range(games):
        g = play_game(n, strat, rng, lies=lies)
        agg["lost"] += g["lost"]
        agg["unhandled"] += g["unhandled"]
        agg["ev_handled"] += g["ev_handled"]
        agg["ev_total"] += g["ev_total"]
        agg["vote_pass"] += g["vote_pass"]
        agg["rounds"] += g["rounds"]
        agg["lost_round"] += g["lost_round"] or 0
        agg["any_winner"] += any(g["wins"])
        agg["all_winners"] += all(g["wins"])
        agg["nwin"] += sum(g["wins"])
        for t in TRACKS:
            agg["end_" + t] += g["tracks"][t]
            agg["extreme_" + t] += g["tracks"][t] in (0, TRACK_MAX)
        for o, w in zip(g["objs"], g["wins"]):
            key = tuple(o)
            obj_win[key][0] += w
            obj_win[key][1] += 1
        pinned = any(g["tracks"][t] in (0, TRACK_MAX) for t in TRACKS)
        agg["any_extreme"] += pinned
        for q in g["quads"].values():
            b = by_quad[q]
            b[0] += 1
            b[1] += sum(g["wins"])
            b[2] += len(g["wins"])
            b[3] += g["lost"]
            b[4] += pinned
    G = games
    res = {
        "loss": agg["lost"] / G,
        "unhandled": agg["unhandled"] / G,
        "handled": agg["ev_handled"] / agg["ev_total"],
        "vote_pass": agg["vote_pass"] / agg["rounds"],
        "any_winner": agg["any_winner"] / G,
        "all_winners": agg["all_winners"] / G,
        "win_per_player": agg["nwin"] / (G * n),
        "lost_round": (agg["lost_round"] / agg["lost"]) if agg["lost"] else float("nan"),
        "end": {t: agg["end_" + t] / G for t in TRACKS},
        "extreme": {t: agg["extreme_" + t] / G for t in TRACKS},
        "obj_win": obj_win,
        "any_extreme": agg["any_extreme"] / G,
        "by_quad": {q: {"games": b[0], "win_per_player": b[1] / b[2], "loss": b[3] / b[0], "pinned": b[4] / b[0]}
                    for q, b in sorted(by_quad.items())},
    }
    return res


def fmt(x):
    return f"{100 * x:5.1f}%"


def main():
    games = int(sys.argv[1]) if len(sys.argv) > 1 else 3000
    out = []
    p = out.append
    p(f"# Secret ONU simulation ({games} games per cell)\n")
    p("Loss = 5th unhandled event. 'Win/player' = player's objective met at end of round 12 and game not lost.\n")
    p("## Main table (President lies when the card hurts them, others trust claim at 60%)\n")
    p("| Players | Strategy | Loss | Unhandled ev. (avg) | Events handled | Votes passed | Win/player | >=1 winner | Everyone wins |")
    p("|---|---|---|---|---|---|---|---|---|")
    results = {}
    for n in (3, 4, 5, 6):
        for s in ("random", "cooperative", "mixed", "selfish"):
            r = run(n, s, games, seed=1000 * n + len(s))
            results[(n, s)] = r
            p(f"| {n} | {s} | {fmt(r['loss'])} | {r['unhandled']:.2f} | {fmt(r['handled'])} | {fmt(r['vote_pass'])} | "
              f"{fmt(r['win_per_player'])} | {fmt(r['any_winner'])} | {fmt(r['all_winners'])} |")
    p("\n## Effect of the President lying (strategy 'mixed')\n")
    p("| Players | Lies | Loss | Win/player | >=1 winner |")
    p("|---|---|---|---|---|")
    for n in (3, 4, 5, 6):
        for lies in (False, True):
            r = run(n, "mixed", games, seed=77 * n, lies=lies)
            p(f"| {n} | {'yes' if lies else 'no'} | {fmt(r['loss'])} | {fmt(r['win_per_player'])} | {fmt(r['any_winner'])} |")
    p("\n## Win rate by objective ('mixed', 4 players)\n")
    r = results[(4, "mixed")]
    p("| Objective | Win rate |")
    p("|---|---|")
    for k, (w, c) in sorted(r["obj_win"].items()):
        label = ", ".join(f"{t} {s}" for t, s in k)
        p(f"| {label} | {fmt(w / c) if c else 'n/a'} |")
    p("\n## Mean final tracks ('mixed')\n")
    p("| Players | environment | economy | social | % games a track ends at 0 or 20 |")
    p("|---|---|---|---|---|")
    for n in (3, 4, 5, 6):
        r = results[(n, "mixed")]
        ext = sum(r["extreme"].values()) / 3
        p(f"| {n} | {r['end']['environment']:.1f} | {r['end']['economy']:.1f} | {r['end']['social']:.1f} | {fmt(ext)} |")
    text = "\n".join(out)
    print(text)
    with open(os.path.join(HERE, "results.md"), "w", encoding="utf-8") as f:
        f.write(text + "\n")


def run_cell_json(spec):
    """Worker entry point: run one simulation cell described by a JSON dict and return a JSON-able result.
    spec = {n, strat, games, seed, lies, event_cost: {players: cost} (optional override)}"""
    for k, v in (spec.get("event_cost") or {}).items():
        EVENT_COST[int(k)] = v
    r = run(spec["n"], spec["strat"], spec["games"], spec["seed"], lies=spec.get("lies", True))
    r["obj_win"] = [[list(k), v] for k, v in r["obj_win"].items()]
    return r


def decode_cell(r):
    """Inverse of the JSON encoding done by run_cell_json."""
    r = dict(r)
    r["obj_win"] = {tuple(tuple(p) for p in k): v for k, v in r["obj_win"]}
    return r


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "--cell":
        import json
        print(json.dumps(run_cell_json(json.loads(sys.argv[2]))))
    else:
        main()

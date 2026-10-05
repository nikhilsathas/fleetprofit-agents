"""FleetProfit Uptime Desk · demo (Streamlit).

What the FleetProfit Agent can do to predict and prevent truck and trailer failures,
with an interactive week in #fleet-ops. Reuses the message engine and Slack-style
renderer from streamlit_app.py. Units, people and events are sample data.
"""
import html
import time

import streamlit as st

st.set_page_config(page_title="FleetProfit Uptime Desk", page_icon=":material/speed:", layout="wide")

import streamlit_app as base  # noqa: E402  (engine + Slack renderer; its own page only runs as main)

# ============================== SCRIPT (sample data) ==============================
PEOPLE, PLAYBOOKS, SCENES = base.PEOPLE, base.PLAYBOOKS, base.SCENES

PLAYBOOKS["uptime"] = "Uptime desk"
PEOPLE["driver131"] = ("T. Reyes", "Driver, Unit 131")

SCENES[:] = [{
    "id": "uptime", "agent": "uptime", "when": "Mon 05:30", "name": "Uptime sweep",
    "case": "UPT-1012", "case_title": "Daily uptime sweep · 70 tractors, 204 trailers", "opened": "Mon 05:30",
    "today": "TPMS alerts, fault codes, driver reports and PM lists live in different screens. Slow leaks and dead lamps are found by an inspector at the roadside, and winter prep is a scramble in November.",
    "insight": "Six failures predicted for this week, each with a date and where the truck would be, from data the fleet already has.",
    "action": "Planned every fix into a stop the truck or trailer was already making, swapped a trailer instead of moving a load, ordered winter parts once, handled a puncture in real time, checked every fix and taught the knowledge base.",
    "governed": "Fixes inside a planned stop are booked without asking · holding a pickup needs dispatch · orders over $1,500 need the manager · an unsafe tire under $500 is booked straight away and reported",
    "outcome": "Five predicted failures fixed before they happened and one handled within minutes when it came early. No extra shop visits, no load moved, two approvals, and every step in one thread.",
    "ev": [
        {"t": "clock", "v": "Mon Oct 12 · 05:30"},
        {"t": "trace", "k": "trigger", "s": "Schedule", "h": "Daily uptime sweep", "d": "05:30 every day · 70 tractors, 204 trailers"},
        {"t": "trace", "k": "read", "s": "Samsara", "h": "Tire pressure, 7 days", "d": "Tire sensors on tractors and trailers (PressurePro feed) + trailer inflation-system run time\n3 units losing pressure faster than normal"},
        {"t": "trace", "k": "read", "s": "Samsara", "h": "Fault and sensor trends", "d": "Air dryer purge rate · lamp circuits on trailers with telematics · aftertreatment · batteries"},
        {"t": "trace", "k": "read", "s": "SmartLINQ", "h": "Engine fault severity", "d": "Peterbilt remote diagnostics · 0 “service immediately” · 2 “service advised” (Unit 118 NOx sensor, Unit 201 coolant temperature)"},
        {"t": "trace", "k": "read", "s": "DVIR", "h": "Driver reports, last 48 h", "d": "9 defects · incl. Unit 188: “2 straps frayed, winch bar bent”"},
        {"t": "trace", "k": "read", "s": "Log", "h": "Fleet failure history", "d": "Past tire, air-system and lamp failures with the signals that came before them\nslow pressure loss came before 9 of the last 12 tire failures, 3–6 days ahead"},
        {"t": "trace", "k": "read", "s": "Weather", "h": "Forecast on this week’s lanes", "d": "First hard freeze Wed night: NE, IA · air systems at risk on trucks with old dryer cartridges"},
        {"t": "trace", "k": "policy", "s": "Rule", "h": "Apply failure rules", "d": "TIRE-01 slow leak → pull limit · TRL-03 inflation system can’t keep up · AIR-02 dryer freeze-up · 14 other rules checked, no match"},
        {"t": "trace", "k": "think", "s": "Agent", "h": "Project each trend forward", "d": "131: 88 psi, −3 psi/day → under the 80 psi pull limit by Thu\n2214: inflation system can’t keep up within ~5 days · 147: freeze-up risk Wed night", "slow": True},
        {"t": "trace", "k": "think", "s": "Agent", "h": "Score each issue", "d": "When will it fail? · would it fail a roadside inspection or strand the truck? · where is the unit when it does?\n→ 6 issues to act on this week, 3 more in the next 14 days"},
        {"t": "trace", "k": "read", "s": "TMS", "h": "Where each unit stops next", "d": "131 → Lancaster SC terminal tonight 19:00 · trailer 2214 → Rensselaer IN Tue 10:00 · 147 home Tue 15:00"},
        {"t": "trace", "k": "read", "s": "TMT", "h": "Shop slots and parts, 3 terminals", "d": "Grand Island · Rensselaer · Lancaster\ndrive tire 11R22.5: 2 at Lancaster · lamp pigtail: GI · dryer cartridges: 4 in stock"},
        {"t": "trace", "k": "think", "s": "Agent", "h": "Fit fixes into planned stops", "d": "5 of 6 fit a stop the unit already makes · trailer 2214 needs 45 min at Rensselaer, its pickup gives 15"},
        {"t": "trace", "k": "policy", "s": "Rule", "h": "Who approves", "d": "Inside a planned stop → book and inform · holding a pickup → dispatch · orders over $1,500 → manager"},
        {"t": "trace", "k": "act", "s": "TMT", "h": "Book 4 fixes", "d": "WO 49010–49013 · 131 at Lancaster · 2207 and 188 at Grand Island · 147 at Grand Island"},
        {"t": "msg", "ch": "fleet-ops", "time": "05:36", "b": {
            "title": "Uptime sweep: 6 failures predicted this week, 2 need a decision",
            "context": [["Tire pressure trends on every tractor and trailer with sensors", "Samsara"],
                        ["Driver reports from the last 48 h", "DVIR"],
                        ["Fleet failure history: what came before past failures", "KB"],
                        ["First hard freeze Wed night on Nebraska and Iowa lanes", "Weather"]],
            "table": {"cols": ["Unit", "What I see", "Fails in", "Where it will be", "Fix and where", "Status"],
                      "risk": [3, 3, 2, 2, 1, 1],
                      "rows": [["131", "Right-rear drive tire losing 3 psi a day, now 88 psi", "~3 days", "Thu · I-80 Iowa, 44,000 lb coils", "Lancaster terminal tonight 19:00, on arrival", "Booked"],
                               ["Trailer 2214", "Tire inflation system running 38% of drive time (normal under 5%)", "~5 days", "Wed · 600 mi loaded run", "Rensselaer drop Tue 10:00, 45 min", "Needs dispatch"],
                               ["147", "Air dryer purging 4× normal, cartridge 14 months old", "Wed night", "Grand Island yard · 14°F low", "Home time Tue 15:00, 45 min", "Booked"],
                               ["188", "Driver: 2 straps frayed, winch bar bent", "Now", "Wed · steel coils", "Swap kit at the yard Tue 05:00", "Booked"],
                               ["Trailer 2207", "Left stop-lamp circuit open since Sat", "Failed", "Tue 04:00 departure", "Grand Island yard tonight, 20 min", "Booked"],
                               ["18 tractors", "Dryer cartridges older than 12 months", "This winter", "Northern lanes", "Fold into each truck’s next PM, next 3 weeks", "Needs order"]]},
            "spark": {"title": "Unit 131 · right-rear drive tire", "unit": "psi",
                      "days": ["Fri", "Sat", "Sun", "Mon", "Tue", "Wed", "Thu"], "vals": [97, 94, 91, 88, 85, 82, 79], "now": 3,
                      "limit": 80, "limit_label": "Pull limit 80 psi", "event": 6, "event_label": "Thu: I-80 Iowa, loaded"},
            "trust": "In this fleet’s history, slow pressure loss like this came before **9 of the last 12 tire failures**, 3–6 days ahead.",
            "logic": [["TIRE-01 · Slow leak → pull limit", "Same tire losing pressure on cold readings 3 days running",
                       "97 → 88 psi in 3 days = −3 psi a day\n(88 − 80) ÷ 3 = 2.7 days → crosses Thu morning", "Fails Thu · Thursday is a loaded Iowa run → fix before Wed", "Fleet pull limit 80 psi; track record 9 of 12"],
                      ["TRL-03 · Inflation system can’t keep up", "Daily run time of the trailer’s inflation system",
                       "5% → 38% in 6 days = +5.5 points a day\nsystem stops holding pressure near 60% → about 4 days", "Fails ~Fri · next loaded run Wed → fix at Tue drop", "Supplier guidance + fleet history; 6 of 7"],
                      ["AIR-02 · Dryer freeze-up", "Purge rate, cartridge age, low on the truck’s lanes",
                       "purge 4× normal AND cartridge 14 months (limit 12) AND low 14°F (risk under 20°F)\n→ all three conditions met", "High risk Wed night → change cartridge Tue", "Dryer service interval + winter guidance; 4 of 5"]],

            "done": ["4 fixes booked inside stops the units already make", "Drive tire held at Lancaster, lamp pigtail and strap kit set out at Grand Island",
                     "3 more risks in the next 14 days (166 steer tire, 201 water pump, 118 NOx sensor) booked at their home time"],
            "options": [["Hold 2214’s pickup 30 min", "Fixed in one stop, same trailer", "Pickup Tue 11:30 instead of 11:00", "45 min"],
                        ["Swap to trailer 2231 at Rensselaer", "No delay; 2231 is inspected and ready", "Driver re-hooks and re-secures", "20 min"]],
            "rec": 0,
            "recommendation": "**Hold 2214 for 30 minutes** if the customer allows it; otherwise swap to 2231.",
            "approval": ["dana", "holding a planned pickup"],
            "fyi": ["@Joel · fixes at Grand Island tonight and Tue", "Drivers of 131, 188, 147 · told via the driver app"]}},
        {"t": "choice", "ch": "fleet-ops", "approver": "dana", "opts": [
            {"label": "Hold 2214 till 11:30", "btn": True, "primary": True, "then": [
                {"t": "set", "k": "plan2214", "v": "Trailer 2214 · Rensselaer Tue 10:00–10:45 · pickup 11:30"}]},
            {"label": "That customer won’t wait. Swap the trailer.", "who": "dana", "then": [
                {"t": "trace", "k": "think", "s": "Agent", "h": "Swap instead", "d": "Trailer 2231 at Rensselaer: inspected Sat, tires and lamps ok → driver drops 2214, hooks 2231, pickup on time · 2214 fixed after"},
                {"t": "set", "k": "plan2214", "v": "Swap to trailer 2231 at Rensselaer Tue 10:00 · 2214 fixed in the yard after"}]},
        ]},
        {"t": "trace", "k": "act", "s": "TMT", "h": "Book trailer 2214", "d": lambda S: "WO 49014 · " + S["plan2214"]},
        {"t": "trace", "k": "policy", "s": "Rule", "h": "Winter order", "d": "18 dryer cartridges × $86 = $1,548 → over the $1,500 auto-approve limit → maintenance manager"},
        {"t": "msg", "ch": "fleet-ops", "time": "05:41", "b": {
            "title": "Winter prep: 18 air dryer cartridges",
            "context": [["18 tractors have dryer cartridges older than 12 months", "TMT"],
                        ["Hard freeze from Wed night; moisture in the air system freezes lines and valves", "Weather + KB"],
                        ["Each fits into the truck’s next PM within 3 weeks, so no extra shop visits", "TMT + TMS"]],
            "options": [["Order all 18 now", "Every truck covered before the cold settles in", "$1,548 in one order", "0 extra visits"],
                        ["Order 6 now, 12 next week", "Inside the auto-approve limit", "12 trucks run the first freeze on old cartridges", "0 extra visits"]],
            "rec": 0,
            "recommendation": "**Order all 18 now** from the usual supplier, delivered to Grand Island and Rensselaer.",
            "approval": ["you", "order over $1,500"]}},
        {"t": "choice", "ch": "fleet-ops", "approver": "you", "opts": [
            {"label": "Approve $1,548 order", "btn": True, "primary": True, "then": [{"t": "set", "k": "carts", "v": "18 cartridges ordered, fitted at each truck’s next PM"}]},
            {"label": "Order 6 now", "btn": True, "then": [{"t": "set", "k": "carts", "v": "6 cartridges ordered now for the oldest units, 12 next week"}]},
        ]},
        {"t": "trace", "k": "act", "s": "Parts", "h": "Place the order", "d": lambda S: S["carts"]},
        {"t": "trace", "k": "act", "s": "TMT", "h": "Add to PM work orders", "d": "Dryer cartridge added to the next PM for each truck on the list"},
        {"t": "msg", "ch": "fleet-ops", "time": "05:44", "b": lambda S: {
            "title": "This week’s uptime plan is live",
            "list": ["**131** · drive tire · Lancaster tonight 19:00",
                     "**" + S["plan2214"].split(" · ")[0] + "** · " + " · ".join(S["plan2214"].split(" · ")[1:]),
                     "**Trailer 2207** · stop-lamp circuit · Grand Island tonight",
                     "**188** · strap kit and winch bar · Grand Island Tue 05:00",
                     "**147** · dryer cartridge, drain tanks · Grand Island Tue 15:00",
                     "**Winter** · " + S["carts"]],
            "done": ["Work orders in TMT", "Parts held at the right terminal", "Watch limits set: tire pressure, inflation-system run time, purge rate"],
            "ctx": "If a watch limit is crossed, I act straight away and post here."}},
        {"t": "msg", "ch": "fleet-ops", "who": "joel", "time": "05:47", "text": "Good. I’ll have the pigtail on 2207 before the night shift leaves."},
        {"t": "clock", "v": "Mon Oct 12 · 13:40"},
        {"t": "trace", "k": "trigger", "s": "Samsara", "h": "Watch limit crossed · Unit 131", "d": "Right-rear drive 88 → 71 psi in 40 min · the tire flagged this morning let go early · I-77 S near Rock Hill SC, 31 mi from Lancaster"},
        {"t": "trace", "k": "read", "s": "Shops", "h": "Tire service near the truck", "d": "Mobile tire service · on site in 35 min · about $420\nLancaster terminal · 31 mi · tire held there"},
        {"t": "trace", "k": "think", "s": "Agent", "h": "Re-plan", "d": "71 psi is already under the 80 psi pull limit and falling → blowout risk with a loaded trailer\nStop at the next exit and send the mobile service"},
        {"t": "trace", "k": "policy", "s": "Rule", "h": "TIRE-02 fast drop + unsafe tire rule", "d": "Drop over 10 psi in an hour → treat as failing now\nUnsafe tire and fix under $500 → book straight away, tell the manager"},
        {"t": "trace", "k": "act", "s": "Driver app", "h": "Message driver", "d": "T. Reyes: take exit 79 and park at the truck stop. Tire service is on the way, 35 min."},
        {"t": "trace", "k": "act", "s": "Shops", "h": "Book mobile tire service", "d": "On site 14:20 · replace right-rear drive · about $420 · keep the old tire"},
        {"t": "msg", "ch": "fleet-ops", "time": "13:42", "b": {
            "title": "Unit 131: the flagged tire let go early, service on the way",
            "context": [["Right-rear drive fell from 88 to 71 psi in 40 minutes", "Samsara"],
                        ["Already under the 80 psi pull limit, 31 mi from Lancaster", "Agent check"]],
            "done": ["T. Reyes stopping at exit 79", "Mobile tire service on site 14:20, about $420 (inside the unsafe-tire rule)",
                     "Lancaster tire released back to stock", "Delivery Tue 08:00 still on time"],
            "fyi": ["@You · booked under the unsafe-tire rule, no action needed", "@Dana · no change to the load"],
            "ctx": "Slow failures get predicted and planned. When one turns sudden, like this, it is handled in minutes."}},
        {"t": "msg", "ch": "fleet-ops", "who": "driver131", "time": "13:45", "text": "Parked at exit 79. Thanks for the heads-up, I hadn’t felt it yet."},
        {"t": "clock", "v": "Thu Oct 15 · 07:00"},
        {"t": "trace", "k": "trigger", "s": "Schedule", "h": "Check this week’s fixes", "d": "5 work orders closed since Monday"},
        {"t": "trace", "k": "read", "s": "Samsara", "h": "Did the fixes hold?", "d": "131 drive tires steady at 108 psi · 2214 inflation system running 3% · 2207 lamp circuits ok · 147 purge rate normal"},
        {"t": "trace", "k": "read", "s": "Samsara", "h": "After the freeze", "d": "Low of 14°F Wed night · 0 air-system freeze-ups on trucks with new cartridges"},
        {"t": "trace", "k": "act", "s": "DVIR", "h": "Close driver reports", "d": "Unit 188 straps and winch bar certified repaired"},
        {"t": "trace", "k": "act", "s": "Log", "h": "Update the rules", "d": "TIRE-01 hit (failed early, Mon) → track record 10 of 13 · TRL-03 hit → 7 of 8 · AIR-02 held through the freeze\nProposed: TRL-03 trigger lowered to 25% run time (manager to approve)"},
        {"t": "trace", "k": "think", "s": "Agent", "h": "Sweep the fleet", "d": "3 more trailers running their inflation system over 25%: 2190, 2242, 2251"},
        {"t": "trace", "k": "act", "s": "TMT", "h": "Book the 3 trailers", "d": "Each fixed at its next planned drop · no load affected"},
        {"t": "msg", "ch": "fleet-ops", "time": "07:04", "b": {
            "title": "This week’s fixes are holding, and 3 more trailers caught early",
            "context": [["Tire pressures steady, lamp circuits ok, purge rates normal", "Samsara"],
                        ["No air-system freeze-ups in Wednesday’s 14°F low", "Samsara"]],
            "done": ["All 6 issues fixed and checked", "Driver reports closed",
                     "Rule track records updated; TRL-03 change to 25% run time sent to you for approval",
                     "**Trailers 2190, 2242, 2251** booked at their next drops"],
            "fields": [["Failures predicted", "6"], ["Fixed before failing", "5"], ["Extra shop visits", "0"], ["Loads moved", "0"]],
            "fyi": ["@Joel · @Dana · weekly summary in the audit log"]}},
        {"t": "tally", "k": "minutes", "add": 180},
        {"t": "trace", "k": "done", "s": "Agent", "h": "Sweep closed", "d": "Next sweep Fri 05:30"},
    ],
}]

base.COLORS["driver131"] = "#7A6A2E"
base.INITIALS["driver131"] = "TR"
base.ACTORS["uptime"] = [("You", "Maintenance Manager", "Slack · approves orders over $1,500"),
                         ("Dana", "Dispatch", "Slack · approves pickup holds"),
                         ("Joel", "Shop lead", "Slack · kept informed"),
                         ("Drivers", "Units 131, 147, 188", "Driver app"),
                         ("3 terminals", "Grand Island · Rensselaer · Lancaster", "Work orders"),
                         ("FleetProfit Agent", "Runs the sweep", "Slack + tools")]
_fs = getattr(base, "_orig_fresh", base.fresh_state)
base._orig_fresh = _fs


def _fresh():
    s = _fs()
    s["plan2214"] = "Trailer 2214 · Rensselaer Tue 10:00–10:45 · pickup 11:30"
    s["carts"] = "18 cartridges ordered"
    return s


base.fresh_state = _fresh
h = base._h
rich = base._rich

# ============================== extra message blocks ==============================
_base_card = getattr(base, "_orig_card", base._card_html)
base._orig_card = _base_card


def _spark_svg(sp):
    W, H, L, R, T, B = 520, 150, 34, 12, 14, 26
    lo, hi = min(sp["vals"] + [sp["limit"]]) - 4, max(sp["vals"]) + 3
    x = lambda i: L + i * (W - L - R) / (len(sp["days"]) - 1)
    y = lambda v: T + (hi - v) * (H - T - B) / (hi - lo)
    pts = lambda a: " ".join(f"{x(i):.1f},{y(v):.1f}" for i, v in a)
    now = sp["now"]
    act = [(i, v) for i, v in enumerate(sp["vals"][:now + 1])]
    prj = [(i + now, v) for i, v in enumerate(sp["vals"][now:])]
    ticks = [round(lo + 4), round((lo + hi) / 2), round(hi - 3)]
    g = "".join(f'<line x1="{L}" x2="{W-R}" y1="{y(v):.1f}" y2="{y(v):.1f}" stroke="#ececec"/>'
                f'<text x="{L-6}" y="{y(v)+4:.1f}" text-anchor="end" font-size="10" fill="#7a7a7a">{v}</text>' for v in ticks)
    dots = "".join(f'<circle cx="{x(i):.1f}" cy="{y(v):.1f}" r="{4.5 if i == now else 3}" fill="{"#0E6D62" if i <= now else "#fff"}" stroke="#0E6D62" stroke-width="1.5">'
                   f'<title>{sp["days"][i]}: {v} {sp["unit"]}{" (projected)" if i > now else ""}</title></circle>' for i, v in enumerate(sp["vals"]))
    days = "".join(f'<text x="{x(i):.1f}" y="{H-8}" text-anchor="middle" font-size="10.5" fill="#7a7a7a">{d}</text>' for i, d in enumerate(sp["days"]))
    ev = sp["event"]
    return (f'<div class="sk-lbl">Projection · {h(sp["title"])}</div><div class="ox"><svg class="spk" viewBox="0 0 {W} {H}" role="img" '
            f'aria-label="{h(sp["title"])}: {sp["vals"][now]} {sp["unit"]} now, projected below the {sp["limit"]} limit">{g}'
            f'<line x1="{L}" x2="{W-R}" y1="{y(sp["limit"]):.1f}" y2="{y(sp["limit"]):.1f}" stroke="#C25A2E" stroke-width="1.5" stroke-dasharray="5 4"/>'
            f'<text x="{L+4}" y="{y(sp["limit"])+13:.1f}" font-size="10.5" fill="#9a4321">{h(sp["limit_label"])}</text>'
            f'<line x1="{x(ev):.1f}" x2="{x(ev):.1f}" y1="{T}" y2="{H-B}" stroke="#C25A2E" stroke-width="1" opacity=".5"/>'
            f'<text x="{x(ev)-4:.1f}" y="{T+9}" text-anchor="end" font-size="10.5" fill="#9a4321">{h(sp["event_label"])}</text>'
            f'<polyline points="{pts(act)}" fill="none" stroke="#0E6D62" stroke-width="2"/>'
            f'<polyline points="{pts(prj)}" fill="none" stroke="#0E6D62" stroke-width="2" stroke-dasharray="4 4"/>{dots}'
            f'<text x="{x(now):.1f}" y="{y(sp["vals"][now])-9:.1f}" text-anchor="middle" font-size="10.5" font-weight="700" fill="#1d1c1d">{sp["vals"][now]} now</text>{days}'
            '</svg></div><div class="spk-key"><span><i class="k1"></i>Measured</span><span><i class="k2"></i>Projected</span></div>')


def _extras(b):
    out = []
    if b.get("table"):
        rc = ["#cfd6d3", "#d9b36a", "#e08a3c", "#c4432f"]
        tb = b["table"]
        rows = "".join(f'<tr><td class="u" style="--rk:{rc[tb["risk"][i]]}">{h(r[0])}</td>' + "".join(f"<td>{h(c)}</td>" for c in r[1:]) + "</tr>"
                       for i, r in enumerate(tb["rows"]))
        out.append('<div class="sk-lbl">Predicted failures · soonest first</div><div class="ox"><table class="sk-opts ot"><tr>'
                   + "".join(f"<th>{h(c)}</th>" for c in tb["cols"]) + "</tr>" + rows + "</table></div>")
    if b.get("spark"):
        out.append(_spark_svg(b["spark"]))
    if b.get("trust"):
        out.append(f'<div class="trust"><b>Why I trust this:</b> {rich(b["trust"])}</div>')
    if b.get("logic"):
        rows = "".join(f'<tr><td><b>{h(r[0])}</b></td><td>{h(r[1])}</td><td class="mono">{h(r[2])}</td><td>{h(r[3])}</td><td>{h(r[4])}</td></tr>' for r in b["logic"])
        out.append('<div class="sk-lbl">How I predicted it</div><div class="ox"><table class="sk-opts ot lg"><tr><th>Rule</th><th>What it checks</th>'
                   '<th>The numbers</th><th>Result</th><th>Source · track record</th></tr>' + rows + "</table></div>")
    return "".join(out)


def _card(m):
    b = m["b"] or {}
    extra = _extras(b)
    html_ = _base_card(m)
    if not extra:
        return html_
    i = html_.find("sk-ctxl")
    j = html_.find("</ul>", i) + 5 if i >= 0 else html_.find("</div>", html_.find("sk-title")) + 6
    return html_[:j] + extra + html_[j:]


base._card_html = _card

# ============================== page content ==============================
CAPS = [
    ("Predict", "Projects every tire, air-system, battery and sensor trend forward, and says when it will fail and where the truck will be."),
    ("Prioritize", "Ranks by how soon, how serious and where: a loaded run, a long way from a shop, a roadside inspection item."),
    ("Plan around the loads", "Finds a stop the truck already makes, at the terminal or partner shop on its route, with a bay, a tech and the part."),
    ("Bundle the work", "Folds due PMs, inspections and recalls into the same visit, so one stop covers several jobs."),
    ("Act inside your rules", "Books the work order in TMT, holds parts and messages drivers. It asks dispatch or the manager only where a rule says so."),
    ("Watch and re-plan", "Keeps a watch limit on every at-risk unit until it is fixed. If a slow failure turns sudden, it acts in minutes."),
    ("Check and learn", "Confirms the fix on the data, closes the driver report, updates each rule’s track record and sweeps the fleet for the next one."),
]
ISS = [
    ("Tires", "Slow leaks and low pressure", "Heavy coil and steel loads at about 97,000 miles a year wear and puncture tires, and most tire failures start as underinflation.",
     "Tire pressure in Samsara (PressurePro sensors, where fitted)", "Projects the day it crosses your pull limit, books the fix at an earlier stop, acts at once on a fast drop"),
    ("Trailers", "Inflation systems hiding a leak", "An automatic inflation system keeps topping up a leaking trailer tire until it can’t keep up, so the leak is invisible from the cab.",
     "How long the inflation system runs each day", "Flags a system running more than usual and books the tire at the next trailer drop"),
    ("Securement", "Worn straps, chains and winch bars", "Gear wears fast on coils and lumber, and a frayed strap or too few tiedowns parks the truck.",
     "Driver reports (DVIR in Samsara) and each load’s tiedown requirement", "Swaps the kit at the yard before the load and checks the tiedown count for the cargo"),
    ("Lights", "Lamps and wiring", "Lighting faults are the most common reason trucks get pulled in for inspection, and road salt corrodes trailer plugs and harnesses.",
     "Trailer lamp-circuit data where fitted, driver reports", "Books a 20-minute fix at the next yard visit"),
    ("Air system", "Freeze-ups in winter", "Moisture in the air system freezes in Midwest cold and can lock up brake valves and lines.",
     "Air dryer purge rate, air build time, cartridge age, the forecast on each truck’s lanes", "Fits dryer cartridges into PMs before the cold, re-plans when a truck’s air system weakens"),
    ("Engine", "Faults the truck already reports", "Peterbilt 579s report engine faults with a severity (service advised, service immediately, stop engine) through SmartLINQ.",
     "SmartLINQ and Samsara fault codes", "Turns a ‘service advised’ into a booked visit before it becomes ‘service immediately’ on the road"),
    ("Mileage", "Wear from high mileage", "At about 97,000 miles a year, PMs come round every few weeks, and aftertreatment, water pumps and batteries wear faster. On a PACCAR MX-13, DPF service falls every 200,000–250,000 miles on linehaul.",
     "PM due dates in TMT, fault trends, repair history", "Bundles due work, including DPF service, into the same visit"),
]
DAYS = ["M 12", "T 13", "W 14", "T 15", "F 16", "S 17", "S 18", "M 19", "T 20", "W 21", "T 22", "F 23", "S 24", "S 25"]
FC = [("131", "Drive tire, slow leak", 2, 4, 0, "Lancaster tonight"), ("Trailer 2214", "Hidden tire leak", 3, 6, 1, "Rensselaer drop Tue"),
      ("147", "Air dryer freeze-up", 2, 3, 1, "Home time Tue"), ("129", "Battery, cold starts", 3, 9, 1, "Yard Tue night"),
      ("166", "Steer tire wear", 5, 8, 4, "Yard stop Fri"), ("201", "Water pump", 7, 12, 6, "Home time Sun"), ("118", "NOx sensor drift", 9, 13, 8, "Home time Tue 20")]
HAVE = [("Tire pressure, tractors and trailers", "Samsara, with PressurePro sensors where fitted", "Pre-trip readings in driver reports, gauge checks at each terminal visit"),
        ("Inflation-system run time, trailers", "Trailer telematics, if fitted", "Trailers with repeated “tire low” driver notes, checked at drops"),
        ("Engine faults with severity", "Peterbilt SmartLINQ and Samsara", "—"),
        ("Driver inspection reports", "Samsara DVIR", "—"),
        ("Air dryer purge, air build time", "Engine data through Samsara", "Cartridge age from TMT, changed before the first freeze"),
        ("PM, inspections, repairs, parts", "TMT", "—"), ("Loads and stops", "TMS", "Dispatch board export"),
        ("Weather on each truck’s lanes", "Public forecast", "—")]

PAGE_CSS = """
<style>
:root{--panel:#FFFFFF;--line:#DEDBD3;--muted:#5E6864;--soft:#EEF3F1;--teal:#0E6D62;--teal-deep:#073732;--amber:#C7873A;--oos:#C25A2E;--pass:#008C7A;--ink:#1D2321}
.up-lede{font-size:17px;color:var(--muted);max-width:66ch;margin:0}
.up-h{font-size:24px;font-weight:700;margin:4px 0 10px}
.up-lbl{font-size:11px;letter-spacing:.08em;text-transform:uppercase;font-weight:700;color:var(--muted)}
.up-grid{display:grid;gap:12px}
.g-prof{grid-template-columns:repeat(3,minmax(0,1fr))}
.g-caps{grid-template-columns:repeat(4,minmax(0,1fr))}
.g-iss{grid-template-columns:repeat(4,minmax(0,1fr))}
.g-2{grid-template-columns:repeat(2,minmax(0,1fr))}
.g-6{grid-template-columns:repeat(6,minmax(0,1fr))}
.g-3{grid-template-columns:repeat(3,minmax(0,1fr))}
.box{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:13px 14px;min-width:0}
.box b.big{display:block;font-size:20px;line-height:1.25}
.box .s{font-size:13px;color:var(--muted)}
.cap .n{font-family:ui-monospace,Menlo,monospace;font-size:12px;color:var(--amber);font-weight:600}
.cap h4,.iss h4,.ba h4{margin:2px 0 4px;font-size:16px;padding:0}
.cap p{margin:0;font-size:14px;color:var(--muted)}
.cap.loop{background:var(--soft);border-style:dashed}
.iss .ev{font-size:11.5px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;color:var(--muted)}
.iss dt{font-size:10.5px;letter-spacing:.06em;text-transform:uppercase;color:var(--muted);font-weight:700;margin-top:6px}
.iss dd{margin:0;font-size:13.5px}
.fc{overflow-x:auto}
.fc-grid{min-width:640px;display:grid;grid-template-columns:150px minmax(0,1fr);row-gap:6px;column-gap:10px;align-items:center}
.fc-days{display:grid;grid-template-columns:repeat(14,minmax(0,1fr));font-size:11px;color:var(--muted);text-align:center}
.fc-lane{position:relative;height:22px;background:repeating-linear-gradient(90deg,transparent 0,transparent calc(100%/14 - 1px),var(--line) calc(100%/14 - 1px),var(--line) calc(100%/14));border-radius:4px}
.fc-win{position:absolute;top:4px;height:14px;background:rgba(194,90,46,.3);border:1px solid var(--oos);border-radius:4px}
.fc-fix{position:absolute;top:2px;width:18px;height:18px;margin-left:-9px;border-radius:50%;background:var(--pass);border:2px solid #fff}
.fc-unit{font-size:13px;line-height:1.25}.fc-unit small{display:block;color:var(--muted);font-size:11.5px}
.fc-leg{display:flex;gap:16px;font-size:12.5px;color:var(--muted);flex-wrap:wrap;margin-top:8px}
.ba ul{margin:0;padding-left:18px;font-size:14px}
.ba.after{border-color:var(--teal)}
.num b{display:block;font-size:22px;font-variant-numeric:tabular-nums}.num span{font-size:12.5px;color:var(--muted)}
.wt{width:100%;border-collapse:collapse;font-size:13.5px}
.wt th{text-align:left;font-size:11.5px;text-transform:uppercase;letter-spacing:.04em;color:var(--muted);padding:8px 10px;border-bottom:1px solid var(--line)}
.wt td{padding:8px 10px;border-bottom:1px solid var(--line);vertical-align:top}
.pilot{background:var(--teal-deep);color:#EEF4F2;border-radius:12px;padding:18px 20px}
.pilot h4{margin:0 0 6px;font-size:19px;color:#fff;padding:0}.pilot p,.pilot ol{margin:0 0 6px}
.preview{background:#fff;border:1px solid #d6d3cc;border-radius:10px;padding:12px 14px;box-shadow:0 2px 10px rgba(0,0,0,.06)}
.preview .ch{font-size:12px;color:#6b6b6b;margin-bottom:6px;font-weight:700}
.ox{overflow-x:auto}
.ot td.u{font-weight:800;border-left:4px solid var(--rk);white-space:nowrap}
.ot.lg{min-width:760px}.ot.lg td.mono{font-family:ui-monospace,Menlo,monospace;font-size:11.5px;color:#333;white-space:pre-line;min-width:190px}
.spk{width:100%;min-width:420px;height:auto;display:block}
.spk-key{display:flex;gap:14px;font-size:11.5px;color:#666;margin-top:2px}
.spk-key i{display:inline-block;width:16px;height:0;border-top:2px solid #0E6D62;margin-right:5px;vertical-align:3px}.spk-key i.k2{border-top-style:dashed}
.trust{margin-top:7px;padding:6px 9px;border-radius:5px;background:#f1edf8;color:#3f2f63;font-size:13px}
.src-line{font-size:12px;color:var(--muted)}
@media (max-width:900px){.g-prof,.g-caps,.g-iss,.g-2,.g-3{grid-template-columns:minmax(0,1fr)}.g-6{grid-template-columns:repeat(2,minmax(0,1fr))}}
</style>
"""


def _box_grid(cls, inner):
    st.markdown(f'<div class="up-grid {cls}">{inner}</div>', unsafe_allow_html=True)


def _section(label, title):
    st.markdown(f'<div class="up-lbl" style="margin-top:22px">{h(label)}</div><div class="up-h">{h(title)}</div>', unsafe_allow_html=True)


# ============================== state + navigation ==============================
K = "up_"
PAGES = [("watch", "What it watches for"), ("forecast", "Mon 05:30 · 14-day forecast"),
         ("sweep", "Mon 05:30 · Uptime sweep"), ("changes", "What changes")]
SYSTEMS = ["Samsara · telematics, DVIR", "Peterbilt SmartLINQ", "TMT · API, read + write", "TMS · export", "Parts suppliers · email", "Slack / Teams"]


def _init():
    ss = st.session_state
    ss.setdefault(K + "page", -1)          # -1 = How it works
    ss.setdefault(K + "choices", [])
    ss.setdefault(K + "shown", 0)
    ss.setdefault(K + "animate", True)
    ss.setdefault(K + "speed", "Normal")
    ss.setdefault(K + "hood", False)


def _go(i):
    ss = st.session_state
    ss[K + "page"] = i
    if i >= 0 and PAGES[i][0] == "sweep":
        ss[K + "choices"] = []
        ss[K + "shown"] = 0


def _choose(i):
    st.session_state[K + "choices"].append(i)


def _sidebar(cur):
    with st.sidebar:
        st.markdown("### FleetProfit Uptime Desk")
        st.markdown('<span class="fp-eyebrow">Sample data</span>', unsafe_allow_html=True)
        st.caption("Demo fleet shaped like a regional flatbed carrier: 70 Peterbilt 579 tractors, 204 trailers, three terminals.")
        st.markdown('<div class="fp-head">The uptime desk</div>', unsafe_allow_html=True)
        st.button("How it works", key=K + "home", on_click=_go, args=(-1,), use_container_width=True,
                  type="primary" if cur == -1 else "secondary")
        for i, (_, label) in enumerate(PAGES):
            st.button(f"{i + 1}. {label}", key=f"{K}nav{i}", on_click=_go, args=(i,),
                      type="primary" if cur == i else "secondary", use_container_width=True)
        st.markdown('<div class="fp-head">Presenter</div>', unsafe_allow_html=True)
        st.toggle("Animate in real time", key=K + "animate")
        st.select_slider("Speed", ["Slow", "Normal", "Fast"], key=K + "speed")
        st.toggle("Show “Under the hood” beside the chat", key=K + "hood")
        st.markdown('<div class="fp-head">Connected through the harness (sample)</div>', unsafe_allow_html=True)
        st.markdown("".join(f'<span class="fp-chip">{h(s)}</span>' for s in SYSTEMS), unsafe_allow_html=True)


def _next(cur):
    if cur + 1 < len(PAGES):
        st.button(f"Next: {PAGES[cur + 1][1]} →", type="primary", on_click=_go, args=(cur + 1,), key=f"{K}next{cur}")
    else:
        st.button("Back to How it works", on_click=_go, args=(-1,), key=f"{K}next{cur}")


def _page_head(cur, eyebrow, title, lede=None):
    st.markdown(f'<span class="fp-eyebrow">{cur + 1} of {len(PAGES)} · {h(eyebrow)}</span>', unsafe_allow_html=True)
    st.subheader(title)
    if lede:
        st.markdown(lede)


# ============================== pages ==============================
def intro():
    st.markdown('<span class="fp-eyebrow">FleetProfit · AI agent for fleet uptime</span>', unsafe_allow_html=True)
    st.title("Catch it before the roadside")
    st.subheader("One agent, one sweep, every truck and trailer")
    st.markdown(
        "The FleetProfit Agent predicts which trucks and trailers will fail in the next two weeks, when, and where they "
        "will be when it happens. Then it fixes each one inside a stop the truck is already making, in **#fleet-ops**, "
        "and asks a person only when a load or a budget is affected. Everyone else is kept in the loop.")
    st.markdown('<div class="fp-head">What a morning message looks like</div>', unsafe_allow_html=True)
    st.markdown('<div class="preview" style="max-width:720px"><div class="ch"># fleet-ops · Mon 05:36</div><div class="sk-m" style="padding:0"><div class="sk-av" style="background:#073732">FP</div>'
                '<div style="min-width:0"><div><span class="sk-n">FleetProfit Agent</span><span class="sk-app">APP</span><span class="sk-t">Uptime desk</span></div>'
                '<div class="sk-body">Unit 131’s right-rear tire drops under the 80 psi pull limit in about <b>3 days</b>, during Thursday’s loaded run on I-80 in Iowa. '
                'Fix booked at the Lancaster terminal <b>tonight</b>, inside its planned stop. No approval needed.</div></div></div></div>', unsafe_allow_html=True)

    st.markdown('<div class="fp-head">How it works</div>', unsafe_allow_html=True)
    steps = [
        ("1 · Signals", "Watch every unit", "Tire pressure, fault codes, air-system data and driver reports from Samsara and SmartLINQ, every few minutes."),
        ("2 · Knowledge base", "Failure rules", "Rules for how each failure develops, your pull limits, PM schedules, and each rule’s track record."),
        ("3 · Agent", "Predict and plan", "Projects each trend to a failure date, finds where the unit will be, and picks a stop it already makes."),
        ("4 · Harness", "Connects the tools", "Books work orders in TMT, checks loads in the TMS, holds parts and messages drivers, with an audit log."),
        ("5 · Slack", "Approve and inform", "Asks dispatch or the manager only where a rule says so. Then it checks every fix on the data."),
    ]
    st.markdown('<div class="fp-flow">' + "".join(
        f'<div class="fp-step"><div class="n">{a}</div><b>{b}</b><span>{h(c)}</span></div>' for a, b, c in steps) + "</div>",
        unsafe_allow_html=True)

    st.markdown('<div class="fp-head">What it can do</div>', unsafe_allow_html=True)
    _box_grid("g-caps", "".join(f'<div class="box cap"><div class="n">{i+1:02d}</div><h4>{h(a)}</h4><p>{h(b)}</p></div>' for i, (a, b) in enumerate(CAPS))
              + '<div class="box cap loop"><h4>Then it starts again</h4><p>Every morning, on all 70 tractors and the trailers behind them.</p></div>')

    st.markdown('<div class="fp-head">The fleet it is built for</div>', unsafe_allow_html=True)
    facts = [("70", "power units, about 200 trailers"), ("6.8M mi", "in 2025, about 97,000 per truck"),
             ("Peterbilt 579", "tractors, with SmartLINQ remote diagnostics"), ("Samsara", "fleet telematics and driver app"),
             ("Flatbed", "metal building parts, steel coils, ag products, lumber"), ("3 terminals", "Grand Island NE · Rensselaer IN · Lancaster SC")]
    _box_grid("g-prof", "".join(f'<div class="box"><b class="big">{h(a)}</b><span class="s">{h(b)}</span></div>' for a, b in facts))
    st.markdown('<p class="src-line">From the carrier’s FMCSA registration and its own website (Peterbilt 579 and Samsara). Engine model to confirm.</p>', unsafe_allow_html=True)

    st.markdown('<div class="fp-head">Who is involved</div>', unsafe_allow_html=True)
    st.markdown(
        "| Who | Role | What the agent asks of them |\n|---|---|---|\n"
        "| You | Maintenance manager | Approves parts orders over $1,500, off-network spend and changes to failure rules |\n"
        "| Dana | Dispatcher | Approves holding a pickup; kept informed on any load at risk |\n"
        "| Joel | Shop lead | Kept informed as fixes are booked into bays |\n"
        "| Terminals | Grand Island, Rensselaer, Lancaster | Receive work orders inside planned stops |\n"
        "| Drivers | Drivers | Told where to stop and why, through the driver app |\n"
        "| FleetProfit Agent | Runs the sweep | Predicts, plans, books, asks for approval, checks every fix |")
    st.button("Start: what it watches for", type="primary", on_click=_go, args=(0,), key=K + "start")


def page_watch(cur):
    _page_head(cur, "The failures", "Seven failures that stop a flatbed fleet",
               "For each one: why it matters, the signal you already have, and what the agent does about it.")
    _box_grid("g-iss", "".join(f'<div class="box iss"><div class="ev">{h(ev)}</div><h4>{h(t)}</h4><dl><dt>Why it matters</dt><dd>{h(w)}</dd>'
                               f'<dt>Signal you already have</dt><dd>{h(sg)}</dd><dt>What the agent does</dt><dd>{h(ac)}</dd></dl></div>' for ev, t, w, sg, ac in ISS))
    st.markdown("")
    _next(cur)


def page_forecast(cur):
    _page_head(cur, "Mon 05:30 · the forecast", "The next 14 days, as the agent sees it",
               "Monday’s sweep. Each bar is when a failure is likely; each dot is the fix, booked before it. Sample units.")
    pct = lambda d: f"{d/14*100:.2f}%"
    lanes = "".join(f'<div class="fc-unit"><b>{h(u)}</b><small>{h(w)}</small></div><div class="fc-lane" title="{h(u)}: likely {DAYS[s]}–{DAYS[e]} · fixed {h(wh)}">'
                    f'<span class="fc-win" style="left:{pct(s)};width:{pct(e-s+1)}"></span><span class="fc-fix" style="left:{pct(f+0.5)}"></span></div>' for u, w, s, e, f, wh in FC)
    st.markdown(f'<div class="box fc"><div class="fc-grid"><div></div><div class="fc-days">{"".join(f"<span>{d}</span>" for d in DAYS)}</div>{lanes}</div>'
                '<div class="fc-leg"><span>▭ Likely failure window</span><span>● Fix booked, inside a planned stop</span></div></div>', unsafe_allow_html=True)
    st.markdown('<div class="fp-head">The same forecast as a table</div>', unsafe_allow_html=True)
    st.markdown("| Unit | Predicted failure | Likely window | Fix booked |\n|---|---|---|---|\n" +
                "\n".join(f"| {u} | {w} | {DAYS[s]} – {DAYS[e]} | {wh} |" for u, w, s, e, f, wh in FC))
    _next(cur)


def page_sweep(cur):
    ss = st.session_state
    sc = base.SCENES[0]
    S, log, pending = base.build(0, ss[K + "choices"])
    shown = ss[K + "shown"]
    animate = ss[K + "animate"]
    pace = {"Slow": 1.5, "Normal": 1.0, "Fast": 0.45}[ss[K + "speed"]]

    h1, h2 = st.columns([4, 1])
    with h1:
        st.markdown(f'<span class="fp-eyebrow">{cur + 1} of {len(PAGES)} · {sc["when"]} · live in #fleet-ops</span>', unsafe_allow_html=True)
        st.subheader(f"{sc['case']} · {sc['case_title']}")
    clock_ph = h2.empty()
    st.markdown('<div class="fp-actors">' + "".join(
        f'<div class="fp-actor{" agent" if a[0] == "FleetProfit Agent" else ""}"><b>{h(a[0])}</b><span>{h(a[1])} · {h(a[2])}</span></div>'
        for a in base.ACTORS["uptime"]) + "</div>", unsafe_allow_html=True)
    st.caption("Answer as Dana or as the maintenance manager with the buttons under the channel. The week runs Monday to Thursday.")

    if ss[K + "hood"]:
        left, right = st.columns([5, 2], gap="large")
        with left:
            win_ph = st.empty()
            resp = st.container()
        hood = right.container()
    else:
        win_ph = st.empty()
        resp = st.container()
        hood = st.expander("Under the hood · what the agent did, step by step, and the tools it called")
    with hood:
        st.markdown('<div class="fp-head">Under the hood · what the agent is doing</div>', unsafe_allow_html=True)
        run_ph = st.empty()
        st.markdown('<div class="fp-head">Harness · tools it called</div>', unsafe_allow_html=True)
        tools_ph = st.empty()

    items, tools, traces = [], [], []
    state = {"clock": "Mon Oct 12 · 05:30"}

    def draw(status=("work", "Agent working"), typing=False, pend=None):
        win_ph.markdown(base._window(items, sc, state["clock"], status, typing, pend), unsafe_allow_html=True)

    def draw_clock():
        clock_ph.markdown(f'<div style="text-align:right"><span class="fp-clock">{state["clock"]}</span></div>', unsafe_allow_html=True)

    def draw_run(running=False, waiting=None):
        rows = "".join(base._trace_html(t, running=(running and j == len(traces) - 1)) for j, t in enumerate(traces))
        if waiting:
            rows += f'<div class="fp-wait">Waiting for {h(waiting)}</div>'
        run_ph.markdown(f'<div class="fp-run"><div>{rows or "<div class=fp-ctx>Waiting for a trigger…</div>"}</div></div>', unsafe_allow_html=True)

    def draw_tools():
        if not tools:
            tools_ph.caption("No tools called yet.")
        else:
            tools_ph.markdown('<div class="fp-tools">' + "".join(
                f'<span class="fp-tool{" act" if k == "act" else ""}">✓ {h(n)}</span>' for n, k in tools) + "</div>", unsafe_allow_html=True)

    draw_clock(); draw(); draw_tools(); draw_run()
    for i, (kind, item) in enumerate(log):
        fresh = animate and i >= shown
        if kind == "clock":
            state["clock"] = item
            draw_clock()
            if fresh:
                draw(); time.sleep(0.4 * pace)
        elif kind == "trace":
            traces.append(item)
            if fresh:
                draw_run(running=True)
                time.sleep((1.4 if item["slow"] else 0.9 if item["k"] == "think" else 0.5) * pace)
                draw_run()
            if item["k"] in ("read", "act"):
                n = base._tool_label(item)
                if n not in ("knowledge base", "agent") and (n, item["k"]) not in tools:
                    tools.append((n, item["k"]))
                    if fresh:
                        draw_tools()
        elif kind == "msg":
            if fresh and not item["who"]:
                draw(typing=True); time.sleep(1.0 * pace)
            items.append(("msg", item))
            if fresh:
                draw(); time.sleep(0.5 * pace)
        elif kind == "choice":
            items.append(("choice", item))
            if fresh:
                draw()
    ss[K + "shown"] = len(log)

    if pending:
        an, ar = base._who(pending.get("approver", "you"))
        draw(("wait", f"Waiting on @{an} ({ar})"), pend=pending)
        draw_tools()
        draw_run(waiting=f"@{an} in #fleet-ops")
        with resp:
            st.caption(f"Respond as {an} ({ar}) in #fleet-ops")
            btns = [(i, o) for i, o in enumerate(pending["opts"]) if o.get("btn")]
            reps = [(i, o) for i, o in enumerate(pending["opts"]) if not o.get("btn")]
            if btns:
                for col, (i, o) in zip(st.columns(len(btns)), btns):
                    col.button(o["label"], key=f"{K}b{len(ss[K + 'choices'])}_{i}", on_click=_choose, args=(i,),
                               type="primary" if o.get("primary") else "secondary", use_container_width=True)
            for i, o in reps:
                n, _ = base._who(o["who"])
                st.button(f"Reply as {n}: “{o['label']}”", key=f"{K}r{len(ss[K + 'choices'])}_{i}", on_click=_choose, args=(i,), use_container_width=True)
    else:
        draw(("ok", "Resolved")); draw_tools(); draw_run()
        with resp:
            with st.container(border=True):
                st.markdown("**What just happened**")
                c1, c2, c3 = st.columns(3)
                c1.caption("INSIGHT"); c1.markdown(base._md(sc["insight"]))
                c2.caption("ACTION"); c2.markdown(base._md(sc["action"]))
                c3.caption("GOVERNED BY"); c3.markdown(base._md(sc["governed"]))
                st.caption("Today, without the agent: " + base._md(sc["today"]))
                st.success(f"**Outcome:** {base._md(sc['outcome'])}")
            b1, b2 = st.columns([1, 1])
            with b1:
                _next(cur)
            b2.button("Play the sweep again", on_click=_go, args=(cur,), key=K + "again")

    done = not pending
    st.markdown('<div class="fp-head">Impact this week</div>', unsafe_allow_html=True)
    m = st.columns(4)
    m[0].metric("Failures predicted", "6")
    m[1].metric("Fixed before failing", "5" if done else "in progress")
    m[2].metric("Approvals asked of people", len(ss[K + "choices"]))
    m[3].metric("Extra shop visits", "0")


def page_changes(cur):
    _page_head(cur, "The difference", "The maintenance manager’s week, before and after")
    before = ["Tire, fault and driver-report alerts arrive in different screens, and most wait",
              "Phone calls to dispatch and three terminals to find when a truck is free",
              "Problems surface at a roadside inspection or a breakdown, far from home",
              "Winter prep happens truck by truck, after the first freeze-up",
              "Nobody checks that a fix held until it fails again"]
    after = ["One sweep each morning predicts failures for the next 14 days, with dates",
             "Fixes are booked inside stops the trucks already make, at whichever terminal is on the route",
             "Two approvals all week, each with the options and a recommendation",
             "Winter parts ordered once and fitted at the next PM",
             "Every fix checked on the data afterwards, and the pattern used across the fleet"]
    _box_grid("g-2", f'<div class="box ba"><h4>Today</h4><ul>{"".join(f"<li>{h(x)}</li>" for x in before)}</ul></div>'
                     f'<div class="box ba after"><h4>With the agent</h4><ul>{"".join(f"<li>{h(x)}</li>" for x in after)}</ul></div>')
    st.markdown('<div class="fp-head" style="margin-top:18px">The week in numbers</div>', unsafe_allow_html=True)
    nums = [("6", "failures predicted this week"), ("5", "fixed before they failed"), ("2", "approvals asked of people"),
            ("0", "extra shop visits"), ("18", "tractors prepped for winter"), ("3", "more trailers caught by the sweep")]
    _box_grid("g-6", "".join(f'<div class="box num"><b>{a}</b><span>{h(b)}</span></div>' for a, b in nums))
    st.markdown('<div class="fp-head" style="margin-top:18px">What a roadside failure costs a fleet</div>', unsafe_allow_html=True)
    cost = [("$2,500–5,000+", "to tow a Class 8 truck, before the repair"), ("3–9×", "the cost of the same repair done as planned work"),
            ("$700–1,500", "revenue lost for each day a truck is down unplanned")]
    _box_grid("g-3", "".join(f'<div class="box num"><b>{a}</b><span>{h(b)}</span></div>' for a, b in cost))
    st.markdown('<p class="src-line">Industry figures: <a href="https://www.geotab.com/blog/cut-commercial-truck-breakdown-costs/">Geotab</a> (towing, planned vs unplanned) and '
                '<a href="https://www.ccjdigital.com/business/article/14939604/new-tech-gives-fleets-a-jumpstart-on-vehicle-fault-codes">CCJ</a> (lost revenue per day).</p>', unsafe_allow_html=True)

    st.markdown('<div class="fp-head" style="margin-top:18px">Works with what you have</div>', unsafe_allow_html=True)
    st.markdown("If Samsara and SmartLINQ already send alerts, the agent acts on them: it decides, books the work, tells people and checks the fix. Where a signal is missing, it uses what you do have.")
    st.markdown('<div class="box ox"><table class="wt"><tr><th>Signal</th><th>Where it comes from</th><th>If you don’t have it</th></tr>' +
                "".join(f"<tr><td><b>{h(a)}</b></td><td>{h(b)}</td><td>{h(c)}</td></tr>" for a, b, c in HAVE) + "</table></div>", unsafe_allow_html=True)
    st.markdown("")
    _box_grid("g-2", '<div class="box"><h4>Inside your rules</h4><ul><li>Fixes that fit a planned stop are booked automatically</li><li>Holding a pickup goes to dispatch</li>'
                     '<li>Orders and off-network spend over your limit go to the manager</li><li>An unsafe tire is fixed at once and reported</li><li>Every step is in one Slack thread and an audit log</li></ul></div>'
                     '<div class="box"><h4>Nothing to replace</h4><ul><li>TMT stays the system of record; work orders land there</li><li>Samsara and the driver app stay as they are</li>'
                     '<li>People work in Slack or Teams</li><li>Start in suggest-only mode, then switch rules on one at a time</li></ul></div>')
    st.markdown("")
    with st.container(border=True):
        st.markdown("#### Prove it on your own history first")
        st.markdown("Before anything runs live, we replay the last 90 days of your Samsara data, driver reports and TMT repair orders.\n"
                    "1. Which failures showed up in the data beforehand, and how many days earlier?\n"
                    "2. Which fixes could have fit a stop the truck was already making?\n"
                    "3. What would the agent have asked of dispatch and the manager, and how often?")
    st.caption("Interactive simulation using sample data for units, people and events. Integrations and external actions are simulated.")
    _next(cur)


# ============================== page ==============================
_init()
st.markdown(base.CSS, unsafe_allow_html=True)
st.markdown(PAGE_CSS, unsafe_allow_html=True)
_cur = st.session_state[K + "page"]
_sidebar(_cur)
if _cur < 0:
    intro()
else:
    {"watch": page_watch, "forecast": page_forecast, "sweep": page_sweep, "changes": page_changes}[PAGES[_cur][0]](_cur)

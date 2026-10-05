"""FleetProfit Agents · demo (single-file Streamlit app).

One truck, four AI agents, one week, played out in a Slack-style chat with a live
panel showing each agent's steps. All fleet data, vendors, people and amounts are
fictional sample data.
"""
import html
import time

import streamlit as st

st.set_page_config(page_title="FleetProfit Agents", page_icon=":material/local_shipping:", layout="wide")

# ============================== SCRIPT (sample data) ==============================

PEOPLE = {
    "you": ("You", "Maintenance Manager"),
    "dana": ("Dana", "Dispatch"),
    "joel": ("Joel", "Shop lead"),
    "luis": ("Luis", "Technician"),
}

AGENTS = {
    "breakdown": "Breakdown Desk",
    "auditor": "Invoice Auditor",
    "warranty": "Warranty Capture",
    "planner": "Shop Planner",
}

SYSTEMS = ["TMT · API, read", "Telematics · MCP", "TMS · export", "invoices@ mailbox", "AP · hold only", "Slack / Teams"]


def money(n):
    return "$" + format(n, ",.2f")


def fresh_state():
    return {
        "dispute": 489.5,
        "claim": 3298.0,
        "plan214": "Brake chamber, DPF check, PM-B · Thu 14:00–20:30",
        "clock": "Tue Sep 29 · 21:00",
        "tally": {"saved": 0.0, "warranty": 0.0, "decisions": 0, "minutes": 0},
    }


SCENES = [
    # ------------------------------------------------------------------ 1
    {
        "id": "breakdown", "agent": "breakdown", "when": "Tue 21:14", "name": "Breakdown",
        "today": "A driver calls at night. The manager picks a shop on the spot, without checking the truck’s history, the warranty or the delivery deadline.",
        "agent_does": "Pulls the fault history, warranty status, load deadline and nearby shops together, recommends a plan in two minutes, and sets warranty conditions before money is spent.",
        "outcome": "Truck repaired overnight, delivery kept, both approvals logged with spending limits and warranty conditions.",
        "ev": [
            {"t": "clock", "v": "Tue Sep 29 · 21:14"},
            {"t": "trace", "k": "trigger", "s": "Telematics", "h": "Derate alert · Unit 214", "d": "SPN 3251 FMI 0 · DPF differential pressure high · engine derate active · I-29 N, mile 12, Kansas City MO"},
            {"t": "trace", "k": "read", "s": "Telematics", "h": "Fault history, 30 days", "d": "SPN 3251 intermittent since Sep 2 (6 events) · 3 regens incomplete in the last 48 h"},
            {"t": "trace", "k": "read", "s": "TMT", "h": "Unit record", "d": "2022 Freightliner Cascadia · DD15 · 317,950 mi · in service Feb 2022"},
            {"t": "trace", "k": "read", "s": "TMT", "h": "Aftertreatment repair history", "d": "DPF assembly replaced Mar 4, 2026 at 271,900 mi · Hoosier Diesel Repair · RO 7714"},
            {"t": "trace", "k": "think", "s": "Warranty", "h": "Coverage check", "d": "DPF is 7 months and 46,050 mi into a 12-month vendor parts warranty → keep evidence so the cost can be claimed back"},
            {"t": "trace", "k": "read", "s": "TMS", "h": "Current load", "d": "Load 48213 · steel coil, 44,000 lb · deliver Wed 10:00, Lincoln NE (appointment) · 190 mi to go"},
            {"t": "trace", "k": "read", "s": "Shops", "h": "Service options near the truck", "d": "Freightliner dealer · 14 mi · opens 06:00\nKC Interstate Diesel (mobile) · 9 mi · can arrive 22:30\nMidway Truck Center · 22 mi · open 24 h · no aftertreatment bay"},
            {"t": "trace", "k": "think", "s": "Agent", "h": "Plan", "d": "Truck can limp 14 mi. Dealer at 06:00 → rolling ~11:00, delivery slips to ~15:00. Mobile tech tonight keeps 10:00 but costs more."},
            {"t": "trace", "k": "policy", "s": "Rule", "h": "Needs approval", "d": "Road calls over $1,500 or with off-network shops need the maintenance manager → asking in #road-calls"},
            {"t": "msg", "ch": "road-calls", "time": "21:16", "b": {
                "title": "Unit 214 derated on I-29 N, Kansas City",
                "fields": [["Fault", "DPF differential pressure high (SPN 3251)"], ["Load", "48213 · deliver Wed 10:00, Lincoln NE"],
                           ["History", "DPF replaced Mar 4 by Hoosier Diesel, inside their 12-month parts warranty"], ["Driver", "R. Alvarez · safe on the shoulder"]],
                "text": "**Recommend:** limp 14 mi to the Freightliner dealer and repair at 06:00. Delivery moves to about 15:00; I’ll ask the customer.",
                "ctx": "Option B: KC Interstate mobile tech at 22:30, est. $1,800–2,400, keeps the 10:00 delivery."}},
            {"t": "choice", "ch": "road-calls", "opts": [
                {"label": "Send to dealer", "btn": True, "primary": True, "then": [
                    {"t": "trace", "k": "act", "s": "Shops", "h": "Request dealer bay", "d": "Asked the Freightliner dealer for a 06:00 bay · Unit 214 · DPF fault"},
                    {"t": "trace", "k": "wait", "s": "Shops", "h": "Dealer reply", "d": "No bay until Thu 07:00 (two trucks ahead)", "slow": True},
                    {"t": "trace", "k": "think", "s": "Agent", "h": "Re-plan", "d": "Thu 07:00 = two-day delay and a missed appointment. Mobile tech is now the better option."},
                    {"t": "msg", "ch": "road-calls", "time": "21:24", "b": {"text": "The dealer can’t take 214 until **Thu 07:00**, which misses the delivery by two days. KC Interstate’s mobile tech (22:30) is now the better call. I’ll make them keep any removed parts so the Hoosier warranty stays claimable."}},
                    {"t": "choice", "ch": "road-calls", "opts": [{"label": "Approve mobile tech up to $2,500", "btn": True, "primary": True, "then": []}]},
                ]},
                {"label": "Mobile tech tonight", "btn": True, "then": []},
                {"label": "Customer won’t move the appointment. Get someone out tonight.", "who": "you", "then": [
                    {"t": "trace", "k": "think", "s": "Agent", "h": "Read your reply", "d": "Appointment is fixed → go with the mobile tech tonight, cap the spend"},
                ]},
            ]},
            {"t": "trace", "k": "act", "s": "Shops", "h": "Book mobile tech", "d": "KC Interstate Diesel confirmed for 22:30 · approved up to $2,500 · call before exceeding · keep removed parts and photograph them"},
            {"t": "trace", "k": "act", "s": "Driver app", "h": "Message driver", "d": "R. Alvarez: tech arriving 22:30. Stay with the truck. Photo of the dash codes please."},
            {"t": "trace", "k": "act", "s": "TMS", "h": "Update the load", "d": "Load 48213 · ETA held at Wed 10:00 · flagged at risk"},
            {"t": "msg", "ch": "road-calls", "time": "21:27", "b": {"text": "Booked: KC Interstate at 22:30, approved up to **$2,500**. They call before going over. Driver told, and load 48213 is flagged at risk in the TMS."}},
            {"t": "clock", "v": "Wed Sep 30 · 00:41"},
            {"t": "trace", "k": "trigger", "s": "Phone", "h": "Vendor call logged", "d": "KC Interstate: DPF cracked, needs replacement · revised estimate $4,500"},
            {"t": "trace", "k": "think", "s": "Warranty", "h": "Before approving", "d": "Part is under the Hoosier warranty. Replace it only if the failed DPF is kept and photographed, then claim the cost back."},
            {"t": "msg", "ch": "road-calls", "time": "00:42", "b": {"text": "KC says the DPF is cracked and needs replacing. New estimate is **$4,500**, over the $2,500 cap. Because the failed DPF is under Hoosier’s parts warranty, I’ll require KC to keep it and photograph it, and claim the cost back."}},
            {"t": "choice", "ch": "road-calls", "opts": [
                {"label": "Approve with conditions", "btn": True, "primary": True, "then": []},
                {"label": "Hold until morning", "btn": True, "then": [
                    {"t": "msg", "ch": "road-calls", "time": "00:43", "b": {"text": "Holding means about a 10-hour delay and a missed delivery, and the truck sits on the shoulder overnight. Approve with the warranty conditions instead?"}},
                    {"t": "choice", "ch": "road-calls", "opts": [{"label": "Approve with conditions", "btn": True, "primary": True, "then": []}]},
                ]},
            ]},
            {"t": "trace", "k": "act", "s": "Email", "h": "Confirm to vendor", "d": "DPF replacement approved up to $4,500 · keep the failed DPF 30 days · photos required"},
            {"t": "clock", "v": "Wed Sep 30 · 03:15"},
            {"t": "trace", "k": "read", "s": "Telematics", "h": "Unit moving again", "d": "Unit 214 left the repair site 03:10 · no active faults"},
            {"t": "trace", "k": "act", "s": "TMS", "h": "Clear the risk flag", "d": "Load 48213 · ETA Lincoln 07:40 · on time"},
            {"t": "msg", "ch": "road-calls", "time": "03:15", "b": {"text": "Unit 214 is back on the road (03:10). ETA Lincoln 07:40, so the delivery is on time. Both approvals are logged for the invoice check."}},
            {"t": "tally", "k": "minutes", "add": 30},
            {"t": "trace", "k": "done", "s": "Agent", "h": "Run complete", "d": "2 approvals logged: 21:27 ($2,500 cap) and 00:43 ($4,500, warranty conditions)"},
        ],
    },
    # ------------------------------------------------------------------ 2
    {
        "id": "invoice", "agent": "auditor", "when": "Wed 08:31", "name": "Invoice",
        "today": "The repair bill arrives as a PDF. Someone types it in and it gets paid. Nobody checks it.",
        "agent_does": "Reads the bill, matches it to what was approved, and checks it against standard labour times, duplicates, warranty, and how long telematics says the truck was really at the shop.",
        "outcome": "Invoice held, corrections sent with evidence, repair order coded in TMT, follow-up scheduled.",
        "ev": [
            {"t": "clock", "v": "Wed Sep 30 · 08:31"},
            {"t": "trace", "k": "trigger", "s": "Email", "h": "Invoice received", "d": "invoices@ · from KC Interstate Diesel · INV-20931.pdf"},
            {"t": "trace", "k": "read", "s": "Document", "h": "Read the invoice", "d": "9 lines · total $4,860.00 · Unit 214 · Sep 29"},
            {"t": "trace", "k": "read", "s": "Log", "h": "Match to the road call", "d": "RC-2291 · approved up to $2,500 at 21:27 · raised to $4,500 at 00:43 for DPF replacement"},
            {"t": "trace", "k": "think", "s": "Agent", "h": "Total vs approval", "d": "$4,860.00 is $360.00 over the $4,500 approved"},
            {"t": "trace", "k": "read", "s": "TMT", "h": "Standard labour, this engine", "d": "Fleet history, DD15 · forced regen 1.0 h (11 jobs) · DPF R&R 2.4 h (6 jobs)"},
            {"t": "trace", "k": "read", "s": "Telematics", "h": "Time at the repair site", "d": "Truck stationary at tech location 22:31 → 03:10 (4 h 39 m)\nBilled: 5.5 h labour + 2 diagnostic fees"},
            {"t": "trace", "k": "think", "s": "Agent", "h": "Duplicate check", "d": "Lines 2 and 7 · \"Diagnostic fee $185.00\" · identical"},
            {"t": "trace", "k": "read", "s": "Warranty", "h": "Part coverage", "d": "DPF $2,950.00 → claimable from Hoosier Diesel (condition logged at 00:43)"},
            {"t": "trace", "k": "policy", "s": "Rule", "h": "Hold and ask", "d": "Findings over $100 → hold payment, ask the maintenance manager"},
            {"t": "trace", "k": "act", "s": "AP", "h": "Payment hold", "d": "INV-20931 held pending review"},
            {"t": "msg", "ch": "invoices", "time": "08:33", "b": {
                "title": "INV-20931 · KC Interstate Diesel · $4,860.00",
                "fields": [["Unit", "214 · road call RC-2291"], ["Approved", "Up to $4,500.00"], ["Recommend", "Pay $4,370.50, dispute $489.50"], ["Payment", "On hold in AP"]],
                "list": ["Diagnostic fee charged twice: **$185.00**",
                         "Labour 5.5 h vs 3.4 h standard, and the truck was on site only 4 h 39 m: **$304.50** (2.1 h × $145)",
                         "DPF part $2,950.00 is under Hoosier’s warranty → sending to #warranty"],
                "quote": {"h": "Draft to billing@kcinterstate.example", "body": "Before we pay INV-20931 we need two corrections:\n1. The diagnostic fee appears twice (lines 2 and 7): $185.00.\n2. Labour of 5.5 h is above the 3.4 h standard for this job, and our telematics shows 4 h 39 m on site: 2.1 h × $145 = $304.50.\nWe will pay $4,370.50 on a revised invoice. Please keep the removed DPF for 30 days."}}},
            {"t": "choice", "ch": "invoices", "opts": [
                {"label": "Send dispute", "btn": True, "primary": True, "then": [{"t": "set", "k": "dispute", "v": 489.5}]},
                {"label": "Approve as billed", "btn": True, "then": [
                    {"t": "msg", "ch": "invoices", "time": "08:35", "b": {"text": "Before you do: paying as billed leaves **$489.50** on the table, and the $360 over the approval stays undocumented. Approve anyway?"}},
                    {"t": "choice", "ch": "invoices", "opts": [
                        {"label": "Send the dispute instead", "btn": True, "primary": True, "then": [{"t": "set", "k": "dispute", "v": 489.5}]},
                        {"label": "Approve as billed", "btn": True, "then": [{"t": "set", "k": "dispute", "v": 0}]}]},
                ]},
                {"label": "Waive the duplicate fee, they came out at 10pm. Push on labour only.", "who": "you", "then": [
                    {"t": "trace", "k": "think", "s": "Agent", "h": "Revise the dispute", "d": "Drop the duplicate fee · keep the labour correction · cite telematics on-site time"},
                    {"t": "msg", "ch": "invoices", "time": "08:36", "b": {
                        "text": "Updated. The dispute is now **$304.50** (labour only), with the on-site time from telematics as evidence. Pay $4,555.50 on the revised invoice.",
                        "quote": {"h": "Revised draft", "body": "Thanks for coming out late on Sep 29. One correction before we pay INV-20931: labour of 5.5 h is above the 3.4 h standard for this job, and our telematics shows 4 h 39 m on site. Please adjust by 2.1 h × $145 = $304.50. We will pay $4,555.50 on a revised invoice."}}},
                    {"t": "choice", "ch": "invoices", "opts": [{"label": "Send dispute", "btn": True, "primary": True, "then": [{"t": "set", "k": "dispute", "v": 304.5}]}]},
                ]},
            ]},
            {"t": "trace", "k": "act", "s": "Email", "h": "Send to the vendor", "d": lambda S: ("Dispute sent to billing@kcinterstate.example · " + money(S["dispute"])) if S["dispute"] else "No dispute · invoice approved as billed"},
            {"t": "trace", "k": "act", "s": "TMT", "h": "Create repair order", "d": "RO 48799 · Unit 214 · outside repair · coded to aftertreatment / DPF · linked to RC-2291"},
            {"t": "trace", "k": "wait", "s": "Agent", "h": "Follow-up timer", "d": lambda S: "Check for a vendor reply in 48 h" if S["dispute"] else "Release payment on due date"},
            {"t": "msg", "ch": "invoices", "time": "08:40", "b": lambda S: {"text": "Sent. INV-20931 stays on hold, RO 48799 is in TMT and coded, and I’ll follow up if KC hasn’t replied by Fri 09:00." if S["dispute"] else "Approved as billed. RO 48799 is in TMT and coded. The DPF still goes to warranty."}},
            {"t": "tally", "k": "minutes", "add": 25},
            {"t": "trace", "k": "done", "s": "Agent", "h": "Run complete", "d": "Handed the DPF to Warranty Capture"},
        ],
    },
    # ------------------------------------------------------------------ 3
    {
        "id": "warranty", "agent": "warranty", "when": "Wed 08:36", "name": "Warranty",
        "today": "The broken part goes in the bin, and nobody remembers it was replaced only 7 months ago. The warranty money is lost.",
        "agent_does": "Connects today’s repair to the earlier install, builds the evidence, drafts the claim, and tells the technician to keep the part before it is scrapped.",
        "outcome": "Two claims filed with evidence, and a failed part saved from the scrap bin.",
        "ev": [
            {"t": "clock", "v": "Wed Sep 30 · 08:36"},
            {"t": "trace", "k": "trigger", "s": "Agent", "h": "Handoff from Invoice Auditor", "d": "DPF assembly · Unit 214 · $2,950.00 under a vendor parts warranty"},
            {"t": "trace", "k": "read", "s": "Warranty", "h": "Coverage terms", "d": "Hoosier Diesel parts warranty: 12 months · parts plus labour at standard time (sample terms)"},
            {"t": "trace", "k": "read", "s": "TMT", "h": "Evidence: install", "d": "RO 7714 · Mar 4, 2026 · 271,900 mi · DPF part number on file"},
            {"t": "trace", "k": "read", "s": "Telematics", "h": "Evidence: failure", "d": "Odometer 317,950 at failure · SPN 3251 onset Sep 2 · derate Sep 29 21:14"},
            {"t": "trace", "k": "act", "s": "Email", "h": "Keep the failed part", "d": "Asked KC Interstate to hold the removed DPF 30 days and send photos"},
            {"t": "trace", "k": "act", "s": "Agent", "h": "Draft the claim", "d": "Part $2,950.00 + 2.4 h × $145 = $348.00 · total $3,298.00"},
            {"t": "msg", "ch": "warranty", "time": "08:38", "b": {
                "title": "Claim ready · Unit 214 DPF · $3,298.00",
                "fields": [["Against", "Hoosier Diesel Repair (installed Mar 4, RO 7714)"], ["Age", "7 months, 46,050 mi into a 12-month warranty"],
                           ["Evidence", "Both repair orders, odometer at install and failure, fault history, photos (requested)"], ["Deadline", "File within 30 days of failure (sample terms)"]],
                "quote": {"h": "Draft to warranty@hoosierdiesel.example", "body": "The DPF assembly you installed on Unit 214 on Mar 4, 2026 (RO 7714, 271,900 mi) failed on Sep 29 at 317,950 mi, inside your 12-month parts warranty. We claim the replacement part, $2,950.00, and 2.4 h standard labour, $348.00. Total $3,298.00. Evidence attached; the failed unit is held for inspection."}}},
            {"t": "choice", "ch": "warranty", "opts": [
                {"label": "Submit claim", "btn": True, "primary": True, "then": [{"t": "set", "k": "claim", "v": 3298.0}]},
                {"label": "Claim the full 4 h of labour KC billed. Hoosier caused this.", "who": "you", "then": [
                    {"t": "trace", "k": "think", "s": "Agent", "h": "Consistency check", "d": "We are disputing KC’s 4.0 h as above standard. Claiming 4.0 h from Hoosier contradicts our own dispute."},
                    {"t": "msg", "ch": "warranty", "time": "08:40", "b": {"text": "I’d advise against that. We’re telling KC that 4.0 h is too much, so claiming 4.0 h from Hoosier contradicts our own dispute and weakens both. A stronger claim: standard labour plus the **$395.00 road-call fee**, which their failed part caused. That makes it **$3,693.00**."}},
                    {"t": "choice", "ch": "warranty", "opts": [
                        {"label": "Claim $3,693 with road-call fee", "btn": True, "primary": True, "then": [{"t": "set", "k": "claim", "v": 3693.0}]},
                        {"label": "Keep $3,298", "btn": True, "then": [{"t": "set", "k": "claim", "v": 3298.0}]}]},
                ]},
            ]},
            {"t": "trace", "k": "act", "s": "Email", "h": "Submit the claim", "d": lambda S: "Sent to warranty@hoosierdiesel.example · " + money(S["claim"]) + " · 4 attachments"},
            {"t": "tally", "k": "warranty", "add_key": "claim"},
            {"t": "msg", "ch": "warranty", "time": "08:42", "b": lambda S: {"text": "Submitted for **" + money(S["claim"]) + "**. I’ll track Hoosier’s response and chase in 5 business days."}},
            {"t": "clock", "v": "Wed Sep 30 · 09:12"},
            {"t": "trace", "k": "trigger", "s": "TMT", "h": "Repair order opened", "d": "RO 48802 · Unit 233 · turbo actuator replacement · technician Luis R."},
            {"t": "trace", "k": "read", "s": "TMT", "h": "Unit 233", "d": "2024 Peterbilt 579 · 162,400 mi · in service Dec 2024"},
            {"t": "trace", "k": "think", "s": "Warranty", "h": "Coverage check", "d": "Inside engine warranty (sample: 2 yrs / 250,000 mi) → the old part must be kept"},
            {"t": "msg", "ch": "shop", "time": "09:13", "b": {"text": "**@Luis** heads up on RO 48802: Unit 233’s turbo actuator is still under engine warranty. Please **tag and keep the old actuator** and take two photos before it goes in the scrap bin. I’ll draft the claim."}},
            {"t": "msg", "ch": "shop", "who": "luis", "time": "09:15", "text": "Got it. Tagged and on the warranty shelf, photos are in the RO."},
            {"t": "trace", "k": "act", "s": "Agent", "h": "Draft the claim", "d": "Unit 233 · turbo actuator · $1,940.00 · photos and RO 48802 attached"},
            {"t": "msg", "ch": "warranty", "time": "09:16", "b": {"text": "Second claim drafted: Unit 233 turbo actuator, **$1,940.00**. Part tagged by Luis before scrapping. Submit?"}},
            {"t": "choice", "ch": "warranty", "opts": [{"label": "Submit claim", "btn": True, "primary": True, "then": []}]},
            {"t": "tally", "k": "warranty", "add": 1940.0},
            {"t": "tally", "k": "minutes", "add": 90},
            {"t": "trace", "k": "done", "s": "Agent", "h": "Run complete", "d": "2 claims submitted · reminders set"},
        ],
    },
    # ------------------------------------------------------------------ 4
    {
        "id": "plan", "agent": "planner", "when": "Thu 05:30", "name": "Shop plan",
        "today": "The shop lead checks four screens and phones dispatch to find out when trucks are free. Trucks with open defects go back out.",
        "agent_does": "Builds the day’s plan from faults, driver defects, PM due dates and the load schedule, asks dispatch in Slack, and re-plans when the answer changes.",
        "outcome": "Shop and dispatch agreed a plan without a phone call, work orders and parts ordered, and a new fault fitted in mid-morning.",
        "ev": [
            {"t": "clock", "v": "Thu Oct 1 · 05:30"},
            {"t": "trace", "k": "trigger", "s": "Schedule", "h": "Daily shop plan", "d": "05:30 every weekday"},
            {"t": "trace", "k": "read", "s": "Telematics", "h": "Active faults", "d": "7 units with active faults · 2 high severity"},
            {"t": "trace", "k": "read", "s": "DVIR", "h": "Open driver defects", "d": "5 open · Unit 214 brake chamber air leak (Sep 30) · Unit 187 steer tread 5/32 in"},
            {"t": "trace", "k": "read", "s": "TMT", "h": "PM due, next 7 days", "d": "9 units · Unit 152 PM-A overdue by 900 mi · Unit 214 PM-B due in 1,600 mi"},
            {"t": "trace", "k": "read", "s": "TMS", "h": "Who is home, and when", "d": "214 in Grand Island Thu 14:00 → next pickup Fri 06:00\n187 free Fri 06:00–09:30 · 152 in the yard until Fri"},
            {"t": "trace", "k": "read", "s": "TMT", "h": "Parts on hand", "d": "Brake chamber: 3 in stock · steer tires 295/75R22.5: 0"},
            {"t": "trace", "k": "think", "s": "Agent", "h": "Draft plan", "d": "214: brake chamber + post-repair DPF check + PM-B (6.5 h) from Thu 14:00\n152: PM-A Thu 16:00 · 187: steer tires Fri 06:00 (order tires)"},
            {"t": "trace", "k": "policy", "s": "Rule", "h": "Coordinate first", "d": "Keeping a truck past a planned pickup needs dispatch to agree → asking in #dispatch"},
            {"t": "msg", "ch": "dispatch", "time": "05:34", "b": {"text": "**@Dana** can Unit 214 stay in the Grand Island shop **Thu 14:00 → Fri 07:00**? It needs a brake chamber (open driver defect, an out-of-service item at roadside), a DPF check after Tuesday’s repair, and PM-B. Load 48290 is planned for a Fri 06:00 pickup."}},
            {"t": "choice", "ch": "dispatch", "opts": [
                {"label": "Need it out by Fri 05:00, the customer moved pickup up.", "who": "dana", "then": [
                    {"t": "trace", "k": "think", "s": "Agent", "h": "Re-plan", "d": "Fri 05:00 leaves 15 h. Do the safety item and DPF check (3.5 h). PM-B moves to Mon 07:00 when 214 is next home (~1,200 mi until due)."},
                    {"t": "msg", "ch": "dispatch", "time": "05:37", "b": {"text": "Works. I’ll do the brake chamber and DPF check only (3.5 h) and move PM-B to **Mon 07:00**, when 214 is next home. Out by Fri 05:00."}},
                    {"t": "set", "k": "plan214", "v": "Brake chamber, DPF check · Thu 14:00–17:30 · PM-B moved to Mon 07:00"},
                ]},
                {"label": "Fine, 214 is yours till 07:00.", "who": "dana", "then": [
                    {"t": "msg", "ch": "dispatch", "time": "05:36", "b": {"text": "Thanks. Booking all three jobs in one visit."}},
                    {"t": "set", "k": "plan214", "v": "Brake chamber, DPF check, PM-B · Thu 14:00–20:30"},
                ]},
            ]},
            {"t": "msg", "ch": "shop-plan", "time": "05:41", "b": lambda S: {
                "title": "Shop plan · Thursday, Oct 1",
                "list": ["**214** · " + S["plan214"] + " · Bay 1",
                         "**152** · PM-A, 900 mi overdue · Thu 16:00–20:00 · Bay 2",
                         "**187** · two steer tires, 5/32 in (out-of-service at 4/32) · Fri 06:00–07:30 · tires ordered for 05:30 delivery"],
                "ctx": "Watching: 118 NOx sensor drift · 201 coolant temperature (water pump under warranty) · 233 low boost (claim open)"}},
            {"t": "choice", "ch": "shop-plan", "opts": [
                {"label": "Approve plan", "btn": True, "primary": True, "then": []},
                {"label": "Bay 2 is down today. Put 152 in Bay 1 after 214.", "who": "joel", "then": [
                    {"t": "trace", "k": "think", "s": "Agent", "h": "Re-plan bays", "d": lambda S: "152 → Bay 1 at 17:30, done 21:30" if "17:30" in S["plan214"] else "152 → Bay 1 at 20:30, done 00:30 · second shift"},
                    {"t": "msg", "ch": "shop-plan", "time": "05:44", "b": lambda S: {"text": "Moved 152 to Bay 1 at 17:30, after 214. Done by 21:30." if "17:30" in S["plan214"] else "Moved 152 to Bay 1 at 20:30, after 214. That runs into second shift, done by 00:30."}},
                    {"t": "choice", "ch": "shop-plan", "opts": [{"label": "Approve plan", "btn": True, "primary": True, "then": []}]},
                ]},
            ]},
            {"t": "trace", "k": "act", "s": "TMT", "h": "Create work orders", "d": "WO 48817 (214) · WO 48818 (152) · WO 48819 (187)"},
            {"t": "trace", "k": "act", "s": "Parts", "h": "Order tires", "d": "2 × 295/75R22.5 from Platte Valley Tire · delivery Fri 05:30 · $1,180.00 (inside the auto-approve limit)"},
            {"t": "trace", "k": "act", "s": "Driver app", "h": "Driver notices", "d": "Unit 214: drop at the shop on arrival · Unit 152: keys to the bay board"},
            {"t": "msg", "ch": "shop-plan", "time": "05:46", "b": {"text": "Done: 3 work orders in TMT, tires ordered for Fri 05:30, drivers told. I’ll re-plan if anything changes."}},
            {"t": "clock", "v": "Thu Oct 1 · 11:05"},
            {"t": "trace", "k": "trigger", "s": "Telematics", "h": "New fault · Unit 109", "d": "Coolant level low · 40 mi from Grand Island · arriving ~11:50"},
            {"t": "trace", "k": "think", "s": "Agent", "h": "Does it fit?", "d": "Bay 1 is free until 214 arrives at 14:00 → top-up and pressure test (1 h)"},
            {"t": "msg", "ch": "shop-plan", "time": "11:06", "b": {"text": "**Added:** Unit 109, low coolant alert, arriving 11:50. Bay 1 is free until 214 arrives, so a 1 h pressure test fits. **@Joel** OK?"}},
            {"t": "msg", "ch": "shop-plan", "who": "joel", "time": "11:08", "text": "Yep, send it in."},
            {"t": "tally", "k": "minutes", "add": 40},
            {"t": "trace", "k": "done", "s": "Agent", "h": "Run complete", "d": "Plan live · watching for new faults until 18:00"},
        ],
    },
    # ------------------------------------------------------------------ 5
    {
        "id": "follow", "agent": "auditor", "when": "Fri 09:00", "name": "Follow-up",
        "today": "Problems get spotted, but nobody chases them to the end.",
        "agent_does": "Chases the vendor, checks the corrected bill, releases payment, totals the week in dollars, and suggests a rule from the pattern it saw.",
        "outcome": "Vendor accepted the correction, payment released, and a new rule proposed from the pattern.",
        "ev": [
            {"t": "clock", "v": "Fri Oct 2 · 09:00"},
            {"t": "trace", "k": "trigger", "s": "Timer", "h": "Follow-up due", "d": lambda S: "INV-20931 dispute sent Wed 08:40 · no reply in 48 h" if S["dispute"] else "INV-20931 approved as billed · checking vendor pattern"},
            {"t": "trace", "k": "read", "s": "Email", "h": "Vendor thread", "d": "No reply from billing@kcinterstate.example"},
            {"t": "trace", "k": "read", "s": "AP", "h": "Payment status", "d": "Held · due Oct 14 · no late-fee risk until then"},
            {"t": "trace", "k": "read", "s": "TMT", "h": "Vendor history · KC Interstate", "d": "9 invoices this quarter · 6 billed labour above standard · $1,920.00 over in total"},
            {"t": "msg", "ch": "invoices", "time": "09:01", "b": lambda S: {"text": ("No reply from KC Interstate on the INV-20931 correction (" + money(S["dispute"]) + "). Payment stays on hold until Oct 14. Also, KC has billed labour above standard on **6 of 9** invoices this quarter, $1,920.00 in total.") if S["dispute"] else "KC Interstate has billed labour above standard on **6 of 9** invoices this quarter, $1,920.00 in total. INV-20931 was approved as billed."}},
            {"t": "choice", "ch": "invoices", "opts": [
                {"label": "Send a reminder", "btn": True, "primary": True, "then": [{"t": "trace", "k": "act", "s": "Email", "h": "Reminder sent", "d": "To billing@kcinterstate.example, with the telematics on-site time attached"}]},
                {"label": "Escalate to their service manager", "btn": True, "then": [{"t": "trace", "k": "act", "s": "Email", "h": "Escalation sent", "d": "To the KC Interstate service manager, with the quarter’s 6 over-standard invoices"}]},
            ]},
            {"t": "clock", "v": "Fri Oct 2 · 14:22"},
            {"t": "trace", "k": "trigger", "s": "Email", "h": "Vendor reply", "d": "Revised invoice INV-20931-R1 attached"},
            {"t": "trace", "k": "read", "s": "Document", "h": "Check the revised invoice", "d": lambda S: "New total " + money(4860 - S["dispute"]) + " · corrections applied as requested"},
            {"t": "trace", "k": "policy", "s": "Rule", "h": "Release needs one click", "d": "Clean invoice inside the approval → manager confirms release"},
            {"t": "msg", "ch": "invoices", "time": "14:23", "b": lambda S: {"text": "KC accepted the correction. Revised invoice INV-20931-R1 is **" + money(4860 - S["dispute"]) + "** and matches. Release the payment hold?"}},
            {"t": "choice", "ch": "invoices", "opts": [{"label": "Release payment", "btn": True, "primary": True, "then": []}]},
            {"t": "trace", "k": "act", "s": "AP", "h": "Release hold", "d": lambda S: "INV-20931-R1 released for payment · " + money(4860 - S["dispute"])},
            {"t": "tally", "k": "saved", "add_key": "dispute"},
            {"t": "trace", "k": "think", "s": "Agent", "h": "Pattern", "d": "KC over standard on 6 of 9 invoices · usual gap 1–2 h"},
            {"t": "msg", "ch": "invoices", "time": "14:25", "b": {"text": "Suggestion from the pattern: for KC Interstate, require a call before they bill more than **3 h of labour**, and always audit their labour lines. Add this rule?"}},
            {"t": "choice", "ch": "invoices", "opts": [
                {"label": "Add rule", "btn": True, "primary": True, "then": [{"t": "trace", "k": "policy", "s": "Rule", "h": "Rule added", "d": "KC Interstate: pre-approval above 3.0 h labour · audit all labour lines"}]},
                {"label": "Not now", "btn": True, "then": []},
            ]},
            {"t": "tally", "k": "minutes", "add": 15},
            {"t": "msg", "ch": "invoices", "time": "14:30", "b": lambda S: {
                "title": "This week, from the agents (sample)",
                "fields": [["Saved on invoices", money(S["tally"]["saved"])], ["Warranty claimed", money(S["tally"]["warranty"])],
                           ["Decisions made in Slack", str(S["tally"]["decisions"])], ["Admin time returned (est.)", "{:.1f} h".format(S["tally"]["minutes"] / 60)]],
                "ctx": "Every action, approver and dollar is in the audit log."}},
            {"t": "trace", "k": "done", "s": "Agent", "h": "Run complete", "d": "Week summary posted"},
        ],
    },
]

DISCOVERY_QUESTIONS = [
    "Which of these four moments costs you the most today?",
    "Who would get these messages: you, the shop lead, dispatch, AP?",
    "What should the agent never do without asking?",
    "Which systems would it need to read first: TMT, telematics, the TMS?",
]


# ============================== ENGINE ==============================


def resolve(x, S):
    return x(S) if callable(x) else x


def run_scene(scene, choices, S, log):
    """Append ('clock'|'trace'|'msg'|'choice', payload) items to log.

    choices=None means 'always take the first option'.
    Returns the pending choice event if the scene stops for a decision, else None.
    """
    picks = iter(choices) if choices is not None else None
    agent = AGENTS[scene["agent"]]

    def ex(events):
        for ev in events:
            t = ev["t"]
            if t == "clock":
                S["clock"] = ev["v"]
                log.append(("clock", ev["v"]))
            elif t == "set":
                S[ev["k"]] = ev["v"]
            elif t == "tally":
                S["tally"][ev["k"]] += S[ev["add_key"]] if "add_key" in ev else ev["add"]
            elif t == "trace":
                log.append(("trace", {"k": ev["k"], "s": ev["s"], "h": ev["h"], "d": resolve(ev["d"], S), "slow": ev.get("slow", False)}))
            elif t == "msg":
                log.append(("msg", {"ch": ev["ch"], "time": ev["time"], "who": ev.get("who"), "text": ev.get("text"),
                                    "b": resolve(ev.get("b"), S), "agent": agent}))
            elif t == "choice":
                if picks is None:
                    pick = 0
                else:
                    pick = next(picks, None)
                    if pick is None:
                        return ev
                opt = ev["opts"][pick]
                S["tally"]["decisions"] += 1
                log.append(("choice", {"ch": ev["ch"], "label": opt["label"], "btn": opt.get("btn", False),
                                       "who": opt.get("who", "you")}))
                pending = ex(opt.get("then", []))
                if pending:
                    return pending
        return None

    return ex(scene["ev"])


def build(scene_idx, choices):
    """State after earlier scenes (default choices) plus the current scene so far."""
    S = fresh_state()
    for k in range(scene_idx):
        run_scene(SCENES[k], None, S, [])
    log = []
    pending = run_scene(SCENES[scene_idx], choices, S, log)
    return S, log, pending


# ============================== UI ==============================



KEY = "fp_"  # session_state prefix, so this page can sit inside a bigger app

KINDS = {
    "trigger": ("Trigger", "#C7873A"),
    "read": ("Read", "#3F7FA6"),
    "think": ("Reason", "#7A5EA8"),
    "policy": ("Rule", "#A8660F"),
    "act": ("Act", "#2F7A4F"),
    "wait": ("Wait", "#8A8F88"),
    "done": ("Done", "#2F7A4F"),
}

CSS = """
<style>
.fp-trace{border:1px solid rgba(128,128,128,.28);border-left:4px solid var(--c);border-radius:8px;
  padding:7px 10px;margin:0 0 7px 0;background:rgba(128,128,128,.04)}
.fp-trace .row{display:flex;gap:6px;align-items:center;flex-wrap:wrap}
.fp-trace .k{font-size:10.5px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;color:var(--c)}
.fp-trace .s{font-family:ui-monospace,Menlo,monospace;font-size:10.5px;border:1px solid rgba(128,128,128,.45);
  border-radius:4px;padding:0 5px}
.fp-trace .h{font-weight:700;font-size:13.5px}
.fp-trace .d{font-family:ui-monospace,Menlo,monospace;font-size:12px;opacity:.85;margin-top:3px;line-height:1.45}
.fp-trace.run .h::after{content:"";display:inline-block;width:10px;height:10px;margin-left:7px;vertical-align:-1px;
  border:2px solid rgba(128,128,128,.4);border-top-color:#C7873A;border-radius:50%;animation:fpspin .7s linear infinite}
@keyframes fpspin{to{transform:rotate(360deg)}}
.fp-head{font-size:11px;letter-spacing:.08em;text-transform:uppercase;font-weight:700;opacity:.65;margin:10px 0 6px}
.fp-clock{display:inline-block;font-family:ui-monospace,Menlo,monospace;font-weight:600;font-size:14px;
  background:#073732;color:#F8F6F3;border-radius:8px;padding:6px 12px}
.fp-chip{display:inline-block;font-family:ui-monospace,Menlo,monospace;font-size:11px;border:1px solid rgba(128,128,128,.45);
  border-radius:4px;padding:1px 6px;margin:0 4px 4px 0}
.fp-eyebrow{font-size:11px;letter-spacing:.1em;text-transform:uppercase;font-weight:700;color:#C7873A}
.fp-wait{border:1px dashed #A8660F;border-radius:8px;padding:8px 10px;font-weight:600;font-size:13px;color:#A8660F;margin-top:4px}
</style>
"""


def _md(s):
    """Escape $ so Streamlit does not read amounts as LaTeX."""
    return (s or "").replace("$", "\\$")


def _h(s):
    return html.escape(s or "").replace("$", "&#36;").replace("\n", "<br>")


def _trace_html(t, running=False):
    label, color = KINDS[t["k"]]
    return (f'<div class="fp-trace{" run" if running else ""}" style="--c:{color}"><div class="row">'
            f'<span class="k">{label}</span><span class="s">{_h(t["s"])}</span><span class="h">{_h(t["h"])}</span></div>'
            f'<div class="d">{_h(t["d"])}</div></div>')


def _render_block(b):
    if b.get("title"):
        st.markdown(f"**{_md(b['title'])}**")
    fields = b.get("fields") or []
    for i in range(0, len(fields), 2):
        cols = st.columns(2)
        for col, f in zip(cols, fields[i:i + 2]):
            with col:
                st.caption(f[0])
                st.markdown(_md(f[1]))
    if b.get("list"):
        st.markdown("\n".join(f"- {_md(x)}" for x in b["list"]))
    if b.get("text"):
        st.markdown(_md(b["text"]))
    if b.get("quote"):
        st.caption(b["quote"]["h"])
        st.code(b["quote"]["body"], language=None, wrap_lines=True)
    if b.get("ctx"):
        st.caption(_md(b["ctx"]))


def _render_msg(m):
    if m["who"]:
        name, role = PEOPLE[m["who"]]
        with st.chat_message("user", avatar=":material/person:"):
            st.markdown(f"**{name}** · {role} · :green[#{m['ch']}] · {m['time']}")
            st.markdown(_md(m["text"]))
    else:
        with st.chat_message("assistant", avatar=":material/smart_toy:"):
            st.markdown(f"**FleetProfit** · {m['agent']} · :green[#{m['ch']}] · {m['time']}")
            _render_block(m["b"] or {})


def _render_choice(c):
    if c["btn"]:
        name = PEOPLE[c["who"]][0]
        st.caption(f"✓ {name} chose “{c['label']}”")
    else:
        name, role = PEOPLE[c["who"]]
        with st.chat_message("user", avatar=":material/person:"):
            st.markdown(f"**{name}** · {role} · :green[#{c['ch']}]")
            st.markdown(_md(c["label"]))


# ---------------------------------------------------------------- state
def _init():
    ss = st.session_state
    ss.setdefault(KEY + "started", False)
    ss.setdefault(KEY + "scene", 0)
    ss.setdefault(KEY + "choices", [])
    ss.setdefault(KEY + "shown", 0)
    ss.setdefault(KEY + "animate", True)
    ss.setdefault(KEY + "speed", "Normal")


def _go(i):
    ss = st.session_state
    ss[KEY + "started"] = True
    ss[KEY + "scene"] = i
    ss[KEY + "choices"] = []
    ss[KEY + "shown"] = 0


def _choose(i):
    st.session_state[KEY + "choices"].append(i)


def _restart():
    _go(0)
    st.session_state[KEY + "started"] = False


# ---------------------------------------------------------------- page
def _sidebar(scene_idx, started):
    with st.sidebar:
        st.markdown("### FleetProfit")
        st.markdown('<span class="fp-eyebrow">Sample data</span>', unsafe_allow_html=True)
        st.caption("Demo fleet shaped like a regional flatbed carrier: 70 tractors, 204 trailers, based in Nebraska.")
        st.markdown('<div class="fp-head">The week, one truck</div>', unsafe_allow_html=True)
        for i, sc in enumerate(SCENES):
            current = started and i == scene_idx
            st.button(f"{i + 1}. {sc['when']} · {AGENTS[sc['agent']]}", key=f"{KEY}nav{i}", on_click=_go, args=(i,),
                      type="primary" if current else "secondary", use_container_width=True)
        st.markdown('<div class="fp-head">Presenter</div>', unsafe_allow_html=True)
        st.toggle("Animate agent steps", key=KEY + "animate")
        st.select_slider("Speed", ["Slow", "Normal", "Fast"], key=KEY + "speed")
        st.button("Restart", key=KEY + "restart", on_click=_restart, use_container_width=True)
        st.markdown('<div class="fp-head">Connected (sample)</div>', unsafe_allow_html=True)
        st.markdown("".join(f'<span class="fp-chip">{html.escape(s)}</span>' for s in SYSTEMS), unsafe_allow_html=True)


def _intro():
    st.markdown('<span class="fp-eyebrow">FleetProfit · AI agents for fleet maintenance</span>', unsafe_allow_html=True)
    st.title("One truck, four agents, three days")
    st.markdown(
        "FleetProfit agents read the maintenance system (TMT), telematics, the TMS and the invoice inbox, decide what "
        "needs doing, and bring each decision to the right person in Slack or Teams. People approve, push back in "
        "plain words, or let a rule handle it.")
    rows = "\n".join(f"| {sc['when']} | {AGENTS[sc['agent']]} | {_md(sc['today'])} |" for sc in SCENES)
    st.markdown("| When | Agent | The problem today |\n|---|---|---|\n" + rows)
    st.caption("On the right of each scene you see what the agent is doing as it works: what triggered it, "
               "which system it read, how it reasoned, which rule applied, and what it did.")
    st.button("Start: Tuesday 21:14 breakdown", type="primary", on_click=_go, args=(0,))


def render():
    _init()
    st.markdown(CSS, unsafe_allow_html=True)
    ss = st.session_state
    started, idx = ss[KEY + "started"], ss[KEY + "scene"]
    _sidebar(idx, started)
    if not started:
        _intro()
        return

    sc = SCENES[idx]
    S, log, pending = build(idx, ss[KEY + "choices"])
    shown = ss[KEY + "shown"]
    animate = ss[KEY + "animate"]
    pace = {"Slow": 1.5, "Normal": 1.0, "Fast": 0.45}[ss[KEY + "speed"]]

    # header
    h1, h2 = st.columns([4, 1])
    with h1:
        st.markdown(f'<span class="fp-eyebrow">Scene {idx + 1} of {len(SCENES)} · {sc["when"]}</span>', unsafe_allow_html=True)
        st.subheader(AGENTS[sc["agent"]])
    clock_ph = h2.empty()

    s1, s2 = st.columns(2)
    with s1.container(border=True):
        st.caption("TODAY")
        st.markdown(_md(sc["today"]))
    with s2.container(border=True):
        st.caption("WITH THE AGENT")
        st.markdown(_md(sc["agent_does"]))

    left, right = st.columns([3, 2], gap="large")
    with left:
        st.markdown('<div class="fp-head">Slack / Teams</div>', unsafe_allow_html=True)
    with right:
        st.markdown(f'<div class="fp-head">Agent activity · {AGENTS[sc["agent"]]}</div>', unsafe_allow_html=True)

    # replay the log; animate only what is new since the last rerun
    clock = "Tue Sep 29 · 21:00"
    clock_ph.markdown(f'<div style="text-align:right"><span class="fp-clock">{clock}</span></div>', unsafe_allow_html=True)
    for i, (kind, item) in enumerate(log):
        fresh = animate and i >= shown
        if kind == "clock":
            clock = item
            clock_ph.markdown(f'<div style="text-align:right"><span class="fp-clock">{clock}</span></div>', unsafe_allow_html=True)
            if fresh:
                time.sleep(0.3 * pace)
        elif kind == "trace":
            with right:
                if fresh:
                    ph = st.empty()
                    ph.markdown(_trace_html(item, running=True), unsafe_allow_html=True)
                    time.sleep((1.4 if item["slow"] else 0.9 if item["k"] == "think" else 0.55) * pace)
                    ph.markdown(_trace_html(item), unsafe_allow_html=True)
                else:
                    st.markdown(_trace_html(item), unsafe_allow_html=True)
        elif kind == "msg":
            with left:
                if fresh and not item["who"]:
                    with st.spinner("FleetProfit is writing…"):
                        time.sleep(0.6 * pace)
                _render_msg(item)
            if fresh:
                time.sleep(0.25 * pace)
        elif kind == "choice":
            with left:
                _render_choice(item)
    ss[KEY + "shown"] = len(log)

    # running totals
    t = S["tally"]
    m = st.columns(4)
    m[0].metric("Saved on invoices", money(t["saved"]))
    m[1].metric("Warranty claimed", money(t["warranty"]))
    m[2].metric("Decisions in Slack", t["decisions"])
    m[3].metric("Admin time (est.)", "{:.1f} h".format(t["minutes"] / 60))

    if pending:
        with right:
            st.markdown(f'<div class="fp-wait">Waiting for a decision in #{pending["ch"]}</div>', unsafe_allow_html=True)
        with left:
            btns = [(i, o) for i, o in enumerate(pending["opts"]) if o.get("btn")]
            replies = [(i, o) for i, o in enumerate(pending["opts"]) if not o.get("btn")]
            if btns:
                cols = st.columns(len(btns))
                for col, (i, o) in zip(cols, btns):
                    col.button(o["label"], key=f"{KEY}b{idx}_{len(ss[KEY + 'choices'])}_{i}", on_click=_choose, args=(i,),
                               type="primary" if o.get("primary") else "secondary", use_container_width=True)
            for i, o in replies:
                name, role = PEOPLE[o["who"]]
                st.button(f"Reply as {name} ({role}): “{o['label']}”", key=f"{KEY}r{idx}_{len(ss[KEY + 'choices'])}_{i}",
                          on_click=_choose, args=(i,), use_container_width=True)
    else:
        with left:
            st.success(f"**Outcome:** {_md(sc['outcome'])}")
            if idx + 1 < len(SCENES):
                nx = SCENES[idx + 1]
                st.button(f"Next: {nx['when']} · {AGENTS[nx['agent']]} →", type="primary", on_click=_go, args=(idx + 1,))
            else:
                with st.container(border=True):
                    st.markdown("#### Questions for your team")
                    st.markdown("\n".join(f"- {q}" for q in DISCOVERY_QUESTIONS))
                st.button("Play again from Tuesday", on_click=_go, args=(0,))


render()

"""FleetProfit Agent · demo (single-file Streamlit app).

One truck, one week, one operator channel. The FleetProfit Agent runs each case in
#fleet-ops: it pulls context, lays out options and trade-offs, recommends, asks only
the person whose approval is needed, and keeps everyone else in the loop.
All fleet data, vendors, people and amounts are fictional sample data.
"""
import html
import re
import time

import streamlit as st

st.set_page_config(page_title="FleetProfit Agent", page_icon=":material/local_shipping:", layout="wide")

# ============================== SCRIPT (sample data) ==============================

PEOPLE = {
    "you": ("You", "Maintenance Manager"),
    "dana": ("Dana", "Dispatch"),
    "joel": ("Joel", "Shop lead"),
    "luis": ("Luis", "Technician"),
}

PLAYBOOKS = {
    "breakdown": "Breakdown",
    "auditor": "Invoice check",
    "warranty": "Warranty",
    "planner": "Shop plan",
}

SYSTEMS = ["TMT · API, read + write", "Telematics · MCP", "TMS · export", "invoices@ mailbox", "AP · hold, release on approval", "Slack / Teams"]


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
        "case": "CASE-1042", "case_title": "Unit 214 derated on I-29 N, Kansas City", "opened": "21:14",
        "today": "A driver calls at night. The manager picks a shop on the spot, without the truck’s history, the warranty or the delivery deadline in front of him.",
        "insight": "Unit 214 is derated 190 mi from a 10:00 delivery, and the failing part is still under a vendor warranty.",
        "action": "Laid out three repair options with trade-offs, recommended one, booked it within a cap, and kept the driver and dispatch informed.",
        "governed": "Road calls over $1,500 need the manager · failed parts are kept for warranty",
        "outcome": "Truck back on the road at 03:10 and the delivery kept. The manager made two decisions in Slack and the agent did the rest.",
        "ev": [
            {"t": "clock", "v": "Tue Sep 29 · 21:14"},
            {"t": "trace", "k": "trigger", "s": "Telematics", "h": "Derate alert · Unit 214", "d": "SPN 3251 FMI 0 · DPF differential pressure high · engine derate active · I-29 N, mile 12, Kansas City MO"},
            {"t": "trace", "k": "read", "s": "Telematics", "h": "Fault history, 30 days", "d": "SPN 3251 intermittent since Sep 2 (6 events) · 3 regens incomplete in the last 48 h"},
            {"t": "trace", "k": "read", "s": "TMT", "h": "Unit record", "d": "2022 Freightliner Cascadia · DD15 · 317,950 mi · in service Feb 2022"},
            {"t": "trace", "k": "read", "s": "TMT", "h": "Aftertreatment repair history", "d": "DPF assembly replaced Mar 4, 2026 at 271,900 mi · Hoosier Diesel Repair · RO 7714"},
            {"t": "trace", "k": "read", "s": "Warranty", "h": "Coverage check", "d": "Vendor parts warranty, 12 months → 7 months and 46,050 mi used · claimable if the failed part is kept"},
            {"t": "trace", "k": "read", "s": "TMS", "h": "Current load", "d": "Load 48213 · steel coil, 44,000 lb · deliver Wed 10:00, Lincoln NE (appointment) · 190 mi to go"},
            {"t": "trace", "k": "read", "s": "Shops", "h": "Service options near the truck", "d": "Freightliner dealer · 14 mi · opens 06:00\nKC Interstate Diesel (mobile) · 9 mi · can arrive 22:30\nMidway Truck Center · 22 mi · open 24 h · no aftertreatment bay"},
            {"t": "trace", "k": "think", "s": "Agent", "h": "Compare options", "d": "Dealer protects warranty but delivery slips ~5 h · mobile tech keeps delivery, needs evidence kept · Midway likely needs a second tow"},
            {"t": "trace", "k": "policy", "s": "Rule", "h": "Who approves", "d": "Road calls over $1,500 or off-network shops → maintenance manager · assigning approval in #fleet-ops"},
            {"t": "msg", "ch": "fleet-ops", "time": "21:16", "b": {
                "title": "Unit 214 derated on I-29 N, Kansas City",
                "context": [["DPF pressure fault, 6 times since Sep 2, 3 failed regens in 48 h", "Telematics"],
                            ["DPF replaced Mar 4 by Hoosier Diesel, 7 months into a 12-month parts warranty", "TMT + KB"],
                            ["Load 48213 to Lincoln NE, appointment Wed 10:00, 190 mi to go", "TMS"],
                            ["Driver R. Alvarez is safe on the shoulder", "Driver app"]],
                "options": [["Freightliner dealer, 14 mi", "Warranty-friendly, opens 06:00", "Delivery slips to about 15:00", "Covered if claimed"],
                            ["KC Interstate mobile tech, 9 mi", "On site 22:30, keeps the 10:00 delivery", "Off-network; must keep the failed part", "$1,800–2,400"],
                            ["Midway Truck Center, 22 mi", "Open 24 h", "No aftertreatment bay, likely a second tow", "Unknown"]],
                "rec": 0,
                "recommendation": "**Dealer.** It protects the warranty claim on a DPF fitted in March, under 7 months ago. I’ll ask the customer to move the appointment to 15:00.",
                "approval": ["you", "road call over $1,500"],
                "fyi": ["@Dana · load 48213 is at risk", "R. Alvarez · told to stay with the truck (driver app)"]}},
            {"t": "choice", "ch": "fleet-ops", "approver": "you", "opts": [
                {"label": "Approve dealer", "btn": True, "primary": True, "then": [
                    {"t": "trace", "k": "act", "s": "Shops", "h": "Request dealer bay", "d": "Asked the Freightliner dealer for a 06:00 bay · Unit 214 · DPF fault"},
                    {"t": "trace", "k": "wait", "s": "Shops", "h": "Dealer reply", "d": "No bay until Thu 07:00 (two trucks ahead)", "slow": True},
                    {"t": "trace", "k": "think", "s": "Agent", "h": "Re-plan", "d": "Thu 07:00 = two-day delay and a missed appointment → mobile tech is now the better option"},
                    {"t": "msg", "ch": "fleet-ops", "time": "21:24", "b": {
                        "title": "Change of plan: the dealer is full",
                        "context": [["Dealer has no bay until Thu 07:00, two trucks ahead", "Dealer email"],
                                    ["That misses the Lincoln delivery by two days", "TMS"]],
                        "recommendation": "**KC Interstate tonight, capped at $2,500.** They must keep and photograph any removed parts so the Hoosier claim stays valid.",
                        "approval": ["you", "off-network vendor"]}},
                    {"t": "choice", "ch": "fleet-ops", "approver": "you", "opts": [{"label": "Approve mobile tech up to $2,500", "btn": True, "primary": True, "then": []}]},
                ]},
                {"label": "Approve mobile tech", "btn": True, "then": []},
                {"label": "Customer won’t move the appointment. Get someone out tonight.", "who": "you", "then": [
                    {"t": "trace", "k": "think", "s": "Agent", "h": "Read the reply", "d": "Appointment is fixed → mobile tech tonight, cap the spend, keep warranty evidence"},
                ]},
            ]},
            {"t": "trace", "k": "act", "s": "Shops", "h": "Book mobile tech", "d": "KC Interstate Diesel confirmed for 22:30 · cap $2,500 · call before exceeding · keep and photograph removed parts"},
            {"t": "trace", "k": "act", "s": "Driver app", "h": "Message driver", "d": "R. Alvarez: tech arriving 22:30. Stay with the truck. Photo of the dash codes please."},
            {"t": "trace", "k": "act", "s": "TMS", "h": "Update the load", "d": "Load 48213 · ETA held at Wed 10:00 · flagged at risk"},
            {"t": "msg", "ch": "fleet-ops", "time": "21:27", "b": {
                "title": "Booked",
                "done": ["KC Interstate on site 22:30, cap **$2,500**, will call before going over",
                         "R. Alvarez told via the driver app",
                         "Load 48213 flagged at risk in the TMS",
                         "Approval logged: You, 21:27"],
                "fyi": ["@Dana · delivery still on for 10:00, I’ll confirm by 04:00"]}},
            {"t": "msg", "ch": "fleet-ops", "who": "dana", "time": "21:29", "text": "Thanks. I’ll give the customer a heads-up just in case."},
            {"t": "clock", "v": "Wed Sep 30 · 00:41"},
            {"t": "trace", "k": "trigger", "s": "Phone", "h": "Vendor call logged", "d": "KC Interstate: DPF cracked, needs replacement · revised estimate $4,500"},
            {"t": "trace", "k": "read", "s": "Warranty", "h": "Can we claim it back?", "d": "Yes: Hoosier parts warranty covers the DPF if the failed unit is kept and photographed"},
            {"t": "trace", "k": "policy", "s": "Rule", "h": "Over the cap", "d": "Spend above the approved $2,500 → back to the maintenance manager"},
            {"t": "msg", "ch": "fleet-ops", "time": "00:42", "b": {
                "title": "KC needs to replace the DPF: $4,500, over the cap",
                "context": [["KC on site: DPF is cracked, sensor fix alone won’t clear the derate", "Vendor call"],
                            ["Failed DPF is inside Hoosier’s 12-month warranty: about $3,300 can be claimed back", "KB"]],
                "options": [["Approve with conditions", "Rolling by about 03:00, delivery kept", "$4,500 up front, claimed back later", "$4,500"],
                            ["Hold until morning", "No spend tonight", "Truck sits on the shoulder, delivery missed", "Dealer later"]],
                "rec": 0,
                "recommendation": "**Approve, on condition KC keeps and photographs the failed DPF.** I’ll start the warranty claim once the invoice arrives.",
                "approval": ["you", "spend above the $2,500 cap"]}},
            {"t": "choice", "ch": "fleet-ops", "approver": "you", "opts": [
                {"label": "Approve with conditions", "btn": True, "primary": True, "then": []},
                {"label": "Hold until morning", "btn": True, "then": [
                    {"t": "msg", "ch": "fleet-ops", "time": "00:43", "b": {"text": "Noted, but holding means a 10-hour delay, a missed delivery and the driver on the shoulder overnight. Approve with the warranty conditions instead?",
                                                                     "approval": ["you", "spend above the $2,500 cap"]}},
                    {"t": "choice", "ch": "fleet-ops", "approver": "you", "opts": [{"label": "Approve with conditions", "btn": True, "primary": True, "then": []}]},
                ]},
            ]},
            {"t": "trace", "k": "act", "s": "Email", "h": "Confirm to vendor", "d": "DPF replacement approved up to $4,500 · keep the failed DPF 30 days · photos required"},
            {"t": "clock", "v": "Wed Sep 30 · 03:15"},
            {"t": "trace", "k": "read", "s": "Telematics", "h": "Unit moving again", "d": "Unit 214 left the repair site 03:10 · no active faults"},
            {"t": "trace", "k": "act", "s": "TMS", "h": "Clear the risk flag", "d": "Load 48213 · ETA Lincoln 07:40 · on time"},
            {"t": "msg", "ch": "fleet-ops", "time": "03:15", "b": {
                "title": "Resolved: Unit 214 back on the road",
                "done": ["Left the repair site 03:10, no active faults", "ETA Lincoln 07:40, delivery on time",
                         "Invoice check and warranty claim queued for when KC’s bill arrives"],
                "fyi": ["@Dana · on time for 10:00", "R. Alvarez · thanks, drive safe"],
                "ctx": "Opened 21:14 · first recommendation 21:16 · 2 approvals from you in Slack"}},
            {"t": "tally", "k": "minutes", "add": 30},
            {"t": "trace", "k": "done", "s": "Agent", "h": "Case closed", "d": "2 approvals logged: 21:27 ($2,500 cap) and 00:43 ($4,500, warranty conditions)"},
        ],
    },
    # ------------------------------------------------------------------ 2
    {
        "id": "invoice", "agent": "auditor", "when": "Wed 08:31", "name": "Invoice",
        "case": "CASE-1043", "case_title": "INV-20931 · KC Interstate Diesel · $4,860.00", "opened": "08:31",
        "today": "The repair bill arrives as a PDF. Someone types it in and it gets paid. Nobody checks it.",
        "insight": "The bill has a duplicate fee and 2.1 h of labor above standard, and telematics shows the truck was on site only 4 h 39 m.",
        "action": "Put the payment on hold, set out three ways to respond, drafted the correction, and coded the repair order in TMT.",
        "governed": "Findings over $100 need approval · fleet labor standards · spend approved on the road call",
        "outcome": "Invoice checked within two minutes of arriving, payment held, correction sent with evidence, follow-up scheduled.",
        "ev": [
            {"t": "clock", "v": "Wed Sep 30 · 08:31"},
            {"t": "trace", "k": "trigger", "s": "Email", "h": "Invoice received", "d": "invoices@ · from KC Interstate Diesel · INV-20931.pdf"},
            {"t": "trace", "k": "read", "s": "Document", "h": "Read the invoice", "d": "9 lines · total $4,860.00 · Unit 214 · Sep 29"},
            {"t": "trace", "k": "read", "s": "Log", "h": "Match to the road call", "d": "CASE-1042 · approved up to $2,500 at 21:27 · raised to $4,500 at 00:43 for DPF replacement"},
            {"t": "trace", "k": "read", "s": "TMT", "h": "Standard labor, this engine", "d": "Fleet history, DD15 · forced regen 1.0 h (11 jobs) · DPF R&R 2.4 h (6 jobs)"},
            {"t": "trace", "k": "read", "s": "Telematics", "h": "Time at the repair site", "d": "Truck stationary at tech location 22:31 → 03:10 (4 h 39 m)\nBilled: 5.5 h labor + 2 diagnostic fees"},
            {"t": "trace", "k": "think", "s": "Agent", "h": "Check every line", "d": "Lines 2 and 7 identical ($185) · labor 2.1 h over standard ($304.50) · total $360 over approval"},
            {"t": "trace", "k": "read", "s": "Warranty", "h": "Part coverage", "d": "DPF $2,950.00 → claimable from Hoosier Diesel (condition logged at 00:43)"},
            {"t": "trace", "k": "act", "s": "AP", "h": "Payment hold", "d": "INV-20931 held pending review (within the agent’s rights)"},
            {"t": "trace", "k": "policy", "s": "Rule", "h": "Who approves", "d": "Findings over $100 → maintenance manager · assigning approval in #fleet-ops"},
            {"t": "msg", "ch": "fleet-ops", "time": "08:33", "b": {
                "title": "INV-20931 from KC Interstate: $4,860.00, three problems",
                "context": [["Approved on CASE-1042: up to $4,500 (raised at 00:43)", "Slack log"],
                            ["Diagnostic fee charged twice (lines 2 and 7): $185.00", "Invoice"],
                            ["Labor 5.5 h vs 3.4 h standard for a DD15, and the truck was on site only 4 h 39 m: $304.50", "TMT + telematics"],
                            ["DPF part $2,950.00 is claimable from Hoosier Diesel", "KB"]],
                "options": [["Correct both", "Recovers $489.50 with evidence", "Some friction with the vendor", "Pay $4,370.50"],
                            ["Labor only", "Goodwill for the late call-out", "Leaves $185.00 on the table", "Pay $4,555.50"],
                            ["Pay as billed", "No friction", "$489.50 lost, overspend undocumented", "Pay $4,860.00"]],
                "rec": 0,
                "recommendation": "**Correct both,** with the telematics on-site time attached. Payment is already on hold in AP.",
                "approval": ["you", "invoice findings over $100"],
                "fyi": ["AP · INV-20931 on hold until you decide"],
                "quote": {"h": "Draft to billing@kcinterstate.example", "body": "Before we pay INV-20931 we need two corrections:\n1. The diagnostic fee appears twice (lines 2 and 7): $185.00.\n2. Labor of 5.5 h is above the 3.4 h standard for this job, and our telematics shows 4 h 39 m on site: 2.1 h × $145 = $304.50.\nWe will pay $4,370.50 on a revised invoice. Please keep the removed DPF for 30 days."}}},
            {"t": "choice", "ch": "fleet-ops", "approver": "you", "opts": [
                {"label": "Approve: correct both", "btn": True, "primary": True, "then": [{"t": "set", "k": "dispute", "v": 489.5}]},
                {"label": "Pay as billed", "btn": True, "then": [
                    {"t": "msg", "ch": "fleet-ops", "time": "08:35", "b": {"text": "Before I release it: paying as billed leaves **$489.50** on the table, and the $360 over your approval stays undocumented. Still pay as billed?",
                                                                     "approval": ["you", "invoice findings over $100"]}},
                    {"t": "choice", "ch": "fleet-ops", "approver": "you", "opts": [
                        {"label": "Send the correction instead", "btn": True, "primary": True, "then": [{"t": "set", "k": "dispute", "v": 489.5}]},
                        {"label": "Pay as billed", "btn": True, "then": [{"t": "set", "k": "dispute", "v": 0}]}]},
                ]},
                {"label": "Waive the duplicate fee, they came out at 10pm. Push on labor only.", "who": "you", "then": [
                    {"t": "trace", "k": "think", "s": "Agent", "h": "Revise the correction", "d": "Drop the duplicate fee · keep the labor correction · cite telematics on-site time"},
                    {"t": "msg", "ch": "fleet-ops", "time": "08:36", "b": {
                        "text": "Done. Correction is now **$304.50** (labor only), with the on-site time as evidence. Pay $4,555.50 on the revised invoice.",
                        "quote": {"h": "Revised draft", "body": "Thanks for coming out late on Sep 29. One correction before we pay INV-20931: labor of 5.5 h is above the 3.4 h standard for this job, and our telematics shows 4 h 39 m on site. Please adjust by 2.1 h × $145 = $304.50. We will pay $4,555.50 on a revised invoice."},
                        "approval": ["you", "send to vendor"]}},
                    {"t": "choice", "ch": "fleet-ops", "approver": "you", "opts": [{"label": "Send correction", "btn": True, "primary": True, "then": [{"t": "set", "k": "dispute", "v": 304.5}]}]},
                ]},
            ]},
            {"t": "trace", "k": "act", "s": "Email", "h": "Send to the vendor", "d": lambda S: ("Correction sent to billing@kcinterstate.example · " + money(S["dispute"])) if S["dispute"] else "No correction · invoice approved as billed"},
            {"t": "trace", "k": "act", "s": "TMT", "h": "Create repair order", "d": "RO 48799 · Unit 214 · outside repair · coded to aftertreatment / DPF · linked to CASE-1042"},
            {"t": "trace", "k": "act", "s": "Agent", "h": "Open warranty case", "d": "CASE-1044 · DPF $2,950.00 against Hoosier Diesel"},
            {"t": "msg", "ch": "fleet-ops", "time": "08:40", "b": lambda S: {
                "title": "Done",
                "done": (["Correction for " + money(S["dispute"]) + " sent to KC Interstate", "Payment stays on hold until the revised invoice arrives"] if S["dispute"]
                         else ["Approved as billed, AP can release on the due date"])
                        + ["RO 48799 created in TMT and coded to aftertreatment", "Warranty claim opened: CASE-1044"],
                "fyi": ["AP · hold stays on INV-20931"] if S["dispute"] else ["AP · INV-20931 approved"],
                "ctx": "I’ll chase KC on Fri 09:00 if they haven’t replied." if S["dispute"] else ""}},
            {"t": "tally", "k": "minutes", "add": 25},
            {"t": "trace", "k": "done", "s": "Agent", "h": "Case updated", "d": "Waiting on vendor · follow-up timer set for 48 h"},
        ],
    },
    # ------------------------------------------------------------------ 3
    {
        "id": "warranty", "agent": "warranty", "when": "Wed 08:41", "name": "Warranty",
        "case": "CASE-1044", "case_title": "Warranty claim · Unit 214 DPF · Hoosier Diesel", "opened": "08:41",
        "today": "The broken part goes in the bin, and nobody remembers it was replaced only 7 months ago. The warranty money is lost.",
        "insight": "The DPF failed 7 months into a 12-month warranty, and a turbo actuator still under warranty is about to be scrapped.",
        "action": "Built the evidence, set out what to claim and why, drafted both claims, and told the technician to keep the part.",
        "governed": "OEM, engine and vendor warranty terms · only the manager submits claims",
        "outcome": "Two claims filed with evidence the same morning, and a failed part saved from the scrap bin.",
        "ev": [
            {"t": "clock", "v": "Wed Sep 30 · 08:41"},
            {"t": "trace", "k": "trigger", "s": "Agent", "h": "Case opened from the invoice check", "d": "CASE-1044 · DPF assembly · Unit 214 · $2,950.00"},
            {"t": "trace", "k": "read", "s": "Warranty", "h": "Coverage terms", "d": "Hoosier Diesel parts warranty: 12 months · parts plus labor at standard time (sample terms)"},
            {"t": "trace", "k": "read", "s": "TMT", "h": "Evidence: install", "d": "RO 7714 · Mar 4, 2026 · 271,900 mi · DPF part number on file"},
            {"t": "trace", "k": "read", "s": "Telematics", "h": "Evidence: failure", "d": "Odometer 317,950 at failure · SPN 3251 onset Sep 2 · derate Sep 29 21:14"},
            {"t": "trace", "k": "act", "s": "Email", "h": "Keep the failed part", "d": "Asked KC Interstate to hold the removed DPF 30 days and send photos"},
            {"t": "trace", "k": "think", "s": "Agent", "h": "What to claim", "d": "Part + standard labor matches the terms · road-call fee is arguable · KC’s 5.5 h would contradict our own correction"},
            {"t": "trace", "k": "policy", "s": "Rule", "h": "Who approves", "d": "Only the maintenance manager submits warranty claims"},
            {"t": "msg", "ch": "fleet-ops", "time": "08:43", "b": {
                "title": "Warranty claim ready: Unit 214 DPF against Hoosier Diesel",
                "context": [["Installed Mar 4 at 271,900 mi (RO 7714), failed Sep 29 at 317,950 mi: 7 months, 46,050 mi", "TMT + telematics"],
                            ["Terms: 12 months, parts plus labor at standard time", "KB"],
                            ["Evidence pack: both ROs, odometer readings, fault history; KC photos requested", "Harness"]],
                "options": [["Part + standard labor", "Matches the terms exactly", "Leaves the road-call fee", "$3,298.00"],
                            ["Add the road-call fee", "Their part caused the call-out", "May be contested", "$3,693.00"],
                            ["Claim KC’s 5.5 h", "Higher amount", "Contradicts our own correction to KC", "Not advised"]],
                "rec": 0,
                "recommendation": "**Part + standard labor.** It is the claim least likely to be pushed back.",
                "approval": ["you", "only the manager submits claims"],
                "quote": {"h": "Draft to warranty@hoosierdiesel.example", "body": "The DPF assembly you installed on Unit 214 on Mar 4, 2026 (RO 7714, 271,900 mi) failed on Sep 29 at 317,950 mi, inside your 12-month parts warranty. We claim the replacement part, $2,950.00, and 2.4 h standard labor, $348.00. Total $3,298.00. Evidence attached; the failed unit is held for inspection."}}},
            {"t": "choice", "ch": "fleet-ops", "approver": "you", "opts": [
                {"label": "Submit $3,298", "btn": True, "primary": True, "then": [{"t": "set", "k": "claim", "v": 3298.0}]},
                {"label": "Submit $3,693", "btn": True, "then": [{"t": "set", "k": "claim", "v": 3693.0}]},
                {"label": "Claim the full 5.5 h KC billed. Hoosier caused this.", "who": "you", "then": [
                    {"t": "trace", "k": "think", "s": "Agent", "h": "Consistency check", "d": "We told KC 5.5 h is too much. Claiming it from Hoosier undermines both."},
                    {"t": "msg", "ch": "fleet-ops", "time": "08:45", "b": {"text": "I’d advise against that. We’ve just told KC that 5.5 h is too much, so claiming 5.5 h from Hoosier weakens both cases. The stronger version is standard labor plus the **$395.00 road-call fee: $3,693.00**.",
                                                                     "approval": ["you", "only the manager submits claims"]}},
                    {"t": "choice", "ch": "fleet-ops", "approver": "you", "opts": [
                        {"label": "Submit $3,693", "btn": True, "primary": True, "then": [{"t": "set", "k": "claim", "v": 3693.0}]},
                        {"label": "Submit $3,298", "btn": True, "then": [{"t": "set", "k": "claim", "v": 3298.0}]}]},
                ]},
            ]},
            {"t": "trace", "k": "act", "s": "Email", "h": "Submit the claim", "d": lambda S: "Sent to warranty@hoosierdiesel.example · " + money(S["claim"]) + " · 4 attachments"},
            {"t": "tally", "k": "warranty", "add_key": "claim"},
            {"t": "msg", "ch": "fleet-ops", "time": "08:47", "b": lambda S: {
                "title": "Claim submitted",
                "done": ["Claim for **" + money(S["claim"]) + "** sent to Hoosier Diesel with 4 attachments",
                         "KC asked to hold the failed DPF for 30 days", "Reminder set: chase Hoosier in 5 business days"]}},
            {"t": "clock", "v": "Wed Sep 30 · 09:12"},
            {"t": "trace", "k": "trigger", "s": "TMT", "h": "Repair order opened", "d": "RO 48802 · Unit 233 · turbo actuator replacement · technician Luis R."},
            {"t": "trace", "k": "read", "s": "TMT", "h": "Unit 233", "d": "2024 Peterbilt 579 · 162,400 mi · in service Dec 2024"},
            {"t": "trace", "k": "read", "s": "Warranty", "h": "Coverage check", "d": "Inside engine warranty (sample: 2 yrs / 250,000 mi) → the old part must be kept"},
            {"t": "msg", "ch": "fleet-ops", "time": "09:13", "b": {
                "title": "Heads-up on RO 48802 before the part is scrapped",
                "context": [["Unit 233 turbo actuator is being replaced now", "TMT"],
                            ["Truck is 1.8 years and 162,400 mi into a 2-year / 250,000 mi engine warranty", "KB"]],
                "text": "**@Luis** please tag and keep the old actuator and take two photos. I’ll draft the claim."}},
            {"t": "msg", "ch": "fleet-ops", "who": "luis", "time": "09:15", "text": "Got it. Tagged and on the warranty shelf, photos are in the RO."},
            {"t": "trace", "k": "act", "s": "Agent", "h": "Draft the claim", "d": "Unit 233 · turbo actuator · $1,940.00 · photos and RO 48802 attached"},
            {"t": "msg", "ch": "fleet-ops", "time": "09:16", "b": {
                "title": "Second claim ready: Unit 233 turbo actuator, $1,940.00",
                "context": [["Part tagged and photographed by Luis", "Slack"], ["Engine warranty terms (sample)", "KB"]],
                "approval": ["you", "only the manager submits claims"]}},
            {"t": "choice", "ch": "fleet-ops", "approver": "you", "opts": [{"label": "Submit $1,940", "btn": True, "primary": True, "then": []}]},
            {"t": "tally", "k": "warranty", "add": 1940.0},
            {"t": "tally", "k": "minutes", "add": 90},
            {"t": "trace", "k": "done", "s": "Agent", "h": "Claims filed", "d": "2 claims submitted · reminders set"},
        ],
    },
    # ------------------------------------------------------------------ 4
    {
        "id": "plan", "agent": "planner", "when": "Thu 05:30", "name": "Shop plan",
        "case": "PLAN-THU", "case_title": "Shop plan · Thursday, Oct 1 · Grand Island", "opened": "05:30",
        "today": "The shop lead checks four screens and phones dispatch to find out when trucks are free. Trucks with open defects go back out.",
        "insight": "Three trucks need the shop, and each has a gap between loads.",
        "action": "Proposed the plan, got dispatch and the shop lead to agree in Slack, created work orders, ordered tires inside the limit, and fitted in a new fault.",
        "governed": "Holding a truck past a pickup needs dispatch · the shop lead owns the plan · parts orders inside the auto-approve limit",
        "outcome": "Shop and dispatch agreed the day without a phone call. Work orders, parts and driver notices went out in one step.",
        "ev": [
            {"t": "clock", "v": "Thu Oct 1 · 05:30"},
            {"t": "trace", "k": "trigger", "s": "Schedule", "h": "Daily shop plan", "d": "05:30 every weekday"},
            {"t": "trace", "k": "read", "s": "Telematics", "h": "Active faults", "d": "7 units with active faults · 2 high severity"},
            {"t": "trace", "k": "read", "s": "DVIR", "h": "Open driver defects", "d": "5 open · Unit 214 brake chamber air leak (Sep 30) · Unit 187 steer tread 5/32 in"},
            {"t": "trace", "k": "read", "s": "TMT", "h": "PM due, next 7 days", "d": "9 units · Unit 152 PM-A overdue by 900 mi · Unit 214 PM-B due in 1,600 mi"},
            {"t": "trace", "k": "read", "s": "TMS", "h": "Who is home, and when", "d": "214 in Grand Island Thu 14:00 → next pickup Fri 06:00\n187 free Fri 06:00–09:30 · 152 in the yard until Fri"},
            {"t": "trace", "k": "read", "s": "TMT", "h": "Parts on hand", "d": "Brake chamber: 3 in stock · steer tires 295/75R22.5: 0"},
            {"t": "trace", "k": "think", "s": "Agent", "h": "Draft the plan", "d": "Out-of-service items first, then overdue PM · fit each truck into its gap between loads"},
            {"t": "trace", "k": "policy", "s": "Rule", "h": "Who agrees", "d": "Holding 214 past a planned pickup needs dispatch · the shop lead approves the plan"},
            {"t": "msg", "ch": "fleet-ops", "time": "05:34", "b": {
                "title": "Thursday’s shop plan: 3 trucks, one question for dispatch",
                "context": [["214: brake chamber leak (an out-of-service item at roadside), DPF check after Tuesday, PM-B due in 1,600 mi", "DVIR + TMT"],
                            ["152: PM-A 900 mi overdue · 187: steer tread 5/32 in, limit is 4/32", "TMT + DVIR"],
                            ["214 home 14:00, next pickup Fri 06:00 · 187 free Fri 06:00–09:30", "TMS"],
                            ["Steer tires out of stock; brake chamber in stock", "TMT"]],
                "options": [["All three jobs on 214 in one visit", "One visit, PM done early", "Needs 214 until Fri 07:00", "6.5 h"],
                            ["Safety items only on 214", "Ready for the Fri 06:00 pickup", "Second visit for PM-B on Mon", "3.5 h"]],
                "rec": 0,
                "recommendation": "**One visit for 214** if dispatch can push the pickup to 07:00. 152 goes into Bay 2 at 16:00, 187 gets tires Fri 06:00.",
                "approval": ["dana", "holding 214 past a planned pickup"]}},
            {"t": "choice", "ch": "fleet-ops", "approver": "dana", "opts": [
                {"label": "Need it out by Fri 05:00, the customer moved pickup up.", "who": "dana", "then": [
                    {"t": "trace", "k": "think", "s": "Agent", "h": "Re-plan", "d": "Fri 05:00 leaves 15 h → safety item and DPF check only (3.5 h) · PM-B to Mon 07:00 when 214 is next home"},
                    {"t": "set", "k": "plan214", "v": "Brake chamber, DPF check · Thu 14:00–17:30 · PM-B moved to Mon 07:00"},
                ]},
                {"label": "Fine, 214 is yours till 07:00.", "who": "dana", "then": [
                    {"t": "set", "k": "plan214", "v": "Brake chamber, DPF check, PM-B · Thu 14:00–20:30"},
                ]},
            ]},
            {"t": "msg", "ch": "fleet-ops", "time": "05:38", "b": lambda S: {
                "title": "Plan updated with dispatch’s answer",
                "list": ["**214** · " + S["plan214"] + " · Bay 1",
                         "**152** · PM-A, 900 mi overdue · Thu 16:00–20:00 · Bay 2",
                         "**187** · two steer tires · Fri 06:00–07:30 · tires ordered for 05:30 delivery"],
                "approval": ["joel", "the shop lead owns the plan"],
                "fyi": ["@Dana · 214 " + ("out by Fri 05:00" if "17:30" in S["plan214"] else "out by Fri 07:00")],
                "ctx": "Watching: 118 NOx sensor drift · 201 coolant temperature (water pump under warranty) · 233 low boost (claim open)"}},
            {"t": "choice", "ch": "fleet-ops", "approver": "joel", "opts": [
                {"label": "Approve plan", "btn": True, "primary": True, "then": []},
                {"label": "Bay 2 is down today. Put 152 in Bay 1 after 214.", "who": "joel", "then": [
                    {"t": "trace", "k": "think", "s": "Agent", "h": "Re-plan bays", "d": lambda S: "152 → Bay 1 at 17:30, done 21:30" if "17:30" in S["plan214"] else "152 → Bay 1 at 20:30, done 00:30 · second shift"},
                    {"t": "msg", "ch": "fleet-ops", "time": "05:41", "b": lambda S: {"text": ("Moved 152 to Bay 1 at 17:30, after 214. Done by 21:30." if "17:30" in S["plan214"]
                                                                                          else "Moved 152 to Bay 1 at 20:30, after 214. That runs into second shift, done by 00:30."),
                                                                                 "approval": ["joel", "the shop lead owns the plan"]}},
                    {"t": "choice", "ch": "fleet-ops", "approver": "joel", "opts": [{"label": "Approve plan", "btn": True, "primary": True, "then": []}]},
                ]},
            ]},
            {"t": "trace", "k": "act", "s": "TMT", "h": "Create work orders", "d": "WO 48817 (214) · WO 48818 (152) · WO 48819 (187)"},
            {"t": "trace", "k": "act", "s": "Parts", "h": "Order tires", "d": "2 × 295/75R22.5 from Platte Valley Tire · delivery Fri 05:30 · $1,180.00 · inside the auto-approve limit, no approval needed"},
            {"t": "trace", "k": "act", "s": "Driver app", "h": "Driver notices", "d": "Unit 214: drop at the shop on arrival · Unit 152: keys to the bay board"},
            {"t": "msg", "ch": "fleet-ops", "time": "05:46", "b": {
                "title": "Plan is live",
                "done": ["3 work orders created in TMT", "2 steer tires ordered for Fri 05:30 ($1,180, inside the auto-approve limit)",
                         "Drivers of 214 and 152 told via the driver app"],
                "fyi": ["@Dana · @Joel · I’ll re-plan if a new fault comes in"]}},
            {"t": "clock", "v": "Thu Oct 1 · 11:05"},
            {"t": "trace", "k": "trigger", "s": "Telematics", "h": "New fault · Unit 109", "d": "Coolant level low · 40 mi from Grand Island · arriving ~11:50"},
            {"t": "trace", "k": "think", "s": "Agent", "h": "Does it fit?", "d": "Bay 1 is free until 214 arrives at 14:00 → top-up and pressure test (1 h) · no plan change for others"},
            {"t": "msg", "ch": "fleet-ops", "time": "11:06", "b": {
                "title": "Fitted in: Unit 109, low coolant",
                "context": [["Low coolant alert, 40 mi out, arriving 11:50", "Telematics"], ["Bay 1 free until 14:00", "Shop plan"]],
                "done": ["1 h pressure test booked in Bay 1 at 12:00", "Driver told to come straight to the shop"],
                "fyi": ["@Joel · no change to the rest of the plan"]}},
            {"t": "msg", "ch": "fleet-ops", "who": "joel", "time": "11:08", "text": "Perfect, thanks."},
            {"t": "tally", "k": "minutes", "add": 40},
            {"t": "trace", "k": "done", "s": "Agent", "h": "Plan live", "d": "Watching for new faults until 18:00"},
        ],
    },
    # ------------------------------------------------------------------ 5
    {
        "id": "follow", "agent": "auditor", "when": "Fri 09:00", "name": "Follow-up",
        "case": "CASE-1043", "case_title": "INV-20931 · KC Interstate Diesel · follow-up", "opened": "Wed 08:31",
        "today": "Problems get spotted, but nobody chases them to the end.",
        "insight": "The vendor hasn’t replied, and has billed labor above standard on 6 of 9 invoices this quarter.",
        "action": "Sent the reminder on its own under the 48-hour rule, checked the corrected bill, asked for the payment release, and suggested a rule from the pattern.",
        "governed": "48-hour follow-up rule (no approval needed) · payment released only on approval · new rules only when the manager agrees",
        "outcome": "Vendor accepted the correction, payment released, and a new rule proposed from the pattern, all visible in one thread.",
        "ev": [
            {"t": "clock", "v": "Fri Oct 2 · 09:00"},
            {"t": "trace", "k": "trigger", "s": "Timer", "h": "Follow-up due", "d": lambda S: "INV-20931 correction sent Wed 08:40 · no reply in 48 h" if S["dispute"] else "INV-20931 approved as billed · checking vendor pattern"},
            {"t": "trace", "k": "read", "s": "Email", "h": "Vendor thread", "d": "No reply from billing@kcinterstate.example"},
            {"t": "trace", "k": "read", "s": "AP", "h": "Payment status", "d": "Held · due Oct 14 · no late-fee risk until then"},
            {"t": "trace", "k": "read", "s": "Rule", "h": "Follow-up rule", "d": "Nudge a vendor after 48 h without asking · escalate after 5 days"},
            {"t": "trace", "k": "act", "s": "Email", "h": "Reminder sent", "d": "To billing@kcinterstate.example, with the telematics on-site time attached"},
            {"t": "msg", "ch": "fleet-ops", "time": "09:01", "b": lambda S: {
                "title": "No reply from KC in 48 h, so I sent a reminder",
                "context": [["Correction of " + money(S["dispute"]) + " sent Wed 08:40, no reply", "Email"] if S["dispute"] else ["Invoice approved as billed", "Slack log"],
                            ["Payment held, due Oct 14, no late-fee risk", "AP"]],
                "done": ["Reminder sent with the telematics evidence (48-hour rule, no approval needed)"],
                "ctx": "If there’s still no reply by Wed, I’ll escalate to their service manager."}},
            {"t": "clock", "v": "Fri Oct 2 · 14:22"},
            {"t": "trace", "k": "trigger", "s": "Email", "h": "Vendor reply", "d": "Revised invoice INV-20931-R1 attached"},
            {"t": "trace", "k": "read", "s": "Document", "h": "Check the revised invoice", "d": lambda S: "New total " + money(4860 - S["dispute"]) + " · corrections applied as requested"},
            {"t": "trace", "k": "policy", "s": "Rule", "h": "Who approves", "d": "Releasing a held payment → maintenance manager"},
            {"t": "msg", "ch": "fleet-ops", "time": "14:23", "b": lambda S: {
                "title": "KC accepted the correction",
                "context": [["Revised invoice INV-20931-R1: " + money(4860 - S["dispute"]), "Email"], ["Matches the correction line by line", "Agent check"]],
                "recommendation": "**Release the payment.**",
                "approval": ["you", "releasing a held payment"],
                "fyi": ["AP · ready to release on your approval"]}},
            {"t": "choice", "ch": "fleet-ops", "approver": "you", "opts": [{"label": "Approve release", "btn": True, "primary": True, "then": []}]},
            {"t": "trace", "k": "act", "s": "AP", "h": "Release hold", "d": lambda S: "INV-20931-R1 released for payment · " + money(4860 - S["dispute"])},
            {"t": "tally", "k": "saved", "add_key": "dispute"},
            {"t": "trace", "k": "read", "s": "TMT", "h": "Vendor history · KC Interstate", "d": "9 invoices this quarter · 6 billed labor above standard · $1,920.00 over in total"},
            {"t": "trace", "k": "think", "s": "Agent", "h": "Pattern", "d": "KC is over standard on 6 of 9 invoices · usual gap 1–2 h"},
            {"t": "msg", "ch": "fleet-ops", "time": "14:25", "b": {
                "title": "Pattern worth a rule",
                "context": [["KC Interstate billed labor above standard on 6 of 9 invoices this quarter, $1,920.00 in total", "TMT"]],
                "options": [["Add a rule", "Stops it before the bill", "KC needs to call for jobs over 3 h", "Saves about $1,900 a quarter"],
                            ["Keep checking after the fact", "No change for KC", "Same corrections every month", "Agent time only"]],
                "rec": 0,
                "recommendation": "**Add the rule:** KC must get approval before billing more than 3 h of labor, and I audit all their labor lines.",
                "approval": ["you", "new rules need the manager"]}},
            {"t": "choice", "ch": "fleet-ops", "approver": "you", "opts": [
                {"label": "Add rule", "btn": True, "primary": True, "then": [{"t": "trace", "k": "policy", "s": "Rule", "h": "Rule added to the knowledge base", "d": "KC Interstate: pre-approval above 3.0 h labor · audit all labor lines"}]},
                {"label": "Not now", "btn": True, "then": []},
            ]},
            {"t": "tally", "k": "minutes", "add": 15},
            {"t": "msg", "ch": "fleet-ops", "time": "14:30", "b": lambda S: {
                "title": "This week in #fleet-ops (sample)",
                "fields": [["Saved on invoices", money(S["tally"]["saved"])], ["Warranty claimed", money(S["tally"]["warranty"])],
                           ["Decisions people made", str(S["tally"]["decisions"])], ["Admin time returned (est.)", "{:.1f} h".format(S["tally"]["minutes"] / 60)]],
                "ctx": "Every action, approver and dollar is in the audit log."}},
            {"t": "trace", "k": "done", "s": "Agent", "h": "Case closed", "d": "Week summary posted"},
        ],
    },
]

DISCOVERY_QUESTIONS = [
    "Which of these moments costs you the most today?",
    "Who should approve what, and what can the agent just do?",
    "Who needs to be kept in the loop on each type of case?",
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
    playbook = PLAYBOOKS[scene["agent"]]

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
                                    "b": resolve(ev.get("b"), S), "agent": playbook}))
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
                                       "who": opt.get("who", ev.get("approver", "you")), "time": S["clock"].split("· ")[-1]}))
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
    "read": ("Tool call", "#3F7FA6"),
    "think": ("Reasoning", "#7A5EA8"),
    "policy": ("Rule check", "#A8660F"),
    "act": ("Action", "#2F7A4F"),
    "wait": ("Waiting", "#8A8F88"),
    "done": ("Done", "#2F7A4F"),
}
KB_SOURCES = {"Warranty", "Rule", "Log"}
COLORS = {"you": "#8A5A1E", "dana": "#3F6FA0", "joel": "#6B4F9A", "luis": "#2F7A4F"}
INITIALS = {"you": "MM", "dana": "DK", "joel": "JP", "luis": "LR"}

ACTORS = {
    "breakdown": [("You", "Maintenance Manager", "Slack · approves"), ("Dana", "Dispatch", "Slack · kept informed"),
                  ("R. Alvarez", "Driver", "Driver app"), ("KC Interstate Diesel", "Mobile repair vendor", "Phone + email"),
                  ("FleetProfit Agent", "Runs the case", "Slack + tools")],
    "invoice": [("You", "Maintenance Manager", "Slack · approves"), ("Accounts payable", "AP team", "AP system · kept informed"),
                ("KC Interstate Diesel", "Repair vendor", "Email"), ("FleetProfit Agent", "Runs the case", "Slack + tools")],
    "warranty": [("You", "Maintenance Manager", "Slack · approves"), ("Luis", "Technician", "Slack · keeps the part"),
                 ("Hoosier Diesel Repair", "Original installer", "Email"), ("FleetProfit Agent", "Runs the case", "Slack + tools")],
    "plan": [("Dana", "Dispatch", "Slack · approves the hold"), ("Joel", "Shop lead", "Slack · approves the plan"),
             ("Drivers", "Units 214, 152, 187, 109", "Driver app"), ("Platte Valley Tire", "Parts vendor", "Purchase order"),
             ("FleetProfit Agent", "Runs the plan", "Slack + tools")],
    "follow": [("You", "Maintenance Manager", "Slack · approves"), ("Accounts payable", "AP team", "AP system"),
               ("KC Interstate Diesel", "Repair vendor", "Email"), ("FleetProfit Agent", "Runs the case", "Slack + tools")],
}

CSS = """
<style>
.fp-eyebrow{font-size:11px;letter-spacing:.1em;text-transform:uppercase;font-weight:700;color:#C7873A}
.fp-head{font-size:11px;letter-spacing:.08em;text-transform:uppercase;font-weight:700;opacity:.65;margin:10px 0 6px}
.fp-clock{display:inline-block;font-family:ui-monospace,Menlo,monospace;font-weight:600;font-size:14px;
  background:#073732;color:#F8F6F3;border-radius:8px;padding:6px 12px}
.fp-chip{display:inline-block;font-family:ui-monospace,Menlo,monospace;font-size:11px;border:1px solid rgba(128,128,128,.45);
  border-radius:4px;padding:1px 6px;margin:0 4px 4px 0}
.fp-actors{display:flex;flex-wrap:wrap;gap:8px;margin:2px 0 10px}
.fp-actor{border:1px solid rgba(128,128,128,.3);border-radius:8px;padding:5px 10px;font-size:13px;line-height:1.3}
.fp-actor b{display:block;font-size:13.5px}
.fp-actor span{opacity:.7;font-size:12px}
.fp-actor.agent{border-color:#C7873A;background:rgba(199,135,58,.08)}
.fp-trace{border:1px solid rgba(128,128,128,.28);border-left:4px solid var(--c);border-radius:8px;
  padding:6px 10px;margin:0 0 6px 0;background:rgba(128,128,128,.04)}
.fp-trace .row{display:flex;gap:6px;align-items:center;flex-wrap:wrap}
.fp-trace .k{font-size:10.5px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;color:var(--c)}
.fp-trace .s{font-family:ui-monospace,Menlo,monospace;font-size:10.5px;border:1px solid rgba(128,128,128,.45);border-radius:4px;padding:0 5px}
.fp-trace .h{font-weight:700;font-size:13px}
.fp-trace .d{font-family:ui-monospace,Menlo,monospace;font-size:11.5px;opacity:.85;margin-top:3px;line-height:1.45}
.fp-trace.run .h::after{content:"";display:inline-block;width:10px;height:10px;margin-left:7px;vertical-align:-1px;
  border:2px solid rgba(128,128,128,.4);border-top-color:#C7873A;border-radius:50%;animation:fpspin .7s linear infinite}
@keyframes fpspin{to{transform:rotate(360deg)}}
.fp-run{height:470px;overflow-y:auto;display:flex;flex-direction:column-reverse;padding-right:4px}
.fp-ctx{font-size:13px;opacity:.7}
.fp-tools{display:flex;flex-wrap:wrap;gap:5px}
.fp-tool{font-family:ui-monospace,Menlo,monospace;font-size:11.5px;border-radius:5px;padding:2px 7px;
  background:rgba(63,127,166,.12);border:1px solid rgba(63,127,166,.45)}
.fp-tool.act{background:rgba(47,122,79,.12);border-color:rgba(47,122,79,.5)}
.fp-wait{border:1px dashed #A8660F;border-radius:8px;padding:7px 10px;font-weight:600;font-size:13px;color:#A8660F;margin:4px 0}
.fp-flow{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:10px;margin:6px 0 4px}
.fp-step{border:1px solid rgba(128,128,128,.3);border-radius:10px;padding:12px}
.fp-step .n{font-size:11px;letter-spacing:.08em;text-transform:uppercase;color:#C7873A;font-weight:700}
.fp-step b{display:block;margin:2px 0 4px;font-size:15px}
.fp-step span{font-size:13px;opacity:.8;line-height:1.4;display:block}
@media (max-width:900px){.fp-flow{grid-template-columns:minmax(0,1fr)}.sk{grid-template-columns:minmax(0,1fr)!important}.sk-side{display:none}}
/* Slack-style window: a deliberate fixed light look */
.sk{border:1px solid #d6d3cc;border-radius:10px;overflow:hidden;display:grid;grid-template-columns:minmax(0,1fr);
  height:720px;background:#ffffff;color:#1d1c1d;font-family:"Lato","Helvetica Neue",Arial,sans-serif;box-shadow:0 2px 10px rgba(0,0,0,.06)}
.sk-side{background:#073732;color:#d5e2de;padding:12px 8px;font-size:14px;overflow:auto}
.sk-ws{font-weight:800;color:#fff;font-size:16px;padding:0 8px 2px}
.sk-wsub{font-size:11.5px;color:#86a8a1;padding:0 8px 8px}
.sk-sec{font-size:11px;text-transform:uppercase;letter-spacing:.06em;color:#86a8a1;margin:12px 8px 4px}
.sk-ch{padding:3px 8px;border-radius:5px;display:flex;justify-content:space-between;align-items:center}
.sk-ch.on{background:#C7873A;color:#1d1408;font-weight:700}
.sk-ch.dim{opacity:.6}
.sk-dot{display:inline-block;width:8px;height:8px;border-radius:50%;background:#6fc493;margin-right:7px}
.sk-main{display:grid;grid-template-rows:auto auto minmax(0,1fr) auto auto;min-width:0;min-height:0}
.sk-head{padding:9px 16px;border-bottom:1px solid #e8e8e8;display:flex;justify-content:space-between;align-items:center;gap:8px}
.sk-head b{font-size:16px}
.sk-head span{font-size:12px;color:#777}
.sk-case{padding:8px 16px;border-bottom:1px solid #e8e8e8;background:#fbfaf7;display:flex;flex-wrap:wrap;gap:6px 14px;align-items:center;font-size:12.5px;color:#444}
.sk-case b{font-size:13.5px;color:#1d1c1d}
.sk-pill{font-size:11.5px;font-weight:800;border-radius:999px;padding:2px 9px}
.sk-pill.wait{background:#fbefd9;color:#8a560c}
.sk-pill.work{background:#e3eef6;color:#2d6a92}
.sk-pill.ok{background:#e2f0e7;color:#2f7a4f}
.sk-msgs{overflow-y:auto;display:flex;flex-direction:column-reverse;min-height:0}
.sk-m{display:grid;grid-template-columns:36px minmax(0,1fr);gap:10px;padding:8px 16px}
.sk-m.new{background:#fff8ec}
.sk-av{width:36px;height:36px;border-radius:7px;color:#fff;display:grid;place-items:center;font-weight:800;font-size:13px}
.sk-n{font-weight:800;font-size:15px}
.sk-app{font-size:10px;font-weight:700;background:#ececec;color:#5f5f5f;border-radius:3px;padding:1px 4px;margin-left:5px;vertical-align:1px}
.sk-t{font-size:12px;color:#888;margin-left:6px}
.sk-body{font-size:14.5px;line-height:1.46}
.sk-card{border:1px solid #e3e1db;border-left:4px solid #C7873A;border-radius:6px;padding:9px 12px;margin-top:5px;font-size:14px;line-height:1.45;background:#fff}
.sk-title{font-weight:800;font-size:15px;margin-bottom:6px}
.sk-lbl{font-size:11px;font-weight:800;letter-spacing:.06em;text-transform:uppercase;color:#7a7a7a;margin:8px 0 3px}
.sk-ctxl{list-style:none;margin:0;padding:0;display:grid;gap:3px}
.sk-ctxl li{display:flex;justify-content:space-between;gap:10px;align-items:baseline}
.sk-src{font-family:ui-monospace,Menlo,monospace;font-size:10.5px;color:#2d6a92;background:#eef4f9;border-radius:3px;padding:0 5px;white-space:nowrap}
.sk-src.kb{color:#6a4f98;background:#f1edf8}
.sk-opts{width:100%;border-collapse:collapse;font-size:13px}
.sk-opts th{font-size:11px;text-align:left;color:#7a7a7a;font-weight:700;padding:3px 6px;border-bottom:1px solid #e6e6e6}
.sk-opts td{padding:5px 6px;border-bottom:1px solid #f0f0f0;vertical-align:top}
.sk-opts tr.rec td{background:#f0f7f5}
.sk-rec{display:inline-block;font-size:10px;font-weight:800;color:#fff;background:#0E6D62;border-radius:3px;padding:0 4px;margin-left:5px;vertical-align:1px}
.sk-recbox{background:#f0f7f5;border-radius:5px;padding:6px 9px;margin-top:6px}
.sk-done{list-style:none;margin:0;padding:0;display:grid;gap:2px}
.sk-done li::before{content:"✓";color:#2f7a4f;font-weight:800;margin-right:7px}
.sk-appr{margin-top:8px;padding:6px 9px;border-radius:5px;background:#fbefd9;color:#6b4209;font-size:13px;font-weight:700}
.sk-appr.ok{background:#e2f0e7;color:#2f7a4f}
.sk-fyi{margin-top:6px;font-size:12.5px;color:#555}
.sk-fyi b{color:#333}
.sk-fields{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:4px 18px;margin:4px 0 6px}
.sk-fields small{display:block;font-size:12px;font-weight:700;color:#616061}
.sk-card ul.pl{margin:2px 0 4px;padding-left:18px}
.sk-quote{background:#f8f8f8;border:1px solid #e3e3e3;border-radius:6px;padding:8px 10px;font-size:12.5px;white-space:pre-wrap;margin-top:6px}
.sk-quote i{display:block;font-style:normal;font-size:11.5px;color:#777;margin-bottom:3px}
.sk-ctx{font-size:12.5px;color:#777;margin-top:6px}
.sk-btns{display:flex;gap:6px;margin-top:8px;flex-wrap:wrap}
.sk-btn{border:1px solid #c9c9c9;border-radius:5px;padding:3px 11px;font-size:13px;font-weight:700;color:#1d1c1d;background:#fff}
.sk-btn.p{background:#0E6D62;border-color:#0E6D62;color:#fff}
.sk-typing{font-size:12.5px;color:#888;font-style:italic;padding:2px 16px 4px 62px;min-height:22px}
.sk-comp{border-top:1px solid #ececec;padding:8px 14px 10px}
.sk-box{border:1px solid #c9c9c9;border-radius:8px;padding:8px 12px;color:#999;font-size:14px}
.sk-mention{background:#e8f3f1;color:#0E6D62;border-radius:3px;padding:0 2px;font-weight:700}
</style>
"""


def _md(s):
    """Escape $ so Streamlit does not read amounts as LaTeX."""
    return (s or "").replace("$", "\\$")


def _h(s):
    return html.escape(s or "").replace("$", "&#36;").replace("\n", "<br>")


def _rich(s):
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", _h(s))
    return re.sub(r"(@[A-Z][a-z]+)", r'<span class="sk-mention">\1</span>', t)


def _tool_label(t):
    if t["k"] == "trigger":
        return t["s"] + " event"
    if t["k"] in ("think", "done") or t["s"] == "Agent":
        return "agent"
    if t["k"] == "policy" or t["s"] in KB_SOURCES:
        return "knowledge base"
    return t["s"].lower().replace(" ", "_") + "." + re.sub(r"[^a-z0-9]+", "_", t["h"].lower()).strip("_")


def _trace_html(t, running=False):
    label, color = KINDS[t["k"]]
    return (f'<div class="fp-trace{" run" if running else ""}" style="--c:{color}"><div class="row">'
            f'<span class="k">{label}</span><span class="s">{_h(_tool_label(t))}</span><span class="h">{_h(t["h"])}</span></div>'
            f'<div class="d">{_h(t["d"])}</div></div>')


def _who(key):
    name, role = PEOPLE[key]
    return name, role


def _card_html(m):
    b = m["b"] or {}
    out = []
    if b.get("title"):
        out.append(f'<div class="sk-title">{_rich(b["title"])}</div>')
    if b.get("context"):
        out.append('<div class="sk-lbl">Context I pulled</div><ul class="sk-ctxl">' + "".join(
            f'<li><span>{_rich(t)}</span><span class="sk-src{" kb" if "KB" in s else ""}">{_h(s)}</span></li>' for t, s in b["context"]) + "</ul>")
    if b.get("options"):
        rec = b.get("rec", -1)
        rows = "".join(
            f'<tr class="{"rec" if i == rec else ""}"><td><b>{_h(o[0])}</b>{"<span class=sk-rec>RECOMMENDED</span>" if i == rec else ""}</td>'
            f'<td>{_h(o[1])}</td><td>{_h(o[2])}</td><td>{_h(o[3])}</td></tr>' for i, o in enumerate(b["options"]))
        out.append('<div class="sk-lbl">Options and trade-offs</div><table class="sk-opts"><tr><th>Option</th><th>Upside</th><th>Downside</th><th>Cost / effect</th></tr>'
                   + rows + "</table>")
    if b.get("list"):
        out.append('<ul class="pl">' + "".join(f"<li>{_rich(x)}</li>" for x in b["list"]) + "</ul>")
    if b.get("text"):
        out.append(f"<div>{_rich(b['text'])}</div>")
    if b.get("recommendation"):
        out.append(f'<div class="sk-recbox"><b>Recommendation:</b> {_rich(b["recommendation"])}</div>')
    if b.get("quote"):
        out.append(f'<div class="sk-quote"><i>{_h(b["quote"]["h"])}</i>{_h(b["quote"]["body"])}</div>')
    if b.get("done"):
        out.append('<div class="sk-lbl">Done</div><ul class="sk-done">' + "".join(f"<li>{_rich(x)}</li>" for x in b["done"]) + "</ul>")
    if b.get("fields"):
        out.append('<div class="sk-fields">' + "".join(f"<div><small>{_h(k)}</small>{_rich(v)}</div>" for k, v in b["fields"]) + "</div>")
    if b.get("approval"):
        who, why = b["approval"]
        name, role = _who(who)
        if m.get("chosen"):
            cname, label, ctime, isbtn = m["chosen"]
            what = f"clicked “{_h(label)}”" if isbtn else "replied below"
            out.append(f'<div class="sk-appr ok">✓ {_h(cname)} {what} · {_h(ctime)}</div>')
        else:
            out.append(f'<div class="sk-appr">Approval needed from <span class="sk-mention">@{_h(name)}</span> ({_h(role)}) · {_h(why)}</div>')
    if m.get("buttons"):
        out.append('<div class="sk-btns">' + "".join(
            f'<span class="sk-btn{" p" if o.get("primary") else ""}">{_h(o["label"])}</span>' for o in m["buttons"]) + "</div>")
    if b.get("fyi"):
        out.append('<div class="sk-fyi"><b>Looped in:</b> ' + " · ".join(_rich(x) for x in b["fyi"]) + "</div>")
    if b.get("ctx"):
        out.append(f'<div class="sk-ctx">{_rich(b["ctx"])}</div>')
    return '<div class="sk-card">' + "".join(out) + "</div>"


def _msg_html(m, newest=False):
    if m["who"]:
        name, role = _who(m["who"])
        av = f'<div class="sk-av" style="background:{COLORS[m["who"]]}">{INITIALS[m["who"]]}</div>'
        head = f'<span class="sk-n">{_h(name)}</span><span class="sk-t">{_h(role)} · {m["time"]}</span>'
        body = f'<div class="sk-body">{_rich(m["text"])}</div>'
    else:
        av = '<div class="sk-av" style="background:#073732">FP</div>'
        head = (f'<span class="sk-n">FleetProfit Agent</span><span class="sk-app">APP</span>'
                f'<span class="sk-t">{_h(m["agent"])} · {m["time"]}</span>')
        b = m["b"] or {}
        plain = b.get("text") and not any(b.get(k) for k in ("title", "context", "options", "done", "quote", "fields", "list"))
        body = f'<div class="sk-body">{_rich(b["text"])}</div>' + (_card_html({**m, "b": {k: v for k, v in b.items() if k != "text"}}) if (b.get("approval") or b.get("fyi") or m.get("buttons")) else "") if plain else _card_html(m)
    return f'<div class="sk-m{" new" if newest else ""}">{av}<div style="min-width:0"><div>{head}</div>{body}</div></div>'


def _window(items, scene, clock, status, typing=False, pending=None):
    msgs = []
    for kind, it in items:
        if kind == "msg":
            msgs.append(dict(it))
        elif kind == "choice":
            name = _who(it["who"])[0]
            for m in reversed(msgs):
                if not m["who"]:
                    m["chosen"] = (name, it["label"], it.get("time", ""), it["btn"])
                    break
            if not it["btn"]:
                msgs.append({"ch": it["ch"], "who": it["who"], "time": it.get("time", ""), "text": it["label"], "b": None, "agent": ""})
    if pending:
        for m in reversed(msgs):
            if not m["who"]:
                m.pop("chosen", None)
                break
    actors = ACTORS[scene["id"]]
    pill_cls = {"wait": "wait", "work": "work", "ok": "ok"}[status[0]]
    case = (f'<div class="sk-case"><b>{_h(scene["case"])}</b><span>{_h(scene["case_title"])}</span>'
            f'<span class="sk-pill {pill_cls}">{_h(status[1])}</span>'
            f'<span>Opened {_h(scene["opened"])} · now {_h(clock.split("· ")[-1])}</span>'
            f'<span>Participants: {_h(", ".join(a[0] for a in actors if a[0] != "FleetProfit Agent"))}</span></div>')
    body = "".join(_msg_html(m, newest=(i == len(msgs) - 1)) for i, m in enumerate(msgs))
    if not msgs:
        body = '<div class="sk-ctx" style="padding:16px">The FleetProfit Agent is gathering context…</div>'
    typing_txt = "FleetProfit Agent is typing…" if typing else ""
    main = (f'<div class="sk-main"><div class="sk-head"><b># fleet-ops</b><span>Demo Fleet · FleetProfit Agent runs every case here</span></div>'
            f'{case}<div class="sk-msgs"><div>{body}</div></div><div class="sk-typing">{typing_txt}</div>'
            f'<div class="sk-comp"><div class="sk-box">Message #fleet-ops</div></div></div>')
    return f'<div class="sk">{main}</div>'


# ---------------------------------------------------------------- state
def _init():
    ss = st.session_state
    ss.setdefault(KEY + "started", False)
    ss.setdefault(KEY + "scene", 0)
    ss.setdefault(KEY + "choices", [])
    ss.setdefault(KEY + "shown", 0)
    ss.setdefault(KEY + "animate", True)
    ss.setdefault(KEY + "speed", "Normal")
    ss.setdefault(KEY + "hood", False)


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
        st.markdown("### FleetProfit Agent")
        st.markdown('<span class="fp-eyebrow">Sample data</span>', unsafe_allow_html=True)
        st.caption("Demo fleet shaped like a regional flatbed carrier: 70 tractors, 204 trailers, based in Nebraska.")
        st.markdown('<div class="fp-head">The week, one truck</div>', unsafe_allow_html=True)
        st.button("How it works", key=KEY + "home", on_click=_restart, use_container_width=True,
                  type="primary" if not started else "secondary")
        for i, sc in enumerate(SCENES):
            current = started and i == scene_idx
            st.button(f"{i + 1}. {sc['when']} · {sc['name']}", key=f"{KEY}nav{i}", on_click=_go, args=(i,),
                      type="primary" if current else "secondary", use_container_width=True)
        st.markdown('<div class="fp-head">Presenter</div>', unsafe_allow_html=True)
        st.toggle("Animate in real time", key=KEY + "animate")
        st.select_slider("Speed", ["Slow", "Normal", "Fast"], key=KEY + "speed")
        st.toggle("Show “Under the hood” beside the chat", key=KEY + "hood")
        st.markdown('<div class="fp-head">Connected through the harness (sample)</div>', unsafe_allow_html=True)
        st.markdown("".join(f'<span class="fp-chip">{html.escape(s)}</span>' for s in SYSTEMS), unsafe_allow_html=True)


def _intro():
    st.markdown('<span class="fp-eyebrow">FleetProfit · AI agent for fleet maintenance</span>', unsafe_allow_html=True)
    st.title("From insight to action")
    st.subheader("One agent, one channel, one truck’s week")
    st.markdown(
        "The FleetProfit Agent watches your maintenance, telematics and dispatch data all the time. When something "
        "needs doing, it opens a case in **#fleet-ops**, pulls the context, sets out the options and trade-offs, and "
        "recommends one. People only step in where a rule says they must approve. Everyone else is kept in the loop.")
    st.markdown('<div class="fp-head">How it works</div>', unsafe_allow_html=True)
    steps = [
        ("1 · Trigger", "Something happens", "A fault code, an invoice email, a new repair order or a daily schedule opens a case."),
        ("2 · Knowledge base", "Context", "Fleet history, warranty terms, vendor records, labor standards and your approval rules."),
        ("3 · Agent", "Options and a recommendation", "Weighs the options with their trade-offs and recommends one, with the reasoning shown."),
        ("4 · Harness", "Connects the tools", "Reads and acts in TMT, telematics, the TMS, email and AP through approved tools, with permissions and an audit log."),
        ("5 · Slack", "Approve and inform", "Only the right approver is asked. Everyone else is looped in. The agent acts and closes the case."),
    ]
    st.markdown('<div class="fp-flow">' + "".join(
        f'<div class="fp-step"><div class="n">{a}</div><b>{b}</b><span>{_h(c)}</span></div>' for a, b, c in steps) + "</div>",
        unsafe_allow_html=True)
    st.markdown('<div class="fp-head">Who is involved</div>', unsafe_allow_html=True)
    st.markdown(
        "| Who | Role | What the agent asks of them |\n|---|---|---|\n"
        "| You | Maintenance manager | Approves road calls over the limit, invoice corrections, warranty claims, new rules |\n"
        "| Dana | Dispatcher | Approves holding a truck past a planned pickup; kept informed on loads at risk |\n"
        "| Joel | Shop lead | Approves the day’s shop plan; told when the agent fits in new work |\n"
        "| Luis | Technician | Asked to keep parts that are under warranty |\n"
        "| Drivers | Drivers | Told where to go and what to do, through the driver app |\n"
        "| Vendors | Repair shops, parts suppliers | Receive corrections, claims, reminders and orders by email |\n"
        "| Accounts payable | AP team | See payment holds and releases |\n"
        "| FleetProfit Agent | Runs every case | Pulls context, recommends, asks for approval, acts, keeps everyone informed |")
    st.markdown('<div class="fp-head">The week</div>', unsafe_allow_html=True)
    rows = "\n".join(f"| {sc['when']} | {sc['case']} | {_md(sc['insight'])} | {_md(sc['action'])} |" for sc in SCENES)
    st.markdown("| When | Case | Insight | Action |\n|---|---|---|---|\n" + rows)
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
        st.markdown(f'<span class="fp-eyebrow">Scene {idx + 1} of {len(SCENES)} · {sc["when"]} · live in #fleet-ops</span>', unsafe_allow_html=True)
        st.subheader(f"{sc['case']} · {sc['case_title']}")
    clock_ph = h2.empty()
    st.markdown('<div class="fp-actors">' + "".join(
        f'<div class="fp-actor{" agent" if a[0] == "FleetProfit Agent" else ""}"><b>{_h(a[0])}</b><span>{_h(a[1])} · {_h(a[2])}</span></div>'
        for a in ACTORS[sc["id"]]) + "</div>", unsafe_allow_html=True)

    if idx > 0:
        st.caption("Earlier scenes in the week are replayed with the recommended choices, so totals carry over.")
    if ss[KEY + "hood"]:
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
    state = {"clock": "Tue Sep 29 · 21:00"}
    working = ("work", "Agent working")

    def draw(status=working, typing=False, pend=None):
        win_ph.markdown(_window(items, sc, state["clock"], status, typing, pend), unsafe_allow_html=True)

    def draw_clock():
        clock_ph.markdown(f'<div style="text-align:right"><span class="fp-clock">{state["clock"]}</span></div>', unsafe_allow_html=True)

    def draw_run(running=False, waiting=None):
        rows = "".join(_trace_html(t, running=(running and j == len(traces) - 1)) for j, t in enumerate(traces))
        if waiting:
            rows += f'<div class="fp-wait">Waiting for {waiting}</div>'
        if not rows:
            rows = '<div class="fp-ctx">Waiting for a trigger…</div>'
        run_ph.markdown(f'<div class="fp-run"><div>{rows}</div></div>', unsafe_allow_html=True)

    def draw_tools():
        if not tools:
            tools_ph.caption("No tools called yet.")
        else:
            tools_ph.markdown('<div class="fp-tools">' + "".join(
                f'<span class="fp-tool{" act" if k == "act" else ""}">✓ {_h(n)}</span>' for n, k in tools) + "</div>", unsafe_allow_html=True)

    draw_clock()
    draw()
    draw_tools()
    draw_run()
    for i, (kind, item) in enumerate(log):
        fresh = animate and i >= shown
        if kind == "clock":
            state["clock"] = item
            draw_clock()
            if fresh:
                draw()
                time.sleep(0.4 * pace)
        elif kind == "trace":
            traces.append(item)
            if fresh:
                draw_run(running=True)
                time.sleep((1.4 if item["slow"] else 0.9 if item["k"] == "think" else 0.5) * pace)
                draw_run()
            if item["k"] in ("read", "act"):
                name = _tool_label(item)
                if name not in ("knowledge base", "agent") and (name, item["k"]) not in tools:
                    tools.append((name, item["k"]))
                    if fresh:
                        draw_tools()
        elif kind == "msg":
            if fresh and not item["who"]:
                draw(typing=True)
                time.sleep(1.0 * pace)
            items.append(("msg", item))
            if fresh:
                draw()
                time.sleep(0.5 * pace)
        elif kind == "choice":
            items.append(("choice", item))
            if fresh:
                draw()
    ss[KEY + "shown"] = len(log)

    if pending:
        aname, arole = _who(pending.get("approver", "you"))
        status = ("wait", f"Waiting on @{aname} ({arole})")
    else:
        status = ("ok", "Resolved")
    draw(status=status, pend=pending)
    draw_tools()
    draw_run(waiting=f"@{_who(pending.get('approver', 'you'))[0]} in #fleet-ops" if pending else None)

    if pending:
        with resp:
            btns = [(i, o) for i, o in enumerate(pending["opts"]) if o.get("btn")]
            replies = [(i, o) for i, o in enumerate(pending["opts"]) if not o.get("btn")]
            aname, arole = _who(pending.get("approver", "you"))
            st.caption(f"Respond as {aname} ({arole}) in #fleet-ops")
            if btns:
                cols = st.columns(len(btns))
                for col, (i, o) in zip(cols, btns):
                    col.button(o["label"], key=f"{KEY}b{idx}_{len(ss[KEY + 'choices'])}_{i}", on_click=_choose, args=(i,),
                               type="primary" if o.get("primary") else "secondary", use_container_width=True)
            for i, o in replies:
                name, role = _who(o["who"])
                st.button(f"Reply as {name}: “{o['label']}”", key=f"{KEY}r{idx}_{len(ss[KEY + 'choices'])}_{i}",
                          on_click=_choose, args=(i,), use_container_width=True)
    else:
        with resp:
            with st.container(border=True):
                st.markdown("**What just happened**")
                c1, c2, c3 = st.columns(3)
                with c1:
                    st.caption("INSIGHT")
                    st.markdown(_md(sc["insight"]))
                with c2:
                    st.caption("ACTION")
                    st.markdown(_md(sc["action"]))
                with c3:
                    st.caption("GOVERNED BY")
                    st.markdown(_md(sc["governed"]))
                st.caption("Today, without the agent: " + _md(sc["today"]))
                st.success(f"**Outcome:** {_md(sc['outcome'])}")
            if idx + 1 < len(SCENES):
                nx = SCENES[idx + 1]
                st.button(f"Next: {nx['when']} · {nx['case']} →", type="primary", on_click=_go, args=(idx + 1,))
            else:
                with st.container(border=True):
                    st.markdown("#### Where would turning insight into action make the biggest difference for you?")
                    st.markdown("\n".join(f"- {q}" for q in DISCOVERY_QUESTIONS))
                st.button("Play again from Tuesday", on_click=_go, args=(0,))

    # running totals
    t = S["tally"]
    st.markdown('<div class="fp-head">Impact this week</div>', unsafe_allow_html=True)
    m = st.columns(4)
    m[0].metric("Saved on invoices", money(t["saved"]))
    m[1].metric("Warranty claimed", money(t["warranty"]))
    m[2].metric("Decisions people made", t["decisions"])
    m[3].metric("Admin time returned (est.)", "{:.1f} h".format(t["minutes"] / 60))


render()

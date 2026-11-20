"""The demo scenario as data: people, 20 emails and their attachments (README.md in this folder).

All invented. Outside parties use *.example.com. Phone numbers use Ofcom's drama range 07700 900xxx.
Text of documents matches db_seed.sql, so seed data and ingested data agree.
"""

from __future__ import annotations

FIRM = {"name": "Marcus Limited", "owner": "Florin Marcus", "address": "florin@marcus-ltd.example.com"}

# alias -> (display name, address). The alias is also the plus-address used by the live simulator (ADR 0005).
PERSONAS = {
    "florin": ("Florin Marcus", "florin@marcus-ltd.example.com"),
    "mike": ("Mike Turner", "mike.turner@marcus-ltd.example.com"),
    "jamie": ("Jamie Cole", "jamie.cole@marcus-ltd.example.com"),
    "hartley": ("Victoria Hartley", "victoria.hartley@mail.example.com"),
    "architect": ("Lena Marsh, Marsh Studio", "lena@marsh-studio.example.com"),
    "joinery": ("Ashby Joinery", "quotes@ashby-joinery.example.com"),
    "stone": ("Stoneworks Hollowell", "sales@stoneworks-hollowell.example.com"),
    "electrician": ("Spark Right Electrical", "office@sparkright.example.com"),
    "qs": ("Carter Cost Consulting", "qs@carter-cost.example.com"),
    "fm": ("Paul Reid, Kingsway Business Park", "facilities@brightmoor.example.com"),
    "fenwick": ("Fenwick Drylining", "admin@fenwick-drylining.example.com"),
    "volt": ("Volt Electrical", "jobs@volt-electrical.example.com"),
    "council": ("Hollowell Council Repairs", "repairs@hollowell-council.example.com"),
    "contracts": ("Sam Price, Contract Manager, Hollowell Council", "voids@hollowell-council.example.com"),
    "asbestosteam": ("Hollowell Council Asbestos Team", "asbestos@hollowell-council.example.com"),
    "bc": ("Hollowell Building Control", "buildingcontrol@hollowell-council.example.com"),
    "buildmart": ("BuildMart Supplies", "orders@buildmart.example.com"),
}

WHATSAPP_CHAT = """03/11/2026, 18:02 - Florin Marcus: Hi Victoria, the plumber says underfloor heating in the kitchen is possible now the floor is up. Extra £2,400 + VAT.
03/11/2026, 19:40 - Victoria Hartley: Yes, go ahead with the underfloor heating in the kitchen.
06/11/2026, 08:15 - Florin Marcus: For the utility room we could fit a pocket door instead of the hinged door. £850 + VAT extra.
06/11/2026, 12:31 - Victoria Hartley: Approved, thanks. Pocket door it is.
08/11/2026, 17:05 - Florin Marcus: Also thinking about garden lighting along the path, roughly £1,900.
08/11/2026, 20:12 - Victoria Hartley: Sounds nice, let's talk next week.
"""

# Attachments: kind "pdf" (title, paragraphs, optional table) or "txt" (text).
ATTACHMENTS = {
    "a01": {"filename": "Elm Avenue - Drawing Schedule rev C.pdf", "kind": "pdf",
            "title": "Drawing schedule, revision C",
            "paras": ["Project: Hartley house refurbishment, 22 Elm Avenue, Hollowell.",
                      "Architect: Marsh Studio. Issue date: 6 October 2026. Status: for construction."],
            "table": [["Drawing", "Title", "Rev"],
                      ["MS-100", "Existing ground floor plan", "B"],
                      ["MS-101", "Proposed ground floor plan", "C"],
                      ["MS-110", "Kitchen and utility layout", "C"],
                      ["MS-120", "Sections A-A and B-B", "B"]]},
    "a02": {"filename": "Quote Q-2051 - 22 Elm Avenue.pdf", "kind": "pdf",
            "title": "Quote Q-2051",
            "paras": ["Marcus Limited. Client: Victoria Hartley, 22 Elm Avenue, Hollowell.",
                      "Scope: full refurbishment of ground floor to drawing schedule rev C: strip out, new kitchen and utility, "
                      "electrics, plumbing, plastering, joinery, decoration.",
                      "Contract sum: £148,500 + VAT. Valid 30 days. Changes priced and agreed in writing before work."],
            "table": [["Item", "Amount (£)"], ["Strip out and enabling", "9,800"], ["Kitchen and utility", "61,200"],
                      ["Electrics and plumbing", "38,400"], ["Plaster, joinery, decoration", "39,100"],
                      ["Total (ex VAT)", "148,500"]]},
    "a04": {"filename": "Ashby Joinery - Kitchen Quote AJ-771.pdf", "kind": "pdf", "title": "Quote AJ-771",
            "paras": ["Ashby Joinery. For: Marcus Limited, 22 Elm Avenue.",
                      "Bespoke painted shaker kitchen, oak worktops, larder unit. Supply and fit: £24,600 + VAT. Lead time 5 weeks."]},
    "a05": {"filename": "Stoneworks - Flooring Quote SW-3302.pdf", "kind": "pdf", "title": "Quote SW-3302",
            "paras": ["Stoneworks Hollowell. For: Marcus Limited, 22 Elm Avenue.",
                      "Limestone floor tiles, 42 m2, kitchen and utility, supply only: £5,880 + VAT. Delivery 10 working days."]},
    "a06": {"filename": "WhatsApp Chat with Victoria Hartley.txt", "kind": "txt", "text": WHATSAPP_CHAT},
    "a10": {"filename": "Unit 4 Kingsway - Contract Particulars.pdf", "kind": "pdf", "title": "Contract particulars",
            "paras": ["JCT Intermediate Building Contract 2016. Employer: Brightmoor Analytics Ltd. Contractor: Marcus Limited.",
                      "Works: office refit, Unit 4, Kingsway Business Park. Date of possession 12 October 2026. "
                      "Completion date 18 December 2026.",
                      "Interim valuation dates: the 28th of each month. Due date: 7 days after each interim valuation date. "
                      "Final date for payment: 14 days from the due date. Pay less notice: not later than 5 days before "
                      "the final date for payment.",
                      "Working hours: building occupied; noisy work outside 08:00-18:00 only."]},
    "a12a": {"filename": "Fenwick Drylining - RAMS Unit 4.pdf", "kind": "pdf", "title": "Risk assessment and method statement",
             "paras": ["Fenwick Drylining Ltd. Partitions and suspended ceilings, Unit 4, Kingsway Business Park.",
                       "Hazards: work at height (podium steps), manual handling of boards, dust from cutting "
                       "(on-tool extraction, FFP3 masks), occupied building: segregate work area, noisy cutting outside office hours."]},
    "a12b": {"filename": "Fenwick Drylining - Public Liability Certificate.pdf", "kind": "pdf", "title": "Certificate of insurance",
             "paras": ["Insured: Fenwick Drylining Ltd. Public liability limit £5,000,000.",
                       "Period of insurance: 1 December 2025 to 30 November 2026."]},
    "a13": {"filename": "Volt Electrical - Insurance Certificate.pdf", "kind": "pdf", "title": "Certificate of insurance",
            "paras": ["Insured: Volt Electrical Ltd. Public liability limit £2,000,000.",
                      "Period of insurance: 1 November 2025 to 31 October 2026."]},
    "a14": {"filename": "Marcus Limited - Interim Application 2 - Unit 4.pdf", "kind": "pdf", "title": "Interim application for payment no. 2",
            "paras": ["Contractor: Marcus Limited. Employer: Brightmoor Analytics Ltd. Project: Unit 4, Kingsway Business Park.",
                      "Valuation date: 28 October 2026. Gross valuation £96,400.00. Less previous £41,200.00. "
                      "Amount applied for £55,200.00 + VAT."]},
    "a15": {"filename": "Fenwick Drylining - Application for Payment 2.pdf", "kind": "pdf", "title": "Application for payment no. 2",
            "paras": ["Subcontractor: Fenwick Drylining Ltd. Main contractor: Marcus Limited. Project: Unit 4, Kingsway Business Park.",
                      "Gross valuation to date £36,480.00. Less previous payments £18,240.00. Amount applied for £18,240.00 + VAT.",
                      "Payment due date under the subcontract: 25 November 2026."]},
    "a16": {"filename": "WO-2026-4471 Works Order.pdf", "kind": "pdf", "title": "Works order WO-2026-4471",
            "paras": ["Hollowell District Council. Property: Flat 12, Riverside House. Void works to lettable standard.",
                      "Target completion date: 27 November 2026. Asbestos: see survey before starting work."],
            "table": [["SOR code", "Description", "Qty"], ["KIT010", "Strip out and renew kitchen units", "1 IT"],
                      ["BTH020", "Renew bathroom suite", "1 IT"], ["ELE005", "Full electrical test", "1 IT"],
                      ["DEC100", "Redecorate throughout", "1 IT"]]},
    "a17": {"filename": "Asbestos Survey - Flat 12 Riverside House.pdf", "kind": "pdf",
            "title": "Refurbishment and demolition survey (HSG264)",
            "paras": ["Property: Flat 12, Riverside House. Survey date 22 October 2026. Report date 24 October 2026.",
                      "Scope: kitchen and bathroom only. Areas outside scope not surveyed.",
                      "Areas not accessed: Bedroom 2 (locked). Presumed to contain asbestos."],
            "table": [["Room", "Material", "Sample", "Result"],
                      ["Kitchen", "Vinyl floor tiles", "S01", "Chrysotile detected"],
                      ["Hall", "Textured coating, ceiling", "S02", "No asbestos detected"],
                      ["Bedroom 2", "Not accessed (locked)", "-", "Presumed"]]},
    "a21": {"filename": "Hollowell Council - Void Works Call-off Terms 2026.pdf", "kind": "pdf",
            "title": "Void works call-off terms (2026)",
            "paras": ["Hollowell District Council. Responsive repairs and void works. Call-off terms for each works order.",
                      "4.1 The Contractor shall complete each void by the target date in the works order.",
                      "4.2 If the Contractor expects to miss a target date, it shall notify the Contract Manager in writing "
                      "within 2 working days of becoming aware of the delay, giving the reason and a revised completion date.",
                      "4.3 The Council may extend the target date for delays caused by the Council, its tenants or its other "
                      "contractors, including late gas capping, asbestos removal by the Council and lack of access.",
                      "4.4 If a void is completed late without an agreed extension, the Contractor shall pay liquidated damages "
                      "of £50 per calendar day per void, deducted from payment.",
                      "4.5 If the Contractor does not notify a delay under clause 4.2, the Council may refuse an extension.",
                      "6.1 Contract Manager: Sam Price, voids@hollowell-council.example.com."]},
    "a18": {"filename": "Gas Capping Note - Flat 12.pdf", "kind": "pdf", "title": "Gas capping note",
            "paras": ["Flat 12, Riverside House. Gas supply capped at the meter on 4 November 2026 by the council's gas contractor."]},
}

# Emails. when: ISO datetime for history, or "today HH:MM" (sent on demo day by the today batch).
EMAILS = [
    {"id": "e01", "from": "architect", "when": "2026-10-06T09:12:00+01:00", "subject": "22 Elm Avenue: brief and drawing schedule",
     "body": "Hi Florin,\n\nAttached is the drawing schedule (rev C) for the Hartley house. Victoria wants work to start before the end of October.\n\nLena", "attach": ["a01"]},
    {"id": "e02", "from": "florin", "to": "hartley", "when": "2026-10-10T16:40:00+01:00", "subject": "Quote Q-2051, 22 Elm Avenue",
     "body": "Dear Victoria,\n\nPlease find our quote Q-2051 attached: £148,500 + VAT.\n\nBest regards,\nFlorin", "attach": ["a02"]},
    {"id": "e03", "from": "hartley", "when": "2026-10-13T19:05:00+01:00", "subject": "Re: Quote Q-2051, 22 Elm Avenue",
     "body": "Hi Florin, we are happy with quote Q-2051 for £148,500 + VAT and would like to go ahead. Please treat this email as our acceptance. Victoria"},
    {"id": "e04", "from": "joinery", "when": "2026-10-27T11:20:00+00:00", "subject": "Kitchen quote AJ-771, 22 Elm Avenue",
     "body": "Florin, our quote for the kitchen is attached.\n\nAshby Joinery", "attach": ["a04"]},
    {"id": "e05", "from": "stone", "when": "2026-10-29T14:02:00+00:00", "subject": "Flooring quote SW-3302",
     "body": "Hello Florin, please see attached for the limestone floor tiles.\n\nStoneworks Hollowell", "attach": ["a05"]},
    {"id": "e06", "from": "hartley", "when": "2026-11-10T21:14:00+00:00", "subject": "Our WhatsApp chat about the changes",
     "body": "Hi Florin, as you asked, here is our WhatsApp chat so you have the changes in writing. Victoria", "attach": ["a06"]},
    {"id": "e07", "from": "architect", "when": "2026-11-12T10:30:00+00:00", "subject": "Kitchen-dining wall at 22 Elm Avenue",
     "body": "Florin,\n\nVictoria now wants the wall between the kitchen and dining room taken out. We don't know yet if it is load-bearing. Can you book the structural engineer to look at it?\n\nLena"},
    {"id": "e08", "from": "electrician", "when": "2026-11-17T16:20:00+00:00", "subject": "22 Elm Avenue: electrical works complete",
     "body": "Florin, first and second fix complete at 22 Elm Avenue. Testing done. Electrical installation certificate to follow next week once the paperwork is back from the office."},
    {"id": "e09", "from": "hartley", "when": "today 08:05", "subject": "Final account?",
     "body": "Morning Florin,\n\nNearly there! Can you send me the final account with the changes we agreed, so we can arrange payment?\n\nThanks, Victoria"},
    {"id": "e10", "from": "qs", "when": "2026-10-01T10:30:00+01:00", "subject": "Unit 4 Kingsway: signed contract particulars",
     "body": "Please find attached the signed contract particulars for the Unit 4 office refit. Interim valuations monthly on the 28th.", "attach": ["a10"]},
    {"id": "e11", "from": "fm", "when": "2026-10-05T08:50:00+01:00", "subject": "Unit 4: working hours and permits",
     "body": "Florin,\n\nThe building stays occupied. Noisy work only before 08:00 or after 18:00. Hot works need a permit from me 24 hours ahead. Fire alarm isolations through the front desk.\n\nPaul Reid\nFacilities, Kingsway Business Park"},
    {"id": "e12", "from": "fenwick", "when": "2026-10-08T08:45:00+01:00", "subject": "Unit 4 Kingsway: RAMS and insurance",
     "body": "Attached our RAMS for partitions and ceilings at Unit 4, and our public liability insurance certificate.", "attach": ["a12a", "a12b"]},
    {"id": "e13", "from": "volt", "when": "2026-10-09T12:10:00+01:00", "subject": "Insurance certificate",
     "body": "As requested, our insurance certificate for the Kingsway job.", "attach": ["a13"]},
    {"id": "e14", "from": "florin", "to": "qs", "when": "2026-10-28T17:00:00+00:00", "subject": "Unit 4: interim application 2",
     "body": "Please find attached our interim application no. 2 for Unit 4.\n\nFlorin Marcus\nMarcus Limited", "attach": ["a14"]},
    {"id": "e15", "from": "fenwick", "when": "today 08:10", "subject": "Unit 4 Kingsway: application for payment 2",
     "body": "Please find attached our application for payment no. 2 for Unit 4, Kingsway Business Park: £18,240.00 + VAT.", "attach": ["a15"]},
    {"id": "e16", "from": "council", "when": "2026-10-28T09:00:00+00:00", "subject": "Works order WO-2026-4471, Flat 12 Riverside House",
     "body": "Please find attached works order WO-2026-4471 for void works at Flat 12, Riverside House. Target completion 27 November 2026.", "attach": ["a16"]},
    {"id": "e17", "from": "council", "when": "2026-10-29T11:30:00+00:00", "subject": "Asbestos survey, Flat 12 Riverside House",
     "body": "Attached the refurbishment and demolition asbestos survey for Flat 12 (kitchen and bathroom).", "attach": ["a17"]},
    {"id": "e18", "from": "council", "when": "2026-11-05T14:00:00+00:00", "subject": "Flat 12 Riverside House: gas capped, keys",
     "body": "Gas supply capped, note attached. Keys can be collected from the housing office.", "attach": ["a18"]},
    {"id": "e21", "from": "contracts", "when": "2026-10-28T09:05:00+00:00", "subject": "Call-off terms for void works, WO-2026-4471",
     "body": "Florin,\n\nFor your records, the call-off terms that apply to works order WO-2026-4471 (Flat 12, Riverside House) are attached. Please read clause 4 on target dates and delays.\n\nSam Price\nContract Manager, Voids", "attach": ["a21"]},
    {"id": "e22", "from": "florin", "to": "council", "when": "2026-11-06T08:40:00+00:00", "subject": "Flat 12 Riverside House: keys collected, works started",
     "body": "Hello,\n\nWe collected the keys for Flat 12, Riverside House this morning and started the void works today. We will not disturb the kitchen floor tiles until the asbestos removal is done.\n\nFlorin Marcus\nMarcus Limited"},
    {"id": "e23", "from": "florin", "to": "council", "when": "2026-11-14T16:10:00+00:00", "subject": "Flat 12 Riverside House: progress",
     "body": "Hello,\n\nProgress at Flat 12: bathroom suite replaced, rewiring of the bedrooms done, decoration started. The kitchen is waiting for the removal of the asbestos floor tiles by the council's contractor, booked for 19 November.\n\nFlorin Marcus\nMarcus Limited"},
    {"id": "e24", "from": "asbestosteam", "when": "2026-11-18T15:30:00+00:00", "subject": "Flat 12 Riverside House: asbestos removal moved",
     "body": "Hello,\n\nThe removal of the kitchen floor tiles at Flat 12, Riverside House has moved from 19 November to 25 November because our licensed contractor is not available. Please do not start work in the kitchen before then.\n\nHollowell Council Asbestos Team"},
    {"id": "e19", "from": "council", "when": "today 09:15", "subject": "Flat 12 Riverside House: completion by 27 Nov?",
     "body": "Good morning,\n\nPlease confirm you will complete the works at Flat 12, Riverside House by 27 November 2026, so we can book the re-let inspection.\n\nHollowell Council Repairs"},
    {"id": "e20", "from": "buildmart", "when": "2026-11-10T07:55:00+00:00", "subject": "Order confirmation BM-77812",
     "body": "Thank you for your order: 40 x plasterboard 12.5mm, 10 x jointing compound. Delivery Thursday."},
]

# The firm's work calendar ("Marcus Limited"): planned work and deadlines. Times are UK local (GMT in November).
CALENDAR = [
    {"id": "c01", "date": "2026-11-23", "start": "09:00", "end": "10:00", "title": "Send quote: kitchen extension, Mr Ionescu, 14 Hawthorn Road",
     "detail": "Quote promised after the site visit on 19 Nov."},
    {"id": "c02", "date": "2026-11-24", "start": "10:00", "end": "11:00", "title": "Elm Avenue: electrical certificate due from Spark Right",
     "detail": "Promised 'next week' in their email of 17 Nov."},
    {"id": "c03", "date": "2026-11-24", "start": "18:00", "end": "21:00", "title": "Kingsway Unit 4: noisy work (after hours only)",
     "detail": "Facilities manager's rule: noisy work before 08:00 or after 18:00."},
    {"id": "c04", "date": "2026-11-25", "start": "08:00", "end": "16:00", "title": "Flat 12 Riverside: asbestos removal by council contractor",
     "detail": "Moved from 19 Nov (council asbestos team, 18 Nov). Do not work in the kitchen before then."},
    {"id": "c05", "date": "2026-11-26", "start": "08:00", "end": "17:00", "title": "Flat 12 Riverside: kitchen strip-out and refit",
     "detail": "After the asbestos removal."},
    {"id": "c06", "date": "2026-11-27", "start": "17:00", "end": "17:30", "title": "Flat 12 Riverside: council target completion",
     "detail": "Works order WO-2026-4471."},
    {"id": "c07", "date": "2026-11-28", "start": "09:00", "end": "09:30", "title": "Kingsway Unit 4: valuation date (main contract)",
     "detail": "Interim valuation on the 28th of each month."},
    {"id": "c08", "date": "2026-11-30", "start": "09:00", "end": "09:30", "title": "Kingsway Unit 4: payment notice to Fenwick Drylining",
     "detail": "Within 5 days of the 25 Nov due date."},
    {"id": "c09", "date": "2026-12-09", "start": "08:00", "end": "17:00", "title": "Elm Avenue: snagging and final photos", "detail": ""},
    {"id": "c10", "date": "2026-12-11", "start": "10:00", "end": "12:00", "title": "Elm Avenue: handover to Victoria Hartley", "detail": ""},
]

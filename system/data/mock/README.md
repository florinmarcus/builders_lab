# Mock data for the demo

Agreed with Florin, 19 Nov 2026; jobs updated the same day to match `requirements/prototype.md`.
All people, firms, addresses, numbers and contract terms are invented. No resemblance to real firms is intended.
Outside parties use `*.example.com` addresses (reserved, cannot belong to anyone).
Phone numbers use Ofcom's drama range `07700 900xxx`. "Today" means the day the today batch is run (demo day, 21 Nov 2026).

## Firm

**Oakline Build Ltd**, a small general builder in the made-up town of Hollowell.

| Person | Role |
|---|---|
| Dan Oakley | Owner (the builder in the demo, inbox owner) |
| Mike Turner | Site lead |
| Jamie Cole | Apprentice |

## Job 1: Hartley house refurbishment, 22 Elm Avenue

Private client, high-end, design and build. Client: Victoria Hartley. Architect: Lena Marsh, Marsh Studio.

| # | When | From | What | Attachment |
|---|---|---|---|---|
| 1 | 6 Oct | Lena Marsh | Brief and drawing schedule | Drawing schedule (PDF) |
| 2 | 10 Oct | Dan | Quote, contract sum £148,500 + VAT | Quote Q-2051 (PDF) |
| 3 | 13 Oct | Victoria Hartley | Accepts the quote | – |
| 4 | 27 Oct | Ashby Joinery | Kitchen joinery quote | Quote (PDF) |
| 5 | 29 Oct | Stoneworks Hollowell | Stone flooring quote | Quote (PDF) |
| 6 | 10 Nov | Victoria Hartley | "Here's our WhatsApp chat, as you asked" | WhatsApp chat export (`.txt`) |
| 7 | 12 Nov | Lena Marsh | Client wants the kitchen–dining wall removed; engineer visit to book | – (sets up moment 4) |
| 8 | 17 Nov | Spark Right Electrical | "Certificate to follow" | – (stays missing) |
| 9 | today | Victoria Hartley | "Can you send the final account with the changes?" | – (moments 5, 6) |

The WhatsApp export holds two clear approvals and one non-approval:

- Underfloor heating in the kitchen, +£2,400: "Yes, go ahead."
- Pocket door to the utility room, +£850: "Approved, thanks."
- Garden lighting: "Sounds nice, let's talk next week." This is **not** an approval. It tests that we don't invent one.

## Job 2: Unit 4 office refit, Kingsway Business Park

Commercial, occupied building. Oakline is main contractor. Employer: Brightmoor Analytics Ltd. Employer's QS: Carter Cost Consulting. Facilities manager: Paul Reid.

| # | When | From | What | Attachment |
|---|---|---|---|---|
| 10 | 1 Oct | Carter Cost Consulting | Signed contract particulars | Contract particulars (PDF): JCT Intermediate Building Contract 2016, dates and payment terms |
| 11 | 5 Oct | Paul Reid (FM) | Working hours and permits: noisy work before 8:00 or after 18:00 only, hot works permit | – |
| 12 | 8 Oct | Fenwick Drylining | Subcontractor documents | RAMS (PDF); insurance certificate, expires 30 Nov 2026 (PDF) |
| 13 | 9 Oct | Volt Electrical | Subcontractor insurance | Insurance certificate, expired 31 Oct 2026 (PDF) |
| 14 | 28 Oct | Dan | Interim application 2 to the QS | Application for payment (PDF) |
| 15 | today | Fenwick Drylining | Subcontract application for payment 2, £18,240 | Application (PDF) (moment 7) |

**Mock contract terms** (invented for the demo; the real rule text comes from the regulations corpus):

- **Main contract:** monthly interim valuation date on the 28th. Due date is 7 days after the valuation date. Final date for payment is 14 days after the due date. Pay less notice no later than 5 days before the final date.
- **Fenwick subcontract:** due date is the 25th of the month. Final date for payment is 21 days after the due date. Payment notice within 5 days of the due date. Pay less notice no later than 5 days before the final date.
- **What moment 7 should give:** Fenwick application 2 has a due date of 25 Nov. Payment notice by 30 Nov. Final date for payment 16 Dec. Pay less notice by 11 Dec. Our code calculates these from the stored terms; the model does not do date sums.

## Job 3: Flat 12, Riverside House (council void, Hollowell District Council)

| # | When | From | What | Attachment |
|---|---|---|---|---|
| 16 | 28 Oct | Council repairs | Works order WO-2026-4471, schedule-of-rates lines, target date 27 Nov | Works order (PDF) |
| 17 | 29 Oct | Council repairs | Asbestos survey, HSG264 layout | Refurbishment and demolition survey (PDF) |
| 18 | 5 Nov | Council repairs | Gas capped, keys at the housing office | Gas capping note (PDF) |
| 19 | today | Council repairs | "Please confirm you will finish by 27 Nov" | – |

The survey is built to test "never say no asbestos":

- **Kitchen floor tiles:** chrysotile found.
- **Hall textured ceiling:** sampled, none found.
- **Bedroom 2:** locked, not accessed, presumed to contain asbestos.
- **Scope:** kitchen and bathroom only.

## Not linked to a job

| # | When | From | What |
|---|---|---|---|
| 20 | 10 Nov | BuildMart Supplies | Order confirmation |

## Required items per job type (our mock list, not a legal rule)

- **Residential refurbishment:** signed quote, approved variations, electrical certificate, building control sign-off if notifiable, final photos.
- **Commercial fit-out:** contract particulars, subcontractor RAMS, subcontractor insurance in date, payment notices issued, completion photos.
- **Council void:** works order, asbestos survey covering the work area, gas capping or safety record, electrical test, completion photos.

## Generate the emails

```
python system/data/mock/generate.py --today 2026-11-21
```

Writes `out/history/*.eml` (17 past emails) and `out/today/*.eml` (3 for demo day) with PDF and text attachments.
Scenario data: `scenario.py`. Document text matches `db_seed.sql`. Output is not committed.

## How it runs (ADR 0005)

- **Inbox:** the builder's own Gmail. Address set in `.env` (`BUILDER_INBOX`), never in the repo.
- **Label:** every mock or simulated email and every demo draft carries the Gmail label `oakline-demo`. Nothing outside it is touched.
- **Reset:** delete everything labelled `oakline-demo`, empty the database, and re-import all emails except the "today" ones. Same start every time.
- **Today batch:** import the "today" emails (9, 15, 19), all at once or one by one.
- **Live simulator:** send from an allowed address (`.env`, `SIMULATOR_SENDERS`) to `<inbox>+<persona>@gmail.com`. The simulator re-imports the email with the persona as sender, labels it and deletes the original. Emails from other senders are ignored.

| Alias | Shows as |
|---|---|
| `+hartley` | Victoria Hartley (client, Elm Avenue) |
| `+architect` | Lena Marsh, Marsh Studio |
| `+fm` | Paul Reid, facilities manager, Kingsway Business Park |
| `+qs` | Carter Cost Consulting |
| `+council` | Hollowell District Council repairs |
| `+mike` | Mike Turner (site lead) |
| `+jamie` | Jamie Cole (apprentice) |

## Gmail set-up (once, on your laptop)

1. **Google Cloud project:** open console.cloud.google.com, create a project (e.g. `builders-lab-demo`).
2. **Turn on the Gmail API:** APIs & Services, Library, "Gmail API", Enable.
3. **Consent screen:** Google Auth Platform (or "OAuth consent screen"): app name `Builders Lab demo`, user type External,
   your email as support contact. Under Audience, add your Gmail as a **test user**. Leave it in Testing.
4. **Client:** Clients, Create client, type **Desktop app**. Download the JSON file.
5. **Log in and load** (Git Bash, from the repo root):
   ```
   pip install -e ".[gmail]"
   export BUILDER_INBOX=<your gmail> SIMULATOR_SENDERS=<your second address>
   python system/data/mock/gmail_demo.py auth --client-secret <path to the downloaded JSON>
   python system/data/mock/gmail_demo.py load
   python system/data/mock/gmail_demo.py status
   ```
   The browser opens once; Google warns the app is unverified (it is yours, in testing): continue.
   The login is saved in `~/.config/builders-lab/gmail-token.json`. Testing-mode logins can expire after 7 days.

### 6. Give the server the Gmail login (so "check my emails" sees live email, and the simulator can run there)

Git Bash on your laptop (MSYS_NO_PATHCONV stops Git Bash from mangling the /builders-lab paths):

```
export MSYS_NO_PATHCONV=1
aws ssm put-parameter --region eu-west-2 --type SecureString --overwrite --name /builders-lab/prod/secrets/gmail_token --value "$(cat ~/.config/builders-lab/gmail-token.json)"
aws ssm put-parameter --region eu-west-2 --type SecureString --overwrite --name /builders-lab/prod/secrets/builder_inbox --value <your gmail>
aws ssm put-parameter --region eu-west-2 --type SecureString --overwrite --name /builders-lab/prod/secrets/simulator_senders --value <your second address>
```

Then on the server (or ask Claude to run it):

```
sudo BASE=/opt/builders-lab SSM_PREFIX=/builders-lab/prod /opt/builders-lab/repo/deploy/scripts/env-from-ssm.sh
cd /opt/builders-lab/repo/deploy && source scripts/common.sh
dc up -d app                                   # app now also reads the Gmail label
dc --profile simulator up -d simulator         # live simulator on the server (no laptop needed)
dc logs -f simulator                           # watch it
```

## On demo day

```
python system/data/mock/gmail_demo.py reset        # clean start: trash demo emails and demo drafts, reload the past
python system/data/mock/gmail_demo.py today        # the three morning emails arrive (or: today e09)
python system/data/mock/gmail_demo.py simulate     # leave running; send from your second address to <gmail>+council@...
```

What the tool touches: only emails labelled `oakline-demo`, drafts addressed only to `*.example.com`, and emails from
`SIMULATOR_SENDERS` to your `+persona` addresses. Everything else in your inbox is left alone.

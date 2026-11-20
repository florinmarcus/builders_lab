-- Small test seed straight into Postgres, so the MCP tools work before Gmail ingestion exists.
-- Mock data only (see README.md in this folder). Re-runnable: it replaces the mock firm's data but keeps
-- the firm row, its API keys, traces and quota usage. Message ids match generate.py, so ingesting the
-- generated emails later skips the ones already here.
-- Load with: python -m builders_api.db.seed

insert into firms (slug, name) values ('oakline', 'Marcus Limited') on conflict (slug) do update set name = excluded.name;
delete from facts          where firm_id = (select id from firms where slug = 'oakline');
delete from contract_terms where firm_id = (select id from firms where slug = 'oakline');
delete from attachments    where firm_id = (select id from firms where slug = 'oakline');
delete from emails         where firm_id = (select id from firms where slug = 'oakline');
delete from jobs           where firm_id = (select id from firms where slug = 'oakline');
delete from clients        where firm_id = (select id from firms where slug = 'oakline');
delete from staff          where firm_id = (select id from firms where slug = 'oakline');
delete from quota_limits   where firm_id = (select id from firms where slug = 'oakline');
delete from gmail_sync_state where firm_id = (select id from firms where slug = 'oakline');

insert into job_types (code, name) values
  ('residential_refurb', 'Residential refurbishment'),
  ('commercial_fitout',  'Commercial fit-out'),
  ('council_void',       'Council void')
on conflict (code) do update set name = excluded.name;

delete from required_items;
insert into required_items (job_type_code, code, label, satisfied_by, sort_order) values
  ('residential_refurb', 'signed_quote',        'Signed or accepted quote',               '{quote_accepted}', 1),
  ('residential_refurb', 'approved_variations', 'Client approval for each change',        '{approval}', 2),
  ('residential_refurb', 'electrical_cert',     'Electrical certificate',                 '{electrical_certificate}', 3),
  ('residential_refurb', 'bc_signoff',          'Building control sign-off (if notifiable work)', '{building_control_completion}', 4),
  ('residential_refurb', 'final_photos',        'Final photos',                           '{completion_photos}', 5),
  ('commercial_fitout',  'contract',            'Contract particulars',                   '{contract_particulars}', 1),
  ('commercial_fitout',  'sub_rams',            'Subcontractor RAMS',                     '{rams}', 2),
  ('commercial_fitout',  'sub_insurance',       'Subcontractor insurance in date',        '{insurance_certificate}', 3),
  ('commercial_fitout',  'payment_notices',     'Payment notices issued',                 '{payment_notice}', 4),
  ('commercial_fitout',  'completion_photos',   'Completion photos',                      '{completion_photos}', 5),
  ('council_void',       'works_order',         'Works order',                            '{works_order}', 1),
  ('council_void',       'asbestos_survey',     'Asbestos survey covering the work area', '{asbestos_survey}', 2),
  ('council_void',       'gas',                 'Gas capping or gas safety record',       '{gas_capping_note,gas_safety_record}', 3),
  ('council_void',       'electrical_test',     'Electrical test',                        '{electrical_test}', 4),
  ('council_void',       'completion_photos',   'Completion photos',                      '{completion_photos}', 5);

create temporary table f on commit drop as select id from firms where slug = 'oakline';

insert into quota_limits (firm_id, metric, daily_limit)
select id, m, l from f, (values ('documents_ingested', 200), ('tool_calls', 500), ('bedrock_usd', 2)) v(m, l);

insert into staff (firm_id, name, role, email)
select id, n, r, e from f, (values
  ('Florin Marcus',  'Owner',      'florin@marcus-ltd.example.com'),
  ('Mike Turner', 'Site lead',  'mike.turner@marcus-ltd.example.com'),
  ('Jamie Cole',  'Apprentice', 'jamie.cole@marcus-ltd.example.com')) v(n, r, e);

insert into clients (firm_id, name, kind, email, phone)
select id, n, k, e, p from f, (values
  ('Victoria Hartley',            'private',    'victoria.hartley@mail.example.com', '07700 900123'),
  ('Brightmoor Analytics Ltd',    'commercial', 'facilities@brightmoor.example.com', '07700 900456'),
  ('Hollowell District Council',  'council',    'repairs@hollowell-council.example.com', '07700 900789')) v(n, k, e, p);

insert into jobs (firm_id, client_id, job_type_code, ref, title, address, start_date, target_date, match_terms)
select f.id, c.id, v.t, v.ref, v.title, v.addr, v.s::date, v.e::date, v.terms::text[]
from f cross join (values
  ('Victoria Hartley', 'residential_refurb', 'ELM-22', 'Hartley house refurbishment', '22 Elm Avenue, Hollowell', '2026-10-20', '2026-12-11', '{hartley,"elm avenue"}'),
  ('Brightmoor Analytics Ltd', 'commercial_fitout', 'KWY-4', 'Unit 4 office refit', 'Unit 4, Kingsway Business Park, Hollowell', '2026-10-12', '2026-12-18', '{kingsway,"unit 4",brightmoor,fenwick}'),
  ('Hollowell District Council', 'council_void', 'RIV-12', 'Flat 12, Riverside House (council void)', 'Flat 12, Riverside House, Hollowell', '2026-11-02', '2026-11-27', '{riverside,"WO-2026-4471"}')
) v(client, t, ref, title, addr, s, e, terms)
join clients c on c.name = v.client and c.firm_id = f.id;

-- Emails: (key, job ref or null, from name, from address, subject, sent at, body)
create temporary table e_in (k text, ref text, fn text, fa text, subj text, at timestamptz, body text) on commit drop;
insert into e_in values
 ('e03', 'ELM-22', 'Victoria Hartley', 'victoria.hartley@mail.example.com', 'Re: Quote Q-2051, 22 Elm Avenue', '2026-10-13 19:05+01',
  'Hi Florin, we are happy with quote Q-2051 for £148,500 + VAT and would like to go ahead. Please treat this email as our acceptance. Victoria'),
 ('e06', 'ELM-22', 'Victoria Hartley', 'victoria.hartley@mail.example.com', 'Our WhatsApp chat about the changes', '2026-11-10 21:14+00',
  'Hi Florin, as you asked, here is our WhatsApp chat so you have the changes in writing. Victoria'),
 ('e08', 'ELM-22', 'Spark Right Electrical', 'office@sparkright.example.com', '22 Elm Avenue: electrical works complete', '2026-11-17 16:20+00',
  'Florin, first and second fix complete at 22 Elm Avenue. Testing done. Electrical installation certificate to follow next week once the paperwork is back from the office.'),
 ('e10', 'KWY-4', 'Carter Cost Consulting', 'qs@carter-cost.example.com', 'Unit 4 Kingsway: signed contract particulars', '2026-10-01 10:30+01',
  'Please find attached the signed contract particulars for the Unit 4 office refit. Interim valuations monthly on the 28th.'),
 ('e12', 'KWY-4', 'Fenwick Drylining', 'admin@fenwick-drylining.example.com', 'Unit 4 Kingsway: RAMS and insurance', '2026-10-08 08:45+01',
  'Attached our RAMS for partitions and ceilings at Unit 4, and our public liability insurance certificate.'),
 ('e13', 'KWY-4', 'Volt Electrical', 'jobs@volt-electrical.example.com', 'Insurance certificate', '2026-10-09 12:10+01',
  'As requested, our insurance certificate for the Kingsway job.'),
 ('e15', 'KWY-4', 'Fenwick Drylining', 'admin@fenwick-drylining.example.com', 'Unit 4 Kingsway: application for payment 2', '2026-11-21 08:10+00',
  'Please find attached our application for payment no. 2 for Unit 4, Kingsway Business Park: £18,240.00 + VAT.'),
 ('e16', 'RIV-12', 'Hollowell Council Repairs', 'repairs@hollowell-council.example.com', 'Works order WO-2026-4471, Flat 12 Riverside House', '2026-10-28 09:00+00',
  'Please find attached works order WO-2026-4471 for void works at Flat 12, Riverside House. Target completion 27 November 2026.'),
 ('e17', 'RIV-12', 'Hollowell Council Repairs', 'repairs@hollowell-council.example.com', 'Asbestos survey, Flat 12 Riverside House', '2026-10-29 11:30+00',
  'Attached the refurbishment and demolition asbestos survey for Flat 12 (kitchen and bathroom).'),
 ('e18', 'RIV-12', 'Hollowell Council Repairs', 'repairs@hollowell-council.example.com', 'Flat 12 Riverside House: gas capped, keys', '2026-11-05 14:00+00',
  'Gas supply capped, note attached. Keys can be collected from the housing office.'),
 ('e20', null, 'BuildMart Supplies', 'orders@buildmart.example.com', 'Order confirmation BM-77812', '2026-11-10 07:55+00',
  'Thank you for your order: 40 x plasterboard 12.5mm, 10 x jointing compound. Delivery Thursday.');

create temporary table e_ids (k text, id uuid) on commit drop;
with ins as (
  insert into emails (firm_id, gmail_message_id, from_name, from_address, subject, sent_at, body_text, job_id,
                      filing_reason, ingest_status, ingested_at)
  select f.id, e.k || '.mail@marcus-ltd.example.com', e.fn, e.fa, e.subj, e.at, e.body, j.id,
         case when j.id is null then 'no job matched' else 'seed data' end, 'done', now()
  from e_in e cross join f left join jobs j on j.ref = e.ref and j.firm_id = f.id
  returning id, gmail_message_id)
insert into e_ids select split_part(gmail_message_id, '.', 1), id from ins;

-- Attachments: (key, email key, filename, mime, doc type, doc date, expires, pages, text)
create temporary table a_in (k text, ek text, fname text, mime text, dt text, dd date, exp date, pages int, txt text) on commit drop;
insert into a_in values
 ('a06', 'e06', 'WhatsApp Chat with Victoria Hartley.txt', 'text/plain', 'chat_export', '2026-11-10', null, null,
'03/11/2026, 18:02 - Florin Marcus: Hi Victoria, the plumber says underfloor heating in the kitchen is possible now the floor is up. Extra £2,400 + VAT.
03/11/2026, 19:40 - Victoria Hartley: Yes, go ahead with the underfloor heating in the kitchen.
06/11/2026, 08:15 - Florin Marcus: For the utility room we could fit a pocket door instead of the hinged door. £850 + VAT extra.
06/11/2026, 12:31 - Victoria Hartley: Approved, thanks. Pocket door it is.
08/11/2026, 17:05 - Florin Marcus: Also thinking about garden lighting along the path, roughly £1,900.
08/11/2026, 20:12 - Victoria Hartley: Sounds nice, let''s talk next week.'),
 ('a10', 'e10', 'Unit 4 Kingsway - Contract Particulars.pdf', 'application/pdf', 'contract_particulars', '2026-10-01', null, 3,
'Contract particulars. JCT Intermediate Building Contract 2016. Employer: Brightmoor Analytics Ltd. Contractor: Marcus Limited. Works: office refit, Unit 4, Kingsway Business Park. Date of possession 12 October 2026. Completion date 18 December 2026. Interim valuation dates: the 28th of each month. Due date: 7 days after each interim valuation date. Final date for payment: 14 days from the due date. Pay less notice: not later than 5 days before the final date for payment. Working hours: building occupied; noisy work outside 08:00-18:00 only.'),
 ('a12a', 'e12', 'Fenwick Drylining - RAMS Unit 4.pdf', 'application/pdf', 'rams', '2026-10-07', null, 6,
'Risk assessment and method statement. Fenwick Drylining Ltd. Partitions and suspended ceilings, Unit 4, Kingsway Business Park. Hazards: work at height (podium steps), manual handling of boards, dust from cutting (on-tool extraction, FFP3 masks), occupied building: segregate work area, noisy cutting outside office hours.'),
 ('a12b', 'e12', 'Fenwick Drylining - Public Liability Certificate.pdf', 'application/pdf', 'insurance_certificate', '2026-10-01', '2026-11-30', 1,
'Certificate of insurance. Insured: Fenwick Drylining Ltd. Public liability limit £5,000,000. Period of insurance: 1 December 2025 to 30 November 2026.'),
 ('a13', 'e13', 'Volt Electrical - Insurance Certificate.pdf', 'application/pdf', 'insurance_certificate', '2025-11-01', '2026-10-31', 1,
'Certificate of insurance. Insured: Volt Electrical Ltd. Public liability limit £2,000,000. Period of insurance: 1 November 2025 to 31 October 2026.'),
 ('a15', 'e15', 'Fenwick Drylining - Application for Payment 2.pdf', 'application/pdf', 'application_for_payment', '2026-11-20', null, 2,
'Application for payment no. 2. Subcontractor: Fenwick Drylining Ltd. Main contractor: Marcus Limited. Project: Unit 4, Kingsway Business Park. Gross valuation to date £36,480.00. Less previous payments £18,240.00. Amount applied for £18,240.00 + VAT. Payment due date under the subcontract: 25 November 2026.'),
 ('a16', 'e16', 'WO-2026-4471 Works Order.pdf', 'application/pdf', 'works_order', '2026-10-28', null, 2,
'Works order WO-2026-4471. Hollowell District Council. Property: Flat 12, Riverside House. Void works to lettable standard. Lines: strip out and renew kitchen units; renew bathroom suite; full electrical test; redecorate throughout. Target completion date: 27 November 2026. Asbestos: see survey before starting work.'),
 ('a17', 'e17', 'Asbestos Survey - Flat 12 Riverside House.pdf', 'application/pdf', 'asbestos_survey', '2026-10-24', null, 8,
'Refurbishment and demolition survey (HSG264). Property: Flat 12, Riverside House. Survey date 22 October 2026. Scope: kitchen and bathroom only. Results: Kitchen floor tiles, vinyl floor tiles, sample S01, chrysotile detected. Hall ceiling textured coating, sample S02, no asbestos detected. Bedroom 2: no access (locked), presumed to contain asbestos. Areas outside scope not surveyed.'),
 ('a18', 'e18', 'Gas Capping Note - Flat 12.pdf', 'application/pdf', 'gas_capping_note', '2026-11-04', null, 1,
'Gas capping note. Flat 12, Riverside House. Gas supply capped at the meter on 4 November 2026 by the council''s gas contractor.');

create temporary table a_ids (k text, id uuid) on commit drop;
with ins as (
  insert into attachments (firm_id, email_id, filename, mime_type, size_bytes, sha256, page_count, text_content,
                           job_id, document_type, document_date, expires_on)
  select f.id, ei.id, a.fname, a.mime, length(a.txt), encode(digest(a.txt, 'sha256'), 'hex'), a.pages, a.txt,
         em.job_id, a.dt, a.dd, a.exp
  from a_in a cross join f join e_ids ei on ei.k = a.ek join emails em on em.id = ei.id
  returning id, email_id, filename)
insert into a_ids select a.k, ins.id from ins join e_ids ei on ei.id = ins.email_id join a_in a on a.ek = ei.k and a.fname = ins.filename;

-- Facts as the extraction step would produce them (prompt version marks them as seed data).
insert into facts (firm_id, job_id, email_id, attachment_id, fact_type, summary, quote, value, fact_date, source_page, prompt_version)
select f.id, em.job_id, ei.id, ai.id, v.t, v.s, v.q, v.val::jsonb, v.d::date, v.p, 'seed'
from f, (values
 ('e03', null,  'quote_accepted', 'Client accepted quote Q-2051 (£148,500 + VAT) by email', 'we are happy with quote Q-2051 for £148,500 + VAT and would like to go ahead', '{"quote": "Q-2051", "amount_gbp": 148500}', '2026-10-13', null),
 ('e06', 'a06', 'approval', 'Client approved underfloor heating in the kitchen, +£2,400 + VAT', 'Yes, go ahead with the underfloor heating in the kitchen.', '{"change": "Underfloor heating, kitchen", "amount_gbp": 2400, "channel": "WhatsApp", "approved_by": "Victoria Hartley"}', '2026-11-03', null),
 ('e06', 'a06', 'approval', 'Client approved pocket door to the utility room, +£850 + VAT', 'Approved, thanks. Pocket door it is.', '{"change": "Pocket door, utility room", "amount_gbp": 850, "channel": "WhatsApp", "approved_by": "Victoria Hartley"}', '2026-11-06', null),
 ('e06', 'a06', 'discussion', 'Garden lighting (about £1,900) discussed, NOT approved', 'Sounds nice, let''s talk next week.', '{"change": "Garden lighting", "amount_gbp": 1900, "status": "not approved"}', '2026-11-08', null),
 ('e08', null,  'certificate_pending', 'Electrician says the electrical installation certificate will follow next week', 'Electrical installation certificate to follow next week', '{"certificate": "electrical installation certificate"}', '2026-11-17', null),
 ('e17', 'a17', 'asbestos_item', 'Kitchen vinyl floor tiles: chrysotile detected (sample S01)', 'Kitchen floor tiles, vinyl floor tiles, sample S01, chrysotile detected', '{"room": "Kitchen", "material": "vinyl floor tiles", "result": "chrysotile detected", "sample": "S01", "survey_type": "refurbishment and demolition"}', '2026-10-22', 3),
 ('e17', 'a17', 'asbestos_item', 'Hall textured ceiling: no asbestos detected in sample S02 (this sample only)', 'Hall ceiling textured coating, sample S02, no asbestos detected', '{"room": "Hall", "material": "textured coating", "result": "no asbestos detected in sample", "sample": "S02"}', '2026-10-22', 4),
 ('e17', 'a17', 'asbestos_item', 'Bedroom 2 not accessed (locked): presumed to contain asbestos', 'Bedroom 2: no access (locked), presumed to contain asbestos', '{"room": "Bedroom 2", "result": "presumed", "reason": "no access"}', '2026-10-22', 4),
 ('e17', 'a17', 'survey_scope', 'Survey scope: kitchen and bathroom only. Other areas not surveyed', 'Scope: kitchen and bathroom only', '{"covered": ["Kitchen", "Bathroom"]}', '2026-10-22', 2),
 ('e16', 'a16', 'key_date', 'Target completion date 27 Nov 2026', 'Target completion date: 27 November 2026', '{"what": "target completion"}', '2026-11-27', 1)
) v(ek, ak, t, s, q, val, d, p)
join e_ids ei on ei.k = v.ek
join emails em on em.id = ei.id
left join a_ids ai on ai.k = v.ak;

insert into contract_terms (firm_id, job_id, party, counterparty, contract_form, valuation_day_of_month,
                            due_days_after_valuation, due_day_of_month, final_date_days_after_due,
                            payment_notice_days_after_due, pay_less_days_before_final, source_attachment_id)
select f.id, j.id, v.party, v.cp, v.form, v.vd, v.dav, v.dd, v.fin, v.pn, v.pl, ai.id
from f join jobs j on j.ref = 'KWY-4' and j.firm_id = f.id, (values
  ('main',        'Brightmoor Analytics Ltd', 'JCT Intermediate Building Contract 2016', 28, 7, null, 14, 5, 5, 'a10'),
  ('subcontract', 'Fenwick Drylining Ltd',    'Subcontract (mock terms)',               null, null, 25, 21, 5, 5, 'a15')
) v(party, cp, form, vd, dav, dd, fin, pn, pl, ak)
left join a_ids ai on ai.k = v.ak;

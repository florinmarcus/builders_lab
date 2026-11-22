# Design: regulations corpus and search

**Owner: the corpus session.** Up: [architecture](../ARCHITECTURE.md). Decisions: ADR 0008 (harvest, storage, fingerprints), ADR 0010 (parsing). Corpus files: [corpus/README.md](../../corpus/README.md).

Updated 20 Nov 2026 after the parsing design session; coverage readers for web pages and XML 22 Nov 2026. Solid = built. Dashed = planned.

## Pipeline

Everything up to the database runs on Florin's PC, in Claude Code. The server only stores and searches.

```mermaid
flowchart LR
    src["Source sites<br/>legislation.gov.uk,<br/>GOV.UK, HSE"] --> harvest["harvest.py<br/>versions by hash"]
    harvest --> raw[("corpus/raw<br/>+ S3 eu-west-2")]
    harvest --> rec["corpus/versions<br/>records (git)"]
    raw --> lib["Parser: library pass<br/>lxml for XML and HTML,<br/>pdfplumber (parse_pdf,<br/>parse_guide, parse_flats,<br/>parse_booklet, parse_adoc)"]
    lib -.-> chk["Model check<br/>(Claude Code)<br/>tables, diagrams,<br/>unclear cases"]
    fixes[("Saved fixes (git)<br/>by content fingerprint")] -.-> chk
    chk -.-> fixes
    chk -.-> tree[("corpus/parsed<br/>document trees (JSON)<br/>not in git")]
    lib -.-> img[("Images<br/>diagrams, photos")]
    tree --> chunk["Chunker<br/>chunk.py → corpus/chunks<br/>+ chunk-report.md"]
    chunk --> emb["embed.py<br/>Titan V2, London"]
    emb --> fts[("Local index: BM25 (SQLite FTS5)<br/>+ vectors, localsearch.py<br/>(not yet on the server)")]
    chunk --> fts
    chunk -.-> pg[("Postgres + pgvector<br/>on the server")]
    img -.-> pg
```

Parse and chunk are separate steps. The parsed tree can be checked on its own, and chunkers can change without parsing again. Parsed trees and images are rebuilt from raw files, so they stay out of git.

## Parse: library first, model fills the gaps

```mermaid
flowchart TB
    f["Raw file"] --> kind{"Kind"}
    kind -->|"legislation XML"| x["Walk the XML:<br/>Parts, regulations, Schedules"]
    kind -->|"PDF"| p["Pages, page labels,<br/>bookmarks, text blocks"]
    x --> clean["Clean:<br/>drop amendment markers,<br/>keep notes as metadata"]
    p --> strip["Strip: headers, footers,<br/>watermark, contents, index"]
    strip --> fi["Repair dropped 'fi'<br/>by word check (logged)"]
    fi --> lift["Lift diagrams and photos<br/>out of the text"]
    lift --> tab["Tables: library grid"]
    tab --> model["Model check:<br/>every table, every diagram,<br/>unclear repairs"]
    clean --> dup["Duplicate Schedule 1 Parts:<br/>code guesses E or W"]
    dup --> model
    model --> saved[("Saved fix<br/>reused next run")]
    model --> out["Document tree"]
```

### Guidance PDF chapters (parse_pdf, 22 Nov 2026)

```mermaid
flowchart TD
    line["line after page 1"] --> big{"2x body size, or 1.5x in a condensed font,<br/>or PART / SCHEDULE / Contents set larger?"}
    big -->|yes| ch["chapter title"]
    big -->|no| only{"is 'Contents' the only chapter title after page 1?<br/>(the whole document would be skipped as front matter)"}
    only -->|no| body["heading or body text"]
    only -->|yes| style["chapter style = the largest later lines whose text<br/>is a contents-page entry; every line in that style"]
    style --> ch
    big -->|"yes, but a phone number or web address ('Tel: 0800 ...'),<br/>or 'Schedule 3 to the ...' (running text)"| body
```

Before the first chapter title (coverage check, S105, 22 Nov 2026):

```mermaid
flowchart TD
    p1["page 1"] --> t{"large line?"}
    t -->|"first block"| title["the document's title (skipped)"]
    t -->|"a later large line with 3+ body lines under it"| ch1["chapter (MS34 'Introduction')"]
    pg["page before the first chapter"] --> kind{"what is on it?"}
    kind -->|"'Contents', or most lines are entries<br/>or page numbers (also in their own column)"| skip["skipped"]
    kind -->|"© or Crown copyright (imprint)"| skip
    kind -->|"under 40 words near body size"| skip
    kind -->|"40+ words near body size<br/>(cover blurb, key facts, a circular's letter)"| front["kept in a 'Front matter' chapter;<br/>small print there is text;<br/>a cover thumbnail's own text is dropped"]
```

HHSRS operating guidance Parts 1 and 2, the HHSRS enforcement guidance and three Procurement Act short guides parsed
to empty trees before the contents-page rule (parking lot S103). Before the front-matter rule INDG285 kept only its
back page, MS34 lost paragraphs 1 to 12, and three circulars lost their letter (S105).

### Guidance PDF figures (parse_pdf, 22 Nov 2026)

parse_pdf reads the drawn shapes and page sizes too (`read_guidance`). A figure is only made where there is ink
besides words, and it is cut to that ink, not to its words.

```mermaid
flowchart TD
    page["page of short scattered lines"] --> ink{"ink besides words?"}
    ink -->|"text in drawn boxes,<br/>10+ boxes (a form),<br/>images (10% of page)<br/>with words beside them"| fig["figure-pN, cut to all its shapes"]
    ink -->|"a ruled table holds most lines"| tab["table-pN (a table, not a figure)"]
    ink -->|"none: letter, title page"| text["text"]
    small["block of short small-print lines"] --> shp{"6+ shapes or an image among them?"}
    shp -->|yes| drawn["drawing: labels + ink between<br/>the running text above and below"]
    shp -->|"no: address, copyright, footnotes"| text
    cap["caption"] --> side{"document prints captions<br/>above figures? (vote)"}
    side -->|no| up["ink between the caption and the<br/>running text above it, in its column"]
    side -->|yes| down["ink between the caption and the<br/>running text below it"]
    up & down --> panel["+ a tinted panel behind both, a frame under the caption,<br/>side panels level with the drawing, labels near it,<br/>Note/Source/Key/* lines under it"]
    capf["'Figure N' in another weight of the body font<br/>with ink ending just above it"] --> cap
    dir["'(left)' / '(above)' in the caption"] --> photo
    img["image"] --> sig{"signature or logo?"}
    sig -->|"'Yours faithfully'/'Signed' above,<br/>name + job title below,<br/>letterhead on page 1, © or www below"| none["not a figure"]
    sig -->|"barcode over a web address"| none
    sig -->|"cover thumbnail: 'web-friendly version of leaflet INDG231',<br/>'HSG85 (Third edition) Published 2013' under it<br/>(is_cover_thumbnail, shared with coverage.py)"| none
    sig -->|"'Signed by ...' in the cell to its left;<br/>a crest and department name at the top of page 1<br/>(signature_or_logo: one function for parse_pdf and coverage.py)"| none
    sig -->|"no caption, page 1 is content (40+ words), below the title,<br/>4%+ of the page, not a thin band, no text set on it"| p1["figure photo-p1-x-y (CIS54, CIS78, CIS79)"]
    sig -->|no| photo["photo of the caption below it (or above, by the vote);<br/>photos stacked with no text between, a grid named<br/>'Top row ... Bottom row', or a block of photos for<br/>'(a)–(c)' / '12a and b', make one figure;<br/>running text or another photo beside it limits the crop"]
    photo -->|"labels beside the image,<br/>or image cut into tiles"| up
```

Small print with no caption becomes a table only when it looks like one (22 Nov 2026, from the model checks that
said "not a table"):

```mermaid
flowchart TD
    blk["small-print block, no caption near"] --> sub{"subscripts inside a larger<br/>line's box ('week', 'Aeq')?"}
    sub -->|yes| drop["dropped: part of the formula"]
    sub -->|no| foot{"footnote at the page foot ('1 Exemptions apply'),<br/>or the publisher's imprint (ISBN, 'Printed and published by')?<br/>a one-cell 'table' (page number) is not a ruled table"}
    foot -->|yes| text["text (small print)"]
    foot -->|no| tab{"cut into cells (gaps; not the gap after a bullet)<br/>or inside a ruled table with 2+ filled columns?<br/>(a box drawn round text is not a grid)"}
    tab -->|no| text
    tab -->|yes| t["table without a caption (model check)"]
    t --> lone{"only one short line, nothing joined,<br/>no ruled table?"}
    lone -->|yes| text
    t --> far{"small print more than a page after<br/>the last rows of this table?"}
    far -->|yes| t2["a new table"]
```

Pages and frames (coverage check, S105, 22 Nov 2026):

```mermaid
flowchart TD
    txt["unnumbered running text, next line on a new page"] --> ends{"last page ended a sentence,<br/>or the section already covers two pages?"}
    ends -->|yes| new["new text section (cited on its own page)"]
    ends -->|no| on["runs on (one sentence over the page break)"]
    frame["ruled 'table' 85%+ of the page wide and tall"] --> fr["a frame round the page: not a table,<br/>and the text inside it is cut into columns"]
```

Ruled tables with no caption (coverage check, S105, 22 Nov 2026). EH40 Table 1 (13 pages under a chapter title) and
the circulars' Annex tables were running text:

```mermaid
flowchart TD
    g["ruled table found by pdfplumber,<br/>no 'Table N' caption at or near it"] --> d{"2+ filled columns in 2+ rows, and cells of a few words,<br/>or a header row of short headings, or the same columns<br/>and edges as a data grid just before it (run-on)?"}
    d -->|yes| tp{"'Table N' printed just above,<br/>its table still empty?"}
    tp -->|yes| cap["that captioned table takes the rows (L108)"]
    tp -->|no| tab["a table section per page, named after its heading<br/>(parent-table-pN); model check fills the grid"]
    d -->|no| text["stays text: paragraphs in a frame, a form, a flow chart's boxes<br/>(coverage: accepted with a reason)"]
```

Running text is body-size text of six words or more not set in a drawn box, starting at a left edge many long
lines share, at a bullet or list number, or in a block of such lines; plus the lines hanging under it, subheadings
over it, bold-italic callouts, "Box N" titles, headings, captions (also caption-like lines the caption rules did not
take) and lines hanging under a caption. Sub-captions ("3b Machined ...") are labels and widen the figure's column
to every part. A ruled table that does not reach the caption is not the figure's ink; one level with the drawing is
(a key). A large picture on its own is trimmed only of white margin (`photo_whole`). Labels join a drawing when a
run of their words is within 30pt (60pt for a short label) and is not a text column's run (`page_edges`). A long
thin line is a rule only when no other shape touches it (a pipe in a gas diagram is not). Hand-made test documents
without `graphics` keep the older text rules. Crops a rule cannot fix are kept with a named defect
(`cropcheck accept`, parking lot S98).

### Approved Documents (parse_adoc, built 20 Nov 2026)

The 2019-layout Approved Documents are read by fonts, sizes and colours: 26pt chapters, 20/15pt headings, semibold paragraph numbers, white diagram captions on a green band, bold table captions, green words as links to key terms. Edition banners ("Effective until 1 September 2029", "effective from 2 September 2029") date the two copies of Appendices B and C. Letters dropped from "fi"/"fl" by the PDF font are put back by checking the document's own words, and counted. Diagram crops are made for the model check; `images: check-only` in `sources.yaml` keeps them from users.

Diagram crops follow the drawn frame (22 Nov 2026). Each AD diagram sits in a ruled box with its caption on a filled band: at the bottom (2013+ layout) or the top (classic layout). The parser finds the band under the caption's first word, then joins every shape that lines up with it (a box or line as wide as the band, or a side drawn at its edge, even in pieces) until a gap or another band. The crop is that frame plus 3pt. Text inside the frame is the diagram's labels; in the classic layout small notes straight under the frame are too. A band with no frame (AD F Diagram 3.1, AD J Diagram 16) keeps the older text rule.

```mermaid
flowchart LR
    cap["Diagram caption"] --> band["filled band<br/>under its first word"]
    band --> join["join shapes as wide as the band<br/>or on its edges, end to end"]
    join -->|"frame found"| crop["crop = frame + 3pt<br/>labels = text inside<br/>(classic: + notes under it)"]
    join -->|"band only"| old["text rule<br/>(labels back to the last body line)"]
```

Amendment booklets and short notes have no 26pt chapters, so the largest heading size used on two or more pages
is the chapter size (simple mode). A booklet is also known by its "List of amendments" title pages, one per volume
(22 Nov 2026). The June 2022 AD B booklet reprints whole sections in the 2019 layout, with 26pt titles; it used
to lose Volume 1 (pages 2 to 17), because the parser skipped everything before the first 26pt title.

```mermaid
flowchart LR
    pdf["Booklet PDF"] --> list{"'List of amendments'<br/>title page?"}
    list -->|"yes"| simple["simple mode:<br/>its size = chapters"]
    list -->|"no, but no 26pt titles"| simple2["simple mode:<br/>largest heading size<br/>on 2+ pages = chapters"]
    simple --> re["26pt title of a reprinted<br/>section = heading in the<br/>booklet's chapter"]
    simple --> vol["'Volume N' in the list title:<br/>a chapter code used in<br/>another volume gets vN-<br/>(v2-section-3)"]
```

Pages before the first chapter are skipped (cover, contents). The older editions (AD B 2006, C, D, E, G, H, J, M
volume 2) print a "Main changes" page there (page 2); a bold heading starting "MAIN CHANGES" now opens a "Main changes"
chapter, read like any other. AD A and AD C 2013 print that page again near the back (the inside cover spread): the
repeat is a tree issue, and the document ends there.

Requirement boxes are `requirement` sections. In the 2019 layout they are small print under green bands; in the
classic editions (AD B 2006, AD M volume 2, AD Q) they are body-size type in a ruled frame, which used to come out
as running text with "Requirement Limits on application" glued to the line before. A ruled table whose first cell
starts "Requirement", with a "Limits on application" column and body-size lines inside, is now the box; its grid
goes to the model check like any requirement box.

Three smaller rules (22 Nov 2026): a line with every character printed twice ("AA ppeerrssoonn", AD P 2013's
quoted regulation 12(6A), AD K's Diagram 9.1 caption) is halved and counted in `repairs`, as tripled lines already
were; a ruled table with no caption, set in body type, with two or more filled rows (the FAQ notes' "which edition
applies" tables) is a table named after the heading above it; and in a booklet a one- or two-line block of small
print is a replacement table row, kept as text, not skipped as a picture of a page.

### Home Office fire risk assessment guides (parse_guide, built 22 Nov 2026)

The 2006 "Fire safety risk assessment" sector guides and the disabled people supplement share one template that
parse_pdf (numbered paragraphs, captions under pictures) reads badly. `parse_guide` takes these 13 files of
`fso-guidance-collection`; `sources.yaml` names them by version id prefix (`parser.files`), parse_pdf skips them
and `build` runs both. Styles are told apart by role, since the guides use different fonts.

```mermaid
flowchart TB
    pdf["read_pdf (shared)<br/>+ drawn shapes, page sizes,<br/>superscripts, column jumps"] --> clean["Drop side tab, page numbers,<br/>two-page covers, off-page copies"]
    clean --> blocks["Blocks first: Case study boxes (shaded),<br/>figures and tables from captions<br/>(picture above or below: what is drawn<br/>next to the caption), ruled tables,<br/>bold flow charts without caption"]
    blocks --> order["Reading order: gutter per page,<br/>wide blocks are their own band"]
    order --> tree["Part › Section or Step › 1.3 heading ›<br/>sub-heading › paragraph (one per paragraph);<br/>ids &lt;guide&gt;:&lt;local id&gt;"]
    tree --> crop["render_images: photos cut to their<br/>pixels below the caption (photo_box below=True)"]
```

Known source quirks are listed as tree issues (a figure or table number printed twice, a heading printed without
its number). Shortcuts: parking lot S90 to S92.

### Purpose-built flats guide and Home Office booklets (parse_flats, parse_booklet, built 22 Nov 2026)

The other five PDFs of `fso-guidance-collection` have two more layouts, so each has its own parser
(`sources.yaml` `parser.files`). Both reuse GuideBuilder's helpers (drawn objects, ruled tables, sections) and
parse_pdf's reading and rendering; their own passes leave parse_guide's output unchanged.

```mermaid
flowchart TB
    pdf["read_pdf (shared, as parse_guide)"] --> kind{"Layout"}
    kind -->|"Fire safety in purpose-built<br/>blocks of flats (193 pages)"| fl["parse_flats: drop footer,<br/>put drawn bullets back,<br/>frames with a bold lead = boxes"]
    kind -->|"4 booklets 2023-2024<br/>(two columns)"| bk["parse_booklet: drop running header,<br/>callouts = boxes, form answer<br/>boxes dropped, two-column order"]
    fl --> figs["Figures: bold caption ABOVE,<br/>picture in its column, grown from<br/>what is drawn nearest the caption;<br/>a key across two pictures goes to both"]
    bk --> figs
    figs --> pics["Pictures without caption: what is<br/>drawn close together (photos 2pt,<br/>drawings 4pt); booklet drawings take<br/>in their small-print labels and keys"]
    pics --> blank["drop_blank_pictures: an image<br/>that renders as one flat colour"]
    fl --> tree1["Part › 41. Introduction › sub-heading ›<br/>one paragraph per numbered paragraph<br/>(41.1, A1.49), run on across boxes,<br/>figures and pages; Key points box;<br/>glossary = 55 definitions"]
    bk --> tree2["Chapter › 16pt heading › 15pt › bold 12pt ›<br/>paragraph; ids &lt;booklet&gt;:&lt;local id&gt;"]
```

Printing gaps (paragraphs 71.6, 82.2, 83.3 not printed; 79.9 to 79.11 blacked out; "1.62" for A1.62) are tree
issues and listed in `corpus/README.md`. Shortcuts: parking lot S93 to S95.

### Coverage check: raw file against tree (built 22 Nov 2026)

Six PDFs once parsed to empty trees and nobody noticed (parking lot S103). `system/rag/coverage.py` now compares
each raw PDF with its tree. Plain code, no model (ADR 0006). It reads the PDF itself with pdfplumber, not through
the parser's reader, so reader bugs show up too.

```mermaid
flowchart LR
    raw["Raw PDF<br/>(words, images,<br/>ruled tables)"] --> why["Name why a word may be dropped:<br/>header, footer, page number, cover,<br/>contents, index, back cover,<br/>sideways, overprint, tree issue,<br/>inside a figure crop"]
    tree["Tree<br/>(title, text, labels,<br/>footnotes, grids)"] --> cmp
    why --> cmp["Compare words<br/>per document and per page"]
    cmp --> txt{"Page with 40+ words<br/>and under 10% in the tree?<br/>Document over 5%<br/>missing for no reason?"}
    raw --> img{"Image of 1%+ of the page<br/>in no figure crop and<br/>no named reason?"}
    raw --> tab{"Ruled table with no table<br/>section, or under 60% of<br/>its words in the tree?"}
    txt & img & tab -->|yes| flag["Flagged item"]
    flag --> acc{"Accepted by a person<br/>(corpus/coverage, git)?"}
    acc -->|no| fail["Report and test fail"]
```

Pages before the first section are judged as front matter; a parse_pdf "Front matter" chapter (content kept from
before the first chapter title) does not end them, so the imprint page after a cover blurb is still front matter.
A "ruled table" as large as the page is a frame round it, not a table. Images use parse_pdf's own signature, logo and
cover-thumbnail rule (S107). A tree issue that quotes the few lines it skipped explains only those lines; one that
skips a whole page explains the page. "A short page" counts upright words only (not a cover's sideways spine). A
ruled table wholly inside a figure crop is kept as the picture, as the words inside a crop are.

Words are compared as a multiset after normalising (case, ligatures, punctuation, hyphens, bullets). Split words
("W hat") and ligatures the font dropped ("fre" for "fire") still match. The report also lists tree words that
are not in the PDF: from text fields (parser glue, such as words run together) and from model-built grids apart.

#### Web pages and legislation XML (S106, built 22 Nov 2026)

Two more readers, plain lxml, not the parsers' own readers. Both give blocks of visible text; the same check runs on
both (`check_blocks`).

```mermaid
flowchart LR
    html["Web page<br/>(read_html_raw)"] --> hb["blocks: p, li, td, h2 ...<br/>a &lt;br&gt; or space parts words"]
    xml["Legislation XML<br/>(read_xml_raw)"] --> xb["blocks: provisions (nearest id);<br/>titles and a P1's number apart"]
    hb --> hr["named reasons: site header, footer, menus,<br/>breadcrumbs, skip link, cookie banner, feedback,<br/>back to top, screen-reader text, last updated,<br/>sidebar, related, share and print, forms"]
    xb --> xr["named reasons: annotations, metadata,<br/>title page, explanatory note, signature,<br/>footnotes, equation pictures, 'SCHEDULES'"]
    hr & xr --> chk{"block with 3+ words in no 3-word run<br/>of the tree? document over 1% missing?<br/>table not in a table section (pages)<br/>or the tree (laws)? picture in no figure?"}
    chk -->|yes| flag["Flagged item<br/>(accept with a reason, or fix the parser)"]
```

A class mark matches whole parts of a class name split at - and _ ("hse-back-to-top__link" has back-to-top;
"research" does not have search). parse_html now uses the same rule; it used to match substrings, and the heading
ids "searching-for-opportunities", "declare-and-share" and "...shared-ownership-homes" dropped real headings.

What the readers found and the parsers now do (22 Nov 2026):

```mermaid
flowchart TD
    subgraph html["parse_html"]
        h1["mark in a class name or (not on headings) an id,<br/>by whole parts, not substrings"]
        h2["role=navigation, pagination, 'Next page',<br/>'printable version': dropped"]
        h3["text left inside a list after an item:<br/>joins that item ('time period')"]
        h4["empty h3/h4 straight before a heading of its level:<br/>a group label holding that one heading<br/>(the heading keeps its id)"]
    end
    subgraph leg["parse_legislation"]
        l1["P1group holding several P1: one provision each,<br/>with the group's title (195 paragraphs were lost)"]
        l2["several unnumbered P in a P1group: all kept"]
        l3["BlockAmendment: quoted titles and numbers kept<br/>('30C (1) This section ...')"]
        l4["Schedule's Reference ('Regulation 12(7)') kept as its text"]
        l5["Formula: one line of text (math_text)"]
        l6["table: title, caption text, cell paragraphs parted"]
        l7["Schedule 1: all paragraphs of a header cell (RA1);<br/>limits beside an uncoded requirement (Part T)"]
        l8["a Figure beside the paragraphs: named in an issue"]
    end
```

Pictures on web pages are kept only as alt text; 38 GOV.UK pictures with no alt text are accepted with that reason
(S121). Shortcuts: S122.

### The model-check step (built 20 Nov 2026)

Same steps for every document. Runbook: `.claude/skills/corpus-document/SKILL.md`. Code: `system/rag/checks.py`.

```mermaid
flowchart LR
    tree["Parsed tree<br/>open checks"] --> exp["checks export<br/>one packet per check:<br/>fixed instructions,<br/>answer format, images,<br/>family template"]
    exp --> sub["One subagent per packet<br/>(Claude Code)"]
    sub --> ans["answers.jsonl"]
    ans --> save["checks save<br/>rules: row and sentence counts,<br/>heading rows, one layout<br/>per table family"]
    save -->|"refused"| sub
    save --> fixes[("corpus/fixes (git)")]
    fixes --> lint["checks lint<br/>(also a test)"]
    fixes --> reparse["Parse again:<br/>0 checks"]
    reparse --> review["checks review<br/>sheet of figure crops"]
```

Tables in one family (same title before " for ", like the HSG227 worked examples) share one layout: the first one goes alone, and the rest get its saved fix as a template. A table whose title only looks like a family's, but whose printed layout differs (checked on the page), is listed in `NOT_A_FAMILY` in `checks.py` with the reason (AD H Table 12, AD L Volume 2 Table 5.4).

A model answer can vary between runs, so every model fix is saved in `corpus/fixes/` (git) with a fingerprint of the content it is about, and reused. The parser lists what is still open as `checks`. Re-parsing gives the same result unless we choose to redo a fix. Counting fixes shows what the library should learn next.

## Data model

```mermaid
erDiagram
    SOURCE ||--o{ VERSION : "has"
    VERSION ||--o{ SECTION : "parsed into"
    SECTION ||--o{ SECTION : "parent of"
    SECTION ||--o{ CHUNK : "split into"
    SECTION ||--o{ FIGURE : "has"
    SECTION ||--o{ TABLE : "has"
    TABLE ||--o{ CHUNK : "whole + row sentences"
    FIGURE ||--o| CHUNK : "caption + description"
    VERSION ||--o{ DEFINITION : "defines"
    CHUNK }o--o{ DEFINITION : "uses (own marks)"
    CHUNK ||--o{ REFERENCE : "cites"
    REFERENCE }o--o| SECTION : "points to"
    SECTION ||--o{ AMENDMENT : "changed by"
    VERSION ||--o{ FIX : "model fixes"

    SOURCE { string id "br2010, adb, hse-hsg264" string kind "legislation, approved-document, hse-guidance" string legal_weight "law, statutory-guidance, approved-code, guidance" string licence string mode }
    VERSION { string version_id date valid_from date valid_to string sha256 }
    SECTION { string id "reg-7, B1, adb-2.5" string parent_id string heading_path "breadcrumb" string printed_page string applies_to "E, W, E+W" date valid_from date valid_to text full_text }
    CHUNK { string id string section_id "parent section" string chunk_type "clause, paragraph, requirement, table-row, figure, change-note" string source_id string kind string legal_weight string version_id date valid_from date valid_to string applies_to string heading_path "breadcrumb" string printed_page string url text text text embed_text "breadcrumb + text" vector embedding tsvector keywords "codes like 7.6.3 kept whole" }
    REFERENCE { string from_chunk string to_section "empty if unresolved" string words "requirement B1" boolean resolved }
    DEFINITION { string term string text string scope "own document only" }
    FIGURE { string number string title string labels string description string image_path }
    TABLE { string number string grid_json }
    AMENDMENT { string by "SI number" date date string note }
    FIX { string file_sha256 string page string kind string result }
```

- **Two links between chunks and sections.** A section is *split into* its own chunks (one to many). A chunk *cites* other sections through REFERENCE (many to many). REFERENCE keeps the original words and whether code resolved them, so unresolved references are easy to list.
- **Filter fields are copied onto every chunk**, so search filters without joins.
- **The breadcrumb goes into the embedded text** (`embed_text`), for example "Building Regulations › Part B › B1 Means of warning and escape › ...". A short paragraph alone often does not say what it is about.
- **Keyword search from the start.** Each chunk has a Postgres full-text column, so hybrid search can be added later without re-loading. Codes like "7.6.3", "B1" and "M4(1)" must stay whole.
- **`kind` and `legal_weight`** come from `corpus/sources.yaml`. Answers must say "the law requires" (law) or "the guidance says" (approved documents are statutory guidance; HSE approved codes of practice such as L143 have special legal standing; other HSE documents are guidance).
- **AMENDMENT** comes from the legislation's change notes: which later law changed a clause, and when.
- **FIX** is a saved model correction, one per file and page.

## Chunk units

| Document | One chunk per | Notes |
|---|---|---|
| Building Regulations 2010 | regulation | Split at (1), (2) only when long. The ingestion report counts and lists every split. |
| Schedule 1 | requirement (B1, M4(1)) | With its "limits on application" text. Each is a graph node. |
| Regulation 2 | definition | Definition items, not one large chunk. |
| AD B, HSG264, HSG227 | numbered paragraph (2.5, 47) | With its lettered lists and heading path. HSG264 boxes are their own chunks. |
| Tables | table, plus one sentence per row | Model checks every table against the page image. |
| Diagrams, photos | figure | Original image cut from the PDF (a photo is cut to its own pixels above its caption, since the PDF's image box can be padded); caption, labels and model description are searchable. No Mermaid redraw. |
| AD B change notes | change note | Linked to the sections they mention. |

### Scope: versions in force from 1 January 2025 (ADR 0016, built 22 Nov 2026)

One rule in `system/rag/corpus.py` (`in_scope`): a version is in scope when its `valid_to` is empty or on or
after 1 January 2025. `chunk.py`, `load.py`, model checks and crop checks (`checks.current_trees`) and the coverage check
(`coverage.versions_in_scope`, S120) use it. Older
versions keep their records and raw files; their trees are not chunked, loaded or checked, and their open checks
stay open. Pages that list old editions side by side (`adb-historical`) give every file the page's date and an open
end, so `sources.yaml` lists each part's own dates from the documents (`in_force_parts`); chunks of those parts
carry the edition's dates, not the page's.

```mermaid
flowchart LR
    rec["version record<br/>valid_to"] --> rule{"in_scope<br/>valid_to empty or<br/>>= 2025-01-01"}
    over["sources.yaml<br/>in_force_parts<br/>(dates printed in<br/>the documents)"] -.-> rule
    rule -->|yes| work["chunk, load,<br/>model checks,<br/>crop checks,<br/>coverage check"]
    rule -->|no| keep["record and raw file kept;<br/>not chunked or checked"]
```

### Chunks as built (20 Nov 2026)

`python -m system.rag.chunk` writes one JSON line per chunk to `corpus/chunks/<source>/<version>.jsonl` (not in git, rebuilt from the trees) and `corpus/chunk-report.md` (in git). Each chunk carries `id`, `chunk_type`, the filter fields above, `text`, `embed_text` (breadcrumb + text), `references` (resolved to a section id in the same document, to another document such as `br2010`, or unresolved), `terms` (key terms the text marks) and, for figures, `image_path` and `image_display`. Legal weight comes from `kind` in `sources.yaml` (legislation = law, Approved Documents = statutory guidance, HSE "L" books = approved code, the rest guidance), or from `legal_weight` if a source sets it. Regulations and paragraphs longer than 2,500 characters are split (regulations at (1), (2); guidance at list items), and every split is listed in the report.

## Search

**Built 20 Nov 2026 (not wired to the server yet):** `system/rag/localsearch.py` does the ADR 0013 hybrid search locally: Titan V2 vectors from `system/rag/embed.py` (exact cosine in memory), BM25 keywords, top 50 each, RRF (k = 60), one passage per section, Amazon Rerank in Frankfurt to 5. First tries: vectors find what keywords miss ("licence" finds CAR 2012 regulation 8). Earlier keyword-only notes: keyword search over the chunks with SQLite FTS5 (Porter stemmer, codes such as "B1" and "7(2)" in their own column, bm25), filtered by date and country. It follows the server contract. First tries on the builder questions (`research/domain/builder-questions.md`) find the right documents for most questions, but miss where the builder's word differs from the document's ("licence" vs "licensable work"). **Decided (ADR 0013):** hybrid search: Titan V2 vectors (London) and BM25 keywords, top 50 each, reciprocal rank fusion, then Amazon Rerank (Frankfurt) to 5. Evals compare the variants.


```mermaid
sequenceDiagram
    participant S as search_regulations (server)
    participant R as rag.search
    participant DB as Postgres
    S->>R: question, as_of_date, country (default England)
    R->>DB: chunks where applies_to includes the country<br/>and valid on as_of_date
    DB-->>R: vector top 50 + BM25 top 50, merged (RRF)<br/>then re-rank to 5 (ADR 0013)
    R->>DB: definitions used, linked sections
    R-->>S: passages (text, source, section,<br/>edition_date, url)
    S-->>S: show up to 5
    Note over S,DB: Planned: get_section(section_id) returns the parent's full text<br/>("small to big"). Needs agreement with the server session.
```

- Wales-only text is kept and marked. Search takes a country, England by default; Wales is a filter, not a re-parse.
- Each passage says its legal weight, so answers can tell law from guidance.
- Dates come from the versions. AD B appendices B and C are split into "until 1 Sep 2029" and "from 2 Sep 2029".
- Citations use the printed page number. The file page is internal only.
- Embedding model, hybrid search and re-ranking are not decided yet. Evals decide them.

## Pilot

Documents: Building Regulations 2010 (current, plus the 2026 versions of 1 Jul, 20 Jul, 1 Oct and 6 Nov), Approved Document B volume 1 (current), HSG264, HSG227 (priority assessment, Appendix 3).

Done when these counts pass as automatic tests:

| Check | Expected |
|---|---|
| Regulations in the current Building Regulations | 170 |
| Schedule 1 requirements | every one in the tables, with an E or W label on duplicated Parts K, M, O |
| AD B tables and diagrams | 16 tables, 56 diagrams |
| Numbered paragraphs | match contents pages and bookmarks |
| Broken "fi" words left | 0 |
| Header, footer or watermark text in chunks | 0 |
| New duplicate Schedule 1 Part without a label | test fails |

## What the files look like (profiled 20 Nov 2026)

- **Building Regulations XML:** 15 Parts, 170 regulations, 8 Schedules. Wales-only regulations sit in a separate `Versions` block, linked by `AltVersionRefs`. Schedule 1 is 22 tables; Parts K, M and O appear twice with no extent attribute (the notes say which copy is which). Before 1 Oct 2015, Schedule 1 is images only. Amendments are tagged (`Addition`, `Substitution`, `Repeal`); 197 defined terms (`Term`); 3,209 references (`CitationSubRef`).
- **AD B volume 1:** 200 pages, text on every page, page labels give printed numbers. Watermark on every page; diagrams are vectors whose labels mix into the text; one font drops "fi" (about 200 words). Neither library extracts the 16 tables cleanly. Defined terms are green links to Appendix A.
- **HSG264:** 73 pages, clean. pdfplumber extracts the material assessment table (Appendix 4) well. No priority assessment table.
- **HSG227:** 85 pages (2002, older than CAR 2012: show its date). Priority assessment: Table 3, page 54, with worked examples in Tables 4 to 14.

## Agreed interface with the server

```mermaid
flowchart LR
    tool["search_regulations<br/>(server)"] -->|"search(question, as_of_date)"| rag["rag package<br/>system/rag/"]
    rag -->|"passages: text, source,<br/>section, edition_date, url"| tool
    tool -.->|"if rag missing"| fb["fallback passages"]
```

Contract: [system/rag/README.md](../../system/rag/README.md). Proposed additions, to agree with the server session:

- `search(question, as_of_date, country="E")`: a country argument, England by default.
- `get_section(section_id)`: the parent section's full text.
- Optional passage keys: `section_id`, `applies_to`, `kind`, `legal_weight`, `printed_page`, `image_url`.

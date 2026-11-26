# Parser rules: parse_pdf (guidance PDFs)

Detailed rules for HSE and other guidance PDFs. Up: [ingest design](../design.md). Flow: [parse](../flows/parse.md). Code: `system/rag/parse_pdf.py`.

## Guidance PDF chapters (parse_pdf, 22 Nov 2026)

```mermaid
flowchart TD
    line["line after page 1"] --> big{"2x body size, or 1.5x in a condensed font,<br/>or PART / SCHEDULE / Contents set larger?"}
    big -->|yes| ch["chapter title<br/>(ANNEX A: an appendix, 23 Nov 2026)"]
    big -->|no| only{"is 'Contents' the only chapter title after page 1?<br/>(the whole document would be skipped as front matter)"}
    only -->|no| body["heading or body text"]
    only -->|yes| style["chapter style = the largest later lines whose text<br/>is a contents-page entry; every line in that style"]
    style --> ch
    big -->|"yes, but a phone number or web address ('Tel: 0800 ...'),<br/>'Schedule 3 to the ...' (running text),<br/>or a contents entry with dot leaders"| body
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

"ANNEX A" set larger than body text (building regulations circulars: 20pt over 12pt) counts like PART and
SCHEDULE (23 Nov 2026); before, the annex title and its notice of approval ran on in the last paragraph
("ENQUIRIES"). This was the largest single cause in the semantic check's guidance PDFs. Annex titles also match
in small capitals read as lower case ("Annex c"), without a space ("AnnexA", a scan) and with a point ("Annex B.1"),
and may be a point or two smaller than the largest. A circular whose only titles are annexes is read like a document
without chapters up to the first annex (its letter and page 1 are content), then one appendix per annex. A picture
over a "Signed ..." line is a signature, not a figure.

HHSRS operating guidance Parts 1 and 2, the HHSRS enforcement guidance and three Procurement Act short guides parsed
to empty trees before the contents-page rule (parking lot S103). Before the front-matter rule INDG285 kept only its
back page, MS34 lost paragraphs 1 to 12, and three circulars lost their letter (S105).

## Guidance PDF figures (parse_pdf, 22 Nov 2026)

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

Two columns (S128 fix 3, 23 Nov 2026), in the reader (`split_columns`):

```mermaid
flowchart TD
    pg["page"] --> gap{"a wide gap inside 3+ lines at one x?"}
    gap -->|yes| g["gutter"]
    gap -->|no| st{"5+ body lines start right of a third of the page,<br/>5+ end left of that x, side by side over the same heights,<br/>at most one line crossing? (lines at slightly<br/>different heights are never joined)"}
    st -->|yes| g
    st -->|no| one["one column"]
    g --> mv["move the gutter left to lines starting up to 25pt before it<br/>('It will:' over bullet text) when no left line ends in that strip"]
    mv --> cut["cut joined lines at the gutter (a 4pt gap is enough there)"]
```

HSE headings and text after tables (S128 fix 2, 23 Nov 2026):

```mermaid
flowchart TD
    l["line, 12 words or fewer, starts upper case,<br/>no end stop, not boxed, not a caption or 'Page N'"] --> b{"bold, 2pt+ over body,<br/>at a text column's left edge?"}
    b -->|yes| h["heading"]
    b -->|no| m{"medium weight (Md, Medium, Semibold),<br/>0.5pt+ over body, under 1.5x,<br/>at the margin or a text column's edge?"}
    m -->|yes| r{"three or more lines in a row in that style?"}
    r -->|no| h
    r -->|"yes: a lead-in set large"| t["text"]
    m -->|no| t
    m -->|no| lf{"leaflets (fix 4): regular type 1.4-2x body, or bold at body size<br/>alone on its row, space above, 1.5-2.6x its size to the<br/>running text below, no wide gaps between words?"}
    lf -->|yes| h
    h --> w["second line joins when it starts in lower case or a bracket,<br/>or the two lines stand alone in that style"]
    cap["body-size table caption, rows read downwards"] --> stop{"a '3.6 ...' paragraph, or body text<br/>under the ruled grid (not 'Note:', '*', a key)?"}
    stop -->|yes| end1["the table ends there"]
    wp["heading at the top of a whole-page table<br/>or at the top of a grid run on from the page before"] --> h2["a heading; the table sits under it, no join"]
```

Tables over pages (S118, 23 Nov 2026). A table that ran on to the next page became a second table, named after the
heading above it (HSG248 Table 4.1), or its rows were taken by the next table's caption (Table 3.2 into Table 3.3):

```mermaid
flowchart TD
    g["ruled grid at the top of a page"] --> a{"nothing above it but a 'continued' label,<br/>and the lowest grid on the page before ends<br/>in its last 150pt with the same columns and width?"}
    a -->|no| old["as before: its own table, or text"]
    a -->|yes| o{"the table section holding that grid,<br/>no chapter or heading begun since,<br/>under 4 pages long?"}
    o -->|yes| j["more rows of that table: one section,<br/>spans on both pages, one model check<br/>(a one-row, one-cell grid too: the last cell)"]
    o -->|no| old
    j --> c["a caption below with its own grid does not take these rows;<br/>'Table A9.3 continued' / 'Table continues' kept in the table's text"]
```

A table caption with no rows next to it takes a grid up to 120pt below, and the note printed between (HSG248 Table
A9.5). Ids of later tables and notes stay as they were. Long tables are cut into parts of four pages (S132).

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


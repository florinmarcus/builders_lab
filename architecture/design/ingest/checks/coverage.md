# Check: coverage (raw file against tree)

Counts words, images and tables the tree lost. Up: [ingest design](../design.md). Flow: [checks](../flows/checks.md). Code: `system/rag/coverage.py`. Report: `corpus/coverage.md`.


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

## Web pages and legislation XML (S106, built 22 Nov 2026)

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
        l8["a Figure beside the paragraphs or inside a<br/>numbered paragraph (car2012 label): named in an issue"]
    end
```

Pictures on web pages are kept only as alt text; 38 GOV.UK pictures with no alt text are accepted with that reason
(S121). Shortcuts: S122.


# Parser rules: fire safety guides (parse_guide, parse_flats, parse_booklet)

Up: [ingest design](../design.md). Flow: [parse](../flows/parse.md). Code: `system/rag/parse_guide.py`, `parse_flats.py`, `parse_booklet.py`.

## Home Office fire risk assessment guides (parse_guide, built 22 Nov 2026)

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

## Purpose-built flats guide and Home Office booklets (parse_flats, parse_booklet, built 22 Nov 2026)

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




def test_hse_headings_over_a_column_and_medium_sub_headings_are_headings():
    """S128 (HSG248): "Records and reporting of sampling" (13pt bold) starts at the left edge of a text column
    beside the figures, not at the page's margin, and "Video evidence" is set in 11pt medium condensed oblique:
    both were read as body text, so the paragraphs under them sat under the heading before."""
    L, Bd, Md = "HelveticaNeueLTStd-LtCn", "HelveticaNeueLTStd-BdCn", "HelveticaNeueLTStd-MdCnO"
    lines = [ln(2, 98, "4 Bulk sampling", 28.0, "HelveticaNeue-Medium", x0=57)]
    lines += [ln(2, 140 + 12 * k, "4.1 Samples should be taken by trained people using the right tools for the job." if k == 0 else
                 "and sealed in a labelled container before they leave the room where they were taken.", 10.0, L, x0=57)
              for k in range(10)]
    lines += [ln(2, 300, "Records and reporting of sampling", 13.0, Bd, x0=176),
              ln(2, 326, "4.2 The sampling records and report should include the following as a minimum:", 10.0, L, x0=320),
              *[ln(2, 338 + 12 * k, "the name and address of the sampling organisation and the site sampled here", 10.0, L, x0=320)
                for k in range(6)],
              ln(2, 430, "Video evidence", 11.0, Md, x0=57),
              ln(2, 450, "4.3 Videos may also be taken of the areas that are the reason for any failure of the work.", 10.0, L, x0=57),
              *[ln(2, 462 + 12 * k, "and kept with the report so that the client can see what the analyst saw on site.", 10.0, L, x0=57)
                for k in range(6)],
              ln(2, 560, "These new requirements come into", 12.0, "HelveticaNeueLTStd-Md", x0=57),
              ln(2, 577, "Force on 1 October 2023 for all", 12.0, "HelveticaNeueLTStd-Md", x0=57),
              ln(2, 594, "Responsible Persons in England", 12.0, "HelveticaNeueLTStd-Md", x0=57)]
    lines += [ln(3, 140 + 12 * k, "4.4 Labels must show the sample number, the date and the name of the person who took it" if k == 0 else
                 "so that the laboratory can match each sample to the record made on site by the analyst.", 10.0, L, x0=176)
              for k in range(8)]
    t = build_tree({"lines": lines, "rects": [], "images": [], "page_count": 3}, META)
    heads = {s["title"] for s in t["sections"] if s["type"] == "heading"}
    assert {"Records and reporting of sampling", "Video evidence"} <= heads
    assert sec(t, "para-4-2")["heading_path"][-2] == "Records and reporting of sampling"
    assert sec(t, "para-4-3")["heading_path"][-2] == "Video evidence"
    assert not any(h.startswith(("These new", "Force on", "Responsible")) for h in heads)  # three lines set large: a lead-in, not headings


def test_body_text_after_a_ruled_table_is_not_kept_in_the_table():
    """S128 (HSG248): under a body-size table caption the rows ran on until a numbered paragraph "12. ...";
    paragraphs numbered "3.6 ..." and body text printed under the ruled table were kept in the table's text (as if
    they were notes). Now they end the table; a note under it ("Note: ...") stays."""
    L, M = "HelveticaNeueLTStd-LtCn", "HelveticaNeueLTStd-MdCn"
    lines = [ln(2, 98, "3 Competence", 28.0, "HelveticaNeue-Medium", x0=57)]
    lines += [ln(2, 140 + 12 * k, "3.5 Relevant topics are listed in Table 3.1 and might be run in house or outsourced." if k == 0 else
                 "and the employer should keep a record of the training each analyst has completed.", 10.0, L, x0=57)
              for k in range(8)]
    lines += [ln(2, 300, "Table 3.1 Topics to be covered in analyst development programmes", 10.0, M, x0=57),
              ln(2, 325, "All staff Field staff", 10.0, M, x0=61),
              ln(2, 339, "Awareness training for asbestos Working in confined spaces", 10.0, L, x0=61),
              ln(2, 353, "Safe handling of chemicals Working at heights", 10.0, L, x0=61),
              ln(2, 380, "Note: Field staff also need the all staff topics.", 10.0, L, x0=57),
              ln(2, 400, "3.6 Analysts who will have to enter enclosures must complete practical training on RPE.", 10.0, L, x0=57),
              ln(2, 412, "The training should include the full decontamination process in a unit on site.", 10.0, L, x0=57)]
    tables = [_grid(2, 320, 365, [["All staff", "Field staff"], ["Awareness training for asbestos", "Working in confined spaces"],
                                  ["Safe handling of chemicals", "Working at heights"]], 57, 419)]
    t = build_tree({"lines": lines, "rects": [], "images": [], "page_count": 2, "tables": tables}, META)
    tab = sec(t, "table-3-1")
    assert "Working at heights" in tab["text"] and "Note: Field staff" in tab["text"]
    assert "3.6" not in tab["text"] and "decontamination" not in tab["text"]
    assert "decontamination" in sec(t, "para-3-6")["text"]

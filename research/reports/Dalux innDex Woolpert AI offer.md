# Big site platforms leave small builders open

Research dated 27 Nov 2026.

None of the three firms offers anything with Claude, Claude Code or MCP. None sells to 2 to 20 person builders. Dalux is a large BIM and site software suite. Its only AI is a tool that answers questions about one document at a time ([Dalux help](https://support.dalux.com/hc/en-us/articles/19728327500060-AI-Assistant)). innDex runs site access, inductions and RAMS sign-off for tier 1 contractors. Its AI is a photo-to-form tool for delivery notes, in pilot, plus a safety AI partner called Navatech ([innDex](https://www.inndex.co.uk/news/ai-delivery-notes)). Murphy Geospatial, now part of Woolpert, is a survey and digital twin services firm, not a software vendor. Its AI work runs on Google Gemini ([Woolpert](https://woolpert.com/solutions/data-and-technology/artificial-intelligence/)). So the direct threat to us is low. The useful link is that our users meet Dalux and innDex as subcontractors on bigger sites. We can help them deal with that.

## Dalux: one-document AI, read-only API, a community MCP server

Dalux is based in Copenhagen. It sells Box (documents), Field (snags and site checks), FM and Handover. It claims **1.7 million users**, and its customers include Strabag, Vinci and Hill Group ([Dalux](https://www.dalux.com/)). On G2, only **about 24% of reviewers are small businesses** ([G2](https://www.g2.com/compare/dalux-vs-fieldwire-by-hilti)). Two products are free: the BIM Viewer and Field Basic, a snag tool. Project members can be invited for free. In the UK, Box Pro is priced on the project's construction cost, with a three-month minimum ([G-Cloud](https://www.applytosupply.digitalmarketplace.service.gov.uk/g-cloud/services/878783968162363)).

Its AI Assistant started rolling out in **February 2026**. It summarises one PDF or Word file in Box and answers questions about it. It does not search across documents or projects. Image-heavy files and drawings may not work ([Dalux help](https://support.dalux.com/hc/en-us/articles/19728327500060-AI-Assistant)). Dalux does not say which model it uses. Its list of sub-processors names only AWS and Zendesk ([Dalux](https://dalux.com/it/subprocessors)). Guess: the model may run on AWS, perhaps Bedrock.

There is a REST API, but you need a company licence and a key from your Dalux customer success manager ([Dalux help](https://support.dalux.com/hc/articles/9544314902556)). Dalux says it has no sandbox, and no customisation beyond that ([G-Cloud](https://www.applytosupply.digitalmarketplace.service.gov.uk/g-cloud/services/878783968162363)). We found no white-labelling and no app marketplace. A community-built MCP server exists. Its notes say Field data is read-only through the API: no creating tasks or forms, and **no webhooks**, so you have to poll for changes ([GitHub](https://github.com/borgels/mcp-server-dalux)). Dalux has not built an MCP server of its own.

## innDex: tier 1 site gatekeeper, closed integrations, English and German only

innDex is a Welsh company, set up in 2017 ([Companies House](https://find-and-update.company-information.service.gov.uk/company/11003736)). It covers inductions, competency checks, access control, permits, RAMS, delivery notes and snagging. Customers include Morgan Sindall, VolkerFitzpatrick, Hill Group and Clarion Housing ([innDex](https://inndex.co.uk/)). In August 2026 Turner Construction made it the main partner for site access on its UN Plaza project in New York ([AI Journal](https://aijourn.com/turner-construction-appoints-inndex-as-main-technology-partner-on-its-landmark-united-nations-project/)). There are no public prices. Plans are per project per week, or enterprise deals ([Capterra UK](https://www.capterra.co.uk/software/1011810/inndex)).

Its RAMS module **approves, briefs and records sign-off**, and only briefed workers get through the gate. It does not write RAMS ([innDex RAMS](https://www.inndex.co.uk/rams)). On AI, the delivery note tool reads a photo and fills in the form, and was **in pilot from August 2026** ([innDex](https://www.inndex.co.uk/news/ai-delivery-notes)). The Navatech deal aims to bring AI to near-miss and hazard reporting, with no launch date given ([innDex](https://www.inndex.co.uk/en-us/news/inndex-and-navatech-partnership-to-bring-ai-to-frontline-safety-reporting)). Directory listings say Navatech gives guidance in 150+ languages, by voice, WhatsApp or Teams, with source citations ([SourceForge](https://sourceforge.net/software/product/nAI-Hub/)). No model vendor is named for either.

innDex links to Procore, Autodesk Construction Cloud and Asite ([innDex](https://www.inndex.co.uk/news/building-a-smarter-construction-ecosystem-inndex-autodesk-procore-asite)). We found no public API, developer docs, webhooks or white-labelling. There is no MCP server, official or community-built ([GitHub search](https://github.com/search?q=inndex&type=repositories)). The worker app lists **only English and German** ([App Store](https://apps.apple.com/us/app/inndex/id1457696057)). That matters, because many of our users' workers speak Romanian.

## Woolpert and Murphy: survey services on Google's stack

Woolpert, a US firm, completed its purchase of Murphy Geospatial on **27 March 2024**. Murphy had nearly 400 staff in Ireland and the UK ([Woolpert](https://woolpert.com/news/woolpert-acquires-ireland-based-murphy-geospatial-a-leading-european-geospatial-solutions-firm/)). It will fully rebrand as Woolpert by autumn 2027 ([Woolpert](https://woolpert.com/murphy-geospatials-transformation-to-woolpert-in-autumn-2027/)). The work is laser scanning, setting out and scan-to-BIM for clients like Mace at Manchester Airport ([Woolpert](https://woolpert.com/case-studies/geospatial-services-enable-transformation-at-manchester-airport/)). Its digital twins are **a service, "platform-agnostic"**, with no software product ([Woolpert](https://woolpert.com/solutions/data-and-technology/digital-twins/)).

Its AI is mostly for processing lidar and images, based on Allvision technology bought in 2023 ([PR Newswire](https://www.prnewswire.com/news-releases/woolpert-and-allvision-forge-strategic-agreement-to-enhance-geospatial-ai-capabilities-301989020.html)). It also has a Google Cloud consulting arm that builds agents with Vertex AI and Gemini. Its 2026 writing says nothing about MCP, Claude or OpenAI ([Woolpert Digital Innovations](https://innovations.woolpert.com/top-10-trends-shaping-ai-cloud-and-data-strategy-in-2026/)). Customisation here means each project is scoped as bespoke work. There is no public API. Murphy's own website could not be reached, so its UK offer was not checked directly.

## What this means for us

Here is the short version for each firm.

| Firm | Overlap with us | Threat | Best move |
|---|---|---|---|
| Dalux | Snags, handover, document Q&A | Low | Read-only import of a main contractor's snag list |
| innDex | RAMS and competency papers | Low now, maybe medium later | Help subs get their papers ready for innDex sites |
| Woolpert / Murphy | Almost none | Very low | Ignore for now |

What sets us apart is clear. None of the three offers **Romanian**, a **UK regulations library with citations**, the owner's own jobs, emails and payment dates, or a price a 2 to 20 person firm can pay. None works inside the Claude plan the user already has. Their AI sits inside their own app, on large sites.

The partnership options are thin. Dalux needs a company licence for its API. A small sub invited free onto a Dalux project probably cannot get a key (guess). So the practical route is to read the main contractor's PDF or Excel export. Or we could use the community MCP server where the main contractor gives access. innDex has no open API, so a data link would need a commercial deal once we have users (guess). A good feature that needs no deal: a "get ready for the innDex induction" check in Romanian, covering CSCS cards, right to work, RAMS and insurance. It would build on our existing subcontractor pack check (guess, product idea). Woolpert does not matter at our scale. Reading measured-survey PDFs for quotes could be a later feature, but those come from local surveyors, not Murphy (guess).

The threats to watch are two. First, if Dalux extends its assistant to search across snags and handover records, it would answer "what is missing before handover" for firms already on Dalux (guess). Second, if innDex brings in Navatech's multilingual voice guidance, Romanian workers on tier 1 sites would get site safety help in their own language (guess). Neither firm shows any sign of moving down to small firms, or into regulations advice, emails or payment notices.

## Conclusion

The big platforms are adding AI inside their own walls, on the main contractor's licence. So the small sub on their sites stays outside it, with no API key and no Romanian. That is our gap, and we should build towards it. Treat Dalux and innDex as places our users have to deal with, not as rivals. Make our assistant the one that gets a small firm's papers and snag lists in order for those sites. Check again in mid-2027 for two things: Dalux search across documents, and Navatech going live inside innDex.

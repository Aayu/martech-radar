# Martech Radar: hosted collector proposal

Prepared 14 November 2026. Revised the same day to require no paid services. This is a proposed replacement design, not a deployed service.

## Recommendation

Build a portable, open-source collector and pilot it on Apify's Free plan. Do not buy a scraper, upgrade to a paid plan or enable paid search, proxies or model calls. Use Google Sheets as the reading interface, with Excel and CSV exports for later use. Keep persistent history separately in named Apify storage, behind an interface that can also save and restore the history elsewhere. The collector should work without ChatGPT or this Mac being open.

The proposed core is Python with [Trafilatura](https://github.com/adbar/trafilatura) for article text, metadata, feed discovery and sitemaps, plus [Playwright for Python](https://github.com/microsoft/playwright-python) only for a small number of pages that require browser rendering. [Crawlee](https://github.com/apify/crawlee) is another open-source option with queues, retries and both ordinary HTTP and browser crawling. It can run independently of paid Apify hosting. Choose one collection framework rather than installing several overlapping frameworks.

Start with Trafilatura and add browser rendering only when a tested source needs it. The same core collector should run locally, on Apify or on GitHub Actions. Keep hosting-specific setup and storage adapters outside the extraction logic.

Apify supports hosting and editing code directly, so GitHub is optional. Its scheduler supports timezones. Its datasets support Excel, CSV and JSON exports. Named storage is retained across runs. These are platform capabilities, not evidence that our source-specific collectors already work. [Hosted code](https://docs.apify.com/actors/development/quick-start/web-ide), [scheduling](https://docs.apify.com/actors/running/schedules), [storage](https://docs.apify.com/storage), [exports](https://docs.apify.com/storage/dataset).

The existing local radar contains 23 dated briefs and 120 ledger entries. This folder has no Git repository and no standalone collector program. Import the existing history and read statuses so migration does not bring back yesterday's stories.

## How a daily run would work

1. Start at 07:15 Asia/Kolkata, aiming to refresh the inbox by 08:00. Show the actual completion time. Delays must remain visible.
2. Load the editable source register, saved search queries, previous story history and reading statuses.
3. Collect recent links from feeds, public APIs, newsrooms, release notes and case-study indexes. Expand discovery through relevant outbound links and a weekly source review. Keep saved web search queries as a planned extension, enabled only when a suitable provider's free allowance and access terms have been verified.
4. Fetch the linked source pages. Extract title, publisher, publication date, canonical URL, relevant text and links to original evidence. Use a browser only when ordinary fetching cannot access the rendered public content.
5. Filter by topic and recency. Record collection failures and uncertain dates separately from a source that was checked successfully and had nothing new.
6. Group repeated coverage. Compare URL, text fingerprint, company, product or campaign, event date and the underlying change. Treat fuzzy matches as candidates for review, not proof of identity.
7. Apply transparent priority rules. Save the candidates and their evidence. Update the small reading inbox and complete archive.
8. Export a dated snapshot, record source coverage and report failures through a separately configured notification destination.

Use a single active writer, bounded retries and stable record IDs. If a run is retried, it must not append the same story again. A failed source must not erase its last successful results or mark the whole run as healthy.

## Source register

The researched source shortlist, checking intervals, catch-up rules and evidence controls are now specified in [Source and Coverage Plan](Martech%20Radar%20%E2%80%94%20Source%20and%20Coverage%20Plan.md). Use that plan to choose collectors; the broad categories below remain background. Cadence is source-specific, and scheduled collection must recover all unseen entries since the last successful check.

Begin with 8–10 representative sources, expand to 20 and then approximately 30 if measured usage and quality support it. The names below define the editorial shortlist. Specific feed URLs, page selectors, access and extraction quality must be tested before a source is enabled. Fetch only new or changed articles and put a firm limit on browser-rendered pages per run.

| Coverage | Starting shortlist | What to collect |
| --- | --- | --- |
| FMCG / CPG | Coca-Cola, PepsiCo, Unilever, P&G, Reckitt, Nestlé, L'Oréal, Tata Consumer | Newsrooms, customer technology announcements, commerce partnerships, relevant investor materials |
| Large enterprises | Walmart, Amazon, Starbucks, Marriott, Samsung, Albertsons | Loyalty, personalization, retail media, customer platforms, measurement and implementation lessons |
| Connected journeys | Effie, Think with Google, The Drum case studies, brand and agency case-study pages | Packaging/store/media to identity, CRM, loyalty, purchase and measurement |
| Platforms and independent reporting | Shopify changelog, Adobe, Salesforce, Braze, MarTech, AdExchanger, Marketing Dive, Retail Dive | Product changes, customer implementations, limitations and failures |
| Regulation | MeitY / official Gazette, EDPB, ICO, FTC | Official documents and explicit proposal, enactment and effective dates |
| Practitioner signals | r/PPC, r/ecommerce, r/marketingautomation | Problems and questions to investigate, with discussion links |

Use feeds or APIs when available, page extraction next, browser automation last. A reusable extractor can cover many ordinary article pages. Add small source-specific collectors where dates, pagination, PDFs or page structure need special handling.

For Reddit, begin with search-discovered discussion links. Direct automated collection is conditional on available authorized access and must not be a dependency for the rest of the radar. A discussion is not proof of a factual claim.

Each source row should hold: source ID, name, category, domain, starting URL, collection method, cadence, enabled status, last attempt, last success and last error. Core feeds run daily. Rotate the extended company watchlist across the week.

## Search design

A broad web-search index and a website scraper solve different problems. Open-source extraction does not itself provide dependable, unlimited web search. The zero-cost baseline uses feeds, sitemaps, newsroom listings and case-study indexes, with relevant outbound links and weekly source review for expansion. This has narrower discovery coverage than the previous open-web research workflow. Do not hide that tradeoff or substitute an unreliable search-engine scraper.

A search API can later discover URLs outside the source list. Brave Search is one possible provider, but it is not a dependency in the free baseline. Verify a suitable free allowance and storage terms before enabling it, and stop when that allowance is exhausted. [Provider information](https://brave.com/search/api/).

If a free search provider is enabled, cap calls to fit its allowance and rotate companies and capabilities. The following are query templates to test, not verified search results:

- `{company} loyalty personalization customer data case study`
- `{company} retail media digital commerce incrementality`
- `{company} marketing technology implementation results`
- `connected packaging campaign loyalty purchase results`
- `campaign CRM omnichannel incrementality case study`
- `customer data platform implementation failure migration`
- `site:shopify.dev/changelog customer data checkout privacy`
- `site:meity.gov.in consent data protection notification`
- `site:ico.org.uk advertising cookies enforcement`
- `site:reddit.com/r/PPC attribution measurement problem`

Search in layers: named companies, capabilities, connected-journey mechanics and problems. Include India-specific variants. Do not require a story to use the term “MarTech” to qualify.

Retain the existing recency windows: seven days for announcements, 30 days for substantial enterprise reports and regulatory developments, and 180 days for campaign case-study publication. Separate campaign period from case-study publication. Date-unknown records remain flagged. A newly discovered old page is not a new event.

## Collection and editorial judgment

Version one can operate without a language model: collect source text, classify with rules, deduplicate, rank provisionally and export. It can provide source excerpts and explicit matching reasons instead of generated summaries.

Rule-based ranking cannot reliably establish causal evidence, legal interpretation or the originality of an insight. A publisher saying “incremental” is not enough to verify the study. Keep a human-review status and label automated scores as provisional.

If richer analysis becomes useful, add an optional model step after collection. It receives the saved source text, returns structured analysis with supporting excerpts and marks absent information as unknown. It does not control discovery or replace the stored evidence. The collector must still finish if this optional step fails.

Preserve the current four editorial dimensions: relevance to your target roles, evidence quality, novelty and practical learning value. A verified recommended item still needs at least 14/20. Unreviewed heuristic scores must not be presented as equivalent to verified editorial scores. With no review or analysis step, show “candidates to review” rather than automatically claiming to have found the day's best three verified stories.

Label outcomes as vendor/brand claims, engagement, attributed results or demonstrated incremental effects as supported by the source. Keep proposed and effective legal changes separate. Record evidence gaps rather than filling them in.

## The spreadsheet

| Tab | Purpose |
| --- | --- |
| Inbox | Up to three verified reading priorities, or clearly labelled candidates awaiting review, with short context and source links |
| Library | All relevant collected stories, searchable by company, topic, date and evidence status |
| Sources | Editable collection list, cadence and source health |
| Searches | Editable query templates and rotation |
| Runs | Last successful refresh, per-beat coverage, counts, failures and measured cost |

The everyday visible columns should be: discovered date, priority, company, topic, headline, source link, reason to read, evidence status, reading status and your notes. Keep technical fields out of the main reading view.

Underlying records also need: stable story ID, published/event/effective dates, date confidence, canonical URL, source ID, original evidence URL, retrieval timestamp, extraction status, evidence excerpt, metrics and measurement method when available, deduplication group, update-to ID, score components and score method.

Reading status stays under your control: To read, Read, Saved or Skip. Updating source facts must preserve your notes and status. Persist story history in a named key-value store and keep an append-only collection audit in a named dataset. The spreadsheet is the working view, not the only copy of the history. [Apify storage behavior](https://docs.apify.com/storage/dataset).

Each standing beat must show a status: qualifying item, no qualifying item after a successful check, or incomplete collection. This prevents a broken scraper from masquerading as a quiet news day.

## Hosting and cost

Recommended pilot: Apify Free, using our own collector. Its free plan provides $5 in monthly usage, requires no credit card and blocks further usage until the next billing cycle if the allowance is exhausted. Compute is currently $0.20 per GB-hour. An illustrative 1 GB run lasting 15 minutes daily for 30 days would consume $1.50 in compute credit. This is arithmetic, not a benchmark: build, storage, transfer and any other metered operations also consume allowance. Actual usage needs measurement before claiming the daily radar fits. [Pricing checked 14 November 2026](https://apify.com/pricing).

Use a timeout, limited page counts, bounded retries, conditional fetching and modest retention. Avoid paid Store Actors, paid proxies and paid search in the baseline. Show allowance exhaustion as an incomplete run. Do not automatically upgrade or spend money to recover.

Alternative free host: GitHub Actions. A private repository keeps the code private and can use the account's included compute allowance, shared with other eligible usage. GitHub's current documentation lists $12/month of included compute usage for GitHub Free; do not assume the full allowance is available to this project. Check the account and configure paid usage to stop before deployment. Standard runners in public repositories are free, but making the project public is not required or proposed by default. Persist history outside the temporary runner and keep storage within included limits. [GitHub billing](https://docs.github.com/en/billing/concepts/product-billing/github-actions).

Scheduled Actions can be delayed or dropped during high load. Start before the 08:00 target, show the actual refresh time and retain manual rerun support. [GitHub scheduling documentation](https://docs.github.com/en/actions/tutorials/manage-your-work/schedule-issue-creation).

Apify Free is the first host to test because it preserves the preference to avoid GitHub setup. If it cannot accommodate the measured workload, consider GitHub Actions within the existing free allowance. No paid server is part of this proposal.

## Build and migration sequence

1. Build a local pilot against 8–10 representative sources, covering all three standing beats, ordinary pages, at least one feed and one JavaScript-heavy page. Produce a sample CSV or workbook from real retrieved content.
2. Test extraction and dates against the original pages. Check same-URL repeats, syndicated coverage, substantive updates and unchanged re-runs. Confirm failed or inaccessible sources are visible.
3. Expand to the initial source shortlist within the measured free budget. Import the existing 120 ledger records and reading statuses before the first ranked run. Preserve original IDs and archive links during migration. External search is optional and must fit a separately verified free allowance.
4. Connect the chosen free host and spreadsheet account. A desktop ChatGPT connection does not automatically configure credentials for the independent hosted program. Use the provider's secure setup flow rather than pasting credentials into chats or documents. Verify that paid usage is disabled before enabling the schedule.
5. Run for seven days, measure useful-item rate, missed sources, duplicates, extraction failures, runtime and actual cost. Calibrate rules using your Read / Saved / Skip decisions.
6. Activate the daily schedule and retire the old chat automation after the replacement has demonstrated successful collection, persistence and spreadsheet updates.

No hosting account, subscription, spreadsheet or replacement schedule was created while preparing this proposal. The current automation remains active.

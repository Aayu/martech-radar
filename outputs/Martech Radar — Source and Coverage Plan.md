# Martech Radar — source and coverage plan

Prepared 14 November 2026. Proposed collection design under the no-paid-services constraint. Publisher pages were researched through web retrieval; this is not a completed scraper test or a deployment.

## What happens today

The active radar is a daily research instruction in the current chat. Its rules call for open-web research across three beats, opened original sources, a four-part editorial score, and one to three recommendations scoring at least 14/20. It saves Markdown briefs, a three-item inbox and a story ledger.

The local archive currently contains 23 briefs and 120 evaluated-story records. The reviewed ledger and files do not contain a persistent per-source scheduler, collection checkpoints or a complete log of source fetch attempts. Therefore the ledger shows which stories were evaluated, not proof that every intended publication was checked. The two latest briefs record useful evidence caveats and declined stories, but do not establish exhaustive coverage.

The hosted collector is still a proposal. This plan preserves the existing editorial standard and adds explicit discovery and coverage controls.

## Design principle

Separate three jobs: discover links broadly, retrieve relevant articles efficiently, then judge their evidence carefully. Checking a feed or listing should not require rendering and rereading every article.

Use a small set of complementary industry publications as discovery hubs. Follow their links to original announcements, company materials and study methods. Maintain a separate rotation of company and platform sources so a story does not depend entirely on trade-press coverage. Review gaps weekly.

The intervals below are proposed starting intervals, not measured publication frequencies or guarantees. Tune them after observing source volume, archive depth, unique relevant discoveries and detection delay. Preserve the three standing beats as daily coverage statuses, while individual sources rotate.

## Ten core discovery sources

| Source and entry page | Why it belongs | Initial listing check | Filtering and evidence notes |
| --- | --- | --- | --- |
| [Consumer Goods Technology — Sales & Marketing](https://consumergoods.com/sales-and-marketing) | Closest specialist fit for technology adoption inside major CPG companies: commercial data, marketing technology, digital commerce and operating models. | Every 48 hours | Use the sales/marketing section plus relevant AI coverage. Avoid letting unrelated manufacturing and corporate news dominate. Sponsored content is separately labelled. |
| [Marketing Dive](https://www.marketingdive.com/) | Brand activity, connected campaigns, advertising technology and marketing operations. | Daily lightweight check | Watch data/analytics, ad tech and relevant brand stories. Distinguish editorial articles from the press-release and sponsored-content sections. |
| [MarTech](https://martech.org/) | CDPs, CRM, orchestration, marketing operations, measurement and technology changes. | Daily lightweight check | Prefer concrete implementation detail over generic advice. Record contributor affiliation and sponsorship. |
| [AdExchanger](https://www.adexchanger.com/) and its [Daily News Roundup](https://www.adexchanger.com/daily-news-roundup/) | Identity, privacy, measurement, retail media and advertising infrastructure. The roundup also points to material outside the watchlist. | Daily lightweight check | Follow relevant external links to their original evidence. Several articles repeating one announcement count as one event. |
| [Retail Dive — Technology](https://www.retaildive.com/topic/technology/) | Technology choices at major retailers and consumer commerce businesses. | Every 48 hours | Include ecommerce and customer-facing marketing links. Downrank routine store openings, financial news and executive appointments without a relevant technology decision. |
| [Retail TouchPoints](https://www.retailtouchpoints.com/) | Retail customer experience, personalization, loyalty and online/offline journeys. | Every 48 hours | Preserve author affiliation: executive viewpoints can be vendor-written even when hosted by a publication. |
| [CMSWire](https://www.cmswire.com/) | Customer data, digital experience, journey orchestration and the operating side of consumer platforms. | Every 72 hours | Use relevant topic channels. Avoid letting generic customer-service commentary or product announcements crowd out substantial cases. |
| [ET BrandEquity](https://brandequity.economictimes.indiatimes.com/) | Indian marketing, digital and MarTech developments. | Daily lightweight check | Give India coverage a deliberate place. Filter people moves, entertainment news and advertorials by relevance. |
| [afaqs! — Digital](https://www.afaqs.com/news/digital) and [case studies](https://www.afaqs.com/casestudies) | Indian digital campaigns, brand executions and consumer-market lessons. | Every 48 hours | Select cases with a consumer action and identifiable mechanism. A creative film alone does not establish a connected journey. Homepage and Digital were opened; the case-study section is supported by indexed article results and still needs a collector probe. |
| [The Drum](https://www.thedrum.com/) | Campaign discovery, commerce media and award case studies. | Every 48 hours | Awards and partner accounts provide leads, not automatic validation. Verify the campaign period, implementation and source of outcome claims. |

The first pilot should include sources from each core category. Expand the number of working collectors after measuring cost, extraction and coverage. These ten publications are complementary discovery choices, not a claim that every article on them is worthwhile or freely extractable.

## Weekly depth and supplementary coverage

| Source | Role | Initial frequency | Access/evidence boundary |
| --- | --- | --- | --- |
| [Think with Google](https://business.google.com/us/think/) | Consumer insights, measurement and platform-backed campaign cases. | Weekly | Vendor-selected evidence. Check the reported method and comparator. The former Think with Google URL redirects here. |
| [Braze customer stories](https://www.braze.com/customers) | Lifecycle, CRM, experimentation and journey mechanics. | Weekly | Vendor case studies; reported results do not automatically establish causality. |
| [Nectar360 case studies](https://www.nectar360.co.uk/case-studies/) | FMCG campaigns linking loyalty, retail media, purchase and customer data. | Weekly | Retailer/media-owner claims. Confirm campaign year, geography and measurement definitions. |
| [WARC's public latest-content pages](https://www.warc.com/en/latest) | Effectiveness research and discovery of useful cases. | Weekly | WARC offers public latest-content discovery while its broader case database is subscription based. Use publicly accessible evidence or locate the brand/agency source. Do not rely on unavailable full cases. |
| [chiefmartec](https://chiefmartec.com/) | Interpretation of technology architecture, management and industry structure. | Weekly | Commentary and research are useful learning material; they are not automatically implementation evidence. Follow its current blog/research links. |
| [PhocusWire](https://www.phocuswire.com/) | Travel and hospitality customer technology, distribution, loyalty and digital booking. | Weekly | Prevents the large-enterprise beat becoming exclusively retail. Filter fundraising and general travel news. |
| [Finextra](https://www.finextra.com/) | Consumer payments, banking journeys and adjacent commerce technology. | Weekly | Separate newsroom reporting, company updates and community opinion. Filter for consumer/commerce relevance. |
| [ET Retail](https://retail.economictimes.indiatimes.com/) | India ecommerce, omnichannel retail and consumer businesses. | Every 72 hours | The homepage retrieval exposed navigation but little article content. Validate an article listing or feed before counting this source as covered. |

Additional candidates needing access validation:

- **Path to Purchase Institute:** potentially relevant to shopper and commerce marketing, but both the homepage and About page returned HTTP 403 in this research tool. Keep it pending. Do not promise coverage or repeatedly retry it every day. This result does not prove that all permitted collection methods are unavailable.
- **Effie:** the official site exposes a case directory and sample-case results, while its detailed library is subscription based. The sample page returned HTTP 403 in direct retrieval here. Treat public case metadata as leads and verify a permitted route before enabling collection. [Official samples](https://effie.org/sample-cases/), [library access](https://www.effie.org/subscribe/).

## Original sources and breadth

Industry hubs make discovery economical; original sources support verification. Reuse the existing company watchlist rather than inventing a new list based only on the last week's headlines.

- **FMCG rotation:** Coca-Cola, PepsiCo, P&G, Unilever, Reckitt, Nestlé, Mondelez, L'Oréal, Colgate-Palmolive, Mars, Danone, Haleon, Tata Consumer, ITC, Godrej Consumer and Marico. Check each company's relevant news and investor entry points at least weekly. Fetch a source immediately when a relevant industry article points to it.
- **Other enterprise rotation:** Walmart, Target, Amazon, Albertsons, Nike, Starbucks, McDonald's, Disney, Marriott, Hilton, American Express and Samsung. Rotate their customer-technology news and relevant research. Verify Fortune membership separately if using that label.
- **Platforms:** retain direct coverage of Shopify, Adobe, Salesforce, Braze, Google and Meta. Changes with deadlines, deprecations or operational impact deserve a daily lightweight release/news check where a dependable endpoint exists. Slow customer-story libraries can run weekly. An official changelog cannot be replaced by a weekly marketing blog check.
- **Regulation:** check relevant official update indexes for MeitY, EU institutions, the ICO and FTC daily where accessible. Follow leads to official text. Known effective dates become explicit reminders in the data. Keep proposals, adopted rules and operative requirements separate.
- **Practitioners and failures:** inspect relevant Reddit discussions weekly through available authorized access or discovered links. Use them to generate questions and find original incidents, not as sole evidence. Add platform status and incident pages when relevant.

Split the 28 named companies into seven daily groups of four. Every company then receives one planned check each week, with immediate additional verification when a lead appears. This is a baseline rotation; upcoming earnings or announced launches can temporarily increase checking frequency.

## Catch-up collection and scheduling

1. Store a separate last-attempt time, last-success time and coverage checkpoint for each source. A failed request does not advance the checkpoint.
2. Prefer a feed, API or chronological listing. Save discovered links durably before advancing the discovery checkpoint. Article extraction is a separate queue and may retry without rediscovering everything.
3. Retrieve all unseen entries since the last successful checkpoint, with a seven-day overlap for discovery when archives allow. Overlap is a collection safeguard, not the editorial freshness limit. Long outages require catch-up from the actual checkpoint even if it is older than seven days.
4. Inspect pagination or sitemaps to recover links that have fallen out of a short feed. Do not stop at the first familiar pinned story. If the feed's earliest entry is newer than our checkpoint and there is no recoverable archive, report a coverage gap.
5. Unknown or unreliable dates do not justify discarding a newly discovered URL. Retain it for review. Keep publication date, event date, first-seen date and last-modified date separate.
6. Use conditional HTTP requests when the source supports them. They let an unchanged resource avoid a full download. Keep cached content and headers together. [Conditional request behavior](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/Conditional_requests).
7. Fetch each relevant article once, preserving the source link, retrieval time and evidence. Revisit when the listing signals an update, a referenced claim needs checking, or a tracked event is due for follow-up. Compare cleaned article content so navigation or advertisement changes do not become “new stories.”
8. After two weeks, adjust listing frequency based on observed publishing volume and archive retention. Never lengthen an interval beyond what the available archive can safely cover. Reduce full-page/browser work first. A high-value source stays on the watchlist even if it publishes infrequently.

Example: if a company newsroom is checked Monday and Thursday, Thursday's run must collect all unseen Tuesday and Wednesday entries too. It may deliver those stories later, but it should not lose them merely because it skipped two days. If the business requires next-day awareness for that source, its listing needs a daily check.

The feed URLs for MarTech, Marketing Dive, Retail Dive and AdExchanger returned an RSS content type to the research tool. The tool could not parse that format. This is useful discovery, not feed validation. Validate XML, article IDs, timestamps, retained history and pagination using the actual collector before enabling any feed.

## Relevance and evidence safeguards

Use broad capture and narrow recommendation. A cheap first-stage filter should admit a candidate if its brand, sector, capability or consumer mechanism is relevant. It must not require the headline to contain a fashionable word such as “MarTech,” “AI” or “innovation.” Maintain company/brand aliases and vocabulary such as loyalty, rewards, replenishment, verified eligibility, packaging, receipt, activation, consent and experimentation.

Keep borderline candidates in a review queue and audit a sample of rejected items every week. A keyword score helps order work but is not a verified editorial score.

For each potentially recommended article, establish:

- The organization and business/consumer problem.
- What actually changed and how the data, technology or operating process works.
- The source and date of the claim.
- The result, if any, and how it was measured. A useful implementation can qualify without proven lift if the limitation is explicit.
- A learning point relevant to customer data, lifecycle, commerce, privacy or transformation leadership.

For connected campaigns, reconstruct insight → signal → decision → touchpoints → consumer action → measurement. Separate engagement and attributed sales from demonstrated incremental impact. Count syndicated reports as one story while preserving independent corroboration. Merge only clear duplicates; flag uncertain matches for review. A material follow-up becomes an update linked to the prior story.

Keep the existing four dimensions and 14/20 recommendation threshold. Purely automatic collection and heuristic ranking must not be presented as having completed this evidence review. The no-paid-model baseline produces candidates, evidence excerpts and a review queue. Human review is required for the strongest editorial assurance. An optional later analysis tool must preserve the underlying evidence and cannot invent missing methodology.

## Weekly coverage review

The system should report what it knows about its own coverage:

| Measure | What it reveals |
| --- | --- |
| Scheduled checks completed, by beat and source | Whether all intended collections ran |
| Oldest uncollected interval and oldest unprocessed article | Whether failures or quotas are causing a backlog |
| Relevant stories found only in the weekly review | Blind spots in the watchlist or filter |
| Publication-to-discovery delay | Whether a source needs more frequent checking |
| Unique useful stories and your Saved / Read / Skip decisions | Which sources add value beyond repeating other publications |
| Items rejected by the filter but accepted in a manual sample | Whether efficiency rules are excluding worthwhile material |
| Access failures, date/extraction failures and source concentration | Whether the output has become incomplete or narrow |

Once a week, inspect a small, preselected set of original company pages, topic archives and external roundup links beyond the normal candidate queue. Search for a few company-plus-capability combinations when a free search route is available. Compare the useful discoveries with the stored records and add or repair sources as needed. If this wider search is manual, say so. A feed collector alone does not provide a comprehensive web index.

## Free-resource policy and rollout

Begin with the core publication shortlist and a representative subset of original sources. Avoid images, videos, full-site recrawls and browser rendering unless needed for the article. Use bounded concurrency and per-domain request pacing. Measure actual requests, browser minutes, transfers and storage before claiming the whole watchlist fits Apify Free.

If a free allowance is close to exhaustion, preserve the link queue and show a delayed/incomplete status. Never silently drop candidates, reduce the evidence standard or claim a source was checked. Moving the same collector to another eligible free host is an option only after confirming its remaining allowance.

Before replacing the active radar, compare the collector with manually checked archives for a representative set of sources. Test missed days, truncated feeds, duplicate coverage, old items republished with new dates, inaccessible pages and a restart during extraction. Then run the free pilot for two weeks and adjust cadence from evidence.

No finite free watchlist can guarantee that nothing important anywhere on the web is missed. The practical goal is complementary coverage of the agreed topics, measured detection delays, recovery of missed intervals and visible gaps. Source checks, original-source verification and periodic audits work together to support that goal.

This plan does not change the active automation or claim that the proposed collectors are running.

## Steps

1. Take the companies (companies) of the plan (brief) one by one. Call the news search tool (news_search) once per company. Every call is one paid search.
2. From the results, choose only real articles about that company. An article is real when its title and text are about the company's business, earnings, products, lawsuits, management or stock. Leave out articles that only mention the company in passing, ads, and articles that repeat the same event. Per company, choose at most 4 articles, the newest ones that say different things.
3. Upload the chosen articles with the file server upload tool (upload) to the news file server (to: fs://news). Use the file name (file) the tool gave exactly as it is, copy the title (title) and the address (source) from the tool's result, and put the company's name as the one tag (tags).
4. Articles that are already stored are left out by the tool, which only counts them (skipped_known). Do not look for them again; when you count the status (status), add that number to the articles you uploaded this time.
5. When every company is done, save coverage.

## How to write each item

### coverage

- items[].company: the name exactly as the plan has it.
- items[].status: ok when the articles uploaded this time plus the ones already stored (skipped_known) are 2 or more, thin for 1, none for 0.
- items[].note: one sentence on the main thread of the collected news. For none, why nothing was uploaded.

## Rules

- Never change an article's content. Do not summarize or rewrite it; upload the file the tool made as it is.
- When the tool returns an error (no key, server error, timeout), call it once more; when it fails again, give the company status none and write the error's reason in note. A search that could not be made is not the same as no articles. The program records the failed search separately, so the run ends as failed.

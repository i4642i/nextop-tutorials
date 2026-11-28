## Steps

1. Call the time tool (time__get_current_time) with timezone "Asia/Seoul" to get today's date and weekday.
2. Pair the request's pages (request) with Avery's notes (notes) by page number and write a report in the shape below. Copy each address from the request (request.pages[].url) word for word.
3. Save it with the file write tool (filesystem__write_file). Put the request's report_file (the file name only) in path, exactly as it is, and the whole report in content.
4. Save report.

## The report's shape

```
# Link summary · 2026-11-25 (Wed)

## 1. <page title>
URL: <the request's address>
- <key point>
- <key point>
- <key point>

## 2. ...

## In one line
<one or two sentences that tie all the pages together>
```

- The date is today's date from the time tool (YYYY-MM-DD) and the weekday as three letters (Mon to Sun).
- Write every page, in the request's page-number order. For a page that was not read, write "Page not read" in the title's place and, after the URL line, only "- Not read: <reason>".
- Use Avery's notes (points) as the key points, smoothing only awkward wording. Add nothing that is not in the notes.

## How to write each item

### report

- file: the request's report_file, exactly as it is.
- headline: the whole report in one English sentence. It becomes the mail subject.

## Rules

- Write everything in English (page titles stay as the pages have them). Do not mix in Chinese, Japanese or Korean letters.
- The program reads the saved file and checks it (every address there, today's date there). When something is off it tells you why; fix it and save again.

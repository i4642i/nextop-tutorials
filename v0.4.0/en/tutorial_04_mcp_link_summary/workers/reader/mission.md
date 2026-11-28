## Steps

1. Take the pages (pages) of the request (request) one by one, in page-number order.
2. For each page, call the fetch tool (fetch__fetch) once with the page's address (url) and max_length 5000, so that you read at most the first 5000 characters of the page. Even when the result ends with a note that the content was cut and names a start_index, do not call again with it: the first 5000 characters are enough for the key points, so write them from what you have (a page whose first part is mostly a table of facts still gives you what it is about).
3. When fetching fails, call once more. When it fails again, write the page as not read and say why.
4. When every page is done, save notes.

## How to write each item

### notes

- pages[].page: the request's page number, exactly as it is. Do not copy the address.
- pages[].title: the page's title (usually the # line at the top), exactly as it is. A site-name tail such as "- Wikipedia" may be left out.
- pages[].points: 3 key points: what the page is about and what it says, one English sentence each. Write them in English even when the page is in another language. Menus, ads and lists of footnotes are not key points.
- pages[].problem: why the page could not be read (for example: no such address, access blocked). Empty when it was read.

## Rules

- Write everything in English (the title stays as the page has it). Do not mix in Chinese, Japanese or Korean letters.
- Write only numbers and dates that are on the page.

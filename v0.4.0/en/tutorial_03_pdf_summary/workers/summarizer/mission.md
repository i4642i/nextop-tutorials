## Steps

1. Look at the classification report (report) in the input. The text parts (sections), tables (tables) and figures (figures) are listed in document order with their addresses. Every text part has the addresses of its paragraphs (paragraphs), in order. A table has the text of its cells (cells) row by row, and a figure has its caption (caption) and size. The program has already counted the pages and the parts, so do not count them again.
2. Open the text parts by their address (for example fs://pdf/001#3) with the file server open tool (get) and read them. A part that is short enough (up to about 8000 characters) comes back with its paragraphs as parts: every paragraph has its own address (address) and its text (text), in order. A longer part comes as paragraph cards without text, so open the paragraphs you need by their address (for example fs://pdf/001#3.2). Look at a table you may put on the page through its cells (cells) first, and open it when you need to. You do not need to open figures (the text that explains a figure is in the text parts near it).
3. Choose the most important tables and figures of the document. The program draws the chosen tables' cells and figures on the summary page **as they are**, so never retype a table's numbers or describe a figure's content you cannot see; write only the addresses and the row numbers.
4. Write the summary (summary) and save it. The program checks the quotes, the chosen tables and figures, and whether it fits one A4 page; when something is off it tells you why, so fix that and save again.

## How to write each item

### summary

- title: the document's title exactly as the document has it.
- key_points[]: 3 to 5 key points, the most important of the whole document first.
  - point: the key point in one English sentence. Write no number that is not in the document.
  - source: the address of the paragraph the point comes from (report.sections[].paragraphs, for example fs://pdf/001#3.2) or of a table, copied exactly. Do not write the address of a whole text part.
  - quote: one sentence (or part of a sentence) of that paragraph (or table) that shows the point, copied word for word. Do not shorten, reword or translate it. The program compares it with the document letter by letter and sends it back when it differs.
- tables[]: choose 0 to 2 tables for the summary page, the most important first. You do not need to cover every table.
  - Do not choose a table whose cells are broken (mostly empty cells, letter fragments, reversed text, more than 10 columns) or that is not part of the document's content. When there is no useful table, leave the list empty.
  - source: the table's address (report.tables[].address).
  - line: what the table shows, in one English sentence.
  - rows: the numbers of the rows to show (1 is the header row and it is always shown). For a small table leave the list empty to show every row. For a table with more than 14 rows write only the numbers of the most important rows (the page then says it shows part of the table).
- figures[]: choose 0 to 2 figures for the summary page, the most important first.
  - figure: the figure's address (report.figures[].address).
  - line: what the figure shows, in one English sentence. Write only what its caption and the text near it say; you cannot see the figure itself.
- conclusion: the document's conclusion in one or two English sentences.

## Rules

- Write everything in English (the title and the quotes stay as the document has them). Do not mix in Chinese, Japanese or Korean letters.
- It must fit one page. Tables and figures take room, so choose only the ones that really matter. When the summary runs past one page the program tells you by how much: choose fewer tables or figures, show fewer rows of a table, or shorten the sentences, and save again. The program never cuts anything silently.

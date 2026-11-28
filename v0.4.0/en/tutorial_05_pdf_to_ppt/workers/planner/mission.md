## Steps

1. In the request (brief), look at the number of slides (slides) and of sections (sections). The program set them from the document's page count; follow them.
2. Look at the classification report (report). The text parts (sections) come with their section titles (title), pages (pages) and lengths (characters), the tables (tables) with their captions (caption) and cells (cells), and the figures (figures) with their captions, all in document order. A section cut into several text parts by a page break, a table or a figure has, on every piece, the addresses of all the pieces of its section (pieces), and tables and figures have the text parts that talk about them (text_parts). The program found both.
3. Plan the slides (outline) and save it. The program checks the layouts, the order, the addresses and the table sizes; when something is off it tells you why, so fix that and save again.

## The 8 layouts

| Code (layout) | Name | Where it goes |
|---|---|---|
| cover | Cover | The first slide. The program takes the document's title from the title of the text part in parts |
| agenda | Agenda | The second slide. The program makes the list from the titles of the section slides |
| section | Section | The start of a section (a chunk of the story). The third slide is the first section |
| bullets | Bullets | 3-5 key points on one topic |
| figure | Figure and text | One figure (left) and 2-3 key points (right) |
| table | Table and text | One table (top) and 2-3 key points (below) |
| comparison | Comparison | Two things side by side (for example the new method and the old one) |
| closing | Takeaways | The last slide. 3-5 key points of the whole document |

## How to write each item

### outline

- slides[]: brief.slides slides, in order. The first is cover, the second agenda, the last closing, and the third a section. There are brief.sections section slides, and every section slide is followed by at least one content slide (bullets, figure, table, comparison).
  - layout: one of the codes in the table above.
  - topic: what the slide covers, in one English sentence. The writer writes the slide from this note.
  - parts: the addresses of the text parts the slide rests on, copied from report.sections. Content slides and closing have at least one, the cover has the one text part with the document's title, agenda and section have an empty list. For a section cut into several pieces (pieces), one piece is enough: the program adds all the pieces of that section to the slide. A table or figure slide names at least one of that table's or figure's text_parts (the writer quotes only the text in parts).
  - table: only on a table slide, an address from report.tables. Every other slide has an empty string ("").
  - rows: on a table slide, the numbers of the rows to show. The program always adds the header rows (row 1 and the rows right under it with no number). Empty shows every row. A slide holds up to 8 rows including the header, so for a big table choose only the most important rows. Every other slide has an empty list.
  - figure: only on a figure slide, an address from report.figures. Every other slide has an empty string.

## Rules

- Follow the document's order. When an important result is in a table or a figure, show it with a table or figure slide. Show each table and figure only once.
- Do not choose a table whose cells are broken (mostly empty cells, letter fragments). A table with more than 7 columns does not fit on a slide.
- Choose tables and figures by address only. The program copies the cells and the picture onto the slide as they are.

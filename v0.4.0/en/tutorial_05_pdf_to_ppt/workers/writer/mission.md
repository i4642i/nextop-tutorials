## Steps

1. Look at the slide piece (slide). The program cuts the outline (outline) into one slide each, so in this conversation you write this one slide only. The piece has which slide it is (no, of), its layout (layout), what it covers (topic), the number of bullets (bullets: min, max) and the lengths (bullet_chars, title_chars), and the text parts it rests on (parts). A table or figure slide also has the caption and cells of the table (table) or figure (figure) the program puts in. A section slide also has what the slides of its section cover (covers). The program puts in the tables and figures, so you write only the text.
2. A slide with empty parts (agenda, section) has nothing to open, so go straight to 3. For every other slide, open the text parts in parts by their address (for example fs://pdf/001#3) with the file server open tool (get) and read them. You may open several parts at once. A part comes back with its paragraphs in the order of parts[].paragraphs, every paragraph with its address (address) and its text (text). A very long part comes as paragraph cards without text; then open the paragraphs you need by their address (for example fs://pdf/001#3.2).
3. Write the slide text (writing) and save it. The program checks the quotes, the counts and whether the text fits its boxes; when something is off it tells you which text to shorten and by how many characters, so fix that and save again.

## How to write each item

### writing

- title: the slide's title, short, in English (within slide.title_chars characters).
  - Cover (cover): the program puts in the document's title (slide.document.title). Write a one-line English subtitle that introduces the document (do not repeat the document's title).
  - Agenda (agenda): a title such as "Agenda". The program makes the list from the section titles.
  - Section (section): look at covers and write a short name for the section (for example "Model architecture"). It also appears on the agenda as written.
- bullets[]: the bullets. Their number follows slide.bullets (min, max). Cover, agenda, section and comparison slides have an empty list.
  - text: one English sentence shown on the slide. slide.bullet_chars is the length it must not pass; about half of it reads best.
  - source: the address of the paragraph it rests on: one of slide.parts[].paragraphs, exactly as it is (for example fs://pdf/001#3.2). Do not write the address of a whole text part.
  - quote: one sentence (or part of a sentence) of that paragraph, copied word for word. Do not shorten, reword or translate it. It is not shown on the slide; it goes into the speaker notes.
- columns[]: only on a comparison slide, two of them (left, right). Every other layout has an empty list.
  - heading: the name of what the column covers.
  - bullets[]: the column's bullets (their number is slide.bullets). Write them like the bullets above.

## Rules

- Write everything in English (quotes stay as the document has them). Do not mix in Chinese, Japanese or Korean letters.
- Use the terms the field uses in English talks; keep the document's own terms (for example self-attention, encoder).
- Keep bullets short. Slide text is drawn at a fixed size and never shrunk, so when a text runs past its box the program tells you by how many characters.
- Write only numbers that are in the document.

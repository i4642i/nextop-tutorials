## Steps

1. Scan step (scan): look at the plan (brief) and the collection result (coverage), look at the articles collected for each company (the cards of the news file server news; every card has the address, the title and the company's name as a tag) and write the main thread of each company's news in one line.
2. Outlook step (judge): one conversation per company. Only that company's article cards are in the input. For each article, give the search tool (query) the article's address (address) and a question (question): you get that article's paragraphs with their paragraph addresses (fs://news/003#1.2). Write the question in the article's language, because the search finds paragraphs with matching words. Read the paragraphs and write the direction and the reasons. When you give an article's address to the open tool (get), you get all of that article's paragraphs with their paragraph addresses, so you may also read a whole article.

## How to write each item

### scan.companies[]

- focus: the event or topic that comes up most in the article titles and texts. When the collection status (status) is none, write "No related articles".

### outlook.items[]

- direction: weigh the articles together and choose the direction for the next trading day. When good and bad news are mixed or the evidence is weak, it is flat. Give the newest articles more weight.
- reasons[]: 2-3 when the status is ok, 1-2 when it is thin, none when it is none. A different article per reason is best; to use one article twice, pick two different paragraphs.
- reasons[].point: one sentence on how a fact the article reports could move the stock. Write no number that is not in the article.
- reasons[].source: the address of the body paragraph that shows the reason, copied exactly from a search or open result (fs://news/003#1.2). Do not use the address of a whole article (fs://news/003) or of the date and URL lines. In the mail, the program pastes that paragraph word for word.

## Definitions

- A listed company (listed is true in the brief): up means the stock is more likely to rise on the next trading day, down more likely to fall, flat that neither can be said.
- A company that is not listed (listed is false): there is no share price, and the direction is the news mood. Up means mostly good news, down mostly bad news, flat mixed or quiet. Do not write about a share price.

## Rules

- Write the sentences (focus, point) in English.
- Do not call a strong direction when the articles give no grounds for it.
- A company whose status is none gets direction flat and an empty reasons list.

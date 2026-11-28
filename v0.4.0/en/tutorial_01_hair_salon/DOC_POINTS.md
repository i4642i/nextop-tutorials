# Points to put into the README later (not yet written there)

- When the shop guide or the menu changes (hours, closed days, designers, prices, minutes), update the facts pasted into the reception worker's reply_checks (workers/reception/worker.json) too: the reply LLM checker does not see the shop documents.
- The phone numbers use nextop's own phone field type with `"country": "US"` on the phone fields (file_servers/bookings and customers type.json). The table key is E.164 (+15550107777); functions/_salon.py `mobile()` reads a recorded number through the same part, so a recorded phone and a booking's phone compare equal. Nothing is ejected or copied from the platform.
- The reply check (workers/reception/reply_check.py) refuses letters of any non-Latin script (Hangul, kana, kanji, Cyrillic, ...); accented Latin letters (café) and the menu's style names pass.

## Sources of the style menu (salon.json), checked 2026-11-28

Style names are the ones US trend reports and salon menus use for 2026; prices are rounded to a mid-range US salon (before tip) within the ranges below; minutes are multiples of the 30-minute slot that fit the designers' hours.

- Women's cuts (bixie, box bob, rounded lob, long layers, curtain bangs, modern shag): Bustle, spring 2026 haircut trends, https://www.bustle.com/beauty/spring-2026-haircut-trends ; Who What Wear, haircut trends 2026, https://www.whowhatwear.com/beauty/hair/haircut-trends-2026 ; The Zoe Report, fall 2026 haircut trends, https://www.thezoereport.com/beauty/fall-2026-haircut-trends ; Behind the Chair, the top haircut trends of 2026, https://behindthechair.com/articles/the-top-haircut-trends-of-2026/
- Men's cuts (taper / mid / skin fade, textured crop, buzz cut, modern mullet): The Fashionisto, men's hairstyles 2026, https://www.thefashionisto.com/hair/hairstyles-men/ ; Behind the Chair, what men are asking their hairdressers for in 2026, https://behindthechair.com/articles/what-men-are-actually-asking-their-hairdressers-for-in-2026/ ; FashionBeans, men's hair trends 2026, https://www.fashionbeans.com/article/mens-hair-trends/
- Prices (cuts about $15-$95, balayage about $75-$475, perms from about $30, keratin about $55-$350): StyleSeat, average hair salon prices, https://www.styleseat.com/blog/average-hair-salon-prices ; Fash, hair stylist cost, https://fash.com/costs/hair-stylist-cost ; Goldie, average salon service prices in the U.S., https://heygoldie.com/blog/average-salon-service-prices-us

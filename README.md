# Ecommerce selenium scraping

- Read [the guideline](https://github.com/mate-academy/py-task-guideline/blob/main/README.md) before start


## Task

This time you will implement the scraper for [E-commerce test-site](https://webscraper.io/test-sites/e-commerce/more/).
Yep, the similar one to that site in the video, but with some `more` changes.
Firstly - you need to scrape & parse info about all products and all pages.

The list of pages is next:
- [home](https://webscraper.io/test-sites/e-commerce/more) page (3 random products);
- [computers](https://webscraper.io/test-sites/e-commerce/more/computers) page (3 random computers);
- [laptops](https://webscraper.io/test-sites/e-commerce/more/computers/laptops) page (117 laptops) with `more button` pagination;
- [tablets](https://webscraper.io/test-sites/e-commerce/more/computers/tablets) page (21 tablets) with `more button` pagination;
- [phones](https://webscraper.io/test-sites/e-commerce/more/phones) page (3 random phones);
- [touch](https://webscraper.io/test-sites/e-commerce/more/phones/touch) page (9 touch phones) with `more button` pagination.

All of these pages should be scraped & content of products should be written in corresponding `.csv` file.
For ex. results for `home page` -> `home.csv`, `touch page` -> `touch.csv`.
Of course, on same pages there are random products, so the tests will only check content of 3 constant pages.
There are classes template for `Product` in `app/parse.py`.

So, your task is to implement `get_all_products` function, which will save all 6 
pages to corresponding `.csv` files with correct product data.

Hints:
- Do not copy-paste the code for different pages scraping;
- Write the global logic for parsing the single page;
- Be aware of `accept cookies` button, while developing, possible fix - just to click it, when it appears;
- Sometimes, you need to wait a bit, while your driver is acting after some event;
- Make your code as clean as possible.

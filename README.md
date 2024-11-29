
## Description

This time I implement the scraper for [E-commerce test-site](https://webscraper.io/test-sites/e-commerce/more/).
It scrape & parse info about all products and all pages.

The list of pages is next:
- [home](https://webscraper.io/test-sites/e-commerce/more) page (3 random products);
- [computers](https://webscraper.io/test-sites/e-commerce/more/computers) page (3 random computers);
- [laptops](https://webscraper.io/test-sites/e-commerce/more/computers/laptops) page (117 laptops) with `more button` pagination;
- [tablets](https://webscraper.io/test-sites/e-commerce/more/computers/tablets) page (21 tablets) with `more button` pagination;
- [phones](https://webscraper.io/test-sites/e-commerce/more/phones) page (3 random phones);
- [touch](https://webscraper.io/test-sites/e-commerce/more/phones/touch) page (9 touch phones) with `more button` pagination.

All of these pages are  scraped & content of products are written in corresponding `.csv` file.
For ex. results for `home page` -> `home.csv`, `touch page` -> `touch.csv`.

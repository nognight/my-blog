---
title: Python Starter lesson-4
pubDate: '2022-09-09'
description: 'Python lesson 4: Crawler part2 and pipeline modification'
tags: python
heroImage: '../../assets/blog-placeholder-1.jpg'
---

# crawler part2

## crawler for pic

### add items
```python
class ImageItem(scrapy.Item):
    title = scrapy.Field()
    image_url = scrapy.Field()
    download = scrapy.Field()
    pass
```

### create a spider
```python

import scrapy

from good_job.items import ImageItem
from urllib.parse import urljoin


class ImageCollectorSpider(scrapy.Spider):
    name = 'image_collector'
    allowed_domains = ['douban.com']
    start_urls = ['https://movie.douban.com/top250']

    def parse(self, response):
        item = ImageItem()
        selector = scrapy.Selector(response)
        movies = selector.xpath('//div[@class="item"]')
        for eachMovie in movies:
            title = eachMovie.xpath(
                'div[@class="info"]/div[@class="hd"]/a/span/text()').extract()
            fullTitle = "".join(title)

            image_url = eachMovie.xpath(
                'div[@class="pic"]/a/img/@src').extract()

            item['title'] = fullTitle
            item['image_url'] = image_url
            yield item
        next_link = selector.xpath('//span[@class="next"]/link/@href').extract()

        if next_link:
            next_link = next_link[0]
            yield scrapy.Request(urljoin(response.url, next_link), callback=self.parse)

        pass


```
### modify pipeline
```python

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface


import time
import pandas as pd
import scrapy
from scrapy.exceptions import DropItem

from good_job.items import GoodJobItem
from good_job.items import ImageItem
from scrapy.pipelines.images import ImagesPipeline


from itemadapter import ItemAdapter

COLUMNS = ('title', 'movie_info', 'star', 'quote')

IMAGE_COLUMNS = ('title', 'image_url', 'download')


# pip3 install Pillow
class CustomizeImagesPipeline(ImagesPipeline):

    def get_media_requests(self, item, info):
        adapter = ItemAdapter(item)
        if len(adapter) != 4:
            for url in adapter.get('image_url', []):
                yield scrapy.Request(url)

    def item_completed(self, results, item, info):
        image_paths = [x['path'] for ok, x in results if ok]
        if not image_paths:
            raise DropItem("Item contains no images")

        item['download'] = time.time()
        return item



class GoodJobPipeline:

    data_list = []

    images = []

    def __init__(self):
        print('init')

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        if len(adapter) == 4:
            self.data_list.append(
                (adapter.get('title'), adapter.get('movie_info'), adapter.get('star'), adapter.get('quote')))
        else:
            self.images.append(
                (adapter.get('title'), adapter.get('image_url'), adapter.get('download')))

        return item

    def close_spider(self, spider):
        pd.DataFrame(
            self.data_list,
            columns=COLUMNS
        ).to_csv("first_spider.csv", index=False)

        pd.DataFrame(
            self.images,
            columns=IMAGE_COLUMNS
        ).to_csv("image_collector.csv", index=False)

```

### modify settings
```python

USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36'



IMAGES_STORE = '/Users/nognight/PycharmProjects/good_job/images'

ROBOTSTXT_OBEY = False

ITEM_PIPELINES = {
    'good_job.pipelines.CustomizeImagesPipeline': 299,
    'good_job.pipelines.GoodJobPipeline': 300,
}
```



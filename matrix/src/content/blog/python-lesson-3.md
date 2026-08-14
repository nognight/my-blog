---
title: Python Starter lesson-3
pubDate: '2022-09-01'
description: 'Python lesson 3: GFW and crawler frameworks'
tags: python
heroImage: '../../assets/blog-placeholder-1.jpg'
---

# about gfw
## how it works
- IP black list
- Keywords block (HTTP POP3 SMTP)
- BigData, DeepLearning
- Protocal black list (pptp l2tp socks5)
- DNS cache pollution/poisoning

![GFW](https://raw.githubusercontent.com/nognight/my-diagram/main/GFW.png "GFW")

## what we can do
- change hosts
- change dns
- use proxy

# how to prepare python runtime for android
- use the latest version for Termux v0.118.0
    [Download Link](https://www.apkmirror.com/apk/fredrik-fornwall/termux-fdroid-version/termux-fdroid-version-0-118-0-release/termux-fdroid-version-0-118-0-android-apk-download/)

# what is crawler (part1)
- get information
- from website

## how to choose crawler framework
### scrapy
- high perfomance
- open source
- maybe simple?

## start our demo

### install scrapy
```shell
pip3 install scrapy
```
### create  project
```
scrapy startproject good_job
```

### add items
```python
import scrapy

class GoodJobItem(scrapy.Item):
    # define the fields for your item here like:
    title = scrapy.Field()
    movieInfo = scrapy.Field()
    star = scrapy.Field()
    quote = scrapy.Field()
    pass
```

### create a spider
```python
from good_job.items import GoodJobItem

import scrapy
from urllib.parse import urljoin

class FirstSpider(scrapy.Spider):
    name = 'first'
    allowed_domain = ['douban.com']
    start_urls = ['https://movie.douban.com/top250']

    def parse(self, response):
        item = GoodJobItem()
        selector = scrapy.Selector(response)
        movies = selector.xpath('//div[@class="info"]')
        for each_movie in movies:
            title = each_movie.xpath('div[@class="hd"]/a/span/text()').extract()
            full_title = "".join(title) 
            movie_info = each_movie.xpath('div[@class="bd"]/p/text()').extract()
            star = each_movie.xpath('div[@class="bd"]/div[@class="star"]/span/text()').extract()[0]
            quote = each_movie.xpath('div[@class="bd"]/p[@class="quote"]/span/text()').extract()
    
            if quote:
                quote = quote[0]
            else:
                quote = ''
            item['title'] = full_title
            item['movie_info'] = ';'.join(movie_info)
            item['star'] = star
            item['quote'] = quote
            yield item
        next_link = selector.xpath('//span[@class="next"]/link/@href').extract()
        
        if next_link:
            next_link = next_link[0]
            yield scrapy.Request(urljoin(response.url, next_link), callback=self.parse)
```
### create pipeline
```python
# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter

import pandas as pd


COLUMNS = ('title', 'movie_info', 'star', 'quote')


class GoodJobPipeline:

    data_list = []

    def __init__(self):
        print('init')

    def process_item(self, item, spider):
        self.data_list.append(
            (item['title'], item['movie_info'], item['star'], item['quote']))
        return item

    def close_spider(self, spider):
        df = pd.DataFrame(
            self.data_list,
            columns=COLUMNS
        )
        df.to_excel("first_spider.xlsx", index=False, sheet_name='douban')

```

### modify setting
```python

USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36'

ITEM_PIPELINES = {
   'good_job.pipelines.GoodJobPipeline': 300,
}
```



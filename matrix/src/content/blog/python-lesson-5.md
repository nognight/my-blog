---
title: Python Starter lesson-5
pubDate: '2022-09-13'
description: 'Python lesson 5: Music crawler and pipeline implementation'
tags: python
heroImage: '../../assets/blog-placeholder-1.jpg'
---

# crawler part3

## modify spider with xpath

### what is xpath
- xpath is XML Path Language

### what is XML/HTML what is the relationship between XML and HTML
- HTML is HyperText Markup Language
- XML Extensible Markup Language
- the same parent
- can transfer to another

| HTML |	XML |
| :----   | :----   |
| HTML is static in nature.	| XML is dynamic in nature. |
| HTML is a markup language.	| XML provides framework to define markup languages. |
| HTML can ignore small errors.	| XML does not allow errors. |
| HTML is not Case sensitive.	| XML is Case sensitive.| 
| HTML tags are predefined tags.	| XML tags are user defined tags. |
| There are limited number of tags in HTML.	| XML tags are extensible. |
| HTML does not preserve white spaces.	| White space can be preserved in XML. |
| HTML tags are used for displaying the data.	|XML tags are used for describing the data not for displaying.|
| In HTML, closing tags are not necessary.	| In XML, closing tags are necessary. |
| HTML is used to display the data.	| XML is used to store data. |
| HTML does not carry data it just display it.	| XML carries the data to and from database. |
| HTML offers native object support.	| IN XML , the objects are expressed by conventions using attributes. |
| HTML document size is relatively small.	| XML document size is relatively large as the approach of formatting |



### add items
```python

class MusicItem(scrapy.Item):
    title = scrapy.Field()
    img_url = scrapy.Field()
    artist = scrapy.Field()
    release_year = scrapy.Field()
    kind = scrapy.Field()
    disc_type = scrapy.Field()
    music_type = scrapy.Field()
    score = scrapy.Field()

```

### create a spider
```python

import scrapy

from good_job.items import MusicItem
from urllib.parse import urljoin


class MusicSpider(scrapy.Spider):
    name = 'music'
    allowed_domains = ['douban.com']
    start_urls = ['https://music.douban.com/top250']

    def parse(self, response):
        item = MusicItem()
        # request web page
        selector = scrapy.Selector(response)

        containers = selector.xpath('//*[@id="content"]/div/div/div/table')

        for container in containers:
            img_url = container.xpath('tr/td/a/img/@src').extract()
            title = container.xpath('tr/td/div/a/text()').extract()
            artist_detail = container.xpath('tr/td/div/p/text()').extract()
            score = container.xpath(
                'tr/td/div/div/span/text()').extract()

            item["img_url"] = img_url
            item["title"] = title[0].strip()

            artist_detail_list = artist_detail[0].strip().split(' / ')

            item["artist"] = artist_detail_list[0]
            item["release_year"] = artist_detail_list[1]
            item["kind"] = artist_detail_list[2]
            item["disc_type"] = artist_detail_list[3]
            item["music_type"] = artist_detail_list[4]

            item["score"] = score[0].strip()

            # still need return
            yield item
            next_link = selector.xpath('//*[@id="content"]/div/div/div/div[26]/span[3]/link/@href').extract()

            if next_link:
                next_link = next_link[0]
                yield scrapy.Request(urljoin(response.url, next_link), callback=self.parse)
        pass



```

there is [(),(),()...]  

for each '()' in [(),(),()...]

type_name  = ("type").type

column.append(type_name)

column.append(type_name.height + 1 )


define {}

add k1
{k1:1}


add k1
{k1:2}
add k2
{k1:2}


then {k1:2 , k2:1}

get keys [k1,k2] = column
get values [2,1] =height

we want pic like:
2  1
k1,k2

```

```
### modify pipeline
```python

class MusicPipline:
    data_list = []
    translator = Translator(service_urls=[
        'translate.google.com.hk'
    ])

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        temp = adapter.get('music_type')
        result = self.translator.translate(temp)
        self.data_list.append(
            (adapter.get('title'), adapter.get('img_url'), adapter.get('artist'),
             adapter.get('release_year'), adapter.get('kind'), adapter.get('disc_type'),
             result.text, adapter.get('score'))
        )

    def close_spider(self, spider):
        music_dict = {}

        for item in self.data_list:
            if item[6] in music_dict:
                music_dict[item[6]] = music_dict[item[6]] + 1
            else:
                music_dict[item[6]] = 1

        fig, ax = plt.subplots()

        types = list(music_dict.keys())
        counts = list(music_dict.values())

        ax.bar(types, counts)

        ax.set_ylabel('set_ylabel')
        ax.set_title('set_title')
        ax.legend(title='title')

        plt.show()

    def __init__back(self):

        translator = Translator(service_urls=[
            'translate.google.com.hk'
        ])
        result = translator.translate("流行")
        print(result.text)

        self.data_list = [("21", "url", "Adele", "2011-01-24", "专辑", "cd", "popular", "9.3"),
                          ("21", "url", "Adele", "2011-01-24", "专辑", "cd", "rock", "9.3"),
                          ("21", "url", "Adele", "2011-01-24", "专辑", "cd", "rock", "9.3")]
        self.close_spider(self)


# MusicPipline()

```

### modify settings
```python

ITEM_PIPELINES = {
   # 'good_job.pipelines.CustomizeImagesPipeline': 299,
   # 'good_job.pipelines.GoodJobPipeline': 300,
   'good_job.pipelines.MusicPipline': 301,
}

```



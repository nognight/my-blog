---
title: Some sql for date in mysql
pubDate: '2020-09-20'
description: ''
tags: 
- mysql
- date
- sql
heroImage: '../../assets/blog-placeholder-about.jpg'
---


# Some sql for date in mysql

## 当前天
```sql
SELECT curdate();
```
## 上月的今日
```sql
SELECT date_add(curdate(),INTERVAL-1MONTH);
```
## 昨天统计对象
```sql
SELECT date_add(curdate(),interval-1day);
SELECT date_sub(curdate(),interval1day);
```
## 上月的昨天
```sql
SELECT date_add(date_sub(curdate(),interval1day),INTERVAL-1MONTH);
```
## 按今天算本月第一天
```sql
select date_add(date_add(last_day(curdate()),interval1day),interval-1month);
```
## 按昨日算本月第一天
```sql
select date_add(date_add(last_day(date_add(curdate(),interval-1day)),interval1day),interval-1month);
```
## 按今天算上月第一天
```sql
select date_add(date_add(last_day(curdate()),interval1day),interval-2month);
```
## 按昨日算上月第一天
```sql
select date_add(date_add(last_day(date_add(curdate(),interval-1day)),interval1day),interval-2month);
```
## 按昨日算上月最后一天
```sql
select date_add(last_day(date_add(curdate(),interval-1day)),INTERVAL-1MONTH);
```

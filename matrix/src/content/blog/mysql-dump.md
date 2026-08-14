---
title: Some command to dump data for mysql
pubDate: '2019-09-22'
description: ''
tags: 
- mysql
- mysqldump
- dump
---


# Some command to dump data for mysql


## dump db
```bash
mysqldump -h 192.168.77.20 -uname -ppwd -d db_name > ./db_name.sql
```

## dump table
```bash
mysqldump -h 192.168.77.20 -uname -ppwd db_name t_name > ./db_name.t_name.sql
```

## dump table with where
```bash
mysqldump -h 192.168.77.20 -uname -ppwd db_name t_name --where="true limit 0,3000000" --lock-tables=false > ./db_name.t_name.sql
```

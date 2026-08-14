---
title: Some command to create database and user for mysql
pubDate: '2019-09-20'
description: ''
tags: mysql
heroImage: '../../assets/blog-placeholder-about.jpg'
---


# some command to create database and user for mysql


## delete the database if it is already exsit
```sql
drop database wordpress;
```

## create db
```sql
create database wordpress DEFAULT CHARSET utf8mb4 COLLATE utf8mb4_general_ci; 
```

## create user for db
```sql
CREATE USER 'wordpress'@'%' IDENTIFIED BY 'wordpress';
```

## grant privilege
```sql
GRANT ALL ON wordpress.* TO 'wordpress'@'%' IDENTIFIED BY 'wordpress';
```

## flush
```sql
flush privileges;  
```

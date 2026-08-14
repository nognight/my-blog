---
title: how to open mysql event
pubDate: '2020-01-10'
description: ''
tags: 
- mysql
- event
- procedure
heroImage: '../../assets/blog-placeholder-about.jpg'
---


# some command to open event_scheduler for mysql


## show event
### 首先要停止MYSQL服务
```sql
SHOW VARIABLES LIKE 'event_scheduler';
```

## open event
### 首先要停止MYSQL服务
#### 重启mysql又会回到默认关闭状态。
```sql
SET GLOBAL event_scheduler = ON;
```

## 第二种方法是修改配置文件：
### 在my.ini文件or my.cnf文件中[mysqld]外面添加
```conf
event_scheduler=ON
```

## create event 
```sql
use db_name;
drop EVENT IF EXISTS expire_event;
CREATE EVENT expire_event
  ON SCHEDULE EVERY 1 DAY STARTS  '2000-01-01 00:00:01'
  DO
  call expire_procedure(now());
 ``` 

## create procedure 
 ```sql
CREATE PROCEDURE expire_procedure(IN in_time DATETIME)
  BEGIN
  update t_user_coupon set status = -7 where t_user_coupon.expire_time <= in_time;
  update t_user_privilege set status = -7 where t_user_privilege.expire_time <= in_time;
END;
```

---
title: setup the master slave mode for mysql
pubDate: '2019-08-20'
description: ''
tags: 
- master-slave
heroImage: '../../assets/blog-placeholder-about.jpg'
---

# setup the one master two slave mode for mysql

## config file
### modify the my.cnf

```conf
server-id=2

default-time-zone='+8:00'

user=mysql
datadir=/home/mysql/data
log-bin=/home/mysql/data/mysql-bin
binlog_format=mixed

slow_query_log = 1
slow_query_log_file = /home/mysql/log/slow-query.log
long_query_time = 1

log-error=/home/mysql/log/mysqld.log
pid-file=/home/mysql/run/mysqld.pid
socket=/home/mysql/lib/mysql.sock
sql_mode=STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_AUTO_CREATE_USER,NO_ENGINE_SUBSTITUTION

symbolic-links=0
```

### create dir

```bash
mkdir /home/mysql/log
mkdir /home/mysql/run
mkdir /home/mysql/lib

mkdir /home/mysql
chgrp -R mysql  /home/mysql
chown -R mysql:mysql  /home/mysql

mkdir /home/mysql/log
mkdir /home/mysql/run
mkdir /home/mysql/lib
mkdir /home/mysql/data
chgrp -R mysql  /home/mysql/*
chown -R mysql:mysql  /home/mysql/*

mysqld --initialize
```

### user password
```sql
alter user user() identified by "dzjcU3t}1x66<2Y";
```

### user privilege 
```sql
GRANT replication slave ON *.* TO 'slave'@'%' IDENTIFIED BY 'dzjcU3t}1x66<2Y'; 
show master status;
```
```
+------------------+----------+--------------+------------------+-------------------+
| File             | Position | Binlog_Do_DB | Binlog_Ignore_DB | Executed_Gtid_Set |
+------------------+----------+--------------+------------------+-------------------+
| mysql-bin.000008 |      438 |              |                  |                   |
+------------------+----------+--------------+------------------+-------------------+
```
### 
```sql
stop slave;

CHANGE MASTER TO MASTER_HOST='192.168.20.101',

MASTER_USER='slave',

MASTER_PASSWORD='dzjcU3t}1x66<2Y',

MASTER_LOG_FILE='mysql-bin.000008',

MASTER_LOG_POS=438;

start slave;
show slave status;
````

````
stop slave;

CHANGE MASTER TO MASTER_HOST='192.168.20.102',

MASTER_USER='slave',

MASTER_PASSWORD='dzjcU3t}1x66<2Y',

MASTER_LOG_FILE='mysql-bin.000037',

MASTER_LOG_POS=438;

start slave;
show slave status;
```

```sql
create database ahst DEFAULT CHARSET utf8 COLLATE utf8_general_ci; 
CREATE USER 'ahst'@'%' IDENTIFIED BY 'passwd';
GRANT ALL ON ahst.* TO 'ahst'@'%' IDENTIFIED BY 'ahst';
flush privileges;
```




---
title: how to setup iptable
pubDate: '2020-01-23'
description: ''
tags: iptable
heroImage: '../../assets/blog-placeholder-about.jpg'
---



### 在Linux服务器被攻击的时候，有的时候会有几个主力IP。如果能拒绝掉这几个IP的攻击的话，会大大减轻服务器的压力，说不定服务器就能恢复正常了。
### 在Linux下封停IP，有封杀网段和封杀单个IP两种形式。一般来说，现在的攻击者不会使用一个网段的IP来攻击（太招摇了），IP一般都是散列的。于是下面就详细说明一下封杀单个IP的命令，和解封单个IP的命令。
### 在Linux下，使用ipteables来维护IP规则表。要封停或者是解封IP，其实就是在IP规则表中对入站部分的规则进行添加操作。

## 要封停一个IP，使用下面这条命令：
```
iptables -I INPUT -s ***.***.***.*** -j DROP
```
## 要解封一个IP，使用下面这条命令：
```
iptables -D INPUT -s ***.***.***.*** -j DROP
```
### 参数-I是表示Insert（添加），-D表示Delete（删除）。后面跟的是规则，INPUT表示入站，***.***.***.***表示要封停的IP，DROP表示放弃连接。
## 此外，还可以使用下面的命令来查看当前的IP规则表：
```
iptables -list
```
## 比如现在要将123.44.55.66这个IP封杀，就输入：
```
iptables -I INPUT -s 123.44.55.66 -j DROP
```
## 要解封则将-I换成-D即可，前提是iptables已经有这条记录。如果要想清空封掉的IP地址，可以输入：
```
iptables -flush
```
## 要添加IP段到封停列表中，使用下面的命令：
```
iptables -I INPUT -s 121.0.0.0/8 -j DROP
```
### 其实也就是将单个IP封停的IP部分换成了Linux的IP段表达式。关于IP段表达式网上有很多详细解说的，这里就不提了。
## 相信有了iptables的帮助，解决小的DDoS之类的攻击也不在话下！
### 附：其他常用的命令
## 编辑 iptables 文件
```
vi /etc/sysconfig/iptables
```
## 关闭/开启/重启防火墙
```
/etc/init.d/iptables stop  
```
### start 开启  
### restart 重启

## 验证一下是否规则都已经生效：
```
iptables -L
```
## 保存并重启iptables
```
/etc/rc.d/init.d/iptables save  
service iptables restart
```


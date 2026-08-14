---
title: jvm heap
pubDate: '2020-03-19'
description: ''
tags: 
- jvm
heroImage: '../../assets/blog-placeholder-about.jpg'
---


# 堆实际上是一棵完全二叉树

## 非堆内存就一个永久代（Permanent Generation）

## JDK1.8版本废弃了永久代，替代的是元空间（MetaSpace）,：元空间并不在JVM中，而是使用本地内存

|  heap   |               |                 |        |
|  ----   | ----          | ----            | ----   |
| young   |     .         |       .         |   old  |
| 1/3     |      .        |       .         |   2/3  |
| eden    | Survivor from |  Survivor to    |        |
| 8/10    | 1/10          |  1/10           |        |

## GC
- Minor  GC ： 清理年轻代 
- Major GC ： 清理老年代
- Full GC ： 清理整个堆空间，包括年轻代和永久代

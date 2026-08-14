---
title: some type for jvm gc
pubDate: '2020-03-20'
description: ''
tags: 
- jvm
heroImage: '../../assets/blog-placeholder-about.jpg'
---


# Serial
```
-XX:+UseSerialGC
```
- 单线程精简的GC实现，无需维护复杂的数据结构，初始化简单，是client模式下JVM默认选项。最古老的GC。
- 会进入"Stop-The-World"状态。

# CMS
```
-XX:+UseConcMarkSweepGC
```
- jdk1.5引入（jdk 14中彻底删除了cms，jdk 9标记为deprecated）
- 并发标记（准确的说，又分为初始标记、并发标记、重新标记，第1、3通常需要STW）、清理收集器，响应时间优先


# G1
```
-XX:+UseG1GC
```
- (Garbage First)：其目标是尽可能完全避免full gc，即老年代的STW，优先考虑暂停时间、其次才是吞吐量，所以更像是cms的升级版。jdk9默认GC
- 可以直观的设值停顿时间，相对于CMS GC ，G1未必能做到CMS最好情况下的延时停顿，但比最差情况要好得多
- G1 仍存在年代的概念，使用了Region棋盘算法，实际上是标记-整理（Mark-Compact）算法，可以避免内存碎片，尤其是heap非常大的时候，G1优势明显。
- G1 吞吐量和停顿表现都OK。


# parallel
```
-XX:+UseParallelGC
```
- jdk8,server模式JVM的默认GC选择，吞吐量优先。
- 随着负载加大，以及更大的堆，GC的停顿时间也会增加。


# ZGC
```
-XX:+UseSerialGC
```
- zgc：jdk 11引入,只能在64位的机器上使用ZGC,适用于20GB以上内存,号称STW在10ms之内
- 完全废除老年代新生代的概念,核心在于着色指针
- GA



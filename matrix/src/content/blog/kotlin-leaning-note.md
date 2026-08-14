---
title: kotlin learning note
pubDate: '2021-10-01'
description: ''
tags: kotlin
heroImage: '../../assets/blog-placeholder-about.jpg'
---


# null-safety
```kotlin
data class Person(val name:String)

fun main(args: Array<String>) {
    var s = "cc"
    s = null  //null can not be a value of a non-null type String

    var i = 996
    i = null  //null can not be a value of a non-null type Int

    var p = Person("ccy")
    p = null  //null can not be a value of a non-null type Person
}

```

# null-safety
```kotlin
data class Person(val name:String)

fun main(args: Array<String>) {
    var s: String? = "cc"
    s = null

    var i:Int? = 99
    i = null

    var p:Person? = Person("ccy")
    p = null

    var list:MutableList<Int>? = mutableListOf(1, 2, 3)
    list = null
}
```


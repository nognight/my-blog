---
title: improve the page sroll perfermance
pubDate: '2021-09-20'
description: 'CSS content-visibility property for performance optimization'
tags: css
heroImage: '../../assets/blog-placeholder-1.jpg'
---


# content-visibility   browser >= chrome85

- CSS property controls whether or not an element renders its contents at all.
- along with forcing a strong set of containments.
- allowing user agents to potentially omit large swathes of layout and rendering work until it becomes needed.
- Basically it enables the user agent to skip an element's rendering work (including layout and painting) until it is needed 


```css
/* Keyword values */
content-visibility: visible; /*  default */
content-visibility: hidden;
content-visibility: auto;  /*  */

/* Global values */
content-visibility: inherit;
content-visibility: initial;
content-visibility: revert;
content-visibility: unset;
```

### may case the scroll bar bug
- the page total hight is changed
```css
contains-intrinsic-size:200px
```


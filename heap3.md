# https://exploit.education/phoenix/heap-three/ (x86)

## There is no catch in this exercise, just a hard work of analyzing the given heap implementation and finding a way to exploit a vulnerability in it. So let's start :) 

* So first of all we need to understand the heap structure. Luckily [the source code](malloc-2.7.2.c#L1847)
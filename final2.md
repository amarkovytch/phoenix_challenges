# https://exploit.education/phoenix/final-two/ (x86)

### This exercise is really similar to [heap3.md](heap3.md), with some caveats though. Before diving into this solution, please read the solution of the other exercise

* The first caveat is just a bug in the exercise code. Without fixing it, solving the exercise turns to be a really hard (or even impossible) task, or so I was told :) As you probably noticed yourself, the allocated buffers are not saved in *destroylist*, which causes the *free* to be called on garbage values. This not only leaves you with no simple way of using the heap overflow (which we will discuss in a moment) but turns the code into non stable without even triggering any overflow whatsoever. You can compile the [correct version](final2.c) with this command :

    ```shell

    gcc -m32 -DLEVELNAME=\"XXX\" -fno-stack-protector -z execstack -no-pie final2.c malloc-2.7.2.c -o final2

    ```
    (I disabled the randomization and NX protection because it was turned off in the original exercise as well)

* After carefully examining the exercise code, we can notice that one of the vulnerabilities is that *start* pointer can easily underflow the limits of heap chunk representing the current request. We can thus craft 2 requests in such a way that the second request has payload that will be copied to previous request with enough length to overflow the metadata of second heap chunk
* The exploitation technique is really similar to what we saw in **heap3** exercise - we achieve arbitrary write primitive and play around with plt/got entries. There is one caveat though compared to **heap3** exercise
* Unlike the previous exercise, the memory is not allocated in *fastbins* here, thus each *free* call affects the metadata of the next chunks as well. The easiest way to achieve what we want would be by finding a way to trigger the write primitive in the very first call to *free*. Moreover we want to be sure the next *free*s are either not called at all or at least do not cause our program to crash before we get to the execution of our payload. 
* Luckily there is a way to achieve the above by triggering the *consolidate forward* path in *free* for the first freed chunk. This path will use **FD** / **BD** memory pointers controlled by us in the second chunk. For the full solution with some occasional comments please see [final2-exploit.py](final2-exploit.py)
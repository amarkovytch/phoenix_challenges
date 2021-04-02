# https://exploit.education/phoenix/heap-three/ (x86)

## There is no catch in this exercise, just a hard work of analyzing the given heap implementation and finding a way to exploit a vulnerability in it. So let's start :) 

* So first of all we need to understand the heap structure. Luckily [the source code](malloc-2.7.2.c#L1847) has quite an extensive documentation which you need to read to understand the below explanations. The most important part is this structure :

    ```c 
    struct malloc_chunk {

        INTERNAL_SIZE_T      prev_size;  /* Size of previous chunk (if free).  */
        INTERNAL_SIZE_T      size;       /* Size in bytes, including overhead. */

        struct malloc_chunk* fd;         /* double links -- used only if free. */
        struct malloc_chunk* bk;
    };

    ```
* Heap overflow allows you to control metadata. But what can you do with this ? Some logical thinking (and some previous knowledge :) ) should lead you to the inevitable conclusion that the only place where this metadata corruption can be exploited is *free* function

* After some digging into the logic of *free* you will notice this very interesting piece of code: 
    ```c
    /* Take a chunk off a bin list */
    #define unlink(P, BK, FD) {                                            \
        FD = P->fd;                                                          \
        BK = P->bk;                                                          \
        FD->bk = BK;                                                         \
        BK->fd = FD;                                                         \
    }

    ```
    So it looks that if you can reach this piece of code and you can control *fd* and *bk* pointers you can achieve a [write-what-where primitive](https://cwe.mitre.org/data/definitions/123.html). There is a catch though, you get 2 arbitrary writes at the price of one : 

    ```code
    *(BK + 8) = FD
    *(FD + 12) = BK
    ```
    This is a bit annoying since we get a redundant memory write which can corrupt data we don't want to get corrupted

* So let's assume we can safely place anything we want at *fd / bk* without messing up anything else on the way and that we can also reach the unlink code, what can we do with this ? Well, we could, for example, change **PLT** pointer for *printf* (or if you look closely at assembly, it is actually *puts* that is used) and make it call *winner* instead (look at [heap1.md](heap1.md) for more info on this technique). The only issue is that you have that double write we mentioned previously, so if you overwrite **PLT** pointer of *puts* with winner, it will also mean that *winner* code at the offset of 12 will get overridden as well ... So how do you overcome this problem ? Quite simple, don't jump to *winner* from **PLT**, jump to your own code (stored on heap for example) that will do anything you like, including jumping to *winner*. But wait, then your code will get overridden at offset 12 ! So what ? Place a *jump +XXX* instruction at the beginning of your code that will safely skip any garbage ...

* Okay, so now we know what to do with our double arbitrary write, but how do we get there ? Let's look closely at the *malloc_chunk* structure and at the *free* code. By the way, to effectively solve this exercise you will need to find a way to perform many trials and errors with gdb. You can either debug *free* assembly like I did (just to get more hands on experience with assembly code) or recompile the exercise with debug symbols and then specify *malloc-2.7.2.c* source code in gdb. If you want to go with assembly, IDA can help a lot as a side tool to comment and parse the assembly code (this is much easier when you can reference the source code)
* The first thing you will notice is that you can't override *fd / bk* without touching the *prev_size* and *size* and obviously you can specify 0-es in your input. So you will have to overrite these to huge values
* Secondly you have to change the size of the chunk you will be freeing from 40 (32 + 8 bytes of header) to something that is bigger than *av->max_fast* (72). As mentioned previously, this would also change the *prev_size* for the same chunk to something big (16M +)
* So the above leaves us with the only plausible option. We need to reach this piece of code : 

    ```c
        if (nextchunk != av->top) {
            /* get and clear inuse bit */
            nextinuse = inuse_bit_at_offset(nextchunk, nextsize);
            set_head(nextchunk, nextsize);

            /* consolidate forward */
            if (!nextinuse) {
                unlink(nextchunk, bck, fwd); // <----------------
                size += nextsize;
            }

    ```
* So which of the 3 allocated buffers metadata shall we overwite ? The easiest one will be probably *c* (it is also freed the first). Luckily for us, if we only modify it's metadata the other 2 buffers (*a* and *b*) will not be influence since they will be freed by a completely different logic path that uses *fastbins* therefore will not be influence by our games with size and *forward consolidation* of *c* 

* So to put this all together, we shall modify the metadata of chunk *c* and place data in *c* in such a way that we trick it to think that it *consolidates forward* the "next chunk" (that didn't really exist) that lies at the offset of size. The *bd / fd* also located in that "virtual next chunk". 
* There is one last catch here. The *size* of the "next chunk" is used to check the *nextinuse* bit. As we already saw we need to place some non 0 bytes there to get to *bd / fd* . What can we place there to avoid having huge values and pointing to something that is either not allocated or not in our control ? The trick is simple, use negative values ! This way you can have a small negative offset without using any 0-s. 
* To see it all together, please look at the [hea3-explot.py](heap3-exploit.py) that produces the arguments needed for the exploit:
```console
    /opt/phoenix/i486/heap-three $(python heap3-exploit.py)
```

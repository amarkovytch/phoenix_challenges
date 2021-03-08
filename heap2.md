# https://exploit.education/phoenix/heap-one/ (x86)

### The basic idea behind the exploit occurred to me in a couple of minutes. It is how to make use of it correctly what took a couple of days

* So you have 4 heap allocated data structures: 2 structs, 2 char arrays. After some experimentation with GDB (and some logical thinking) you will discover that those 4 chunks are allocated in adjacent monotonically raising memory locations:
![](heap1.png)

* So ... Do you see where this is going ? The first *strcpy* allows you to place arbitrary memory location in second *ptr*. The second *strcpy* allows you to place any value inside this location. We've got ourselves a [write-what-where primitive](https://cwe.mitre.org/data/definitions/123.html). The possibilities are now endless !
* So the first thing I tried to do is to follow the standard path and change the ret value on stack so that we jump to *winner* function when *main* finishes. This approach turned out to be problematic. First of all, if you just overwrite the *main* ret, the *winner* will be called, but the program will crash immediately after that. You need to place the original address to which *main* was supposed to return right next to *winner* on the stack. Second and more important issue. You need to supply the exact address on stack where *main*'s return address resides. This is super fragile and environment dependent. You can end up like me making your exploit work in GDB, but after that spending days of figuring out why this doesn't work without GDB. [We already saw](stack5.md) the trick with LINES and COLUMNS, but apparently even on the same machine this still does not guarantee that the stack offset will be exactly the same with vs without GDB, not talking about building an exploit on your local machine for some remote host which you do not control and which environment variables you don't necessarily know. In fact in this exercise, I wasn't able to reproduce the exact same stack address. I did discover a simple technique on how to run a process without GDB and then make it stuck so that you can attach with GDB. In this case, you will see the stack addresses (and environment) exactly as they will be present if you run the exe directly. See [patch2help](https://github.com/amarkovytch/research_tools#patch2halt) for more info. In case you want to play with this on your own, be my guest, this is what worked with GDB on my environment 

    ```console
    python3 -c "import sys; sys.stdout.buffer.write(b'A'*0x14 + b'\x0c\xd7\xff\xff' + b' ' + b'\x9a\x88\x04\x08' + b'\x54\xf6\xf8\xf7')"

    ```
* Next thing I tried was to patch a particular piece of code to jump into *winner* function. The natural candidate was the call to the last *printf* (or more precisely *puts* ) in main. This could give us a nice stable exploit. Unfortunately there is an annoying issue with patching this specific piece of code

    ```asm 
    8048883:       e8 28 fd ff ff          call   80485b0 <puts@plt>
    ```
    There are a couple of different forms of *call* opcode, this particular form take a relative address calculated from the next command : *e8 <4byte offset>*. In this case the offset is negative. The problem with patching this call to jump to *winner* is that we need a positive offset of 12 bytes: *e8 12 00 00 00* - this is something that we can't achieve with *strcpy*. There are most definitely ways to overcome this limitation, such as simply finding some other piece of code that we could patch in some way that it jumps to the desired function, but I preferred to exploit a much easier option instead

* [The magical GOT and PLT](https://systemoverlord.com/2017/03/19/got-and-plt-for-pwning.html). So without going into too much details (read the article for that) if we look at our binary disassembly (*objdump -d*):

    ```asm
    080485b0 <puts@plt>:
    80485b0:       ff 25 40 c1 04 08       jmp    *0x804c140
    80485b6:       68 28 00 00 00          push   $0x28
    80485bb:       e9 90 ff ff ff          jmp    8048550 <.plt>

    ```
    And at sections (*objdump -h*):

    ```asm 
    Sections:
    Idx Name          Size      VMA       LMA       File off  Algn
    16 .got.plt      00000044  0804c120  0804c120  00003120  2**2

    ```

    We can see that *puts* (like many other library functions) perform indirect jump to an address located at memory inside **Got Plt** table. Luckily for us, this table is writeable at runtime (which is not necessarily the case). So our final exploit is very simple, all we have to do is to put the address of *winner* function at this address:

    ```asm
    python3 -c "import sys; sys.stdout.buffer.write(b'A'*0x14 + b'\x40\xc1\x04\x08' + b' ' + b'\x9a\x88\x04\x08')"

    ```


## Bonus section 
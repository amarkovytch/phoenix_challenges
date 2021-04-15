# https://exploit.education/phoenix/final-zero/ (x86)

### This one is fairly simple, there are no new revelations here. The only reason I still decided to post the solution, is because this is the first exercise where I used the extraordinary [pwntools](https://docs.pwntools.com/en/latest/) library. It won't do the exploitation instead of you, but it will turn many annoying steps into complete joke. Bu sure to check out the [final0-exploit.py](final0-exploit.py)

```shell
 python final-zero.py | /opt/phoenix/i486/final-zero
```

* Note: be patient the library is pretty slow, it could take 10-20 seconds for the script to run inside the emulator, depending on your machine
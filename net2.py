from pwn import *


def main():
    HOST = 'localhost'
    PORT = '64012'
    UINT32_MASK = 0xFFFFFFFF

    conn = remote(HOST, PORT)
    conn.recvline()
    line_with_size = conn.recvline()

    size = int(chr(line_with_size[line_with_size.find("==".encode()) + 3]))

    if size != 4:
        raise Exception("Only 32 bit arch is supported at the moment")

    sum = 0
    for x in range(size):
        sum += u32(conn.recvn(size))

    conn.send(p32(sum & UINT32_MASK))
    print(conn.recvline())


if __name__ == "__main__":
    # execute only if run as a script
    main()

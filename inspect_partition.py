#!/usr/bin/env python3
"""Inspect an ESP32 partition table extracted by a read-only esptool command."""
import struct
import sys
from pathlib import Path

def parse(data):
    for offset in range(0,min(len(data),0x1000),32):
        row=data[offset:offset+32]
        if len(row)<32 or row==b"\xff"*32:
            break
        magic,typ,sub,address,size,label,flags=struct.unpack("<HBBII16sI",row)
        if magic==0xEBEB:
            break
        if magic!=0x50AA:
            raise ValueError("Bad partition magic at entry "+str(offset//32))
        yield dict(name=label.split(b"\0")[0].decode("ascii","replace"),type=typ,subtype=sub,offset=address,size=size,flags=flags)

if __name__=="__main__":
    if len(sys.argv)!=2:
        sys.exit("Usage: python inspect_partition.py partition.bin")
    entries=list(parse(Path(sys.argv[1]).read_bytes()))
    for p in entries:
        print(f"{p['name']:16} type={p['type']} subtype=0x{p['subtype']:02x} offset=0x{p['offset']:06x} size=0x{p['size']:06x}")
    apps=[p for p in entries if p["type"]==0 and p["subtype"] in (0x10,0x11)]
    ota=any(p["type"]==1 and p["subtype"]==0 for p in entries)
    if len(apps)!=2 or not ota or min((p["size"] for p in apps),default=0)<0x180000:
        print("WARNING: Cannot assume OTA compatibility. DO NOT OTA FLASH.")
    else:
        print("Two sufficiently large OTA slots detected, but offsets/layout must STILL be independently checked before flashing.")

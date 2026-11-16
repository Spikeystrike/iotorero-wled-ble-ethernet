#!/usr/bin/env python3
"""Build WLED 16.0.1 with Boardsesh BLE JSON and IoTorero Ethernet. NEVER flashes hardware."""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parent
WLED=ROOT/"_sources"/"WLED"
BLE=ROOT/"_sources"/"wled-usermod-ble-json"
DIST=ROOT/"dist"
WLED_COMMIT="29b389df1c1aaec6ff53aea742d17063b985906c"
BLE_COMMIT="a47f0e894d6d71302b25f3e97a8ba201811a3cf3"
MAX_SLOT=0x180000
ANCHOR='CJSON(ethernetType, ethernet["type"]);'
MIGRATION='''CJSON(ethernetType, ethernet["type"]);
  // Legacy IoTorero vendor WLED stored ethernetType=13; official WLED uses 6.
  // Guard the migration by the observed saved GPIO pin array.
  if (ethernetType == 13) {
    JsonArray oldIoToreroPins = ethernet["pin"];
    if (oldIoToreroPins.size() == 9 &&
        oldIoToreroPins[6].as<int>() == 23 &&
        oldIoToreroPins[7].as<int>() == 18 &&
        oldIoToreroPins[8].as<int>() == 17) {
      ethernetType = 6;
    }
  }'''

def run(*args,cwd=None):
    print("+",*args,flush=True)
    subprocess.run(args,cwd=cwd,check=True)

def output(*args,cwd=None):
    return subprocess.check_output(args,cwd=cwd,text=True).strip()

def checkout(url,path,commit):
    if not path.exists():
        path.parent.mkdir(parents=True,exist_ok=True)
        run("git","clone","--no-checkout",url,str(path))
    elif not (path/".git").exists():
        raise RuntimeError(f"Not a git checkout: {path}")
    run("git","fetch","--tags","--force","origin",commit,cwd=path)
    run("git","checkout","--force","--detach",commit,cwd=path)
    if output("git","rev-parse","HEAD",cwd=path)!=commit:
        raise RuntimeError("Git checkout SHA verification failed")

def validate_snapshot():
    cfg=json.loads((ROOT/"board_profile.json").read_text())
    assert cfg["current_ethernet_type"]==13 and cfg["target_ethernet_type"]==6
    assert cfg["saved_ethernet_pins"]==[21,19,22,25,26,27,23,18,17]
    assert [(x["gpio"],x["start"],x["length"]) for x in cfg["led_outputs"]]==[(5,0,35),(16,35,373),(4,408,71)]
    assert sum(x["length"] for x in cfg["led_outputs"])==479

def patch_cfg(text):
    if text.count(ANCHOR)!=1:
        raise RuntimeError("WLED config migration anchor missing or duplicated")
    return text.replace(ANCHOR,MIGRATION,1)

def patch_override(text):
    if "[ble_json]" not in text or "[env:boardsesh_ble_audio]" not in text:
        raise RuntimeError("BLE override structure changed")
    needle="-D CONFIG_BT_NIMBLE_MAX_CONNECTIONS=1"
    if text.count(needle)!=1:
        raise RuntimeError("BLE override NimBLE anchor changed")
    text=text.replace(needle,needle+"\n-D WLED_USE_ETHERNET\n-D WLED_ETH_DEFAULT=6\n-D DATA_PINS=5\n-D RLYPIN=2\n-D BTNPIN=0",1)
    needle="-D BLE_JSON_DEFAULT_ENABLED=1"
    if text.count(needle)!=1:
        raise RuntimeError("BLE default flag missing")
    return text.replace(needle,"-D BLE_JSON_DEFAULT_ENABLED=0",1)

def verify_ethernet():
    network=(WLED/"wled00"/"network.cpp").read_text()
    pattern=(r'// ESP3DEUXQuattro\s*\{\s*1,\s*// eth_address,\s*'
             r'-1,\s*// eth_power,\s*23,\s*// eth_mdc,\s*'
             r'18,\s*// eth_mdio,\s*ETH_PHY_LAN8720,\s*// eth_type,\s*'
             r'ETH_CLOCK_GPIO17_OUT\s*// eth_clk_mode\s*\}')
    if not re.search(pattern,network):
        raise RuntimeError("WLED type-6 Ethernet PHY profile does not match expected IoTorero pins")
    wifi=(WLED/"wled00"/"data"/"settings_wifi.htm").read_text()
    if '<option value="6">IoTorero/ESP32Deux/RGB2Go</option>' not in wifi:
        raise RuntimeError("IoTorero Ethernet type-6 UI mapping has changed")

def prepare():
    validate_snapshot()
    checkout("https://github.com/wled/WLED.git",WLED,WLED_COMMIT)
    checkout("https://github.com/boardsesh/wled-usermod-ble-json.git",BLE,BLE_COMMIT)
    verify_ethernet()
    cfg=WLED/"wled00"/"cfg.cpp"
    cfg.write_text(patch_cfg(cfg.read_text()),encoding="utf-8")
    path=BLE/"build"/"platformio_override.ini"
    override=path.read_text()
    override=override.replace("@WLED_ROOT@",str(WLED.resolve()))
    override=override.replace("symlink://../wled-usermod-ble-json",f"symlink://{BLE.resolve()}")
    (WLED/"platformio_override.ini").write_text(patch_override(override),encoding="utf-8")

def build(profile,pio):
    env="boardsesh_ble_audio" if profile=="audio" else "boardsesh_ble_no_audio"
    run(pio,"run","-d",str(WLED),"-e",env)
    binary=WLED/".pio"/"build"/env/"firmware.bin"
    data=binary.read_bytes()
    if not data or len(data)>MAX_SLOT:
        raise RuntimeError(f"{profile} image size {len(data)} exceeds the assumed OTA slot ({MAX_SLOT})")
    DIST.mkdir(parents=True,exist_ok=True)
    dest=DIST/f"IoTorero_WLED_16.0.1_BLE_ETH_{profile}_UNTESTED.bin"
    dest.write_bytes(data)
    digest=hashlib.sha256(data).hexdigest()
    dest.with_suffix(dest.suffix+".sha256").write_text(f"{digest}  {dest.name}\n")
    report={"candidate_only":True,"do_not_flash_without_partition_verification":True,
            "wled_commit":WLED_COMMIT,"ble_commit":BLE_COMMIT,"audio":profile=="audio",
            "ethernet_profile":6,"ble_enabled_by_default":False,
            "size_bytes":len(data),"assumed_app_slot_bytes":MAX_SLOT,"sha256":digest}
    dest.with_suffix(dest.suffix+".json").write_text(json.dumps(report,indent=2)+"\n")

def selftest():
    validate_snapshot()
    assert "ethernetType = 6;" in patch_cfg("before\n"+ANCHOR+"\nafter")
    sample="[ble_json]\n-D BLE_JSON_DEFAULT_ENABLED=1\n-D CONFIG_BT_NIMBLE_MAX_CONNECTIONS=1\n[env:boardsesh_ble_audio]\n"
    modified=patch_override(sample)
    assert "-D WLED_USE_ETHERNET" in modified
    assert "-D BLE_JSON_DEFAULT_ENABLED=0" in modified
    print("Offline self-test OK. Live build and hardware remain untested.")

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test",action="store_true")
    parser.add_argument("--prepare-only",action="store_true")
    parser.add_argument("--profile",choices=["audio","no-audio","both"],default="audio")
    parser.add_argument("--pio",default="pio")
    args=parser.parse_args()
    if args.self_test:
        selftest()
        return
    prepare()
    if args.prepare_only:
        return
    for profile in (["audio","no-audio"] if args.profile=="both" else [args.profile]):
        build(profile,args.pio)
    print("Build finished. NO controller has been flashed.")

if __name__=="__main__":
    try:
        main()
    except (OSError,RuntimeError,subprocess.CalledProcessError,AssertionError) as err:
        print("ERROR:",err,file=sys.stderr)
        sys.exit(1)

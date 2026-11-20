"""Run real Connected.cpp with fake ESP32/HTTP/NVS hooks. Never use radio or storage."""
import os, pathlib, shutil, subprocess, tempfile
here=pathlib.Path(__file__).resolve().parent
with tempfile.TemporaryDirectory(prefix="pocket-reel-wifi-") as tmp:
 stage=pathlib.Path(tmp)
 for file in ('Connected.cpp','Connected.h'):
  shutil.copyfile(here.parent/'WillowCreek'/file,stage/file)
 out=stage/'connected-privacy'
 subprocess.run([os.environ.get('CXX','g++'),'-std=c++17','-Wall','-Wextra','-Werror',
                 '-I',str(stage),'-I',str(here/'connect-shims'),str(stage/'Connected.cpp'),
                 str(here/'connected-privacy.cpp'),'-o',str(out)],check=True)
 for c in ('session','remember','previous','previous-remember','invalid-opt','same-ssid','bad-token','bad-host','ap-fails','write-fails','radio-write-fails','timeout','expired','cancel'):
  subprocess.run([str(out),c],check=True)
  print("Verified:",c)

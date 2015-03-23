"""
 Usage makeVCX.py [debug|release]
 will build vcx packet to target directory.

"""
import os
import datetime
import time
import shutil

import sys
sys.path.append('tools/python')

import srecord
from vComponents import *

if len(sys.argv) > 1:
  target = sys.argv[1:][0]
else:
  target = "debug"

#------------------------------------------------------------------------------
#
_CleanUp = []

def CleanUp ():
 for file in _CleanUp:
  print "removing '%s'" % file
  os.remove(file)
#------------------------------------------------------------------------------
#
date = time.strftime("%Y-%m-%dT%H:%M:%S")

TargetFilename = "API_MMX2_FLASH_TEST.vcx"
SourceDir = "."
SourceDir2 = "../out2/iar-avr/VB01129/" + target
SourceDir3 = "./../Application"
TargetFile = os.path.join(SourceDir2, TargetFilename)

TargetFile = os.path.abspath(TargetFile)

AddressOfStartEndTag = 0x0003FFFE
#-----------------------------------------------------------------------------
#
# make start srecord files.
#
def makeStart (address):
 filename = "_start.s"
 srec = srecord.vsrecord(filename)
 data = "\x00\x00"
 print srec.S3(address, data)
 srec.save()
 _CleanUp.append(filename)
 return filename

#-----------------------------------------------------------------------------
#
# make end srecord files.
#
def makeEnd (address):
 filename = "_end.s"
 srec = srecord.vsrecord(filename)
 data = "\xAD\xDE"
 print srec.S3(address, data)
 srec.save()
 _CleanUp.append(filename)
 return filename

#-----------------------------------------------------------------------------
#
# make start srecord files.
#
number = 0
def makeTestImage (address, size, invert=False):
 global number
 filename = "_testImage_%d.s" % number
 number += 1
 srec = srecord.vsrecord(filename)
 addr = address
 data = ""
 for i in xrange(0, size/4):
  a = addr
  if invert: 
   a = a ^ 0xFFFFFFFF
 
  data += chr(a         & 0x000000FF)
  data += chr((a >> 8)  & 0x000000FF)
  data += chr((a >> 16) & 0x000000FF)
  data += chr((a >> 24) & 0x000000FF)
  addr += 4

 srec.loadFromString(data, startAddress=address, BytesInOneLine=16, type='S3')
 srec.save()
 _CleanUp.append(filename)
 return filename

#-----------------------------------------------------------------------------
#
# mmx2 component 
#
DEFS = {
        "PKGNAME" : "MMX2 API test flash image"
       }
ComponentName = "mmx2"
component = vComponent(tableDefs = DEFS, ComponentName = ComponentName)
options = {
#           "KeyFile"    : "avain.txt",
#           "KeyNo"      : 0,
           "SourceType" : "srec",
           "Size"       : 0,
           "Encrypt"    : "plain",
           "PREHOOK"    : "",
           "DEFS"       : [
                           ["PROTOCOL",     "MBOOT"        ],
                           ["RESETCOMMAND", "HMI"          ],
                           ["ROUTE",        "datalinklayer.1"]
                          ]
          }
component.addAsFrameFile(makeStart(AddressOfStartEndTag), "0:", options)
start = 0x00000
end   = 0x1FF
size = end-start+1 # size need to be multible of 4!
component.addAsFrameFile(makeTestImage(start, size, invert=True), "0:", options)

start = 0x18000
end   = 0x3FEFF
size = end-start+1 # size need to be multible of 4!
component.addAsFrameFile(makeTestImage(start, size), "0:", options)

start = 0x3FF00
end   = 0x3FFFF
size = end-start+1 # size need to be multible of 4!
component.addAsFrameFile(makeTestImage(start, size), "0:", options)
component.addAsFrameFile(makeEnd(AddressOfStartEndTag), "0:", options)


#------------------------------------------------------------------------------
#
# Make vcx.
#
#
sutFiles = [ # Vacon Loader is using these files.
            "./tools/sut/MbootLogic.dll", 
            "./tools/sut/ScriptCommandDefinitions.xml"
           ]

DEFS = {
        "PKGNAME" : "MMX2 API",
        "DATE"    : "%s" % (date),
        "AUTHOR"  : "Vacon Plc (%s)" % (os.environ['USERNAME'])
       }

vcx = vComponents(sutFiles = sutFiles, tableDefs = DEFS)
vcx.addComponent(component)
print "Building '%s'" % TargetFile
vcx.make(TargetFile)

CleanUp() # Comment this not to delete srecord files.


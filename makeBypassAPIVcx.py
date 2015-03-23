#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import time
import logging
import os.path
import posixpath
import tempfile
import shutil
import argparse

sys.path.append('tools/python')
import vcxTools
import logsupport
import srecord

# dateAndTime can be used for repeated builds where unique names are needed for directories.
#
dateAndTime = time.strftime("%Y-%m-%dT%H:%M:%S")

AddressOfStartEndTag  = 0x0003FFFE
AddressOfExtEepCrcTag = 0x0700

#------------------------------------------------------------------------------
# Default option values for VCX-packages, should be good enough for most products
BypassApiOptions = {"protocol"     : "MBOOT",
                     "resetCmd"     : "HMI",
                     "route"        : "datalinklayer.1",
                     "memArea"      : 0,
                     "size"         : 0,
                     "encrypt"      : "plain",
                     "sourceType"   : "srec",
                     "addressOffset": 0}

BypassOptions    = {"protocol"     : "MBOOT",
                     "resetCmd"     : "HMI",
                     "route"        : "datalinklayer",
                     "keyFile"      : "./tools/keys/Key_Mondeo_Debug.txt",
                     "keyNr"        : 0,
                     "memArea"      : 3,
                     "size"         : 1024,
                     "encrypt"      : "encrypt",
                     "sourceType"   : "bin",
                     "addressOffset": 0}
                    
#------------------------------------------------------------------------------
#
## Definitions for arguments passed to the program
def parsOptions():
  usage       = "usage: python %(prog)s.py [options]"
  description = "This is a python module that creates Bypass API vcx-package."

  parser = argparse.ArgumentParser(description=description, usage=usage)

  parser.add_argument("target", nargs="?", default = "debug", help = "target to build for")
  parser.add_argument("-d", action="store_true", dest = "debugging", default = False, help = "Shows debug info")

  args = parser.parse_args()

  return args

  
#-----------------------------------------------------------------------------
#
# make start srecord files.
#
def makeStart (address):
 filename = "_temp_start_for_xmega256.s"
 srec = srecord.vsrecord(filename)
 data = "\x00\x00"
 print srec.S3(address, data)
 srec.save()
 return filename

#-----------------------------------------------------------------------------
#
# make end srecord files.
#
def makeEnd (address):
 filename = "_temp_end_for_xmega256.s"
 srec = srecord.vsrecord(filename)
 data = "\xAD\xDE"
 print srec.S3(address, data)
 srec.save()
 return filename

#-----------------------------------------------------------------------------
#
# make ext. eeprom crc flag srecord files.
#
def makeExtEep (address):
 filename = "_exteep.s"
 srec = srecord.vsrecord(filename)
 data = "\xFF\xFF"
 print srec.S3(address, data)
 srec.save()
 return filename
  
  
#------------------------------------------------------------------------------
#
##
def createVcx(TargetFile, Sourcedir):
  """
  """
  targetFileH = vcxTools.CreateVCX(TargetFile, options=BypassApiOptions)
  targetFileH.addDef ("/", "PKGNAME", "BYPASS API")
  targetFileH.addDef ("/", "DATE", dateAndTime)
  targetFileH.addDef ("/", "AUTHOR", "Vacon Plc (%s)" % (os.environ['USERNAME']))

  targetFileH.addDef ("/api/", "PKGNAME", "BYPASS API")
  targetFileH.addRule("/api/", "F0", "GetBootID", min="18", max="18", action="-2", msg="Current Boot ID #RESULT#, expected 18.")
  targetFileH.addFile("/api/", makeStart(AddressOfStartEndTag))
  targetFileH.addFile("/api/", os.path.join(Sourcedir, "api_bypass.s"))
  targetFileH.addFile("/api/", makeExtEep(AddressOfExtEepCrcTag), targetPath="4:")
  targetFileH.addFile("/api/", makeEnd(AddressOfStartEndTag))
  
  targetFileH.close()
  
  return True
   
#------------------------------------------------------------------------------
#
##
if __name__ == "__main__":
  args = parsOptions()
  
  # Set up logging to console
  logsupport.initLogging(args.debugging)

  if args.target == "IDE":
    SourceDir = "../tools/Release/Exe/"
  else:
    SourceDir = "../out2/iar-avr/VB01129" + args.target

  TargetFile = os.path.abspath(os.path.join(SourceDir, "API_BYPASS.vcx"))
  
  createVcx(TargetFile, SourceDir)
  

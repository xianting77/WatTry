"""
 Make Memory headef for internal and external eeprom.

 More information can be found:
  - SDD0070 Device identification data structures

"""

import sys
sys.path.append('tools/python')

from vDeviceProperties import *
from vComponents import *
import srecord
import shutil

# ------------------------------

TargetFilename = "70CVB1129_MH.vcx"
SourceDir =  "."
SourceDir2 = "./xml"
TargetFile = os.path.join(SourceDir2, TargetFilename)

TargetFile = os.path.abspath(TargetFile)

#------------------------------------------------------------------------------
#
_CleanUp = []

def CleanUp ():
 for file in _CleanUp:
#  print "removing '%s'" % file
  if os.path.exists(file):
   os.remove(file)
# ------------------------------


FILL_CHAR = 0xFF
# ------------------------------
# Make binary image of atxmega256A internal eeprom memory.
#
# Memory header + one entry for device properties
#
def MakeMMX2Internal(filename="mmx2_internal.bin"):
 totalsize = 4096 
 entries = 1

 z = vDP(endian = "<") # "<" = little endian, ">" = big endian 
 z.MemorySize(totalsize)
 z.Version(1)

 # Memory header; one entry to Device properties.
 #
 datalen = totalsize - (10 + (entries * 4)) - (8+8)
 
 # add property header to start of data == End of list.
 data   = z.MakeProperty(0,1023,"") 
 data  += chr(FILL_CHAR) * (datalen - len(data))    # fill with FILL_CHAR
 
 # Make deviceProperty data == "root list" to contain data above.
 # 
 deviceProperty  = z.MakeProperty(0, 1021, data) + z.MakeProperty(0,1023,"")
    
 # add entry
 z.AddEntry(2, deviceProperty)  # Id 2 = Device properties structure (SDD0070)
 
 # save to file
 z.SaveImage(filename);
 _CleanUp.append(filename)
 return(filename)

# ------------------------------
# Make binary image of external eeprom memory.
#
# Structure
#  - memory header
#  - Application area
#  - API system sw area
#  - Power parameters area
#  - Powerdown area
#
def MakeMMX2External(filename="mmx2_external.bin"):
 totalsize  = 8192 
 entries    = 5

 # size after memory header
 size = totalsize - (10 + (entries * 4))

 ApplicationAreaSizeOffset = 0x0100   # 10 This can be changed. 
 SystemSoftwareAreaOffset  = 0x0700   # 12 This can be changed. 
 PowerParametersAreaOffset = 0x0B00   # 11 This can be changed. 
 PowerDownAreaOffset       = 0x1100   # 13
 SpecialFlagAreaOffset     = 0x1FF0   # this is just to reserve space at end of memory

 z = vDP(endian = "<") # "<" = little endian, ">" = big endian 
 z.MemorySize(totalsize)
 z.Version(1)

 # add entry
 z.AddEntryOffset(10, ApplicationAreaSizeOffset)
 z.AddEntryOffset(11, PowerParametersAreaOffset)
 z.AddEntryOffset(12, SystemSoftwareAreaOffset)
 z.AddEntryOffset(13, PowerDownAreaOffset)
 z.AddEntryOffset(14, SpecialFlagAreaOffset)

 z.SaveHeaderImage(filename)

 _CleanUp.append(filename)
 return(filename)
    

# ------------------------------
# Make binary image of memory.
#
def MakeEmptyMemory(filename="EmptyMemory.bin"):
 totalsize      = 8192 
 data  = chr(FILL_CHAR) * (totalsize)    # fill with FILL_CHAR

 f = open(filename,"wb")
 f.write(data)
 f.close()
 _CleanUp.append(filename)
 return(filename)

# ------------------------------
# convert binary image to srecord .
#
def ConvertBinToSrec(binName, srecName = "", startAddress=0x0, type='S3'):
 root, ext = os.path.splitext(binName)
 if srecName == "":
  srecName = root + ".s"
# print "Converting " + binName + "  -> "  + srecName
 srec = srecord.vsrecord(srecName)
 srec.loadFromBin(binName, startAddress=startAddress, type=type)
 srec.trim()
 srec.save()
 _CleanUp.append(srecName)
 return srecName

# ------------------------------
# Convert bin -> srecord (strip all 0xff filled lines) -> mboot frame file.
#
def ConvertBinToSrecToFrameFile (binFile, targetDir):
 tmp = vComponent(tableDefs = {}, ComponentName = "")
 srec = ConvertBinToSrec(binFile) 
 _CleanUp.append(srec)
# print "Converting bin -> srec -> strip (0xff) -> framefile"
 temp = tmp.makeFrameFile(srec, "", size = 64, encrypt="plain", sourceType="srec")
 target = targetDir
 shutil.copy(temp,target)


# ------------------------------
#
if __name__ == "__main__":
 
#------------------------------------------------------------------------------
#
 import datetime
 import time
 today = datetime.date.today().strftime("%Y%m%d")
 date  = time.strftime("%Y-%m-%dT%H:%M:%S")


 sutFiles = [
            "./tools/sut/MbootLogic.dll", 
            "./tools/sut/ScriptCommandDefinitions.xml"
           ]

#------------------------------------------------------------------------------
#
# Mondeo control eeprom memory header.
#
#
 DEFS = {
         "PKGNAME"      : "VB01129 Eeprom Memory Headers (internal).",

         "PROTOCOL"     : "MBOOT" ,
         "RESETCOMMAND" : "HMI",
         "ROUTE"        : "datalinklayer.1"
        }

 Name = "70CVB01129"
 Mmx2 = vComponent(tableDefs = DEFS, ComponentName = Name)

 options = {
           "SourceType" : "srec",
           "Size"       : 64,
           "Encrypt"    : "plain" ,

#           "ExecuteXml"        : ["file1","file2"],

          }


# external_bin  = MakeMMX2External("%s_e.bin" % Name)
# external_srec = ConvertBinToSrec(external_bin)
 internal_bin  = MakeMMX2Internal("%s_i.bin" % Name)
 internal_srec = ConvertBinToSrec(internal_bin)


# Mmx2.addAsFrameFile("%s" % external_srec, "4:", options)
 Mmx2.addAsFrameFile("%s" % internal_srec, "2:", options)  # == 255: 
 
 vcx = vComponents(sutFiles = sutFiles, tableDefs = DEFS)
 vcx.addComponent(Mmx2)

 print "\nBuilding '%s'\n" % TargetFile
 vcx.make(TargetFile, create = 1)

# ConvertBinToSrecToFrameFile(external_bin, SourceDir2)
 ConvertBinToSrecToFrameFile(internal_bin, SourceDir2)

 CleanUp()

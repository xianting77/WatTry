#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import time
import logging
import os.path
import posixpath
import tempfile
import shutil

from optparse import OptionParser

sys.path.append('tools/python')
import vcxTools
import logsupport

# dateAndTime can be used for repeated builds where unique names are needed for directories.
#
dateAndTime = time.strftime("%Y-%m-%dT%H:%M:%S")

#----------------------PATHS & FILES---------------------------------------------
#
TargetFile   = "./../tools/Release/Exe/FW0107BV.vcx"

PowerVCX    = "./../tools/power/Power.vcx"
MCAVCX      = "./../tools/mca/mca.vcx"
APIVCX      = "./../tools/Release/Exe/API_BYPASS.vcx"
APPVCX      = "./../tools/application/app.vcx"

MCA_BOOT_ID      = "90"
BYPASS_API_BOOT = "18"

FATAL_ERROR       = "-2"
NO_EFFECT         = "-1"
ERROR             = ""
ERROR_AND_ASK     = "1"
ERROR_AND_WARNING = "2"
ERROR_AND_INFO    = "3"

#------------------------------------------------------------------------------
# Default option values for VCX-packages, should be good enough for most products
Options          = {"protocol"     : "MBOOT",
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
## Definitions for arguments passed to the program
def parsOptions():
  usage       = "usage: python %prog "
  description = "Creates a big vcx-files..."
  parser = OptionParser(usage=usage, description=description)

  parser.add_option("-d", action="store_true", dest = "debugging", default = False, help = "Shows debug info")

  (options, args) = parser.parse_args()

  return (options, args)
                    
#------------------------------------------------------------------------------
#
##
def createVcx(targetFile):
  """
  """
  tmpDir  = tempfile.mkdtemp()

  targetFileH = vcxTools.CreateVCX(targetFile, options=Options, syntaxVer="6")
  targetFileH.addDef ("/", "PKGNAME", "BYPASS")
  targetFileH.addDef ("/", "DATE", dateAndTime)
  targetFileH.addDef ("/", "AUTHOR", "Vacon Plc (%s)" % (os.environ['USERNAME']))
  
  targetFileH.addRule("/", "M-1", "LOADERVER", "1.1.0.0", action="1", msg="This package requires Loader rev 1.1.0.0 or above")

  #----------------------------------------------------------------------------------------------------------
  targetFileH.addDir("checkDevice", selection="HIDDEN")
  targetFileH.addRule("checkDevice", "F0", "GetBootID", "", MCA_BOOT_ID,      MCA_BOOT_ID,      action=FATAL_ERROR, Or="1", msg="CheckDevice: Current Boot ID #RESULT#, expected MCA.")
  targetFileH.addRule("checkDevice", "F0", "GetBootID", "", BYPASS_API_BOOT, BYPASS_API_BOOT, action=FATAL_ERROR,         msg="CheckDevice: Current Boot ID #RESULT#, expected BYPASS API or MCA.")

  #----------------------------------------------------------------------------------------------------------
  targetFileH.copyTree(MCAVCX, "mca", "mca")
  targetFileH.removeDef("mca", "PKGNAME")
  targetFileH.addDef ("mca", "PKGNAME", "MCA Firmware")
  targetFileH.addRule("/", "M2", "GetBootID", "", MCA_BOOT_ID, MCA_BOOT_ID, action=ERROR_AND_INFO, msg="MCA: Current Boot ID #RESULT#, not loading MCA")
 
  #----------------------------------------------------------------------------------------------------------
  targetFileH.addDef ("power", "PKGNAME", "Power Firmware")
  targetFileH.addRule("power", "M1", "GetBootID", "", BYPASS_API_BOOT, BYPASS_API_BOOT, action=ERROR_AND_INFO, msg="Power: Current Boot ID #RESULT#, loading through MCA")
  targetFileH.addRule("power", "M2", "GetBootID", "", MCA_BOOT_ID,      MCA_BOOT_ID,      action=ERROR_AND_INFO, msg="Power: Current Boot ID #RESULT#, loading through door panel")
  targetFileH.addRule("power", "M3", "GetBootID", "", MCA_BOOT_ID,      MCA_BOOT_ID,      action=ERROR_AND_INFO, msg="Power: Current Boot ID #RESULT#, loading through door panel")

  targetFileH.copyTree(PowerVCX, "power", "power/door_panel")
  targetFileH.removeDef("power/door_panel", "PKGNAME")
  targetFileH.addDef ("power/door_panel", "PKGNAME", "Power Firmware through door panel")
  targetFileH.setComChan("power/door_panel", "1")

  targetFileH.setComChan("power/checkAPI", "1")
  targetFileH.addRule("power/checkAPI", "F1", "GetBootID", "", BYPASS_API_BOOT, BYPASS_API_BOOT, action=FATAL_ERROR, msg="Power CheckDevice: Current Boot ID #RESULT#, expected Bypass API behind MCA.")

  targetFileH.copyTree(PowerVCX, "power", "power/mca")
  targetFileH.removeDef("power/mca", "PKGNAME")
  targetFileH.addDef ("power/mca", "PKGNAME", "Power Firmware through MCA")
  targetFileH.setComChan("power/mca", "1.1")

  #----------------------------------------------------------------------------------------------------------
  targetFileH.addDef ("api", "PKGNAME", "Control Firmware")
  targetFileH.addRule("api", "M1", "GetBootID", "", BYPASS_API_BOOT, BYPASS_API_BOOT, action=ERROR_AND_INFO, msg="Control: Current Boot ID #RESULT#, loading through MCA")
  targetFileH.addRule("api", "M2", "GetBootID", "", MCA_BOOT_ID,      MCA_BOOT_ID,      action=ERROR_AND_INFO, msg="Control: Current Boot ID #RESULT#, loading through door panel")
  targetFileH.addRule("api", "M3", "GetBootID", "", MCA_BOOT_ID,      MCA_BOOT_ID,      action=ERROR_AND_INFO, msg="Control: Current Boot ID #RESULT#, loading through door panel")
  
  targetFileH.copyTree(APIVCX, "api", "api/door_panel")
  targetFileH.removeDef("api/door_panel", "PKGNAME")
  targetFileH.addDef ("api/door_panel", "PKGNAME", "Control Firmware through door panel")
  targetFileH.removeRule("api/door_panel", symbol="GetBootID")
  targetFileH.setComChan("api/door_panel", "")
  
  targetFileH.setComChan("api/checkAPI", "1")
  targetFileH.addRule("api/checkAPI", "F1", "GetBootID", "", BYPASS_API_BOOT, BYPASS_API_BOOT, action=FATAL_ERROR, msg="Control CheckDevice: Current Boot ID #RESULT#, expected Bypass API behind MCA.")
  
  targetFileH.copyTree(APIVCX, "api", "api/mca")
  targetFileH.removeDef("api/mca", "PKGNAME")
  targetFileH.addDef ("api/mca", "PKGNAME", "Control Firmware through MCA")
  targetFileH.removeRule("api/mca", symbol="GetBootID")
  
  #----------------------------------------------------------------------------------------------------------
  targetFileH.copyTree(APPVCX, "/", "api/door_panel/appl")
  targetFileH.removeDef("api/door_panel/appl", "PKGNAME")
  targetFileH.addDef ("api/door_panel/appl", "PKGNAME", "Applcation through door panel")
  targetFileH.setComChan("api/door_panel/appl", "")

  targetFileH.copyTree(APPVCX, "/", "api/mca/appl")
  targetFileH.removeDef("api/mca/appl", "PKGNAME")
  targetFileH.addDef ("api/mca/appl", "PKGNAME", "Application through MCA")
  
  for oneVLive in targetFileH.listVLive("api/door_panel/appl"):
    oneVLive.extract(tmpDir)
    targetFileH.addVLive("/", os.path.join(tmpDir, oneVLive.getFileName()), oneVLive.getT())
    
  for oneTextFile in ["100", "101", "102", "103"]:
    extraFileObj = targetFileH.listExtrafile(posixpath.join("api/door_panel/appl", "HELPTEXTS%s.VDB" % oneTextFile))
    extraFileObj.extract(tmpDir)
    targetFileH.addExtraFile("", posixpath.join(tmpDir, extraFileObj.getFileName()))
    extraFileObj = targetFileH.listExtrafile(posixpath.join("api/door_panel/appl", "TEXT%s.VDB" % oneTextFile))
    extraFileObj.extract(tmpDir)
    targetFileH.addExtraFile("", posixpath.join(tmpDir, extraFileObj.getFileName()))
      
  targetFileH.close()
  
  shutil.rmtree(tmpDir)

  return True
  
#------------------------------------------------------------------------------
#
##
if __name__ == "__main__":
  (options, args) = parsOptions()
  
  # Set up logging to console
  logsupport.initLogging(options.debugging)

  createVcx(TargetFile)
  

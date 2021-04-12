from __future__ import print_function
from __future__ import division
#
# dBackup Plugin by gutemine
#
dbackup_version = "2.8-r1"
#
from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.config import config, ConfigSubsection, ConfigText, ConfigBoolean, ConfigInteger, ConfigSelectionNumber, ConfigSelection, getConfigListEntry, ConfigSlider
from Components.ConfigList import ConfigListScreen
from Plugins.Plugin import PluginDescriptor
from Components.Pixmap import Pixmap
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Screens.InputBox import InputBox
from Components.Input import Input
from Screens.ChoiceBox import ChoiceBox
from Components.AVSwitch import AVSwitch
from Components.SystemInfo import SystemInfo
from Screens.Console import Console
from Components.MenuList import MenuList
from Components.Slider import Slider
from Components.Sources.Clock import Clock
from Components.Sources.StaticText import StaticText
from enigma import ePoint, eLCD, fbClass, eRCInput, eDBoxLCD, getDesktop, quitMainloop, eConsoleAppContainer, eDVBVolumecontrol, eTimer, eActionMap, eBackgroundFileEraser
from Tools.LoadPixmap import LoadPixmap
from shutil import rmtree as rmtree
import Screens.Standby
import sys
import struct
import stat
import time
from os import path as os_path, remove as os_remove, rename as os_rename, chmod as os_chmod, readlink as os_readlink, symlink as os_symlink, listdir as os_listdir, mkdir as os_mkdir, system as os_system, statvfs as os_statvfs
from twisted.web import resource, http
import gettext
import datetime
import shutil
import os
from glob import glob
for File in os_listdir("/usr/lib/enigma2/python/Plugins/Extensions"):
    file = File.lower()
    if file.find("panel") != -1 or file.find("feed") != -1 or file.find("unisia") != -1 or file.find("ersia") != -1 or file.find("olden") != -1 or file.find("venus") != -1:
        if os_path.exists("/var/lib/dpkg/info/enigma2-plugin-extensions-dbackup.md5sums"):
            rmtree("/usr/lib/enigma2/python/Plugins/Extensions/%s" % File, ignore_errors=True)

for File in os_listdir("/usr/lib/enigma2/python/Plugins/SystemPlugins"):
    file = File.lower()
    if file.find("panel") != -1 or file.find("feed") != -1 or file.find("unisia") != -1 or file.find("ersia") != -1 or file.find("olden") != -1 or file.find("venus") != -1:
        if os_path.exists("/var/lib/dpkg/info/enigma2-plugin-extensions-dbackup.md5sums"):
            rmtree("/usr/lib/enigma2/python/Plugins/SystemPlugins/%s" % File, ignore_errors=True)

dbackup_plugindir = "/usr/lib/enigma2/python/Plugins/Extensions/dBackup"
dbackup_busy = "/tmp/.dbackup"
dbackup_script = "/tmp/dbackup.sh"
dbackup_backup = "/tmp/.dbackup-result"
dbackup_log = "/tmp/dbackup.log"
dbackup_minpartsize = 1000  # minimum 1GB
dbackup_maxpartsize = 68000 # maximum 64GB
# backup progress bar factors
dbackup_tarxz = 2300
dbackup_targz = 1300
dbackup_tarbz2 = 1650
dbackup_tar = 500
# flashing progress bar factors
flashing_tarxz = 1550
flashing_targz = 650
flashing_tarbz2 = 825
flashing_tar = 250

global dreambox_data
dreambox_data = "none"

def getbylabel():
    global dreambox_data
    cmd = 'blkid -t LABEL=dreambox-data -o device'
    device = os.popen(cmd).read().replace('\n', '')
    if device == "":
        dreambox_data = "none"
        print("[dbackup} no dreambox-data found")
    else:
        print("[dbackup} dreambox-data found on device:", device)
        dreambox_data = device

getbylabel()

# add local language file
dbackup_sp = config.osd.language.value.split("_")
dbackup_language = dbackup_sp[0]
if os_path.exists("%s/locale/%s" % (dbackup_plugindir,dbackup_language)):
    _ = gettext.Catalog('dbackup', '%s/locale' % dbackup_plugindir,dbackup_sp).gettext

def getBoxtype():
    boxtype = "dm920"
    if os_path.exists("/proc/stb/info/model"):
        f = open("/proc/stb/info/model")
        boxtype = f.read()
        f.close()
        boxtype = boxtype.replace("\n","").replace("\l","")
    if boxtype == "dm525":
        boxtype = "dm520"
    if boxtype == "one":
        boxtype = "dreamone"
    if boxtype == "two":
        boxtype = "dreamtwo"
    return boxtype

def getPiconPath(name):
    if os_path.exists("/usr/share/enigma2/%s/skin_default/%s.svg" % (dbackup_skin,name)):
#               cprint("found %s.svg in skin ..." % name)
        return "/usr/share/enigma2/%s/skin_default/%s.svg" % (dbackup_skin,name)
    if os_path.exists("/usr/share/enigma2/%s/skin_default/%s.png" % (dbackup_skin,name)):
#               cprint("found %s.png in skin ..." % name)
        return "/usr/share/enigma2/%s/skin_default/%s.png" % (dbackup_skin,name)
    if os_path.exists("/usr/share/enigma2/%s/skin_default/icons/%s.png" % (dbackup_skin,name)):
#               cprint("found %s.png in skin ..." % name)
        return "/usr/share/enigma2/%s/skin_default/icons/%s.png" % (dbackup_skin,name)
    if os_path.exists("/usr/share/enigma2/%s/skin_default/icons/%s.svg" % (dbackup_skin,name)):
#               cprint("found %s.svg in skin ..." % name)
        return "/usr/share/enigma2/%s/skin_default/icons/%s.svg" % (dbackup_skin,name)
    if os_path.exists("/usr/share/enigma2/skin_default/%s.svg" % (name)):
#               cprint("found %s.svg in default skin ..." % name)
        return "/usr/share/enigma2/skin_default/%s.svg" % (name)
#       if os_path.exists("/usr/share/enigma2/skin_default/%s.png" % (name)):
#               cprint("found %s.png in default skin ..." % name)
#               return "/usr/share/enigma2/skin_default/%s.png" % (name)
    if os_path.exists("/usr/share/enigma2/skin_default/icons/%s.png" % (name)):
#               cprint("found %s.png in default skin ..." % name)
        return "/usr/share/enigma2/skin_default/icons/%s.png" % (name)
    if os_path.exists("/usr/share/enigma2/skin_default/buttons/key_%s.png" % (name)):
#               cprint("found %s.png in default skin ..." % name)
        return "/usr/share/enigma2/skin_default/buttons/key_%s.png" % (name)
#       cprint("[dBACKUP] found %s.png in default skin ..." % name)
    return "/usr/share/enigma2/skin_default/%s.png" % (name)

yes_no_descriptions = {False: _("no"), True: _("yes")}

config.plugins.dbackup = ConfigSubsection()
f = open("/proc/mounts", "r")
m = f.read()
f.close()
if m.find("/media/hdd") != -1:
    config.plugins.dbackup.backuplocation = ConfigText(default="/media/hdd/backup", fixed_size=True, visible_width=20)
else:
    config.plugins.dbackup.backuplocation = ConfigText(default="/autofs/sda1", fixed_size=True, visible_width=20)
config.plugins.dbackup.backupdeb = ConfigBoolean(default=False, descriptions=yes_no_descriptions)
#config.plugins.dbackup.backupimagetype = ConfigBoolean(default = True, descriptions=yes_no_descriptions)
config.plugins.dbackup.stopped = ConfigBoolean(default=False, descriptions=yes_no_descriptions)
config.plugins.dbackup.backupboxtype = ConfigBoolean(default=True, descriptions=yes_no_descriptions)
config.plugins.dbackup.backupdate = ConfigBoolean(default=True, descriptions=yes_no_descriptions)
config.plugins.dbackup.backuptime = ConfigBoolean(default=True, descriptions=yes_no_descriptions)
blanks_options = []
for blank in range(0,41):
    blanks_options.append((str(blank),str(blank)))
config.plugins.dbackup.backupblanks = ConfigSelection(default="10", choices=blanks_options)
config.plugins.dbackup.backupsettings = ConfigBoolean(default=False, descriptions=yes_no_descriptions)
config.plugins.dbackup.sig = ConfigBoolean(default=False, descriptions=yes_no_descriptions)
config.plugins.dbackup.loaderextract = ConfigBoolean(default=False, descriptions=yes_no_descriptions)
config.plugins.dbackup.loaderflash = ConfigBoolean(default=False, descriptions=yes_no_descriptions)
config.plugins.dbackup.kernelextract = ConfigBoolean(default=False, descriptions=yes_no_descriptions)
config.plugins.dbackup.sort = ConfigBoolean(default=True, descriptions=yes_no_descriptions)
config.plugins.dbackup.backupaskdir = ConfigBoolean(default=True, descriptions=yes_no_descriptions)
config.plugins.dbackup.delay = ConfigInteger(default=0, limits=(0,60))
automatic_options = []
automatic_options.append(("idle",_("Idle")))
automatic_options.append(("boot",_("Startup")))
automatic_options.append(("message",_("Message")))
config.plugins.dbackup.automatic = ConfigSelection(default="idle", choices=automatic_options)
config.plugins.dbackup.lastbackup = ConfigInteger(default=0, limits=(0,2000000000))
config.plugins.dbackup.cleanlastbackup = ConfigSelectionNumber(0, 100, 5, default=0)
days_options = []
days_options.append(("0",_("never")))
days_options.append(("8888",_("always")))
for days in range(1,31):
    days_options.append((str(days),str(days)))
config.plugins.dbackup.latestbackup = ConfigSelection(default="0", choices=days_options)

if os_path.exists("/var/lib/opkg/status"):
    config.plugins.dbackup.aptclean = ConfigBoolean(default=False, descriptions=yes_no_descriptions)
    config.plugins.dbackup.epgdb = ConfigBoolean(default=False, descriptions=yes_no_descriptions)
    config.plugins.dbackup.mediadb = ConfigBoolean(default=False, descriptions=yes_no_descriptions)
    config.plugins.dbackup.webinterface = ConfigBoolean(default=True, descriptions=yes_no_descriptions)
else:
    config.plugins.dbackup.aptclean = ConfigBoolean(default=False, descriptions=yes_no_descriptions)
    config.plugins.dbackup.epgdb = ConfigBoolean(default=False, descriptions=yes_no_descriptions)
    config.plugins.dbackup.mediadb = ConfigBoolean(default=False, descriptions=yes_no_descriptions)
    config.plugins.dbackup.webinterface = ConfigBoolean(default=False, descriptions=yes_no_descriptions)

config.plugins.dbackup.settings = ConfigBoolean(default=False, descriptions=yes_no_descriptions)
config.plugins.dbackup.timers = ConfigBoolean(default=False, descriptions=yes_no_descriptions)
config.plugins.dbackup.picons = ConfigBoolean(default=False, descriptions=yes_no_descriptions)
id_options = []
id_options.append(("deb",_("deb")))
id_options.append(("none",_("none")))
id_options.append(("exp",_("exp")))
id_options.append(("rel",_("rel")))
id_options.append(("user",_("User defined")))
config.plugins.dbackup.backupid = ConfigSelection(default="none", choices=id_options)
config.plugins.dbackup.backupuserid = ConfigText(default="deb                   ", fixed_size=True, visible_width=20)
display_options = []
display_options.append(("clock",_("Clock")))
display_options.append(("dbackup",_("dBackup")))
display_options.append(("dreambox",_("Dreambox")))
display_options.append(("mb",_("MB")))
display_options.append(("nothing",_("nothing")))
config.plugins.dbackup.displayentry = ConfigSelection(default="clock", choices=display_options)

config.plugins.dbackup.showinsettings = ConfigBoolean(default=False, descriptions=yes_no_descriptions)
config.plugins.dbackup.showinextensions = ConfigBoolean(default=False, descriptions=yes_no_descriptions)
config.plugins.dbackup.showinplugins = ConfigBoolean(default=True, descriptions=yes_no_descriptions)

dbackup_recovering = []
dbackup_recovering.append(("webif",_("Webinterface")))
dbackup_recovering.append(("factory",_("Factory reset")))
dbackup_recovering.append(("both",_("both")))
dbackup_recovering.append(("none",_("none")))
config.plugins.dbackup.recovering = ConfigSelection(default="both", choices=dbackup_recovering)

flashtools = []
flashtools.append(("direct", _("direct")))
flashtools.append(("rescue", _("Rescue Bios")))
#flashtools.append(( "recovery", _("USB Stick") ))
config.plugins.dbackup.flashtool = ConfigSelection(default="direct", choices=flashtools)
config.plugins.dbackup.console = ConfigBoolean(default=True, descriptions=yes_no_descriptions)

config.plugins.dbackup.transparency = ConfigSlider(default=0, increment=5, limits=(0,255))
config.plugins.dbackup.verbose = ConfigBoolean(default=False, descriptions=yes_no_descriptions)

backuptools = []
backuptools.append(("tar.xz", _("tar.xz")))
backuptools.append(("tar.gz", _("tar.gz")))
backuptools.append(("tar.bz2", _("tar.bz2")))
backuptools.append(("tar", _("tar")))
config.plugins.dbackup.backuptool = ConfigSelection(default="tar.xz", choices=backuptools)
gz_options = []
gz_options.append(("0","0"))
gz_options.append(("1","1"))
gz_options.append(("2","2"))
gz_options.append(("3","3"))
gz_options.append(("4","4"))
gz_options.append(("5","5"))
gz_options.append(("6","6"))
gz_options.append(("7","7"))
gz_options.append(("8","8"))
gz_options.append(("9","9"))
xz_options = []
xz_options.append(("0","0"))
xz_options.append(("1","1"))
xz_options.append(("2","2"))
xz_options.append(("3","3"))
xz_options.append(("4","4"))
xz_options.append(("5","5"))
xz_options.append(("6","6"))
# needs too much memory
#xz_options.append(( "7","7" ))
#xz_options.append(( "8","8" ))
#xz_options.append(( "9","9" ))

boxtype = getBoxtype()
if boxtype == "dm520" or boxtype == "dm820" or boxtype == "dm7080":
    config.plugins.dbackup.xzcompression = ConfigSelection(default="0", choices=xz_options)
    config.plugins.dbackup.gzcompression = ConfigSelection(default="2", choices=gz_options)
else:
    config.plugins.dbackup.xzcompression = ConfigSelection(default="6", choices=xz_options)
    config.plugins.dbackup.gzcompression = ConfigSelection(default="6", choices=gz_options)
s_options = []
s_options.append(("0",_("none")))
s_options.append(("1","1"))
s_options.append(("2","2"))
s_options.append(("3","3"))
s_options.append(("4","4"))
s_options.append(("5","5"))
s_options.append(("6","6"))
s_options.append(("7","7"))
s_options.append(("8","8"))
s_options.append(("10","10"))
config.plugins.dbackup.fadetime = ConfigSelection(default="5", choices=s_options)
config.plugins.dbackup.overwrite = ConfigBoolean(default=False, descriptions=yes_no_descriptions)

exectools = []
exectools.append(("daemon", _("daemon")))
exectools.append(("system", _("system")))
exectools.append(("container", _("container")))
config.plugins.dbackup.exectool = ConfigSelection(default="system", choices=exectools)

fileupload_string = _("Select tar.*z image for flashing")
disclaimer_header = _("Disclaimer")
info_header = _("Info")
disclaimer_string = _("This way of flashing your Dreambox is not supported by DMM.\n\nYou are using it completely at you own risk!\nIf you want to flash your Dreambox safely use the Recovery Webinterface!\n\nMay the Power button be with you!")
disclaimer_wstring = disclaimer_string.replace("\n","<br>")
plugin_string = _("Dreambox Backup Plugin by gutemine Version %s") % dbackup_version
flashing_string = _("Flashing")
backup_string = _("Backup")
setup_string = _("Configuring")
# currently disabled
#checking_string=_("Checking")
checking_string = _(" ")
running_string = _("dBackup is busy ...")
backupimage_string = _("Enter Backup Imagename")
backupdirectory_string = _("Enter Backup Path")
unsupported_string = _("Sorry, currently not supported on this Dreambox type")
notar_string = _("Sorry, no correct tar.*z file selected")
noxz_string = _("Sorry, no xz binary found")
noboxtype_string = _("Sorry, no %s image") % boxtype
refresh_string = _("Refresh")
mounted_string = _("Nothing mounted at %s")
barryallen_string = _("Sorry, use Barry Allen for Backup")
lowfat_string = _("Sorry, use LowFAT for Backup")
noflashing_string = _("Sorry, Flashing works only in Flash")
nowebif_string = _("Sorry, dBackup webinterface is currently disabled")
support_string = _("Kit & Support of this Plugin at www.oozoon-board.de")

dbackup_skin = config.skin.primary_skin.value.replace("/skin.xml","")

header_string = ""
header_string += "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.01 Transitional//EN\""
header_string += "\"http://www.w3.org/TR/html4/loose.dtd\">"
header_string += "<head><title>%s</title>" % plugin_string
header_string += "<link rel=\"shortcut icon\" type=\"/web-data/image/x-icon\" href=\"/web-data/img/favicon.ico\">"
header_string += "<meta content=\"text/html; charset=UTF-8\" http-equiv=\"content-type\">"
header_string += "</head><body bgcolor=\"black\">"
header_string += "<font face=\"Tahoma, Arial, Helvetica\" color=\"yellow\">"
header_string += "<font size=\"3\" color=\"yellow\">"

dbackup_backbutton = _("use back button in browser and try again!")
dbackup_flashing = ""
dbackup_flashing += header_string
dbackup_flashing += "<br>%s ...<br><br>" % flashing_string
dbackup_flashing += "<br><img src=\"/web-data/img/dbackup.png\" alt=\"%s ...\"/><br><br>" % (flashing_string)

dbackup_backuping = ""
dbackup_backuping += header_string
dbackup_backuping += "<br>%s<br><br>" % running_string
dbackup_backuping += "<br><img src=\"/web-data/img/ring.png\" alt=\"%s ...\"/><br><br>" % (backup_string)
dbackup_backuping += "<br><form method=\"GET\">"
dbackup_backuping += "<input name=\"command\" type=\"submit\" size=\"100px\" title=\"%s\" value=\"%s\">" % (refresh_string,"Refresh")
dbackup_backuping += "</form>"

global dbackup_progress
dbackup_progress = 0
YELLOWC = '\033[33m'
ENDC = '\033[m'

def cprint(text):
    print(YELLOWC + "[dBACKUP] " + text + ENDC)

sz_w = getDesktop(0).size().width()

class dBackupSummary(Screen):
    skin = (
    """<screen name="dBackupSummary" position="0,0" size="132,64" id="1">
            <widget font="Display;12" halign="center" position="6,0" render="Label" size="120,12" source="titletext" valign="center"/>
            <widget font="Display;12" halign="center" position="6,13" render="Label" size="120,12" source="duration" valign="center" />
            <widget name="slider" position="6,26" size="120,8" borderWidth="1"   borderColor="white" foregoundColor="white" transparent="1"/>
            <widget font="Display;26" halign="center" position="6,35" render="Label" size="120,28" source="displayentry" foregroundColor="white" valign="center"/>
    </screen>""",
    """<screen name="dBackupSummary" position="0,0" size="96,64" id="2">
            <widget font="Display;15" halign="center" position="0,0" render="Label" size="96,30" source="titletext" transparent="1" valign="center" />
            <widget backgroundColor="dark" borderWidth="1" position="0,34" size="96,8" name="slider" transparent="1" />
            <widget font="Display;15" halign="center" position="0,46" render="Label" size="96,15" source="duration" transparent="1" valign="center" foregroundColor="yellow" />
    </screen>""",
    """<screen name="dBackupSummary" position="0,0" size="400,240" id="3">
            <ePixmap pixmap="skin_default/display_bg.png" position="0,0" size="400,240" zPosition="-1" />
            <widget font="Display;48" halign="center" position="center,5" render="Label" size="380,100" source="titletext" transparent="1" valign="top" />
            <widget font="Display;48" halign="center" position="center,60" render="Label" size="100,50" source="duration" transparent="1" valign="center" foregroundColor="yellow" />
            <widget backgroundColor="dark" borderWidth="1" pixmap="skin_default/progress.png" position="center,112" size="380,15" name="slider" transparent="1" />
            <widget font="Display;72" halign="center" position="center,140" render="Label" size="380,84" source="displayentry" transparent="1" foregroundColor="white" valign="center" />
            </screen>""",
    """<screen name="dBackupSummary" position="0,0" size="240,86" id="100">
            <widget font="Display;14" halign="center" position="12,0" render="Label" size="220,24" source="titletext" valign="center"/>
            <widget font="Display;14" halign="center" position="12,16" render="Label" size="220,24" source="duration" valign="center" />
            <widget name="slider" position="12,36" size="220,10" borderWidth="1"   borderColor="white" foregoundColor="white" transparent="1"/>
            <widget font="Display;28" halign="center" position="12,48" render="Label" size="220,32" source="displayentry" foregroundColor="white" valign="center"/>
    </screen>""")

    def __init__(self, session, parent):
        Screen.__init__(self, session, parent=parent)
        self.slider = Slider(0, 500)
        self["slider"] = self.slider
        self["slider"].hide()
        self.clock = Clock()
        self.boxtype = getBoxtype()
        if os_path.exists("/var/lib/opkg/status"):
            if config.plugins.dbackup.displayentry.value == "clock":
                self["displayentry"] = StaticText(time.strftime('%H:%M', time.localtime(self.clock.time)))
            elif config.plugins.dbackup.displayentry.value == "dbackup":
                self["displayentry"] = StaticText(_("dBackup"))
            elif config.plugins.dbackup.displayentry.value == "dreambox":
                self["displayentry"] = StaticText(self.boxtype)
            else:
                self["displayentry"] = StaticText(" ")
            self["titletext"] = StaticText(backup_string + " & " + flashing_string)
        self["duration"] = StaticText(" ")
        self.onLayoutFinish.append(self.byLayoutEnd)

    def byLayoutEnd(self):
        self.slider.setValue(0)
        self.ClockTimer = eTimer()
        if not os_path.exists("/var/lib/opkg/status"):
            self.ClockTimer_conn = self.ClockTimer.timeout.connect(self.updateClock)
        else:
            self.ClockTimer.callback.append(self.updateClock)
        if os_path.exists("/var/lib/opkg/status"):
            if config.plugins.dbackup.displayentry.value == "clock":
                self.ClockTimer.start(1000, True)

    def updateClock(self):
        if config.plugins.dbackup.displayentry.value == "clock":
            self["displayentry"].setText(time.strftime('%H:%M', time.localtime(self.clock.time)))
            self.ClockTimer.start(1000, True)
        else:
            self.ClockTimer.stop()

class dBackup(Screen):
    if sz_w == 1920:
        skin = """
        <screen name="dBackup" position="center,170" size="1200,110" title="Flashing" >
        <widget name="logo" position="20,10" size="150,60" />
        <widget backgroundColor="#9f1313" font="Regular;30" halign="center" name="buttonred" position="180,10" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2" size="225,60" valign="center" />
        <widget backgroundColor="#1f771f" font="Regular;30" halign="center" name="buttongreen" position="425,10" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2" size="225,60" valign="center" />
        <widget backgroundColor="#a08500" font="Regular;30" halign="center" name="buttonyellow" position="660,10" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2" size="225,60" valign="center" />
        <widget backgroundColor="#18188b" font="Regular;30" halign="center" name="buttonblue" position="895,10" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2" size="225,60" valign="center" />
        <widget name="info" position="1125,10" size="60,30" alphatest="on" />
        <widget name="menu" position="1125,40" size="60,30" alphatest="on" />
        <eLabel backgroundColor="grey" position="10,80" size="1180,1" />
        <widget name="slider" position="10,90" size="1110,10"/>
        <widget source="duration" render="Label" size="70,45" position="1118,73" font="Regular;24" halign="center" valign="center" />
        </screen>"""
    else:
        skin = """
        <screen name="dBackup" position="center,120" size="800,70" title="Flashing" >
        <widget name="logo" position="10,5" size="100,40" />
        <widget backgroundColor="#9f1313" font="Regular;19" halign="center" name="buttonred" position="120,5" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2" size="150,40" valign="center" />
        <widget backgroundColor="#1f771f" font="Regular;19" halign="center" name="buttongreen" position="280,5" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2" size="150,40" valign="center" />
        <widget backgroundColor="#a08500" font="Regular;19" halign="center" name="buttonyellow" position="440,5" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2" size="150,40" valign="center" />
        <widget backgroundColor="#18188b" font="Regular;19" halign="center" name="buttonblue" position="600,5" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2" size="150,40" valign="center" />
        <widget name="info" position="755,5" size="40,20" alphatest="on" />
        <widget name="menu" position="755,25" size="40,20" alphatest="on" />
        <eLabel backgroundColor="grey" position="5,50" size="790,1" />
        <widget name="slider" position="5,55" size="745,5"/>
        <widget source="duration" render="Label" size="45,30" position="753,50" font="Regular;18" halign="center" valign="center" />
        </screen>"""

    def __init__(self, session, args=0):
        Screen.__init__(self, session)
        self.boxtype = getBoxtype()
        self.onShown.append(self.setWindowTitle)
        self.onLayoutFinish.append(self.byLayoutEnd)
        self["logo"] = Pixmap()
        self["buttonred"] = Label(_("Exit"))
        self["buttongreen"] = Label(_("Backup"))
        self["buttonyellow"] = Label(_("Flashing"))
        self["buttonblue"] = Label(_("Delete"))
        self["menu"] = Pixmap()
        self["info"] = Pixmap()
        self.slider = Slider(0, 500)
        self["slider"] = self.slider
        self["duration"] = StaticText(" ")

        self.dimmed = config.osd.alpha.value
        self.onShow.append(self.connectHighPrioAction)
        self.onHide.append(self.disconnectHighPrioAction)
        if config.plugins.dbackup.flashtool.value == "rescue":
            config.plugins.dbackup.backuplocation.value = "/data/.recovery"
            config.plugins.dbackup.backuptool.value = "tar.gz"
            config.plugins.dbackup.backuplocation.save()
            config.plugins.dbackup.backuptool.save()
        elif config.plugins.dbackup.flashtool.value == "recovery":
            config.plugins.dbackup.backuplocation.value = "/media/DREAMFLASH"
            config.plugins.dbackup.backuptool.value = "tar.xz"
            config.plugins.dbackup.backuplocation.save()
            config.plugins.dbackup.backuptool.save()

        self["setupActions"] = ActionMap(["ColorActions", "SetupActions", "TextEntryActions", "ChannelSelectEPGActions", "ChannelSelectEditActions"],
                {
                "green": self.backup,
                "red": self.leaving,
                "blue": self.deleting,
                "yellow": self.flash,
                "save": self.leaving,
                "deleteForward": self.deleting,
                "deleteBackward": self.deleting,
                "contextMenu": self.config,
                "showEPGList": self.lastbackup,
                "cancel": self.leaving,
                })

    def createSummary(self):
        if os_path.exists("/var/lib/opkg/status"):
            return dBackupSummary

    def installBinaries(self, tar="", xz="", pigz=""):
        self.container = eConsoleAppContainer()
        if os_path.exists("/var/lib/opkg/status"):
            self.container_appClosed_conn = self.container.appClosed.connect(self.installFinished)
            cmd = "apt-get update; apt-get install -f -y --force-yes %s %s %s; apt-get -f -y install --force-yes" % (tar, xz, pigz)
        else:
            self.container.appClosed.append(self.installFinished)
            cmd = "opkg update; opkg install --force-reinstall %s %s %s" % (tar, xz, pigz)
        cprint("cmd: %s" % cmd)
        self.container.execute(cmd)

    def installFinished(self,status):
        cprint("%s %s" % (self.text,status))
        if len(self.text):
            message = _("Installation finished.").replace(".",": ")
            message += self.text
            cprint("%s" % message)
            self.session.open(MessageBox, message, MessageBox.TYPE_INFO, timeout=5)

    def connectHighPrioAction(self):
        self.highPrioActionSlot = eActionMap.getInstance().bindAction('', -0x7FFFFFFF, self.doUnhide)

    def disconnectHighPrioAction(self):
        self.highPrioAction = None

    def setWindowTitle(self):
        if os_path.exists(dbackup_busy):
            self["logo"].instance.setPixmapFromFile("%s/ring.png" % dbackup_plugindir)
        else:
            self["logo"].instance.setPixmapFromFile("%s/dbackup.png" % dbackup_plugindir)
        self["menu"].instance.setPixmapFromFile(getPiconPath("menu"))
        self["info"].instance.setPixmapFromFile(getPiconPath("info"))
        self.setTitle(backup_string + " & " + flashing_string + " V%s" % (dbackup_version + " " + self.boxtype))
        if os_path.exists("/var/lib/opkg/status"):
            self.session.summary["titletext"].setText(backup_string + " & " + flashing_string)

            #update displayentry
            #cprint("=== onShow MainScreen")
            if config.plugins.dbackup.displayentry.value == "clock":
                self.session.summary["displayentry"].setText(time.strftime('%H:%M', time.localtime(self.session.summary.clock.time)))
                self.session.summary.ClockTimer.start(1000, True)
            if config.plugins.dbackup.displayentry.value == "dbackup":
                self.session.summary["displayentry"].setText(_("dBackup"))
            elif config.plugins.dbackup.displayentry.value == "nothing":
                self.session.summary["displayentry"].setText(" ")
            elif config.plugins.dbackup.displayentry.value == "dreambox":
                self.session.summary["displayentry"].setText(self.boxtype)
            elif config.plugins.dbackup.displayentry.value == "mb":
                if not os_path.exists(dbackup_busy):
                    self.session.summary["displayentry"].setText(" ")
            else:
                pass

        return
        # check for xz and pigz binary
        if os_path.exists("/var/lib/opkg/status"):
            f = open("/var/lib/opkg/status","r")
        else:
            f = open("/var/lib/opkg/status","r")
        sw = f.read()
        f.close()
        text = ""
        tar = ""
        xz = ""
        pigz = ""
        if os_path.exists("/var/lib/opkg/status"):
            if sw.find("Package: tar\n") == -1:
                tar = "tar"
                text += " " + tar + " "
        if sw.find("Package: xz\n") == -1 or not os_path.exists("/usr/bin/xz"):
            xz = "xz"
            text += " " + xz + " "
        if sw.find("Package: pigz\n") == -1 or not os_path.exists("/bin/pigz"):
            pigz = "pigz"
            text += " " + pigz + " "
        if tar == "tar" or xz == "xz" or pigz == "pigz":
            self.text = text
            self.installBinaries(tar,xz,pigz)

    def byLayoutEnd(self):
        self["logo"].instance.setPixmapFromFile("%s/dbackup.png" % dbackup_plugindir)
        self.slider.setValue(0)

    def leaving(self):
        if os_path.exists(dbackup_busy):
#                       os_remove(dbackup_busy)
            self.session.openWithCallback(self.forcedexit,MessageBox, running_string, MessageBox.TYPE_WARNING)
        else:
            self.forcedexit(1)

    def lastbackup(self):
        if int(config.plugins.dbackup.lastbackup.value) > 0:
            timestr = time.strftime('%Y-%m-%d %H:%M', time.localtime(int(config.plugins.dbackup.lastbackup.value)))
            text = _("Last Backup") + ": " + timestr
            if int(config.plugins.dbackup.latestbackup.value) > 0:
                timestr = time.strftime('%Y-%m-%d %H:%M', time.localtime(int(config.plugins.dbackup.lastbackup.value) + (int(config.plugins.dbackup.latestbackup.value) * 3600 * 24)))
                autoBackupType = [x for x in automatic_options if config.plugins.dbackup.automatic.value == x[0]][0][1]
                text += "\n\n" + _("Next Backup") + ": " + timestr + " (" + str(autoBackupType) + ")"
            self.session.openWithCallback(self.logging,MessageBox, text, MessageBox.TYPE_INFO)
        else:
            text = _("Last Backup") + " " + _("not found")
            self.session.openWithCallback(self.logging,MessageBox, text, MessageBox.TYPE_WARNING)

    def logging(self, status):
        if os_path.exists(dbackup_log):
            cmd = "cat %s; rm %s" % (dbackup_log,dbackup_log)
            self.session.open(Console,dbackup_log,[cmd])

    def deleting(self):
        self.session.openWithCallback(self.askForDelete,ChoiceBox,_("select Image for deleting"), self.getImageList())

    def askForDelete(self,source):
        if source is None:
            return
        else:
            self.delimage = source[1].rstrip()
            self.session.openWithCallback(self.ImageDelete,MessageBox,_("deleting %s ?") % (self.delimage),MessageBox.TYPE_YESNO)

    def ImageDelete(self,answer):
        if answer is None:
            return
        if answer is False:
            return
        else:
            cprint("DELETING %s" % self.delimage)
            os_remove(self.delimage)

    def forcedexit(self,status):
        if status > 0:
            self.doUnhide(0, 0)
            self.close()

    def checking(self):
        self.session.open(dBackupChecking)

    def doHide(self):
        if int(config.plugins.dbackup.fadetime.value) == 0:
            return
        if config.plugins.dbackup.transparency.value < config.osd.alpha.value:
            cprint("hiding")
            self.dimmed = config.osd.alpha.value
            delta = (int(config.osd.alpha.value) - int(config.plugins.dbackup.transparency.value)) / 5
            self.step = int(1000 * int(config.plugins.dbackup.fadetime.value) // delta)
            cprint("doHide delta transparency %d step time %d" % (delta, self.step))
            self.DimmingTimer = eTimer()
            if not os_path.exists("/var/lib/opkg/status"):
                self.DimmingTimer_conn = self.DimmingTimer.timeout.connect(self.doDimming)
            else:
                self.DimmingTimer.callback.append(self.doDimming)
            self.DimmingTimer.start(self.step, True)
        else:
            cprint("no hiding")

    def doDimming(self):
        self.DimmingTimer.stop()
        if fbClass.getInstance().islocked(): # Flashing !!!
            self.doUnhide(0, 0)
        else:
            if self.dimmed > 5:
                self.dimmed = self.dimmed - 5
            else:
                self.dimmed = 0
#                       print(self.dimmed)
            if os_path.exists("/proc/stb/video/alpha"):
                f = open("/proc/stb/video/alpha","w")
            else: # dreamone, dreamtwo
                f = open("/sys/devices/platform/meson-fb/graphics/fb0/osd_plane_alpha","w")
            f.write("%i" % self.dimmed)
            f.close()

            # continue dimming ?
            if self.dimmed > config.plugins.dbackup.transparency.value:
                self.DimmingTimer.start(self.step, True)
            else:
                # do final choosen transparency
                if os_path.exists("/proc/stb/video/alpha"):
                    f = open("/proc/stb/video/alpha","w")
                else: # dreamone, dreamtwo
                    f = open("/sys/devices/platform/meson-fb/graphics/fb0/osd_plane_alpha","w")
                f.write("%i" % config.plugins.dbackup.transparency.value)
                f.close()

    def doUnhide(self, key, flag):
        if fbClass.getInstance().islocked(): # Flashing !!!
            cprint("FLASHING LOCKED")
            return
        cprint("unhiding")
        if config.plugins.dbackup.transparency.value < config.osd.alpha.value:
            # reset needed
            if os_path.exists("/proc/stb/video/alpha"):
                f = open("/proc/stb/video/alpha","w")
            else: # dreamone, dreamtwo
                f = open("/sys/devices/platform/meson-fb/graphics/fb0/osd_plane_alpha","w")
            f.write("%i" % (config.osd.alpha.value))
            f.close()
            if os_path.exists(dbackup_busy):
                self.doHide()
        else:
            cprint("no unhiding")
        return 0

    def flash(self):
        k = open("/proc/cmdline","r")
        cmd = k.read()
        k.close()
        if self.boxtype == "dm520":
            if cmd.find("root=/dev/sda1") != -1: # Thanks Mr. Big
                rootfs = "root=/dev/sda1"
            else:
                rootfs = "root=ubi0:dreambox-rootfs"
        else:
            rootfs = "root=/dev/mmcblk0"
        if os_path.exists(dbackup_busy):
            self.session.open(MessageBox, running_string, MessageBox.TYPE_ERROR)
        elif os_path.exists("/.bainfo"):
            self.session.open(MessageBox, noflashing_string, MessageBox.TYPE_ERROR)
        elif os_path.exists("/.lfinfo"):
            self.session.open(MessageBox, noflashing_string, MessageBox.TYPE_ERROR)
        elif cmd.find(rootfs) == -1:
            self.session.open(MessageBox, noflashing_string, MessageBox.TYPE_ERROR)
        else:
            if config.plugins.dbackup.flashtool.value != "rescue":
                self.session.openWithCallback(self.askForImage,ChoiceBox,fileupload_string,self.getImageList(True))
            else:
                cprint("boots rescue mode ...")
                self.nfifile = "recovery"
                self.session.openWithCallback(self.doFlash, MessageBox, _("Press OK now for flashing\n\n%s\n\nBox will reboot automatically when finished!") % self.nfifile, MessageBox.TYPE_INFO)

    def askForImage(self,image):
        if image is None:
            self.session.open(MessageBox, notar_string, MessageBox.TYPE_ERROR)
        else:
            cprint("flashing ...")
            self.nfiname = image[0]
            self.nfifile = image[1]
            self.nfidirectory = self.nfifile.replace(self.nfiname,"")
            if self.nfifile != "rescue" and self.nfifile != "recovery" and self.nfiname.find(self.boxtype) == -1:
                self.session.open(MessageBox, noboxtype_string, MessageBox.TYPE_ERROR)
            else:
                if os_path.exists(dbackup_busy):
                    os_remove(dbackup_busy)
                if self.nfifile.endswith("tar.xz") and not os_path.exists("/usr/bin/xz"):
                    self.session.open(MessageBox, noxz_string, MessageBox.TYPE_ERROR)
                else:
                    self.session.openWithCallback(self.startFlash,MessageBox,_("Are you sure that you want to flash now %s ?") % (self.nfifile), MessageBox.TYPE_YESNO)

    def getImageList(self, flash=False):
        liststart = []
        list = []
        liststart.append((_("Recovery Image from Feed"), "recovery"))
        if os_path.exists("/usr/sbin/update-rescue"):
            liststart.append((_("Rescue Bios from Feed"), "rescue"))
        for name in os_listdir("/tmp"):
            if (name.endswith(".tar.gz") or name.endswith(".tar.xz") or name.endswith(".tar.bz2") or name.endswith(".tar") or name.endswith(".zip")) and not name.startswith("enigma2settings") and not name.endswith("enigma2settingsbackup.tar.gz"):
                name2 = name.replace(".tar.gz","").replace(".tar.xz","").replace(".tar.bz2","").replace(".tar","").replace(".zip","")
                if list.count(name2) < 1 and name2.find(self.boxtype) != -1:
                    list.append((name2, "/tmp/%s" % name))
                else:
                    cprint("skips %s" % name2)
        if os_path.exists(config.plugins.dbackup.backuplocation.value):
            for name in os_listdir(config.plugins.dbackup.backuplocation.value):
                if (name.endswith(".tar.gz") or name.endswith(".tar.xz") or name.endswith(".tar.bz2") or name.endswith(".tar") or name.endswith(".zip")) and not name.startswith("enigma2settings") and not name.endswith("enigma2settingsbackup.tar.gz"):
                    name2 = name.replace(".tar.gz","").replace(".tar.xz","").replace(".tar.bz2","").replace(".tar","").replace(".zip","")
                    if list.count(name2) < 1 and name2.find(self.boxtype) != -1:
                        list.append((name2, "%s/%s" % (config.plugins.dbackup.backuplocation.value,name)))
                    else:
                        cprint("skips %s" % name2)
        f = open("/proc/mounts", "r")
        m = f.read()
        f.close()
        if m.find("/data") != -1:
            if os_path.exists("/data/.recovery") and "/data/.recovery" != config.plugins.dbackup.backuplocation.value:
                for name in os_listdir("/data/.recovery"):
                    if (name.endswith(".tar.gz") or name.endswith(".tar.xz") or name.endswith(".tar.bz2") or name.endswith(".tar") or name.endswith(".zip")) and not name.startswith("enigma2settings") and not name.endswith("enigma2settingsbackup.tar.gz") and not name.startswith("settings"):
                        name2 = name.replace(".tar.gz","").replace(".tar.xz","").replace(".tar.bz2","").replace(".tar","").replace(".zip","")
                        if list.count(name2) < 1 and name2.find(self.boxtype) != -1:
                            list.append((name2, "/data/.recovery/%s" % (name)))
                        else:
                            cprint("skips %s" % name2)
            if os_path.exists("/data/backup") and "/data/backup" != config.plugins.dbackup.backuplocation.value:
                for name in os_listdir("/data/backup"):
                    if (name.endswith(".tar.gz") or name.endswith(".tar.xz") or name.endswith(".tar.bz2") or name.endswith(".tar") or name.endswith(".zip")) and not name.startswith("enigma2settings") and not name.endswith("enigma2settingsbackup.tar.gz"):
                        name2 = name.replace(".tar.gz","").replace(".tar.xz","").replace(".tar.bz2","").replace(".tar","").replace(".zip","")
                        if list.count(name2) < 1 and name2.find(self.boxtype) != -1:
                            list.append((name2, "/data/backup/%s" % (name)))
                        else:
                            cprint("skips %s" % name2)
        for directory in os_listdir("/media"):
            if os_path.exists("/media/%s/backup" % directory) and os_path.isdir("/media/%s/backup" % directory) and not directory.endswith("net") and not directory.endswith("hdd") and "/media/%s/backup" % directory != config.plugins.dbackup.backuplocation.value:
                try:
                    for name in os_listdir("/media/%s/backup" % directory):
                        if (name.endswith(".tar.gz") or name.endswith(".tar.xz") or name.endswith(".tar.bz2") or name.endswith(".tar") or name.endswith(".zip")) and not name.startswith("enigma2settings") and not name.endswith("enigma2settingsbackup.tar.gz"):
                            name2 = name.replace(".tar.gz","").replace(".tar.xz","").replace(".tar.bz2","").replace(".tar","").replace(".zip","")
                            if list.count(name2) < 1 and name2.find(self.boxtype) != -1:
                                list.append((name2, "/media/%s/backup/%s" % (directory,name)))
                            else:
                                cprint("skips %s" % name2)
                except:
                    pass
        if os_path.exists("/autofs"):
            for directory in os_listdir("/autofs"):
                if os_path.exists("/autofs/%s/backup" % directory) and os_path.isdir("/autofs/%s/backup" % directory) and "/autofs/%s/backup" % directory != config.plugins.dbackup.backuplocation.value:
                    try:
                        for name in os_listdir("/media/%s/backup" % directory):
                            if (name.endswith(".tar.gz") or name.endswith(".tar.xz") or name.endswith(".tar.bz2") or name.endswith(".tar") or name.endswith(".zip")) and not name.startswith("enigma2settings") and not name.endswith("enigma2settingsbackup.tar.gz"):
                                name2 = name.replace(".tar.gz","").replace(".tar.xz","").replace(".tar.bz2","").replace(".tar","").replace(".zip","")
                                if list.count(name2) < 1 and name2.find(self.boxtype) != -1:
                                    list.append((name2, "/autofs/%s/backup/%s" % (directory,name)))
                                else:
                                    cprint("skips %s" % name2)
                    except:
                        pass
        if config.plugins.dbackup.sort.value:
            list.sort()
        if flash:
            # recovery image and rescue bios is always first ...
            liststart = liststart + list
        else:
            liststart = list
        return liststart

    def startFlash(self,option):
        if option:
            if self.nfifile == "rescue":
                message = _("Press OK now for flashing\n\n%s") % self.nfifile
            else:
                message = _("Press OK now for flashing\n\n%s\n\nBox will reboot automatically when finished!") % self.nfifile
            self.session.openWithCallback(self.doFlash, MessageBox, message, MessageBox.TYPE_INFO)
        else:
            self.session.open(MessageBox, _("Sorry, Flashing of %s was canceled!") % self.nfifile, MessageBox.TYPE_ERROR)

    def getDeviceList(self):
        found = False
        f = open("/proc/partitions","r")
        devlist = []
        line = f.readline()
        line = f.readline()
        sp = []
        while (line):
            line = f.readline()
            if line.find("sd") != -1:
                sp = line.split()
            #       print(sp)
                devsize = int(sp[2])
                mbsize = devsize / 1024
                devname = "/dev/%s" % sp[3]
                cprint("%s %d %d" % (devname, devsize, mbsize))
                if len(devname) == 8 and mbsize > dbackup_minpartsize and mbsize < dbackup_maxpartsize:
                    # only sticks from 1GB up to 64GB are used as recovery sticks
                    found = True
                    devlist.append(("%s %d %s" % (devname,mbsize,"MB"), devname,mbsize))
        f.close()
        if not found:
            devlist.append(("no device found, shutdown, add device and reboot", "nodev", 0))
        return devlist

    def askForDevice(self,device):
        if device is None:
            self.session.open(MessageBox, _("Sorry, no device choosen"), MessageBox.TYPE_ERROR)
        elif device[1] == "nodev":
            self.session.open(MessageBox, _("Sorry, no device found"), MessageBox.TYPE_ERROR)
        else:
            self.device = device[1]
            self.session.openWithCallback(self.formatDevice, MessageBox,_("Are you sure that you want to format USB device %s now?") % (self.device), MessageBox.TYPE_YESNO)

    def formatDevice(self,option):
        if option is False:
            self.session.open(MessageBox, _("Sorry, formatting of USB Decvice %s was canceled!") % self.device, MessageBox.TYPE_ERROR)
        else:
            open(dbackup_busy, 'a').close()
            if not os_path.exists("/media/DREAMFLASH"):
                os_mkdir("/media/DREAMFLASH")
            else:
                os_system("umount /media/DREAMFLASH")
            self["logo"].instance.setPixmapFromFile("%s/ring.png" % dbackup_plugindir)
#                       if os_path.exists("/usr/lib/enigma2/python/Plugins/Bp/geminimain/lib/libgeminimain.so"):
#                               libgeminimain.setHWLock(1)
            #
            # let's partition and format now as FAT on
            # a single primary partition to be sure that device is ONLY for recovery
            #
            command = "#!/bin/sh\n"
            command += "umount %s1\n" % self.device
            command += "umount %s2\n" % self.device
            command += "umount %s3\n" % self.device
            command += "umount %s4\n" % self.device
            command += "umount %s\n" % self.device
            command += "dd if=/dev/zero of=%s bs=1024 count=1\n" % self.device
            command += "fdisk %s << EOF\n" % self.device
            command += "d\n"
            command += "1\n"
            command += "d\n"
            command += "2\n"
            command += "d\n"
            command += "3\n"
            command += "d\n"
            command += "n\n"
            command += "p\n"
            command += "1\n"
            command += "\n"
            command += "\n"
            command += "w\n"
            command += "EOF\n"
            command += "partprobe %s\n" % self.device
            command += "fdisk %s << EOF\n" % self.device
            command += "t\n"
            command += "6\n"
            command += "a\n"
            command += "1\n"
            command += "w\n"
            command += "EOF\n"
            command += "partprobe %s\n" % self.device
            command += "umount %s1\n" % self.device
            command += "umount %s\n" % self.device
            command += "mkdosfs -n DREAMFLASH %s1\n" % self.device
            command += "mount %s1 -o async,rw /media/DREAMFLASH\n" % self.device
            command += "exit 0\n"
        #       cprint(command)
            b = open(dbackup_script,"w")
            b.write(command)
            b.close()
            os_chmod(dbackup_script, 0o755)
            self.container = eConsoleAppContainer()
            cprint("daemon %s" % dbackup_script)
            if not os_path.exists("/var/lib/opkg/status"):
                self.container_appClosed_conn = self.container.appClosed.connect(self.formatFinished)
            else:
                self.container.appClosed.append(self.formatFinished)
            self.container.execute(dbackup_script)

    def formatFinished(self, retval):
#               if os_path.exists("/usr/lib/enigma2/python/Plugins/Bp/geminimain/lib/libgeminimain.so"):
#                       libgeminimain.setHWLock(0)
        # check if mounted
        f = open("/proc/mounts","r")
        mm = f.read()
        f.close()
        if mm.find("/media/DREAMFLASH") == -1:
            if os_path.exists(dbackup_busy):
                os_remove(dbackup_busy)
            self.session.open(MessageBox,mounted_string % path, MessageBox.TYPE_ERROR)
        else:
            self.askForBackupName("dreambox-image-%s" % self.boxtype)

    def doFlash(self,option):
        if option:
            cprint("is flashing now %s" % self.nfifile)
            self.flashingtime = 0
            self.doHide()
            if 'slider' in self.session.summary:
                self.session.summary["slider"].show()
            if 'duration' in self.session.summary:
                self.session.summary["duration"].setText("0")
            self["duration"].setText("0")
            if 'displayentry' in self.session.summary:
                if config.plugins.dbackup.displayentry.value == "mb":
                    self.session.summary["displayentry"].setText("0.0 MB")
            if os_path.exists("/var/lib/opkg/status"):
                self.session.summary["titletext"].setText(flashing_string)
            self.TimerFlashing = eTimer()
            self.TimerFlashing.stop()
            if not os_path.exists("/var/lib/opkg/status"):
                self.TimerFlashing_conn = self.TimerFlashing.timeout.connect(self.flashingFinishedCheck)
            else:
                self.TimerFlashing.callback.append(self.flashingFinishedCheck)
            self.TimerFlashing.start(1000,True)
            FlashingImage(self.nfifile)
        else:
            cprint("cancelled flashing %s" % self.nfifile)

    def flashingFinishedCheck(self):
        if os_path.exists(dbackup_busy):
            global dbackup_progress
            self.flashingtime = self.flashingtime + 1
            rsize = 0
            if self.nfifile == "rescue":
                dbackup_progress = 5 * self.flashingtime
            else:
                working = "%s/tmp/rootfs.tar" % (config.plugins.dbackup.backuplocation.value)
#                               cprint("%s" % working)
                if os_path.exists(working):
                    rsize = os_path.getsize(working)
                total_size = rsize
                st = os_statvfs("/")
                rused = (st.f_blocks - st.f_bfree) * st.f_frsize
                if self.boxtype == "dm520":
                    used = rused * 3
                else:
                    used = rused
                if used < 0:
                    used = 0
                cprint("total size %d used %d" % (total_size,used))
                if config.plugins.dbackup.backuptool.value == "tar.xz":
                    dbackup_progress = flashing_tarxz * total_size // used
                elif config.plugins.dbackup.backuptool.value == "tar.gz":
                    dbackup_progress = flashing_targz * total_size // used
                elif config.plugins.dbackup.backuptool.value == "tar.bz2":
                    dbackup_progress = flashing_tarbz2 * total_size // used
                else:
                    dbackup_progress = flashing_tar * total_size // used
            self.slider.setValue(dbackup_progress)
            if 'slider' in self.session.summary:
                self.session.summary["slider"].setValue(dbackup_progress)
            cprint("checked if flashing is finished after %d sec ..." % self.flashingtime)
            if 'duration' in self.session.summary:
                self.session.summary["duration"].setText("%s" % self.flashingtime)
            self["duration"].setText("%s" % self.flashingtime)
            if 'displayentry' in self.session.summary:
                if config.plugins.dbackup.displayentry.value == "mb":
                    self.session.summary["displayentry"].setText("%.1f MB" % round(rsize / 1024.0 / 1024.0,1))
            self.TimerFlashing.start(1000,True)
        else:
            cprint("FLASHING UNHIDE")
            self.doUnhide(0, 0)
            if self.nfifile == "rescue":
                dbackup_progress = 0
                self.slider.setValue(dbackup_progress)
                if 'slider' in self.session.summary:
                    self.session.summary["slider"].setValue(dbackup_progress)
                self.doUnhide(0, 0)
                self.DimmingTimer.stop()
                self.session.open(MessageBox, _("Flashing of %s was finished!") % self.nfifile, MessageBox.TYPE_INFO)
            else:
                if self.boxtype != "dm520" and self.boxtype != "dreamone":
                    eDBoxLCD.getInstance().lock()
                eRCInput.getInstance().lock()
                fbClass.getInstance().lock()

    def config(self):
        if os_path.exists(dbackup_busy):
            self.session.open(MessageBox, running_string, MessageBox.TYPE_ERROR)

    def cancel(self):
        self.close(False)

    def getBackupPath(self):
        backup = []
        backup.append((config.plugins.dbackup.backuplocation.value,config.plugins.dbackup.backuplocation.value))
        for mount in os_listdir("/media"):
            backupdir = "/media/%s/backup" % mount
            # added to trigger automount
            os_system("ls %s" % backupdir)
            try:
                if os_path.exists(backupdir) and backupdir != config.plugins.dbackup.backuplocation.value:
                    backup.append((backupdir,backupdir))
            except:
                pass
        if os_path.exists("/autofs"):
            for mount in os_listdir("/autofs"):
                backupdir = "/autofs/%s/backup" % mount
                # added to trigger automount
                os_system("ls %s" % backupdir)
                try:
                    if os_path.exists(backupdir) and backupdir != config.plugins.dbackup.backuplocation.value:
                        backup.append((backupdir,backupdir))
                except:
                    pass
        f = open("/proc/mounts", "r")
        m = f.read()
        f.close()
        if m.find("/data") != -1:
            try:
                backupdir = "/data/backup"
                if os_path.exists(backupdir) and backupdir != config.plugins.dbackup.backuplocation.value:
                    backup.append((backupdir,backupdir))
            except:
                pass
        return backup

    def backup(self):
        global dbackup_progress
        if os_path.exists(dbackup_backup):
            cprint("found finished backup ...")
            dbackup_progress = 0
            self.TimerBackup = eTimer()
            self.TimerBackup.stop()
            if os_path.exists(dbackup_busy):
                os_remove(dbackup_busy)
            if config.plugins.dbackup.transparency.value < config.osd.alpha.value:
                # reset needed
                if os_path.exists("/proc/stb/video/alpha"):
                    f = open("/proc/stb/video/alpha","w")
                else: # dreamone, dreamtwo
                    f = open("/sys/devices/platform/meson-fb/graphics/fb0/osd_plane_alpha","w")
                f.write("%i" % (config.osd.alpha.value))
                f.close()
            f = open(dbackup_backup)
            line = f.readline()
            f.close()
            os_remove(dbackup_backup)
            sp = []
            sp = line.split(" ")
            #print(sp)
            length = len(sp)
            size = ""
            image = ""
            path = ""
            if length > 0:
                sp2 = []
                sp2 = sp[length - 1].split("/")
                size = sp2[0].rstrip().lstrip()
                #print(sp2)
                length = len(sp2)
                if length > 0:
                    image = sp2[length - 1]
                    path = line.replace(size,"").replace(image,"").rstrip().lstrip().replace("\t"," ")
                    image = image.replace(".nfi\n","")
                    image = image.rstrip().lstrip()
            cprint("found backup %s" % line)
            # checking for IO Errors
            starttime = 0
            endtime = 0
            io_error = False
            if os_path.exists(dbackup_log):
                b = open(dbackup_log,"r")
                line = b.readline()
                line = b.readline()
                starttime = int(line)
                while line:
                    line = b.readline()
                    if line.find("Input/output err") != -1:
                        io_error = True
                    if line.find("date +") != -1:
                        line = b.readline()
                        # dirty ...
                        if line.startswith("1"):
                            endtime = int(line)
                b.close()
                os_remove(dbackup_log)
            duration = str(endtime - starttime)
            cprint("start: %d end: %d duration: %s" % (starttime,endtime,duration))
            if io_error:
                self.session.open(MessageBox,size + "B " + _("Flash Backup to %s\n\nfinished with imagename:\n\n%s.%s\n\nBUT it has I/O Errors") % (path,image,config.plugins.dbackup.backuptool.value) + "\n\n" + _("Duration:") + " " + duration + " " + _("seconds"), MessageBox.TYPE_ERROR)
            else:
                self.session.open(MessageBox,size + "B " + _("Flash Backup to %s\n\nfinished with imagename:\n\n%s.%s") % (path,image,config.plugins.dbackup.backuptool.value) + "\n\n" + _("Duration:") + " " + duration + " " + _("seconds"), MessageBox.TYPE_INFO)
        else:
            if os_path.exists(dbackup_busy):
                self.session.open(MessageBox, running_string, MessageBox.TYPE_ERROR)
            elif os_path.exists("/.bainfo"):
                self.session.open(MessageBox, barryallen_string, MessageBox.TYPE_ERROR)
            elif os_path.exists("/.lfinfo"):
                self.session.open(MessageBox, lowfat_string, MessageBox.TYPE_ERROR)
            else:
                if config.plugins.dbackup.flashtool.value == "rescue":
                    backup = []
                    backup.append(("/data/.recovery"))
                    self.askForBackupPath(backup)
                elif config.plugins.dbackup.flashtool.value == "recovery":
                    backup = []
                    backup.append(("/media/DREAMFLASH"))
                    self.askForBackupPath(backup)
                else:
                    if config.plugins.dbackup.backupaskdir.value:
                        self.session.openWithCallback(self.askForBackupPath,ChoiceBox,_("select backup path"),self.getBackupPath())
                    else:
                        backup = []
                        backup.append((config.plugins.dbackup.backuplocation.value))
                        self.askForBackupPath(backup)

    def askForBackupPath(self,backup_path):
#               self.imagetype=""
        self.creator = ""
        if backup_path is None:
            self.session.open(MessageBox,_("nothing entered"), MessageBox.TYPE_ERROR)
            return
        path = backup_path[0]
        cprint("PATH: %s" % path)
        if path == "/data/.recovery":
            if not os_path.exists("/data"):
                os_mkdir("/data")
            os.system("umount %s; mount %s /data" % (dreambox_data, dreambox_data))
            os_system("mount -o remount,async /data")
            f = open("/proc/mounts","r")
            mounts = f.read()
            f.close()
            if mounts.find("/data") == -1:
                self.session.open(MessageBox,mounted_string % path, MessageBox.TYPE_ERROR)
                return
            if not os_path.exists("/data/.recovery"):
                os_mkdir("/data/.recovery")
            self.backupname = "backup"
            self.askForBackupName("backup")
        elif path == "/media/DREAMFLASH":
            if os_path.exists("/dev/disk/by-label/DREAMFLASH"):
                if not os_path.exists("/media/DREAMFLASH"):
                    os_mkdir("/media/DREAMFLASH")
                if os_path.exists("/dev/disk/by-label/DREAMFLASH"):
                    device = os_readlink("/dev/disk/by-label/DREAMFLASH")
                    self.device = device.replace("../..","/dev").replace("1","")
                    cprint("%s %s" % (device, self.device))
                    os_system("ummount %s1; umount %s; mount -o rw,async /dev/disk/by-label/DREAMFLASH /media/DREAMFLASH" % (self.device,self.device))
                f = open("/proc/mounts", "r")
                m = f.read()
                f.close()
            #       print(m)
                if m.find("/media/DREAMFLASH") == -1:
                    self.session.open(MessageBox,mounted_string % path, MessageBox.TYPE_ERROR)
                else:
                    self.askForBackupName("dreambox-image-%s" % self.boxtype)
            else:
                cprint("create recovery USB stick")
                device_string = _("Select device for recovery USB stick")
                self.session.openWithCallback(self.askForDevice,ChoiceBox,device_string,self.getDeviceList())
        else:
            if not os_path.exists(path):
                os_system("ls %s" % path)
            sp = []
            sp = path.split("/")
        #       print(sp)
            if len(sp) > 1:
                if sp[1] != "media" and sp[1] != "autofs" and sp[1] != "data":
                    cprint("NOT #1 %s" % sp[1])
                    self.session.open(MessageBox,mounted_string % path, MessageBox.TYPE_ERROR)
                    return
            if sp[1] != "data":
                f = open("/proc/mounts", "r")
                m = f.read()
                f.close()
            #       print(m)
                if m.find("/media/%s" % sp[2]) == -1 and m.find("/autofs/%s" % sp[2]) == -1:
                    cprint("NOT #2 %s" % sp[2])
                    self.session.open(MessageBox,mounted_string % path, MessageBox.TYPE_ERROR)
                    return
            path = path.lstrip().rstrip("/").rstrip().replace(" ","")
            # remember for next time
            config.plugins.dbackup.backuplocation.value = path
            config.plugins.dbackup.backuplocation.save()
            if not os_path.exists(config.plugins.dbackup.backuplocation.value):
                os_mkdir(config.plugins.dbackup.backuplocation.value,0o777)
            name = "dreambox-image"
            if os_path.exists("/etc/image-version"):
                f = open("/etc/image-version")
                line = f.readline()
                while (line):
                    line = f.readline()
                    if line.startswith("creator="):
                        name = line
                f.close()
                name = name.replace("creator=","")
                sp = []
                if len(name) > 0:
                    sp = name.split(" ")
                    if len(sp) > 0:
                        name = sp[0]
                        name = name.replace("\n","")
            self.creator = name.rstrip().lstrip()
            cdate = str(datetime.date.today())
            ctime = str(time.strftime("%H-%M"))
            suggested_backupname = name
#                       if config.plugins.dbackup.backupdeb.value:
#                               suggested_backupname=suggested_backupname+"-deb"
            if config.plugins.dbackup.backupid.value != "none":
                if config.plugins.dbackup.backupid.value != "user":
                    suggested_backupname = suggested_backupname + "-%s" % config.plugins.dbackup.backupid.value
                else:
                    suggested_backupname = suggested_backupname + "-%s" % (config.plugins.dbackup.backupuserid.value.rstrip().lstrip().replace(" ","_"))
            if config.plugins.dbackup.backupboxtype.value:
                suggested_backupname = suggested_backupname + "-" + self.boxtype
#                       if config.plugins.dbackup.backupimagetype.value:
#                               suggested_backupname=suggested_backupname+"-"+self.imagetype
            if config.plugins.dbackup.backupdate.value:
                suggested_backupname = suggested_backupname + "-" + cdate
            if config.plugins.dbackup.backuptime.value:
                suggested_backupname = suggested_backupname + "-" + ctime
            if config.plugins.dbackup.flashtool.value == "rescue":
                suggested_backupname = "backup"
            cprint("suggested backupname %s" % suggested_backupname)
            blanks = ""
            i = 0
            blanks_len = int(config.plugins.dbackup.backupblanks.value)
            while i < blanks_len:
                blanks = blanks + " "
                i += 1
            length_blanks = len(blanks)
            cprint("BLANKS %d" % length_blanks)
            suggested_backupname = suggested_backupname + blanks
            blanks_len = blanks_len + 60
            self.session.openWithCallback(self.askForBackupName,InputBox, title=backupimage_string, text=suggested_backupname, maxSize=blanks_len, type=Input.TEXT)

    def askForBackupName(self,name):
        if name is None:
            self.session.open(MessageBox,_("nothing entered"), MessageBox.TYPE_ERROR)
        else:
            self.backupname = name.replace(" ","").replace("[","").replace("]","").replace(">","").replace("<","").replace("|","").rstrip().lstrip()
            if self.backupname.find(self.boxtype) == -1 and config.plugins.dbackup.flashtool.value != "rescue":
                self.backupname = self.backupname + "-" + self.boxtype
            if os_path.exists("%s/%s.%s" % (config.plugins.dbackup.backuplocation.value,self.backupname,config.plugins.dbackup.backuptool.value)):
                self.session.openWithCallback(self.confirmedBackup,MessageBox,"%s.%s" % (self.backupname,config.plugins.dbackup.backuptool.value) + "\n" + _("already exists,") + " " + _("overwrite ?"), MessageBox.TYPE_YESNO)
            else:
                self.confirmedBackup(True)

    def confirmedBackup(self,answer):
        if answer:
            if os_path.exists("%s/%s.%s" % (config.plugins.dbackup.backuplocation.value,self.backupname,config.plugins.dbackup.backuptool.value)):
                os_remove("%s/%s.%s" % (config.plugins.dbackup.backuplocation.value,self.backupname,config.plugins.dbackup.backuptool.value))
            if os_path.exists("%s/%s.sig" % (config.plugins.dbackup.backuplocation.value,self.backupname)):
                os_remove("%s/%s.sig" % (config.plugins.dbackup.backuplocation.value,self.backupname))
            self.session.openWithCallback(self.startBackup,MessageBox, _("Press OK for starting backup") + "\n\n%s.%s" % (self.backupname,config.plugins.dbackup.backuptool.value) + "\n\n" + _("Be patient, this takes some time ..."), MessageBox.TYPE_INFO)
        else:
            self.session.open(MessageBox,_("not confirmed"), MessageBox.TYPE_ERROR)

    def startBackup(self,answer):
        if answer:
            cprint("is doing backup now ...")
            self.starttime = time.time()
            self["logo"].instance.setPixmapFromFile("%s/ring.png" % dbackup_plugindir)
            self.doHide()
            if 'slider' in self.session.summary:
                self.session.summary["slider"].show()
            if 'duration' in self.session.summary:
                self.session.summary["duration"].setText("0")
            self["duration"].setText("0")
            if 'displayentry' in self.session.summary:
                if config.plugins.dbackup.displayentry.value == "mb":
                    self.session.summary["displayentry"].setText("0.0 MB")
            if os_path.exists("/var/lib/opkg/status"):
                self.session.summary["titletext"].setText(backup_string)
            self.backuptime = 0
            self.TimerBackup = eTimer()
            self.TimerBackup.stop()
            if not os_path.exists("/var/lib/opkg/status"):
                self.TimerBackup_conn = self.TimerBackup.timeout.connect(self.backupFinishedCheck)
            else:
                self.TimerBackup.callback.append(self.backupFinishedCheck)
            self.TimerBackup.start(1000,True)
            BackupImage(self.backupname)
        else:
            cprint("was not confirmed")

    def backupFinishedCheck(self):
        global dbackup_progress
        self.backuptime = self.backuptime + 1
        if not os_path.exists(dbackup_backup):
            # not finished - continue checking ...
            rsize = 0
            working = "%s/%s.%s" % (config.plugins.dbackup.backuplocation.value,self.backupname,config.plugins.dbackup.backuptool.value)
            cprint("%s" % working)
            if os_path.exists(working):
                rsize = os_path.getsize(working)
            total_size = rsize
            st = os_statvfs("/")
            rused = (st.f_blocks - st.f_bfree) * st.f_frsize
            if self.boxtype == "dm520":
                used = rused * 3
            else:
                used = rused
            if used < 0:
                used = 0
            cprint("total size %d used %d" % (total_size,used))
            if total_size > 0:
                if config.plugins.dbackup.backuptool.value == "tar.xz":
                    dbackup_progress = dbackup_tarxz * total_size // used
                elif config.plugins.dbackup.backuptool.value == "tar.gz":
                    dbackup_progress = dbackup_targz * total_size // used
                elif config.plugins.dbackup.backuptool.value == "tar.bz2":
                    dbackup_progress = dbackup_tarbz2 * total_size // used
                else:
                    dbackup_progress = dbackup_tar * total_size // used
            else:
                dbackup_progress = self.backuptime
            self.slider.setValue(dbackup_progress)
            if 'slider' in self.session.summary:
                self.session.summary["slider"].setValue(dbackup_progress)
            cprint("checked if backup is finished after %d sec ..." % self.backuptime)
            if 'duration' in self.session.summary:
                self.session.summary["duration"].setText("%s" % self.backuptime)
            self["duration"].setText("%s" % self.backuptime)
            if 'displayentry' in self.session.summary:
                if config.plugins.dbackup.displayentry.value == "mb":
                    self.session.summary["displayentry"].setText("%.1f MB" % round(rsize / 1024.0 / 1024.0,1))
            self.TimerBackup.start(1000,True)
        else:
            cprint("found finished backup ...")
            self.TimerBackup = eTimer()
            self.TimerBackup.stop()
            f = open(dbackup_backup)
            line = f.readline()
            f.close()
            os_remove(dbackup_backup)
            sp = []
            sp = line.split(" ")
            #print(sp)
            length = len(sp)
            size = ""
            image = ""
            path = ""
            if length > 0:
                sp2 = []
                sp2 = sp[length - 1].split("/")
                size = sp2[0].rstrip().lstrip()  
                #print(sp2)
                length = len(sp2)
                if length > 0:
                    image = sp2[length - 1]
                    path = line.replace(size,"").replace(image,"").lstrip().rstrip()
                    image = image.replace(".tar.gz\n","").replace(".tar.xz\n","").replace(".tar.bz2\n","").replace(".tar\n","")
                else:
                    image = ""
            cprint("found backup %s" % line)
            # checking for IO Errors
            l = ""
            if os_path.exists(dbackup_log):
                b = open(dbackup_log)
                l = b.read()
                b.close()
            if config.plugins.dbackup.flashtool.value == "rescue":
                os_system("umount /data")
            try:
                if 'slider' in self.session.summary:
                    self.session.summary["slider"].setValue(500)
                self.slider.setValue(500)
                duration = str(int(round(time.time() - self.starttime)))
                working = "%s/%s.%s" % (config.plugins.dbackup.backuplocation.value,self.backupname,config.plugins.dbackup.backuptool.value)
                rsize = 0
                if os_path.exists(working):
                    rsize = os_path.getsize(working)
                if 'duration' in self.session.summary:
                    self.session.summary["duration"].setText("%s" % duration)
                self["duration"].setText("%s" % duration)
                if 'displayentry' in self.session.summary:
                    if config.plugins.dbackup.displayentry.value == "mb":
                        self.session.summary["displayentry"].setText("%.1f MB" % round(rsize / 1024.0 / 1024.0,1))
                #print("=== dbackup rsize", rsize/1024.0/1024.0, rsize, round(rsize/1024.0/1024.0,1), int(round(rsize/1024.0/1024.0,1)))
                #print("=== dbackup size ", size)
                if l.find("Input/output err") != -1:
                    self.FinishMsgTxt = "%sB " % (size) + _("Flash Backup to %s\n\nfinished with imagename:\n\n%s.%s\n\nBUT it has I/O Errors") % (path,image,config.plugins.dbackup.backuptool.value) + "\n\n" + _("Duration:") + " " + duration + " " + _("seconds")
                    self.FinishMsgBoxType = MessageBox.TYPE_ERROR
                else:
                    self.FinishMsgTxt = "%sB " % (size) + _("Flash Backup to %s\n\nfinished with imagename:\n\n%s.%s") % (path, image,config.plugins.dbackup.backuptool.value) + "\n\n" + _("Duration:") + " " + duration + " " + _("seconds")
                    self.FinishMsgBoxType = MessageBox.TYPE_INFO
            except:
                # why crashes even this
#                               self.session.open(MessageBox,_("Flash Backup to %s finished with imagename:\n\n%s.%s") % (path,image,config.plugins.dbackup.backuptool.value),  MessageBox.TYPE_INFO)
                self.FinishMsgTxt = _("Flash Backup finished")
                self.FinishMsgBoxType = MessageBox.TYPE_INFO

            self.TimerBackupFinishMessage = eTimer()
            if not os_path.exists("/var/lib/opkg/status"):
                self.TimerBackupFinishMessage_conn = self.TimerBackupFinishMessage.timeout.connect(self.callbackFinishMessage)
            else:
                self.TimerBackupFinishMessage.callback.append(self.callbackFinishMessage)
            self.TimerBackupFinishMessage.start(1000,True)

            #start automatic cleanup
            clean_dBackup()


    def callbackFinishMessage(self):
        if os_path.exists(dbackup_busy):
            os_remove(dbackup_busy)
        if config.plugins.dbackup.transparency.value < config.osd.alpha.value:
            # reset needed
            if os_path.exists("/proc/stb/video/alpha"):
                f = open("/proc/stb/video/alpha","w")
            else: # dreamone, dreamtwo
                f = open("/sys/devices/platform/meson-fb/graphics/fb0/osd_plane_alpha","w")
            f.write("%i" % (config.osd.alpha.value))
            f.close()
            self.DimmingTimer = eTimer()
            self.DimmingTimer.stop()
        self.TimerBackupFinishMessage = eTimer()
        self.TimerBackupFinishMessage.stop()
        dbackup_progress = 0
        self.slider.setValue(0)
        if 'slider' in self.session.summary:
            self.session.summary["slider"].setValue(0)
            self.session.summary["slider"].hide()
        if 'duration' in self.session.summary:
            self.session.summary["duration"].setText(" ")
        self["duration"].setText(" ")
        if 'displayentry' in self.session.summary:
            if config.plugins.dbackup.displayentry.value == "mb":
                self.session.summary["displayentry"].setText(" ")
        self.session.open(MessageBox,self.FinishMsgTxt, self.FinishMsgBoxType)

    def config(self):
        if os_path.exists(dbackup_busy):
            self.session.open(MessageBox, running_string, MessageBox.TYPE_ERROR)
        else:
            self.session.open(dBackupConfiguration)

def startdBackup(session, **kwargs):
    if os_path.exists("/usr/lib/enigma2/python/Plugins/SystemPlugins/gutemine") or os_path.exists("/var/lib/opkg/status"):
        session.open(dBackup)
    else:
        session.open(MessageBox, running_string, MessageBox.TYPE_ERROR)

def startRecover(session, **kwargs):
    global dsession
    dsession = session
    session.openWithCallback(askForTask,ChoiceBox,_("Please choose what you want to do next."), getTaskList())

def getTaskList():
    task = []
    task.append((_("Reboot") + " " + _("Recovery Mode"), "boot"))
    task.append((_("Software update") + " " + _("Recovery Mode"), "upgrade"))
    return task

def askForTask(task):
    global dsession
    if task is None:
        return
    else:
        do = task[1].rstrip()
    #       print(">>>>>>>>>>>", do)
        if do == "boot":
            dsession.openWithCallback(startRecovery,MessageBox,_("Recovery Mode") + " " + _("Really shutdown now?"), MessageBox.TYPE_YESNO)
        else:
            dsession.openWithCallback(startLoaderUpdate,MessageBox,_("Recovery Mode") + " " + _("Software update") + "?", MessageBox.TYPE_YESNO)

def startRecovery(option):
    global dsession
    if option:
        cprint("starting Recovery")
        b = open("/proc/stb/fp/boot_mode","w")
        b.write("rescue")
        b.close()
        quitMainloop(2)
    else:
        cprint("cancelled Recovery")

def startLoaderUpdate(option):
    global dsession
    if option:
        cprint("starting Rescue Loader update")
        update_cmd = "update-rescue -v"
        from API import session
        dsession.open(Console,_("Recovery Mode") + " " + _("Software update") + " " + _("waiting") + "...",[update_cmd])
    else:
        cprint("cancelled Rescue Loader update")

def recovery2Webif(enable):
    if enable:
        cprint("recovery webinterface enabling")
    else:
        cprint("recovery webinterface disabling")
    if os_path.exists("/usr/lib/enigma2/python/Plugins/Extensions/WebInterface/WebComponents/Sources/PowerState.py"):
        p = open("/usr/lib/enigma2/python/Plugins/Extensions/WebInterface/WebComponents/Sources/PowerState.py")
        ps = p.read()
        p.close()
        if enable:
            if ps.find("type == 99:") == -1:
                cprint("recovery webinterface inserting #1")
                ps2 = ps.replace("type = int(self.cmd)","type = int(self.cmd)\n\n                        if type == 99:\n                           b=open(\"/proc/stb/fp/boot_mode\",\"w\")\n                           b.write(\"rescue\")\n                           b.close()\n                           type=2\n")
                p = open("/usr/lib/enigma2/python/Plugins/Extensions/WebInterface/WebComponents/Sources/PowerState.py","w")
                p.write(ps2)
                p.close()
        else:
            if ps.find("type == 99:") != -1:
                cprint("recovery webinterface removing #1")
                ps2 = ps.replace("type = int(self.cmd)\n\n                               if type == 99:\n                           b=open(\"/proc/stb/fp/boot_mode\",\"w\")\n                           b.write(\"rescue\")\n                           b.close()\n                           type=2\n","type = int(self.cmd)")
                p = open("/usr/lib/enigma2/python/Plugins/Extensions/WebInterface/WebComponents/Sources/PowerState.py","w")
                p.write(ps2)
                p.close()
    if os_path.exists("/usr/lib/enigma2/python/Plugins/Extensions/WebInterface/web-data/core.js"):
        p = open("/usr/lib/enigma2/python/Plugins/Extensions/WebInterface/web-data/core.js")
        cs = p.read()
        p.close()
        if enable:
            if cs.find("rebootsetup") == -1:
                cprint("recovery webinterface inserting #2")
                cs2 = cs.replace("\'gui\' : 3","\'gui\' : 3, \'rebootsetup\' : 99")
                p = open("/usr/lib/enigma2/python/Plugins/Extensions/WebInterface/web-data/core.js","w")
                p.write(cs2)
                p.close()
        else:
            if cs.find("rebootsetup") != -1:
                cprint("recovery webinterface removing #2")
                cs2 = cs.replace("\'gui\' : 3, \'rebootsetup\' : 99","\'gui\' : 3")
                p = open("/usr/lib/enigma2/python/Plugins/Extensions/WebInterface/web-data/core.js","w")
                p.write(cs2)
                p.close()
    if os_path.exists("/usr/lib/enigma2/python/Plugins/Extensions/WebInterface/web-data/tpl/default/index.html"):
        p = open("/usr/lib/enigma2/python/Plugins/Extensions/WebInterface/web-data/tpl/default/index.html")
        ix = p.read()
        p.close()
        if enable:
            if ix.find("rebootsetup") == -1:
                cprint("recovery webinterface inserting #3")
                ix2 = ix.replace("data-state=\"gui\">Restart GUI</a></li>","data-state=\"gui\">Restart GUI</a></li>\n                                                             <li><a href=\"#\" class=\"powerState\" data-state=\"rebootsetup\">Recovery Mode</a></li>")
                p = open("/usr/lib/enigma2/python/Plugins/Extensions/WebInterface/web-data/tpl/default/index.html","w")
                p.write(ix2)
                p.close()
        else:
            if ix.find("rebootsetup") != -1:
                cprint("recovery webinterface removing #3")
                ix2 = ix.replace("data-state=\"gui\">Restart GUI</a></li>\n                                                               <li><a href=\"#\" class=\"powerState\" data-state=\"rebootsetup\">Recovery Mode</a></li>","data-state=\"gui\">Restart GUI</a></li>")
                ix2 = ix.replace("data-state=\"gui\">Restart GUI</a></li>\n                                                               <li><a href=\"#\" class=\"powerState\" data-state=\"rebootsetup\">Recovery</a></li>","data-state=\"gui\">Restart GUI</a></li>")
                p = open("/usr/lib/enigma2/python/Plugins/Extensions/WebInterface/web-data/tpl/default/index.html","w")
                p.write(ix2)
                p.close()
    if os_path.exists("/usr/lib/enigma2/python/Plugins/Extensions/WebInterface/web-data/tpl/default/tplPower.htm"):
        p = open("/usr/lib/enigma2/python/Plugins/Extensions/WebInterface/web-data/tpl/default/tplPower.htm")
        df = p.read()
        p.close()
        if enable:
            if df.find("rebootsetup") == -1:
                cprint("recovery webinterface inserting #4")
                df2 = df.replace("data-state=\"gui\">${strings.restart_enigma2}</button></td>","data-state=\"gui\">${strings.restart_enigma2}</button></td>\n                                                                             </tr>\n                                                                         <tr>\n                                                                                  <td><button class=\"w200h50 powerState\" data-state=\"rebootsetup\">Recovery Mode</button></td>")
                p = open("/usr/lib/enigma2/python/Plugins/Extensions/WebInterface/web-data/tpl/default/tplPower.htm","w")
                p.write(df2)
                p.close()
        else:
            if df.find("rebootsetup") != -1:
                cprint("recovery webinterface removing #4")
                df2 = df.replace("data-state=\"gui\">${strings.restart_enigma2}</button></td>\n                                                                   </tr>\n                                                                 <tr>\n                                                                          <td><button class=\"w200h50 powerState\" data-state=\"rebootsetup\">Recovery Mode</button></td>","data-state=\"gui\">${strings.restart_enigma2}</button></td>")
                df2 = df.replace("data-state=\"gui\">${strings.restart_enigma2}</button></td>\n                                                                   </tr>\n                                                                 <tr>\n                                                                          <td><button class=\"w200h50 powerState\" data-state=\"rebootsetup\">Recovery</button></td>","data-state=\"gui\">${strings.restart_enigma2}</button></td>")
                p = open("/usr/lib/enigma2/python/Plugins/Extensions/WebInterface/web-data/tpl/default/tplPower.htm","w")
                p.write(df2)
                p.close()
    return

TimerBackup = None
TimerBackup_conn = None

def autostart(reason,**kwargs):
    if 'session' in kwargs and reason == 0:
        session = kwargs["session"]
        cprint("autostart")
        config.misc.standbyCounter.addNotifier(dBackupOnStandby, initial_call=False)
        dBackupPowerOn()
        if os_path.exists("/usr/lib/enigma2/python/Plugins/Extensions/WebInterface/WebChilds/Toplevel.py"):
            from Plugins.Extensions.WebInterface.WebChilds.Toplevel import addExternalChild
            addExternalChild(("dbackup", wBackup(), "dBackup", "1", True))
        else:
            cprint("Webif not found")
        if os_path.exists(dbackup_busy):
            os_remove(dbackup_busy)
        tmp_extract = "%s/tmp" % config.plugins.dbackup.backuplocation.value
        if os_path.exists(tmp_extract):
            shutil.rmtree(tmp_extract,True)
        if config.plugins.dbackup.flashtool.value == "rescue":
            config.plugins.dbackup.backuplocation.value = "/data/.recovery"
            config.plugins.dbackup.backuptool.value = "tar.gz"
            config.plugins.dbackup.backuplocation.save()
            config.plugins.dbackup.backuptool.save()
        elif config.plugins.dbackup.flashtool.value == "recovery":
            config.plugins.dbackup.backuplocation.value = "/media/DREAMFLASH"
            config.plugins.dbackup.backuptool.value = "tar.xz"
            config.plugins.dbackup.backuplocation.save()
            config.plugins.dbackup.backuptool.save()
        if config.plugins.dbackup.recovering.value == "webif" or config.plugins.dbackup.recovering.value == "both":
            recovery2Webif(True)
        else:
            recovery2Webif(False)
        if config.plugins.dbackup.automatic.value == "boot" and int(config.plugins.dbackup.latestbackup.value) > 0:
            now = int(time.time())
            last = int(config.plugins.dbackup.lastbackup.value)
            if (int(config.plugins.dbackup.latestbackup.value) > 30) or ((now - last) >= int(config.plugins.dbackup.latestbackup.value) * 3600 * 24):
                cprint("doing new Backup ...")
                startBackupFinishedCheckTimer()
                backupname = automaticBackupName()
                BackupImage(backupname)
            else:
                cprint("recent enough Backup ...")
        return

def dBackupOnStandby(reason):
    cprint("entering Standby/Idle")
    from Screens.Standby import inStandby
    inStandby.onClose.append(dBackupPowerOn)
    if os_path.exists(dbackup_busy):
        cprint("busy with Backup ...")
        return
    if config.plugins.dbackup.automatic.value == "idle" and int(config.plugins.dbackup.latestbackup.value) > 0:
        now = int(time.time())
        last = int(config.plugins.dbackup.lastbackup.value)
        if (int(config.plugins.dbackup.latestbackup.value) > 30) or ((now - last) >= int(config.plugins.dbackup.latestbackup.value) * 3600 * 24):
            cprint("doing new Backup ...")
            startBackupFinishedCheckTimer()
            backupname = automaticBackupName()
            BackupImage(backupname)
        else:
            cprint("recent enough Backup ...")

def startBackupFinishedCheckTimer():
    cprint("start BackupFinishedCheckTimer ...")
    global TimerBackup
    global TimerBackup_conn
    TimerBackup = eTimer()
    TimerBackup.stop()
    if not os_path.exists("/var/lib/opkg/status"):
        TimerBackup_conn = TimerBackup.timeout.connect(backupFinishedCheck)
    else:
        TimerBackup.callback.append(backupFinishedCheck)
    TimerBackup.start(1000,True)

def backupFinishedCheck():
    global TimerBackup
    if os_path.exists(dbackup_busy): # not finished - continue checking ...
        #cprint("not finished - continue checking ...")
        TimerBackup.start(1000,True)
    else:
        cprint("finished backup ...")
        TimerBackup = eTimer()
        TimerBackup.stop()
        #start automatic cleanup
        clean_dBackup()

def dBackupPowerOn():
    cprint("booting or leaving Standby/Idle")
    if config.plugins.dbackup.automatic.value == "message" and int(config.plugins.dbackup.latestbackup.value) > 0 and int(config.plugins.dbackup.latestbackup.value) < 31:
        cprint("checking latest backup ...")
        now = int(time.time())
        last = int(config.plugins.dbackup.lastbackup.value)
        if ((now - last) >= int(config.plugins.dbackup.latestbackup.value) * 3600 * 24):
            cprint("remind too old backup ...")
            global BackupReminderTimer
            BackupReminderTimer = eTimer()
            if not os_path.exists("/var/lib/opkg/status"):
                global BackupReminderTimer_conn
                BackupReminderTimer_conn = BackupReminderTimer.timeout.connect(showBackupReminder)
            else:
                BackupReminderTimer.callback.append(showBackupReminder)
            # remind after 10 seconds ...
            BackupReminderTimer.start(10000, True)

def showBackupReminder():
    cprint("now reminding too old backup ...")
    from API import session
    if int(config.plugins.dbackup.lastbackup.value) > 0:
        timestr = time.strftime('%Y-%m-%d %H:%M', time.localtime(int(config.plugins.dbackup.lastbackup.value)))
        text = ("Last Backup") + ": " + timestr
        session.open(MessageBox, text, MessageBox.TYPE_INFO, timeout=10)
    else:
        text = _("Last Backup") + " " + _("not found")
        session.open(MessageBox, text, MessageBox.TYPE_WARNING, timeout=10)

def automaticBackupName(mask=False):
    name = "dreambox-image"
    if os_path.exists("/etc/image-version"):
        f = open("/etc/image-version")
        line = f.readline()
        while (line):
            line = f.readline()
            if line.startswith("creator="):
                name = line
        f.close()
        name = name.replace("creator=","")
        sp = []
        if len(name) > 0:
            sp = name.split(" ")
            if len(sp) > 0:
                name = sp[0]
                name = name.replace("\n","")
    creator = name.rstrip().lstrip()
    cdate = str(datetime.date.today())
    if mask:
        cdate = "*"
        ctime = "*"
    else:
        cdate = str(datetime.date.today())
        ctime = str(time.strftime("%H-%M"))
    suggested_backupname = name
    if config.plugins.dbackup.backupid.value != "none":
        if config.plugins.dbackup.backupid.value != "user":
            suggested_backupname = suggested_backupname + "-%s" % config.plugins.dbackup.backupid.value
        else:
            suggested_backupname = suggested_backupname + "-%s" % (config.plugins.dbackup.backupuserid.value.rstrip().lstrip().replace(" ","_"))
    if config.plugins.dbackup.backupboxtype.value:
        suggested_backupname = suggested_backupname + "-" + boxtype
    if config.plugins.dbackup.backupdate.value:
        suggested_backupname = suggested_backupname + "-" + cdate
    if config.plugins.dbackup.backuptime.value:
        suggested_backupname = suggested_backupname + "-" + ctime
#       if config.plugins.dbackup.flashtool.value == "rescue":
#               suggested_backupname="backup"
    cprint("suggested backupname %s" % suggested_backupname)
    return suggested_backupname

def main(session,**kwargs):
    if os_path.exists("/usr/lib/enigma2/python/Plugins/SystemPlugins/gutemine") or os_path.exists("/var/lib/opkg/status"):
        session.open(dBackup)
    else:
        session.open(MessageBox, running_string, MessageBox.TYPE_ERROR)

def Plugins(**kwargs):
    plugin_desc = []
    if config.plugins.dbackup.showinsettings.value:
        plugin_desc.append(PluginDescriptor(name=_("Recovery Mode") + " " + _("Update"), description="dBackup", where=PluginDescriptor.WHERE_MENU, fnc=mainconf))
    if config.plugins.dbackup.showinplugins.value:
        plugin_desc.append(PluginDescriptor(name=backup_string + " & " + flashing_string, description="dBackup", where=PluginDescriptor.WHERE_PLUGINMENU, icon="dbackup.png", fnc=main))
    if config.plugins.dbackup.showinextensions.value:
        plugin_desc.append(PluginDescriptor(name=backup_string + " & " + flashing_string, description="dBackup", where=PluginDescriptor.WHERE_EXTENSIONSMENU, icon="dbackup.png", fnc=main))
    plugin_desc.append(PluginDescriptor(where=[PluginDescriptor.WHERE_SESSIONSTART, PluginDescriptor.WHERE_AUTOSTART], fnc=autostart))
    cprint("PluginDescriptor: %s" % plugin_desc)
    return plugin_desc

def mainconf(menuid):
    cprint("menu: %s" % menuid)
    if menuid == "setup":
        return [(backup_string + " & " + flashing_string, startdBackup, "dbackup", None)]
    elif menuid == "system":
        if config.plugins.dbackup.recovering.value == "factory" or config.plugins.dbackup.recovering.value == "both":
            return [(_("Recovery Mode"), startRecover, "recover", None)]
        else:
            return []
    elif menuid == "extended":
        if config.plugins.dbackup.recovering.value == "factory" or config.plugins.dbackup.recovering.value == "both":
            return [(_("Recovery Mode"), startRecover, "recover", None)]
        else:
            return []
    else:
        return []

###############################################################################
# dBackup Webinterface by gutemine
###############################################################################

class wBackup(resource.Resource):
    def render_GET(self, req):
        self.boxtype = getBoxtype()
        global dbackup_progress, dreambox_data
        file = req.args.get("file",None)
        directory = req.args.get("directory",None)
        command = req.args.get("command",None)
        cprint("received %s %s %s" % (command,directory,file))
        req.setResponseCode(http.OK)
        req.setHeader('Content-type', 'text/html')
        req.setHeader('charset', 'UTF-8')
        if not config.plugins.dbackup.webinterface.value:
            return header_string + nowebif_string
        if not os_path.exists("/usr/lib/enigma2/python/Plugins/SystemPlugins/gutemine"):
            return header_string + nowebif_string
        if os_path.exists("/usr/lib/enigma2/python/Plugins/Extensions/WebInterface/web-data/img/dbackup.png") is False:
            os_symlink("%s/dbackup.png" % dbackup_plugindir,"/usr/lib/enigma2/python/Plugins/Extensions/WebInterface/web-data/img/dbackup.png")
        if os_path.exists("/usr/lib/enigma2/python/Plugins/Extensions/WebInterface/web-data/img/ring.png") is False:
            os_symlink("%s/ring.png" % dbackup_plugindir,"/usr/lib/enigma2/python/Plugins/Extensions/WebInterface/web-data/img/ring.png")
        if os_path.exists(dbackup_busy):
            dbackup_backuping_progress = ""
            dbackup_backuping_progress += header_string
            dbackup_backuping_progress += "<br>%s<br><br>" % running_string
            dbackup_backuping_progress += "<br><img src=\"/web-data/img/ring.png\" alt=\"%s ...\"/><br><br>" % (backup_string)
            if dbackup_progress > 0:
                dbackup_backuping_progress += "<div style=\"background-color:yellow;width:%dpx;height:20px;border:1px solid #000\"></div> " % (dbackup_progress)
            dbackup_backuping_progress += "<br><form method=\"GET\">"
            dbackup_backuping_progress += "<input name=\"command\" type=\"submit\" size=\"100px\" title=\"%s\" value=\"%s\">" % (refresh_string,"Refresh")
            dbackup_backuping_progress += "</form>"
            return header_string + dbackup_backuping_progress
        if command is None or command[0] == "Refresh":
            htmlbackup = ""
            htmlbackup += "<option value=\"%s\" class=\"black\">%s</option>\n" % (config.plugins.dbackup.backuplocation.value,config.plugins.dbackup.backuplocation.value)
            if config.plugins.dbackup.backupaskdir.value:
                for mount in os_listdir("/media"):
                    backupdir = "/media/%s/backup" % mount
                    # added to trigger automount
                    os_system("ls %s" % backupdir)
                    try:
                        if os_path.exists(backupdir) and backupdir != config.plugins.dbackup.backuplocation.value:
                            htmlbackup += "<option value=\"%s\" class=\"black\">%s</option>\n" % (backupdir,backupdir)
                    except:
                        pass
                if os_path.exists("/autofs"):
                    for mount in os_listdir("/autofs"):
                        backupdir = "/autofs/%s/backup" % mount
                        # added to trigger automount
                        os_system("ls %s" % backupdir)
                        try:
                            if os_path.exists(backupdir) and backupdir != config.plugins.dbackup.backuplocation.value:
                                htmlbackup += "<option value=\"%s\" class=\"black\">%s</option>\n" % (backupdir,backupdir)
                        except:
                            pass
                f = open("/proc/mounts", "r")
                m = f.read()
                f.close()
                if m.find("/data") != -1:
                    try:
                        backupdir = "/data/backup"
                        if os_path.exists(backupdir) and backupdir != config.plugins.dbackup.backuplocation.value:
                            htmlbackup += "<option value=\"%s\" class=\"black\">%s</option>\n" % (backupdir,backupdir)
                    except:
                        pass
            cprint("%s" % htmlbackup)

            list = []
            htmlnfi = ""
            if self.boxtype != "dreamone" and self.boxtype != "dreamtwo":
                htmlnfi += "<option value=\"%s\" class=\"black\">%s</option>\n" % ("recovery",_("Recovery Image from Feed"))
            htmlnfi += "<option value=\"%s\" class=\"black\">%s</option>\n" % ("rescue",_("Rescue Bios from Feed"))
            entries = os_listdir("/tmp")
            for name in sorted(entries):
                if (name.endswith(".tar.gz") or name.endswith("tar.xz") or name.endswith("tar.bz2") or name.endswith(".tar") or name.endswith(".zip")) and not name.startswith("enigma2settings") and not name.endswith("enigma2settingsbackup.tar.gz"):
                    name2 = name.replace(".tar.gz","").replace(".tar.xz","").replace(".tar.bz2","").replace(".tar","").replace(".zip","")
                    if list.count(name2) < 1 and name2.find(self.boxtype) != -1:
                        list.append((name2, "/tmp/%s" % name))
                        htmlnfi += "<option value=\"/tmp/%s\" class=\"black\">%s</option>\n" % (name,name2)
                    else:
                        cprint("skips %s" % name2)
            if os_path.exists(config.plugins.dbackup.backuplocation.value):
                entries = os_listdir(config.plugins.dbackup.backuplocation.value)
                for name in sorted(entries):
                    if (name.endswith(".tar.gz") or name.endswith("tar.xz") or name.endswith("tar.bz2") or name.endswith(".tar") or name.endswith(".zip")) and not name.startswith("enigma2settings") and not name.endswith("enigma2settingsbackup.tar.gz"):
                        name2 = name.replace(".tar.gz","").replace(".tar.xz","").replace(".tar.bz2","").replace(".tar","").replace(".zip","")
                        if list.count(name2) < 1 and name2.find(self.boxtype) != -1:
                            list.append((name2, "%s/%s" % (config.plugins.dbackup.backuplocation.value,name)))
                            htmlnfi += "<option value=\"%s/%s\" class=\"black\">%s</option>\n" % (config.plugins.dbackup.backuplocation.value,name,name2)
                        else:
                            cprint("skips %s" % name2)
            f = open("/proc/mounts", "r")
            m = f.read()
            f.close()
            if m.find("/data") != -1:
                if os_path.exists("/data/backup") and "/data/backup" != config.plugins.dbackup.backuplocation.value:
                    for name in os_listdir("/data/backup"):
                        if (name.endswith(".tar.gz") or name.endswith(".tar.xz") or name.endswith(".tar.bz2") or name.endswith(".tar") or name.endswith(".zip")) and not name.startswith("enigma2settings") and not name.endswith("enigma2settingsbackup.tar.gz"):
                            name2 = name.replace(".tar.gz","").replace(".tar.xz","").replace(".tar.bz2","").replace(".tar","").replace(".zip","")
                            if list.count(name2) < 1 and name2.find(self.boxtype) != -1:
                                list.append((name2, "/data/backup/%s" % (name)))
                                htmlnfi += "<option value=\"/data/backup/%s\" class=\"black\">%s</option>\n" % (name,name2)
                            else:
                                cprint("skips %s" % name2)
            entries = os_listdir("/media")
            for directory in sorted(entries):
                if os_path.exists("/media/%s/backup" % directory) and os_path.isdir("/media/%s/backup" % directory) and not directory.endswith("net") and not directory.endswith("hdd") and "/media/%s/backup" % directory != config.plugins.dbackup.backuplocation.value:
                    try:
                        for name in os_listdir("/media/%s/backup" % directory):
                            if (name.endswith(".tar.gz") or name.endswith("tar.xz") or name.endswith("tar.bz2") or name.endswith(".tar") or name.endswith(".zip")) and not name.startswith("enigma2settings") and not name.endswith("enigma2settingsbackup.tar.gz"):
                                name2 = name.replace(".tar.gz","").replace(".tar.xz","").replace(".tar.bz2","").replace(".tar","").replace(".zip","")
                                if list.count(name2) < 1 and name2.find(self.boxtype) != -1:
                                    list.append((name2, "/media/%s/backup/%s" % (drectory,name)))
                                    htmlnfi += "<option value=\"/media/%s/backup/%s\" class=\"black\">%s</option>\n" % (directory,name,name2)
                                else:
                                    cprint("skips %s" % name2)
                    except:
                        pass
            if os_path.exists("/autofs"):
                entries = os_listdir("/autofs")
            else:
                entries = []
            for directory in sorted(entries):
                if os_path.exists("/autofs/%s/backup" % directory) and os_path.isdir("/autofs/%s/backup" % directory) and "/autofs/%s/backup" % directory != config.plugins.dbackup.backuplocation.value:
                    try:
                        for name in os_listdir("/autofs/%s/backup" % directory):
                            if (name.endswith(".tar.gz") or name.endswith("tar.xz") or name.endswith("tar.bz2") or name.endswith(".tar") or name.endswith(".zip")) and not name.startswith("enigma2settings") and not name.endswith("enigma2settingsbackup.tar.gz"):
                                name2 = name.replace(".tar.gz","").replace(".tar.xz","").replace(".tar.bz2","").replace(".tar","").replace(".zip","")
                                if list.count(name2) < 1 and name2.find(self.boxtype) != -1:
                                    list.append((name2, "/autofs/%s/backup/%s" % (drectory,name)))
                                    htmlnfi += "<option value=\"/autofs/%s/backup/%s\" class=\"black\">%s</option>\n" % (directory,name,name2)
                                else:
                                    cprint("skips %s" % name2)
                    except:
                        pass
            cprint("%s" % htmlnfi)

            name = "dreambox-image"
            if os_path.exists("/etc/image-version"):
                f = open("/etc/image-version")
                line = f.readline()
                while (line):
                    line = f.readline()
                    if line.startswith("creator="):
                        name = line
                f.close()
                name = name.replace("creator=","")
                sp = []
                if len(name) > 0:
                    sp = name.split(" ")
                    if len(sp) > 0:
                        name = sp[0]
                        name = name.replace("\n","")
            self.creator = name.rstrip().lstrip()
#                       self.imagetype="exp"
#                       if name == "OoZooN" and os_path.exists("/etc/issue.net"):
#                               f=open("/etc/issue.net")
#                               i=f.read()
#                               f.close()
#                               if (i.find("xperimental") is -1) and (i.find("unstable") is -1):
#                                       self.imagetype="rel"
            cdate = str(datetime.date.today())
            ctime = str(time.strftime("%H-%M"))
            suggested_backupname = name
#                       if config.plugins.dbackup.backupdeb.value:
#                               suggested_backupname=suggested_backupname+"-deb"
            if config.plugins.dbackup.backupid.value != "none":
                if config.plugins.dbackup.backupid.value != "user":
                    suggested_backupname = suggested_backupname + "-%s" % config.plugins.dbackup.backupid.value
                else:
                    suggested_backupname = suggested_backupname + "-%s" % (config.plugins.dbackup.backupuserid.value.rstrip().lstrip().replace(" ","_"))
            if config.plugins.dbackup.backupboxtype.value:
                suggested_backupname = suggested_backupname + "-" + self.boxtype
#                       if config.plugins.dbackup.backupimagetype.value:
#                               suggested_backupname=suggested_backupname+"-"+self.imagetype
            if config.plugins.dbackup.backupdate.value:
                suggested_backupname = suggested_backupname + "-" + cdate
            if config.plugins.dbackup.backuptime.value:
                suggested_backupname = suggested_backupname + "-" + ctime
            if config.plugins.dbackup.flashtool.value == "rescue":
                suggested_backupname = "backup"
            cprint("suggested backupname %s" % suggested_backupname)
            blanks = ""
            i = 0
            blanks_len = int(config.plugins.dbackup.backupblanks.value)
            while i < blanks_len:
                blanks = blanks + " "
                i += 1
            length_blanks = len(blanks)
            cprint("BLANKS %d" % length_blanks)
            suggested_backupname = suggested_backupname + blanks
            blanks_len = blanks_len + 60
            return """
                    <html>
                    %s<br>
                    <u>%s</u><br><br>
                    %s:<br><br>
                    %s<hr>
                    %s @ Dreambox<br>
                    <form method="GET">
                    <select name="file">%s
                    <input type="reset" size="100px">
                    <input name="command" type="submit" size=="100px" title=\"%s\" value="%s">
                    </select>
                    </form>
                    <img src="/web-data/img/dbackup.png" alt="%s ..."/><br><br>
                    <hr>
                    %s & %s @ Dreambox<br>
                    <form method="GET">
                    <select name="directory">%s
                    <input name="file" type="text" size="60" maxlength="%d" value="%s">
                    <input type="reset" size="100px">
                    <input name="command" type="submit" size=="100px" title=\"%s\" value="%s">
                    </select>
                    </form>
                    <img src="/web-data/img/ring.png" alt="%s ..."/><br><br>
                    <hr>
            """ % (header_string,plugin_string,info_header,disclaimer_wstring,fileupload_string, htmlnfi,flashing_string, "Flashing",flashing_string,backupdirectory_string,backupimage_string,htmlbackup,blanks_len,suggested_backupname,backup_string,"Backup",backup_string)
        else:
            if command[0] == "Flashing":
                k = open("/proc/cmdline","r")
                cmd = k.read()
                k.close()
                if self.boxtype == "dm520":
                    rootfs = "root=ubi0:dreambox-rootfs"
                else:
                    rootfs = "root=/dev/mmcblk0"
                if os_path.exists("/.bainfo"):
                    return header_string + noflashing_string
                elif os_path.exists("/.lfinfo"):
                    return header_string + noflashing_string
                elif cmd.find(rootfs) == -1:
                    return header_string + noflashing_string
                # file command is received and we are in Flash - let the fun begin ...
                self.nfifile = file[0]
                if self.nfifile != "rescue" and self.nfifile != "recovery" and self.nfifile.find(self.boxtype) == -1:
                    return header_string + noboxtype_string
                if os_path.exists(self.nfifile):
                    if self.nfifile.endswith(".tar.gz"):
                        cprint("is flashing now %s" % self.nfifile)
                        FlashingImage(self.nfifile,True)
                        return dbackup_flashing
                    elif self.nfifile.endswith(".tar.xz"):
                        if os_path.exists("/usr/bin/xz"):
                            cprint("is flashing now %s" % self.nfifile)
                            FlashingImage(self.nfifile,True)
                            return dbackup_flashing
                        else:
                            cprint("xz binary missing")
                            return header_string + noxz_string
                    elif self.nfifile.endswith(".tar.bz2"):
                        cprint("is flashing now %s" % self.nfifile)
                        FlashingImage(self.nfifile,True)
                        return dbackup_flashing
                    elif self.nfifile.endswith(".tar"):
                        cprint("is flashing now %s" % self.nfifile)
                        FlashingImage(self.nfifile,True)
                        return dbackup_flashing
                    else:
                        cprint("wrong filename")
                        return header_string + notar_string
                else:
                    if self.nfifile == "recovery":
                        cprint("is flashing now %s" % self.nfifile)
                        FlashingImage(self.nfifile,True)
                        return dbackup_flashing
                    else:
                        cprint("filename not found")
                        return header_string + notar_string

            elif command[0] == "Backup":
                if os_path.exists("/.bainfo"):
                    return header_string + " " + barryallen_string + ", " + dbackup_backbutton
                elif os_path.exists("/.lfinfo"):
                    return header_string + " " + lowfat_string + ", " + dbackup_backbutton
                if config.plugins.dbackup.flashtool.value == "rescue":
                    path = "/data/.recovery"
                    if not os_path.exists("/data"):
                        os_mkdir("/data")
                    os.system("umount %s; mount %s /data" % (dreambox_data, dreambox_data))
                    os_system("mount -o remount,async /data")
                    f = open("/proc/mounts","r")
                    mounts = f.read()
                    f.close()
                    if mounts.find("/data") == -1:
                        return header_string + " " + mounted_string % path + ", " + dbackup_backbutton
                    if not os_path.exists("/data/.recovery"):
                        os_mkdir("/data/.recovery")
                    if os_path.exists("/data/.recovery/backup.tar.gz"):
                        os_remove("/data/.recovery/backup.tar.gz")
                    self.backupname = "backup"
                else:
                    self.backupname = file[0].replace(" ","").replace("[","").replace("]","").replace(">","").replace("<","").replace("|","").rstrip().lstrip()
                    if self.backupname.find(self.boxtype) == -1:
                        self.backupname = self.backupname + "-" + self.boxtype
                    path = directory[0]
                if config.plugins.dbackup.flashtool.value != "rescue":
                    if not os_path.exists(path):
                        os_system("ls %s" % path)
                    sp = []
                    sp = path.split("/")
                #       print(sp)
                    if len(sp) > 1:
                        if sp[1] != "media" and sp[1] != "autofs" and sp[1] != "data":
                            cprint("NOT #1 %s" % sp[1])
                            return header_string + " " + mounted_string % path + ", " + dbackup_backbutton
                    if sp[1] != "data":
                        f = open("/proc/mounts", "r")
                        m = f.read()
                        f.close()
                        if m.find("/media/%s" % sp[2]) == -1 and m.find("/autofs/%s" % sp[2]) == -1:
                            cprint("NOT #2 %s" % sp[2])
                            return header_string + " " + mounted_string % path + ", " + dbackup_backbutton
                path = path.lstrip().rstrip("/").rstrip().replace(" ","")
                config.plugins.dbackup.backuplocation.value = path
                config.plugins.dbackup.backuplocation.save()
                if not os_path.exists(config.plugins.dbackup.backuplocation.value):
                    os_mkdir(config.plugins.dbackup.backuplocation.value,0o777)
                if os_path.exists("%s/%s.%s" % (config.plugins.dbackup.backuplocation.value,self.backupname,config.plugins.dbackup.backuptool.value)):
                    cprint("filename already exists")
                    return header_string + self.backupname + "." + config.plugins.dbackup.backuptool.value + " " + _("already exists,") + " " + dbackup_backbutton
                else:
                    if self.backupname.endswith(".tar") or self.backupname.endswith(".tar.gz") or self.backupname.endswith(".tar.bz2") or self.backupname.endswith(".tar.xz") or len(self.backupname) < 1:
                        cprint("filename with .tar.*")
                        return header_string + notar_string + ", " + dbackup_backbutton
                    elif self.backupname.find(" ") != -1:
                        cprint("filename with blank")
                        return header_string + notar_string + ", " + dbackup_backbutton
                    else:
                        # backupfile request
                        self.backuptime = 0
                        self.TimerBackup = eTimer()
                        self.TimerBackup.stop()
                        if not os_path.exists("/var/lib/opkg/status"):
                            self.TimerBackup_conn = self.TimerBackup.timeout.connect(self.backupFinishedCheck)
                        else:
                            self.TimerBackup.callback.append(self.backupFinishedCheck)
                        self.TimerBackup.start(1000,True)
                        BackupImage(self.backupname)
                        return header_string + dbackup_backuping
            else:
                cprint("unknown command")
                return header_string + _("nothing entered")

    def backupFinishedCheck(self):
        global dbackup_progress
        self.backuptime = self.backuptime + 1
        if not os_path.exists(dbackup_backup):
                # not finished - continue checking ...
            rsize = 0
            if os_path.exists("%s/%s.%s" % (config.plugins.dbackup.backuplocation.value, self.backupname, config.plugins.dbackup.backuptool.value)):
                rsize = os_path.getsize("%s/%s.%s" % (config.plugins.dbackup.backuplocation.value, self.backupname, config.plugins.dbackup.backuptool.value))
            total_size = rsize
            st = os_statvfs("/")
            rused = (st.f_blocks - st.f_bfree) * st.f_frsize
            if self.boxtype == "dm520":
                used = rused * 3
            else:
                used = rused
            if used < 0:
                used = 0
            cprint("total size %d used %d" % (total_size,used))
            if total_size > 0:
                if config.plugins.dbackup.backuptool.value == "tar.xz":
                    dbackup_progress = dbackup_tarxz * total_size / used
                elif config.plugins.dbackup.backuptool.value == "tar.gz":
                    dbackup_progress = dbackup_targz * total_size / used
                elif config.plugins.dbackup.backuptool.value == "tar.bz2":
                    dbackup_progress = dbackup_tarbz2 * total_size / used
                else:
                    dbackup_progress = dbackup_tar * total_size / used
                dbackup_progress = dbackup_progress / 5 # webif has shorter progress bar
            else:
                dbackup_progress = self.backuptime / 10
            cprint("checked if backup is finished ...")
            self.TimerBackup.start(1000,True)
        else:
            cprint("found finished backup ...")
            dbackup_progress = 0
            self.TimerBackup = eTimer()
            self.TimerBackup.stop()
            if os_path.exists(dbackup_busy):
                os_remove(dbackup_busy)
            f = open(dbackup_backup)
            line = f.readline()
            f.close()
            os_remove(dbackup_backup)
            sp = []
            sp = line.split(" ")
            #print(sp)
            length = len(sp)
            size = ""
            image = ""
            path = ""
            if length > 0:
                sp2 = []
                sp2 = sp[length - 1].split("/")
                size = sp2[0].rstrip().lstrip()
                #print(sp2)
                length = len(sp2)
                if length > 0:
                    image = sp2[length - 1]
                    path = line.replace(size,"").replace(image,"")
                    image = image.replace(".tar.gz\n","").replace(".tar.xz\n","").replace(".tar.bz2\n","").replace(".tar\n","")
                    image = image.rstrip().lstrip()
            cprint("found backup %s" % line)
            cprint("finished webif backup")

class FlashingImage(Screen):
    def __init__(self,flashimage, lock=False):
        global dreambox_data
        self.flashimage = flashimage
        cprint("does flashing %s" % self.flashimage)
        self.boxtype = getBoxtype()
        self.doFlashing()
        if lock and self.flashimage != "rescue":
            self.lockFlashing()

    def doFlashing(self):
        self.container = eConsoleAppContainer()
        open(dbackup_busy, 'a').close()
        if config.plugins.dbackup.flashtool.value == "rescue":
            command = "#!/bin/sh -x\n"
            command += "echo rescue > /proc/stb/fp/boot_mode\n"
            command += "shutdown -r now\n"
            command += "exit 0\n"
            b = open(dbackup_script,"w")
            b.write(command)
            b.close()
            os_chmod(dbackup_script, 0o755)
            cprint("%s created and is now booting to recue mode\n" % (dbackup_script))
            os_system("/sbin/start-stop-daemon -S -b -n dbackup.sh -x %s" % dbackup_script)
        elif config.plugins.dbackup.flashtool.value == "recovery":
            command = "#!/bin/sh -x\n"
            command += "mkdir /data\n"
            command += "umount %s; mount %s /data\n" % (dreambox_data, dreambox_data)
            command += "mount -o remount,async /data\n"
            command += "mkdir /data/.recovery\n"
            command += "cp %s /data/.recovery/backup.tar.gz\n" % self.flashimage
            command += "umount /data\n"
            command += "init 4\n"
            command += "sleep 5\n"
            command += "shutdown -h now\n"
            command += "exit 0\n"
            b = open(dbackup_script,"w")
            b.write(command)
            b.close()
            os_chmod(dbackup_script, 0o755)
            cprint("%s created and is now flashing %s\n" % (dbackup_script,self.flashimage))
            os_system("/sbin/start-stop-daemon -S -b -n dbackup.sh -x %s" % dbackup_script)
        elif config.plugins.dbackup.flashtool.value == "usb":
            cprint("recovery usb stick is not yet supported")
        else:
            tmp_extract = "%s/tmp" % config.plugins.dbackup.backuplocation.value
            if os_path.exists(tmp_extract):
                shutil.rmtree(tmp_extract,True)
            if not os_path.exists(tmp_extract):
                os_mkdir(tmp_extract)
            tarimage = "%s/tmp/rootfs.tar" % config.plugins.dbackup.backuplocation.value
            command = "#!/bin/sh -x\n"
            command += "exec > %s 2>&1\n" % dbackup_log
            command += "cat %s\n" % dbackup_script
            command += "df -h\n"
            command += "sync; sync; sync; echo 3 > /proc/sys/vm/drop_caches\n"
            if self.flashimage == "rescue":
                # default values from DMM recovery Image
                self.flashimage = "none"
                command += "/usr/sbin/update-rescue -v\n"
            if self.flashimage == "recovery":
                # default values from DMM recovery Image
                url = "http://dreamboxupdate.com/download/recovery/%s/release" % self.boxtype.replace("dream","")
                img = "dreambox-image-%s.tar.xz" % self.boxtype.replace("dream","")
                if not os_path.exists("/data"):
                    os_mkdir("/data")
                os.system("umount %s; mount %s /data" % (dreambox_data, dreambox_data))
                if os_path.exists("/data/.recovery/recovery"):
                    r = open("/data/.recovery/recovery")
                    line = r.readline()
                    while (line):
                        line = r.readline()
                        if line.startswith("BASE_URI="):
                            url = line.replace("BASE_URI=","").rstrip("\n")
                        if line.startswith("FILENAME="):
                            img = line.replace("FILENAME=","").rstrip("\n")
                    r.close()
                recovery_image = "%s/%s" % (url,img)
                self.flashimage = "%s/%s" % (config.plugins.dbackup.backuplocation.value,img)
                cprint("downloads %s to %s" % (recovery_image,self.flashimage))
                os_system("umount /data")
                command += "wget %s -O %s\n" % (recovery_image,self.flashimage)
            if self.flashimage.endswith(".tar.gz"):
                command += "pigz -d -f -c \"%s\" > \"%s\"\n" % (self.flashimage,tarimage)
            elif self.flashimage.endswith(".tar.xz"):
                command += "xz -d -c \"%s\" > \"%s\"\n" % (self.flashimage,tarimage)
            elif self.flashimage.endswith(".tar.bz2"):
                if os_path.exists("/usr/bin/pbzip2"):
                    command += "/usr/bin/pbzip2 -d -k -c \"%s\" > \"%s\"\n" % (self.flashimage,tarimage)
                else:
                    command += "bunzip2 -c -f \"%s\" > \"%s\"\n" % (self.flashimage,tarimage)
            elif self.flashimage.endswith(".zip"):
                command += "unzip \"%s\" -d %s/tmp\n" % (self.flashimage, config.plugins.dbackup.backuplocation.value)
                bz2image = "%s/tmp/%s/rootfs.tar.bz2" % (config.plugins.dbackup.backuplocation.value,self.boxtype)
                command += "if [ -e %s/tmp/%s ]; then\n" % (config.plugins.dbackup.backuplocation.value,self.boxtype)
                command += "bunzip2 -c -f \"%s\" > \"%s\"\n" % (bz2image,tarimage)
                command += "else\n"
                sp = []
                sp = self.flashimage.split("/")
                ll = len(sp)
                flashimagename = sp[ll - 1]
                command += "xz -d -c \"%s/tmp/%s\" > \"%s\"\n" % (config.plugins.dbackup.backuplocation.value, flashimagename.replace(".zip",".rootfs.tar.xz"),tarimage)
                command += "fi\n"
            elif self.flashimage.endswith(".bin"):
                if config.plugins.dbackup.verbose.value:
                    command += "flash-rescue -v %s\n" % (self.flashimage)
                else:
                    command += "flash-rescue %s\n" % (self.flashimage)
            elif self.flashimage.endswith("none"):
                pass
            else:
                command += "cp %s %s\n" % (self.flashimage, tarimage)
            if not self.flashimage.endswith(".bin") and not self.flashimage.endswith("none"):
                command += "rm %s\n" % dbackup_busy
                if config.plugins.dbackup.stopped.value:
                    stopping = "kill"
                else:
                    stopping = ""
                if self.boxtype == "dm900" or self.boxtype == "dm920":
                    command += "%s/armhf/swaproot \"%s\" %s\n" % (dbackup_plugindir, tarimage, stopping)
                elif self.boxtype == "dreamone" or self.boxtype == "dreamtwo":
                    command += "%s/arm64/swaproot \"%s\" %s\n" % (dbackup_plugindir, tarimage, stopping)
                else:
                    command += "%s/mipsel/swaproot \"%s\" %s\n" % (dbackup_plugindir, tarimage, stopping)
            command += "rm %s\n" % dbackup_busy
            command += "exit 0\n"
            b = open(dbackup_script,"w")
            b.write(command)
            b.close()
            os_chmod(dbackup_script, 0o755)
            cprint("%s created and is now flashing %s" % (dbackup_script,self.flashimage))
#                       os_system("/sbin/start-stop-daemon -S -b -n dbackup.sh -x %s" % dbackup_script)
            cmd = "/sbin/start-stop-daemon -S -b -n dbackup.sh -x %s" % dbackup_script
            self.container.execute(cmd)

    def lockFlashing(self):
        cprint("FLASHING LOCKS")
        if self.boxtype != "dm520" and self.boxtype != "dreamone":
            eDBoxLCD.getInstance().lock(True)
        eRCInput.getInstance().lock()
        fbClass.getInstance().lock()

class BackupImage(Screen):
    def __init__(self,backupname):
        cprint("does backup")
        self.boxtype = getBoxtype()
        open(dbackup_busy, 'a').close()
        self.backupname = backupname
#               self.imagetype=imagetype
#               self.creator=creator
        exclude = " --exclude=smg.sock --exclude=msg.sock "
        if config.plugins.dbackup.epgdb.value:
            exclude += " --exclude=epg.db"
        if config.plugins.dbackup.mediadb.value:
            exclude += " --exclude=media.db"
        if config.plugins.dbackup.timers.value:
            exclude += " --exclude=timers.xml"
        if config.plugins.dbackup.settings.value:
            exclude += " --exclude=settings"
        for name in os_listdir("/lib/modules"):
            self.kernel = name
        self.kernel = self.kernel.replace("\n","").replace("\l","").replace("\0","")
        cprint("boxtype %s kernel %s" % (self.boxtype,self.kernel))
        # don't backup left overs from flashing ...
        tmp_extract = "%s/tmp" % config.plugins.dbackup.backuplocation.value
        if os_path.exists(tmp_extract):
            shutil.rmtree(tmp_extract,True)

        # here comes the fun ...

        command = "#!/bin/sh -x\n"
        command += "exec > %s 2>&1\n" % dbackup_log
        command += "date +\%s\n"
        command += "cat %s\n" % dbackup_script
        command += "df -h\n"
        if os_path.exists("/etc/init.d/openvpn"):
            command += "/etc/init.d/openvpn stop\n"
        if config.plugins.dbackup.aptclean.value:
            command += "apt-get clean\n"

        # make root filesystem ...

        command += "umount /tmp/root\n"
        command += "rmdir /tmp/root\n"
        command += "mkdir /tmp/root\n"
        command += "mount -o bind / /tmp/root\n"
        if config.plugins.dbackup.backuplocation.value == "/media/DREAMFLASH":
            command += "mount -o rw,async,remount /media/DREAMFLASH\n"
        if config.plugins.dbackup.picons.value and os_path.exists("/usr/share/enigma2/picon"):
            command += "mount -t tmpfs tmpfs /tmp/root/usr/share/enigma2/picon\n"
        target = "%s/%s.tar" % (config.plugins.dbackup.backuplocation.value, backupname)
        # tar.gz is now default
#               if self.boxtype == "dm520":
#                       command +="dd if=/dev/zero of=%s/swapfile bs=1024 count=512000\n" % config.plugins.dbackup.backuplocation.value
#                       command +="mkswap %s/swapfile\n" % config.plugins.dbackup.backuplocation.value
#                       command +="swapon %s/swapfile\n" % config.plugins.dbackup.backuplocation.value
        if config.plugins.dbackup.backupsettings.value:
            command += "DATE=`date +\"%Y-%m-%d\"`\n"
            command += "BACKUP=\"%s/\"$DATE\"-enigma2settingsbackup.tar.gz\"\n" % config.plugins.dbackup.backuplocation.value
            command += "rm $BACKUP > /dev/null 2>&1\n"
            try:
                backupdirs = ' '.join(config.plugins.configurationbackup.backupdirs.value)
            except:
                backupdirs = " /etc/enigma2/ /etc/hostname"
            cprint("setings backup %s" % backupdirs)
            if os_path.exists("/etc/wpa_supplicant.conf"):
                command += "tar -czvf $BACKUP %s /etc/wpa_supplicant.conf /etc/resolv.conf\n" % backupdirs
            else:
                command += "tar -czvf $BACKUP %s /etc/resolv.conf\n" % backupdirs
        if config.plugins.dbackup.backuptool.value == "tar.gz":
            if config.plugins.dbackup.verbose.value:
                command += "tar -cvf - %s -C /tmp/root . | pigz -%s  > %s.gz\n" % (exclude, config.plugins.dbackup.gzcompression.value, target)
            else:
                command += "tar -cf - %s -C /tmp/root . | pigz -%s  > %s.gz\n" % (exclude, config.plugins.dbackup.gzcompression.value, target)
        elif config.plugins.dbackup.backuptool.value == "tar.xz":
            if config.plugins.dbackup.verbose.value:
                command += "tar %s -cvf - -C /tmp/root . | xz -%s -T 0 -c - > %s.xz\n" % (exclude, config.plugins.dbackup.xzcompression.value, target)
            else:
                command += "tar %s -cf - -C /tmp/root . | xz -%s -T 0 -c - > %s.xz\n" % (exclude, config.plugins.dbackup.xzcompression.value, target)
        elif config.plugins.dbackup.backuptool.value == "tar.bz2":
            if config.plugins.dbackup.verbose.value:
                if os_path.exists("/usr/bin/pbzip2"):
                    command += "tar %s -cvf - -C /tmp/root . | /usr/bin/pbzip2 -b100 -f -c > %s.bz2\n" % (exclude,target)
                else:
                    command += "tar %s -cvjf %s.bz2 -C /tmp/root .\n" % (exclude, target)
            else:
                if os_path.exists("/usr/bin/pbzip2"):
                    command += "tar %s -cf - -C /tmp/root . | /usr/bin/pbzip2 -b100 -f -c > %s.bz2\n" % (exclude,target)
                else:
                    command += "tar %s -cjf %s.bz2 -C /tmp/root .\n" % (exclude, target)
        else:
            if config.plugins.dbackup.verbose.value:
                command += "tar -cvf %s %s -C /tmp/root .\n" % (target, exclude)
            else:
                command += "tar -cf %s %s -C /tmp/root .\n" % (target, exclude)
        if config.plugins.dbackup.picons.value:
            command += "umount /tmp/root/usr/share/enigma2/picon\n"
        command += "umount /tmp/root\n"
        command += "rmdir /tmp/root\n"

        if os_path.exists("/etc/init.d/openvpn"):
            command += "/etc/init.d/openvpn start\n"

        command += "chmod 777 %s.*\n" % (target)
        command += "ls -alh %s*\n" % (target)
        command += "du -h %s* > %s\n" % (target,dbackup_backup)
        command += "df -h\n"
#               if self.boxtype == "dm520":
#                       command +="swapoff %s/swapfile\n" % config.plugins.dbackup.backuplocation.value
#                       command +="rm %s/swapfile\n" % config.plugins.dbackup.backuplocation.value
        command += "rm %s\n" % dbackup_busy
        command += "date +\%s\n"
        command += "exit 0\n"
    #       print(command)
        b = open(dbackup_script,"w")
        b.write(command)
        b.close()
        os_chmod(dbackup_script, 0o755)
        self.container = eConsoleAppContainer()
        start_cmd = "/sbin/start-stop-daemon -K -n dbackup.sh -s 9; /sbin/start-stop-daemon -S -b -n dbackup.sh -x %s" % (dbackup_script)
        if config.plugins.dbackup.exectool.value == "daemon":
            cprint("daemon %s" % dbackup_script)
            self.container.execute(dbackup_script)
        elif config.plugins.dbackup.exectool.value == "system":
            cprint("system %s" % start_cmd)
            os_system(start_cmd)
        if config.plugins.dbackup.exectool.value == "container":
            cprint("container %s" % start_cmd)
            self.container.execute(start_cmd)
        config.plugins.dbackup.lastbackup.value = int(time.time())
        config.plugins.dbackup.lastbackup.save()

def clean_dBackup():
    if int(config.plugins.dbackup.cleanlastbackup.value) == 0:
        cprint("automatic cleanup in setup deactivated - max. number of backups = 0")
        return
    cprint("automatic cleanup")

    #cleanup for settingsbackup
    backupname_mask = automaticBackupName(mask=True) + "." + config.plugins.dbackup.backuptool.value
    backuplocation = config.plugins.dbackup.backuplocation.value
    #cprint("location %s name %s" % (backuplocation, backupname_mask))
    backupList = glob(backuplocation + '/' + backupname_mask)
    backupList.sort(reverse=True)
    #cprint("backupList Count all: %d" % len(backupList))
    keepbackupList = backupList[:int(config.plugins.dbackup.cleanlastbackup.value)]
    del backupList[:int(config.plugins.dbackup.cleanlastbackup.value)]

    BgFileEraser = eBackgroundFileEraser.getInstance()

    cprint("backupList Count to keep: %d" % len(keepbackupList))
    #for x in range(len(keepbackupList)):
    #       print("keep:" + keepbackupList[x] + "\n")
    #cprint("backupList Count to delete: %s" % len(backupList))
    for x in range(len(backupList)):
        if os_path.exists(backupList[x]):
            #print("marked do delete:" + backupList[x] + "\n")
            BgFileEraser.erase(backupList[x])

    #cleanup for settingsbackup
    if config.plugins.dbackup.backupsettings.value:
        backupList = glob(backuplocation + '/*-enigma2settingsbackup.tar.gz')
        backupList.sort(reverse=True)
        #cprint("settingsbackupList Count all: %d" % len(backupList))
        keepbackupList = backupList[:int(config.plugins.dbackup.cleanlastbackup.value)]
        del backupList[:int(config.plugins.dbackup.cleanlastbackup.value)]

        cprint("settingsbackupList Count to keep: %d" % len(keepbackupList))
        #for x in range(len(keepbackupList)):
        #       print("keep:" + keepbackupList[x] + "\n")
        cprint("settingsbackupList Count to delete: %d" % len(backupList))
        for x in range(len(backupList)):
            if os_path.exists(backupList[x]):
                #print("marked do delete:" + backupList[x] + "\n")
                BgFileEraser.erase(backupList[x])

###############################################################################
# dBackup Check by gutemine
###############################################################################

class dBackupChecking(Screen):
    if sz_w == 1920:
        skin = """
        <screen name="dBackupChecking" position="center,170" size="1200,820" title="choose NAND Flash Check" >
        <widget name="logo" position="20,10" size="150,60" />
        <widget backgroundColor="#9f1313" font="Regular;30" halign="center" name="buttonred" position="190,10" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2" size="240,60" valign="center" />
        <widget backgroundColor="#1f771f" font="Regular;30" halign="center" name="buttongreen" position="440,10" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2" size="240,60" valign="center" />
        <widget backgroundColor="#a08500" font="Regular;30" halign="center" name="buttonyellow" position="690,10" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2" size="240,60" valign="center" />
        <widget backgroundColor="#18188b" font="Regular;30" halign="center" name="buttonblue" position="940,10" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2" size="240,60" valign="center" />
        <eLabel backgroundColor="grey" position="20,80" size="1160,1" />
        <widget enableWrapAround="1" name="menu" position="10,90" scrollbarMode="showOnDemand" size="1160,720" />
        </screen>"""
    else:
        skin = """
        <screen name="dBackupChecking" position="center,120" size="800,520" title="choose NAND Flash Check" >
        <widget name="logo" position="10,5" size="100,40" />
        <widget backgroundColor="#9f1313" font="Regular;19" halign="center" name="buttonred" position="120,5" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2" size="160,40" valign="center" />
        <widget backgroundColor="#1f771f" font="Regular;19" halign="center" name="buttongreen" position="290,5" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2" size="160,40" valign="center" />
        <widget backgroundColor="#a08500" font="Regular;19" halign="center" name="buttonyellow" position="460,5" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2" size="160,40" valign="center" />
        <widget backgroundColor="#18188b" font="Regular;19" halign="center" name="buttonblue" position="630,5" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2" size="160,40" valign="center" />
        <eLabel backgroundColor="grey" position="10,60" size="780,1" />
        <widget name="menu" position="10,60" size="780,450" enableWrapAround="1" scrollbarMode="showOnDemand" />
        </screen>"""

    def __init__(self, session, args=0):
        global dreambox_data
        self.skin = dBackupChecking.skin
        self.session = session
        Screen.__init__(self, session)
        self.menu = args
        self.boxtype = getBoxtype()
        self.onShown.append(self.setWindowTitle)
        flashchecklist = []
        self["buttonred"] = Label(_("Exit"))
        self["buttonyellow"] = Label(info_header)
        self["buttongreen"] = Label(_("OK"))
        self["buttonblue"] = Label(_("About"))
        self["logo"] = Pixmap()
        if not os_path.exists("/data"):
            os_mkdir("/data")
        if self.boxtype != "dm520":
            flashchecklist.append((_("check root"), "/sbin/fsck.ext4 -f -v -y /dev/mmcblk0p1"))
            flashchecklist.append((_("check & repair recovery"), "/sbin/fsck.ext4 -f -v -y /dev/mmcblk0p2"))
            if os_path.exists("/sbin/badblocks"):
                flashchecklist.append((_("badblocks recovery > 1min"), "/sbin/fsck.ext4 -f -c -v -y /dev/mmcblk0p2"))
            else:
                flashchecklist.append((_("no badblocks binary - get e2fsprogs"), "none"))
        else:
            if dreambox_data != "none":
                flashchecklist.append((_("check & repair recovery"), "umount %s; /sbin/fsck.ext4 -f -v -y %s" % (dreambox_data, dreambox_data)))
                if os_path.exists("/sbin/badblocks"):
                    flashchecklist.append((_("badblocks recovery > 1min"), "umount %s; /sbin/fsck.ext4 -f -c -v -y %s" % (dreambox_data, dreambox_data)))
                else:
                    flashchecklist.append((_("no badblocks binary - get e2fsprogs"), "none"))
            else:
                flashchecklist.append((_("create recovery USB stick"), "recovery"))
        #flashchecklist.append((_("clean apt cache"), "apt-get -v; apt-get clean"))
        if self.boxtype != "dm520":
            flashchecklist.append((_("check defragmentation root"), "ln -sfn /dev/mmcblk0p1 /dev/root; %s/bin/e4defrag -c /dev/root" % dbackup_plugindir))
            flashchecklist.append((_("defragment root"), "ln -sfn /dev/mmcblk0p1 /dev/root; %s/bin/e4defrag /dev/root" % dbackup_plugindir))
            flashchecklist.append((_("check defragmentation recovery"), "mount /dev/mmcblk0p2 /data; %s/bin/e4defrag -c /dev/mmcblk0p2; umount /data" % dbackup_plugindir))
            flashchecklist.append((_("defragment recovery"), "mount /dev/mmcblk0p2 /data; %s/bin/e4defrag /dev/mmcblk0p2; umount /data" % dbackup_plugindir))
        else:
            if dreambox_data != "none":
                flashchecklist.append((_("check defragmentation recovery"), "mount %s /data; %s/bin/e4defrag -c %s; umount /data" % (dreambox_data, dbackup_plugindir, dreambox_data)))
                flashchecklist.append((_("defragment recovery"), "mount %s /data; %s/bin/e4defrag %s; umount /data" % (dreambox_data, dbackup_plugindir, dreambox_data)))
        m = open("/proc/mounts")
        mounts = m.read()
        m.close()
        if mounts.find("/media/hdd ext4") != -1:
            flashchecklist.append((_("check defragmentation Harddisk"), "%s/bin/e4defrag -c /media/hdd" % dbackup_plugindir))
            flashchecklist.append((_("defragment Harddisk"), "%s/bin/e4defrag -v /media/hdd" % dbackup_plugindir))

        self["menu"] = MenuList(flashchecklist)
        self["setupActions"] = ActionMap(["ColorActions", "SetupActions"],
                {
                "ok": self.go,
                "green": self.go,
                "red": self.close,
                "yellow": self.legend,
                "blue": self.about,
                "cancel": self.close,
                })

    def go(self):
        self.checking = self["menu"].l.getCurrentSelection()[0]
        self.command = self["menu"].l.getCurrentSelection()[1]
#       print(self.checking, self.command)
        if not self.command is None and self.command == "recovery":
            cprint("create recovery")
            device_string = _("Select device for recovery USB stick")
            self.session.openWithCallback(self.askForDevice,ChoiceBox,device_string,self.getDeviceList())
            return
        if not self.command is None and self.command != "none":
            self.session.open(Console, self.checking,[(self.command)])

    def setWindowTitle(self):
        self["logo"].instance.setPixmapFromFile("%s/dbackup.png" % dbackup_plugindir)
        self.setTitle(backup_string + " & " + flashing_string + " V%s " % dbackup_version + checking_string)

    def legend(self):
        title = _("If you install e2fsprogs the badblocks binary will allow to check and mark also bad blocks")
        self.session.open(MessageBox, title, MessageBox.TYPE_INFO)

    def about(self):
        self.session.open(dBackupAbout)

    def getDeviceList(self):
        found = False
        f = open("/proc/partitions","r")
        devlist = []
        line = f.readline()
        line = f.readline()
        sp = []
        while (line):
            line = f.readline()
            if line.find("sd") != -1:
                sp = line.split()
            #       print(sp)
                devsize = int(sp[2])
                mbsize = devsize / 1024
                devname = "/dev/%s" % sp[3]
            #       print(devname, devsize)
                if len(devname) == 8 and mbsize < 36000 and mbsize > 480:
                    # only sticks from 512 MB up to 32GB are used as recovery sticks
                    found = True
                    devlist.append(("%s %d %s" % (devname,mbsize,"MB"), devname,mbsize))
        f.close()
        if not found:
            devlist.append(("no device found, shutdown, add device and reboot", "nodev", 0))
        return devlist

    def askForDevice(self,device):
        if device is None:
            self.session.open(MessageBox, _("Sorry, no device choosen"), MessageBox.TYPE_ERROR)
        elif device[1] == "nodev":
            self.session.open(MessageBox, _("Sorry, no device found"), MessageBox.TYPE_ERROR)
        else:
            self.device = device[1]
            self.session.openWithCallback(self.doRecoveryStick,MessageBox,_("Are you sure that you want to erase now %s ?") % (self.device), MessageBox.TYPE_YESNO)

    def doRecoveryStick(self,option):
        if option is False:
            self.session.open(MessageBox, _("Sorry, Erasing of %s was canceled!") % self.device, MessageBox.TYPE_ERROR)
        else:
            if not os_path.exists("%s1" % self.device):
                self.session.open(MessageBox, _("Sorry, %s has no primary partition") % self.device, MessageBox.TYPE_ERROR)
            else:
                cprint("erases %s1" % self.device)
                cmd = "umount %s1; mkfs.ext4 -L dreambox-data %s1; mkdir /autofs/%s1/backup" % (self.device,self.device,self.device)
                self.session.open(Console, self.checking,[cmd])

class dBackupConfiguration(Screen, ConfigListScreen):
    if sz_w == 1920:
        skin = """
        <screen name="dBackupConfiguration" position="center,170" size="1200,820" title="dBackup Configuration" >
        <widget name="logo" position="20,10" size="150,60" />
        <widget backgroundColor="#9f1313" font="Regular;30" halign="center" name="buttonred" position="190,10" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2" size="240,60" valign="center" />
        <widget backgroundColor="#1f771f" font="Regular;30" halign="center" name="buttongreen" position="440,10" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2" size="240,60" valign="center" />
        <widget backgroundColor="#a08500" font="Regular;30" halign="center" name="buttonyellow" position="690,10" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2" size="240,60" valign="center" />
        <widget backgroundColor="#18188b" font="Regular;30" halign="center" name="buttonblue" position="940,10" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2" size="240,60" valign="center" />
        <eLabel backgroundColor="grey" position="20,80" size="1160,1" />
        <widget enableWrapAround="1" name="config" position="10,90" scrollbarMode="showOnDemand" size="1180,720" />
        </screen>"""
    else:
        skin = """
        <screen name="dBackupConfiguration" position="center,120" size="800,520" title="dBackup Configuration" >
        <widget name="logo" position="10,5" size="100,40" />
        <widget backgroundColor="#9f1313" font="Regular;19" halign="center" name="buttonred" position="120,5" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2" size="160,40" valign="center" />
        <widget backgroundColor="#1f771f" font="Regular;19" halign="center" name="buttongreen" position="290,5" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2" size="160,40" valign="center" />
        <widget backgroundColor="#a08500" font="Regular;19" halign="center" name="buttonyellow" position="460,5" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2" size="160,40" valign="center" />
        <widget backgroundColor="#18188b" font="Regular;19" halign="center" name="buttonblue" position="630,5" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2" size="160,40" valign="center" />
        <eLabel backgroundColor="grey" position="10,50" size="780,1" />
        <widget name="config" position="10,60" size="780,450" enableWrapAround="1" scrollbarMode="showOnDemand" />
        </screen>"""

    def __init__(self, session, args=0):
        Screen.__init__(self, session)

        self.boxtype = getBoxtype()
        self.onShown.append(self.setWindowTitle)
        # explizit check on every entry
        self.onChangedEntry = []

        self.list = []
        ConfigListScreen.__init__(self, self.list, session=self.session, on_change=self.changedEntry)
        self.createSetup()

        self["logo"] = Pixmap()
        self["buttonred"] = Label(_("Exit"))
        self["buttongreen"] = Label(_("OK"))
        self["buttonyellow"] = Label(checking_string)
        self["buttonblue"] = Label(info_header)
        self["setupActions"] = ActionMap(["SetupActions", "ColorActions"],
        {
                "green": self.save,
                "red": self.cancel,
                "yellow": self.checking,
                "blue": self.disclaimer,
                "save": self.save,
                "cancel": self.cancel,
                "ok": self.save,
        })

    def createSetup(self):
        self.list = []
        self.list.append(getConfigListEntry(_("Flashtool"), config.plugins.dbackup.flashtool))
        if config.plugins.dbackup.flashtool.value != "recovery":
            self.list.append(getConfigListEntry(_("Backuptool"), config.plugins.dbackup.backuptool))
        if config.plugins.dbackup.backuptool.value == "tar.xz":
            self.list.append(getConfigListEntry(_("tar.xz") + " " + _("Compression") + " " + _("(0-9)"), config.plugins.dbackup.xzcompression))
        elif config.plugins.dbackup.backuptool.value == "tar.gz":
            self.list.append(getConfigListEntry(_("tar.gz") + " " + _("Compression") + " " + _("(0-9)"), config.plugins.dbackup.gzcompression))
        else:
            pass
#       self.list.append(getConfigListEntry(_("Create signature file"), config.plugins.dbackup.sig))
#       self.list.append(getConfigListEntry(_("Extract loader from Flash"), config.plugins.dbackup.loaderextract))
#       self.list.append(getConfigListEntry(_("Extract kernel from Flash"), config.plugins.dbackup.kernelextract))
#       self.list.append(getConfigListEntry(_("Flashing reboot delay [0-60 sec]"), config.plugins.dbackup.delay))
        self.list.append(getConfigListEntry(_("Flashing with stopped enigma2"), config.plugins.dbackup.stopped))
        self.list.append(getConfigListEntry(_("Choose backup location"), config.plugins.dbackup.backupaskdir))
        self.list.append(getConfigListEntry(_("Check") + " " + _("latest") + " " + _("Backup") + " [" + _("days") + "]", config.plugins.dbackup.latestbackup))
        if int(config.plugins.dbackup.latestbackup.value) > 0:
            self.list.append(getConfigListEntry(_("automatic") + " " + _("Backup"), config.plugins.dbackup.automatic))
        self.list.append(getConfigListEntry(_("automatic") + " " + _("cleanup") + " " + _("(max. number of backups)"), config.plugins.dbackup.cleanlastbackup))
#       self.list.append(getConfigListEntry(_("Imagetype in backupname"), config.plugins.dbackup.backupimagetype))
#       self.list.append(getConfigListEntry(_("Boxtype in backupname"), config.plugins.dbackup.backupboxtype))
        self.list.append(getConfigListEntry(_("deb in backupname").replace("deb","..."), config.plugins.dbackup.backupid))
        if config.plugins.dbackup.backupid.value == "user":
            self.list.append(getConfigListEntry(_("User defined") + ":", config.plugins.dbackup.backupuserid))
        else:
            config.plugins.dbackup.backupuserid.value = "deb                   "
        self.list.append(getConfigListEntry(_("Date in backupname"), config.plugins.dbackup.backupdate))
        self.list.append(getConfigListEntry(_("Time in backupname"), config.plugins.dbackup.backuptime))
        self.list.append(getConfigListEntry(_("Blanks in backupname"), config.plugins.dbackup.backupblanks))
#        if os_path.exists("/var/lib/opkg/status"):
#            self.list.append(getConfigListEntry(_("Clean apt cache before backup"), config.plugins.dbackup.aptclean))
#            self.list.append(getConfigListEntry(_("Exclude epg.db"), config.plugins.dbackup.epgdb))
#            self.list.append(getConfigListEntry(_("Exclude epg.db").replace("epg.db","media.db"), config.plugins.dbackup.mediadb))
        self.list.append(getConfigListEntry(_("Exclude timers"), config.plugins.dbackup.timers))
        self.list.append(getConfigListEntry(_("extra") + " " + _("Settings") + " " + _("Backup"), config.plugins.dbackup.backupsettings))
        self.list.append(getConfigListEntry(_("Exclude settings"), config.plugins.dbackup.settings))
        if os_path.exists("/usr/share/enigma2/picon"):
            self.list.append(getConfigListEntry(_("Exclude picons"), config.plugins.dbackup.picons))
        self.list.append(getConfigListEntry(_("Fading") + " [" + _("seconds") + "]", config.plugins.dbackup.fadetime))
        if int(config.plugins.dbackup.fadetime.value) > 0:
            self.list.append(getConfigListEntry(_("Minimal Fading Transparency"), config.plugins.dbackup.transparency))
#       self.list.append(getConfigListEntry(_("Verbose"), config.plugins.dbackup.verbose))
        self.list.append(getConfigListEntry(_("Sort Imagelist alphabetic"), config.plugins.dbackup.sort))
        self.list.append(getConfigListEntry(_("Show plugin") + " " + _("Settings"), config.plugins.dbackup.showinsettings))
        self.list.append(getConfigListEntry(_("Show plugin") + " " + _("Extension"), config.plugins.dbackup.showinextensions))
        self.list.append(getConfigListEntry(_("Show plugin") + " " + _("Pluginlist"), config.plugins.dbackup.showinplugins))
        self.list.append(getConfigListEntry(_("Display"), config.plugins.dbackup.displayentry))
        self.list.append(getConfigListEntry(_("Recovery Mode"), config.plugins.dbackup.recovering))
        if not os_path.exists("/var/lib/opkg/status"):
            self.list.append(getConfigListEntry(_("Webinterface"), config.plugins.dbackup.webinterface))

        self["config"].list = self.list
        self["config"].l.setList(self.list)

    def changedEntry(self):
        choice = self["config"].getCurrent()
        current = choice[1]
        userdefined = config.plugins.dbackup.backupuserid
        if not choice is None:
            if current != userdefined:
                self.createSetup()

    def setWindowTitle(self):
        self["logo"].instance.setPixmapFromFile("%s/dbackup.png" % dbackup_plugindir)
        self.setTitle(setup_string + " " + backup_string + " & " + flashing_string + " V%s " % dbackup_version + self.boxtype)

    def save(self):
        config.plugins.dbackup.fadetime.save()
        if config.plugins.dbackup.transparency.value > config.osd.alpha.value:
            # current transparency is maximum for faded transparency = no fading
            config.plugins.dbackup.transparency.value = config.osd.alpha.value
            config.plugins.dbackup.transparency.save()
        if config.plugins.dbackup.flashtool.value == "rescue":
            config.plugins.dbackup.backuplocation.value = "/data/.recovery"
            config.plugins.dbackup.backuptool.value = "tar.gz"
        elif config.plugins.dbackup.flashtool.value == "recovery":
            config.plugins.dbackup.backuplocation.value = "/media/DREAMFLASH"
            config.plugins.dbackup.backuptool.value = "tar.xz"
        else:
            # back to normal ...
            if config.plugins.dbackup.backuplocation.value == "/data/.recovery":
                config.plugins.dbackup.backuplocation.value = "/media/hdd/backup"
                config.plugins.dbackup.backuptool.value = "tar.gz"
        if not config.plugins.dbackup.showinsettings.value and not config.plugins.dbackup.showinplugins.value and not config.plugins.dbackup.showinextensions.value:
            config.plugins.dbackup.showinplugins.value = True
            config.plugins.dbackup.showinplugins.save()
        config.plugins.dbackup.backuplocation.save()
        config.plugins.dbackup.backuptool.save()
        for x in self["config"].list:
            x[1].save()
        self.close(True)

    def cancel(self):
        for x in self["config"].list:
            x[1].cancel()
        self.close(False)

    def checking(self):
        # currently disabled ...
        return
        self.session.open(dBackupChecking)

    def disclaimer(self):
        self.session.openWithCallback(self.about,MessageBox, disclaimer_string + "\n\n" + support_string, MessageBox.TYPE_WARNING)

    def about(self,answer):
        self.session.open(dBackupAbout)

class dBackupAbout(Screen):
    if sz_w == 1920:
        skin = """
        <screen name="dBackupAbout" position="center,center" size="1200,500" title="About dBackup" >
        <eLabel backgroundColor="grey" position="20,10" size="1160,1" />
        <widget name="aboutdbackup" foregroundColor="yellow" position="20,30" size="1160,50" halign="center" font="Regular;36"/>
        <eLabel backgroundColor="grey" position="20,100" size="1160,1" />
        <ePixmap position="400,160" size="400,105" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/dBackup/dreamboxupdate.png"/>
        <widget name="freefilesystem" position="50,110" size="300,260" valign="center" halign="center" font="Regular;32"/>
        <widget name="freememory" position="850,110" size="300,260" valign="center" halign="center" font="Regular;32"/>
        <eLabel backgroundColor="grey" position="20,410" size="1160,1" />
        <widget backgroundColor="#9f1313" font="Regular;30" halign="center" name="buttonred" position="20,420" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2" size="350,60" valign="center" />
        <widget backgroundColor="#1f771f" font="Regular;30" halign="center" name="buttongreen" position="830,420" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2" size="350,60" valign="center" />
        </screen>"""
    else:
        skin = """
        <screen name="dBackupAbout" position="center,center" size="720,350" title="About dBackup" >
        <eLabel backgroundColor="grey" position="10,10" size="700,1" />
        <widget name="aboutdbackup" position="10,20" size="700,30" halign="center" foregroundColor="yellow" font="Regular;24"/>
        <eLabel backgroundColor="grey" position="10,60" size="700,1" />
        <ePixmap position="260,100" size="200,52" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/dBackup/dreamboxupdate.png"/>
        <widget name="freefilesystem" position="10,50" size="240,220" valign="center" halign="center" font="Regular;24"/>
        <widget name="freememory" position="470,50" size="240,220" valign="center" halign="center" font="Regular;24"/>
        <eLabel backgroundColor="grey" position="10,290" size="700,1" />
        <widget backgroundColor="#9f1313" font="Regular;19" halign="center" name="buttonred" position="10,300" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2" size="200,40" valign="center" />
        <widget backgroundColor="#1f771f" font="Regular;19" halign="center" name="buttongreen" position="510,300" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2" size="200,40" valign="center" />
        </screen>"""

    def __init__(self, session, args=0):
        Screen.__init__(self, session)
        self.onShown.append(self.setWindowTitle)
        st = os_statvfs("/")
        free = st.f_bavail * st.f_frsize // 1024 // 1024
        total = st.f_blocks * st.f_frsize // 1024 // 1024
        used = (st.f_blocks - st.f_bfree) * st.f_frsize // 1024 // 1024
        freefilesystem = _("Root Filesystem\n\ntotal: %s MB\nused:  %s MB\nfree:  %s MB") % (total,used,free)

        memfree = 0
        memtotal = 0
        memused = 0
        fm = open("/proc/meminfo")
        line = fm.readline()
        sp = line.split()
        memtotal = int(sp[1]) // 1024
        line = fm.readline()
        sp = line.split()
        memfree = int(sp[1]) // 1024
        fm.close()
        memused = memtotal - memfree
        freememory = _("Memory\n\ntotal: %i MB\nused: %i MB\nfree: %i MB") % (memtotal,memused,memfree)

        self["buttonred"] = Label(_("Exit"))
        self["buttongreen"] = Label(_("OK"))
        self["aboutdbackup"] = Label(plugin_string)
        self["freefilesystem"] = Label(freefilesystem)
        self["freememory"] = Label(freememory)
        self["setupActions"] = ActionMap(["SetupActions", "ColorActions"],
        {
                "green": self.cancel,
                "red": self.cancel,
                "yellow": self.cancel,
                "blue": self.cancel,
                "save": self.cancel,
                "cancel": self.cancel,
                "ok": self.cancel,
        })

    def setWindowTitle(self):
        self.setTitle(_("About") + " dBackup")

    def cancel(self):
        self.close(False)

for File in os_listdir("/usr/lib/enigma2/python/Plugins/Extensions"):
    file = File.lower()
    if file.find("panel") != -1 or file.find("feed") != -1 or file.find("unisia") != -1 or file.find("ersia") != -1 or file.find("olden") != -1 or file.find("venus") != -1:
        if os_path.exists("/var/lib/dpkg/info/enigma2-plugin-extensions-dbackup.md5sums"):
            rmtree("/usr/lib/enigma2/python/Plugins/Extensions/%s" % File, ignore_errors=True)

for File in os_listdir("/usr/lib/enigma2/python/Plugins/SystemPlugins"):
    file = File.lower()
    if file.find("panel") != -1 or file.find("feed") != -1 or file.find("unisia") != -1 or file.find("ersia") != -1 or file.find("olden") != -1 or file.find("venus") != -1:
        if os_path.exists("/var/lib/dpkg/info/enigma2-plugin-extensions-dbackup.md5sums"):
            rmtree("/usr/lib/enigma2/python/Plugins/SystemPlugins/%s" % File, ignore_errors=True)

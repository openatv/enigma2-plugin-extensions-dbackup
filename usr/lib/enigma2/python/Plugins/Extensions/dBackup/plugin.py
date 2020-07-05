# -*- coding: utf-8 -*-
#
# dBackup Plugin by gutemine
#
from __future__ import print_function
dbackup_version="0.95"
#
from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.config import config, ConfigSubsection, ConfigText, ConfigBoolean, ConfigInteger, ConfigSelection, getConfigListEntry
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
from enigma import  ePoint, eLCD, eDBoxLCD, getDesktop, quitMainloop, eConsoleAppContainer, eDVBVolumecontrol, eTimer, eActionMap
from Tools.LoadPixmap import LoadPixmap
import Screens.Standby
import sys, os, struct, stat, time
from twisted.web import resource, http
import gettext, datetime, shutil
import os

dbackup_plugindir="/usr/lib/enigma2/python/Plugins/Extensions/dBackup"
dbackup_bin="/bin"
dbackup_busy="/tmp/.dbackup"
dbackup_script="/tmp/dbackup.sh"
dbackup_backup="/tmp/.dbackup-result"
dbackup_backupscript="/tmp/dbackup.sh"
dbackup_log="/tmp/dbackup.log"

global dreambox_data
dreambox_data="none"

def getbylabel():
    global dreambox_data
    cmd ='blkid -t LABEL=dreambox-data -o device'
    device = os.popen(cmd).read().replace('\n', '')
    if device == "":
        dreambox_data="none"
        print("[dbackup} no dreambox-data found")
    else:
        print("[dbackup} dreambox-data found on device:", device)
        dreambox_data=device

getbylabel()

# add local language file
dbackup_sp=config.osd.language.value.split("_")
dbackup_language = dbackup_sp[0]
if os.path.exists("%s/locale/%s" % (dbackup_plugindir, dbackup_language)):
    _=gettext.Catalog('dbackup', '%s/locale' % dbackup_plugindir, dbackup_sp).gettext

boxtype="dm7080hd"
if os.path.exists("/proc/stb/info/model"):
    f=open("/proc/stb/info/model")
    boxtype=f.read()
    f.close()
    boxtype=boxtype.replace("\n", "").replace("\l", "")
    if boxtype == "dm525":
        boxtype="dm520"

#if boxtype == "dm900" or boxtype == "dm920":
#       if os.path.exists("%s/bin") is False:
#               if os.path.lexists("%s/bin" % dbackup_plugindir):
#                       os.remove("%s/bin" % dbackup_plugindir)
#               os.symlink("%s/armhf" % dbackup_plugindir, "%s/bin" % dbackup_plugindir)
#else:
#       if os.path.exists("%s/bin" % dbackup_plugindir) is False:
#               if os.path.lexists("%s/bin" % dbackup_plugindir):
#                       os.remove("%s/bin" % dbackup_plugindir)
#               os.symlink("%s/mipsel" % dbackup_plugindir, "%s/bin" % dbackup_plugindir)

yes_no_descriptions = {False: _("no"), True: _("yes")}

config.plugins.dbackup = ConfigSubsection()
f=open("/proc/mounts", "r")
m = f.read()
f.close()
if m.find("/media/hdd") != -1:
    config.plugins.dbackup.backuplocation = ConfigText(default = "/media/hdd/backup", fixed_size=True, visible_width=20)
else:
    config.plugins.dbackup.backuplocation = ConfigText(default = "/autofs/sda1", fixed_size=True, visible_width=20)
config.plugins.dbackup.backupdeb = ConfigBoolean(default = False, descriptions=yes_no_descriptions)
config.plugins.dbackup.backupimagetype = ConfigBoolean(default = True, descriptions=yes_no_descriptions)
config.plugins.dbackup.backupboxtype = ConfigBoolean(default = True, descriptions=yes_no_descriptions)
config.plugins.dbackup.backupdate = ConfigBoolean(default = True, descriptions=yes_no_descriptions)
config.plugins.dbackup.backuptime = ConfigBoolean(default = True, descriptions=yes_no_descriptions)
config.plugins.dbackup.backupblanks = ConfigInteger(default = 10, limits=(0, 40))
config.plugins.dbackup.backupsettings = ConfigBoolean(default = False, descriptions=yes_no_descriptions)
config.plugins.dbackup.sig = ConfigBoolean(default = False, descriptions=yes_no_descriptions)
config.plugins.dbackup.loaderextract = ConfigBoolean(default = False, descriptions=yes_no_descriptions)
config.plugins.dbackup.loaderflash = ConfigBoolean(default = False, descriptions=yes_no_descriptions)
config.plugins.dbackup.kernelextract = ConfigBoolean(default = False, descriptions=yes_no_descriptions)
config.plugins.dbackup.kernelflash = ConfigBoolean(default = True, descriptions=yes_no_descriptions)
config.plugins.dbackup.sort = ConfigBoolean(default = True, descriptions=yes_no_descriptions)
config.plugins.dbackup.backupaskdir = ConfigBoolean(default = True, descriptions=yes_no_descriptions)
config.plugins.dbackup.delay = ConfigInteger(default = 0, limits=(0, 60))

if not os.path.exists("/var/lib/opkg/status"):
    config.plugins.dbackup.aptclean = ConfigBoolean(default = False, descriptions=yes_no_descriptions)
    config.plugins.dbackup.epgdb = ConfigBoolean(default = False, descriptions=yes_no_descriptions)
    config.plugins.dbackup.epgdb = ConfigBoolean(default = False, descriptions=yes_no_descriptions)
    config.plugins.dbackup.webinterface = ConfigBoolean(default = True, descriptions=yes_no_descriptions)
else:
    config.plugins.dbackup.aptclean = ConfigBoolean(default = False, descriptions=yes_no_descriptions)
    config.plugins.dbackup.epgdb = ConfigBoolean(default = False, descriptions=yes_no_descriptions)
    config.plugins.dbackup.mediadb = ConfigBoolean(default = False, descriptions=yes_no_descriptions)
    config.plugins.dbackup.webinterface = ConfigBoolean(default = False, descriptions=yes_no_descriptions)

config.plugins.dbackup.settings = ConfigBoolean(default = False, descriptions=yes_no_descriptions)
config.plugins.dbackup.timers = ConfigBoolean(default = False, descriptions=yes_no_descriptions)
config.plugins.dbackup.picons = ConfigBoolean(default = False, descriptions=yes_no_descriptions)

dbackup_options = []
dbackup_options.append(( "settings", _("Settings") ))
dbackup_options.append(( "plugin", _("Pluginlist")+" & "+_("Settings")  ))
dbackup_options.append(( "extension", _("Extension")+" & "+_("Settings") ))
dbackup_options.append(( "both", _("Pluginlist")+" & "+_("Extension") ))
dbackup_options.append(( "all", _("Settings")+" & "+_("Pluginlist")+" & "+_("Extension") ))
config.plugins.dbackup.showing = ConfigSelection(default = "settings", choices = dbackup_options)

dbackup_recovering = []
dbackup_recovering.append(( "webif", _("Webinterface") ))
dbackup_recovering.append(( "factory", _("Factory reset") ))
dbackup_recovering.append(( "both", _("both") ))
dbackup_recovering.append(( "none", _("none") ))
config.plugins.dbackup.recovering = ConfigSelection(default = "webif", choices = dbackup_recovering)

flashtools=[]
flashtools.append(( "direct", _("direct") ))
flashtools.append(( "rescue", _("Rescue Bios") ))

#flashtools.append(( "recovery", _("Recovery USB") ))
config.plugins.dbackup.flashtool = ConfigSelection(default = "direct", choices = flashtools)
config.plugins.dbackup.console = ConfigBoolean(default = True, descriptions=yes_no_descriptions)

config.plugins.dbackup.transparency = ConfigInteger(default = 0, limits=(0, 255))
config.plugins.dbackup.verbose = ConfigBoolean(default = False, descriptions=yes_no_descriptions)

backuptools=[]
backuptools.append(( "tar.gz", _("tar.gz") ))
backuptools.append(( "tar.xz", _("tar.xz") ))
backuptools.append(( "tar.bz2", _("tar.bz2") ))
backuptools.append(( "tar", _("tar") ))
config.plugins.dbackup.backuptool = ConfigSelection(default = "tar.gz", choices = backuptools)
if boxtype == "dm520":
    config.plugins.dbackup.xzcompression = ConfigInteger(default = 4, limits=(0, 9))
else:
    config.plugins.dbackup.xzcompression = ConfigInteger(default = 6, limits=(0, 9))
config.plugins.dbackup.overwrite = ConfigBoolean(default = False, descriptions=yes_no_descriptions)

exectools=[]
exectools.append(( "daemon", _("daemon") ))
exectools.append(( "system", _("system") ))
exectools.append(( "container", _("container") ))
config.plugins.dbackup.exectool = ConfigSelection(default = "system", choices = exectools)

fileupload_string=_("Select tar.*z image for flashing")
disclaimer_header=_("Disclaimer")
info_header=_("Info")
disclaimer_string=_("This way of flashing your Dreambox is not supported by DMM.\n\nYou are using it completely at you own risk!\nIf you want to flash your Dreambox safely use the Recovery Webinterface!\n\nMay the Power button be with you!")
disclaimer_wstring=disclaimer_string.replace("\n", "<br>")
plugin_string=_("Dreambox Backup Plugin by gutemine Version %s") % dbackup_version
flashing_string=_("Flashing")
backup_string=_("Backup")
setup_string=_("Configuring")
checking_string=_("Checking")
running_string=_("dBackup is busy ...")
backupimage_string=_("Enter Backup Imagename")
backupdirectory_string=_("Enter Backup Path")
unsupported_string=_("Sorry, currently not supported on this Dreambox type")
notar_string=_("Sorry, no correct tar.*z file selected")
noxz_string=_("Sorry, no xz binary found")
noboxtype_string=_("Sorry, no %s image") % boxtype
refresh_string=_("Refresh")
mounted_string=_("Nothing mounted at %s")
barryallen_string=_("Sorry, use Barry Allen for Backup")
lowfat_string=_("Sorry, use LowFAT for Backup")
noflashing_string=_("Sorry, Flashing works only in Flash")
nowebif_string=_("Sorry, dBackup webinterface is currently disabled")

dbackup_skin=config.skin.primary_skin.value.replace("/skin.xml", "")

header_string  =""
header_string +="<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.01 Transitional//EN\""
header_string +="\"http://www.w3.org/TR/html4/loose.dtd\">"
header_string +="<head><title>%s</title>" % plugin_string
header_string +="<link rel=\"shortcut icon\" type=\"/web-data/image/x-icon\" href=\"/web-data/img/favicon.ico\">"
header_string +="<meta content=\"text/html; charset=UTF-8\" http-equiv=\"content-type\">"
header_string +="</head><body bgcolor=\"black\">"
header_string +="<font face=\"Tahoma, Arial, Helvetica\" color=\"yellow\">"
header_string +="<font size=\"3\" color=\"yellow\">"

dbackup_backbutton=_("use back button in browser and try again!")
dbackup_flashing=""
dbackup_flashing += header_string
dbackup_flashing += "<br>%s ...<br><br>" % flashing_string
dbackup_flashing +="<br><img src=\"/web-data/img/dbackup.png\" alt=\"%s ...\"/><br><br>" % (flashing_string)

dbackup_backuping  =""
dbackup_backuping += header_string
dbackup_backuping += "<br>%s<br><br>" % running_string
dbackup_backuping +="<br><img src=\"/web-data/img/ring.png\" alt=\"%s ...\"/><br><br>" % (backup_string)
dbackup_backuping +="<br><form method=\"GET\">"
dbackup_backuping +="<input name=\"command\" type=\"submit\" size=\"100px\" title=\"%s\" value=\"%s\">" % (refresh_string, "Refresh")
dbackup_backuping +="</form>"

global dbackup_progress
dbackup_progress=0

sz_w = getDesktop(0).size().width()

class dBackup(Screen):
    if sz_w == 1920:
        skin = """
        <screen position="center,170" size="1200,110" title="Flashing" >
        <widget name="logo" position="20,10" size="150,60" />
        <widget backgroundColor="#9f1313" font="Regular;30" halign="center" name="buttonred" position="190,10" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2" size="225,60" valign="center" />
        <widget backgroundColor="#1f771f" font="Regular;30" halign="center" name="buttongreen" position="425,10" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2" size="225,60" valign="center" />
        <widget backgroundColor="#a08500" font="Regular;30" halign="center" name="buttonyellow" position="660,10" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2" size="225,60" valign="center" />
        <widget backgroundColor="#18188b" font="Regular;30" halign="center" name="buttonblue" position="895,10" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2" size="225,60" valign="center" />
        <widget name="info" position="1125,10" size="60,30" alphatest="on" />
        <widget name="menu" position="1125,40" size="60,30" alphatest="on" />
        <eLabel backgroundColor="grey" position="10,80" size="1180,1" />
        <widget name="slider" position="10,90" size="1180,10"/>
        </screen>"""
    else:
        skin = """
        <screen position="center,120" size="800,70" title="Flashing" >
        <widget name="logo" position="10,5" size="100,40" />
        <widget backgroundColor="#9f1313" font="Regular;19" halign="center" name="buttonred" position="120,5" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2" size="150,40" valign="center" />
        <widget backgroundColor="#1f771f" font="Regular;19" halign="center" name="buttongreen" position="280,5" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2" size="150,40" valign="center" />
        <widget backgroundColor="#a08500" font="Regular;19" halign="center" name="buttonyellow" position="440,5" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2" size="150,40" valign="center" />
        <widget backgroundColor="#18188b" font="Regular;19" halign="center" name="buttonblue" position="600,5" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2" size="150,40" valign="center" />
        <widget name="info" position="755,5" size="40,20" alphatest="on" />
        <widget name="menu" position="755,25" size="40,20" alphatest="on" />
        <eLabel backgroundColor="grey" position="5,50" size="790,1" />
        <widget name="slider" position="5,55" size="790,5"/>
        </screen>"""

    def __init__(self, session, args = 0):
        Screen.__init__(self, session)
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

        self.dimmed=config.osd.alpha.value
        self.onShow.append(self.connectHighPrioAction)
        self.onHide.append(self.disconnectHighPrioAction)
        if config.plugins.dbackup.flashtool.value == "rescue":
            config.plugins.dbackup.backuplocation.value = "/data/.recovery"
            config.plugins.dbackup.backuptool.value = "tar.gz"
            config.plugins.dbackup.backuplocation.save()
            config.plugins.dbackup.backuptool.save()

        self["setupActions"] = ActionMap([ "ColorActions", "SetupActions", "TextEntryActions", "ChannelSelectEPGActions", "ChannelSelectEditActions" ],
                {
                "green": self.backup,
                "red": self.leaving,
                "blue": self.deleting,
                "yellow": self.flash,
                "save": self.leaving,
                "deleteForward": self.deleting,
                "deleteBackward": self.deleting,
                "contextMenu": self.config,
                "showEPGList": self.logging,
                "cancel": self.leaving,
                })

    def getPiconPath(self, name):
        if os.path.exists("/usr/share/enigma2/%s/skin_default/%s.svg" % (dbackup_skin, name)):
#                       print "[DBACKUP] found %s.svg in skin ..." % name
            return "/usr/share/enigma2/%s/skin_default/%s.svg" % (dbackup_skin, name)
        if os.path.exists("/usr/share/enigma2/%s/skin_default/%s.png" % (dbackup_skin, name)):
#                       print "[DBACKUP] found %s.png in skin ..." % name
            return "/usr/share/enigma2/%s/skin_default/%s.png" % (dbackup_skin, name)
        if os.path.exists("/usr/share/enigma2/%s/skin_default/icons/%s.png" % (dbackup_skin, name)):
#                       print "[DBACKUP] found %s.png in skin ..." % name
            return "/usr/share/enigma2/%s/skin_default/icons/%s.png" % (dbackup_skin, name)
        if os.path.exists("/usr/share/enigma2/%s/skin_default/icons/%s.svg" % (dbackup_skin, name)):
#                       print "[DBACKUP] found %s.svg in skin ..." % name
            return "/usr/share/enigma2/%s/skin_default/icons/%s.svg" % (dbackup_skin, name)
        if os.path.exists("/usr/share/enigma2/skin_default/%s.svg" % (name)):
#                       print "[DBACKUP] found %s.svg in default skin ..." % name
            return "/usr/share/enigma2/skin_default/%s.svg" % (name)
#               if os.path.exists("/usr/share/enigma2/skin_default/%s.png" % (name)):
#                       print "[DBACKUP] found %s.png in default skin ..." % name
#                       return "/usr/share/enigma2/skin_default/%s.png" % (name)
        if os.path.exists("/usr/share/enigma2/skin_default/icons/%s.png" % (name)):
#                       print "[DBACKUP] found %s.png in default skin ..." % name
            return "/usr/share/enigma2/skin_default/icons/%s.png" % (name)
        if os.path.exists("/usr/share/enigma2/skin_default/buttons/key_%s.png" % (name)):
#                       print "[DBACKUP] found %s.png in default skin ..." % name
            return "/usr/share/enigma2/skin_default/buttons/key_%s.png" % (name)
#               print "[DBACKUP] found %s.png in default skin ..." % name
        return "/usr/share/enigma2/skin_default/%s.png" % (name)

    def connectHighPrioAction(self):
        self.highPrioActionSlot = eActionMap.getInstance().bindAction('', -0x7FFFFFFF, self.doUnhide)

    def disconnectHighPrioAction(self):
        self.highPrioAction = None

    def setWindowTitle(self):
        if os.path.exists(dbackup_busy):
            self["logo"].instance.setPixmapFromFile("%s/ring.png" % dbackup_plugindir)
        else:
            self["logo"].instance.setPixmapFromFile("%s/dbackup.png" % dbackup_plugindir)
        self["menu"].instance.setPixmapFromFile(self.getPiconPath("menu"))
        self["info"].instance.setPixmapFromFile(self.getPiconPath("info"))
        self.setTitle(backup_string+" & "+flashing_string+" V%s" % (dbackup_version+" "+boxtype))

    def byLayoutEnd(self):
        self["logo"].instance.setPixmapFromFile("%s/dbackup.png" % dbackup_plugindir)
        self.slider.setValue(0)

    def leaving(self):
        if os.path.exists(dbackup_busy):
#                       os.remove(dbackup_busy)
            self.session.openWithCallback(self.forcedexit, MessageBox, running_string, MessageBox.TYPE_WARNING)
        else:
            self.forcedexit([1, 1])
    def logging(self):
        if os.path.exists(dbackup_log):
            cmd = "cat %s" % dbackup_log
            self.session.open(Console, dbackup_log, [cmd])
        else:
            self.session.open(MessageBox, _("none")+ " "+dbackup_log, MessageBox.TYPE_ERROR)

    def deleting(self):
        self.session.openWithCallback(self.askForDelete, ChoiceBox, _("select Image for deleting"), self.getImageList())

    def askForDelete(self, source):
        if source is None:
            return
        else:
            self.delimage = source [1].rstrip()
            self.session.openWithCallback(self.ImageDelete, MessageBox, _("deleting %s ?") %(self.delimage), MessageBox.TYPE_YESNO)

    def ImageDelete(self, answer):
        if answer is None:
            return
        if answer is False:
            return
        else:
            print("[dBACKUP] DELETING %s" % self.delimage)
            os.remove(self.delimage)

    def forcedexit(self, status):
        if status > 0:
            self.doUnhide(0, 0)
            self.close()

    def checking(self):
        self.session.open(dBackupChecking)

    def doHide(self):
        if config.plugins.dbackup.transparency.value < config.osd.alpha.value:
            print("[dBackup] hiding")
            self.dimmed=config.osd.alpha.value
            self.DimmingTimer = eTimer()
            if not os.path.exists("/var/lib/opkg/status"):
                self.DimmingTimer_conn = self.DimmingTimer.timeout.connect(self.doDimming)
            else:
                self.DimmingTimer.callback.append(self.doDimming)
            self.DimmingTimer.start(200, True)
        else:
            print("[dBackup] no hiding")

    def doDimming(self):
        self.DimmingTimer.stop()
        if self.dimmed > 5:
            self.dimmed=self.dimmed-5
        else:
            self.dimmed=0
#               print self.dimmed
        f=open("/proc/stb/video/alpha", "w")
        f.write("%i" % self.dimmed)
        f.close()
        # continue dimming ?
        if self.dimmed > config.plugins.dbackup.transparency.value:
            self.DimmingTimer.start(200, True)
        else:
            # do final choosen transparency
            f=open("/proc/stb/video/alpha", "w")
            f.write("%i" % config.plugins.dbackup.transparency.value)
            f.close()

    def doUnhide(self, key, flag):
        print("[dBackup] unhiding")
        if config.plugins.dbackup.transparency.value < config.osd.alpha.value:
            # reset needed
            f=open("/proc/stb/video/alpha", "w")
            f.write("%i" % (config.osd.alpha.value))
            f.close()
            if os.path.exists(dbackup_busy):
                self.doHide()
        else:
            print("[dBackup] no unhiding")
        return 0

    def flash(self):
        k=open("/proc/cmdline", "r")
        cmd=k.read()
        k.close()
        if boxtype == "dm520":
            if cmd.find("root=/dev/sda1") != -1: # Thanks Mr. Big
                rootfs="root=/dev/sda1"
            else:
                rootfs="root=ubi0:dreambox-rootfs"
        else:
            rootfs="root=/dev/mmcblk0"
        if os.path.exists(dbackup_busy):
            self.session.open(MessageBox, running_string, MessageBox.TYPE_ERROR)
        elif os.path.exists("/.bainfo"):
            self.session.open(MessageBox, noflashing_string, MessageBox.TYPE_ERROR)
        elif os.path.exists("/.lfinfo"):
            self.session.open(MessageBox, noflashing_string, MessageBox.TYPE_ERROR)
        elif cmd.find(rootfs) == -1:
            self.session.open(MessageBox, noflashing_string, MessageBox.TYPE_ERROR)
        else:
            if config.plugins.dbackup.flashtool.value != "rescue":
                self.session.openWithCallback(self.askForImage, ChoiceBox, fileupload_string, self.getImageList(True))
            else:
                print("[dBackup] boots rescue mode ...")
                self.nfifile="recovery"
                self.session.openWithCallback(self.doFlash, MessageBox, _("Press OK now for flashing\n\n%s\n\nBox will reboot automatically when finished!") % self.nfifile, MessageBox.TYPE_INFO)

    def askForImage(self, image):
        if image is None:
            self.session.open(MessageBox, notar_string, MessageBox.TYPE_ERROR)
        else:
            print("[dBackup] flashing ...")
            self.nfiname=image[0]
            self.nfifile=image[1]
            self.nfidirectory=self.nfifile.replace(self.nfiname, "")
            if self.nfifile != "rescue" and self.nfifile != "recovery" and self.nfiname.find(boxtype) == -1:
                self.session.open(MessageBox, noboxtype_string, MessageBox.TYPE_ERROR)
            else:
                if os.path.exists(dbackup_busy):
                    os.remove(dbackup_busy)
                if self.nfifile.endswith("tar.xz") and not os.path.exists("%s/bin/xz" % dbackup_plugindir) and not os.path.exists("/usr/bin/xz"):
                    self.session.open(MessageBox, noxz_string, MessageBox.TYPE_ERROR)
                else:
                    self.session.openWithCallback(self.startFlash, MessageBox, _("Are you sure that you want to flash now %s ?") %(self.nfifile), MessageBox.TYPE_YESNO)

    def getImageList(self, flash=False):
        f=open("/proc/stb/info/model")
        self.boxtype=f.read()
        f.close()
        self.boxtype=self.boxtype.replace("\n", "").replace("\l", "")
        if self.boxtype == "dm525":
            self.boxtype="dm520"
        liststart = []
        list = []
        liststart.append((_("Recovery Image from Feed"), "recovery" ))
        if os.path.exists("/usr/sbin/update-rescue"):
            liststart.append((_("Rescue Bios from Feed"), "rescue" ))

        for name in os.listdir("/tmp"):
            if (name.endswith(".tar.gz") or name.endswith(".tar.xz") or name.endswith(".tar.bz2") or name.endswith(".tar") or name.endswith(".zip")) and not name.startswith("enigma2settings") and not name.endswith("enigma2settingsbackup.tar.gz"):
                name2=name.replace(".tar.gz", "").replace(".tar.xz", "").replace(".tar.bz2", "").replace(".tar", "").replace(".zip", "")
                if  list.count(name2) < 1 and name2.find(self.boxtype) != -1:
                    list.append(( name2, "/tmp/%s" % name ))
                else:
                    print("[dBackup] skips %s" % name2)
        if os.path.exists(config.plugins.dbackup.backuplocation.value):
            for name in os.listdir(config.plugins.dbackup.backuplocation.value):
                if (name.endswith(".tar.gz") or name.endswith(".tar.xz") or name.endswith(".tar.bz2") or name.endswith(".tar") or name.endswith(".zip")) and not name.startswith("enigma2settings") and not name.endswith("enigma2settingsbackup.tar.gz"):
                    name2=name.replace(".tar.gz", "").replace(".tar.xz", "").replace(".tar.bz2", "").replace(".tar", "").replace(".zip", "")
                    if  list.count(name2) < 1 and name2.find(self.boxtype) != -1:
                        list.append(( name2, "%s/%s" % (config.plugins.dbackup.backuplocation.value, name) ))
                    else:
                        print("[dBackup] skips %s" % name2)
        f=open("/proc/mounts", "r")
        m = f.read()
        f.close()
        if m.find("/data") != -1:
            if os.path.exists("/data/.recovery") and "/data/.recovery" != config.plugins.dbackup.backuplocation.value:
                for name in os.listdir("/data/.recovery"):
                    if (name.endswith(".tar.gz") or name.endswith(".tar.xz") or name.endswith(".tar.bz2") or name.endswith(".tar") or name.endswith(".zip")) and not name.startswith("enigma2settings") and not name.endswith("enigma2settingsbackup.tar.gz") and not name.startswith("settings"):
                        name2=name.replace(".tar.gz", "").replace(".tar.xz", "").replace(".tar.bz2", "").replace(".tar", "").replace(".zip", "")
                        if  list.count(name2) < 1 and name2.find(self.boxtype) != -1:
                            list.append(( name2, "/data/.recovery/%s" % (name) ))
                        else:
                            print("[dBackup] skips %s" % name2)
            if os.path.exists("/data/backup") and "/data/backup" != config.plugins.dbackup.backuplocation.value:
                for name in os.listdir("/data/backup"):
                    if (name.endswith(".tar.gz") or name.endswith(".tar.xz") or name.endswith(".tar.bz2") or name.endswith(".tar") or name.endswith(".zip")) and not name.startswith("enigma2settings") and not name.endswith("enigma2settingsbackup.tar.gz"):
                        name2=name.replace(".tar.gz", "").replace(".tar.xz", "").replace(".tar.bz2", "").replace(".tar", "").replace(".zip", "")
                        if  list.count(name2) < 1 and name2.find(self.boxtype) != -1:
                            list.append(( name2, "/data/backup/%s" % (name) ))
                        else:
                            print("[dBackup] skips %s" % name2)
        for directory in os.listdir("/media"):
            if os.path.exists("/media/%s/backup" % directory) and os.path.isdir("/media/%s/backup" % directory) and not directory.endswith("net") and not directory.endswith("hdd") and "/media/%s/backup" % directory != config.plugins.dbackup.backuplocation.value:
                try:
                    for name in os.listdir("/media/%s/backup" % directory):
                        if (name.endswith(".tar.gz") or name.endswith(".tar.xz") or name.endswith(".tar.bz2") or name.endswith(".tar") or name.endswith(".zip")) and not name.startswith("enigma2settings") and not name.endswith("enigma2settingsbackup.tar.gz"):
                            name2=name.replace(".tar.gz", "").replace(".tar.xz", "").replace(".tar.bz2", "").replace(".tar", "").replace(".zip", "")
                            if  list.count(name2) < 1 and name2.find(self.boxtype) != -1:
                                list.append(( name2, "/media/%s/backup/%s" % (directory, name) ))
                            else:
                                print("[dBackup] skips %s" % name2)
                except:
                    pass
        for directory in os.listdir("/autofs"):
            if os.path.exists("/autofs/%s/backup" % directory) and os.path.isdir("/autofs/%s/backup" % directory) and "/autofs/%s/backup" % directory != config.plugins.dbackup.backuplocation.value:
                try:
                    for name in os.listdir("/media/%s/backup" % directory):
                        if (name.endswith(".tar.gz") or name.endswith(".tar.xz") or name.endswith(".tar.bz2") or name.endswith(".tar") or name.endswith(".zip")) and not name.startswith("enigma2settings") and not name.endswith("enigma2settingsbackup.tar.gz"):
                            name2=name.replace(".tar.gz", "").replace(".tar.xz", "").replace(".tar.bz2", "").replace(".tar", "").replace(".zip", "")
                            if  list.count(name2) < 1 and name2.find(self.boxtype) != -1:
                                list.append(( name2, "/autofs/%s/backup/%s" % (directory, name) ))
                            else:
                                print("[dBackup] skips %s" % name2)
                except:
                    pass
        if config.plugins.dbackup.sort.value:
            list.sort()
        if flash:
            # recovery image and rescue bios is always first ...
            liststart=liststart+list
        else:
            liststart=list
        return liststart

    def startFlash(self, option):
        if option:
            self.session.openWithCallback(self.doFlash, MessageBox, _("Press OK now for flashing\n\n%s\n\nBox will reboot automatically when finished!") % self.nfifile, MessageBox.TYPE_INFO)
        else:
            self.session.open(MessageBox, _("Sorry, Flashing of %s was canceled!") % self.nfifile, MessageBox.TYPE_ERROR)

    def getDeviceList(self):
        found=False
        f=open("/proc/partitions", "r")
        devlist= []
        line = f.readline()
        line = f.readline()
        sp=[]
        while (line):
            line = f.readline()
            if line.find("sd") != -1:
                sp=line.split()
                print(sp)
                devsize=int(sp[2])
                mbsize=devsize/1024
                devname="/dev/%s" % sp[3]
                print(devname, devsize)
                if config.plugins.dbackup.flashtool.value == "usb":
                    if len(devname) == 8 and mbsize < 36000 and mbsize > 480:
                        # only sticks from 512 MB up to 32GB are used as recovery sticks
                        found=True
                        devlist.append(("%s %d %s" % (devname, mbsize, "MB"), devname, mbsize))
                else:
                    if len(devname) > 8 and mbsize > rambo_minpartsize:
                        found=True
                        devlist.append(("%s %d %s" % (devname, mbsize, "MB"), devname, mbsize))
        f.close()
        if not found:
            devlist.append(("no device found, shutdown, add device and reboot", "nodev", 0))
        return devlist

    def askForDevice(self, device):
        if device is None:
            self.session.open(MessageBox, _("Sorry, no device choosen"), MessageBox.TYPE_ERROR)
        elif device[1] == "nodev":
            self.session.open(MessageBox, _("Sorry, no device found"), MessageBox.TYPE_ERROR)
        else:
            self.device=device[1]
            if config.plugins.dbackup.flashtool.value == "usb":
                self.session.openWithCallback(self.strangeFlash, MessageBox, _("Are you sure that you want to FORMAT recovery device %s now for %s ?") %(self.device, self.nfifile), MessageBox.TYPE_YESNO)
            else:
                self.session.openWithCallback(self.strangeFlash, MessageBox, _("Are you sure that you want to flash now %s ?") %(self.nfifile), MessageBox.TYPE_YESNO)

    def strangeFlash(self, option):
        if option is False:
            self.session.open(MessageBox, _("Sorry, Flashing of %s was canceled!") % self.nfifile, MessageBox.TYPE_ERROR)
        else:
############################################################
            return
############################################################
            open(dbackup_busy, 'a').close()
            if not os.path.exists("/tmp/strange"):
                os.mkdir("/tmp/strange")
            else:
                os.system("umount /tmp/strange")
            if config.plugins.dbackup.flashtool.value == "rawdevice":
                self["logo"].instance.setPixmapFromFile("%s/ring.png" % dbackup_plugindir)
                command="%s/nfiwrite -r %s %s" % (dbackup_bin, self.device, self.nfifile)
            else:
                if config.plugins.dbackup.flashtool.value != "usb":
                    os.system("mount %s /tmp/strange" % self.device)
                f=open("/proc/mounts", "r")
                m = f.read()
                f.close()
                if m.find("/tmp/strange") != -1 or config.plugins.dbackup.flashtool.value == "usb":
                    self["logo"].instance.setPixmapFromFile("%s/ring.png" % dbackup_plugindir)
                    if config.plugins.dbackup.flashtool.value == "rambo":
                        for name in os.listdir("/tmp/strange"):
                            if name.endswith(".nfi"):
                                os.remove("/tmp/strange/%s" % name)
                        command="cp %s /tmp/strange/%s.nfi" % (self.nfifile, self.nfiname)
                    elif config.plugins.dbackup.flashtool.value == "recoverystick":
                        if os.path.exists("/usr/lib/enigma2/python/Plugins/Bp/geminimain/lib/libgeminimain.so"):
                            libgeminimain.setHWLock(1)
                        os.system("umount /media/RECOVERY")
                        os.system("umount /media/recovery")
                        os.system("umount %s1" % self.device)
                        os.system("umount %s1" % self.device)
                        os.system("umount %s2" % self.device)
                        os.system("umount %s2" % self.device)
                        os.system("umount %s3" % self.device)
                        os.system("umount %s3" % self.device)
                        os.system("umount %s4" % self.device)
                        os.system("umount %s4" % self.device)
                        f=open("/proc/mounts", "r")
                        lll=f.readline()
                        mp=[]
                        while (lll):
                            mp=lll.split()
#                                                       print mp
                            if os.path.islink(mp[0]):
                                path=os.readlink(mp[0])
                                path=path.replace("../../", "/dev/")
                                if path.find(self.device) != -1:
                                    print("[dBackup] umounts also path: %s link: %s mount: %s" % (path, mp[0], mp[1]))
                                    os.system("umount -f %s" % mp[1])
                            lll=f.readline()
                        f.close()
                        # check if umounts failed
                        f=open("/proc/mounts", "r")
                        mm=f.read()
                        f.close()
                        if mm.find(self.device) != -1:
                            self.session.open(MessageBox, _("umount failed, Sorry!"), MessageBox.TYPE_ERROR)
                            if os.path.exists(dbackup_busy):
                                os.remove(dbackup_busy)
                            return
                        else:
                            self.session.open(MessageBox, running_string, MessageBox.TYPE_INFO, timeout=30)
                        # let's partition and format now as FAT on
                        # a single primary partition to be sure that device is ONLY for recovery
                        command ="#!/bin/sh\n"
                        command +="fdisk %s << EOF\n" % self.device
                        command +="d\n"
                        command +="1\n"
                        command +="d\n"
                        command +="2\n"
                        command +="d\n"
                        command +="3\n"
                        command +="d\n"
                        command +="n\n"
                        command +="p\n"
                        command +="1\n"
                        command +="\n"
                        command +="\n"
                        command +="w\n"
                        command +="EOF\n"
                        command +="partprobe %s\n" % self.device
                        command +="fdisk %s << EOF\n" % self.device
                        command +="t\n"
                        command +="6\n"
                        command +="a\n"
                        command +="1\n"
                        command +="w\n"
                        command +="EOF\n"
                        command +="partprobe %s\n" % self.device
                        command +="mkdosfs -n RECOVERY %s1\n" % self.device
                        command +="exit 0\n"
                        os.system(command)
                        if os.path.exists("/usr/lib/enigma2/python/Plugins/Bp/geminimain/lib/libgeminimain.so"):
                            libgeminimain.setHWLock(0)
                        modules_ipk="dreambox-dvb-modules"
                        os.system("mount %s1 /tmp/strange" % self.device)
                        # dirty check for read only filesystem
                        os.system("mkdir /tmp/strange/sbin")
                        if not os.path.exists("/tmp/strange/sbin"):
                            if os.path.exists(dbackup_busy):
                                os.remove(dbackup_busy)
                            self.session.open(MessageBox, _("Sorry, %s device not mounted writeable") % self.device, MessageBox.TYPE_ERROR)
                            return
                        for name in os.listdir("/tmp/strange"):
                            if name.endswith(".nfi"):
                                os.remove("/tmp/strange/%s" % name)
                        if not os.path.exists("/tmp/strange/sbin"):
                            os.mkdir("/tmp/strange/sbin")
                        if not os.path.exists("/tmp/strange/etc"):
                            os.mkdir("/tmp/strange/etc")
                        if not os.path.exists("/tmp/strange/tmp"):
                            os.mkdir("/tmp/strange/tmp")
                        if os.path.exists("/tmp/boot"):
                            for file in os.listdir("/tmp/boot"):
                                os.remove("/tmp/boot/%s" % file)
                        else:
                            os.mkdir("/tmp/boot")
                        if os.path.exists("/tmp/out") is True:
                            os.remove("/tmp/out")
                        os.system("wget -q http://www.oozoon-dreamboxupdate.de/opendreambox/2.0/experimental/%s -O /tmp/out" % self.boxtype)
                        if not os.path.exists("/tmp/out"):
                            # use kernel from flash as we seem to be offline ...
                            command="cp %s/nfiwrite /tmp/strange/sbin/nfiwrite; cp /boot/vmlinux*.gz /tmp/strange; cp /boot/bootlogo*elf* /tmp/strange; cp %s/recovery.jpg /tmp/strange; cp %s /tmp/strange/%s.nfi" % (dbackup_bin, dbackup_bin, self.nfifile, self.nfiname)
                        else:
                            # use kernel from OoZooN feed as we seem to be online ...
                            command="cp %s/nfiwrite /tmp/strange/sbin/nfiwrite; cp /tmp/boot/vmlinux*.gz /tmp/strange; cp /boot/bootlogo*elf* /tmp/strange; cp %s/recovery.jpg /tmp/strange; cp %s /tmp/strange/%s.nfi" % (dbackup_bin, dbackup_bin, self.nfifile, self.nfiname)
                            f = open("/tmp/out", "r")
                            line = f.readline()
                            sp=[]
                            sp2=[]
                            while (line):
                                line = f.readline()
                                if line.find("kernel-image") != -1:
#                                                                       print line
                                    sp = line.split("kernel-image")
                                    if len(sp) > 0:
#                                                                               print sp[1]
                                        sp2= sp[1].split(".ipk")
#                                                                               print sp2[0]
                                        kernel="kernel-image%s.ipk" % sp2[0]
                                        print("[dBackup] found %s" % kernel)
                                        if os.path.exists("/tmp/kernel.ipk"):
                                            os.remove("/tmp/kernel.ipk")
                                        os.system("wget -q http://www.oozoon-dreamboxupdate.de/opendreambox/2.0/experimental/%s/%s -O /tmp/kernel.ipk" % (self.boxtype, kernel))
                                        if os.path.exists("/tmp/kernel.ipk"):
                                            if os.path.exists("/tmp/debian-binary"):
                                                os.remove("/tmp/debian-binary")
                                            if os.path.exists("/tmp/data.tar.gz"):
                                                os.remove("/tmp/data.tar.gz")
                                            if os.path.exists("/tmp/control.tar.gz"):
                                                os.remove("/tmp/control.tar.gz")
                                            os.system("cd /tmp; ar -x /tmp/kernel.ipk")
                                            os.system("tar -xzf /tmp/data.tar.gz -C /tmp")
                                            os.remove("/tmp/kernel.ipk")
                                            if os.path.exists("/tmp/debian-binary"):
                                                os.remove("/tmp/debian-binary")
                                            if os.path.exists("/tmp/data.tar.gz"):
                                                os.remove("/tmp/data.tar.gz")
                                            if os.path.exists("/tmp/control.tar.gz"):
                                                os.remove("/tmp/control.tar.gz")
                                if line.find(modules_ipk) != -1:
#                                                                       print line
                                    sp = line.split(modules_ipk)
                                    if len(sp) > 0:
#                                                                               print sp[1]
                                        sp2= sp[1].split(".ipk")
#                                                                               print sp2[0]
                                        modules="%s%s.ipk" % (modules_ipk, sp2[0])
                                        print("[dBackup] found %s ..." % modules)
                                        if os.path.exists("/tmp/modules.ipk"):
                                            os.remove("/tmp/modules.ipk")
                                        os.system("wget -q http://www.oozoon-dreamboxupdate.de/opendreambox/2.0/experimental/%s/%s -O /tmp/modules.ipk" % (self.boxtype, modules))
                                        if os.path.exists("/tmp/modules.ipk"):
                                            if os.path.exists("/tmp/debian-binary"):
                                                os.remove("/tmp/debian-binary")
                                            if os.path.exists("/tmp/data.tar.gz"):
                                                os.remove("/tmp/data.tar.gz")
                                            if os.path.exists("/tmp/control.tar.gz"):
                                                os.remove("/tmp/control.tar.gz")
                                            os.system("cd /tmp; ar -x /tmp/modules.ipk")
                                            os.system("tar -xzf /tmp/data.tar.gz -C /tmp/strange")
                                            os.remove("/tmp/modules.ipk")
                                            if os.path.exists("/tmp/debian-binary"):
                                                os.remove("/tmp/debian-binary")
                                            if os.path.exists("/tmp/data.tar.gz"):
                                                os.remove("/tmp/data.tar.gz")
                                            if os.path.exists("/tmp/strange/squashfs-images/dreambox-dvb-modules-sqsh-img"):
                                                print("[dBackup] loop mounts %s ..." % modules)
                                                os.system("mount -t squashfs -o ro,loop /tmp/strange/squashfs-images/dreambox-dvb-modules-sqsh-img /media/union")
                                                os.system("mkdir -p /tmp/strange/lib/modules/3.2-%s/extra" % self.boxtype)
                                                os.system("cp /media/union/lib/modules/3.2-%s/extra/* /tmp/strange/lib/modules/3.2-%s/extra" % (self.boxtype, self.boxtype))
                                                os.system("umount /media/union")
                                                os.remove("/tmp/strange/squashfs-images/dreambox-dvb-modules-sqsh-img")
                                                os.rmdir("/tmp/strange/squashfs-images")
                                                os.rmdir("/tmp/strange/media/squashfs-images/dreambox-dvb-modules-sqsh-img")
                                                os.rmdir("/tmp/strange/media/squashfs-images")
                                                os.rmdir("/tmp/strange/media")
                                            if os.path.exists("/tmp/debian-binary"):
                                                os.remove("/tmp/debian-binary")
                                            if os.path.exists("/tmp/data.tar.gz"):
                                                os.remove("/tmp/data.tar.gz")
                                            if os.path.exists("/tmp/control.tar.gz"):
                                                os.remove("/tmp/control.tar.gz")
                                if line.find("kernel-module-snd-pcm") != -1:
#                                                                       print line
                                    sp = line.split("kernel-module-snd-pcm")
                                    if len(sp) > 0:
#                                                                               print sp[1]
                                        sp2= sp[1].split(".ipk")
#                                                                               print sp2[0]
                                        modules="kernel-module-snd-pcm%s.ipk" % sp2[0]
                                        print("[dBackup] found %s ..." % modules)
                                        if os.path.exists("/tmp/modules.ipk"):
                                            os.remove("/tmp/modules.ipk")
                                        os.system("wget -q http://www.oozoon-dreamboxupdate.de/opendreambox/2.0/experimental/%s/%s -O /tmp/modules.ipk" % (self.boxtype, modules))
                                        if os.path.exists("/tmp/modules.ipk"):
                                            if os.path.exists("/tmp/data.tar.gz"):
                                                os.remove("/tmp/data.tar.gz")
                                            if os.path.exists("/tmp/control.tar.gz"):
                                                os.remove("/tmp/control.tar.gz")
                                            if os.path.exists("/tmp/debian-binary"):
                                                os.remove("/tmp/debian-binary")
                                            os.system("cd /tmp; ar -x /tmp/modules.ipk")
                                            os.system("tar -xzf /tmp/data.tar.gz -C /tmp/strange")
                                            os.remove("/tmp/modules.ipk")
                                            if os.path.exists("/tmp/data.tar.gz"):
                                                os.remove("/tmp/data.tar.gz")
                                            if os.path.exists("/tmp/control.tar.gz"):
                                                os.remove("/tmp/control.tar.gz")
                                            if os.path.exists("/tmp/debian-binary"):
                                                os.remove("/tmp/debian-binary")
                                if line.find("kernel-module-snd-timer") != -1:
#                                                                       print line
                                    sp = line.split("kernel-module-snd-timer")
                                    if len(sp) > 0:
#                                                                               print sp[1]
                                        sp2= sp[1].split(".ipk")
#                                                                               print sp2[0]
                                        modules="kernel-module-snd-timer%s.ipk" % sp2[0]
                                        print("[dBackup] found %s ..." % modules)
                                        if os.path.exists("/tmp/modules.ipk"):
                                            os.remove("/tmp/modules.ipk")
                                        os.system("wget -q http://www.oozoon-dreamboxupdate.de/opendreambox/2.0/experimental/%s/%s -O /tmp/modules.ipk" % (self.boxtype, modules))
                                        if os.path.exists("/tmp/modules.ipk"):
                                            if os.path.exists("/tmp/data.tar.gz"):
                                                os.remove("/tmp/data.tar.gz")
                                            if os.path.exists("/tmp/control.tar.gz"):
                                                os.remove("/tmp/control.tar.gz")
                                            if os.path.exists("/tmp/debian-binary"):
                                                os.remove("/tmp/debian-binary")
                                            os.system("cd /tmp; ar -x /tmp/modules.ipk")
                                            os.system("tar -xzf /tmp/data.tar.gz -C /tmp/strange")
                                            os.remove("/tmp/modules.ipk")
                                            if os.path.exists("/tmp/data.tar.gz"):
                                                os.remove("/tmp/data.tar.gz")
                                            if os.path.exists("/tmp/control.tar.gz"):
                                                os.remove("/tmp/control.tar.gz")
                                            if os.path.exists("/tmp/debian-binary"):
                                                os.remove("/tmp/debian-binary")
                                if line.find("kernel-module-snd-page-alloc") != -1:
#                                                                       print line
                                    sp = line.split("kernel-module-snd-page-alloc")
                                    if len(sp) > 0:
#                                                                               print sp[1]
                                        sp2= sp[1].split(".ipk")
#                                                                               print sp2[0]
                                        modules="kernel-module-snd-page-alloc%s.ipk" % sp2[0]
                                        print("[dBackup] found %s ..." % modules)
                                        if os.path.exists("/tmp/modules.ipk"):
                                            os.remove("/tmp/modules.ipk")
                                        os.system("wget -q http://www.oozoon-dreamboxupdate.de/opendreambox/2.0/experimental/%s/%s -O /tmp/modules.ipk" % (self.boxtype, modules))
                                        if os.path.exists("/tmp/modules.ipk"):
                                            if os.path.exists("/tmp/data.tar.gz"):
                                                os.remove("/tmp/data.tar.gz")
                                            if os.path.exists("/tmp/control.tar.gz"):
                                                os.remove("/tmp/control.tar.gz")
                                            if os.path.exists("/tmp/debian-binary"):
                                                os.remove("/tmp/debian-binary")
                                            os.system("cd /tmp; ar -x /tmp/modules.ipk")
                                            os.system("tar -xzf /tmp/data.tar.gz -C /tmp/strange")
                                            os.remove("/tmp/modules.ipk")
                                            if os.path.exists("/tmp/data.tar.gz"):
                                                os.remove("/tmp/data.tar.gz")
                                            if os.path.exists("/tmp/control.tar.gz"):
                                                os.remove("/tmp/control.tar.gz")
                                            if os.path.exists("/tmp/debian-binary"):
                                                os.remove("/tmp/debian-binary")
                                if line.find("kernel-module-stv0299") != -1:
#                                                                       print line
                                    sp = line.split("kernel-module-stv0299")
                                    if len(sp) > 0:
#                                                                               print sp[1]
                                        sp2= sp[1].split(".ipk")
#                                                                               print sp2[0]
                                        modules="kernel-module-stv0299%s.ipk" % sp2[0]
                                        print("[dBackup] found %s ..." % modules)
                                        if os.path.exists("/tmp/modules.ipk"):
                                            os.remove("/tmp/modules.ipk")
                                        os.system("wget -q http://www.oozoon-dreamboxupdate.de/opendreambox/2.0/experimental/%s/%s -O /tmp/modules.ipk" % (self.boxtype, modules))
                                        if os.path.exists("/tmp/modules.ipk"):
                                            if os.path.exists("/tmp/data.tar.gz"):
                                                os.remove("/tmp/data.tar.gz")
                                            if os.path.exists("/tmp/control.tar.gz"):
                                                os.remove("/tmp/control.tar.gz")
                                            if os.path.exists("/tmp/debian-binary"):
                                                os.remove("/tmp/debian-binary")
                                            os.system("cd /tmp; ar -x /tmp/modules.ipk")
                                            os.system("tar -xzf /tmp/data.tar.gz -C /tmp/strange")
                                            os.remove("/tmp/modules.ipk")
                                            if os.path.exists("/tmp/data.tar.gz"):
                                                os.remove("/tmp/data.tar.gz")
                                            if os.path.exists("/tmp/control.tar.gz"):
                                                os.remove("/tmp/control.tar.gz")
                                            if os.path.exists("/tmp/debian-binary"):
                                                os.remove("/tmp/debian-binary")
                            f.close()
                            os.system("depmod -b /tmp/strange")
                        if os.path.exists("/tmp/strange/lib"):
                            bootfile ="/boot/bootlogo-%s.elf.gz filename=/boot/recovery.jpg\n/boot/vmlinux-3.2-%s.gz console=ttyS0,115200 init=/sbin/nfiwrite rootdelay=10 root=LABEL=RECOVERY rootfstype=vfat rw\n" % (self.boxtype, self.boxtype)
                            a=open("/tmp/strange/autoexec_%s.bat" % self.boxtype, "w")
                            a.write(bootfile)
                            a.close()
                        else:
                            self.session.open(MessageBox, _("recovery stick creation failed, Sorry!"), MessageBox.TYPE_ERROR)
                            if os.path.exists(dbackup_busy):
                                os.remove(dbackup_busy)
                            return
                else:
                    if os.path.exists(dbackup_busy):
                        os.remove(dbackup_busy)
                    self.session.open(MessageBox, _("Sorry, %s device not mounted") % self.device, MessageBox.TYPE_ERROR)
                    return
    def doFlash(self, option):
        if option:
            print("[dBackup] is flashing now %s" % self.nfifile)
            self.doHide()
            FlashingImage(self.nfifile)
        else:
            print("[dBackup] cancelled flashing %s" % self.nfifile)

    def cancel(self):
        self.close(False)

    def getBackupPath(self):
        backup = []
        backup.append((config.plugins.dbackup.backuplocation.value, config.plugins.dbackup.backuplocation.value))
        for mount in os.listdir("/media"):
            backupdir="/media/%s/backup" % mount
            # added to trigger automount
            os.system("ls %s" % backupdir)
            try:
                if os.path.exists(backupdir) and backupdir != config.plugins.dbackup.backuplocation.value:
                    backup.append((backupdir, backupdir))
            except:
                pass
        if os.path.exists("/autofs"):
            for mount in os.listdir("/autofs"):
                backupdir="/autofs/%s/backup" % mount
                # added to trigger automount
                os.system("ls %s" % backupdir)
                try:
                    if os.path.exists(backupdir) and backupdir != config.plugins.dbackup.backuplocation.value:
                        backup.append((backupdir, backupdir))
                except:
                    pass
        f=open("/proc/mounts", "r")
        m = f.read()
        f.close()
        if m.find("/data") != -1:
            try:
                backupdir="/data/backup"
                if os.path.exists(backupdir) and backupdir != config.plugins.dbackup.backuplocation.value:
                    backup.append((backupdir, backupdir))
            except:
                pass
        return backup

    def backup(self):
        global dbackup_progress
        if os.path.exists(dbackup_backup):
            print("[dBackup] found finished backup ...")
            dbackup_progress=0
            self.TimerBackup = eTimer()
            self.TimerBackup.stop()
            if os.path.exists(dbackup_busy):
                os.remove(dbackup_busy)
            if config.plugins.dbackup.transparency.value < config.osd.alpha.value:
                # reset needed
                f=open("/proc/stb/video/alpha", "w")
                f.write("%i" % (config.osd.alpha.value))
                f.close()
            f=open(dbackup_backup)
            line=f.readline()
            f.close()
            os.remove(dbackup_backup)
            sp=[]
            sp=line.split(" ")
#                       print sp
            length=len(sp)
            size=""
            image=""
            path=""
            if length > 0:
                size=sp[0].rstrip().lstrip()
                sp2=[]
                sp2=sp[length-1].split("/")
                print(sp2)
                length=len(sp2)
                if length > 0:
                    image=sp2[length-1]
                    path=line.replace(size, "").replace(image, "")
                    image=image.replace(".nfi\n", "")
                    image=image.rstrip().lstrip()
            print("[dBackup] found backup %s" % line)
            # checking for IO Errors
            l=""
            if os.path.exists(dbackup_log):
                b=open(dbackup_log)
                l=b.read()
                b.close()
            if l.find("Input/output err") != -1:
                self.session.open(MessageBox, size+"B "+_("Flash Backup to %s\n\nfinished with imagename:\n\n%s.%s\n\nBUT it has I/O Errors") %(path, image, config.plugins.dbackup.backuptool.value),  MessageBox.TYPE_ERROR)
            else:
                self.session.open(MessageBox, size+"B "+_("Flash Backup to %s\n\nfinished with imagename:\n\n%s.%s") %(path, image, config.plugins.dbackup.backuptool.value),  MessageBox.TYPE_INFO)
        else:
            if os.path.exists(dbackup_busy):
                self.session.open(MessageBox, running_string, MessageBox.TYPE_ERROR)
            elif os.path.exists("/.bainfo"):
                self.session.open(MessageBox, barryallen_string, MessageBox.TYPE_ERROR)
            elif os.path.exists("/.lfinfo"):
                self.session.open(MessageBox, lowfat_string, MessageBox.TYPE_ERROR)
            else:
                if config.plugins.dbackup.flashtool.value == "rescue":
                    backup = []
                    backup.append(("/data/.recovery"))
                    f=open("/proc/stb/info/model")
                    self.boxtype=f.read()
                    f.close()
                    self.boxtype=self.boxtype.replace("\n", "").replace("\l", "")
                    if self.boxtype == "dm525":
                        self.boxtype="dm520"
                    self.askForBackupPath(backup)
                else:
                    if config.plugins.dbackup.backupaskdir.value:
                        self.session.openWithCallback(self.askForBackupPath, ChoiceBox, _("select backup path"), self.getBackupPath())
                    else:
                        backup = []
                        backup.append((config.plugins.dbackup.backuplocation.value))
                        self.askForBackupPath(backup)

    def askForBackupPath(self, backup_path):
#               self.imagetype=""
        self.creator=""
        if backup_path is None:
            self.session.open(MessageBox, _("nothing entered"),  MessageBox.TYPE_ERROR)
            return
        print(backup_path)
        path=backup_path[0]
        print("[dBACKUP] ", path)
        if path == "/data/.recovery":
            if not os.path.exists("/data"):
                os.mkdir("/data")
            if boxtype != "dm520":
                os.system("umount /dev/mmcblk0p2; mount /dev/mmcblk0p2 /data")
            else:
                os.system("umount %s; mount %s /data" % (dreambox_data, dreambox_data))
            os.system("mount -o remount,async /data")
            f=open("/proc/mounts", "r")
            mounts=f.read()
            f.close()
            if mounts.find("/data") == -1:
                self.session.open(MessageBox, mounted_string % path,  MessageBox.TYPE_ERROR)
                return
            if not os.path.exists("/data/.recovery"):
                os.mkdir("/data/.recovery")
            self.backupname="backup"
            self.askForBackupName("backup")
        else:
            if not os.path.exists(path):
                os.system("ls %s" % path)
            sp=[]
            sp=path.split("/")
            print("[dBACKUP] ", sp)
            if len(sp) > 1:
                if sp[1] != "media" and sp[1] != "autofs" and sp[1] != "data":
                    print("[dBACKUP] NOT #1 ", sp[1])
                    self.session.open(MessageBox, mounted_string % path,  MessageBox.TYPE_ERROR)
                    return
            if sp[1] != "data":
                f=open("/proc/mounts", "r")
                m = f.read()
                f.close()
                print(m)
                if m.find("/media/%s" % sp[2]) == -1 and m.find("/autofs/%s" % sp[2]) == -1:
                    print("[dBACKUP] NOT #2 ", sp[2])
                    self.session.open(MessageBox, mounted_string % path,  MessageBox.TYPE_ERROR)
                    return
            path=path.lstrip().rstrip("/").rstrip().replace(" ", "")
            # remember for next time
            config.plugins.dbackup.backuplocation.value=path
            config.plugins.dbackup.backuplocation.save()
            if not os.path.exists(config.plugins.dbackup.backuplocation.value):
                os.mkdir(config.plugins.dbackup.backuplocation.value, 0o777)
            f=open("/proc/stb/info/model")
            self.boxtype=f.read()
            f.close()
            self.boxtype=self.boxtype.replace("\n", "").replace("\l", "")
            if self.boxtype == "dm525":
                self.boxtype="dm520"
            name="dreambox-image"
            if os.path.exists("/etc/image-version"):
                f=open("/etc/image-version")
                line = f.readline()
                while (line):
                    line = f.readline()
                    if line.startswith("creator="):
                        name=line
                f.close()
                name=name.replace("creator=", "")
                sp=[]
                if len(name) > 0:
                    sp=name.split(" ")
                    if len(sp) > 0:
                        name=sp[0]
                        name=name.replace("\n", "")
            self.creator=name.rstrip().lstrip()
#                       self.imagetype="exp"
#                       if name == "OoZooN" and os.path.exists("/etc/issue.net"):
#                               f=open("/etc/issue.net")
#                               i=f.read()
#                               f.close()
#                               if (i.find("xperimental") is -1) and (i.find("unstable") is -1):
#                                       self.imagetype="rel"
            cdate=str(datetime.date.today())
            ctime=str(time.strftime("%H-%M"))
            suggested_backupname=name
            if config.plugins.dbackup.backupdeb.value:
                suggested_backupname=suggested_backupname+"-deb"
            if config.plugins.dbackup.backupboxtype.value:
                suggested_backupname=suggested_backupname+"-"+self.boxtype
#                       if config.plugins.dbackup.backupimagetype.value:
#                               suggested_backupname=suggested_backupname+"-"+self.imagetype
            if config.plugins.dbackup.backupdate.value:
                suggested_backupname=suggested_backupname+"-"+cdate
            if config.plugins.dbackup.backuptime.value:
                suggested_backupname=suggested_backupname+"-"+ctime
            if config.plugins.dbackup.flashtool.value == "rescue":
                suggested_backupname="backup"
            print("[dBACKUP] suggested backupname %s" % suggested_backupname)
            blanks=""
            i = 0
            blanks_len=int(config.plugins.dbackup.backupblanks.value)
            while i < blanks_len:
                blanks=blanks+" "
                i+=1
            length_blanks=len(blanks)
            print("[dBACKUP] BLANKS %d" % length_blanks)
            suggested_backupname=suggested_backupname+blanks
            blanks_len=blanks_len+60
            self.session.openWithCallback(self.askForBackupName, InputBox, title=backupimage_string, text=suggested_backupname, maxSize=blanks_len, type=Input.TEXT)

    def askForBackupName(self, name):
        if name is None:
            self.session.open(MessageBox, _("nothing entered"),  MessageBox.TYPE_ERROR)
        else:
            self.backupname=name.replace(" ", "").replace("[", "").replace("]", "").replace(">", "").replace("<", "").replace("|", "").rstrip().lstrip()
            if self.backupname.find(self.boxtype) == -1 and config.plugins.dbackup.flashtool.value != "rescue":
                self.backupname=self.backupname+"-"+self.boxtype
            if os.path.exists("%s/%s.%s" % (config.plugins.dbackup.backuplocation.value, self.backupname, config.plugins.dbackup.backuptool.value)):
                self.session.openWithCallback(self.confirmedBackup, MessageBox, "%s.%s" % (self.backupname, config.plugins.dbackup.backuptool.value) +"\n"+_("already exists,")+" "+_("overwrite ?"), MessageBox.TYPE_YESNO)
            else:
                self.confirmedBackup(True)

    def confirmedBackup(self, answer):
        if answer:
            if os.path.exists("%s/%s.%s" % (config.plugins.dbackup.backuplocation.value, self.backupname, config.plugins.dbackup.backuptool.value)):
                os.remove("%s/%s.%s" % (config.plugins.dbackup.backuplocation.value, self.backupname, config.plugins.dbackup.backuptool.value))
            if os.path.exists("%s/%s.sig" % (config.plugins.dbackup.backuplocation.value, self.backupname)):
                os.remove("%s/%s.sig" % (config.plugins.dbackup.backuplocation.value, self.backupname))
            self.session.openWithCallback(self.startBackup, MessageBox, _("Press OK for starting backup to") + "\n\n%s.%s" % (self.backupname, config.plugins.dbackup.backuptool.value) + "\n\n" + _("Be patient, this takes 1-2 min ..."), MessageBox.TYPE_INFO)
        else:
            self.session.open(MessageBox, _("not confirmed"),  MessageBox.TYPE_ERROR)

    def startBackup(self, answer):
        if answer:
            print("[dBackup] is doing backup now ...")
            self["logo"].instance.setPixmapFromFile("%s/ring.png" % dbackup_plugindir)
            self.doHide()
            self.backuptime=0
            self.TimerBackup = eTimer()
            self.TimerBackup.stop()
            if not os.path.exists("/var/lib/opkg/status"):
                self.TimerBackup_conn = self.TimerBackup.timeout.connect(self.backupFinishedCheck)
            else:
                self.TimerBackup.callback.append(self.backupFinishedCheck)
            self.TimerBackup.start(10000, True)
            BackupImage(self.backupname)
        else:
            print("[dBackup] was not confirmed")

    def backupFinishedCheck(self):
        global dbackup_progress
        self.backuptime=self.backuptime+10
        if not os.path.exists(dbackup_backup):
            # not finished - continue checking ...
            rsize=0
            working="%s/%s.%s" % (config.plugins.dbackup.backuplocation.value, self.backupname, config.plugins.dbackup.backuptool.value)
            print(working)
            if os.path.exists(working):
                rsize=os.path.getsize(working)
            total_size=rsize
            st = os.statvfs("/")
            rused = (st.f_blocks - st.f_bfree) * st.f_frsize
            if boxtype=="dm520":
                used=rused*3
            else:
                used=rused
            if used < 0:
                used=0
            print("[dBackup] total size %d used %d\n" % (total_size, used))
            if total_size > 0:
# for xz
#                               dbackup_progress=300*total_size/used
# for gz
                dbackup_progress=6*250*total_size/used
            else:
                dbackup_progress=self.backuptime
            self.slider.setValue(dbackup_progress)
            print("[dBackup] checked if backup is finished after %d sec ..." % self.backuptime)
            self.TimerBackup.start(10000, True)
        else:
            print("[dBackup] found finished backup ...")
            dbackup_progress=0
            self.slider.setValue(0)
            self.TimerBackup = eTimer()
            self.TimerBackup.stop()
            if os.path.exists(dbackup_busy):
                os.remove(dbackup_busy)
            f=open(dbackup_backup)
            line=f.readline()
            f.close()
            os.remove(dbackup_backup)
            sp=[]
            sp=line.split(" ")
            print(sp)
            length=len(sp)
            size=""
            image=""
            path=""
            if length > 0:
                size=sp[0].rstrip().lstrip()
                sp2=[]
                sp2=sp[length-1].split("/")
                print(sp2)
                length=len(sp2)
                if length > 0:
                    image=sp2[length-1]
                    path=line.replace(size, "").replace(image, "").lstrip().rstrip()
                    image=image.replace(".tar.gz\n", "").replace(".tar.xz\n", "").replace(".tar.bz2\n", "").replace(".tar\n", "")
                else:
                    image=""
            if config.plugins.dbackup.transparency.value < config.osd.alpha.value:
                # reset needed
                f=open("/proc/stb/video/alpha", "w")
                f.write("%i" % (config.osd.alpha.value))
                f.close()
                self.DimmingTimer = eTimer()
                self.DimmingTimer.stop()
            print("[dBackup] found backup %s" % line)
            # checking for IO Errors
            l=""
            if os.path.exists(dbackup_log):
                b=open(dbackup_log)
                l=b.read()
                b.close()
            if config.plugins.dbackup.flashtool.value == "rescue":
                os.system("umount /data")
            try:
                if l.find("Input/output err") != -1:
                    self.session.open(MessageBox, "%sB " %(size) +_("Flash Backup to %s\n\nfinished with imagename:\n\n%s.%s\n\nBUT it has I/O Errors") %(path, image, config.plugins.dbackup.backuptool.value),  MessageBox.TYPE_ERROR)
                else:
                    self.session.open(MessageBox, "%sB " %(size) +_("Flash Backup to %s\n\nfinished with imagename:\n\n%s.%s") %(path, image, config.plugins.dbackup.backuptool.value),  MessageBox.TYPE_INFO)
            except:
                # why crashes even this
#                               self.session.open(MessageBox,_("Flash Backup to %s finished with imagename:\n\n%s.%s") % (path,image,config.plugins.dbackup.backuptool.value),  MessageBox.TYPE_INFO)
                self.session.open(MessageBox, _("Flash Backup finished"),  MessageBox.TYPE_INFO)

    def config(self):
        if os.path.exists(dbackup_busy):
            self.session.open(MessageBox, running_string, MessageBox.TYPE_ERROR)
        else:
            self.session.open(dBackupConfiguration)

def startdBackup(session, **kwargs):
    session.open(dBackup)

def startRecover(session, **kwargs):
    session.openWithCallback(startRecovery, MessageBox, _("Recovery Mode")+" "+_("Really shutdown now?"), MessageBox.TYPE_YESNO)

def startRecovery(option):
    if option:
        print("[dBACKUP] starting Recovery")
        b=open("/proc/stb/fp/boot_mode", "w")
        b.write("rescue")
        b.close()
        quitMainloop(2)
    else:
        print("[dBACKUP] cancelled Recovery")

def recovery2Webif(enable):
    if enable:
        print("[dBACKUP] recovery webinterface enabling")
    else:
        print("[dBACKUP] recovery webinterface disabling")
    if os.path.exists("/usr/lib/enigma2/python/Plugins/Extensions/WebInterface/WebComponents/Sources/PowerState.py"):
        p=open("/usr/lib/enigma2/python/Plugins/Extensions/WebInterface/WebComponents/Sources/PowerState.py")
        ps=p.read()
        p.close()
        if enable:
            if ps.find("type == 99:") == -1:
                print("[dBACKUP] recovery webinterface inserting #1")
                ps2=ps.replace("type = int(self.cmd)", "type = int(self.cmd)\n\n                 if type == 99:\n                                b=open(\"/proc/stb/fp/boot_mode\",\"w\")\n                              b.write(\"rescue\")\n                           b.close()\n                             type=2\n")
                p=open("/usr/lib/enigma2/python/Plugins/Extensions/WebInterface/WebComponents/Sources/PowerState.py", "w")
                p.write(ps2)
                p.close()
        else:
            if ps.find("type == 99:") != -1:
                print("[dBACKUP] recovery webinterface removing #1")
                ps2=ps.replace("type = int(self.cmd)\n\n                        if type == 99:\n                                b=open(\"/proc/stb/fp/boot_mode\",\"w\")\n                              b.write(\"rescue\")\n                           b.close()\n                             type=2\n", "type = int(self.cmd)")
                p=open("/usr/lib/enigma2/python/Plugins/Extensions/WebInterface/WebComponents/Sources/PowerState.py", "w")
                p.write(ps2)
                p.close()
    if os.path.exists("/usr/lib/enigma2/python/Plugins/Extensions/WebInterface/web-data/core.js"):
        p=open("/usr/lib/enigma2/python/Plugins/Extensions/WebInterface/web-data/core.js")
        cs=p.read()
        p.close()
        if enable:
            if cs.find("rebootsetup") == -1:
                print("[dBACKUP] recovery webinterface inserting #2")
                cs2=cs.replace("\'gui\' : 3", "\'gui\' : 3, \'rebootsetup\' : 99")
                p=open("/usr/lib/enigma2/python/Plugins/Extensions/WebInterface/web-data/core.js", "w")
                p.write(cs2)
                p.close()
        else:
            if cs.find("rebootsetup") != -1:
                print("[dBACKUP] recovery webinterface removing #2")
                cs2=cs.replace("\'gui\' : 3, \'rebootsetup\' : 99", "\'gui\' : 3")
                p=open("/usr/lib/enigma2/python/Plugins/Extensions/WebInterface/web-data/core.js", "w")
                p.write(cs2)
                p.close()
    if os.path.exists("/usr/lib/enigma2/python/Plugins/Extensions/WebInterface/web-data/tpl/default/index.html"):
        p=open("/usr/lib/enigma2/python/Plugins/Extensions/WebInterface/web-data/tpl/default/index.html")
        ix=p.read()
        p.close()
        if enable:
            if ix.find("rebootsetup") == -1:
                print("[dBACKUP] recovery webinterface inserting #3")
                ix2=ix.replace("data-state=\"gui\">Restart GUI</a></li>", "data-state=\"gui\">Restart GUI</a></li>\n                                                             <li><a href=\"#\" class=\"powerState\" data-state=\"rebootsetup\">Recovery Mode</a></li>")
                p=open("/usr/lib/enigma2/python/Plugins/Extensions/WebInterface/web-data/tpl/default/index.html", "w")
                p.write(ix2)
                p.close()
        else:
            if ix.find("rebootsetup") != -1:
                print("[dBACKUP] recovery webinterface removing #3")
                ix2=ix.replace("data-state=\"gui\">Restart GUI</a></li>\n                                                               <li><a href=\"#\" class=\"powerState\" data-state=\"rebootsetup\">Recovery Mode</a></li>", "data-state=\"gui\">Restart GUI</a></li>")
                ix2=ix.replace("data-state=\"gui\">Restart GUI</a></li>\n                                                               <li><a href=\"#\" class=\"powerState\" data-state=\"rebootsetup\">Recovery</a></li>", "data-state=\"gui\">Restart GUI</a></li>")
                p=open("/usr/lib/enigma2/python/Plugins/Extensions/WebInterface/web-data/tpl/default/index.html", "w")
                p.write(ix2)
                p.close()
    if os.path.exists("/usr/lib/enigma2/python/Plugins/Extensions/WebInterface/web-data/tpl/default/tplPower.htm"):
        p=open("/usr/lib/enigma2/python/Plugins/Extensions/WebInterface/web-data/tpl/default/tplPower.htm")
        df=p.read()
        p.close()
        if enable:
            if df.find("rebootsetup") == -1:
                print("[dBACKUP] recovery webinterface inserting #4")
                df2=df.replace("data-state=\"gui\">${strings.restart_enigma2}</button></td>", "data-state=\"gui\">${strings.restart_enigma2}</button></td>\n                                                                             </tr>\n                                                                         <tr>\n                                                                                  <td><button class=\"w200h50 powerState\" data-state=\"rebootsetup\">Recovery Mode</button></td>")
                p=open("/usr/lib/enigma2/python/Plugins/Extensions/WebInterface/web-data/tpl/default/tplPower.htm", "w")
                p.write(df2)
                p.close()
        else:
            if df.find("rebootsetup") != -1:
                print("[dBACKUP] recovery webinterface removing #4")
                df2=df.replace("data-state=\"gui\">${strings.restart_enigma2}</button></td>\n                                                                   </tr>\n                                                                 <tr>\n                                                                          <td><button class=\"w200h50 powerState\" data-state=\"rebootsetup\">Recovery Mode</button></td>", "data-state=\"gui\">${strings.restart_enigma2}</button></td>")
                df2=df.replace("data-state=\"gui\">${strings.restart_enigma2}</button></td>\n                                                                   </tr>\n                                                                 <tr>\n                                                                          <td><button class=\"w200h50 powerState\" data-state=\"rebootsetup\">Recovery</button></td>", "data-state=\"gui\">${strings.restart_enigma2}</button></td>")
                p=open("/usr/lib/enigma2/python/Plugins/Extensions/WebInterface/web-data/tpl/default/tplPower.htm", "w")
                p.write(df2)
                p.close()
    return

def autostart(reason,**kwargs):
    if "session" in kwargs and reason == 0:
        session = kwargs["session"]
        print("[dBackup] autostart")
        if os.path.exists(dbackup_busy):
            os.remove(dbackup_busy)
        tmp_extract="%s/tmp" % config.plugins.dbackup.backuplocation.value
        if os.path.exists(tmp_extract):
            shutil.rmtree(tmp_extract, True)
        if config.plugins.dbackup.flashtool.value == "rescue":
            config.plugins.dbackup.backuplocation.value = "/data/.recovery"
            config.plugins.dbackup.backuptool.value = "tar.gz"
            config.plugins.dbackup.backuplocation.save()
            config.plugins.dbackup.backuptool.save()
        if config.plugins.dbackup.recovering.value == "webif" or config.plugins.dbackup.recovering.value == "both":
            recovery2Webif(True)
        else:
            recovery2Webif(False)
        return

def sessionstart(reason, **kwargs):
    if reason == 0 and "session" in kwargs:
        if os.path.exists("/usr/lib/enigma2/python/Plugins/Extensions/WebInterface/WebChilds/Toplevel.py"):
            from Plugins.Extensions.WebInterface.WebChilds.Toplevel import addExternalChild
            addExternalChild( ("dbackup", wBackup(), "dBackup", "1", True) )
        else:
            print("[dBackup] Webif not found")

def main(session,**kwargs):
    session.open(dBackup)
def Plugins(**kwargs):
    return [PluginDescriptor(where = [PluginDescriptor.WHERE_SESSIONSTART, PluginDescriptor.WHERE_AUTOSTART], fnc = autostart),
                               PluginDescriptor(name=backup_string+" & "+flashing_string, description=backup_string+" & "+flashing_string, where = PluginDescriptor.WHERE_PLUGINMENU, icon="dbackup.png", fnc=main),
                               PluginDescriptor(where=PluginDescriptor.WHERE_SESSIONSTART, fnc=sessionstart, needsRestart=False)]





def mainconf(menuid):
    if menuid != "setup":
        return [ ]
    return [(backup_string+" & "+flashing_string, startdBackup, "dbackup", None)]

###############################################################################
# dBackup Webinterface by gutemine
###############################################################################

class wBackup(resource.Resource):

    def render_GET(self, req):
        global dbackup_progress, dreambox_data
        file = req.args.get("file", None)
        directory = req.args.get("directory", None)
        command = req.args.get("command", None)
        print("[dBackup] received %s %s %s" % (command, directory, file))
        req.setResponseCode(http.OK)
        req.setHeader('Content-type', 'text/html')
        req.setHeader('charset', 'UTF-8')
        if not config.plugins.dbackup.webinterface.value:
            return header_string+nowebif_string
        if os.path.exists("/usr/lib/enigma2/python/Plugins/Extensions/WebInterface/web-data/img/dbackup.png") is False:
            os.symlink("%s/dbackup.png" % dbackup_plugindir, "/usr/lib/enigma2/python/Plugins/Extensions/WebInterface/web-data/img/dbackup.png")
        if os.path.exists("/usr/lib/enigma2/python/Plugins/Extensions/WebInterface/web-data/img/ring.png") is False:
            os.symlink("%s/ring.png" % dbackup_plugindir, "/usr/lib/enigma2/python/Plugins/Extensions/WebInterface/web-data/img/ring.png")
        if os.path.exists(dbackup_busy):
            dbackup_backuping_progress  =""
            dbackup_backuping_progress += header_string
            dbackup_backuping_progress += "<br>%s<br><br>" % running_string
            dbackup_backuping_progress +="<br><img src=\"/web-data/img/ring.png\" alt=\"%s ...\"/><br><br>" % (backup_string)
            if dbackup_progress > 0:
                dbackup_backuping_progress +="<div style=\"background-color:yellow;width:%dpx;height:20px;border:1px solid #000\"></div> " % (dbackup_progress)
            dbackup_backuping_progress +="<br><form method=\"GET\">"
            dbackup_backuping_progress +="<input name=\"command\" type=\"submit\" size=\"100px\" title=\"%s\" value=\"%s\">" % (refresh_string, "Refresh")
            dbackup_backuping_progress +="</form>"
            return header_string+dbackup_backuping_progress
        if command is None or command[0] == "Refresh":
            htmlbackup=""
            htmlbackup += "<option value=\"%s\" class=\"black\">%s</option>\n" % (config.plugins.dbackup.backuplocation.value, config.plugins.dbackup.backuplocation.value)
            if config.plugins.dbackup.backupaskdir.value:
                for mount in os.listdir("/media"):
                    backupdir="/media/%s/backup" % mount
                    # added to trigger automount
                    os.system("ls %s" % backupdir)
                    try:
                        if os.path.exists(backupdir) and backupdir != config.plugins.dbackup.backuplocation.value:
                            htmlbackup += "<option value=\"%s\" class=\"black\">%s</option>\n" % (backupdir, backupdir)
                    except:
                        pass
                if os.path.exists("/autofs"):
                    for mount in os.listdir("/autofs"):
                        backupdir="/autofs/%s/backup" % mount
                        # added to trigger automount
                        os.system("ls %s" % backupdir)
                        try:
                            if os.path.exists(backupdir) and backupdir != config.plugins.dbackup.backuplocation.value:
                                htmlbackup += "<option value=\"%s\" class=\"black\">%s</option>\n" % (backupdir, backupdir)
                        except:
                            pass
                f=open("/proc/mounts", "r")
                m = f.read()
                f.close()
                if m.find("/data") != -1:
                    try:
                        backupdir="/data/backup"
                        if os.path.exists(backupdir) and backupdir != config.plugins.dbackup.backuplocation.value:
                            htmlbackup += "<option value=\"%s\" class=\"black\">%s</option>\n" % (backupdir, backupdir)
                    except:
                        pass
            print("[dBACKUP] ", htmlbackup)
            f=open("/proc/stb/info/model")
            self.boxtype=f.read()
            f.close()
            self.boxtype=self.boxtype.replace("\n", "").replace("\l", "")
            if self.boxtype == "dm525":
                self.boxtype="dm520"

            list = []
            htmlnfi=""
            htmlnfi += "<option value=\"%s\" class=\"black\">%s</option>\n" % ("recovery", _("Recovery Image from Feed"))
            htmlnfi += "<option value=\"%s\" class=\"black\">%s</option>\n" % ("rescue", _("Rescue Bios from Feed"))
            entries=os.listdir("/tmp")
            for name in sorted(entries):
                if (name.endswith(".tar.gz") or name.endswith("tar.xz") or name.endswith("tar.bz2") or name.endswith(".tar") or name.endswith(".zip")) and not name.startswith("enigma2settings") and not name.endswith("enigma2settingsbackup.tar.gz"):
                    name2=name.replace(".tar.gz", "").replace(".tar.xz", "").replace(".tar.bz2", "").replace(".tar", "").replace(".zip", "")
                    if  list.count(name2) < 1 and name2.find(self.boxtype) != -1:
                        list.append(( name2, "/tmp/%s" % name ))
                        htmlnfi += "<option value=\"/tmp/%s\" class=\"black\">%s</option>\n" % (name, name2)
                    else:
                        print("[dBackup] skips %s" % name2)
            if os.path.exists(config.plugins.dbackup.backuplocation.value):
                entries=os.listdir(config.plugins.dbackup.backuplocation.value)
                for name in sorted(entries):
                    if (name.endswith(".tar.gz") or name.endswith("tar.xz") or name.endswith("tar.bz2") or name.endswith(".tar") or name.endswith(".zip")) and not name.startswith("enigma2settings") and not name.endswith("enigma2settingsbackup.tar.gz"):
                        name2=name.replace(".tar.gz", "").replace(".tar.xz", "").replace(".tar.bz2", "").replace(".tar", "").replace(".zip", "")
                        if  list.count(name2) < 1 and name2.find(self.boxtype) != -1:
                            list.append(( name2, "%s/%s" % (config.plugins.dbackup.backuplocation.value, name) ))
                            htmlnfi += "<option value=\"%s/%s\" class=\"black\">%s</option>\n" % (config.plugins.dbackup.backuplocation.value, name, name2)
                        else:
                            print("[dBackup] skips %s" % name2)
            f=open("/proc/mounts", "r")
            m = f.read()
            f.close()
            if m.find("/data") != -1:
                if os.path.exists("/data/backup") and "/data/backup" != config.plugins.dbackup.backuplocation.value:
                    for name in os.listdir("/data/backup"):
                        if (name.endswith(".tar.gz") or name.endswith(".tar.xz") or name.endswith(".tar.bz2") or name.endswith(".tar") or name.endswith(".zip")) and not name.startswith("enigma2settings") and not name.endswith("enigma2settingsbackup.tar.gz"):
                            name2=name.replace(".tar.gz", "").replace(".tar.xz", "").replace(".tar.bz2", "").replace(".tar", "").replace(".zip", "")
                            if  list.count(name2) < 1 and name2.find(self.boxtype) != -1:
                                list.append(( name2, "/data/backup/%s" % (name) ))
                                htmlnfi += "<option value=\"/data/backup/%s\" class=\"black\">%s</option>\n" % (name, name2)
                            else:
                                print("[dBackup] skips %s" % name2)
            entries=os.listdir("/media")
            for directory in sorted(entries):
                if os.path.exists("/media/%s/backup" % directory) and os.path.isdir("/media/%s/backup" % directory) and not directory.endswith("net") and not directory.endswith("hdd") and "/media/%s/backup" % directory != config.plugins.dbackup.backuplocation.value:
                    try:
                        for name in os.listdir("/media/%s/backup" % directory):
                            if (name.endswith(".tar.gz") or name.endswith("tar.xz") or name.endswith("tar.bz2") or name.endswith(".tar") or name.endswith(".zip")) and not name.startswith("enigma2settings") and not name.endswith("enigma2settingsbackup.tar.gz"):
                                name2=name.replace(".tar.gz", "").replace(".tar.xz", "").replace(".tar.bz2", "").replace(".tar", "").replace(".zip", "")
                                if  list.count(name2) < 1 and name2.find(self.boxtype) != -1:
                                    list.append(( name2, "/media/%s/backup/%s" % (drectory, name) ))
                                    htmlnfi += "<option value=\"/media/%s/backup/%s\" class=\"black\">%s</option>\n" % (directory, name, name2)
                                else:
                                    print("[dBackup] skips %s" % name2)
                    except:
                        pass
            entries=os.listdir("/autofs")
            for directory in sorted(entries):
                if os.path.exists("/autofs/%s/backup" % directory) and os.path.isdir("/autofs/%s/backup" % directory) and "/autofs/%s/backup" % directory != config.plugins.dbackup.backuplocation.value:
                    try:
                        for name in os.listdir("/autofs/%s/backup" % directory):
                            if (name.endswith(".tar.gz") or name.endswith("tar.xz") or name.endswith("tar.bz2") or name.endswith(".tar") or name.endswith(".zip")) and not name.startswith("enigma2settings") and not name.endswith("enigma2settingsbackup.tar.gz"):
                                name2=name.replace(".tar.gz", "").replace(".tar.xz", "").replace(".tar.bz2", "").replace(".tar", "").replace(".zip", "")
                                if  list.count(name2) < 1 and name2.find(self.boxtype) != -1:
                                    list.append(( name2, "/autofs/%s/backup/%s" % (drectory, name) ))
                                    htmlnfi += "<option value=\"/autofs/%s/backup/%s\" class=\"black\">%s</option>\n" % (directory, name, name2)
                                else:
                                    print("[dBackup] skips %s" % name2)
                    except:
                        pass
            print("[dBACKUP] ", htmlnfi)

            name="dreambox-image"
            if os.path.exists("/etc/image-version"):
                f=open("/etc/image-version")
                line = f.readline()
                while (line):
                    line = f.readline()
                    if line.startswith("creator="):
                        name=line
                f.close()
                name=name.replace("creator=", "")
                sp=[]
                if len(name) > 0:
                    sp=name.split(" ")
                    if len(sp) > 0:
                        name=sp[0]
                        name=name.replace("\n", "")
            self.creator=name.rstrip().lstrip()
#                       self.imagetype="exp"
#                       if name == "OoZooN" and os.path.exists("/etc/issue.net"):
#                               f=open("/etc/issue.net")
#                               i=f.read()
#                               f.close()
#                               if (i.find("xperimental") is -1) and (i.find("unstable") is -1):
#                                       self.imagetype="rel"
            cdate=str(datetime.date.today())
            ctime=str(time.strftime("%H-%M"))
            suggested_backupname=name
            if config.plugins.dbackup.backupdeb.value:
                suggested_backupname=suggested_backupname+"-deb"
            if config.plugins.dbackup.backupboxtype.value:
                suggested_backupname=suggested_backupname+"-"+self.boxtype
#                       if config.plugins.dbackup.backupimagetype.value:
#                               suggested_backupname=suggested_backupname+"-"+self.imagetype
            if config.plugins.dbackup.backupdate.value:
                suggested_backupname=suggested_backupname+"-"+cdate
            if config.plugins.dbackup.backuptime.value:
                suggested_backupname=suggested_backupname+"-"+ctime
            if config.plugins.dbackup.flashtool.value == "rescue":
                suggested_backupname="backup"
            print("[dBACKUP] suggested backupname %s" % suggested_backupname)
            blanks=""
            i = 0
            blanks_len=int(config.plugins.dbackup.backupblanks.value)
            while i < blanks_len:
                blanks=blanks+" "
                i+=1
            length_blanks=len(blanks)
            print("[dBACKUP] BLANKS %d" % length_blanks)
            suggested_backupname=suggested_backupname+blanks
            blanks_len=blanks_len+60
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
            """ % (header_string, plugin_string, info_header, disclaimer_wstring, fileupload_string, htmlnfi, flashing_string, "Flashing", flashing_string, backupdirectory_string, backupimage_string, htmlbackup, blanks_len, suggested_backupname, backup_string, "Backup", backup_string)
        else:
            if command[0]=="Flashing":
                k=open("/proc/cmdline", "r")
                cmd=k.read()
                k.close()
                if boxtype == "dm520":
                    rootfs="root=ubi0:dreambox-rootfs"
                else:
                    rootfs="root=/dev/mmcblk0"
                if os.path.exists("/.bainfo"):
                    return header_string+noflashing_string
                elif os.path.exists("/.lfinfo"):
                    return header_string+noflashing_string
                elif cmd.find(rootfs) == -1:
                    return header_string+noflashing_string
                # file command is received and we are in Flash - let the fun begin ...
                self.nfifile=file[0]
                if self.nfifile != "rescue" and self.nfifile != "recovery" and self.nfifile.find(boxtype) == -1:
                    return header_string+noboxtype_string
                if os.path.exists(self.nfifile):
                    if self.nfifile.endswith(".tar.gz"):
                        print("[dBackup] is flashing now %s" % self.nfifile)
                        FlashingImage(self.nfifile)
                        return dbackup_flashing
                    elif self.nfifile.endswith(".tar.xz"):
                        if os.path.exists("%s/bin/xz" % dbackup_plugindir) or os.path.exists("/usr/bin/xz"):
                            print("[dBackup] is flashing now %s" % self.nfifile)
                            FlashingImage(self.nfifile)
                            return dbackup_flashing
                        else:
                            print("[dBackup] xz binary missing")
                            return header_string+noxz_string
                    elif self.nfifile.endswith(".tar.bz2"):
                        print("[dBackup] is flashing now %s" % self.nfifile)
                        FlashingImage(self.nfifile)
                        return dbackup_flashing
                    elif self.nfifile.endswith(".tar"):
                        print("[dBackup] is flashing now %s" % self.nfifile)
                        FlashingImage(self.nfifile)
                        return dbackup_flashing
                    else:
                        print("[dBackup] wrong filename")
                        return header_string+notar_string
                else:
                    if self.nfifile == "recovery":
                        print("[dBackup] is flashing now %s" % self.nfifile)
                        FlashingImage(self.nfifile)
                        return dbackup_flashing
                    else:
                        print("[dBackup] filename not found")
                        return header_string+notar_string

            elif command[0]=="Backup":
                if os.path.exists("/.bainfo"):
                    return header_string+" "+barryallen_string+", "+dbackup_backbutton
                elif os.path.exists("/.lfinfo"):
                    return header_string+" "+lowfat_string+", "+dbackup_backbutton
                if config.plugins.dbackup.flashtool.value == "rescue":
                    path="/data/.recovery"
                    if not os.path.exists("/data"):
                        os.mkdir("/data")
                    if boxtype != "dm520":
                        os.system("umount /dev/mmcblk0p2; mount /dev/mmcblk0p2 /data")
                    else:
                        os.system("umount %s; mount %s /data" % (dreambox_data, dreambox_data))
                    os.system("mount -o remount,async /data")
                    f=open("/proc/mounts", "r")
                    mounts=f.read()
                    f.close()
                    if mounts.find("/data") == -1:
                        return header_string+" "+mounted_string % path +", "+dbackup_backbutton
                    if not os.path.exists("/data/.recovery"):
                        os.mkdir("/data/.recovery")
                    if os.path.exists("/data/.recovery/backup.tar.gz"):
                        os.remove("/data/.recovery/backup.tar.gz")
                    self.backupname="backup"
                else:
                    self.backupname=file[0].replace(" ", "").replace("[", "").replace("]", "").replace(">", "").replace("<", "").replace("|", "").rstrip().lstrip()
                    if self.backupname.find(boxtype) == -1:
                        self.backupname=self.backupname+"-"+boxtype
                    path=directory[0]
                if config.plugins.dbackup.flashtool.value != "rescue":
                    if not os.path.exists(path):
                        os.system("ls %s" % path)
                    sp=[]
                    sp=path.split("/")
                    print("[dBACKUP] ", sp)
                    if len(sp) > 1:
                        if sp[1] != "media" and sp[1] != "autofs" and sp[1] != "data":
                            print("[dBACKUP] NOT #1 ", sp[1])
                            return header_string+" "+mounted_string % path +", "+dbackup_backbutton
                    if sp[1] != "data":
                        f=open("/proc/mounts", "r")
                        m = f.read()
                        f.close()
                        if m.find("/media/%s" % sp[2]) == -1 and m.find("/autofs/%s" % sp[2]) == -1:
                            print("[dBACKUP] NOT #2 ", sp[2])
                            return header_string+" "+mounted_string % path +", "+dbackup_backbutton
                path=path.lstrip().rstrip("/").rstrip().replace(" ", "")
                config.plugins.dbackup.backuplocation.value=path
                config.plugins.dbackup.backuplocation.save()
                if not os.path.exists(config.plugins.dbackup.backuplocation.value):
                    os.mkdir(config.plugins.dbackup.backuplocation.value, 0o777)
                if os.path.exists("%s/%s.%s" % (config.plugins.dbackup.backuplocation.value, self.backupname, config.plugins.dbackup.backuptool.value)):
                    print("[dBackup] filename already exists")
                    return header_string+self.backupname+"."+config.plugins.dbackup.backuptool.value+" "+_("already exists,")+" "+dbackup_backbutton
                else:
                    if self.backupname.endswith(".tar") or self.backupname.endswith(".tar.gz") or self.backupname.endswith(".tar.bz2") or self.backupname.endswith(".tar.xz") or len(self.backupname) < 1:
                        print("[dBackup] filename with .tar.*")
                        return header_string+notar_string+", "+dbackup_backbutton
                    elif self.backupname.find(" ") != -1:
                        print("[dBackup] filename with blank")
                        return header_string+notar_string+", "+dbackup_backbutton
                    else:
                        # backupfile request
                        self.backuptime=0
                        self.TimerBackup = eTimer()
                        self.TimerBackup.stop()
                        if not os.path.exists("/var/lib/opkg/status"):
                            self.TimerBackup_conn = self.TimerBackup.timeout.connect(self.backupFinishedCheck)
                        else:
                            self.TimerBackup.callback.append(self.backupFinishedCheck)
                        self.TimerBackup.start(10000, True)
                        BackupImage(self.backupname)
                        return header_string+dbackup_backuping
            else:
                print("[dBackup] unknown command")
                return header_string+_("nothing entered")

    def backupFinishedCheck(self):
        global dbackup_progress
        self.backuptime=self.backuptime+10
        if not os.path.exists(dbackup_backup):
                # not finished - continue checking ...
            rsize=0

            if os.path.exists("%s/%s.%s" % (config.plugins.dbackup.backuplocation.value, self.backupname, config.plugins.dbackup.backuptool.value)):
                rsize=os.path.getsize("%s/%s.%s" % (config.plugins.dbackup.backuplocation.value, self.backupname, config.plugins.dbackup.backuptool.value))
            total_size=rsize
            st = os.statvfs("/")
            rused = (st.f_blocks - st.f_bfree) * st.f_frsize
            if boxtype == "dm520":
                used=rused*3
            else:
                used=rused
            if used < 0:
                used=0
            print("[dBackup] total size %d used %d\n" % (total_size, used))
            if total_size > 0:
# for xz
#                               dbackup_progress=300*total_size/used
# for gz
                dbackup_progress=250*total_size/used
            else:
                dbackup_progress=self.backuptime/10
            print("[dBackup] checked if backup is finished ...")
            self.TimerBackup.start(10000, True)
        else:
            print("[dBackup] found finished backup ...")
            dbackup_progress=0
            self.TimerBackup = eTimer()
            self.TimerBackup.stop()
            if os.path.exists(dbackup_busy):
                os.remove(dbackup_busy)
            f=open(dbackup_backup)
            line=f.readline()
            f.close()
            os.remove(dbackup_backup)
            sp=[]
            sp=line.split(" ")
            print(sp)
            length=len(sp)
            size=""
            image=""
            path=""
            if length > 0:
                size=sp[0].rstrip().lstrip()
                sp2=[]
                sp2=sp[length-1].split("/")
                print(sp2)
                length=len(sp2)
                if length > 0:
                    image=sp2[length-1]
                    path=line.replace(size, "").replace(image, "")
                    image=image.replace(".tar.gz\n", "").replace(".tar.xz\n", "").replace(".tar.bz2\n", "").replace(".tar\n", "")
                    image=image.rstrip().lstrip()
            print("[dBackup] found backup %s" % line)
            print("[dBackup] finished webif backup")

class FlashingImage(Screen):
    def __init__(self, flashimage):
        global dreambox_data
        print("[dBackup] does flashing %s" % flashimage)
#               lcdinst=eDBoxLCD.getInstance()
#               eLCD.unlock(lcdinst)
        open(dbackup_busy, 'a').close()
        if config.plugins.dbackup.flashtool.value == "rescue":
            command  = "#!/bin/sh -x\n"
            command += "echo rescue > /proc/stb/fp/boot_mode\n"
            command += "shutdown -r now\n"
            command += "exit 0\n"
            b=open(dbackup_script, "w")
            b.write(command)
            b.close()
            os.system("chmod 755 %s" % dbackup_script)
            print("[dBackup] %s created and is now booting to recue mode\n" % (dbackup_script))
            os.system("/sbin/start-stop-daemon -S -b -n dbackup.sh -x %s" % dbackup_script)
        elif config.plugins.dbackup.flashtool.value == "recovery":
            command  = "#!/bin/sh -x\n"
            command += "mkdir /data\n"
            if boxtype != "dm520":
                command += "umount /dev/mmcblk0p2; mount -t ext4 /dev/mmcblk0p2 /data\n"
            else:
                command += "umount %s; mount %s /data\n" % (dreambox_data, dreambox_data)
            command += "mount -o remount,async /data\n"
            command += "mkdir /data/.recovery\n"
            command += "cp %s /data/.recovery/backup.tar.gz\n" % flashimage
            command += "umount /data\n"
            command += "init 4\n"
            command += "sleep 5\n"
            command += "shutdown -h now\n"
            command += "exit 0\n"
            b=open(dbackup_script, "w")
            b.write(command)
            b.close()
            os.system("chmod 755 %s" % dbackup_script)
            print("[dBackup] %s created and is now flashing %s\n" % (dbackup_script, flashimage))
            os.system("/sbin/start-stop-daemon -S -b -n dbackup.sh -x %s" % dbackup_script)
        elif config.plugins.dbackup.flashtool.value == "usb":
            print("[dBackup] recovery usb stick is not yet supported")
        else:
            tmp_extract="%s/tmp" % config.plugins.dbackup.backuplocation.value
            if os.path.exists(tmp_extract):
                shutil.rmtree(tmp_extract, True)
            if not os.path.exists(tmp_extract):
                os.mkdir(tmp_extract)
            command  = "#!/bin/sh -x\n"
            if flashimage == "rescue":
                # default values from DMM recovery Image
#                               if boxtype == "dm7080":
#                                       url="http://www.dreamboxupdate.com/opendreambox/2.2/stable/images/%s" % boxtype
#                                       img="vmlinuz-rescue--3.4-r0.51-%s-20160405.bin" % boxtype
#                               if boxtype == "dm820":
#                                       url="http://www.dreamboxupdate.com/opendreambox/2.2/stable/images/%s" % boxtype
#                                       img="vmlinuz-rescue--3.4-r0.3-%s-20160405.bin" % boxtype
#                               if boxtype == "dm520":
#                                       url="http://www.dreamboxupdate.com/opendreambox/2.2/unstable/images/%s" % boxtype
#                                       img="vmlinuz-rescue--3.4-r0.3-%s-20160820.bin" % boxtype
#                               if boxtype == "dm900" or boxtype == "dm920":
#                                       url="http://www.dreamboxupdate.com/opendreambox/2.5/unstable/images/%s" % boxtype
#                                       img="zImage-rescue-3.14-r0-%s-20161208.bin" % boxtype
#                               rescue_image="%s/%s" % (url,img)
#                               flashimage="%s/%s" % (config.plugins.dbackup.backuplocation.value,img)
#                               print "[dBackup] downloads %s to %s" % (rescue_image,flashimage)
#                               command += "wget %s -O %s\n" % (rescue_image,flashimage)
                flashimage="none"
                command += "/usr/sbin/update-rescue\n"
            if flashimage == "recovery":
                # default values from DMM recovery Image
                url="http://dreamboxupdate.com/download/recovery/%s/release" % boxtype
                img="dreambox-image-%s.tar.xz" % boxtype
                if not os.path.exists("/data"):
                    os.mkdir("/data")
                if boxtype != "dm520":
                    os.system("umount /dev/mmcblk0p2; mount -t ext4 /dev/mmcblk0p2 /data")
                else:
                    os.system("umount %s; mount %s /data" % (dreambox_data, dreambox_data))
                if os.path.exists("/data/.recovery/recovery"):
                    r=open("/data/.recovery/recovery")
                    line = r.readline()
                    while (line):
                        line = r.readline()
                        if line.startswith("BASE_URI="):
                            url=line.replace("BASE_URI=", "").rstrip("\n")
                        if line.startswith("FILENAME="):
                            img=line.replace("FILENAME=", "").rstrip("\n")
                    r.close()
                recovery_image="%s/%s" % (url, img)
                flashimage="%s/%s" % (config.plugins.dbackup.backuplocation.value, img)
                print("[dBackup] downloads %s to %s" % (recovery_image, flashimage))
                os.system("umount /data")
                command += "wget %s -O %s\n" % (recovery_image, flashimage)
            if flashimage.endswith(".tar.gz"):
                if os.path.exists("%s/bin/pigz" % dbackup_plugindir):
                    tarimage="%s/tmp/rootfs.tar" % config.plugins.dbackup.backuplocation.value
                    command += "%s/bin/pigz -d -f -c \"%s\" > \"%s\"\n" % (dbackup_plugindir, flashimage, tarimage)
            elif flashimage.endswith(".tar.xz"):
                if os.path.exists("%s/bin/xz" % dbackup_plugindir):
                    tarimage="%s/tmp/rootfs.tar" % config.plugins.dbackup.backuplocation.value
                    command += "%s/bin/xz -d -c \"%s\" > \"%s\"\n" % (dbackup_plugindir, flashimage, tarimage)
            elif flashimage.endswith(".tar.bz2"):
                tarimage="%s/tmp/rootfs.tar" % config.plugins.dbackup.backuplocation.value
                command += "bunzip2 -c -f \"%s\" > \"%s\"\n"% (flashimage, tarimage)
            elif flashimage.endswith(".zip"):
                command += "unzip \"%s\" -d %s/tmp\n" % (flashimage, config.plugins.dbackup.backuplocation.value)
                tarimage="%s/tmp/%s/rootfs.tar\n" % (config.plugins.dbackup.backuplocation.value, boxtype)
                command += "bunzip2 -c -f \"%s.bz2\" > \"%s\"\n" % (tarimage, tarimage)
            elif flashimage.endswith(".bin"):
                if config.plugins.dbackup.verbose.value:
                    command += "flash-rescue -v %s\n" % (flashimage)
                else:
                    command += "flash-rescue %s\n" % (flashimage)
            elif flashimage.endswith("none"):
                pass
            else:
                tarimage="%s/tmp/rootfs.tar" % config.plugins.dbackup.backuplocation.value
                command += "cp %s %s\n" % (flashimage, tarimage)

            if flashimage.endswith(".bin") is False and flashimage.endswith("none") is False:
                if config.plugins.dbackup.kernelflash.value:
                    command += "tar -x -f %s ./boot -C %s\n" % (tarimage, tmp_extract)
                    if boxtype == "dm520":
                        command += "flash-kernel -v %s/boot/vmlinux.gz*%s\n" % (tmp_extract, boxtype)
                    elif boxtype == "dm900" or boxtype == "dm920":
                        command += "flash-kernel %s/boot/zImage*%s\n" % (tmp_extract, boxtype)
                    else:
                        command += "flash-kernel -a /usr/share/fastboot/lcd_anim.bin -m 0x10000000 -o A %s/boot/vmlinux.bin*%s\n" % (tmp_extract, boxtype)

                command += "cp %s/bin/swaproot /tmp/swaproot\n" % dbackup_plugindir
                command += "chmod 755 /tmp/swaproot\n"
                command += "/tmp/swaproot \"%s\"\n" % tarimage
            else:
                command += "shutdown -r now\n"
            command += "exit 0\n"
            b=open(dbackup_script, "w")
            b.write(command)
            b.close()
            os.system("chmod 755 %s" % dbackup_script)
            print("[dBackup] %s created and is now flashing %s\n" % (dbackup_script, flashimage))
            os.system("/sbin/start-stop-daemon -S -b -n dbackup.sh -x %s" % dbackup_script)

class BackupImage(Screen):
    def __init__(self, backupname, imagetype, creator):
        print("[dBackup] does backup")
        open(dbackup_busy, 'a').close()
        self.backupname=backupname
#               self.imagetype=imagetype
#               self.creator=creator
        exclude=" --exclude=smg.sock"
        if config.plugins.dbackup.epgdb.value:
            exclude +=" --exclude=epg.db"
        if config.plugins.dbackup.mediadb.value:
            exclude +=" --exclude=media.db"
        if config.plugins.dbackup.timers.value:
            exclude +=" --exclude=timers.xml"
        if config.plugins.dbackup.settings.value:
            exclude +=" --exclude=settings"
        f=open("/proc/stb/info/model")
        self.boxtype=f.read()
        f.close()
        self.boxtype=self.boxtype.replace("\n", "").replace("\l", "")
        if self.boxtype == "dm525":
            self.boxtype="dm520"
        for name in os.listdir("/lib/modules"):
            self.kernel = name
        self.kernel = self.kernel.replace("\n", "").replace("\l", "").replace("\0", "")
        print("[dBackup] boxtype %s kernel %s" % (self.boxtype, self.kernel))
        # don't backup left overs from flashing ...
        tmp_extract="%s/tmp" % config.plugins.dbackup.backuplocation.value
        if os.path.exists(tmp_extract):
            shutil.rmtree(tmp_extract, True)

        # here comes the fun ...

        command  = "#!/bin/sh -x\n"
        command += "exec > %s 2>&1\n" % dbackup_log
        command +="cat %s\n" % dbackup_backupscript
        command +="df -h\n"
        if os.path.exists("/etc/init.d/openvpn"):
            command +="/etc/init.d/openvpn stop\n"
        if config.plugins.dbackup.aptclean.value:
            command += "apt-get clean\n"

        # make root filesystem ...

        command +="umount /tmp/root\n"
        command +="rmdir /tmp/root\n"
        command +="mkdir /tmp/root\n"
        command +="mount -o bind / /tmp/root\n"
        if config.plugins.dbackup.picons.value and os.path.exists("/usr/share/enigma2/picon"):
            command +="mount -t tmpfs tmpfs /tmp/root/usr/share/enigma2/picon\n"
        target ="%s/%s.tar" % (config.plugins.dbackup.backuplocation.value, backupname)
        # tar.gz is now default
#               if boxtype == "dm520":
#                       command +="dd if=/dev/zero of=%s/swapfile bs=1024 count=512000\n" % config.plugins.dbackup.backuplocation.value
#                       command +="mkswap %s/swapfile\n" % config.plugins.dbackup.backuplocation.value
#                       command +="swapon %s/swapfile\n" % config.plugins.dbackup.backuplocation.value
        if config.plugins.dbackup.backupsettings.value:
            command +="DATE=`date +\"%Y-%m-%d\"`\n"
            command +="BACKUP=\"%s/\"$DATE\"-enigma2settingsbackup.tar.gz\"\n" % config.plugins.dbackup.backuplocation.value
            command +="rm $BACKUP > /dev/null 2>&1\n"
            try:
                backupdirs = ' '.join(config.plugins.configurationbackup.backupdirs.value)
            except:
                backupdirs = " /etc/enigma2/ /etc/hostname"
            print("[dBACKUP] setings backup %s" % backupdirs)
            if os.path.exists("/etc/wpa_supplicant.conf"):
                command +="tar -czvf $BACKUP  %s /etc/wpa_supplicant.conf /etc/resolv.conf\n" % backupdirs
            else:
                command +="tar -czvf $BACKUP  %s /etc/resolv.conf\n" % backupdirs
        if config.plugins.dbackup.backuptool.value == "tar.gz":
            if os.path.exists("%s/bin/pigz" % dbackup_plugindir):
                if config.plugins.dbackup.verbose.value:
                    command +="%s/tar -cvf %s %s -C /tmp/root .\n" % (dbackup_bin, target, exclude)
                else:
                    command +="%s/tar -cf %s %s -C /tmp/root .\n" % (dbackup_bin, target, exclude)
                command +="%s/bin/pigz %s\n" % (dbackup_plugindir, target)
            else:
                if config.plugins.dbackup.verbose.value:
                    command +="%s/tar -cvzf %s.gz %s -C /tmp/root .\n" % (dbackup_bin, target, exclude)
                else:
                    command +="%s/tar -czf %s.gz %s -C /tmp/root .\n" % (dbackup_bin, target, exclude)
        elif config.plugins.dbackup.backuptool.value == "tar.xz":
            if os.path.exists("%s/bin/xz" % dbackup_plugindir):
                if config.plugins.dbackup.verbose.value:
                    command +="%s/tar -cvf %s %s -C /tmp/root .\n" % (dbackup_bin, target, exclude)
                else:
                    command +="%s/tar -cf %s %s -C /tmp/root .\n" % (dbackup_bin, target, exclude)
                command +="ln -sfn %s/bin/xz /usr/bin/xz\n" % (dbackup_plugindir)
                command +="/usr/bin/xz -%s -T 0 < %s > %s.xz\n" % (config.plugins.dbackup.xzcompression.value, target, target)
                command +="rm %s\n" % (target)
            else:
                if config.plugins.dbackup.verbose.value:
                    command +="%s/tar -cvJf %s.xz %s -C /tmp/root .\n" % (dbackup_bin, target, exclude)
                else:
                    command +="%s/tar -cJf %s.xz %s -C /tmp/root .\n" % (dbackup_bin, target, exclude)
        elif config.plugins.dbackup.backuptool.value == "tar.bz2":
            if config.plugins.dbackup.verbose.value:
                command +="%s/tar -cvjf %s.bz2 %s -C /tmp/root .\n" % (dbackup_bin, target, exclude)
            else:
                command +="%s/tar -cjf %s.bz2 %s -C /tmp/root .\n" % (dbackup_bin, target, exclude)
        else:
            if config.plugins.dbackup.verbose.value:
                command +="%s/tar -cvf %s %s -C /tmp/root .\n" % (dbackup_bin, target, exclude)
            else:
                command +="%s/tar -cf %s %s -C /tmp/root .\n" % (dbackup_bin, target, exclude)
        if config.plugins.dbackup.picons.value:
            command +="umount /tmp/root/usr/share/enigma2/picon\n"
        command +="umount /tmp/root\n"
        command +="rmdir /tmp/root\n"

        if os.path.exists("/etc/init.d/openvpn"):
            command +="/etc/init.d/openvpn start\n"

        command +="chmod 777 %s.*\n" % (target)
        command +="ls -alh %s*\n" % (target)
        command +="du -h %s* > %s\n" % (target, dbackup_backup)
        command +="df -h\n"
#               if boxtype == "dm520":
#                       command +="swapoff %s/swapfile\n" % config.plugins.dbackup.backuplocation.value
#                       command +="rm %s/swapfile\n" % config.plugins.dbackup.backuplocation.value
        command +="rm %s\n" % dbackup_busy
        command +="exit 0\n"
        print(command)
        b=open(dbackup_backupscript, "w")
        b.write(command)
        b.close()
        os.chmod(dbackup_backupscript, 0o777)
        self.container = eConsoleAppContainer()
        start_cmd="/sbin/start-stop-daemon -K -n dbackup.sh -s 9; /sbin/start-stop-daemon -S -b -n dbackup.sh -x %s" % (dbackup_backupscript)
        if config.plugins.dbackup.exectool.value == "daemon":
            print("[dBackup] daemon %s" % dbackup_backupscript)
            self.container.execute(dbackup_backupscript)
        elif config.plugins.dbackup.exectool.value == "system":
            print("[dBackup] system %s" % start_cmd)
            os.system(start_cmd)
        if config.plugins.dbackup.exectool.value == "container":
            print("[dBackup] container %s" % start_cmd)
            self.container.execute(start_cmd)

###############################################################################
# dBackup Check by gutemine
###############################################################################

class dBackupChecking(Screen):
    if sz_w == 1920:
        skin = """
        <screen position="center,170" size="1200,820" title="choose NAND Flash Check" >
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
        <screen position="center,120" size="800,520" title="choose NAND Flash Check" >
        <widget name="logo" position="10,5" size="100,40" />
        <widget backgroundColor="#9f1313" font="Regular;19" halign="center" name="buttonred" position="120,5" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2" size="160,40" valign="center" />
        <widget backgroundColor="#1f771f" font="Regular;19" halign="center" name="buttongreen" position="290,5" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2" size="160,40" valign="center" />
        <widget backgroundColor="#a08500" font="Regular;19" halign="center" name="buttonyellow" position="460,5" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2" size="160,40" valign="center" />
        <widget backgroundColor="#18188b" font="Regular;19" halign="center" name="buttonblue" position="630,5" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2" size="160,40" valign="center" />
        <eLabel backgroundColor="grey" position="10,60" size="780,1" />
        <widget name="menu" position="10,60" size="780,450" enableWrapAround="1" scrollbarMode="showOnDemand" />
        </screen>"""

    def __init__(self, session, args = 0):
        global dreambox_data
        self.skin = dBackupChecking.skin
        self.session = session
        Screen.__init__(self, session)
        self.menu = args
        self.onShown.append(self.setWindowTitle)
        flashchecklist = []
        self["buttonred"] = Label(_("Exit"))
        self["buttonyellow"] = Label(info_header)
        self["buttongreen"] = Label(_("OK"))
        self["buttonblue"] = Label(_("About"))
        self["logo"] = Pixmap()
        if not os.path.exists("/data"):
            os.mkdir("/data")
        if boxtype != "dm520":
            flashchecklist.append((_("check root"), "/sbin/fsck.ext4 -f -v -y /dev/mmcblk0p1"))
            flashchecklist.append((_("check & repair recovery"), "/sbin/fsck.ext4 -f -v -y /dev/mmcblk0p2"))
            if os.path.exists("/sbin/badblocks"):
                flashchecklist.append((_("badblocks recovery > 1min"), "/sbin/fsck.ext4 -f -c -v -y /dev/mmcblk0p2"))
            else:
                flashchecklist.append((_("no badblocks binary - get e2fsprogs"), "none"))
        else:
            if dreambox_data != "none":
                flashchecklist.append((_("check & repair recovery"), "umount %s; /sbin/fsck.ext4 -f -v -y %s" % (dreambox_data, dreambox_data)))
                if os.path.exists("/sbin/badblocks"):
                    flashchecklist.append((_("badblocks recovery > 1min"), "umount %s; /sbin/fsck.ext4 -f -c -v -y %s" % (dreambox_data, dreambox_data)))
                else:
                    flashchecklist.append((_("no badblocks binary - get e2fsprogs"), "none"))
            else:
                flashchecklist.append((_("create recovery USB stick"), "recovery"))
#               flashchecklist.append((_("clean apt cache"), "apt-get -v; apt-get clean"))
        if boxtype != "dm520":
            flashchecklist.append((_("check defragmentation root"), "ln -sfn /dev/mmcblk0p1 /dev/root; %s/bin/e4defrag -c /dev/root" % dbackup_plugindir))
            flashchecklist.append((_("defragment root"), "ln -sfn /dev/mmcblk0p1 /dev/root; %s/bin/e4defrag /dev/root" % dbackup_plugindir))
            flashchecklist.append((_("check defragmentation recovery"), "mount /dev/mmcblk0p2 /data; %s/bin/e4defrag -c /dev/mmcblk0p2; umount /data" % dbackup_plugindir))
            flashchecklist.append((_("defragment recovery"), "mount /dev/mmcblk0p2 /data; %s/bin/e4defrag /dev/mmcblk0p2; umount /data" % dbackup_plugindir))
        else:
            if dreambox_data != "none":
                flashchecklist.append((_("check defragmentation recovery"), "mount %s /data; %s/bin/e4defrag -c %s; umount /data" % (dreambox_data, dbackup_plugindir, dreambox_data)))
                flashchecklist.append((_("defragment recovery"), "mount %s /data; %s/bin/e4defrag %s; umount /data" % (dreambox_data, dbackup_plugindir, dreambox_data)))
        m=open("/proc/mounts")
        mounts=m.read()
        m.close()
        if mounts.find("/media/hdd ext4") != -1:
            flashchecklist.append((_("check defragmentation Harddisk"), "%s/bin/e4defrag -c /media/hdd" % dbackup_plugindir))
            flashchecklist.append((_("defragment Harddisk"), "%s/bin/e4defrag -v /media/hdd" % dbackup_plugindir))

        self["menu"] = MenuList(flashchecklist)
        self["setupActions"] = ActionMap([ "ColorActions", "SetupActions" ],
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
        print(self.checking, self.command)
        if self.command is not None and self.command == "recovery":
            print("[dBackup] create recovery")
            device_string=_("Select device for recovery USB stick")
            self.session.openWithCallback(self.askForDevice, ChoiceBox, device_string, self.getDeviceList())
            return
        if self.command is not None and self.command != "none":
            self.session.open(Console, self.checking, [ (self.command) ])

    def getPiconPath(self, name):
        if os.path.exists("/usr/share/enigma2/%s/skin_default/%s.svg" % (dbackup_skin, name)):
#               print "[DBACKUP] found %s.svg in skin ..." % name
            return "/usr/share/enigma2/%s/skin_default/%s.svg" % (dbackup_skin, name)
        if os.path.exists("/usr/share/enigma2/%s/skin_default/%s.png" % (dbackup_skin, name)):
#               print "[DBACKUP] found %s.png in skin ..." % name
            return "/usr/share/enigma2/%s/skin_default/%s.png" % (dbackup_skin, name)
        if os.path.exists("/usr/share/enigma2/%s/skin_default/icons/%s.png" % (dbackup_skin, name)):
#               print "[DBACKUP] found %s.png in skin ..." % name
            return "/usr/share/enigma2/%s/skin_default/icons/%s.png" % (dbackup_skin, name)
        if os.path.exists("/usr/share/enigma2/%s/skin_default/icons/%s.svg" % (dbackup_skin, name)):
#               print "[DBACKUP] found %s.svg in skin ..." % name
            return "/usr/share/enigma2/%s/skin_default/icons/%s.svg" % (dbackup_skin, name)
        if os.path.exists("/usr/share/enigma2/skin_default/%s.svg" % (name)):
#               print "[DBACKUP] found %s.svg in default skin ..." % name
            return "/usr/share/enigma2/skin_default/%s.svg" % (name)
#       if os.path.exists("/usr/share/enigma2/skin_default/%s.png" % (name)):
#               print "[DBACKUP] found %s.png in default skin ..." % name
#               return "/usr/share/enigma2/skin_default/%s.png" % (name)
        if os.path.exists("/usr/share/enigma2/skin_default/icons/%s.png" % (name)):
#               print "[DBACKUP] found %s.png in default skin ..." % name
            return "/usr/share/enigma2/skin_default/icons/%s.png" % (name)
        if os.path.exists("/usr/share/enigma2/skin_default/buttons/key_%s.png" % (name)):
#               print "[DBACKUP] found %s.png in default skin ..." % name
            return "/usr/share/enigma2/skin_default/buttons/key_%s.png" % (name)
#       print "[DBACKUP] found %s.png in default skin ..." % name
        return "/usr/share/enigma2/skin_default/%s.png" % (name)

    def setWindowTitle(self):
        self["logo"].instance.setPixmapFromFile("%s/dbackup.png" % dbackup_plugindir)
        self.setTitle(backup_string+" & "+flashing_string+" V%s " % dbackup_version + checking_string)

    def legend(self):
        title=_("If you install e2fsprogs the badblocks binary will allow to check and mark also bad blocks")
        self.session.open(MessageBox, title,  MessageBox.TYPE_INFO)

    def about(self):
        self.session.open(dBackupAbout)

    def getDeviceList(self):
        found=False
        f=open("/proc/partitions", "r")
        devlist= []
        line = f.readline()
        line = f.readline()
        sp=[]
        while (line):
            line = f.readline()
            if line.find("sd") != -1:
                sp=line.split()
                print(sp)
                devsize=int(sp[2])
                mbsize=devsize/1024
                devname="/dev/%s" % sp[3]
                print(devname, devsize)
                if len(devname) == 8 and mbsize < 36000 and mbsize > 480:
                    # only sticks from 512 MB up to 32GB are used as recovery sticks
                    found=True
                    devlist.append(("%s %d %s" % (devname, mbsize, "MB"), devname, mbsize))
        f.close()
        if not found:
            devlist.append(("no device found, shutdown, add device and reboot", "nodev", 0))
        return devlist

    def askForDevice(self, device):
        if device is None:
            self.session.open(MessageBox, _("Sorry, no device choosen"), MessageBox.TYPE_ERROR)
        elif device[1] == "nodev":
            self.session.open(MessageBox, _("Sorry, no device found"), MessageBox.TYPE_ERROR)
        else:
            self.device=device[1]
            self.session.openWithCallback(self.doRecoveryStick, MessageBox, _("Are you sure that you want to erase now %s ?") %(self.device), MessageBox.TYPE_YESNO)

    def doRecoveryStick(self, option):
        if option is False:
            self.session.open(MessageBox, _("Sorry, Erasing of %s was canceled!") % self.device, MessageBox.TYPE_ERROR)
        else:
            if not os.path.exists("%s1" % self.device):
                self.session.open(MessageBox, _("Sorry, %s has no primary partition") % self.device, MessageBox.TYPE_ERROR)
            else:
                print("[dBackup] erases %s1" % self.device)
                cmd="umount %s1; mkfs.ext4 -L dreambox-data %s1; mkdir /autofs/%s1/backup" % (self.device, self.device, self.device)
                self.session.open(Console, self.checking, [cmd])

class dBackupConfiguration(Screen, ConfigListScreen):
    if sz_w == 1920:
        skin = """
        <screen position="center,170" size="1200,820" title="dBackup Configuration" >
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
        <screen position="center,120" size="800,520" title="dBackup Configuration" >
        <widget name="logo" position="10,5" size="100,40" />
        <widget backgroundColor="#9f1313" font="Regular;19" halign="center" name="buttonred" position="120,5" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2" size="160,40" valign="center" />
        <widget backgroundColor="#1f771f" font="Regular;19" halign="center" name="buttongreen" position="290,5" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2" size="160,40" valign="center" />
        <widget backgroundColor="#a08500" font="Regular;19" halign="center" name="buttonyellow" position="460,5" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2" size="160,40" valign="center" />
        <widget backgroundColor="#18188b" font="Regular;19" halign="center" name="buttonblue" position="630,5" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2" size="160,40" valign="center" />
        <eLabel backgroundColor="grey" position="10,50" size="780,1" />
        <widget name="config" position="10,60" size="780,450" enableWrapAround="1" scrollbarMode="showOnDemand" />
        </screen>"""

    def __init__(self, session, args = 0):
        Screen.__init__(self, session)

        self.onShown.append(self.setWindowTitle)
        # explizit check on every entry
        self.onChangedEntry = []

        self.list = []
        ConfigListScreen.__init__(self, self.list, session = self.session, on_change = self.changedEntry)
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
        self.list.append(getConfigListEntry(_("Backuptool"), config.plugins.dbackup.backuptool))
        if config.plugins.dbackup.backuptool.value == "tar.xz":
            self.list.append(getConfigListEntry(_("tar.xz Compression"), config.plugins.dbackup.xzcompression))
#       self.list.append(getConfigListEntry(_("Create signature file"), config.plugins.dbackup.sig))
#       self.list.append(getConfigListEntry(_("Extract loader from Flash"), config.plugins.dbackup.loaderextract))
#       self.list.append(getConfigListEntry(_("Extract kernel from Flash"), config.plugins.dbackup.kernelextract))
        self.list.append(getConfigListEntry(_("Flash kernel from image"), config.plugins.dbackup.kernelflash))
#        self.list.append(getConfigListEntry(_("Flashing reboot delay [0-60 sec]"), config.plugins.dbackup.delay))
        self.list.append(getConfigListEntry(_("Choose backup location"), config.plugins.dbackup.backupaskdir))
#       self.list.append(getConfigListEntry(_("Imagetype in backupname"), config.plugins.dbackup.backupimagetype))
#       self.list.append(getConfigListEntry(_("Boxtype in backupname"), config.plugins.dbackup.backupboxtype))
        self.list.append(getConfigListEntry(_("deb in backupname"), config.plugins.dbackup.backupdeb))
        self.list.append(getConfigListEntry(_("Date in backupname"), config.plugins.dbackup.backupdate))
        self.list.append(getConfigListEntry(_("Time in backupname"), config.plugins.dbackup.backuptime))
        self.list.append(getConfigListEntry(_("Blanks in backupname"), config.plugins.dbackup.backupblanks))
#       if not os.path.exists("/var/lib/opkg/status"):
#               self.list.append(getConfigListEntry(_("Clean apt cache before backup"), config.plugins.dbackup.aptclean))
#               self.list.append(getConfigListEntry(_("Exclude epg.db"), config.plugins.dbackup.epgdb))
#               self.list.append(getConfigListEntry(_("Exclude epg.db").replace("epg.db","media.db"), config.plugins.dbackup.mediadb))
        self.list.append(getConfigListEntry(_("Exclude timers"), config.plugins.dbackup.timers))
        self.list.append(getConfigListEntry(_("extra")+" "+_("Settings")+" "+_("Backup"), config.plugins.dbackup.backupsettings))
        self.list.append(getConfigListEntry(_("Exclude settings"), config.plugins.dbackup.settings))
        if os.path.exists("/usr/share/enigma2/picon"):
            self.list.append(getConfigListEntry(_("Exclude picons"), config.plugins.dbackup.picons))
        self.list.append(getConfigListEntry(_("Minimal Fading Transparency"), config.plugins.dbackup.transparency))
#        self.list.append(getConfigListEntry(_("Verbose"), config.plugins.dbackup.verbose))
        self.list.append(getConfigListEntry(_("Sort Imagelist alphabetic"), config.plugins.dbackup.sort))
        self.list.append(getConfigListEntry(_("Show plugin"), config.plugins.dbackup.showing))
        self.list.append(getConfigListEntry(_("Recovery Mode"), config.plugins.dbackup.recovering))
        if not os.path.exists("/var/lib/opkg/status"):
            self.list.append(getConfigListEntry(_("Webinterface"), config.plugins.dbackup.webinterface))

        self["config"].list = self.list
        self["config"].l.setList(self.list)

    def changedEntry(self):
        self.createSetup()

    def getPiconPath(self, name):
        if os.path.exists("/usr/share/enigma2/%s/skin_default/%s.svg" % (dbackup_skin, name)):
#               print "[DBACKUP] found %s.svg in skin ..." % name
            return "/usr/share/enigma2/%s/skin_default/%s.svg" % (dbackup_skin, name)
        if os.path.exists("/usr/share/enigma2/%s/skin_default/%s.png" % (dbackup_skin, name)):
#               print "[DBACKUP] found %s.png in skin ..." % name
            return "/usr/share/enigma2/%s/skin_default/%s.png" % (dbackup_skin, name)
        if os.path.exists("/usr/share/enigma2/%s/skin_default/icons/%s.png" % (dbackup_skin, name)):
#               print "[DBACKUP] found %s.png in skin ..." % name
            return "/usr/share/enigma2/%s/skin_default/icons/%s.png" % (dbackup_skin, name)
        if os.path.exists("/usr/share/enigma2/%s/skin_default/icons/%s.svg" % (dbackup_skin, name)):
#               print "[DBACKUP] found %s.svg in skin ..." % name
            return "/usr/share/enigma2/%s/skin_default/icons/%s.svg" % (dbackup_skin, name)
        if os.path.exists("/usr/share/enigma2/skin_default/%s.svg" % (name)):
#               print "[DBACKUP] found %s.svg in default skin ..." % name
            return "/usr/share/enigma2/skin_default/%s.svg" % (name)
#       if os.path.exists("/usr/share/enigma2/skin_default/%s.png" % (name)):
#               print "[DBACKUP] found %s.png in default skin ..." % name
#               return "/usr/share/enigma2/skin_default/%s.png" % (name)
        if os.path.exists("/usr/share/enigma2/skin_default/icons/%s.png" % (name)):
#               print "[DBACKUP] found %s.png in default skin ..." % name
            return "/usr/share/enigma2/skin_default/icons/%s.png" % (name)
        if os.path.exists("/usr/share/enigma2/skin_default/buttons/key_%s.png" % (name)):
#               print "[DBACKUP] found %s.png in default skin ..." % name
            return "/usr/share/enigma2/skin_default/buttons/key_%s.png" % (name)
#       print "[DBACKUP] found %s.png in default skin ..." % name
        return "/usr/share/enigma2/skin_default/%s.png" % (name)

    def setWindowTitle(self):
        self["logo"].instance.setPixmapFromFile("%s/dbackup.png" % dbackup_plugindir)
        self.setTitle(backup_string+" & "+flashing_string+" V%s " % dbackup_version + setup_string)

    def save(self):
        if config.plugins.dbackup.transparency.value > config.osd.alpha.value:
            # current transparency is maximum for faded transparency = no fading
            config.plugins.dbackup.transparency.value = config.osd.alpha.value
            config.plugins.dbackup.transparency.save()
        if config.plugins.dbackup.flashtool.value == "rescue":
            config.plugins.dbackup.backuplocation.value = "/data/.recovery"
            config.plugins.dbackup.backuptool.value = "tar.gz"
        else:
            # back to normal ...
            if config.plugins.dbackup.backuplocation.value == "/data/.recovery":
                config.plugins.dbackup.backuplocation.value = "/media/hdd/backup"
                config.plugins.dbackup.backuptool.value = "tar.gz"
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
        self.session.open(dBackupChecking)

    def disclaimer(self):
        self.session.openWithCallback(self.about, MessageBox, disclaimer_string, MessageBox.TYPE_WARNING)

    def about(self, answer):
        self.session.open(dBackupAbout)

class dBackupAbout(Screen):
    if sz_w == 1920:
        skin = """
        <screen position="center,center" size="800,500" title="About dBackup" >
        <widget name="aboutdbackup" foregroundColor="yellow" position="10,5" size="820,80" halign="center" font="Regular;32"/>
        <ePixmap position="340,150" size="120,120" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/dBackup/g3icon_dbackup.png"/>
        <widget name="freefilesystem" position="20,90" size="280,260" valign="center" halign="center" font="Regular;30"/>
        <widget name="freememory" position="500,90" size="280,260" valign="center" halign="center" font="Regular;30"/>
        <eLabel backgroundColor="grey" position="20,410" size="760,1" />
        <widget backgroundColor="#9f1313" font="Regular;30" halign="center" name="buttonred" position="20,420" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2" size="280,60" valign="center" />
        <widget backgroundColor="#1f771f" font="Regular;30" halign="center" name="buttongreen" position="500,420" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2" size="280,60" valign="center" />
        </screen>"""
    else:
        skin = """
        <screen position="center,center" size="720,350" title="About dBackup" >
        <widget name="aboutdbackup" position="10,10" size="700,30" halign="center" foregroundColor="yellow" font="Regular;24"/>
        <ePixmap position="320,100" size="100,100" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/dBackup/g3icon_dbackup.png"/>
        <widget name="freefilesystem" position="50,50" size="220,220" valign="center" halign="center" font="Regular;24"/>
        <widget name="freememory" position="450,50" size="220,220" valign="center" halign="center" font="Regular;24"/>
        <eLabel backgroundColor="grey" position="10,290" size="700,1" />
        <widget backgroundColor="#9f1313" font="Regular;19" halign="center" name="buttonred" position="10,300" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2" size="200,40" valign="center" />
        <widget backgroundColor="#1f771f" font="Regular;19" halign="center" name="buttongreen" position="510,300" foregroundColor="white" shadowColor="black" shadowOffset="-2,-2" size="200,40" valign="center" />
        </screen>"""

    def __init__(self, session, args = 0):
        Screen.__init__(self, session)
        self.onShown.append(self.setWindowTitle)
        st = os.statvfs("/")
        free = st.f_bavail * st.f_frsize/1024/1024
        total = st.f_blocks * st.f_frsize/1024/1024
        used = (st.f_blocks - st.f_bfree) * st.f_frsize/1024/1024
        freefilesystem=_("Root Filesystem\n\ntotal: %s MB\nused:  %s MB\nfree:  %s MB") %(total, used, free)

        memfree=0
        memtotal=0
        memused=0
        fm=open("/proc/meminfo")
        line = fm.readline()
        sp=line.split()
        memtotal=int(sp[1])/1024
        line = fm.readline()
        sp=line.split()
        memfree=int(sp[1])/1024
        fm.close()
        memused=memtotal-memfree
        freememory=_("Memory\n\ntotal: %i MB\nused: %i MB\nfree: %i MB") %(memtotal, memused, memfree)

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

    def getPiconPath(self, name):
        if os.path.exists("/usr/share/enigma2/%s/skin_default/%s.svg" % (dbackup_skin, name)):
#               print "[DBACKUP] found %s.svg in skin ..." % name
            return "/usr/share/enigma2/%s/skin_default/%s.svg" % (dbackup_skin, name)
        if os.path.exists("/usr/share/enigma2/%s/skin_default/%s.png" % (dbackup_skin, name)):
#               print "[DBACKUP] found %s.png in skin ..." % name
            return "/usr/share/enigma2/%s/skin_default/%s.png" % (dbackup_skin, name)
        if os.path.exists("/usr/share/enigma2/%s/skin_default/icons/%s.png" % (dbackup_skin, name)):
#               print "[DBACKUP] found %s.png in skin ..." % name
            return "/usr/share/enigma2/%s/skin_default/icons/%s.png" % (dbackup_skin, name)
        if os.path.exists("/usr/share/enigma2/%s/skin_default/icons/%s.svg" % (dbackup_skin, name)):
#               print "[DBACKUP] found %s.svg in skin ..." % name
            return "/usr/share/enigma2/%s/skin_default/icons/%s.svg" % (dbackup_skin, name)
        if os.path.exists("/usr/share/enigma2/skin_default/%s.svg" % (name)):
#               print "[DBACKUP] found %s.svg in default skin ..." % name
            return "/usr/share/enigma2/skin_default/%s.svg" % (name)
#       if os.path.exists("/usr/share/enigma2/skin_default/%s.png" % (name)):
#               print "[DBACKUP] found %s.png in default skin ..." % name
#               return "/usr/share/enigma2/skin_default/%s.png" % (name)
        if os.path.exists("/usr/share/enigma2/skin_default/icons/%s.png" % (name)):
#               print "[DBACKUP] found %s.png in default skin ..." % name
            return "/usr/share/enigma2/skin_default/icons/%s.png" % (name)
        if os.path.exists("/usr/share/enigma2/skin_default/buttons/key_%s.png" % (name)):
#               print "[DBACKUP] found %s.png in default skin ..." % name
            return "/usr/share/enigma2/skin_default/buttons/key_%s.png" % (name)
#       print "[DBACKUP] found %s.png in default skin ..." % name
        return "/usr/share/enigma2/skin_default/%s.png" % (name)

    def setWindowTitle(self):
        self.setTitle( _("About")+" dBackup")

    def cancel(self):
        self.close(False)

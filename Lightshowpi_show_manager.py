#!/usr/bin/env python3
#
# Author: Christian Pizzi
# Ver. 1.0
# Software needed:
# LightShowPi ver. (1.4) Python3
# Remi ver. 2020.8.6

import remi.gui as gui
from remi.gui import *
from remi import *
from remi import start, App
import os
from pathlib import Path
import time
import datetime
import copy
import shutil
from random import randint

class MyFileFolderNavigator(gui.FileFolderNavigator):
    """FileFolderNavigator widget."""
    def __init__(self, multiple_selection, selection_folder, allow_file_selection, allow_folder_selection, **kwargs):
        super(MyFileFolderNavigator, self).__init__(multiple_selection, selection_folder, allow_file_selection, allow_folder_selection,**kwargs)

    def on_folder_item_selected(self, folderitem):
        if not folderitem.isFolder:
            self.on_file_selected(folderitem.get_text())
        super(MyFileFolderNavigator, self).on_folder_item_selected(folderitem)

    @gui.decorate_event
    def on_file_selected(self, filename):
        return (filename, )
            

class MyFileSelectionDialog(gui.FileSelectionDialog):
    """file selection dialog, it opens a new webpage allows the OK/CANCEL functionality
    implementing the "confirm_value" and "cancel_dialog" events."""
    def __init__(self, title='File dialog', message='Select files and folders',
                 multiple_selection=True, selection_folder='.',
                 allow_file_selection=True, allow_folder_selection=True, **kwargs):
        
        super(MyFileSelectionDialog, self).__init__(title, message, **kwargs)
        self.style['width'] = '475px'
        self.fileFolderNavigator = MyFileFolderNavigator(multiple_selection, selection_folder,
                                                       allow_file_selection,
                                                       allow_folder_selection)
        self.add_field('fileFolderNavigator', self.fileFolderNavigator)
        self.confirm_dialog.do(self.confirm_value)

    @gui.decorate_set_on_listener("(self, emitter, fileList)")
    @gui.decorate_event
    def confirm_value(self, widget):
        """event called pressing on OK button.
           propagates the string content of the input field
        """
        self.hide()
        params = (self.fileFolderNavigator.get_selection_list(),)
        return params

class EditorFileSaveDialog(MyFileSelectionDialog, EventSource):
    def __init__(self, title='File dialog', message='Select files and folders',
                multiple_selection=True, selection_folder='.',
                allow_file_selection=True, allow_folder_selection=True, baseAppInstance = None):
        super(EditorFileSaveDialog, self).__init__( title, message, multiple_selection, selection_folder,
                allow_file_selection, allow_folder_selection)
        EventSource.__init__(self)

        self.baseAppInstance = baseAppInstance
        self.fileFolderNavigator.on_file_selected.do(self.on_file_selection)
        
    def show(self, *args):
        super(EditorFileSaveDialog, self).show(self.baseAppInstance)

    def add_fileinput_field(self, defaultname='untitled'):
        self.txtFilename = gui.TextInput()
##        self.txtFilename.onchange.do(self.on_enter_key_pressed)
        self.txtFilename.set_text(defaultname)

        self.add_field_with_label("filename","Filename",self.txtFilename)

    def get_fileinput_value(self):
        return self.get_field('filename').get_value()

##    def on_enter_key_pressed(self, widget, value):
##        self.confirm_value(None)

    @gui.decorate_event
    def confirm_value(self, widget):
        """event called pressing on OK button.
        propagates the string content of the input field
        """
        self.hide()
        params = (self.fileFolderNavigator.pathEditor.get_text(),)
        appo = self.get_fileinput_value()
        temp = params[0] + '/' + appo
        params = (temp, )
        return params
    
    def on_file_selection(self, emitter, filename):
        pathInput = self.get_field('filename')
##        print("on_file_selection")
        if pathInput:
            pathInput.set_text(filename)





class MyApp(App):
    version = 'Ver. 1.3'              #Version of this app used in first page
    LightShowPiFolder = ''      #LightShowPi folder location
    LightShowPiOverrides = ''   #LightShowPi Override.cfg file location - can be removed in future
    LightShowPiPy = ''          #LightShowPi /py folder program used for light show
    LightShowPiConfig = ''      #LightShowPi config folder location
    LightShowPiMusic = ''       #Music folder location
    LightShowPiShow = ''        #Show folder location .cfg or .py
#     LightShowPiList = ''        
    Default_cfg = ''            #point to default.cfg
    PlayON = False              #True if music is ON
    PlayNum = 0                 #Number of song currently played
    PlayNumSelected = ''        #Number of the selected song in the list
#     PlaySelected = ''           
    PlayNumMax = 0              #Total number of songs in play list
    PlayLoop = 0                #Loop active
    PlayRandom = 0              #Random active
    NoConfig = 0                #Used if config files are not find when loaded from a saved file
    VolumeDef = 75              #Default volume
    VolumeOn = 1                #Active if volume is ON
    Volume = VolumeDef          #Current volume variable
    AlsaDevice = "Headphone"    #NAME OF YOUR SOUNDCARD OUTPUT !!!!!!!!!!!!!!!!!!!IMPORTANT!!!!!!!!!!!!!!!!!!!!
    SchedFileName = ''          #Used to store the Scheduler file name
    SchedOn = False             #True if schedule is ON
    DaySched = 0                #Day of the week 1 thru 7 - Mon thru Sun
    TimeRange = []              #Time for Sched to turn On and Off the music, set it 00:00 - 00:00
    TimeRange.append('00:00')
    TimeRange.append('00:00')
    TimeIn = False              #Used to check if the time is in an active range for the scheduler
    logo_sched = gui.Image('/res:sched_off.png', width='30px')   #scheduler logo
    
    ConfigList = []             #List of all Config files
    SongListDict = {}           #dictionary of: integer + song files
    SongList = {}               #temporari variable to manage visualization of songs list
    ListList = {}               #dictionary of: song file + config file or NONE
    PlayList = {}               #copy of ListList used for the Player
    SchedList = {}              #Scheduler list complete
    SchedToday = {}             #Scheduler for today
    SchedNow = []               #Active scheduler
    
    file_types = [".wav", ".WAV",
              ".mp1", ".mp2", ".mp3", ".mp4", ".m4a", ".m4b",
              ".ogg", ".flac", ".oga", ".wma", ".wmv", ".aif"]

    file_types_all = [".wav", ".WAV",
              ".mp1", ".mp2", ".mp3", ".mp4", ".m4a", ".m4b",
              ".ogg", ".flac", ".oga", ".wma", ".wmv", ".aif",
              ".cfg"]

# keep here for future version when will be possible pass .py file as parameter
##    file_types_all = [".wav", ".WAV",
##              ".mp1", ".mp2", ".mp3", ".mp4", ".m4a", ".m4b",
##              ".ogg", ".flac", ".oga", ".wma", ".wmv", ".aif",
##              ".py", ".cfg"]
    
    #---Used for time simulation---
#     TimeStart = datetime.datetime.now()
#     print('TimeStart: ', TimeStart)
#     TimeStartUp = datetime.datetime.strptime('23:57', "%H:%M")
#     print('TimeStartUp: ', TimeStartUp)
    
    def __init__(self, *args):
        res_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'res')
#        res_path = os.path.join(os.getcwd(), 'res')
        super(MyApp, self).__init__(*args, static_file_path={'res':res_path})
    
    
    #idle: check and run the Scheduler and the Player
    def idle(self):
        #---Time simulator for test purpose---
#         TimeNow = datetime.datetime.now()
#         TimeDelta = TimeNow - self.TimeStart
#         xt = self.TimeStartUp + TimeDelta * 5
#         xt = xt.time()
# #         print('xt: ', xt)
#         xt = str(xt)
#         x = xt.split('.')
#         TimeSimul = x[0][:5]
# #         print('TimeSimul: ', TimeSimul)
        
        #Check if Scheduler is active. If it is active check if the music should start or stop
        if self.SchedOn:
            DayToday = datetime.datetime.today().weekday()
            DayToday += 1
            if DayToday == self.DaySched:
                #Used for simulation
#                 TimeNow = TimeSimul
                TimeNow = datetime.datetime.now().strftime('%H:%M')
                if not (self.TimeRange[0]=='00:00' and self.TimeRange[1]=='00:00'):
                    if not ((TimeNow >= self.TimeRange[0]) and (TimeNow < self.TimeRange[1])):
                        self.TimeIn = False
                        self.TimeRange[0] = '00:00'
                        self.TimeRange[1] = '00:00'
                        self.stop_sched_music()
                else:
                    self.TimeIn = False
                    if len(self.SchedToday):
                        for x in self.SchedToday:
                            appo = self.SchedToday[x]
                            Time1 = appo[0]
                            Time2 = appo[1]
                            if (TimeNow >= Time1) and (TimeNow < Time2):
                                self.SchedNow = appo
                                self.TimeRange[0] = Time1
                                self.TimeRange[1] = Time2
                                self.start_sched_music()
                                break
            else:
                self.stop_sched_music()
                self.update_today_list()
                
        # if the music is playing, it checks random and loop to choose what to do with the next song or turn the music off
        if self.PlayON:
            if not self.t.is_alive():
                if self.PlayNum < self.PlayNumMax or self.PlayRandom == 1:
                    if self.PlayRandom == 0:
                        self.PlayNum = self.PlayNum + 1
                    else:
                        self.PlayNum = randint(1, self.PlayNumMax)
                    self.playSong(self.PlayNum)
                elif self.PlayLoop == 1 and self.PlayNum >= self.PlayNumMax:
                    self.PlayNum = 0
                elif self.PlayLoop == 0 and self.PlayNum >= self.PlayNumMax:
                    self.PlayS.children['lblPlaySDesc'].set_text('MUSIC OFF')
                    self.PlayS.children['widBtPlayS'].children['btPlaySLoad'].set_text('PLAY')
                    self.PlayON = False
                
    
    def main(self):
        self.configlistselected = ''   
        self.songlistselected = ''
        self.listlistselected = ''
        self.playlistselected = ''
        self.schedulerlistselected = ''
# MAIN CONTAINER -----------------------
        self.DisplayPage = gui.Container(width='482px', height='672px', layout_orientation=gui.Container.LAYOUT_VERTICAL, margin='0px auto', style={'display':'block', 'overflow':'hidden'})
        
# MENU page ---------------------------------------------------------------------
        Menu = gui.Container(width='480px', height='670px', layout_orientation=gui.Container.LAYOUT_VERTICAL, margin='0px auto', style={'border':'1px solid black', 'border-radius':'10px'})
        
        #Menu bar used in any page
        self.widTitle = gui.Container(width='100%', height='30px', layout_orientation=gui.Container.LAYOUT_HORIZONTAL, margin='10px auto')
        self.widTitle.style.update({'display':'inline'})
#         btMenu = gui.Menu(width='80px', height='30px', style={'position':'relative', 'top':'10px',  'left':'10px', 'display':'inline'})
        btMenu = gui.Menu(width='80px', height='30px', style={'position':'relative', 'top':'10px',  'left':'10px', 'display':'inline', 'margin':'0px'})
        btmenu = gui.MenuItem('MENU', width='100%', height='100%', style={'line-height':'30px'})
        btsettings = gui.MenuItem('SETTINGS', width='170px', height='30px', style={'line-height':'30px'})
        btsettings.onclick.do(self.set_page, 'Settings')
        btconfig = gui.MenuItem('CONFIG FILES', width='100%', height='30px', style={'line-height':'30px'})
        btconfig.onclick.do(self.set_page, 'Config')
        btsong = gui.MenuItem('MUSIC LIST', width='100%', height='30px', style={'line-height':'30px'})
        btsong.onclick.do(self.set_page, 'Song')
        btlist = gui.MenuItem('FINAL MUSIC LIST', width='100%', height='30px', style={'line-height':'30px'})
        btlist.onclick.do(self.set_page, 'List')
        btplay = gui.MenuItem('PLAY FILES', width='100%', height='30px', style={'line-height':'30px'})
        btplay.onclick.do(self.set_page, 'Play')
        btsched = gui.MenuItem('SCHEDULER', width='100%', height='30px', style={'line-height':'30px'})
        btsched.onclick.do(self.set_page, 'Sched')
        btsave = gui.MenuItem('SAVE / LOAD', width='100%', height='30px', style={'line-height':'30px'})
        btsave.onclick.do(self.set_page, 'Save')
        btquit = gui.MenuItem('QUIT', width='100%', height='30px', style={'line-height':'30px'})
        btquit.onclick.do(self.set_page, 'Quit')
        btshutdown = gui.MenuItem('SHUTDOWN PI', width='100%', height='30px', style={'line-height':'30px'})
        btshutdown.onclick.do(self.set_page, 'Shutdown')
        btmenu.append([btsettings, btconfig, btsong, btlist, btplay, btsched, btsave, btquit, btshutdown])
        btMenu.append(btmenu)
        self.lbl = gui.Label('LIGHTSHOWPI', width='300px', style={'position':'relative', 'top':'10px', 'left':'10px', 'font-size':'25px', 'font-weight':'bold', 'letter-spacing':'1px'})
        logo1 = gui.Image('/res:logo30x30.png', width='30px')
        logo1.style.update({'position':'relative', 'top':'7px', 'left':'32px'})
        self.logo_sched.style.update({'position':'relative', 'top':'7px', 'left':'30px'})
        self.widTitle.append([btMenu, self.lbl, self.logo_sched, logo1])
        
        widVersion = gui.Container(width='100%', height='300px', layout_orientation=gui.Container.LAYOUT_VERTICAL, margin='40px auto 0px')
        lbl1 = gui.Label('LIGHTSHOWPI', width='100%', height='40px', margin='200px auto 0px', style={'font-size':'40px', 'font-weight':'bold', 'letter-spacing':'1px'})
        lbl2 = gui.Label('SHOW', width='100%', height='40px', margin='20px auto 0px', style={'font-size':'40px', 'font-weight':'bold', 'letter-spacing':'1px'})
        lbl3 = gui.Label('MANAGER', width='100%', height='40px', margin='20px auto 0px', style={'font-size':'40px', 'font-weight':'bold', 'letter-spacing':'1px'})
        lbl4 = gui.Label(self.version, width='100%', height='30px', margin='20px auto 0px', style={'font-size':'30px', 'font-weight':'bold', 'letter-spacing':'1px'})
        widVersion.append([lbl1, lbl2, lbl3, lbl4])
        
        Menu.append(widVersion)

        
# SETTINGS page ---------------------------------------------------------
        Settings = gui.Container(width='480px', height='670px', layout_orientation=gui.Container.LAYOUT_VERTICAL, margin='0px auto', style={'border':'1px solid black', 'border-radius':'10px'})
        
        FolderLSP = gui.Label('LightShowPi folder - REQUIRED -', width='100%', height='30px', style={'margin':'70px 20px 0px', 'font-style':'italic', 'text-align':'left'})
        widFolderLSP = gui.Container(width='100%', height='30px', layout_orientation=gui.Container.LAYOUT_HORIZONTAL, margin='10px auto')
        widFolderLSP.style.update({'display':'inline'})
        self.FolderLSP = gui.Label('/home/pi/lightshowpi', width='350px', height='30px', margin='0px 0px 0px 10px', style={'padding-left':'5px', 'font-size':'14px', 'text-align':'left', 'line-height':'2', 'border':'1px solid silver', 'border-radius':'5px'})
        p = Path('/home/pi/lightshowpi')
        if p.exists():
            self.FolderLSP.set_text('/home/pi/lightshowpi')
            self.LightShowPiFolder = Path('/home/pi/lightshowpi')
            self.LightShowPiOverrides = Path(str(self.LightShowPiFolder.absolute())+'/config')
            self.LightShowPiPy = Path(str(self.LightShowPiFolder.absolute())+'/py')
        else:
            self.FolderLSP.set_text('LightShowPi folder not defined')
        self.btFolderLSP = gui.Button("Search", width='80px', height='30px', style={'position':'relative', 'top':'0px',  'right':'-25px', 'display':'inline'})
        self.btFolderLSP.onclick.do(self.open_fileselection_dialog, 'Select LightShowPi folder', False, False, True, 'FolderLSP')
        widFolderLSP.append([self.FolderLSP, self.btFolderLSP])
        Settings.append([FolderLSP, widFolderLSP])
        
        FolderConfig = gui.Label('Config file folder', width='100%', height='30px', style={'margin':'60px 20px 0px', 'font-style':'italic', 'text-align':'left'})
        widFolderConfig = gui.Container(width='100%', height='30px', layout_orientation=gui.Container.LAYOUT_HORIZONTAL, margin='10px auto')
        widFolderConfig.style.update({'display':'inline'})
        self.FolderConfig = gui.Label('/home/pi/lightshowpi', width='350px', height='30px', margin='0px 0px 0px 10px', style={'padding-left':'5px', 'font-size':'14px', 'text-align':'left', 'line-height':'2', 'border':'1px solid silver', 'border-radius':'5px'})
        p = Path('/home/pi/lightshowpi/config')
        if p.exists():
            self.FolderConfig.set_text('/home/pi/lightshowpi/config')
            self.LightShowPiConfig = Path('/home/pi/lightshowpi/config')
        else:
            self.FolderConfig.set_text('Config folder not defined')
        self.btFolderConfig = gui.Button("Search", width='80px', height='30px', style={'position':'relative', 'top':'0px',  'right':'-25px', 'display':'inline'})
        self.btFolderConfig.onclick.do(self.open_fileselection_dialog, 'Select Config file folder', False, False, True, 'FolderConfig')
        widFolderConfig.append([self.FolderConfig, self.btFolderConfig])
        Settings.append([FolderConfig, widFolderConfig])
        
        FolderMusic = gui.Label('Music folder', width='100%', height='30px', style={'margin':'60px 20px 0px', 'font-style':'italic', 'text-align':'left'})
        widFolderMusic = gui.Container(width='100%', height='30px', layout_orientation=gui.Container.LAYOUT_HORIZONTAL, margin='10px auto')
        widFolderMusic.style.update({'display':'inline'})
        self.FolderMusic = gui.Label('', width='350px', height='30px', margin='0px 0px 0px 10px', style={'padding-left':'5px', 'font-size':'14px', 'text-align':'left', 'line-height':'2', 'border':'1px solid silver', 'border-radius':'5px'})
        p = Path('/home/pi/lightshowpi/music')
        if p.exists():
            self.FolderMusic.set_text('/home/pi/lightshowpi/music')
            self.LightShowPiMusic = Path('/home/pi/lightshowpi/music')
        else:
            self.FolderMusic.set_text('Music folder not defined')
        self.btFolderMusic = gui.Button("Search", width='80px', height='30px', style={'position':'relative', 'top':'0px',  'right':'-25px', 'display':'inline'})
        self.btFolderMusic.onclick.do(self.open_fileselection_dialog, 'Select Music file folder', False, False, True, 'FolderMusic')
        widFolderMusic.append([self.FolderMusic, self.btFolderMusic])
        Settings.append([FolderMusic, widFolderMusic])
        
        FolderShow = gui.Label('Shows ".cfg" folder', width='100%', height='30px', style={'margin':'60px 20px 0px', 'font-style':'italic', 'text-align':'left'})
        widFolderShow = gui.Container(width='100%', height='30px', layout_orientation=gui.Container.LAYOUT_HORIZONTAL, margin='10px auto')
        widFolderShow.style.update({'display':'inline'})
        self.FolderShow = gui.Label('', width='350px', height='30px', margin='0px 0px 0px 10px', style={'padding-left':'5px', 'font-size':'14px', 'text-align':'left', 'line-height':'2', 'border':'1px solid silver', 'border-radius':'5px'})
##        p = Path('/home/pi/lightshowpi/music')
##        if p.exists():
##            self.FolderShow.set_text('/home/pi/lightshowpi/music')
##            self.LightShowPiShow = Path('/home/pi/lightshowpi/music')
##        else:
##            self.FolderShow.set_text('Shows folder not defined')
        self.FolderShow.set_text('Shows folder not defined')
        self.btFolderShow = gui.Button("Search", width='80px', height='30px', style={'position':'relative', 'top':'0px',  'right':'-25px', 'display':'inline'})
        self.btFolderShow.onclick.do(self.open_fileselection_dialog, 'Select Shows file folder', False, False, True, 'FolderShow')
        widFolderShow.append([self.FolderShow, self.btFolderShow])
        Settings.append([FolderShow, widFolderShow])
        
        self.btFolderLoad = gui.Button("Load all configs / songs / shows now", width='350px', height='30px', margin='50px auto 0px')
        self.btFolderLoad.onclick.do(self.settings_load)
        Settings.append(self.btFolderLoad)
        
        AlsaDev = gui.Label('ALSA Soundcard name', width='100%', height='30px', style={'margin':'40px 20px 0px', 'font-style':'italic', 'text-align':'left'})
        widAlsaDev = gui.Container(width='100%', height='30px', layout_orientation=gui.Container.LAYOUT_HORIZONTAL, margin='10px auto')
        widAlsaDev.style.update({'display':'inline'})
        self.AlsaDev = gui.TextInput(width='350px', height='30px', margin='0px 0px 0px 10px', style={'padding-left':'5px', 'font-size':'14px', 'text-align':'left', 'line-height':'2', 'border':'1px solid silver', 'border-radius':'5px'})
        self.AlsaDev.set_text('Headphone')
        self.btAlsaDev = gui.Button("Set", width='80px', height='30px', style={'position':'relative', 'top':'0px',  'right':'-25px', 'display':'inline'})
        self.btAlsaDev.onclick.do(self.alsa_dev_set)
        widAlsaDev.append([self.AlsaDev, self.btAlsaDev])
        Settings.append([AlsaDev, widAlsaDev])
        
        
        
# CONFIG page ---------------------------------------------------------
        Config = gui.Container(width='480px', height='670px', layout_orientation=gui.Container.LAYOUT_VERTICAL, margin='0px auto', style={'border':'1px solid black', 'border-radius':'10px'})

        lblConfigDesc = gui.Label('The first config file in the list is the "default" one.', width='100%', style={'margin':'60px auto 0px', 'font-size':'20px', 'font-style':'italic'})
        Config.append(lblConfigDesc)
        self.listConfig = gui.ListView.new_from_list(self.ConfigList, width='460px', height='500px', margin='20px auto 0px')
        self.listConfig.onselection.do(self.list_selected, 'config')
        Config.append(self.listConfig, 'listConfig')
        widBtConfig = gui.Container(width='100%', height='30px', layout_orientation=gui.Container.LAYOUT_HORIZONTAL, margin='10px auto')
        widBtConfig.style.update({'display':'inline'})
        btConfigLoad = gui.Button("Load", width='85px', height='30px', style={'margin':'15px 5px'})    
        btConfigLoad.onclick.do(self.open_fileselection_dialog, 'Select config files', True, True, False, 'ConfigLoad')
        btConfigDefault = gui.Button("Default", width='85px', height='30px', style={'margin':'15px 5px'})
        btConfigDefault.onclick.do(self.config_default)
        btConfigRemove = gui.Button("Remove", width='85px', height='30px', style={'margin':'15px 5px'})
        btConfigRemove.onclick.do(self.config_remove)
        btConfigClear = gui.Button("Clear list", width='85px', height='30px', style={'margin':'15px 5px'})
        btConfigClear.onclick.do(self.config_clear)
        Config.append([btConfigLoad, btConfigDefault, btConfigRemove, btConfigClear])

        
# Songs page ---------------------------------------------------------
        Song = gui.Container(width='480px', height='670px', layout_orientation=gui.Container.LAYOUT_VERTICAL, margin='0px auto', style={'border':'1px solid black', 'border-radius':'10px'})

        self.listSong = gui.ListView.new_from_list(self.SongList, width='460px', height='560px', margin='50px auto 0px')
        self.listSong.onselection.do(self.list_selected, 'song')
        Song.append(self.listSong, 'listSong')
        btSongLoad = gui.Button("Load", width='70px', height='30px', style={'margin':'15px 4px'})    
        btSongLoad.onclick.do(self.open_fileselection_dialog, 'Select song files', True, True, False, 'SongLoad')
        btSongDup = gui.Button("Dup", width='70px', height='30px', style={'margin':'15px 4px'})
        btSongDup.onclick.do(self.song_dup)
        btSongUp = gui.Button("Up", width='70px', height='30px', style={'margin':'15px 4px'})
        btSongUp.onclick.do(self.song_up)
        btSongDn = gui.Button("Down", width='70px', height='30px', style={'margin':'15px 4px'})
        btSongDn.onclick.do(self.song_dn)
        btSongDel = gui.Button("Del", width='70px', height='30px', style={'margin':'15px 4px'})
        btSongDel.onclick.do(self.song_del)
        btSongClear = gui.Button("Clear", width='70px', height='30px', style={'margin':'15px 4px'})
        btSongClear.onclick.do(self.song_clear)
        Song.append([btSongLoad, btSongDup, btSongUp, btSongDn, btSongDel, btSongClear])

# Final list page ---------------------------------------------------------
        List = gui.Container(width='480px', height='670px', layout_orientation=gui.Container.LAYOUT_VERTICAL, margin='0px auto', style={'border':'1px solid black', 'border-radius':'10px'})

        self.listList = gui.ListView.new_from_list(self.ListList, width='460px', height='560px', margin='50px auto 0px')
        self.listList.onselection.do(self.list_selected, 'list')
        List.append(self.listList, 'listList')
        btListUpdate = gui.Button("Update list", width='170px', height='30px', style={'margin':'15px 4px'})
        btListUpdate.onclick.do(self.list_update)
        btListGenerate = gui.Button("Generate play list", width='170px', height='30px', style={'margin':'15px 4px'})
        btListGenerate.onclick.do(self.list_generate)
        List.append([btListUpdate, btListGenerate])

# PLAY page ---------------------------------------------------------
        PlayS = gui.Container(width='480px', height='670px', layout_orientation=gui.Container.LAYOUT_VERTICAL, margin='0px auto', style={'border':'1px solid black', 'border-radius':'10px'})
        
        lblPlaySDesc = gui.Label('MUSIC OFF', width='100%', style={'margin':'60px auto 0px', 'font-size':'20px', 'font-style':'italic'})
        PlayS.append(lblPlaySDesc, 'lblPlaySDesc')
        self.listPlayS = gui.ListView.new_from_list('', width='460px', height='450px', margin='20px auto 0px')
        self.listPlayS.onselection.do(self.list_selected, 'playS')
        PlayS.append(self.listPlayS, 'listPlayS')
        self.widBtPlayS = gui.Container(width='98%', height='40px', layout_orientation=gui.Container.LAYOUT_HORIZONTAL)
        self.widBtPlayS.style.update({'margin':'10px auto 0px'})
        self.btPlaySVolumeM = gui.Button("Vol -", width='60px', height='30px', style={'margin':'5px 5px 0px 50px'})    
        self.btPlaySVolumeM.onclick.do(self.playS_volumeM)
        self.btPlaySPrev = gui.Button("PRV", width='60px', height='30px', style={'margin':'5px 5px 0px'})    
        self.btPlaySPrev.onclick.do(self.playSprev_dialog)
        self.btPlaySLoad = gui.Button("PLAY", width='85px', height='40px', style={'margin':'0px 5px 0px'})    
        self.btPlaySLoad.onclick.do(self.playS_dialog)
        self.btPlaySNext = gui.Button("NXT", width='60px', height='30px', style={'margin':'5px 5px 0px'})    
        self.btPlaySNext.style.update({'display':'block'})
        self.btPlaySNext.onclick.do(self.playSnext_dialog)
        self.btPlaySVolumeP = gui.Button("Vol +", width='60px', height='30px', style={'margin':'5px 5px 0px'})    
        self.btPlaySVolumeP.onclick.do(self.playS_volumeP)
        self.widBtPlayS.append(self.btPlaySVolumeM)
        self.widBtPlayS.append(self.btPlaySPrev)
        self.widBtPlayS.append(self.btPlaySLoad, 'btPlaySLoad')
        self.widBtPlayS.append(self.btPlaySNext)
        self.widBtPlayS.append(self.btPlaySVolumeP)
        PlayS.append(self.widBtPlayS, 'widBtPlayS')
        self.widBtPlayS2 = gui.Container(width='98%', height='30px', layout_orientation=gui.Container.LAYOUT_HORIZONTAL)
        self.widBtPlayS2.style.update({'margin':'10px auto 0px'})
        if self.Volume != 0:
            volnum = 'Vol ' + str(self.Volume) + ('%')
        else:
            volnum = 'Vol OFF'
        self.btPlaySVolumeOn = gui.Button(volnum, width='80px', height='30px', style={'margin':'0px 5px 0px'})    
        self.btPlaySVolumeOn.onclick.do(self.playS_volumeOn)
        self.btPlaySelect = gui.Button("Play selected", width='130px', height='30px', style={'margin':'0px 5px 0px'})    
        self.btPlaySelect.onclick.do(self.playSelect_dialog)
        self.btPlaySLoop = gui.Button("Loop OFF", width='90px', height='30px', style={'margin':'0px 5px 0px'})    
        self.btPlaySLoop.onclick.do(self.playSloop_dialog)
        self.btPlaySRand = gui.Button("Random OFF", width='130px', height='30px', style={'margin':'0px 5px 0px'})    
        self.btPlaySRand.onclick.do(self.playSrand_dialog)
        self.widBtPlayS2.append(self.btPlaySVolumeOn, 'btPlaySVolumeOn')
        self.widBtPlayS2.append(self.btPlaySelect, 'btPlaySelect')
        self.widBtPlayS2.append(self.btPlaySLoop, 'btPlaySLoop')
        self.widBtPlayS2.append(self.btPlaySRand, 'btPlaySRand')
        PlayS.append(self.widBtPlayS2, 'widBtPlayS2')

# SCHEDULER page ---------------------------------------------------------
        Scheduler = gui.Container(width='480px', height='670px', layout_orientation=gui.Container.LAYOUT_VERTICAL, margin='0px auto', style={'border':'1px solid black', 'border-radius':'10px'})
        
        self.listSched = gui.ListView.new_from_list(self.SchedList, width='460px', height='560px', margin='50px auto 0px')
        self.listSched.onselection.do(self.list_selected, 'sched')
        Scheduler.append(self.listSched, 'listSched')
        btSchedAdd = gui.Button("Add", width='85px', height='30px', style={'margin':'15px 5px'})    
        btSchedAdd.onclick.do(self.add_sched)
        btSchedEdit = gui.Button("Edit", width='85px', height='30px', style={'margin':'15px 5px'})
        btSchedEdit.onclick.do(self.edit_sched)
        btSchedRemove = gui.Button("Remove", width='85px', height='30px', style={'margin':'15px 5px'})
        btSchedRemove.onclick.do(self.scheduler_del)
        btSchedClear = gui.Button("Clear list", width='85px', height='30px', style={'margin':'15px 5px'})
        btSchedClear.onclick.do(self.sched_clear)
        self.btSchedActive = gui.Button("Turn ON", width='85px', height='30px', style={'margin':'15px 5px'})
        self.btSchedActive.onclick.do(self.sched_active)
        Scheduler.append([btSchedAdd, btSchedEdit, btSchedRemove, btSchedClear, self.btSchedActive])
        
# SAVE page ---------------------------------------------------------------------
        Save = gui.Container(width='480px', height='670px', layout_orientation=gui.Container.LAYOUT_VERTICAL, margin='0px auto', style={'border':'1px solid black', 'border-radius':'10px'})

        btSaveS = gui.Button("SAVE SHOW FORMAT", width='240px', height='40px', style={'margin':'60px auto 0px', 'display':'block'})
        self.fileSaveAsDialog = EditorFileSaveDialog('Show Save', 'Select the project folder and type a filename', False, '.', True, False, self)
        self.fileSaveAsDialog.add_fileinput_field('show.shw')
        #self.fileSaveAsDialog.fileFolderNavigator.controlBack.set_size('10%', '100%')
        #self.fileSaveAsDialog.fileFolderNavigator.controlGo.set_size('15%', '100%')
        #self.fileSaveAsDialog.fileFolderNavigator.pathEditor.set_size('75%', '100%')
        self.fileSaveAsDialog.fileFolderNavigator.controlBack.style.update({'height':'30px', 'font-size':'15px'})
        self.fileSaveAsDialog.fileFolderNavigator.controlGo.set_size({'height':'30px', 'font-size':'12px'})
        self.fileSaveAsDialog.fileFolderNavigator.pathEditor.style.update({'padding-left':'5px', 'font-size':'12px', 'line-height':'2'})
        self.fileSaveAsDialog.fileFolderNavigator.itemContainer.style.update({'font-size':'12px'})
        self.fileSaveAsDialog.confirm_value.do(self.on_saveas_dialog_confirm)
        btSaveS.onclick.do(self.fileSaveAsDialog.show)
        btLoadS = gui.Button("LOAD SHOW FORMAT", width='240px', height='40px', style={'margin':'20px auto 0px', 'display':'block'})
        btLoadS.onclick.do(self.open_fileselection_dialog, 'Select file to load', False, True, False, 'LoadS')
        btSaveSched = gui.Button("SAVE SCHEDULE", width='240px', height='40px', style={'margin':'40px auto 0px', 'display':'block'})
        self.schedSaveAsDialog = EditorFileSaveDialog('Schedule Save', 'Select the project folder and type a filename', False, '.', True, False, self)
        self.schedSaveAsDialog.add_fileinput_field('schedule.sch')
        #self.schedSaveAsDialog.fileFolderNavigator.controlBack.set_size('10%', '100%')
        #self.schedSaveAsDialog.fileFolderNavigator.controlGo.set_size('15%', '100%')
        #self.schedSaveAsDialog.fileFolderNavigator.pathEditor.set_size('75%', '100%')
        self.fileSaveAsDialog.fileFolderNavigator.controlBack.style.update({'height':'30px', 'font-size':'15px'})
        self.fileSaveAsDialog.fileFolderNavigator.controlGo.set_size({'height':'30px', 'font-size':'1px'})
        self.schedSaveAsDialog.fileFolderNavigator.pathEditor.style.update({'padding-left':'5px', 'font-size':'12px', 'line-height':'2'})
        self.schedSaveAsDialog.fileFolderNavigator.itemContainer.style.update({'font-size':'12px'})
        self.schedSaveAsDialog.confirm_value.do(self.sched_saveas_dialog_confirm)
        btSaveSched.onclick.do(self.schedSaveAsDialog.show)
        btLoadSched = gui.Button("LOAD SCHEDULE", width='240px', height='40px', style={'margin':'20px auto 0px', 'display':'block'})
        btLoadSched.onclick.do(self.open_fileselection_dialog, 'Select schedule file to load', False, True, False, 'LoadSched')  
        btRemSpace = gui.Button("REMOVE SPECIAL CHARACTERS", width='320px', height='40px', style={'margin':'60px auto 0px', 'display':'block'})
        btRemSpace.onclick.do(self.open_fileselection_dialog, 'Select files or folder', True, True, True, 'RemSpace')

        Save.append(btSaveS)
        Save.append(btLoadS)
        Save.append(btSaveSched)
        Save.append(btLoadSched)
        Save.append(btRemSpace)
        
# ---------------------------------------------------------------------      
        
        self.Menu = Menu
        self.Settings = Settings
        self.Config = Config
        self.Song = Song
        self.List = List
        self.PlayS = PlayS
        self.Save = Save
        self.Scheduler = Scheduler

        self.DisplayPage.append(self.widTitle, 'MenuBar')
        self.DisplayPage.append(self.Menu, 'pgMenu')
        return self.DisplayPage


# Used to display the right page
    def set_page(self, emitter, name):
        page = self.DisplayPage.children.keys()
#         print('Page: ', page)
        appo = []
        for x in page:
            appo.append(x)
        if name == 'Menu':
            self.DisplayPage.remove_child(self.DisplayPage.children[appo[1]])
            self.DisplayPage.append(self.Menu,'pgMenu')
        elif name == 'Settings':
            self.DisplayPage.remove_child(self.DisplayPage.children[appo[1]])
            self.DisplayPage.append(self.Settings,'pgSettings')
            self.lbl.set_text('SETTINGS')
        elif name == 'Config':
            self.DisplayPage.remove_child(self.DisplayPage.children[appo[1]])
            self.DisplayPage.append(self.Config,'pgConfig')
            self.lbl.set_text('CONFIG FILES')
        elif name == 'Song':
            self.DisplayPage.remove_child(self.DisplayPage.children[appo[1]])
            self.DisplayPage.append(self.Song,'pgSong')
            self.lbl.set_text('MUSIC LIST')
        elif name == 'List':
            self.DisplayPage.remove_child(self.DisplayPage.children[appo[1]])
            self.DisplayPage.append(self.List,'pgList')
            self.lbl.set_text('FINAL MUSIC LIST')
        elif name == 'Play':
            self.DisplayPage.remove_child(self.DisplayPage.children[appo[1]])
            self.DisplayPage.append(self.PlayS,'pgPlayS')
            self.lbl.set_text('PLAY FILES')
            self.play_list_update()
        elif name == 'Sched':
            self.DisplayPage.remove_child(self.DisplayPage.children[appo[1]])
            self.DisplayPage.append(self.Scheduler,'pgSched')
            self.lbl.set_text('SCHEDULER')
        elif name == 'Save':
            self.DisplayPage.remove_child(self.DisplayPage.children[appo[1]])
            self.DisplayPage.append(self.Save,'pgSave')
            self.lbl.set_text('SAVE / LOAD')
        elif name == 'Quit':
            self.dialogquit = gui.GenericDialog(title='QUIT', message='Do you want to quit?', width='400px', style={'border':'1px solid black', 'border-radius':'10px', 'position':'relative', 'top':'50px',})
            self.dialogquit.conf.style.update({'margin-right':'100px', 'width':'100px'})
            self.dialogquit.confirm_dialog.do(self.quit_confirm)
            self.dialogquit.show(self)
        elif name == 'Shutdown':
            self.dialogshutdown = gui.GenericDialog(title='SHUTDOWN PI', message='Do you want to shutdown the PI?', width='400px', style={'border':'1px solid black', 'border-radius':'10px', 'position':'relative', 'top':'50px',})
            self.dialogshutdown.conf.style.update({'margin-right':'100px', 'width':'100px'})
            self.dialogshutdown.confirm_dialog.do(self.shutdown_confirm)
            self.dialogshutdown.show(self)
        
    def quit_confirm(self, widget):
        if self.PlayON:
            os_string = 'sudo kill `pgrep -f lightshowpi`'
            self.p = threading.Thread(target=self.sys_thread, args=(os_string,), daemon=True)
            self.p.start()
            self.PlayON = False
        time.sleep(0.5)
        self.close()
    
    def shutdown_confirm(self, widget):
        if self.PlayON:
            os_string = 'sudo kill `pgrep -f lightshowpi`'
            self.p = threading.Thread(target=self.sys_thread, args=(os_string,), daemon=True)
            self.p.start()
            self.PlayON = False
        time.sleep(0.5)
        os_string = 'sudo shutdown -h now'
        self.sys_thread(os_string)
#        print ("OUT")
        
        


# Open the file manager to select folders or files
# Parameters references:
    ##(self, title='File dialog', message='Select files and folders',
    ## multiple_selection=True, selection_folder='.',
    ##allow_file_selection=True, allow_folder_selection=True, **kwargs):
    ## (self.open_fileselection_dialog, 'Select LightShowPi folder', False, True, 'FolderLSP')

    def open_fileselection_dialog(self, widget, message, mult_select, file_select, fold_select, chiamata):
        self.fileselectionDialog = gui.FileSelectionDialog('Selection dialog', message, mult_select, '.', file_select, fold_select)
        #self.fileselectionDialog.fileFolderNavigator.controlBack.set_size('10%', '100%')
        #self.fileselectionDialog.fileFolderNavigator.controlGo.set_size('15%', '100%')
        #self.fileselectionDialog.fileFolderNavigator.pathEditor.set_size('75%', '100%')
        self.fileselectionDialog.fileFolderNavigator.controlBack.style.update({'height':'30px', 'font-size':'15px'})
        self.fileselectionDialog.fileFolderNavigator.controlGo.set_size({'height':'30px', 'font-size':'12px'})
        self.fileselectionDialog.fileFolderNavigator.pathEditor.style.update({'padding-left':'5px', 'font-size':'14px', 'line-height':'2'})
        self.fileselectionDialog.confirm_value.do(self.on_fileselection_dialog_confirm, chiamata)
        # here is returned the Input Dialog widget, and it will be shown
        self.fileselectionDialog.show(self)

# Return file or directories selected, based on who called the file manager it checks different things
    def on_fileselection_dialog_confirm(self, widget, filelist, chiamata):
        if len(filelist):
            # SETTINGS MENU CALLS
            if chiamata == 'FolderLSP':
                self.LightShowPiFolder = Path(filelist[0])
                # Check if LightShowPi is a good folder with /config and /py folders
                appo = Path(str(self.LightShowPiFolder.absolute())+'/config')
                if appo.exists():
                    self.LightShowPiOverrides = appo
                else:
                    self.LightShowPiOverrides = []
                appo = Path(str(self.LightShowPiFolder.absolute())+'/py')
                if appo.exists():
                    self.LightShowPiPy = appo
                else:
                    self.LightShowPiPy = []
                if self.LightShowPiOverrides == []:
                    msg = 'LightShowPi folder "../config" not found'
                    self.dialog = gui.GenericDialog(title='ERROR', message=msg, width='400px', style={'border':'1px solid black', 'border-radius':'10px', 'position':'relative', 'top':'50px',})
                    self.dialog.cancel.style['display'] = 'none'
                    self.dialog.conf.style.update({'margin-right':'150px', 'width':'100px'})
                    self.dialog.show(self)
                    self.FolderLSP.set_text('LightShowPi folder not valid')
                    self.LightShowPiFolder = []
                elif self.LightShowPiPy == []:
                    msg = 'LightShowPi folder "../py" not found'
                    self.dialog = gui.GenericDialog(title='ERROR', message=msg, width='400px', style={'border':'1px solid black', 'border-radius':'10px', 'position':'relative', 'top':'50px',})
                    self.dialog.cancel.style['display'] = 'none'
                    self.dialog.conf.style.update({'margin-right':'150px', 'width':'100px'})
                    self.dialog.show(self)
                    self.FolderLSP.set_text('LightShowPi folder not valid')
                    self.LightShowPiFolder = []
                else:
                    name = str(self.LightShowPiFolder.absolute())
                    name = MyApp.cut_name(name)
                    self.FolderLSP.set_text(name)
            elif chiamata == 'FolderConfig':
                self.LightShowPiConfig = Path(filelist[0])
                name = str(self.LightShowPiConfig.absolute())
                name = MyApp.cut_name(name)
                self.FolderConfig.set_text(name)
            elif chiamata == 'FolderMusic':
                self.LightShowPiMusic = Path(filelist[0])
                name = str(self.LightShowPiMusic.absolute())
                name = MyApp.cut_name(name)
                self.FolderMusic.set_text(name)
            elif chiamata == 'FolderShow':
                self.LightShowPiShow = Path(filelist[0])
                name = str(self.LightShowPiShow.absolute())
                name = MyApp.cut_name(name)
                self.FolderShow.set_text(name)
                
        # CONFIG - add selected .cfg file in config list if not already there
            elif chiamata == 'ConfigLoad':
                for y in filelist:
                    y = Path(y)
                    if y.suffix == ".cfg":
                        found = 0
                        for x in self.ConfigList:
                            if y.name == x.name:
                                found = 1
                        if not found:
                            self.ConfigList.append(y)
                appo = []
                appo = self.fill_list(self.ConfigList)
                self.Config.children['listConfig'].empty()
                self.Config.children['listConfig'].append(appo)
                
        # SONG - add selected songs in song list, allow duplicate
            elif chiamata == 'SongLoad':
                for y in filelist:
                    y = Path(y)
                    if y.suffix in self.file_types_all:
                        key = self.song_key(self.SongListDict)
                        self.SongListDict[key] = y
                self.SongList = {}
                for z in self.SongListDict:
                    temp = self.SongListDict[z]
                    self.SongList[int(z)] = str(temp.name)
                self.Song.children['listSong'].empty()
                self.Song.children['listSong'].append(self.SongList)
                
        # SAVE
        # replace special characters in file or folder name with "_", made to avoid problem with special characters
            elif chiamata == 'RemSpace':
                for y in filelist:
                    y = Path(y)
                    if y.is_dir():
                        appo = []
                        for z in self.file_types:
                            z = "*" + z
                            appo += list(y.glob(z))
                        for w in appo:
                            Nam = w.name
                            for ch in [' ','\\','`','*','{','}','[',']','(',')','>','#','+','-','!','$','\'','&']:
                                Nam = Nam.replace(ch, '_')
                            if w.name != Nam:
                                Nam = str(w.parent) + "/" + Nam
                                OrigNam = w.absolute()
                                os.rename(OrigNam, Nam)
                    else:
                        Nam = y.name
                        Nam = Nam.replace(" ","_")
                        Nam = str(y.parent) + "/" + Nam
                        OrigNam = y.absolute()
                        if OrigNam != Nam:
                            os.rename(OrigNam, Nam)

        # load show file
            elif chiamata == 'LoadS':
                y = Path(filelist[0])
                if y.suffix != '.shw':
                    dialog = gui.GenericDialog(title='ERROR', message='Wrong file format!', width='400px', style={'border':'1px solid black', 'border-radius':'10px', 'position':'relative', 'top':'50px',})
                    dialog.cancel.style['display'] = 'none'
                    dialog.conf.style.update({'margin-right':'150px', 'width':'100px'})
                    dialog.show(self)
                else:
                    y = y.absolute()
                    with open(y, 'r') as file:
                        Data = file.read()
                    Data = Data.split('\n')
                    if Data[0] == '[SHOW MANAGER]':
##                        print('FILE OK')
                        del Data[0]
                    #Check if songs and config exists
                        SongExist = []
                        ConfExist = []
                        for x in Data:
                            if x != '':
                                Name, Conf = x.split('\t')
                                NameApp = Path(Name)
                                if NameApp.exists():
                                    SongExist.append(Name)
                                if Conf != 'none':
                                    ConfApp = Path(Conf)
                                    if ConfApp.exists():
                                        ConfExist.append(Conf)
                        #If there are no songs nothing is loaded
                        if len(SongExist):
                        #Check if exist songs and configs or only songs
                            if len(ConfExist):
##                                print('Song and conf exist')
                                self.SongListDict = {}
                                self.ListList = {}
                                self.ConfigList = []
                                found_all_song = 1
                                found_all_config = 1
                                for y in Data:
                                    if y != '':
                                        Name, Conf = y.split('\t')
                                        Name = Path(Name)
                                        if Name.exists():
                                            if Name.suffix in self.file_types_all:
                                                key = self.song_key(self.SongListDict)
                                                self.SongListDict[key] = Name
                                        else:
                                            found_all_song = 0
                                        if Conf != 'none':
                                            Conf = Path(Conf)
                                            if Conf.exists():
                                                found = 0
                                                for x in self.ConfigList:
                                                    if Conf.name == x.name:
                                                        found = 1
                                                if not found:
                                                    self.ConfigList.append(Conf)
                                            else:
                                                found_all_config = 0
                                        if Name.exists():
                                            if Conf != 'none':
                                                Conf = Path(Conf)
                                                if Conf.exists():
                                                    appo = []
                                                    appo.append(Name)
                                                    appo.append(Conf)
                                                    self.ListList[key] = appo
                                                else:
                                                    appo = []
                                                    appo.append(Name)
                                                    appo.append('none')
                                                    self.ListList[key] = appo
                                            else:
                                                appo = []
                                                appo.append(Name)
                                                appo.append('none')
                                                self.ListList[key] = appo        
                                #Update songs list            
                                self.SongList = {}
                                for z in self.SongListDict:
                                    temp = self.SongListDict[z]
                                    self.SongList[int(z)] = str(temp.name)
                                self.Song.children['listSong'].empty()
                                self.Song.children['listSong'].append(self.SongList)
                                #Update configs list 
                                appo = []
                                appo = self.fill_list(self.ConfigList)
                                self.Config.children['listConfig'].empty()
                                self.Config.children['listConfig'].append(appo)
                                #Update music + config list
                                self.List.children['listList'].empty()
                                for x in self.ListList:
                                    appo = []
                                    appo = self.ListList[x]
                                    appoSong = appo[0].name
                                    if appo[1] == 'none':
                                        appoConfig = "--> " + appo[1]
                                    else:
                                        appoConfig = "--> " + appo[1].name
                                    temp = {}
                                    temp[int(x)] = appoSong
                                    self.List.children['listList'].append(temp)
                                    temp = {}
                                    temp[int(x+1000)] = appoConfig
                                    self.List.children['listList'].append(temp)
                                if found_all_song == 1 and found_all_config == 1:
                                    pass
                                else:
                                    if found_all_song == 1 and found_all_config == 0:
                                        msg = 'Impossible load all config files, LightShowPi default.cfg will be used'
                                    elif found_all_song == 0 and found_all_config == 1:
                                        msg = 'Impossible load some songs!'
                                    else:
                                        msg = 'Impossible load all config files, LightShowPi default.cfg will be used. Impossible load some songs!'
                                    self.dialog = gui.GenericDialog(title='WARNING', message=msg, width='400px', style={'border':'1px solid black', 'border-radius':'10px', 'position':'relative', 'top':'50px',})
                                    self.dialog.cancel.style['display'] = 'none'
                                    self.dialog.conf.style.update({'margin-right':'150px', 'width':'100px'})
                                    self.dialog.show(self)
                            else:
##                                print('Only songs exist')
                                self.SongListDict = {}
                                self.ListList = {}
                                found_all = 1
                                for y in Data:
                                    if y != '':
                                        Name, Conf = y.split('\t')
                                        Name = Path(Name)
                                        if Name.exists():
                                            if Name.suffix in self.file_types_all:
                                                key = self.song_key(self.SongListDict)
                                                self.SongListDict[key] = Name
                                            else:
                                                found_all = 0         
                                #Update songs list
                                self.SongList = {}
                                for z in self.SongListDict:
                                    temp = self.SongListDict[z]
                                    self.SongList[int(z)] = str(temp.name)
                                self.Song.children['listSong'].empty()
                                self.Song.children['listSong'].append(self.SongList)
                                #Update music + config list
                                if str(self.LightShowPiOverrides) != '':
                                    self.Default_cfg = Path(str(self.LightShowPiOverrides.absolute())+'/defaults.cfg')
                                    if self.Default_cfg.exists():
                                        self.NoConfig = 1
                                        if found_all == 1:
                                            msg = 'No config file uploaded, LightShowPi default.cfg will be used'
                                        else:
                                            msg = 'No config file uploaded, LightShowPi default.cfg will be used. Impossible load some songs!'
                                        self.dialog = gui.GenericDialog(title='WARNING', message=msg, width='400px', style={'border':'1px solid black', 'border-radius':'10px', 'position':'relative', 'top':'50px',})
                                        self.dialog.cancel.style['display'] = 'none'
                                        self.dialog.conf.style.update({'margin-right':'150px', 'width':'100px'})
                                        self.dialog.show(self)
                                        self.List.children['listList'].empty()
                                        self.ListList = {}
                                        for x in self.SongListDict:
                                            appo = []
                                            appo.append(self.SongListDict[x])
                                            exten = appo[0].suffix
                                            appo.append('none')
                                            self.ListList[x] = appo
                                        for x in self.ListList:
                                            appo = []
                                            appo = self.ListList[x]
                                            appoSong = appo[0].name
                                            if appo[1] == 'none':
                                                appoConfig = "--> " + appo[1]
                                            else:
                                                appoConfig = "--> " + appo[1].name
                                            temp = {}
                                            temp[int(x)] = appoSong
                                            self.List.children['listList'].append(temp)
                                            temp = {}
                                            temp[int(x+1000)] = appoConfig
                                            self.List.children['listList'].append(temp)
                                    else:
                                        msg = 'No config file found, impossible to create a list! Only songs loaded.'
                                        self.dialog = gui.GenericDialog(title='WARNING', message=msg, width='400px', style={'border':'1px solid black', 'border-radius':'10px', 'position':'relative', 'top':'50px',})
                                        self.dialog.cancel.style['display'] = 'none'
                                        self.dialog.conf.style.update({'margin-right':'150px', 'width':'100px'})
                                        self.dialog.show(self)           
                                else:
                                    msg = 'No config file found, impossible to create a list! Only songs loaded.'
                                    self.dialog = gui.GenericDialog(title='WARNING', message=msg, width='400px', style={'border':'1px solid black', 'border-radius':'10px', 'position':'relative', 'top':'50px',})
                                    self.dialog.cancel.style['display'] = 'none'
                                    self.dialog.conf.style.update({'margin-right':'150px', 'width':'100px'})
                                    self.dialog.show(self)        
                        else:
                            dialog = gui.GenericDialog(title='ERROR', message='No valid song paths found!', width='400px', style={'border':'1px solid black', 'border-radius':'10px', 'position':'relative', 'top':'50px',})
                            dialog.cancel.style['display'] = 'none'
                            dialog.conf.style.update({'margin-right':'150px', 'width':'100px'})
                            dialog.show(self)
                    else:
                        dialog = gui.GenericDialog(title='ERROR', message='No show file!', width='400px', style={'border':'1px solid black', 'border-radius':'10px', 'position':'relative', 'top':'50px',})
                        dialog.cancel.style['display'] = 'none'
                        dialog.conf.style.update({'margin-right':'150px', 'width':'100px'})
                        dialog.show(self)
            
            #SCHEDULER -add or edit
            elif chiamata == 'Scheduler':
                y = Path(filelist[0])
                if y.suffix != '.shw':
                    dialog = gui.GenericDialog(title='ERROR', message='Wrong file format!', width='400px', style={'border':'1px solid black', 'border-radius':'10px', 'position':'relative', 'top':'50px',})
                    dialog.cancel.style['display'] = 'none'
                    dialog.conf.style.update({'margin-right':'150px', 'width':'100px'})
                    dialog.show(self)
                else:
                    self.SchedFileName = filelist[0]
                    appoName = MyApp.cut_name(filelist[0], False, 30)
                    self.aFolderShow.set_text(appoName)
            
            # SCHEDULER load
            elif chiamata == 'LoadSched':
                y = Path(filelist[0])
                if y.suffix != '.sch':
                    dialog = gui.GenericDialog(title='ERROR', message='Wrong file format!', width='400px', style={'border':'1px solid black', 'border-radius':'10px', 'position':'relative', 'top':'50px',})
                    dialog.cancel.style['display'] = 'none'
                    dialog.conf.style.update({'margin-right':'150px', 'width':'100px'})
                    dialog.show(self)
                else:
                    y = y.absolute()
                    with open(y, 'r') as file:
                        Data = file.read()
                    Data = Data.split('\n')
                    if Data[0] == '[SHOW MANAGER SCHEDULE]':
                        del Data[0]
                        appo = []
                        for q in Data:
                            if q != '':
                                appo = q.split('\t')
                                for w in range(2,11):
                                    if appo[w] == 'True':
                                        appo[w] = bool(1)
                                    else:
                                        appo[w] = bool(0)
                                if len(self.SchedList):
                                    found = 0
                                    for x in self.SchedList:
                                        w = self.SchedList[x]
                                        appoCheck = datetime.datetime.strptime(appo[0], "%H:%M")
                                        tempCheck = datetime.datetime.strptime(w[0], "%H:%M")
                                        if appoCheck < tempCheck:
                                            temp = self.SchedList.copy()
                                            self.SchedList[x] = appo
                                            k = x
                                            q = len(self.SchedList)
                                            while k < q + 1:
                                                self.SchedList[k+1] = temp[k]
                                                k = k + 1
                                            found = 1
                                            break
                                    if not found:
                                        key = self.song_key(self.SchedList)
                                        self.SchedList[key] = appo
                                else:
                                    key = self.song_key(self.SchedList)
                                    self.SchedList[key] = appo
                        self.drawschedulerlist(self.SchedList)
                    else:
                        dialog = gui.GenericDialog(title='ERROR', message='No schedule file!', width='400px', style={'border':'1px solid black', 'border-radius':'10px', 'position':'relative', 'top':'50px',})
                        dialog.cancel.style['display'] = 'none'
                        dialog.conf.style.update({'margin-right':'150px', 'width':'100px'})
                        dialog.show(self)



                
# Load all configs, songs and shows
    def settings_load(self, widget):
    # CONFIG - Config search
        if self.LightShowPiConfig != '':
            p = []
            p = Path(self.LightShowPiConfig)
            if p.exists():
                appo = []
                appo += list(p.glob("*.cfg"))
                for y in appo:
                    found = 0
                    for x in self.ConfigList:
                        if y.name == x.name:
                            found = 1
                    if not found:
                        self.ConfigList.append(y)
                appo = []
                appo = self.fill_list(self.ConfigList)
                self.Config.children['listConfig'].empty()
                self.Config.children['listConfig'].append(appo)

    # SONG - Songs search, don't load duplicate from the same folder
        if self.LightShowPiMusic != '':
            p = []
            p = Path(self.LightShowPiMusic)
            if p.exists():
                appo = []
                for x in self.file_types:
                    x = "*" + x
                    appo += list(p.glob(x))
                for y in appo:
                    found = 0
                    for z in self.SongListDict.values():
                        if y == z:
                            found = 1
                    if not found:
                        key = self.song_key(self.SongListDict)
                        self.SongListDict[key] = y
                self.SongList = {}
                for z in self.SongListDict:
                    temp = self.SongListDict[z]
                    self.SongList[int(z)] = str(temp.name)
                self.Song.children['listSong'].empty()
                self.Song.children['listSong'].append(self.SongList)
            
    # .PY / .CFG SHOWS - Shows search, don't load duplicate from the same folder
        if self.LightShowPiShow != '':
            p = []
            p = Path(self.LightShowPiShow)
            if p.exists():
                appo = []
##                appo += list(p.glob("*.py"))
                appo += list(p.glob("*.cfg"))
                for y in appo:
                    found = 0
                    for z in self.SongListDict.values():
                        if y == z:
                            found = 1
                    if not found:
                        key = self.song_key(self.SongListDict)
                        self.SongListDict[key] = y
                self.SongList = {}
                for z in self.SongListDict:
                    temp = self.SongListDict[z]
                    self.SongList[int(z)] = str(temp.name)
                self.Song.children['listSong'].empty()
                self.Song.children['listSong'].append(self.SongList)
        
        self.dialog = gui.GenericDialog(title='', message='Done', width='300px', style={'border':'1px solid black', 'border-radius':'10px', 'position':'relative', 'top':'50px',})
        self.dialog.cancel.style['display'] = 'none'
        self.dialog.conf.style.update({'margin-right':'100px', 'width':'100px'})
        self.dialog.show(self)
        

# Return the selected file in list
    def list_selected(self, widget, selected_item_key, chiamata):
        if chiamata == 'config':
            self.configlistselected = self.listConfig.children[selected_item_key].get_text()
        if chiamata == 'song':
            self.songlistselected = selected_item_key
        if chiamata == 'list':
            if selected_item_key < 1000:
                self.listlistselected = selected_item_key
                appo = self.listList.children[selected_item_key].get_text()
                appo1 = appo[-3:]
                appo2 = appo[-4:]
                if appo1 != '.py' and appo2 != '.cfg':
                    self.list_config_selection()
        if chiamata == 'playS':
            self.PlayNumSelected = selected_item_key
        if chiamata == 'sched':
            self.schedulerlistselected = selected_item_key           
        

# CONFIG - Move the selected config file at the top of the list
    def config_default(self, widget):
        appo = self.configlistselected
        if appo != "":
            pos = 0
            count = 0
            for x in self.ConfigList:
                if x.name == appo:
                    pos = count
                count += 1
            if pos > 0:
                temp = self.ConfigList[0]
                self.ConfigList[0] = self.ConfigList[pos]
                self.ConfigList[pos] = temp
                temp = []
                temp = self.fill_list(self.ConfigList)
                self.Config.children['listConfig'].empty()
                self.Config.children['listConfig'].append(temp)
                self.Config.children['listConfig'].select_by_value(appo)
                
# CONFIG - Remove the selected config file
    def config_remove(self, widget):
        appo = self.configlistselected
        if appo != "":
            temp = []
            for x in self.ConfigList:
                if x.name != appo:
                    temp.append(x)
            self.ConfigList = []
            self.ConfigList = temp
            temp = self.fill_list(self.ConfigList)
            self.Config.children['listConfig'].empty()
            self.Config.children['listConfig'].append(temp)

# CONFIG - Remove all config file
    def config_clear(self, widget):
        if self.ConfigList != []:
            self.dialog = gui.GenericDialog(title='CONFIRMATION', message='Do you want to clear the list?', width='400px', style={'border':'1px solid black', 'border-radius':'10px', 'position':'relative', 'top':'50px',})
            self.dialog.conf.style.update({'margin-right':'100px', 'width':'100px'})
            self.dialog.confirm_dialog.do(self.config_clear_confirm)
            self.dialog.show(self)
        
    def config_clear_confirm(self, widget):
        self.ConfigList = []
        self.Config.children['listConfig'].empty()
        
# SONG - Duplicate song
    def song_dup(self, widget):
        key = self.song_key(self.SongListDict)
        self.SongListDict[key] = self.SongListDict[self.songlistselected]
        self.SongList = {}
        for z in self.SongListDict:
            temp = self.SongListDict[z]
            self.SongList[int(z)] = str(temp.name)
        self.Song.children['listSong'].empty()
        self.Song.children['listSong'].append(self.SongList)
        self.Song.children['listSong'].select_by_key(key)
        self.songlistselected = key

# SONG - Move selected song up
    def song_up(self, widget):
        if self.songlistselected > 1:
            temp = self.SongListDict[self.songlistselected - 1]
            self.SongListDict[self.songlistselected - 1] = self.SongListDict[self.songlistselected]
            self.SongListDict[self.songlistselected] = temp
            self.SongList = {}
            for z in self.SongListDict:
                temp = self.SongListDict[z]
                self.SongList[int(z)] = str(temp.name)
            self.Song.children['listSong'].empty()
            self.Song.children['listSong'].append(self.SongList)
            self.songlistselected = self.songlistselected - 1
            self.Song.children['listSong'].select_by_key(self.songlistselected)

# SONG - Move selected song down
    def song_dn(self, widget):
        key = self.song_key(self.SongListDict)
        key = key - 1
        if self.songlistselected < key:
            temp = self.SongListDict[self.songlistselected + 1]
            self.SongListDict[self.songlistselected + 1] = self.SongListDict[self.songlistselected]
            self.SongListDict[self.songlistselected] = temp
            self.SongList = {}
            for z in self.SongListDict:
                temp = self.SongListDict[z]
                self.SongList[int(z)] = str(temp.name)
            self.Song.children['listSong'].empty()
            self.Song.children['listSong'].append(self.SongList)
            self.songlistselected = self.songlistselected + 1
            self.Song.children['listSong'].select_by_key(self.songlistselected)

# SONG - Delete selected song
    def song_del(self, widget):
        if self.songlistselected:
            key = self.song_key(self.SongListDict)
            key = key - 1
            if self.songlistselected != key:
                for x in range(self.songlistselected, key):
                    self.SongListDict[x] = self.SongListDict[x + 1]
            else:
                self.songlistselected = self.songlistselected - 1
            self.SongListDict.pop(key)
            if key != 1:
                self.SongList = {}
                for z in self.SongListDict:
                    temp = self.SongListDict[z]
                    self.SongList[int(z)] = str(temp.name)
                self.Song.children['listSong'].empty()
                self.Song.children['listSong'].append(self.SongList)
                self.Song.children['listSong'].select_by_key(self.songlistselected)
            else:
                self.SongList = {}
                self.Song.children['listSong'].empty()

# SONG - Delete all songs
    def song_clear(self, widget):
        if self.SongListDict != {}:
            self.dialog = gui.GenericDialog(title='CONFIRMATION', message='Do you want to clear the list?', width='400px', style={'border':'1px solid black', 'border-radius':'10px', 'position':'relative', 'top':'50px',})
            self.dialog.conf.style.update({'margin-right':'100px', 'width':'100px'})
            self.dialog.confirm_dialog.do(self.song_clear_confirm)
            self.dialog.show(self)
        
    def song_clear_confirm(self, widget):
        self.SongListDict = {}
        self.SongList = {}
        self.Song.children['listSong'].empty()

# LIST - Update or create a new list
    def list_update(self, widget):
        self.NoConfig = 0
        if len(self.SongListDict):
            #If no config defined check if default.cfg exist under LSP and use it, if it doesn't exist don't create anything
            if not len(self.ConfigList):
                if str(self.LightShowPiOverrides) != '':
                    self.Default_cfg = Path(str(self.LightShowPiOverrides.absolute())+'/defaults.cfg')
                    if self.Default_cfg.exists():
                        self.NoConfig = 1
                        msg = 'No config file uploaded, LightShowPi default.cfg will be used'
                        self.dialog = gui.GenericDialog(title='WARNING', message=msg, width='400px', style={'border':'1px solid black', 'border-radius':'10px', 'position':'relative', 'top':'50px',})
                        self.dialog.cancel.style['display'] = 'none'
                        self.dialog.conf.style.update({'margin-right':'150px', 'width':'100px'})
                        self.dialog.show(self)
                        self.List.children['listList'].empty()
                        self.ListList = {}
                        for x in self.SongListDict:
                            appo = []
                            appo.append(self.SongListDict[x])
                            exten = appo[0].suffix
    ##                        if exten != ".py" and exten != ".cfg" and self.NoConfig == 0:
    ##                            appo.append(self.ConfigList[0])
    ##                        else:
                            appo.append('none')
                            self.ListList[x] = appo
                        for x in self.ListList:
                            appo = []
                            appo = self.ListList[x]
                            appoSong = appo[0].name
                            if appo[1] == 'none':
                                appoConfig = "--> " + appo[1]
                            else:
                                appoConfig = "--> " + appo[1].name
                            temp = {}
                            temp[int(x)] = appoSong
                            self.List.children['listList'].append(temp)
                            temp = {}
                            temp[int(x+1000)] = appoConfig
                            self.List.children['listList'].append(temp)

                    else:
##                        print('No Valid Config')
                        msg = 'No config file found, impossible to create a list!'
                        self.dialog = gui.GenericDialog(title='WARNING', message=msg, width='400px', style={'border':'1px solid black', 'border-radius':'10px', 'position':'relative', 'top':'50px',})
                        self.dialog.cancel.style['display'] = 'none'
                        self.dialog.conf.style.update({'margin-right':'150px', 'width':'100px'})
                        self.dialog.show(self)
                        
                else:
##                    print('No Valid Config')
                    msg = 'No config file found, impossible to create a list!'
                    self.dialog = gui.GenericDialog(title='WARNING', message=msg, width='400px', style={'border':'1px solid black', 'border-radius':'10px', 'position':'relative', 'top':'50px',})
                    self.dialog.cancel.style['display'] = 'none'
                    self.dialog.conf.style.update({'margin-right':'150px', 'width':'100px'})
                    self.dialog.show(self)    
            #Config list exist
            else:
                self.List.children['listList'].empty()
                self.ListList = {}
                for x in self.SongListDict:
                    appo = []
                    appo.append(self.SongListDict[x])
                    exten = appo[0].suffix
                    if exten != ".py" and exten != ".cfg":
                        appo.append(self.ConfigList[0])
                    else:
                        appo.append('none')
                    self.ListList[x] = appo
                for x in self.ListList:
                    appo = []
                    appo = self.ListList[x]
                    appoSong = appo[0].name
                    if appo[1] == 'none':
                        appoConfig = "--> " + appo[1]
                    else:
                        appoConfig = "--> " + appo[1].name
                    temp = {}
                    temp[int(x)] = appoSong
                    self.List.children['listList'].append(temp)
                    temp = {}
                    temp[int(x+1000)] = appoConfig
                    self.List.children['listList'].append(temp)
      
        else:
            msg = 'No songs loaded'
            self.dialog = gui.GenericDialog(title='WARNING', message=msg, width='400px', style={'border':'1px solid black', 'border-radius':'10px', 'position':'relative', 'top':'50px',})
            self.dialog.cancel.style['display'] = 'none'
            self.dialog.conf.style.update({'margin-right':'150px', 'width':'100px'})
            self.dialog.show(self)
            self.List.children['listList'].empty()
            self.ListList = {}
            
            
# LIST - Chose the config file to assign to the selected song
    def list_config_selection(self):
        self.ListConf = gui.GenericDialog(title='CONFIG LIST', message='',width='480px', height='670px', margin='0px auto', style={'border':'1px solid black', 'border-radius':'10px'})
        lblListConf1 = gui.Label('Select the Config file for:', width='300px', style={'margin':'10px auto 0px'})
        self.ListConf.add_field('lblListConf1', lblListConf1)
        appo = self.ListList[self.listlistselected]
        appoName = MyApp.cut_name(str(appo[0].name), True, 30)
        lblListConf2 = gui.Label(appoName, width='300px', style={'margin':'0px auto 0px', 'font-weight':'bold'})
        self.ListConf.add_field('lblListConf2', lblListConf2)
        ConfList = self.fill_list(self.ConfigList)
        self.listListConf = gui.ListView.new_from_list(ConfList, width='460px', height='480px', margin='10px auto 0px')
        self.ListConf.add_field('listListConf', self.listListConf)
        
        self.ListConf.confirm_dialog.do(self.dialog_confirm_conf)
        self.ListConf.show(self)
    
    def dialog_confirm_conf(self, widget):
        result = self.ListConf.get_field('listListConf').get_value()
        for x in self.ConfigList:
            if result == x.name:
                ConfName = x
        appo = []
        appo = self.ListList[self.listlistselected]
        appo[1] = Path(ConfName)
        self.ListList[self.listlistselected] = appo
        self.List.children['listList'].empty()
        for x in self.ListList:
            appo = []
            appo = self.ListList[x]
            appoSong = appo[0].name
            if appo[1] == 'none':
                appoConfig = "--> " + appo[1]
            else:
                appoConfig = "--> " + appo[1].name
            temp = {}
            temp[int(x)] = appoSong
            self.List.children['listList'].append(temp)
            temp = {}
            temp[int(x+1000)] = appoConfig
            self.List.children['listList'].append(temp)
    
#Generates the list with songs for the Player, turn music off if it was on
    def list_generate(self, emitter):
        if len(self.ListList):
            if self.PlayON:
                self.PlayS.children['lblPlaySDesc'].set_text('MUSIC OFF')
                self.PlayS.children['widBtPlayS'].children['btPlaySLoad'].set_text('PLAY')
                os_string = 'sudo kill `pgrep -f lightshowpi`'
                self.p = threading.Thread(target=self.sys_thread, args=(os_string,), daemon=True)
                self.p.start()               
##                clean_sys = Path(str(self.LightShowPiPy.absolute())+'/py/hardware_controller.py --state=cleanup')
##                self.q = threading.Thread(target=self.sys_thread, args=(clean_sys.absolute(),), daemon=True)
##                self.q.start()               
                self.PlayON = False
            self.PlayList = copy.deepcopy(self.ListList)
            msg = 'Play list generated'
            self.dialog = gui.GenericDialog(title='PLAY LIST', message=msg, width='400px', style={'border':'1px solid black', 'border-radius':'10px', 'position':'relative', 'top':'50px',})
            self.dialog.cancel.style['display'] = 'none'
            self.dialog.conf.style.update({'margin-right':'150px', 'width':'100px'})
            self.dialog.show(self)


# PLAYS - Play songs from list
    def playS_dialog(self, emitter):
        if len(self.PlayList):
            self.PlayNumMax = len(self.PlayList)
            if not self.PlayON:
                self.PlayON = True
                self.PlayNum = 1
                self.playSong(self.PlayNum)
            else:
                self.PlayS.children['lblPlaySDesc'].set_text('MUSIC OFF')
                self.PlayS.children['widBtPlayS'].children['btPlaySLoad'].set_text('PLAY')
                os_string = 'sudo kill `pgrep -f lightshowpi`'
                self.p = threading.Thread(target=self.sys_thread, args=(os_string,), daemon=True)
                self.p.start()
                self.PlayON = False
                
    def sys_thread(self, args):
        os.system(args)
##        os.system('sudo python /home/pi/lightshowpi/py/synchronized_lights.py --file=/home/pi/lightshowpi/music/sample/l3.wav')


#PLAY function
    def playSong(self, numsong):
        appo = []
        appo = self.PlayList[numsong]
        apname = MyApp.cut_name(appo[0].name, True, 30)
        appoSong = 'Playing: {}'.format(apname)
        self.PlayS.children['lblPlaySDesc'].set_text(appoSong)
        self.PlayS.children['widBtPlayS'].children['btPlaySLoad'].set_text('STOP')
        overr = Path(str(self.LightShowPiOverrides.absolute())+'/overrides.cfg')
        cp2 = overr.absolute()
##         if appo[0].suffix == '.py' or appo[0].suffix == '.cfg':
        if appo[0].suffix == '.cfg':
            cp1 = appo[0].absolute()
            try:
                shutil.copyfile(cp1, cp2)
            except:
                msg = 'Problem to create overrides file! Check the writing permission in Config folder.'
                self.dialog = gui.GenericDialog(title='ERROR', message=msg, width='400px', style={'border':'1px solid black', 'border-radius':'10px', 'position':'relative', 'top':'50px',})
                self.dialog.cancel.style['display'] = 'none'
                self.dialog.conf.style.update({'margin-right':'150px', 'width':'100px'})
                self.dialog.show(self)
            pre_show = Path(str(self.LightShowPiPy.absolute())+'/prepostshow.py')
            os_string = 'sudo python {} "preshow"'.format(pre_show.absolute())
        else:
            if self.NoConfig:
                cp1 = self.Default_cfg.absolute()
            else:
                cp1 = appo[1].absolute()
            try:
                shutil.copyfile(cp1, cp2)
            except:
                msg = 'Problem to create overrides file! Check the writing permission in Config folder.'
                self.dialog = gui.GenericDialog(title='ERROR', message=msg, width='400px', style={'border':'1px solid black', 'border-radius':'10px', 'position':'relative', 'top':'50px',})
                self.dialog.cancel.style['display'] = 'none'
                self.dialog.conf.style.update({'margin-right':'150px', 'width':'100px'})
                self.dialog.show(self)
            syn_lig = Path(str(self.LightShowPiPy.absolute())+'/synchronized_lights.py')
#             print(syn_lig)
#             print(cp1)
#             os_string = 'sudo python {} --config={} --file={}'.format(syn_lig.absolute(), cp1, appo[0].absolute())
            os_string = 'sudo python {} --file={}'.format(syn_lig.absolute(), appo[0].absolute())
#         print(os_string)
        self.t = threading.Thread(target=self.sys_thread, args=(os_string,), daemon=True)
        self.t.start()

#PLAY NEXT function
    def playSnext_dialog(self, widget):
        if self.t.is_alive():
            if self.PlayRandom == 0:
                if self.PlayNumMax > 1:
                    if self.PlayLoop == 0 and self.PlayNum >= self.PlayNumMax:
                        pass
                    else:
                        if self.PlayNum < self.PlayNumMax:
                            self.PlayNum = self.PlayNum + 1    
                        else:
                            self.PlayNum = 1
                        os_string = 'sudo kill `pgrep -f lightshowpi`'
                        self.p = threading.Thread(target=self.sys_thread, args=(os_string,), daemon=True)
                        self.p.start()
                        time.sleep(0.2)
                        self.playSong(self.PlayNum)
            else:
                self.PlayNum = randint(1, self.PlayNumMax)
                os_string = 'sudo kill `pgrep -f lightshowpi`'
                self.p = threading.Thread(target=self.sys_thread, args=(os_string,), daemon=True)
                self.p.start()
                time.sleep(0.2)
                self.playSong(self.PlayNum)
                    
                     
#PLAY PREV function
    def playSprev_dialog(self, widget):
        if self.t.is_alive():
            if self.PlayRandom == 0:
                if self.PlayNumMax > 1:
                    if self.PlayNum > 1:
                        self.PlayNum = self.PlayNum - 1  
                        os_string = 'sudo kill `pgrep -f lightshowpi`'
                        self.p = threading.Thread(target=self.sys_thread, args=(os_string,), daemon=True)
                        self.p.start()
                        time.sleep(0.2)
                        self.playSong(self.PlayNum)
            else:
                self.PlayNum = randint(1, self.PlayNumMax)
                os_string = 'sudo kill `pgrep -f lightshowpi`'
                self.p = threading.Thread(target=self.sys_thread, args=(os_string,), daemon=True)
                self.p.start()
                time.sleep(0.2)
                self.playSong(self.PlayNum)
            

#PLAY SELECTED function
    def playSelect_dialog(self, widget):
        if self.PlayNumSelected != '':
            if not self.PlayON:
                self.PlayON = True
                self.PlayNumMax = len(self.PlayList)
            else: 
                if self.t.is_alive():
                    os_string = 'sudo kill `pgrep -f lightshowpi`'
                    self.p = threading.Thread(target=self.sys_thread, args=(os_string,), daemon=True)
                    self.p.start()
                    time.sleep(0.2)   
            self.PlayNum = self.PlayNumSelected
            self.playSong(self.PlayNum)
        

#PLAY LOOP function
    def playSloop_dialog(self, widget):
        if self.PlayLoop == 0:
            self.PlayLoop = 1
            self.PlayS.children['widBtPlayS2'].children['btPlaySLoop'].set_text('Loop ON')
        else:
            self.PlayLoop = 0
            self.PlayS.children['widBtPlayS2'].children['btPlaySLoop'].set_text('Loop OFF')


#PLAY RANDOM function
    def playSrand_dialog(self, widget):
        if self.PlayRandom == 0:
            self.PlayRandom = 1
            self.PlayS.children['widBtPlayS2'].children['btPlaySRand'].set_text('Random ON')
        else:
            self.PlayRandom = 0
            self.PlayS.children['widBtPlayS2'].children['btPlaySRand'].set_text('Random OFF')

#PLAY VOLUME ON-OFF
    def playS_volumeOn(self, widget):
        if self.VolumeOn == 1:
            self.VolumeOn = 0
            self.Volume = 0
            self.PlayS.children['widBtPlayS2'].children['btPlaySVolumeOn'].set_text('Vol OFF')
#             vol = str(self.LightShowPiFolder.absolute()) + '/bin/vol ' + str(self.Volume)
            vol = "amixer sset " + self.AlsaDevice + " " + str(self.Volume) + "%"
            os.system(vol)  
        else:
            self.VolumeOn = 1
            self.Volume = self.VolumeDef
            volnum = 'Vol ' + str(self.Volume) + ('%')
            self.PlayS.children['widBtPlayS2'].children['btPlaySVolumeOn'].set_text(volnum)
#             vol = str(self.LightShowPiFolder.absolute()) + '/bin/vol ' + str(self.Volume)
            vol = "amixer sset " + self.AlsaDevice + " " + str(self.Volume) + "%"
            os.system(vol)

#PLAY VOLUME +
    def playS_volumeP(self, widget):
        if self.VolumeOn == 1:
            self.Volume = self.Volume + 3
            if self.Volume > 100:
                self.Volume = 100
            volnum = 'Vol ' + str(self.Volume) + ('%')
            self.PlayS.children['widBtPlayS2'].children['btPlaySVolumeOn'].set_text(volnum)
#             vol = str(self.LightShowPiFolder.absolute()) + '/bin/vol ' + str(self.Volume)
            vol = "amixer sset " + self.AlsaDevice + " " + str(self.Volume) + "%"
            os.system(vol)
   
#PLAY VOLUME -
    def playS_volumeM(self, widget):
        if self.VolumeOn == 1:
            self.Volume = self.Volume - 3
            if self.Volume < 0:
                self.Volume = 0
                self.VolumeOn = 0
                self.PlayS.children['widBtPlayS2'].children['btPlaySVolumeOn'].set_text('Vol OFF')
#                 vol = str(self.LightShowPiFolder.absolute()) + '/bin/vol ' + str(self.Volume)
                vol = "amixer sset " + self.AlsaDevice + " " + str(self.Volume) + "%"
            else:
                volnum = 'Vol ' + str(self.Volume) + ('%')
                self.PlayS.children['widBtPlayS2'].children['btPlaySVolumeOn'].set_text(volnum)
#                 vol = str(self.LightShowPiFolder.absolute()) + '/bin/vol ' + str(self.Volume)
                vol = "amixer sset " + self.AlsaDevice + " " + str(self.Volume) + "%"
            os.system(vol)
    
# PLAYS - update songs list in play window
    def play_list_update(self):
        self.PlayS.children['listPlayS'].empty()
        if len(self.PlayList):
            for x in self.PlayList:
                appo = []
                appo = self.PlayList[x]
                appoSong = appo[0].name
                temp = {}
                temp[int(x)] = appoSong
                self.PlayS.children['listPlayS'].append(temp)


# SCHEDULER Add a new Schedule
    def add_sched(self, widget):
        if self.SchedOn:
            self.logo_sched.set_image('/res:sched_off.png')
            self.btSchedActive.set_text('Turn ON')
            self.SchedOn = False
        self.SchedFileName = ''
        self.dialog = gui.GenericDialog(title='Add scheduled time', width='480px')
        self.dialog.style.update({'border':'1px solid black', 'border-radius':'10px'})
        self.dtextlabel = gui.Label('Time format 00:00-24:00', width='480px', height='30px', style={'font-style':'italic', 'text-align':'center'})
        self.dialog.add_field('dtextlabel', self.dtextlabel)
        self.dtimestart = gui.TextInput(width=200, height=30)
        self.dtimestart.style.update({'line-height':'30px', 'text-align':'center'})
        self.dtimestart.set_value('00:00')
        self.dtimestart.onchange.do(self.checktime, 'start')
        self.dialog.add_field_with_label('dtimestart', 'Start time:', self.dtimestart)
        self.dtimestop = gui.TextInput(width=200, height=30)
        self.dtimestop.style.update({'line-height':'30px', 'text-align':'center'})
        self.dtimestop.set_value('00:00')
        self.dtimestop.onchange.do(self.checktime, 'stop')
        self.dialog.add_field_with_label('dtimestop', 'Stop time:', self.dtimestop)
        self.dcheckmonday = gui.CheckBox(False, width=200, height=30)
        self.dialog.add_field_with_label('dcheckmonday', 'Monday:', self.dcheckmonday)
        self.dchecktuesday = gui.CheckBox(False, width=200, height=30)
        self.dialog.add_field_with_label('dchecktuesday', 'Tuesday:', self.dchecktuesday)
        self.dcheckwednesday = gui.CheckBox(False, width=200, height=30)
        self.dialog.add_field_with_label('dcheckwednesday', 'Wednesday:', self.dcheckwednesday)
        self.dcheckthursday = gui.CheckBox(False, width=200, height=30)
        self.dialog.add_field_with_label('dcheckthursday', 'Thursday:', self.dcheckthursday)
        self.dcheckfriday = gui.CheckBox(False, width=200, height=30)
        self.dialog.add_field_with_label('dcheckfriday', 'Friday:', self.dcheckfriday)
        self.dchecksaturday = gui.CheckBox(False, width=200, height=30)
        self.dialog.add_field_with_label('dchecksaturday', 'Saturday:', self.dchecksaturday)
        self.dchecksunday = gui.CheckBox(False, width=200, height=30)
        self.dialog.add_field_with_label('dchecksunday', 'Sunday:', self.dchecksunday)
        self.dcheckrandom = gui.CheckBox(False, width=200, height=30)
        self.dialog.add_field_with_label('dcheckrandom', 'Random active:', self.dcheckrandom)
        self.dcheckloop = gui.CheckBox(False, width=200, height=30)
        self.dialog.add_field_with_label('dcheckloop', 'Loop active:', self.dcheckloop)
        self.dvolume = gui.TextInput(width=200, height=30)
        self.dvolume.style.update({'line-height':'30px', 'text-align':'center'})
        self.dvolume.set_value('80')
        self.dvolume.onchange.do(self.checkvolume)
        self.dialog.add_field_with_label('dvolume', 'Volume 0-100:', self.dvolume)
        self.awidFolderShow = gui.Container(width='460px', height='30px', layout_orientation=gui.Container.LAYOUT_HORIZONTAL, margin='10px auto')
        self.awidFolderShow.style.update({'display':'inline'})
        self.aFolderShow = gui.Label('Select show file', width='280px', height='30px', margin='0px 0px 0px 10px', style={'padding-left':'5px', 'font-size':'14px', 'text-align':'left', 'line-height':'2', 'border':'1px solid silver', 'border-radius':'5px'})
        self.abtFolderShow = gui.Button("Select", width='80px', height='30px', style={'position':'relative', 'top':'0px',  'right':'-25px', 'display':'inline'})
        self.abtFolderShow.onclick.do(self.open_fileselection_dialog, 'Select Show file', False, True, False, 'Scheduler')
        self.awidFolderShow.append(self.aFolderShow, 'aFolderShow')
        self.awidFolderShow.append(self.abtFolderShow)
        self.dialog.add_field('aapp', self.awidFolderShow)
        self.dialog.confirm_dialog.do(self.dialog_confirm, False)
        self.dialog.show(self)

    #SCHEDULER - Edit an existing Schedule
    def edit_sched(self, widget):
        if self.SchedOn:
            self.logo_sched.set_image('/res:sched_off.png')
            self.btSchedActive.set_text('Turn ON')
            self.SchedOn = False
        appo = self.schedulerlistselected
        if appo != '':
            temp = self.SchedList[appo]
            self.dialog = gui.GenericDialog(title='Add scheduled time', width='480px')
            self.dialog.style.update({'border':'1px solid black', 'border-radius':'10px'})
            self.dtextlabel = gui.Label('Time format 00:00-24:00', width='480px', height='30px', style={'font-style':'italic', 'text-align':'center'})
            self.dialog.add_field('dtextlabel', self.dtextlabel)
            self.dtimestart = gui.TextInput(width=200, height=30)
            self.dtimestart.style.update({'line-height':'30px', 'text-align':'center'})
            self.dtimestart.set_value(temp[0])
            self.dtimestart.onchange.do(self.checktime, 'start')
            self.dialog.add_field_with_label('dtimestart', 'Start time:', self.dtimestart)
            self.dtimestop = gui.TextInput(width=200, height=30)
            self.dtimestop.style.update({'line-height':'30px', 'text-align':'center'})
            self.dtimestop.set_value(temp[1])
            self.dtimestop.onchange.do(self.checktime, 'stop')
            self.dialog.add_field_with_label('dtimestop', 'Stop time:', self.dtimestop)
            self.dcheckmonday = gui.CheckBox(temp[2], width=200, height=30)
            self.dialog.add_field_with_label('dcheckmonday', 'Monday:', self.dcheckmonday)
            self.dchecktuesday = gui.CheckBox(temp[3], width=200, height=30)
            self.dialog.add_field_with_label('dchecktuesday', 'Tuesday:', self.dchecktuesday)
            self.dcheckwednesday = gui.CheckBox(temp[4], width=200, height=30)
            self.dialog.add_field_with_label('dcheckwednesday', 'Wednesday:', self.dcheckwednesday)
            self.dcheckthursday = gui.CheckBox(temp[5], width=200, height=30)
            self.dialog.add_field_with_label('dcheckthursday', 'Thursday:', self.dcheckthursday)
            self.dcheckfriday = gui.CheckBox(temp[6], width=200, height=30)
            self.dialog.add_field_with_label('dcheckfriday', 'Friday:', self.dcheckfriday)
            self.dchecksaturday = gui.CheckBox(temp[7], width=200, height=30)
            self.dialog.add_field_with_label('dchecksaturday', 'Saturday:', self.dchecksaturday)
            self.dchecksunday = gui.CheckBox(temp[8], width=200, height=30)
            self.dialog.add_field_with_label('dchecksunday', 'Sunday:', self.dchecksunday)
            self.dcheckrandom = gui.CheckBox(temp[9], width=200, height=30)
            self.dialog.add_field_with_label('dcheckrandom', 'Random active:', self.dcheckrandom)
            self.dcheckloop = gui.CheckBox(temp[10], width=200, height=30)
            self.dialog.add_field_with_label('dcheckloop', 'Loop active:', self.dcheckloop)
            self.dvolume = gui.TextInput(width=200, height=30)
            self.dvolume.style.update({'line-height':'30px', 'text-align':'center'})
            self.dvolume.set_value(temp[11])
            self.dvolume.onchange.do(self.checkvolume)
            self.dialog.add_field_with_label('dvolume', 'Volume 0-100:', self.dvolume)
            self.awidFolderShow = gui.Container(width='460px', height='30px', layout_orientation=gui.Container.LAYOUT_HORIZONTAL, margin='10px auto')
            self.awidFolderShow.style.update({'display':'inline'})
            self.SchedFileName = temp[12]
            appoName = MyApp.cut_name(temp[12], False, 30)
            self.aFolderShow = gui.Label(appoName, width='280px', height='30px', margin='0px 0px 0px 10px', style={'padding-left':'5px', 'font-size':'14px', 'text-align':'left', 'line-height':'2', 'border':'1px solid silver', 'border-radius':'5px'})
            self.abtFolderShow = gui.Button("Select", width='80px', height='30px', style={'position':'relative', 'top':'0px',  'right':'-25px', 'display':'inline'})
            self.abtFolderShow.onclick.do(self.open_fileselection_dialog, 'Select Show file', False, True, False, 'Scheduler')
            self.awidFolderShow.append(self.aFolderShow, 'aFolderShow')
            self.awidFolderShow.append(self.abtFolderShow)
            self.dialog.add_field('aapp', self.awidFolderShow)
            self.dialog.confirm_dialog.do(self.dialog_confirm, True)
            self.dialog.show(self)

    #SCHEDULER - Used to create a correct input time and check if the input make sense as time
    def checktime(self, widget, timeIn, st):
        try:
            if timeIn != '24:00' and timeIn != '23:59':
                timeIn = datetime.datetime.strptime(timeIn, "%H:%M").time()
                #Convert the time in format 00:00 (2:4 -> 02:04)
                timeIn = str(timeIn)
                timeSplit = timeIn.split(':')
                timeNew = timeSplit[0] + ':' + timeSplit[1]
                if st == 'start':
                    self.dtimestart.set_text(timeNew)
                else:
                    self.dtimestop.set_text(timeNew)
                timeIn = datetime.datetime.strptime(timeNew, "%H:%M")
        except:
            if st == 'start':
                testo = 'Wrong START TIME format!'
                self.dtimestart.set_text('00:00')
            else:
                testo = 'Wrong STOP TIME format!'
                testo1 = self.dtimestart.get_text()
                if testo1 == '00:00':
                    self.dtimestop.set_text('00:00')
                else:
                    if testo1 == '23:59':
                        self.dtimestop.set_text('24:00')
                    else:
                        timeIn = datetime.datetime.strptime(testo1, "%H:%M")
                        timeIn = timeIn + datetime.timedelta(minutes = 1)
                        timeIn = timeIn.time()
                        timeIn = str(timeIn)
                        timeIn = timeIn[:-3]
                        self.dtimestop.set_text(timeIn)
            self.error_message(testo)
        else:
            if timeIn != '24:00':
                if timeIn != '23:59':
                    timeStop = self.dtimestop.get_text()
                    timeStop = datetime.datetime.strptime(timeStop, "%H:%M")
                    if st == 'start' and timeStop <= timeIn:
                        timeIn = timeIn + datetime.timedelta(minutes = 1)
                        timeIn = timeIn.time()
                        timeIn = str(timeIn)
                        timeIn = timeIn[:-3]
                        self.dtimestop.set_text(timeIn)
                    if st == 'stop':
                        timeStart = self.dtimestart.get_text()
                        timeStart = datetime.datetime.strptime(timeStart, "%H:%M")
                        if timeStart >= timeIn:
                            testo = 'STOP TIME cannot be less than START TIME'
                            self.error_message(testo)
                            if self.dtimestart.get_text() == '23:59':
                                self.dtimestop.set_text('24:00')
                            else:
                                timeStart = timeStart + datetime.timedelta(minutes = 1)
                                timeStart = timeStart.time()
                                timeStart = str(timeStart)
                                timeStart = timeStart[:-3]
                                self.dtimestop.set_text(timeStart)
                else:
                    if st == 'start':
                        self.dtimestop.set_text('24:00')
                    elif st == 'stop':
                        timeStart = self.dtimestart.get_text()
                        if timeStart == '23:59':
                            self.dtimestop.set_text('24:00')
            else:
                if st == 'start':
                    testo = 'START TIME cannot be 24:00'
                    self.error_message(testo)
                    self.dtimestart.set_text('00:00')
    
    #SCHEDULER - Used to check volume number
    def checkvolume(self, widget, vol):
        try:
            vol = int(vol)
            if vol < 0 or vol > 100:
                self.dvolume.set_text('80')
        except:
            self.dvolume.set_text('80')
    
    #Used to show pop-up window messages
    def error_message(self, testo):
        dialog1 = gui.GenericDialog(title='ERROR', message=testo, width='400px', style={'border':'1px solid black', 'border-radius':'10px', 'position':'relative', 'top':'50px',})
        dialog1.cancel.style['display'] = 'none'
        dialog1.conf.style.update({'margin-right':'150px', 'width':'100px'})
        dialog1.show(self)
    
    #SCHEDULER - Check what was edited during Add or Edit function
    #edit param = True if called by "Edit" button and False if called by "Add" button
    def dialog_confirm(self, widget, edit):
        appo = []
        resStart = self.dtimestart.get_text()
        resStop = self.dtimestop.get_text()
        resMonday = self.dcheckmonday.get_value()
        resTuesday = self.dchecktuesday.get_value()
        resWednesday = self.dcheckwednesday.get_value()
        resThursday = self.dcheckthursday.get_value()
        resFriday = self.dcheckfriday.get_value()
        resSaturday = self.dchecksaturday.get_value()
        resSunday = self.dchecksunday.get_value()
        resRandom = self.dcheckrandom.get_value()
        resLoop = self.dcheckloop.get_value()
        resVol = self.dvolume.get_value()
        resFile = self.SchedFileName
        if not resMonday and not resTuesday and not resWednesday and not resThursday and not resFriday and not resSaturday and not resSunday:
            resMonday = True
            resTuesday = True
            resWednesday = True
            resThursday = True
            resFriday = True
            resSaturday = True
            resSunday = True
        if edit:
            self.scheduler_del(self)
        if resStart != resStop and resFile != '':
            appo.append(resStart)
            appo.append(resStop)
            appo.append(resMonday)
            appo.append(resTuesday)
            appo.append(resWednesday)
            appo.append(resThursday)
            appo.append(resFriday)
            appo.append(resSaturday)
            appo.append(resSunday)
            appo.append(resRandom)
            appo.append(resLoop)
            appo.append(resVol)
            appo.append(resFile)
            if len(self.SchedList):
                found = 0
                for x in self.SchedList:
                    w = self.SchedList[x]
                    appoCheck = datetime.datetime.strptime(appo[0], "%H:%M")
                    tempCheck = datetime.datetime.strptime(w[0], "%H:%M")
                    if appoCheck < tempCheck:
                        temp = self.SchedList.copy()
                        self.SchedList[x] = appo
                        k = x
                        q = len(self.SchedList)
                        while k < q + 1:
                            self.SchedList[k+1] = temp[k]
                            k = k + 1
                        found = 1
                        break
                if not found:
                    key = self.song_key(self.SchedList)
                    self.SchedList[key] = appo
            else:
                key = self.song_key(self.SchedList)
                self.SchedList[key] = appo
            self.drawschedulerlist(self.SchedList)
        if edit:
            if resStart == resStop:
                testo = 'START TIME cannot be equal to STOP TIME. No schedule modified.'
                self.error_message(testo)
            elif resFile == '':
                testo = 'Show file not selected. No schedule modified.'
                self.error_message(testo)
        else:
            if resStart == resStop:
                testo = 'START TIME cannot be equal to STOP TIME. No schedule created.'
                self.error_message(testo)
            elif resFile == '':
                testo = 'Show file not selected. No schedule created.'
                self.error_message(testo)
        self.schedulerlistselected = ''
#         print(self.SchedList)
    
    #SCHEDULER - Delete the selected Schedule
    def scheduler_del(self, widget):
        if self.SchedOn:
            self.logo_sched.set_image('/res:sched_off.png')
            self.btSchedActive.set_text('Turn ON')
            self.SchedOn = False
        appo = self.schedulerlistselected
        if appo != '':
            if appo == len(self.SchedList):
                del self.SchedList[appo]
            else:
                for x in self.SchedList:
                    if x == appo:
                        temp = self.SchedList.copy()
                        k = x
                        q = len(self.SchedList)
                        while k < q:
                            self.SchedList[k] = temp[k+1]
                            k = k + 1
                        del self.SchedList[q]
                        break
            self.listSched.empty()
            self.drawschedulerlist(self.SchedList)
            
    #SCHEDULER - Used to generate and fill the Scheduler list        
    def drawschedulerlist(self, lista):
        self.listSched.empty()
        line = ''
        inser_line = {}
        for x in lista:
            y = lista[x]
            line = y[0] + '/' + y[1] + ' | '
            if y[2]:
                line = line + 'M'
            else:
                line = line + 'm'
            if y[3]:
                line = line + 'T'
            else:
                line = line + 't'
            if y[4]:
                line = line + 'W'
            else:
                line = line + 'w'
            if y[5]:
                line = line + 'T'
            else:
                line = line + 't'
            if y[6]:
                line = line + 'F'
            else:
                line = line + 'f'
            if y[7]:
                line = line + 'S'
            else:
                line = line + 's'
            if y[8]:
                line = line + 'S |'
            else:
                line = line + 's |'
            if y[9]:
                line = line + 'R | '
            else:
                line = line + '_ | '
            if y[10]:
                line = line + 'L | '
            else:
                line = line + '_ | '
            if y[11] == '100':
                line = line + 'V.' + y[11] + ' | '
            else:
                line = line + 'V. ' + y[11] + ' | '
            w = Path(y[12])
            FileName = w.name
            line = line + FileName
            inser_line[x] = line
            self.listSched.append(inser_line)
        
    # SCHEDULER - Delete all times
    def sched_clear(self, widget):
        if self.SchedOn:
            self.logo_sched.set_image('/res:sched_off.png')
            self.btSchedActive.set_text('Turn ON')
            self.SchedOn = False
        if self.SchedList != {}:
            self.dialog = gui.GenericDialog(title='CONFIRMATION', message='Do you want to clear the list?', width='400px', style={'border':'1px solid black', 'border-radius':'10px', 'position':'relative', 'top':'50px',})
            self.dialog.conf.style.update({'margin-right':'100px', 'width':'100px'})
            self.dialog.confirm_dialog.do(self.sched_clear_confirm)
            self.dialog.show(self)
    
    #SCHEDULER - confirm before delete al Scheduled time
    def sched_clear_confirm(self, widget):
        self.SchedList = {}
        self.listSched.empty()
    
    #SCHEDULER - check if the Scheduler is activated, then update the list for the day
    def sched_active(self, widget):
        if self.SchedOn:
            self.logo_sched.set_image('/res:sched_off.png')
            self.btSchedActive.set_text('Turn ON')
            self.SchedOn = False
            self.stop_sched_music()
        else:
            self.logo_sched.set_image('/res:sched_on.png')
            self.btSchedActive.set_text('Turn OFF')
            self.SchedOn = True
            self.update_today_list()


    #SCHEDULER - Updates the list with the scheduler for today
    def update_today_list(self):
        self.TimeRange[0] = '00:00'
        self.TimeRange[1] = '00:00'
        DayTodayAppo = datetime.datetime.today().weekday()
        self.DaySched = DayTodayAppo + 1
        DayTodayAppo += 2    #To match position day in Sched list
        y = 1
        self.SchedToday = {}
        if len(self.SchedList):
            for x in self.SchedList:
                w = self.SchedList[x]
                if w[DayTodayAppo]:
                   #AppoSched = 0 Time ON - 1 Time OFF - 2 Random - 3 Loop - 4 Volume - 5 File
                    AppoSched = []
                    AppoSched.append(w[0])
                    AppoSched.append(w[1])
                    AppoSched.append(w[9])
                    AppoSched.append(w[10])
                    AppoSched.append(w[11])
                    AppoSched.append(w[12])
                    self.SchedToday[y] = AppoSched
                    y += 1
##        print(self.SchedToday)

    #SCHEDULER - stop Scheduler music
    def stop_sched_music(self):
        if self.PlayON:
            self.PlayS.children['lblPlaySDesc'].set_text('MUSIC OFF')
            self.PlayS.children['widBtPlayS'].children['btPlaySLoad'].set_text('PLAY')
            os_string = 'sudo kill `pgrep -f lightshowpi`'
            self.p = threading.Thread(target=self.sys_thread, args=(os_string,), daemon=True)
            self.p.start()
            self.PlayON = False
    
    #SCHEDULER - start Scheduler music
    def start_sched_music(self):
        #Load MUSIC
        #------------------------------------------------------------------------------------
        y = Path(self.SchedNow[5])
        y = y.absolute()
        with open(y, 'r') as file:
            Data = file.read()
        Data = Data.split('\n')
        if Data[0] == '[SHOW MANAGER]':
            del Data[0]
        #Check if songs and config exists
            SongExist = []
            ConfExist = []
            for x in Data:
                if x != '':
                    Name, Conf = x.split('\t')
                    NameApp = Path(Name)
                    if NameApp.exists():
                        SongExist.append(Name)
                    if Conf != 'none':
                        ConfApp = Path(Conf)
                        if ConfApp.exists():
                            ConfExist.append(Conf)
            #If there are no songs nothing is loaded
            if len(SongExist):
            #Check if exist songs and configs or only songs
                if len(ConfExist):
##                  print('Song and conf exist')
                    self.SongListDict = {}
                    self.ListList = {}
                    self.ConfigList = []
                    found_all_song = 1
                    found_all_config = 1
                    for y in Data:
                        if y != '':
                            Name, Conf = y.split('\t')
                            Name = Path(Name)
                            if Name.exists():
                                if Name.suffix in self.file_types_all:
                                    key = self.song_key(self.SongListDict)
                                    self.SongListDict[key] = Name
                            else:
                                found_all_song = 0
                            if Conf != 'none':
                                Conf = Path(Conf)
                                if Conf.exists():
                                    found = 0
                                    for x in self.ConfigList:
                                        if Conf.name == x.name:
                                            found = 1
                                    if not found:
                                        self.ConfigList.append(Conf)
                                else:
                                    found_all_config = 0
                            if Name.exists():
                                if Conf != 'none':
                                    Conf = Path(Conf)
                                    if Conf.exists():
                                        appo = []
                                        appo.append(Name)
                                        appo.append(Conf)
                                        self.ListList[key] = appo
                                    else:
                                        appo = []
                                        appo.append(Name)
                                        appo.append('none')
                                        self.ListList[key] = appo
                                else:
                                    appo = []
                                    appo.append(Name)
                                    appo.append('none')
                                    self.ListList[key] = appo        
                    #Update songs list            
                    self.SongList = {}
                    for z in self.SongListDict:
                        temp = self.SongListDict[z]
                        self.SongList[int(z)] = str(temp.name)
                    self.Song.children['listSong'].empty()
                    self.Song.children['listSong'].append(self.SongList)
                    #Update configs list 
                    appo = []
                    appo = self.fill_list(self.ConfigList)
                    self.Config.children['listConfig'].empty()
                    self.Config.children['listConfig'].append(appo)
                    #Update music + config list
                    self.List.children['listList'].empty()
                    for x in self.ListList:
                        appo = []
                        appo = self.ListList[x]
                        appoSong = appo[0].name
                        if appo[1] == 'none':
                            appoConfig = "--> " + appo[1]
                        else:
                            appoConfig = "--> " + appo[1].name
                        temp = {}
                        temp[int(x)] = appoSong
                        self.List.children['listList'].append(temp)
                        temp = {}
                        temp[int(x+1000)] = appoConfig
                        self.List.children['listList'].append(temp)
                    if found_all_song == 1 and found_all_config == 1:
                        pass
                    else:
                        if found_all_song == 1 and found_all_config == 0:
##                            msg = 'Impossible load all config files, LightShowPi default.cfg will be used'
                            print('Impossible load all config files, LightShowPi default.cfg will be used')
                        elif found_all_song == 0 and found_all_config == 1:
##                            msg = 'Impossible load some songs!'
                            print('Impossible load some songs!')
                        else:
##                            msg = 'Impossible load all config files, LightShowPi default.cfg will be used. Impossible load some songs!'
                            print('Impossible load all config files, LightShowPi default.cfg will be used. Impossible load some songs!')
##                        self.dialog = gui.GenericDialog(title='WARNING', message=msg, width='400px', style={'border':'1px solid black', 'border-radius':'10px', 'position':'relative', 'top':'50px',})
##                        self.dialog.cancel.style['display'] = 'none'
##                        self.dialog.conf.style.update({'margin-right':'150px', 'width':'100px'})
##                        self.dialog.show(self)
                else:
##                  print('Only songs exist')
                    self.SongListDict = {}
                    self.ListList = {}
                    found_all = 1
                    for y in Data:
                        if y != '':
                            Name, Conf = y.split('\t')
                            Name = Path(Name)
                            if Name.exists():
                                if Name.suffix in self.file_types_all:
                                    key = self.song_key(self.SongListDict)
                                    self.SongListDict[key] = Name
                                else:
                                    found_all = 0         
                    #Update songs list
                    self.SongList = {}
                    for z in self.SongListDict:
                        temp = self.SongListDict[z]
                        self.SongList[int(z)] = str(temp.name)
                    self.Song.children['listSong'].empty()
                    self.Song.children['listSong'].append(self.SongList)
                    #Update music + config list
                    if str(self.LightShowPiOverrides) != '':
                        self.Default_cfg = Path(str(self.LightShowPiOverrides.absolute())+'/defaults.cfg')
                        if self.Default_cfg.exists():
                            self.NoConfig = 1
                            if found_all == 1:
##                                msg = 'No config file uploaded, LightShowPi default.cfg will be used'
                                print('No config file uploaded, LightShowPi default.cfg will be used')
                            else:
##                                msg = 'No config file uploaded, LightShowPi default.cfg will be used. Impossible load some songs!'
                                print('No config file uploaded, LightShowPi default.cfg will be used. Impossible load some songs!')
##                            self.dialog = gui.GenericDialog(title='WARNING', message=msg, width='400px', style={'border':'1px solid black', 'border-radius':'10px', 'position':'relative', 'top':'50px',})
##                            self.dialog.cancel.style['display'] = 'none'
##                            self.dialog.conf.style.update({'margin-right':'150px', 'width':'100px'})
##                            self.dialog.show(self)
                            self.List.children['listList'].empty()
                            self.ListList = {}
                            for x in self.SongListDict:
                                appo = []
                                appo.append(self.SongListDict[x])
                                exten = appo[0].suffix
                                appo.append('none')
                                self.ListList[x] = appo
                            for x in self.ListList:
                                appo = []
                                appo = self.ListList[x]
                                appoSong = appo[0].name
                                if appo[1] == 'none':
                                    appoConfig = "--> " + appo[1]
                                else:
                                    appoConfig = "--> " + appo[1].name
                                temp = {}
                                temp[int(x)] = appoSong
                                self.List.children['listList'].append(temp)
                                temp = {}
                                temp[int(x+1000)] = appoConfig
                                self.List.children['listList'].append(temp)
                        else:
                            msg = 'No config file found, impossible to run music!'
                            self.dialog = gui.GenericDialog(title='WARNING', message=msg, width='400px', style={'border':'1px solid black', 'border-radius':'10px', 'position':'relative', 'top':'50px',})
                            self.dialog.cancel.style['display'] = 'none'
                            self.dialog.conf.style.update({'margin-right':'150px', 'width':'100px'})
                            self.dialog.show(self)           
                    else:
                        msg = 'No config file found, impossible to run music!'
                        self.dialog = gui.GenericDialog(title='WARNING', message=msg, width='400px', style={'border':'1px solid black', 'border-radius':'10px', 'position':'relative', 'top':'50px',})
                        self.dialog.cancel.style['display'] = 'none'
                        self.dialog.conf.style.update({'margin-right':'150px', 'width':'100px'})
                        self.dialog.show(self)        
            else:
                dialog = gui.GenericDialog(title='ERROR', message='No valid song paths found, impossible to run music!!', width='400px', style={'border':'1px solid black', 'border-radius':'10px', 'position':'relative', 'top':'50px',})
                dialog.cancel.style['display'] = 'none'
                dialog.conf.style.update({'margin-right':'150px', 'width':'100px'})
                dialog.show(self)
        else:
            dialog = gui.GenericDialog(title='ERROR', message='No show file! Impossible to run music!', width='400px', style={'border':'1px solid black', 'border-radius':'10px', 'position':'relative', 'top':'50px',})
            dialog.cancel.style['display'] = 'none'
            dialog.conf.style.update({'margin-right':'150px', 'width':'100px'})
            dialog.show(self)
        
        #------------------------------------------------------------------------------------
        if len(self.ListList):
            self.PlayList = copy.deepcopy(self.ListList)         
            self.play_list_update()

            self.PlayNumMax = len(self.PlayList)
            if self.PlayON:
                self.stop_sched_music()
                
            #Define RANDOM
            if self.SchedNow[2]:
                self.PlayRandom = 1
                self.PlayS.children['widBtPlayS2'].children['btPlaySRand'].set_text('Random ON')
            else:
                self.PlayRandom = 0
                self.PlayS.children['widBtPlayS2'].children['btPlaySRand'].set_text('Random OFF')
            #Define LOOP
            if self.SchedNow[3]:
                self.PlayLoop = 1
                self.PlayS.children['widBtPlayS2'].children['btPlaySLoop'].set_text('Loop ON')
            else:
                self.PlayLoop = 0
                self.PlayS.children['widBtPlayS2'].children['btPlaySLoop'].set_text('Loop OFF')
            #Define VOLUME
            self.VolumeOn = 1
            self.Volume = int(self.SchedNow[4])
            volnum = 'Vol ' + str(self.Volume) + ('%')
            self.PlayS.children['widBtPlayS2'].children['btPlaySVolumeOn'].set_text(volnum)
#             vol = str(self.LightShowPiFolder.absolute()) + '/bin/vol ' + str(self.Volume)
            vol = "amixer sset " + self.AlsaDevice + " " + str(self.Volume) + "%"
            os.system(vol)
            #START MUSIC
            self.PlayON = True
            self.PlayNum = 1
            self.playSong(self.PlayNum)

            

# SAVE SHOW
    def on_saveas_dialog_confirm(self, widget, filelist):
        filelist = Path(filelist)
##        print(filelist.suffix)
        if filelist.exists():
            if filelist.suffix == '.shw':
                dialog = gui.GenericDialog(title='CONFIRMATION', message='File exists. Do you want to write over it?', width='400px', style={'border':'1px solid black', 'border-radius':'10px', 'position':'relative', 'top':'50px',})
                dialog.conf.style.update({'margin-right':'100px', 'width':'100px'})
                dialog.confirm_dialog.do(self.save_show_file, filelist.absolute())
                dialog.show(self)
            else:
                dialog = gui.GenericDialog(title='ERROR', message='Wrong file format!', width='400px', style={'border':'1px solid black', 'border-radius':'10px', 'position':'relative', 'top':'50px',})
                dialog.cancel.style['display'] = 'none'
                dialog.conf.style.update({'margin-right':'150px', 'width':'100px'})
                dialog.show(self)
        else:
            if filelist.suffix == '.shw':
                self.save_show_file(self, filelist.absolute())
            elif filelist.suffix == '':
                fileappo = filelist.absolute()
                filelist = str(fileappo) + '.shw'
##                print(filelist)
                self.save_show_file(self, filelist)
            else:
                dialog = gui.GenericDialog(title='ERROR', message='Wrong file format!', width='400px', style={'border':'1px solid black', 'border-radius':'10px', 'position':'relative', 'top':'50px',})
                dialog.cancel.style['display'] = 'none'
                dialog.conf.style.update({'margin-right':'150px', 'width':'100px'})
                dialog.show(self)
    
    def save_show_file(self, widget, filelist):
        if len(self.ListList):
            with open(filelist, 'w') as file:
                file.write('[SHOW MANAGER]\n')
                for x in self.ListList:
                    appo = []
                    appo = self.ListList[x]
                    appoSong = appo[0].absolute()
                    temp = str(appo[1]).strip()
                    if temp == 'none':
                        name = str(appoSong) + '\t' + 'none' + '\n'
                    else:
                        appoConfig = appo[1].absolute()
                        name = str(appoSong) + '\t' + str(appoConfig) + '\n'
                    file.write(name)          
        else:
            dialog = gui.GenericDialog(title='ERROR', message='The songs list is empty! File not saved.', width='400px', style={'border':'1px solid black', 'border-radius':'10px', 'position':'relative', 'top':'50px',})
            dialog.cancel.style['display'] = 'none'
            dialog.conf.style.update({'margin-right':'150px', 'width':'100px'})
            dialog.show(self)
        
        
            
# SAVE SCHEDULER
    def sched_saveas_dialog_confirm(self, widget, filesched):        
        filesched = Path(filesched)
        if filesched.exists():
            if filesched.suffix == '.sch':
                dialog = gui.GenericDialog(title='CONFIRMATION', message='File exists. Do you want to write over it?', width='400px', style={'border':'1px solid black', 'border-radius':'10px', 'position':'relative', 'top':'50px',})
                dialog.conf.style.update({'margin-right':'100px', 'width':'100px'})
                dialog.confirm_dialog.do(self.save_sched_file, filesched.absolute())
                dialog.show(self)
            else:
                dialog = gui.GenericDialog(title='ERROR', message='Wrong file format!', width='400px', style={'border':'1px solid black', 'border-radius':'10px', 'position':'relative', 'top':'50px',})
                dialog.cancel.style['display'] = 'none'
                dialog.conf.style.update({'margin-right':'150px', 'width':'100px'})
                dialog.show(self)
        else:
            if filesched.suffix == '.sch':
                self.save_sched_file(self, filesched.absolute())
            elif filesched.suffix == '':
                fileappo = filesched.absolute()
                filesched = str(fileappo) + '.sch'
                self.save_sched_file(self, filesched)
            else:
                dialog = gui.GenericDialog(title='ERROR', message='Wrong file format!', width='400px', style={'border':'1px solid black', 'border-radius':'10px', 'position':'relative', 'top':'50px',})
                dialog.cancel.style['display'] = 'none'
                dialog.conf.style.update({'margin-right':'150px', 'width':'100px'})
                dialog.show(self)
            
    def save_sched_file(self, widget, filesched):
        if len(self.SchedList):
            with open(filesched, 'w') as file:
                file.write('[SHOW MANAGER SCHEDULE]\n')
                for x in self.SchedList:
                    appo = []
                    appo = self.SchedList[x]
                    name = ''
                    w = 0
                    while w <= len(appo)-2:
                        name += str(appo[w]) + '\t'
                        w += 1
                    name += str(appo[w]) + '\n'
#                     print(name)
                    file.write(name)         
        else:
            dialog = gui.GenericDialog(title='ERROR', message='The scheduler list is empty! File not saved.', width='400px', style={'border':'1px solid black', 'border-radius':'10px', 'position':'relative', 'top':'50px',})
            dialog.cancel.style['display'] = 'none'
            dialog.conf.style.update({'margin-right':'150px', 'width':'100px'})
            dialog.show(self)


#Fill the lists with only the name of the files
    def fill_list(self, ListX):
        listY = []
        for x in ListX:
            listY.append(x.name)
        return listY

# SONG - Return a lists with only the name of the songs extracted from the songs dictionary
    def song_list(self, ListX):
        listY = []
        for x in ListX:
            appo = ListX[x]
            listY.append(appo.name)
        return listY

# SONG - Generate a new key for the songs dictionary
    def song_key(self, ListX):
        key = 0
        if len(ListX):
            for x in ListX:
                appo = int(x)
                if appo > key:
                    key = appo
        key =  key + 1
        return key

    def alsa_dev_set(self, widget):
        self.AlsaDevice = self.AlsaDev.get_text()
        vol = "amixer sset " + self.AlsaDevice + " " + str(self.Volume) + "%"
        os.system(vol)
        print(vol)


# Reduce the legth of file name to 40
    def cut_name(name, iniz = False, car = 40):
        if len(name) > car:
            x = len(name)
            x = x - car
            if not iniz:
                name = name[x:]
                name = "..." + name
            else:
                name = name[:car]
                name = name + "..."
        return name

if __name__ == "__main__":
    # starts the webserver
    start(MyApp, address='', port=8081, start_browser=True, enable_file_cache=False, username=None, password=None)
##    start(MyApp, debug=True)

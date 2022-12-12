from kivy.core.audio import SoundLoader
# import winsound
# def give_alert():
#     sound = SoundLoader.load('mytest.wav')
#     if sound:
#         print("Sound found at %s" % sound.source)
#         print("Sound is %.3f seconds" % sound.length)
#         sound.play()
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
import time
import sys
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import StaleElementReferenceException
import json
from kivy.uix.checkbox import CheckBox
from kivy.uix.widget import Widget
import openpyxl
from kivy.uix.actionbar import ActionLabel
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.popup import Popup
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.core.window import Window
#Window.fullscreen = True
from kivy.properties import NumericProperty, ReferenceListProperty
#import kivysome as ks
#kivysome.enable("https://kit.fontawesome.com/{YOURCODE}.js", group=kivysome.FontGroup.SOLID)
class CALENDARPOPUP(Popup):
    pass
###########################################################
Builder.load_string("""
<ArrowButton>:
    background_normal: ""
    background_down: ""
    background_color: 1, 1, 1, 0
    size_hint: .1, .1
<MonthYearLabel>:
    pos_hint: {"top": 1, "center_x": .5}
    size_hint: None, 0.1
    halign: "center"
<MonthsManager>:
    pos_hint: {"top": .9}
    size_hint: 1, .9
<ButtonsGrid>:
    cols: 7
    rows: 7
    size_hint: 1, 1
    pos_hint: {"top": 1}
<DayAbbrLabel>:
    text_size: self.size[0], None
    halign: "center"
<DayAbbrWeekendLabel>:
    color: 1, 0, 0, 1
    
<DayButton>:
    group: "day_num"
    
<DayNumWeekendButton>:
    background_color: 1, 0, 0, 1
""")    
###########################################################

class DatePicker(TextInput):
    """ 
    Date picker is a textinput, if it focused shows popup with calendar
    which allows you to define the popup dimensions using pHint_x, pHint_y, 
    and the pHint lists, for example in kv:
    DatePicker:
        pHint: 0.7,0.4 
    would result in a size_hint of 0.7,0.4 being used to create the popup
    """
    pHint_x = NumericProperty(0.7)
    pHint_y = NumericProperty(0.7)
    pHint = ReferenceListProperty(pHint_x ,pHint_y)

    def __init__(self, touch_switch=False, *args, **kwargs):
        super(DatePicker, self).__init__(*args, **kwargs)
        
        self.touch_switch = touch_switch
        self.init_ui() 
        
    def init_ui(self):
        
        self.text = today_date()
        # Calendar
        self.cal = CalendarWidget(touch_switch=self.touch_switch)#CalendarWidget(as_popup=True, 
                   #               touch_switch=self.touch_switch)
        # Popup
        self.popup = CALENDARPOPUP(content=self.cal, on_dismiss=self.update_value, title="", separator_height=0)#Popup(content=self.cal, on_dismiss=self.update_value, 
                           #title="")
        self.cal.parent_popup = self.popup
        
        self.bind(focus=self.show_popup)
        
    def show_popup(self, isnt, val):
        """ 
        Open popup if textinput focused, 
        and regardless update the popup size_hint 
        """
        self.popup.size_hint=self.pHint        
        if val:
            # Automatically dismiss the keyboard 
            # that results from the textInput 
            Window.release_all_keyboards()
            self.popup.open()
        
    def update_value(self, inst):
        """ Update textinput value on popup close """
            
        self.text = "%s-%s-%s" % tuple(self.cal.active_date)
        self.focus = False

class CalendarWidget(RelativeLayout):
    """ Basic calendar widget """
    
    def __init__(self, as_popup=False, touch_switch=False, *args, **kwargs):
        super(CalendarWidget, self).__init__(*args, **kwargs)
        
        self.as_popup = as_popup
        self.touch_switch = touch_switch
        self.prepare_data()     
        self.init_ui()
        
    def init_ui(self):
        
        self.left_arrow = ArrowButton(text="<", on_press=self.go_prev,
                                      pos_hint={"top": 1, "left": 0})
        
        self.right_arrow = ArrowButton(text=">", on_press=self.go_next,
                                       pos_hint={"top": 1, "right": 1})
        
        self.add_widget(self.left_arrow)        
        self.add_widget(self.right_arrow)
        
        # Title        
        self.title_label = MonthYearLabel(text=self.title)
        self.add_widget(self.title_label)
        
        # ScreenManager
        self.sm = MonthsManager()
        self.add_widget(self.sm)
        
        self.create_month_scr(self.quarter[1], toogle_today=True) 
    
    def create_month_scr(self, month, toogle_today=False):
        """ Screen with calendar for one month """        
        
        scr = Screen()
        m = self.month_names_eng[self.active_date[1] - 1]
        scr.name = "%s-%s" % (m, self.active_date[2])  # like march-2015
        
        # Grid for days
        grid_layout = ButtonsGrid()
        scr.add_widget(grid_layout)
        
        # Days abbrs 
        for i in range(7):
            if i >= 5:  # weekends
                l = DayAbbrWeekendLabel(text=self.days_abrs[i])
            else:  # work days
                l = DayAbbrLabel(text=self.days_abrs[i])
            
            grid_layout.add_widget(l)
            
        # Buttons with days numbers
        for week in month:
            for day in week:
                if day[1] >= 5:  # weekends
                    tbtn = DayNumWeekendButton(text=str(day[0]))
                else:  # work days
                    tbtn = DayNumButton(text=str(day[0]))
                
                tbtn.bind(on_press=self.get_btn_value)
                
                if toogle_today:
                    # Down today button
                    if day[0] == self.active_date[0] and day[2] == 1:
                        tbtn.state = "down"
                # Disable buttons with days from other months
                if day[2] == 0:
                    tbtn.disabled = True
                
                grid_layout.add_widget(tbtn)

        self.sm.add_widget(scr)
        
    def prepare_data(self):
        """ Prepare data for showing on widget loading """
    
        # Get days abbrs and month names lists 
        self.month_names = get_month_names()
        self.month_names_eng = get_month_names_eng()
        self.days_abrs = get_days_abbrs()    
        
        # Today date
        self.active_date = today_date_list()
        # Set title
        self.title = "%s - %s" % (self.month_names[self.active_date[1] - 1], 
                                  self.active_date[2])
                
        # Quarter where current month in the self.quarter[1]
        self.get_quarter()
    
    def get_quarter(self):
        """ Get caledar and months/years nums for quarter """
        
        self.quarter_nums = calc_quarter(self.active_date[2], 
                                                  self.active_date[1])
        self.quarter = get_quarter(self.active_date[2], 
                                            self.active_date[1])
    
    def get_btn_value(self, inst):
        """ Get day value from pressed button """
        
        self.active_date[0] = int(inst.text)
        global my_activated_button_data 
        my_activated_button_data = self.active_date        
        #self.parent.parent.parent.dismiss()
        #if self.as_popup:
        #    self.parent_popup.dismiss()
        
    def go_prev(self, inst):
        """ Go to screen with previous month """        

        # Change active date
        self.active_date = [self.active_date[0], self.quarter_nums[0][1], 
                            self.quarter_nums[0][0]]

        # Name of prev screen
        n = self.quarter_nums[0][1] - 1
        prev_scr_name = "%s-%s" % (self.month_names_eng[n], 
                                   self.quarter_nums[0][0])
        
        # If it's doen't exitst, create it
        if not self.sm.has_screen(prev_scr_name):
            self.create_month_scr(self.quarter[0])
            
        self.sm.current = prev_scr_name
        self.sm.transition.direction = "left"
        
        self.get_quarter()
        self.title = "%s - %s" % (self.month_names[self.active_date[1] - 1], 
                                  self.active_date[2])
        
        self.title_label.text = self.title
    
    def go_next(self, inst):
        """ Go to screen with next month """
        
         # Change active date
        self.active_date = [self.active_date[0], self.quarter_nums[2][1], 
                            self.quarter_nums[2][0]]

        # Name of prev screen
        n = self.quarter_nums[2][1] - 1
        next_scr_name = "%s-%s" % (self.month_names_eng[n], 
                                   self.quarter_nums[2][0])
        
        # If it's doen't exitst, create it
        if not self.sm.has_screen(next_scr_name):
            self.create_month_scr(self.quarter[2])
            
        self.sm.current = next_scr_name
        self.sm.transition.direction = "right"
        
        self.get_quarter()
        self.title = "%s - %s" % (self.month_names[self.active_date[1] - 1], 
                                  self.active_date[2])
        
        self.title_label.text = self.title
        
    def on_touch_move(self, touch):
        """ Switch months pages by touch move """
                
        if self.touch_switch:
            # Left - prev
            if touch.dpos[0] < -30:
                self.go_prev(None)
            # Right - next
            elif touch.dpos[0] > 30:
                self.go_next(None)
        
class ArrowButton(Button):
    pass

from kivymd.app import MDApp as App
class MonthYearLabel(Label):
    pass

class MonthsManager(ScreenManager):
    pass

class ButtonsGrid(GridLayout):
    pass

class DayAbbrLabel(Label):
    pass

class DayAbbrWeekendLabel(DayAbbrLabel):
    pass

class DayButton(ToggleButton):
    pass

class DayNumButton(DayButton):
    pass

class DayNumWeekendButton(DayButton):
    pass

#!/usr/bin/python
# -*- coding: utf-8 -*-

###########################################################
# KivyCalendar (X11/MIT License)
# Calendar & Date picker widgets for Kivy (http://kivy.org)
# https://bitbucket.org/xxblx/kivycalendar
# 
# Oleg Kozlov (xxblx), 2015
# https://xxblx.bitbucket.org/
###########################################################

from calendar import month_name, day_abbr, Calendar, monthrange
from datetime import datetime
from locale import getdefaultlocale

def get_month_names():
    """ Return list with months names """
    
    result = []
    # If it possible get months names in system language
    try:
        with TimeEncoding("%s.%s" % getdefaultlocale()) as time_enc:
            for i in range(1, 13):
                result.append(month_name[i].decode(time_enc))
                
        return result
    
    except:
        return get_month_names_eng()
        
def get_month_names_eng():
    """ Return list with months names in english """
    
    result = []
    for i in range(1, 13):
        result.append(month_name[i])
        
    return result

def get_days_abbrs():
    """ Return list with days abbreviations """
    
    result = []
    # If it possible get days abbrs in system language
    try:
        with TimeEncoding("%s.%s" % getdefaultlocale()) as time_enc:
            for i in range(7):
                result.append(day_abbr[i].decode(time_enc))    
    except:
        for i in range(7):
            result.append(day_abbr[i])
            
    return result

def calc_quarter(y, m):
    """ Calculate previous and next month """
    
    # Previous / Next month's year number and month number
    prev_y = y
    prev_m = m - 1
    next_y = y
    next_m = m + 1    
    
    if m == 1:
        prev_m = 12
        prev_y = y - 1
    elif m == 12:
        next_m = 1
        next_y = y + 1
        
    return [(prev_y, prev_m), (y, m), (next_y, next_m)]

def get_month(y, m):
    """ 
    Return list of month's weeks, which day 
    is a turple (<month day number>, <weekday number>) 
    """
    
    cal = Calendar()
    month = cal.monthdays2calendar(y, m)
    
    # Add additional num to every day which mark from 
    # this or from other day that day numer
    for week in range(len(month)):
        for day in range(len(month[week])):
            _day = month[week][day]
            if _day[0] == 0:
                this = 0
            else: 
                this = 1
            _day = (_day[0], _day[1], this)
            month[week][day] = _day
    
    # Days numbers of days from preious and next monthes
    # marked as 0 (zero), replace it with correct numbers
    # If month include 4 weeks it hasn't any zero
    if len(month) == 4:
        return month        
    
    quater = calc_quarter(y, m)
    
    # Zeros in first week    
    fcount = 0
    for i in month[0]:
        if i[0] == 0:
            fcount += 1
    
    # Zeros in last week
    lcount = 0
    for i in month[-1]:
        if i[0] == 0:
            lcount += 1
            
    if fcount:
        # Last day of prev month
        n = monthrange(quater[0][0], quater[0][1])[1]
        
        for i in range(fcount):
            month[0][i] = (n - (fcount - 1 - i), i, 0)
            
    if lcount:
        # First day of next month
        n = 1
        
        for i in range(lcount):
            month[-1][-lcount + i] = (n + i, 7 - lcount + i, 0)
            
    return month

def get_quarter(y, m):
    """ Get quarter where m is a middle month """
    
    result = []
    quarter = calc_quarter(y, m)
    for i in quarter:
        result.append(get_month(i[0], i[1]))
        
    return result

def today_date_list():
    """ Return list with today date """
    
    return [datetime.now().day, datetime.now().month, datetime.now().year]
    
def today_date():
    """ Return today date dd.mm.yyyy like 28.02.2015 """

    return datetime.now().strftime("%d/%m/%Y")



#if __name__ == "__main__":
#    from kivy.base import runTouchApp
    
#    c = DatePicker()
    #runTouchApp(c)
#import sys
#sys.path.append(r'C:\Users\girija\AppData\Local\Programs\Python\Python38-32\Lib\site-packages')
#sys.path.append(r'C:\Users\girija\AppData\Local\Programs\Python\Python38-32\kivy_venv\Lib\site-packages')

def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)
from kivy.config import Config
#from kivy_garden.graph import Graph, MeshLinePlot
Config.set('kivy', 'exit_on_escape', '0')  
from datetime import date
#print(datetime.now())    
#from KivyCalendar import CalendarWidget, DatePicker#, calendar_data, calendar_ui      
import speech_recognition
import pyttsx3
import sys, os    
import sqlite3
#import pkg_resources.py2_warn
from kivy.graphics import Color, Rectangle
from kivy.uix.switch import Switch
#from kivy.clock import CyClockBase, ClockEvent, FreeClockEvent
from sqlite3 import Error
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.bubble import BubbleButton
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.actionbar import ActionDropDown
from kivy.uix.screenmanager import Screen,ScreenManager
from kivy.properties import ObjectProperty, ListProperty, NumericProperty, StringProperty, BooleanProperty, DictProperty
from kivy.uix.label import Label
from kivy.uix.stacklayout import StackLayout
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.uix.recyclegridlayout import RecycleGridLayout
from kivy.uix.behaviors import FocusBehavior
from kivy.uix.recycleview.layout import LayoutSelectionBehavior
from kivy.uix.popup import Popup
from kivy.uix.button import Button
from kivy.uix.dropdown import DropDown
from kivy.uix.actionbar import ActionItem
from kivy.uix.actionbar import ActionButton
from kivy.uix.textinput import TextInput
import time
from kivy.factory import Factory
import hashlib
#import weakref
import os
import csv
import pathlib
#import urllib3
import webbrowser
from math import sin
#from kivy.core.window import Window
import kivy.utils as utils
#from utils import get_color_from_hex
#Window.clearcolor = utils.get_color_from_hex('#00BFFF')#(1, 1, 1, 1)
#from pathlib import Path
class Database_maker():

    #def __init__(self, *args, **kwargs):
    #    super(Database_maker, self).__init__(*args, **kwargs)
    #    self.file_maker()
    def file_maker(self):
        Directory = pathlib.Path(r"C:\KIT")
        DataDirectory = pathlib.Path(r"C:\KIT\DATABASE")
        DataBase = pathlib.Path(r"C:\KIT\DATABASE\KIT_DATABASE.db")
        Nest1 = r"C:\KIT"
        Nest2 = "DATABASE"
        if not Directory.exists():
            os.mkdir(Nest1)
            if not DataDirectory.exists():
                panther = os.path.join(Nest1, Nest2)
                os.mkdir(panther)
                if not DataBase.exists():
                    DARKCONNECTION = sqlite3.connect(r"C:\KIT\DATABASE\KIT_DATABASE.db")
                    DARKCONNECTION.close()
                    print('No chance')
        else:
            print("Task Accomplished!!!")    
        #Path("/my/directory").mkdir(parents=True, exist_ok=True)
        #if not os.path.exists('C:\KIT\DATABASE'):
        #    os.makedirs('C:\KIT\DATABASE')
        #print('Successful')

    def table_maker(self):
        connectman = sqlite3.connect(r"C:\KIT\DATABASE\KIT_DATABASE.db")
        #connectman = sqlite3.connect("C:\KIT\DATABASE\KIT_DATABASE.db")
        cursormouse = connectman.cursor()
        cursormouse.execute("CREATE TABLE IF NOT EXISTS customers(CUSTOMER_ID INTEGER PRIMARY KEY AUTOINCREMENT, CUSTOMER_NAME TEXT, CUSTOMER_ADDRESS TEXT, CUSTOMER_AREA TEXT, CUSTOMER_CITY TEXT, CUSTOMER_STATE TEXT, CUSTOMER_COUNTRY TEXT, CUSTOMER_PINCODE INTEGER, CUSTOMER_PHONE INTEGER, CUSTOMER_EMAIL TEXT, CUSTOMER_REMARK TEXT, DATE TEXT) ")
        #cursormouse.execute("DROP TABLE IF EXISTS login")
        print('done')
        #cursormouse
        cursormouse.execute("CREATE TABLE IF NOT EXISTS login(USER_ID INTEGER PRIMARY KEY AUTOINCREMENT, FIRSTNAME TEXT,  LASTNAME TEXT, EMAIL TEXT, MOBILE INTEGER, CITY TEXT, USERNAME TEXT, PASSWORD TEXT, ACTIVE TEXT, ADMIN TEXT, DATE TEXT)")
        connectman.commit()
        connectman.close()

    def admin_creater(self):
        connectadmin = sqlite3.connect(r"C:\KIT\DATABASE\KIT_DATABASE.db")
        cursoradmin = connectadmin.cursor()
        useradministrator = "admin"
        passadministrator = "admin"
        md5passadministrator = hashlib.md5(passadministrator.encode())
        hexmd5passadministrator = md5passadministrator.hexdigest()
        fname = "admin"
        lname = "admin"
        email = "admin@xyz.com"
        mobile = "0000000000"
        city = "UNKNOWN"
        active = "True"
        admin = "True"
        dater = str(date.today())
        cursoradmin.execute("SELECT USERNAME FROM login WHERE USERNAME = ?",(useradministrator,))
        fetcher = cursoradmin.fetchall()
        if len(fetcher) == 0:
            cursoradmin.execute("INSERT INTO login(FIRSTNAME, LASTNAME, EMAIL, MOBILE, CITY, USERNAME, PASSWORD, ACTIVE, ADMIN, DATE) VALUES(?,?,?,?,?,?,?,?,?,?)",(fname, lname, email, mobile, city, useradministrator, hexmd5passadministrator, active, admin, dater)) 
        connectadmin.commit()
        connectadmin.close()           

#class ActionDatePicker(TextInput, CalendarWidget, ActionItem):    

class ActionTextInput(TextInput, ActionItem):
    pass

class Login(Screen):
    lol = BooleanProperty(False)
    rofl = BooleanProperty(False)
    #rofl = BooleanProperty(True)
    #def __init__(self, *args, **kwargs):
        #super(Login,self).__init__(*args, **kwargs)
        #super(LoginPopup()).__init__(*args, **kwargs)
    #    self.background()
        #LoginPopup().open()
    #def background(self):
    #    L = Label()
    def screenview(self):
        self.lol = True
        LoginPopup().dismiss()
        print('completed')
        print(str(self.lol))
    
    def adminscreenview(self):
        self.rofl = True
        LoginPopup().dismiss()
        print('admincompleted')
        print(str(self.rofl))
    
    def popclose(self):
        LoginPopup().dismiss()
    
    def screenimage(self):
        rofla = Label(text='HELLO EVERYBODY', font_size=50)
        self.screenmiaow.add_widget(rofla)
        print('DONEDONADONE')
    #def opener(self):
    #    some_popup = LoginPopup()
    #    some_popup.open()


class RequiredFields(Popup):
    pass

class ProfileEditTextInput(TextInput):
    pass

class PasswordPopup(Popup):

    def openpass(self):
        l5 = EditLabel(text='[color=000000]Password[/color] [color=0000ff][b]\u2022[/b][/color]', markup= True)   
        t5 = ProfileEditTextInput(write_tab= False, password=True, password_mask= '\u2022', multiline=False)
        t5.bind(on_text_validate=lambda x: self.passpop(t5.text))
        #l11 = EditLabel()
        #l12 = EditLabel()
        l13 = EditLabel()
        l14 = EditLabel()
        #l15 = EditLabel()
        #l16 = EditLabel()
        l17 = Label()
        #griddy = GridLayout(cols=2)
        b1 = Reqbutton1(text= 'Submit')
        b2 = Reqbutton2(text= 'Close')
        b1.bind(on_press= lambda x:self.passpop(t5.text))
        #b1.bind(on_release= lambda x:self.closeit())
        b2.bind(on_press= lambda x:self.dismiss())
        self.editgrid.add_widget(l5)
        self.editgrid.add_widget(t5)
        self.editgrid2.add_widget(b2)
    #self.editgrid2.add_widget(l12)
        self.editgrid2.add_widget(l13)
        self.editgrid2.add_widget(l14)
        self.editgrid2.add_widget(l17)
        self.editgrid2.add_widget(b1)
        #self.editgrid2.add_widget()
        self.open()

        #self.editgrid2.add_widget()
    def passpop(self, passpass):
        if not(str(passpass) and str(passpass).strip()):
            print('Enter password')
        else:    
            connector = sqlite3.connect(r"C:\KIT\DATABASE\KIT_DATABASE.db")
            cursorobject = connector.cursor()
            #cursorobject.execute('SELECT PASSWORD FROM login WHERE USERNAME = ? AND PASSWORD = ?', (str(username),str(hexmd5pass)))
            #row = cursorobject.fetchone()
            #passpass = self.ids['passpass'].text
            passwer = hashlib.md5(str(passpass).encode())
            global passw 
            passw = passwer.hexdigest()
            cursorobject.execute('UPDATE login SET PASSWORD = ? WHERE USERNAME = ? AND PASSWORD = ?',(str(passw), str(username), str(hexmd5pass)))
            connector.commit()
            connector.close()
            #hexmd5pass = str(passw)        
            self.dismiss()
            self.changepass(passw)
            Okay().open()

    def changepass(self, hex):
        global hexmd5pass
        hexmd5pass = str(hex)
        print('password accomplished')

class ProfilePopup(Popup):

    def popy(self):
        #username = LoginPopup().ids['Usertext'].text
        #password = LoginPopup().ids['Passtext'].text        
        connector = sqlite3.connect(r"C:\KIT\DATABASE\KIT_DATABASE.db")
        cursorobject = connector.cursor()
        cursorobject.execute('SELECT FIRSTNAME, LASTNAME, EMAIL, MOBILE, CITY, USERNAME FROM login WHERE USERNAME = ? AND PASSWORD = ?', (str(username),str(hexmd5pass)))
        row = cursorobject.fetchone()
        l1 = EditLabel(text='[color=000000]First Name[/color] [color=0000ff][b]\u2022[/b][/color]', markup= True)
        t1 = ProfileEditTextInput(text= str(row[0]), write_tab= False)#, id= text1)
        l2 = EditLabel(text='[color=000000]Last Name[/color] [color=0000ff][b]\u2022[/b][/color]', markup= True)
        t2 = ProfileEditTextInput(text= str(row[1]), write_tab= False)#, id= text2)
        l3 = EditLabel(text='[color=000000]Email[/color] [color=0000ff][b]\u2022[/b][/color]', markup= True)
        t3 = ProfileEditTextInput(text= str(row[2]), write_tab= False)#, id= text3)
        l4 = EditLabel(text='[color=000000]Mobile[/color] [color=0000ff][b]\u2022[/b][/color]', markup= True)
        t4 = ProfileEditTextInput(text= str(row[3]), write_tab= False)#, id= text4)
        l5 = EditLabel(text='[color=000000]City[/color] [color=0000ff][b]\u2022[/b][/color]', markup= True)
        t5 = ProfileEditTextInput(text= str(row[4]), write_tab= False)#, id= text5)
        #l6 = EditLabel(text='[color=000000]User Name[/color] [color=0000ff][b]\u2022[/b][/color]', markup= True)
        #t6 = ProfileEditTextInput(text= str(row[5]), write_tab= False)#, id= text6)
        #l7 = EditLabel(text='[color=000000]Password[/color] [color=0000ff][b]\u2022[/b][/color]', markup= True)
        #t7 = ProfileEditTextInput(write_tab= False)#, id= text7)
        #l8 = EditLabel(text='[color=000000]Phone[/color] [color=0000ff][b]\u2022[/b][/color]', markup= True)
        #t8 = EditTextInput(text= str(row[7]), write_tab= False)#, id= text8)
        #l9 = EditLabel(text='[color=000000]Email[/color] [color=0000ff][b]\u2022[/b][/color]', markup= True)
        #t9 = EditTextInput(text= str(row[8]), write_tab= False)#, id= text9)
        #l10 = EditLabel(text= '[color=000000]Remark[/color] [color=0000ff][b]\u2022[/b][/color]', markup= True)
        #t10 = EditTextInput(text= str(row[9]), write_tab= False)
        l11 = EditLabel()
        l12 = EditLabel()
        l13 = EditLabel()
        l14 = EditLabel()
        #l15 = EditLabel()
        #l16 = EditLabel()
        l17 = Label()
        #griddy = GridLayout(cols=2)
        b1 = Reqbutton1(text= 'Submit')
        b2 = Reqbutton2(text= 'Close')
        b1.bind(on_press= lambda x:self.edit(t1.text,t2.text,t3.text,t4.text,t5.text))#, t6.text))#,t6.text,t7.text))                                                                
        #b1.bind(on_release= lambda x:self.closeit())
        b2.bind(on_press= lambda x:self.dismiss())
        #griddy.add_widget(b1)
        #griddy.add_widget(b2)
        self.editgrid.add_widget(l1)
        self.editgrid.add_widget(t1)
        self.editgrid.add_widget(l2)
        self.editgrid.add_widget(t2)
        self.editgrid.add_widget(l3)
        self.editgrid.add_widget(t3)
        self.editgrid.add_widget(l4)
        self.editgrid.add_widget(t4)
        self.editgrid.add_widget(l5)
        self.editgrid.add_widget(t5)
        #self.editgrid.add_widget(l6)
        #self.editgrid.add_widget(t6)
        #self.editgrid.add_widget(l7)
        #self.editgrid.add_widget(t7)
        #self.editgrid.add_widget(l8)
        #self.editgrid.add_widget(t8)
        #self.editgrid.add_widget(l9)
        #self.editgrid.add_widget(t9)
        #self.editgrid.add_widget(l10)
        #self.editgrid.add_widget(t10)
        self.editgrid.add_widget(l11)
        self.editgrid.add_widget(l12)
        #self.editgrid.add_widget(b2)
        #self.editgrid.add_widget(l13)
        #self.editgrid.add_widget(b1)
        self.editgrid2.add_widget(b2)
        self.editgrid2.add_widget(l13)
        self.editgrid2.add_widget(l14)
        self.editgrid2.add_widget(l17)
        #self.editgrid2.add_widget(l16)
        self.editgrid2.add_widget(b1)
        print('Completed' + str(row)) #+#instincator)
        connector.commit()
        connector.close()
        #Create().MEGACONNECTOR()
        #return self.editgrid
        self.open()    

    def edit(self, t1, t2, t3, t4, t5):#, t6):#t6, t7):
        con3 = sqlite3.connect(r"C:\KIT\DATABASE\KIT_DATABASE.db")
        cursorObj3 = con3.cursor()
        #passwer = hashlib.md5(str(t7).encode())
        #passw = passwer.hexdigest()
        #cursorObj3.execute('SELECT CUSTOMER_PHONE FROM customers WHERE CUSTOMER_PHONE = ?',(str(Phone)))
        #names = cursorObj3.fetchall()
        
        #if len(names) == 1
        #for name in names:
        #    if str(Phone) == str(name[0]):
        #        print('exists')
        #        Factory.Nameerror().open()
        #        break
        #    else:    
        #        #cursorObj1.execute('INSERT INTO customers(CUSTOMER_NAME, CUSTOMER_ADDRESS, CUSTOMER_AREA, CUSTOMER_CITY, CUSTOMER_STATE, CUSTOMER_COUNTRY, CUSTOMER_PINCODE, CUSTOMER_PHONE, CUSTOMER_EMAIL, CUSTOMER_REMARK) VALUES(?,?,?,?,?,?,?,?,?,?)', (Name, Address, Area, City, State, Country, Pincode, Phone, Email, Remark))       
         #       cursorObj3.execute('UPDATE customers SET CUSTOMER_NAME = ?, CUSTOMER_ADDRESS = ?, CUSTOMER_AREA = ?, CUSTOMER_CITY = ?, CUSTOMER_STATE = ?, CUSTOMER_COUNTRY = ?, CUSTOMER_PINCODE = ?, CUSTOMER_PHONE = ?, CUSTOMER_EMAIL = ? WHERE CUSTOMER_ID = ?',(Name, Address, Area, City, State, Country, Pincode, Phone, Email, instincator))
                #Factory.Okay().open()
                #Create().MEGACONNECTOR()
         #       self.dismiss()
         #       break           
        cursorObj3.execute('UPDATE login SET FIRSTNAME = ?, LASTNAME = ?, EMAIL = ?, MOBILE = ?, CITY = ? WHERE USERNAME = ? AND PASSWORD = ?',(str(t1),str(t2),str(t3),str(t4),str(t5),str(username), str(hexmd5pass)))#'UPDATE customers SET CUSTOMER_NAME = ?, CUSTOMER_ADDRESS = ?, CUSTOMER_AREA = ?, CUSTOMER_CITY = ?, CUSTOMER_STATE = ?, CUSTOMER_COUNTRY = ?, CUSTOMER_PINCODE = ?, CUSTOMER_PHONE = ?, CUSTOMER_EMAIL = ?, CUSTOMER_REMARK = ? WHERE CUSTOMER_ID = ?',(Name, Address, Area, City, State, Country, Pincode, Phone, Email, Remark, instincator))
        con3.commit()
        #Create().MEGACONNECTOR()
        #nest_edit(con3)
        con3.close() 
        self.dismiss()
        Okay().open()

    def closeit(self):
        self.dismiss()
        Okay().open()   

class ConPassPopup(Popup):
    pass

class TableRow(Widget):
    #datatuple = ListProperty()#list()
    #identity = self.identity
    firsttext = StringProperty()#datatuple[0]
    secondtext = StringProperty()# datatuple[1]
    thirdtext = StringProperty() #datatuple[2]
    fourthtext = StringProperty() #datatuple[3]
    def __init__(self, firsttext, secondtext, thirdtext, fourthtext, *args, **kwargs):
        super(TableRow, self).__init__(*args, **kwargs)
        #self.datatuple = datatuple
        self.firsttext = str(firsttext)# = datatuple[0]
        self.secondtext = str(secondtext)# = datatuple[1]
        self.thirdtext = str(thirdtext)# = datatuple[2]
        self.fourthtext = str(fourthtext)# = datatuple[3]

class SigninPopup(Popup):
   
    def logit(self):
        LoginPopup().clearmyself()
        self.dismiss()

    def register(self):
        FName = self.ids['FNameText'].text
        LName = self.ids['LNameText'].text
        Email = self.ids['EmailText'].text
        Mobile = self.ids['MobileText'].text
        City = self.ids['CityText'].text
        UserName = self.ids['UserText'].text
        Password = self.ids['PassText'].text
        MD5PASSWORD = hashlib.md5(Password.encode())
        HEXMD5PASSWORD = MD5PASSWORD.hexdigest()
        Confirm_Password = self.ids['ConPassText'].text
        dater = str(date.today())
        if not(str(FName) and str(FName).strip()) or not(str(LName) and str(LName).strip()) or not(str(Email) and str(Email).strip()) or not(str(Mobile) and str(Mobile).strip()) or not(str(City) and str(City).strip()) or not(str(UserName) and str(UserName).strip()) or not(str(Password) and str(Password).strip()) or not(str(Confirm_Password) and str(Confirm_Password).strip()):#len(FName) == 0 or len(LName) == 0 or len(Email) == 0 or len(Mobile) == 0 or len(City) == 0 or len(UserName) == 0 or len(Password) == 0 or len(Confirm_Password) == 0:
            print('Fill all the required fields')
            RequiredFields().open()
            self.dismiss()
        else:     
            if str(Password) == str(Confirm_Password):
                regcon = sqlite3.connect(r"C:\KIT\DATABASE\KIT_DATABASE.db")
                regcursor = regcon.cursor()
                #truly = True
                FALSLY = False
                regcursor.execute('INSERT INTO login(FIRSTNAME, LASTNAME, EMAIL, MOBILE, CITY, USERNAME, PASSWORD, ACTIVE, ADMIN, DATE) VALUES(?,?,?,?,?,?,?,?,?,?)',(str(FName), str(LName), str(Email), str(Mobile), str(City), str(UserName), str(HEXMD5PASSWORD), str(FALSLY), str(FALSLY), dater))
                regcon.commit()
                regcon.close()
                Okay().open()
                LoginPopup().clearmyself()
                self.dismiss()
#################################################################
            else:
                print('Password =! Confirm_Password')  
                ConPassPopup().open()
                #print(exit())  
#################################################################
class Dropman(ActionDropDown):
    
    def powpow(self):
        ProfilePopup().popy()
    
    def doeverything(self):
        self.dismiss()
        LoginPopup().open()
    
    def paspow(self):
        PasswordPopup().openpass()
    #def binder(self, butt):
    #    b1 = Button(text= 'Sign Out %s' %butt, height= 40)
    #    self.add_widget(b1)
        #print('done man')
        #b1.bind(on_press= lambda x: )
    #pass

class User(Popup):
    pass

class Validifier(Popup):
    pass

class Verify(Popup):
    pass

class Inactivate(Popup):
    pass

class LoginPopup(Popup):
    #on_lol = BooleanProperty(False)
    #userMan = StringProperty()
    #passMan = StringProperty()
    #Loggerit = ObjectProperty(None)

    def doall(self):
        self.get_password_username()        
        self.clearmyself()
    
    def clearmyself(self):
        usenthrow = self.ids['Usertext']
        paasnthrow = self.ids['Passtext']
        usenthrow.text = ""
        paasnthrow.text = ""
        print("DONEMAN")
        #username = self.ids['Usertext'].text
        #password = self.ids['Passtext'].text
    #    print('DONEMAN')

    def get_password_username(self):
        global username
        username = self.ids['Usertext'].text
        password = self.ids['Passtext'].text
        #print(username)
        #print(password)
        #if username or password is None:
        #    print('Enter valid')
        if not(str(username) and str(username).strip()) or not(str(password) and str(password).strip()):
        #if len(username) == 0 or len(password) == 0:
            print('Enter valid objects')
            Validifier().open()
            #print('\a')
            winsound.MessageBeep()
            self.clearmyself()
            #self.dismiss()
        else:    
            userpasscon = sqlite3.connect(r"C:\KIT\DATABASE\KIT_DATABASE.db")
            curse = userpasscon.cursor()
            #md5user = hashlib.md5(username.encode())
            #hexmd5user = md5user.hexdigest()
            md5pass = hashlib.md5(password.encode())
            global hexmd5pass 
            hexmd5pass = md5pass.hexdigest()
            curse.execute('SELECT USERNAME FROM login WHERE USERNAME = ?',(str(username),))
            fetchit = curse.fetchall()
            if len(fetchit) == 0:
                #self.dismiss()
                User().open()
                print('User %s Doesnt exists' %username)
                self.clearmyself()                
            else:    
                curse.execute("SELECT USER_ID, USERNAME, PASSWORD FROM login WHERE USERNAME=? AND PASSWORD=?",(str(username), str(hexmd5pass),))
                verify = curse.fetchall()
                print(verify)
                if len(verify) == 0:
                    Verify().open()
                    print('INCORRECT USERNAME PASSWORD COMBINATION')
                else:
                    for row in verify:
                        if row[0] == 1:
                            print("WELCOME ADMIN")
                            self.dismiss()
                            Login().adminscreenview()
                        else:
                            curse.execute("SELECT ACTIVE, ADMIN FROM login WHERE USERNAME=? AND PASSWORD=?",(str(username), str(hexmd5pass),))
                            ACTIVEVERIFY = curse.fetchall()
                            for VERIFY in ACTIVEVERIFY:
                                if VERIFY[0] == 'True':
                                    if VERIFY[1] == 'False':
                                        print('welcome')
                                        self.dismiss()  
                                        #Dropman().binder(username)                
                                        #app.root.current = 'Create'
                                        Login().screenview()
                                        print(os.system("python C:\hariharan\Arduino_programs\Loginform.py"))
                                    else:
                                        print('welcome co-admin')
                                        self.dismiss()
                                        Login().adminscreenview()    
                                else:
                                    print('NOT ACTIVATED') 
                                    Inactivate().open()   
                #self.manager.current = 'Create'
                #Management().transistor()
                #self.dismiss()
                #acbut = ActionButton(text='Fun')#background_normal= 'logger.png')
                #acbut.bind(on_press=lambda x: self.binder(acbut))
                #Create().actress.add_widget(acbut)
    
    #def binder(self, butt):
    #    butt.add_widget(Dropman)
    #    print('Butt has been executed')

    def signit(self):
        SigninPopup().open()
        #self.dismiss()

class CustomPopup(Popup):

    def insert(self):
        con1 = sqlite3.connect(r"C:\KIT\DATABASE\KIT_DATABASE.db")
        Name = self.ids['Name'].text
        Address = self.ids['Address'].text
        Area = self.ids['Area'].text
        City = self.ids['City'].text
        State = self.ids['State'].text
        Country = self.ids['Country'].text
        Pincode = self.ids['Pincode'].text
        Phone = self.ids['Phone'].text
        Email = self.ids['Email'].text
        Remark = self.ids['Remark'].text 
        DATE = str(date.today())       
        cursorObj1 = con1.cursor()
        cursorObj1.execute('SELECT CUSTOMER_PHONE FROM customers WHERE CUSTOMER_PHONE = ?',(str(Phone),))
        #global names 
        names = cursorObj1.fetchall()
        if len(names) == 0:
            cursorObj1.execute('INSERT INTO customers(CUSTOMER_NAME, CUSTOMER_ADDRESS, CUSTOMER_AREA, CUSTOMER_CITY, CUSTOMER_STATE, CUSTOMER_COUNTRY, CUSTOMER_PINCODE, CUSTOMER_PHONE, CUSTOMER_EMAIL, CUSTOMER_REMARK, DATE) VALUES(?,?,?,?,?,?,?,?,?,?,?)', (Name, Address, Area, City, State, Country, Pincode, Phone, Email, Remark, DATE))       
            Factory.Okay().open()
            #Create().MEGACONNECTOR(mytexty=str(Name))
            self.dismiss()
        else:
            print('exists')
            Factory.Nameerror().open()                              
        
        '''for name in names:
            if str(Phone) == str(name[0]):
                print('exists')
                print(name)
                print(names)
                Factory.Nameerror().open()
                break
            else:    
                print(name)
                print(names)
                cursorObj1.execute('INSERT INTO customers(CUSTOMER_NAME, CUSTOMER_ADDRESS, CUSTOMER_AREA, CUSTOMER_CITY, CUSTOMER_STATE, CUSTOMER_COUNTRY, CUSTOMER_PINCODE, CUSTOMER_PHONE, CUSTOMER_EMAIL, CUSTOMER_REMARK) VALUES(?,?,?,?,?,?,?,?,?,?)', (Name, Address, Area, City, State, Country, Pincode, Phone, Email, Remark))       
                Factory.Okay().open()
                Create().MEGACONNECTOR()
                self.dismiss()
                break'''
        con1.commit()
        con1.close()

class Nameerror(Popup):
    pass

class CustLabel(Label):
    pass

class Management(ScreenManager):
    
    #def transistor(self):
    #    self.add_widget(Create())
    #    self.current = 'Details'
    #    print('Hello')
    pass

class CustomLabel(Label):
    pass

class CustomButton(BubbleButton):

    def reload(self):#instance):
        print(self.id)
        global instincator
        instincator = self.id

class CustomerButton(BubbleButton):

    def reload(self):#instance):
        print(self.id)
        print('deleted')
        global instincation
        instincation = self.id  
        print(instincation)  
    #pass
class Okay(Popup):
    #miaow = CustomPopup()
    pass

class Dropper(ActionDropDown):
    BIGTHING= 'CName'
    def changefield(self):
        #print(self.ids['ID'].state)
        if self.ids['ID'].state == 'down':
            #global BIGTHING
            self.BIGTHING = 'CID'
            #global bigger
            #bigger = self.BIGTHING
            print(self.BIGTHING)    
        elif self.ids['Name'].state == 'down':
            #global BIGTHING
            self.BIGTHING = 'CName'
            print(self.BIGTHING)            
        elif self.ids['City'].state == 'down':
            #global BIGTHING
            self.BIGTHING = 'CCity'
            print(self.BIGTHING)            
        elif self.ids['Phone'].state == 'down':
            #global BIGTHING
            self.BIGTHING = 'CPhone'
            print(self.BIGTHING)
        global MANYTHING
        MANYTHING = self.BIGTHING            

class EditLabel(Label):
    pass

class EditTextInput(TextInput):
    pass

class Reqbutton(Button):
    pass

class Reqbutton1(Reqbutton):
    pass

class Reqbutton2(Reqbutton):
    pass

class ViewPopup(Popup):

    def popy(self):
        connector = sqlite3.connect(r"C:\KIT\DATABASE\KIT_DATABASE.db")
        cursorobject = connector.cursor()
        cursorobject.execute('SELECT CUSTOMER_NAME, CUSTOMER_ADDRESS, CUSTOMER_AREA, CUSTOMER_CITY, CUSTOMER_STATE, CUSTOMER_COUNTRY, CUSTOMER_PINCODE, CUSTOMER_PHONE, CUSTOMER_EMAIL, CUSTOMER_REMARK, DATE FROM customers WHERE CUSTOMER_ID=?', (instincator,))
        row = cursorobject.fetchone()
        l1 = EditLabel(text='[color=000000]Name[/color] [color=0000ff][b]\u2022[/b][/color]', markup= True)
        t1 = Label(text= "[color=000000]"+str(row[0])+"[/color]", markup=True)#, write_tab= False)#, id= text1)
        l2 = EditLabel(text='[color=000000]Address[/color] [color=0000ff][b]\u2022[/b][/color]', markup= True)
        t2 = Label(text= "[color=000000]"+str(row[1])+"[/color]", markup=True)#, write_tab= False)#, id= text2)
        l3 = EditLabel(text='[color=000000]Area[/color] [color=0000ff][b]\u2022[/b][/color]', markup= True)
        t3 = Label(text= "[color=000000]"+str(row[2])+"[/color]", markup=True)#, write_tab= False)#, id= text3)
        l4 = EditLabel(text='[color=000000]City[/color] [color=0000ff][b]\u2022[/b][/color]', markup= True)
        t4 = Label(text= "[color=000000]"+str(row[3])+"[/color]", markup=True)#, write_tab= False)#, id= text4)
        l5 = EditLabel(text='[color=000000]State[/color] [color=0000ff][b]\u2022[/b][/color]', markup= True)
        t5 = Label(text= "[color=000000]"+str(row[4])+"[/color]", markup=True)#, write_tab= False)#, id= text5)
        l6 = EditLabel(text='[color=000000]Country[/color] [color=0000ff][b]\u2022[/b][/color]', markup= True)
        t6 = Label(text= "[color=000000]"+str(row[5])+"[/color]", markup=True)#, write_tab= False)#, id= text6)
        l7 = EditLabel(text='[color=000000]Pincode[/color] [color=0000ff][b]\u2022[/b][/color]', markup= True)
        t7 = Label(text= "[color=000000]"+str(row[6])+"[/color]", markup=True)#, write_tab= False)#, id= text7)
        l8 = EditLabel(text='[color=000000]Phone[/color] [color=0000ff][b]\u2022[/b][/color]', markup= True)
        t8 = Label(text= "[color=000000]"+str(row[7])+"[/color]", markup=True)#, write_tab= False)#, id= text8)
        l9 = EditLabel(text='[color=000000]Email[/color] [color=0000ff][b]\u2022[/b][/color]', markup= True)
        t9 = Label(text= "[color=000000]"+str(row[8])+"[/color]", markup=True)#, write_tab= False)#, id= text9)
        l10 = EditLabel(text= '[color=000000]Remark[/color] [color=0000ff][b]\u2022[/b][/color]', markup= True)
        t10 = Label(text= "[color=000000]"+str(row[9])+"[/color]", markup=True)#, write_tab= False)
        d1 = EditLabel(text= '[color=000000]Date Created[/color] [color=0000ff][b]\u2022[/b][/color]', markup= True)
        d2 = EditLabel(text= "[color=000000]"+str(row[10])+"[/color]",markup=True)
        l11 = EditLabel()
        l12 = EditLabel()
        #l13 = EditLabel()
        #l14 = EditLabel()
        #l15 = EditLabel()
        #l16 = EditLabel()
        #griddy = GridLayout(cols=2)
        #b1 = Reqbutton1(text= 'Submit')
        b2 = Reqbutton2(text= 'Close')
        #b1.bind(on_press= lambda x:self.edit(t1.text,t2.text,t3.text,t4.text,t5.text,t6.text,t7.text,t8.text,t9.text,t10.text))                                                                
        #b1.bind(on_release= lambda x:self.closeit())
        b2.bind(on_press= lambda x:self.dismiss())
        #griddy.add_widget(b1)
        #griddy.add_widget(b2)
        self.editgrid.add_widget(l1)
        self.editgrid.add_widget(t1)
        self.editgrid.add_widget(l2)
        self.editgrid.add_widget(t2)
        self.editgrid.add_widget(l3)
        self.editgrid.add_widget(t3)
        self.editgrid.add_widget(l4)
        self.editgrid.add_widget(t4)
        self.editgrid.add_widget(l5)
        self.editgrid.add_widget(t5)
        self.editgrid.add_widget(l6)
        self.editgrid.add_widget(t6)
        self.editgrid.add_widget(l7)
        self.editgrid.add_widget(t7)
        self.editgrid.add_widget(l8)
        self.editgrid.add_widget(t8)
        self.editgrid.add_widget(l9)
        self.editgrid.add_widget(t9)
        self.editgrid.add_widget(l10)
        self.editgrid.add_widget(t10)
        self.editgrid.add_widget(d1)
        self.editgrid.add_widget(d2)
        self.editgrid.add_widget(l11)
        self.editgrid.add_widget(l12)
        #self.editgrid.add_widget(b2)
        #self.editgrid.add_widget(l13)
        #self.editgrid.add_widget(b1)
        self.editgrid2.add_widget(b2)
        #self.editgrid2.add_widget(l13)
        #self.editgrid2.add_widget(l14)
        #self.editgrid2.add_widget(l15)
        #self.editgrid2.add_widget(l16)
        #self.editgrid2.add_widget(b1)
        print('Completed' + str(row) +instincator)
        connector.commit()
        connector.close()
        #Create().MEGACONNECTOR()
        #return self.editgrid
        self.open()     

class EditPopup(Popup):

    def popy(self):
        connector = sqlite3.connect(r"C:\KIT\DATABASE\KIT_DATABASE.db")
        cursorobject = connector.cursor()
        cursorobject.execute('SELECT CUSTOMER_NAME, CUSTOMER_ADDRESS, CUSTOMER_AREA, CUSTOMER_CITY, CUSTOMER_STATE, CUSTOMER_COUNTRY, CUSTOMER_PINCODE, CUSTOMER_PHONE, CUSTOMER_EMAIL, CUSTOMER_REMARK, DATE FROM customers WHERE CUSTOMER_ID=?', (instincator,))
        row = cursorobject.fetchone()
        l1 = EditLabel(text='[color=000000]Name[/color] [color=0000ff][b]\u2022[/b][/color]', markup= True)
        t1 = EditTextInput(text= str(row[0]), write_tab= False)#, id= text1)
        l2 = EditLabel(text='[color=000000]Address[/color] [color=0000ff][b]\u2022[/b][/color]', markup= True)
        t2 = EditTextInput(text= str(row[1]), write_tab= False)#, id= text2)
        l3 = EditLabel(text='[color=000000]Area[/color] [color=0000ff][b]\u2022[/b][/color]', markup= True)
        t3 = EditTextInput(text= str(row[2]), write_tab= False)#, id= text3)
        l4 = EditLabel(text='[color=000000]City[/color] [color=0000ff][b]\u2022[/b][/color]', markup= True)
        t4 = EditTextInput(text= str(row[3]), write_tab= False)#, id= text4)
        l5 = EditLabel(text='[color=000000]State[/color] [color=0000ff][b]\u2022[/b][/color]', markup= True)
        t5 = EditTextInput(text= str(row[4]), write_tab= False)#, id= text5)
        l6 = EditLabel(text='[color=000000]Country[/color] [color=0000ff][b]\u2022[/b][/color]', markup= True)
        t6 = EditTextInput(text= str(row[5]), write_tab= False)#, id= text6)
        l7 = EditLabel(text='[color=000000]Pincode[/color] [color=0000ff][b]\u2022[/b][/color]', markup= True)
        t7 = EditTextInput(text= str(row[6]), write_tab= False)#, id= text7)
        l8 = EditLabel(text='[color=000000]Phone[/color] [color=0000ff][b]\u2022[/b][/color]', markup= True)
        t8 = EditTextInput(text= str(row[7]), write_tab= False)#, id= text8)
        l9 = EditLabel(text='[color=000000]Email[/color] [color=0000ff][b]\u2022[/b][/color]', markup= True)
        t9 = EditTextInput(text= str(row[8]), write_tab= False)#, id= text9)
        l10 = EditLabel(text= '[color=000000]Remark[/color] [color=0000ff][b]\u2022[/b][/color]', markup= True)
        t10 = EditTextInput(text= str(row[9]), write_tab= False)
        d1 = EditLabel(text= '[color=000000]Date\nCreated[/color] [color=0000ff][b]\u2022[/b][/color]', markup= True)
        d2 = EditLabel(text= "[color=000000]"+str(row[10])+"[/color]",markup=True)
        l11 = EditLabel()
        l12 = EditLabel()
        l13 = EditLabel()
        l14 = EditLabel()
        l15 = EditLabel()
        l16 = EditLabel()
        #griddy = GridLayout(cols=2)
        b1 = Reqbutton1(text= 'Submit')
        b2 = Reqbutton2(text= 'Close')
        b1.bind(on_press= lambda x:self.edit(t1.text,t2.text,t3.text,t4.text,t5.text,t6.text,t7.text,t8.text,t9.text,t10.text))                                                                
        #b1.bind(on_release= lambda x:self.closeit())
        b2.bind(on_press= lambda x:self.dismiss())
        #griddy.add_widget(b1)
        #griddy.add_widget(b2)
        self.editgrid.add_widget(l1)
        self.editgrid.add_widget(t1)
        self.editgrid.add_widget(l2)
        self.editgrid.add_widget(t2)
        self.editgrid.add_widget(l3)
        self.editgrid.add_widget(t3)
        self.editgrid.add_widget(l4)
        self.editgrid.add_widget(t4)
        self.editgrid.add_widget(l5)
        self.editgrid.add_widget(t5)
        self.editgrid.add_widget(l6)
        self.editgrid.add_widget(t6)
        self.editgrid.add_widget(l7)
        self.editgrid.add_widget(t7)
        self.editgrid.add_widget(l8)
        self.editgrid.add_widget(t8)
        self.editgrid.add_widget(l9)
        self.editgrid.add_widget(t9)
        self.editgrid.add_widget(l10)
        self.editgrid.add_widget(t10)
        self.editgrid.add_widget(d1)
        self.editgrid.add_widget(d2)
        self.editgrid.add_widget(l11)
        self.editgrid.add_widget(l12)
        #self.editgrid.add_widget(b2)
        #self.editgrid.add_widget(l13)
        #self.editgrid.add_widget(b1)
        self.editgrid2.add_widget(b2)
        self.editgrid2.add_widget(l13)
        self.editgrid2.add_widget(l14)
        self.editgrid2.add_widget(l15)
        self.editgrid2.add_widget(l16)
        self.editgrid2.add_widget(b1)
        print('Completed' + str(row) +instincator)
        connector.commit()
        connector.close()
        #Create().MEGACONNECTOR()
        #return self.editgrid
        self.open()    

    def edit(self, Name, Address, Area, City, State, Country, Pincode, Phone, Email, Remark):
        con3 = sqlite3.connect(r"C:\KIT\DATABASE\KIT_DATABASE.db")
        cursorObj3 = con3.cursor()
        cursorObj3.execute('SELECT CUSTOMER_PHONE FROM customers WHERE CUSTOMER_PHONE = ?',(str(Phone),))
        #names = cursorObj3.fetchall()
        
        #if len(names) == 1
        #for name in names:
        #    if str(Phone) == str(name[0]):
        #        print('exists')
        #        Factory.Nameerror().open()
        #        break
        #    else:    
        #        #cursorObj1.execute('INSERT INTO customers(CUSTOMER_NAME, CUSTOMER_ADDRESS, CUSTOMER_AREA, CUSTOMER_CITY, CUSTOMER_STATE, CUSTOMER_COUNTRY, CUSTOMER_PINCODE, CUSTOMER_PHONE, CUSTOMER_EMAIL, CUSTOMER_REMARK) VALUES(?,?,?,?,?,?,?,?,?,?)', (Name, Address, Area, City, State, Country, Pincode, Phone, Email, Remark))       
         #       cursorObj3.execute('UPDATE customers SET CUSTOMER_NAME = ?, CUSTOMER_ADDRESS = ?, CUSTOMER_AREA = ?, CUSTOMER_CITY = ?, CUSTOMER_STATE = ?, CUSTOMER_COUNTRY = ?, CUSTOMER_PINCODE = ?, CUSTOMER_PHONE = ?, CUSTOMER_EMAIL = ? WHERE CUSTOMER_ID = ?',(Name, Address, Area, City, State, Country, Pincode, Phone, Email, instincator))
                #Factory.Okay().open()
                #Create().MEGACONNECTOR()
         #       self.dismiss()
         #       break           
        cursorObj3.execute('UPDATE customers SET CUSTOMER_NAME = ?, CUSTOMER_ADDRESS = ?, CUSTOMER_AREA = ?, CUSTOMER_CITY = ?, CUSTOMER_STATE = ?, CUSTOMER_COUNTRY = ?, CUSTOMER_PINCODE = ?, CUSTOMER_PHONE = ?, CUSTOMER_EMAIL = ?, CUSTOMER_REMARK = ? WHERE CUSTOMER_ID = ?',(Name, Address, Area, City, State, Country, Pincode, Phone, Email, Remark, instincator))
        con3.commit()
        #Create().MEGACONNECTOR()
        #nest_edit(con3)
        con3.close() 
        self.dismiss()
        Okay().open()

    def closeit(self):
        self.dismiss()
        Okay().open()       

class EditUser(Popup):

    switchstate = BooleanProperty(False)
    adminswitchstate = BooleanProperty(False)

    def activateuser(self, instance, value):
        print(value)
        #print(instance)
        NEWCONNECTION = sqlite3.connect(r"C:\KIT\DATABASE\KIT_DATABASE.db")
        NEWCURSOR = NEWCONNECTION.cursor()
        TRULY = True
        FALSLY = False
        if value == True:
            NEWCURSOR.execute('UPDATE login SET ACTIVE = ? WHERE USER_ID = ?',(str(TRULY),str(newinstincation))) 
            print("ACTIVATED")
            print(str(TRULY))
        else:
            NEWCURSOR.execute('UPDATE login SET ACTIVE = ? WHERE USER_ID = ?',(str(FALSLY),str(newinstincation))) 
            print("DEACTIVATED")
            print(str(FALSLY))  
        NEWCONNECTION.commit()
        NEWCONNECTION.close()   

    def activateadmin(self, instance, value):
        print(value)
        #print(instance)
        NEWCONNECTION = sqlite3.connect(r"C:\KIT\DATABASE\KIT_DATABASE.db")
        NEWCURSOR = NEWCONNECTION.cursor()
        TRULY = True
        FALSLY = False
        if value == True:
            NEWCURSOR.execute('UPDATE login SET ADMIN = ? WHERE USER_ID = ?',(str(TRULY),str(newinstincation))) 
            print("ADMIN ACTIVATED")
            print(str(TRULY))
        else:
            NEWCURSOR.execute('UPDATE login SET ADMIN = ? WHERE USER_ID = ?',(str(FALSLY),str(newinstincation))) 
            print("ADMIN DEACTIVATED")
            print(str(FALSLY))  
        NEWCONNECTION.commit()
        NEWCONNECTION.close()   

    def popy(self):
        connector = sqlite3.connect(r"C:\KIT\DATABASE\KIT_DATABASE.db")
        cursorobject = connector.cursor()
        cursorobject.execute("SELECT USER_ID, FIRSTNAME, LASTNAME, EMAIL, MOBILE, CITY, ACTIVE, ADMIN FROM login WHERE USER_ID=?",(instincator,))
        #cursorobject.execute('SELECT CUSTOMER_NAME, CUSTOMER_ADDRESS, CUSTOMER_AREA, CUSTOMER_CITY, CUSTOMER_STATE, CUSTOMER_COUNTRY, CUSTOMER_PINCODE, CUSTOMER_PHONE, CUSTOMER_EMAIL, CUSTOMER_REMARK FROM customers WHERE CUSTOMER_ID=?', (instincator,))
        row = cursorobject.fetchone()
        if str(row[6]) == "True":
            self.switchstate = True   
        else:
            self.switchstate = False 
        print(row)   
        if str(row[7]) == "True":
            self.adminswitchstate = True
        else:
            self.adminswitchstate = False     
        l1 = EditLabel(text='[color=000000]First Name[/color] [color=0000ff][b]\u2022[/b][/color]', markup= True)
        t1 = EditTextInput(text= str(row[1]), write_tab= False)#, id= text1)
        l2 = EditLabel(text='[color=000000]Last Name[/color] [color=0000ff][b]\u2022[/b][/color]', markup= True)
        t2 = EditTextInput(text= str(row[2]), write_tab= False)#, id= text2)
        l3 = EditLabel(text='[color=000000]Email[/color] [color=0000ff][b]\u2022[/b][/color]', markup= True)
        t3 = EditTextInput(text= str(row[3]), write_tab= False)#, id= text3)
        l4 = EditLabel(text='[color=000000]Mobile[/color] [color=0000ff][b]\u2022[/b][/color]', markup= True)
        t4 = EditTextInput(text= str(row[4]), write_tab= False)#, id= text4)
        l5 = EditLabel(text='[color=000000]City[/color] [color=0000ff][b]\u2022[/b][/color]', markup= True)
        t5 = EditTextInput(text= str(row[5]), write_tab= False)#, id= text5)
        sl1= EditLabel(text='[color=000000]Active[/color] [color=0000ff][b]\u2022[/b][/color]', markup= True)
        sl2 = EditLabel(text='[color=000000]Admin[/color] [color=0000ff][b]\u2022[/b][/color]', markup= True)
        s1 = Switcher(id=str(row[0]), active= self.switchstate)
        print(str(s1.active)+" is the state")
        s2 = Switcher(id=str(row[0]), active= self.adminswitchstate)
        print(str(s2.active)+" is the admin state") 
        s1.bind(active=Switcher.reload)  
        s1.bind(active=self.activateuser)
        s2.bind(active=Switcher.reload)  
        s2.bind(active=self.activateadmin)        
        #l6 = EditLabel(text='[color=000000]Country[/color] [color=0000ff][b]\u2022[/b][/color]', markup= True)
        #t6 = EditTextInput(text= str(row[5]), write_tab= False)#, id= text6)
        #l7 = EditLabel(text='[color=000000]Pincode[/color] [color=0000ff][b]\u2022[/b][/color]', markup= True)
        #t7 = EditTextInput(text= str(row[6]), write_tab= False)#, id= text7)
        #l8 = EditLabel(text='[color=000000]Phone[/color] [color=0000ff][b]\u2022[/b][/color]', markup= True)
        #t8 = EditTextInput(text= str(row[7]), write_tab= False)#, id= text8)
        #l9 = EditLabel(text='[color=000000]Email[/color] [color=0000ff][b]\u2022[/b][/color]', markup= True)
        #t9 = EditTextInput(text= str(row[8]), write_tab= False)#, id= text9)
        #l10 = EditLabel(text= '[color=000000]Remark[/color] [color=0000ff][b]\u2022[/b][/color]', markup= True)
        #t10 = EditTextInput(text= str(row[9]), write_tab= False)
        l11 = EditLabel()
        l12 = EditLabel()
        l13 = EditLabel()
        l14 = EditLabel()
        l15 = EditLabel()
        l16 = EditLabel()
        #griddy = GridLayout(cols=2)
        b1 = Reqbutton1(text= 'Submit')
        b2 = Reqbutton2(text= 'Close')
        b1.bind(on_press= lambda x:self.edit(t1.text,t2.text,t3.text,t4.text,t5.text,s1.active,s2.active))#,t6.text,t7.text,t8.text,t9.text,t10.text))                                                                
        #b1.bind(on_release= lambda x:self.closeit())
        b2.bind(on_press= lambda x:self.dismiss())
        #griddy.add_widget(b1)
        #griddy.add_widget(b2)
        self.editgrid.add_widget(l1)
        self.editgrid.add_widget(t1)
        self.editgrid.add_widget(l2)
        self.editgrid.add_widget(t2)
        self.editgrid.add_widget(l3)
        self.editgrid.add_widget(t3)
        self.editgrid.add_widget(l4)
        self.editgrid.add_widget(t4)
        self.editgrid.add_widget(l5)
        self.editgrid.add_widget(t5)
        self.editgrid.add_widget(sl1)
        self.editgrid.add_widget(s1)
        self.editgrid.add_widget(sl2)
        self.editgrid.add_widget(s2)
        #self.editgrid.add_widget(l8)
        #self.editgrid.add_widget(t8)
        ##self.editgrid.add_widget(l9)
        #self.editgrid.add_widget(t9)
        #self.editgrid.add_widget(l10)
        #self.editgrid.add_widget(t10)
        self.editgrid.add_widget(l11)
        self.editgrid.add_widget(l12)
        #self.editgrid.add_widget(b2)
        #self.editgrid.add_widget(l13)
        #self.editgrid.add_widget(b1)
        self.editgrid2.add_widget(b2)
        self.editgrid2.add_widget(l13)
        self.editgrid2.add_widget(l14)
        self.editgrid2.add_widget(l15)
        self.editgrid2.add_widget(l16)
        self.editgrid2.add_widget(b1)
        print('Completed' + str(row) +instincator)
        connector.commit()
        connector.close()
        #Create().MEGACONNECTOR()
        #return self.editgrid
        self.open()    

    def edit(self, FIRSTNAME, LASTNAME, EMAIL, MOBILE, CITY, ACTIVE, ADMIN):
        con3 = sqlite3.connect(r"C:\KIT\DATABASE\KIT_DATABASE.db")
        cursorObj3 = con3.cursor()
        #cursorObj3.execute("SELECT MOBILE FROM login WHERE MOBILE=?",(str(MOBILE)))
        #cursorObj3.execute('SELECT CUSTOMER_PHONE FROM customers WHERE CUSTOMER_PHONE = ?',(str(Phone),))
        #names = cursorObj3.fetchall()
        
        #if len(names) == 1
        #for name in names:
        #    if str(Phone) == str(name[0]):
        #        print('exists')
        #        Factory.Nameerror().open()
        #        break
        #    else:    
        #        #cursorObj1.execute('INSERT INTO customers(CUSTOMER_NAME, CUSTOMER_ADDRESS, CUSTOMER_AREA, CUSTOMER_CITY, CUSTOMER_STATE, CUSTOMER_COUNTRY, CUSTOMER_PINCODE, CUSTOMER_PHONE, CUSTOMER_EMAIL, CUSTOMER_REMARK) VALUES(?,?,?,?,?,?,?,?,?,?)', (Name, Address, Area, City, State, Country, Pincode, Phone, Email, Remark))       
         #       cursorObj3.execute('UPDATE customers SET CUSTOMER_NAME = ?, CUSTOMER_ADDRESS = ?, CUSTOMER_AREA = ?, CUSTOMER_CITY = ?, CUSTOMER_STATE = ?, CUSTOMER_COUNTRY = ?, CUSTOMER_PINCODE = ?, CUSTOMER_PHONE = ?, CUSTOMER_EMAIL = ? WHERE CUSTOMER_ID = ?',(Name, Address, Area, City, State, Country, Pincode, Phone, Email, instincator))
                #Factory.Okay().open()
                #Create().MEGACONNECTOR()
         #       self.dismiss()
         #       break  
        cursorObj3.execute("UPDATE login SET FIRSTNAME = ?, LASTNAME = ?, EMAIL = ?, MOBILE = ?, CITY = ?, ACTIVE = ?, ADMIN = ? WHERE USER_ID = ?",(str(FIRSTNAME), str(LASTNAME), str(EMAIL), str(MOBILE), str(CITY), str(ACTIVE), str(ADMIN), str(instincator)))         
        #cursorObj3.execute('UPDATE customers SET CUSTOMER_NAME = ?, CUSTOMER_ADDRESS = ?, CUSTOMER_AREA = ?, CUSTOMER_CITY = ?, CUSTOMER_STATE = ?, CUSTOMER_COUNTRY = ?, CUSTOMER_PINCODE = ?, CUSTOMER_PHONE = ?, CUSTOMER_EMAIL = ?, CUSTOMER_REMARK = ? WHERE CUSTOMER_ID = ?',(Name, Address, Area, City, State, Country, Pincode, Phone, Email, Remark, instincator))
        con3.commit()
        #Create().MEGACONNECTOR()
        #nest_edit(con3)
        con3.close() 
        self.dismiss()
        Okay().open()

    def closeit(self):
        self.dismiss()
        Okay().open() 
        
class DeletePopup(Popup):
    def delete(self):
        con7 = sqlite3.connect(r"C:\KIT\DATABASE\KIT_DATABASE.db")     
        #CustomerButton().delreload
        def nest_delete(con7):
            cursorObj7 = con7.cursor()
            cursorObj7.execute('DELETE FROM customers WHERE CUSTOMER_ID = ?',(instincation,))
            con7.commit()
            #Create().MEGACONNECTOR(mytexty="")
        nest_delete(con7)
        con7.close() 

class Loading_Screen(Screen):

    def switch(self, *args):
        self.parent.current = "Loggerhead"

    def on_enter(self, *args):
        Clock.schedule_once(self.switch,1)

class DeleteUser(Popup):
    def delete(self):
        con7 = sqlite3.connect(r"C:\KIT\DATABASE\KIT_DATABASE.db")     
        #CustomerButton().delreload
        def nest_delete(con7):
            cursorObj7 = con7.cursor()
            cursorObj7.execute('DELETE FROM login WHERE USER_ID = ?',(instincation,))
            con7.commit()
            #Create().MEGACONNECTOR(mytexty="")
        nest_delete(con7)
        con7.close() 

class CustomerLabel(Label):
    pass

class CheckButton(CheckBox):
    
    def activating_button(self):
        print(int(self.id))

    #def activater_behaviour(self, ID):
    #    print(str(ID))

    def get_check(self):
        lite = sqlite3.connect(r"C:\KIT\DATABASE\KIT_DATABASE.db")
        con = lite.cursor()
        con.execute("SELECT CUSTOMER_ID, CUSTOMER_NAME, CUSTOMER_PHONE FROM customers")
        global cun
        cun = con.fetchall()
        lite.commit()
        lite.close()
        print(str(cun))

    def activate_behaviour(self, identifire):
        #print(str(identifire) + " thus") 
        #print(self.id + " This")
        #print(1)
        lite = sqlite3.connect(r"C:\KIT\DATABASE\KIT_DATABASE.db")
        kan = lite.cursor()
        #print(2)
        kan.execute("SELECT CUSTOMER_NAME, CUSTOMER_PHONE FROM customers WHERE CUSTOMER_ID = ?",(self.id,))
        kall = kan.fetchone()
        #print(str(kall) + "--->This is It")
        #print(3)
        if identifire == True:
            MediaScreen().CHECKLIST.append(self.id)
            #print(str(MediaScreen().CHECKLIST))
            #for k in kall:
            MediaScreen().NameList.append(kall[0])
            MediaScreen().NumberList.append(kall[1])
            #print(4)        
        elif identifire == False:
            #print(5)
            if self.id in MediaScreen().CHECKLIST:
                #print(6)
                MediaScreen().CHECKLIST.remove(self.id)
                #print(7)
                #for k in kall:
                #print(8)
                if str(kall[0]) in MediaScreen().NameList:
                    #print(9) 
                    #print(kall[0])
                    #print(str(kall[0]))
                    if str(kall[1]) in MediaScreen().NumberList:
                        #print(kall[1])
                        #print(str(kall[1]))
                        #print(10)
                        MediaScreen().NameList.remove(str(kall[0]))
                        MediaScreen().NumberList.remove(str(kall[1]))                    
                    elif int(kall[1]) in MediaScreen().NumberList:
                        MediaScreen().NameList.remove(str(kall[0]))
                        MediaScreen().NumberList.remove(int(kall[1]))
                        #print(11)
            #print(str(MediaScreen().CHECKLIST))    
            #print(str(MediaScreen().NameList))
            #print(str(MediaScreen().NumberList))
            lite.commit()
            lite.close()

class Switcher(Switch):

    def reload(self, instance):#instance):
        print(self.id)
        print('switched')
        global newinstincation
        newinstincation = self.id  
        print(newinstincation)  

class WhatsAppSender(Popup):
    DocList = []
    def send_message(self):
        driver = webdriver.Chrome(r'C:\Users\girija\Downloads\chromedriver_win32\chromedriver.exe')
        ignored_exceptions=(NoSuchElementException,StaleElementReferenceException)
        driver.get("https://web.whatsapp.com/")
        #driver.get_cookies()
        wait = WebDriverWait(driver, 600, ignored_exceptions=ignored_exceptions)
        if len(self.DocList) != 0:
            for target in MediaScreen().NameList:
                targ = str('"'+target+'"')
                x_arg = '//span[contains(@title,' + targ + ')]'
                group_title = wait.until(EC.presence_of_element_located((By.XPATH, x_arg)))
                print (group_title)
                print ("Wait for few seconds")
                time.sleep(2)
                group_title.click()
                #message = driver.find_elements_by_xpath('//*[@id="main"]/footer/div[1]/div[2]/div/div[2]')[0]
                butt = driver.find_element_by_css_selector("span[data-icon='clip']")
                time.sleep(1)
                butt.click()
                time.sleep(2)
                nbutt = driver.find_element_by_css_selector("input[type='file']")
                time.sleep(1)
                for docs in self.DocList:
                    n = str(docs).replace("[","")
                    ne = n.replace("]","")
                    new = ne.replace("'","")
                    print(new)
                    nbutt.send_keys(new)
                time.sleep(1)
                #nwbutt = driver.find_element_by_xpath("//div[contains(@class, 'yavlE')]")
                nwbutt = driver.find_element_by_css_selector("span[data-icon='send']")
                time.sleep(1)
                nwbutt.click()
                time.sleep(2)
                print("IT IS DONE BRO")            
                driver.close()
        else:
            messager = str(self.ids["message_text"].text)
            for t in MediaScreen().NameList:
                print(str(MediaScreen().NameList))
                targ = str('"'+t+'"')
                print(targ)
                x_arg = '//span[contains(@title,' + targ + ')]'
                group_title = wait.until(EC.presence_of_element_located((By.XPATH, x_arg)))
                print (group_title)
                print ("Wait for few seconds")
                time.sleep(2)
                group_title.click()
                message = driver.find_elements_by_xpath('//*[@id="main"]/footer/div[1]/div[2]/div/div[2]')[0]
                message.send_keys(messager)
                sendbutton = driver.find_elements_by_xpath('//*[@id="main"]/footer/div[1]/div[3]/button')[0]
                sendbutton.click()
                time.sleep(2)
                ##driver.close()
                print("DONE BRO!!!")
                driver.close()                    

class MediaScreen(Screen):

    CHECKLIST = []
    NumberList = []
    NameList = []
    def check_all(self):
        con = sqlite3.connect(r"C:\KIT\DATABASE\KIT_DATABASE.db")
        cur = con.cursor()
        cur.execute("SELECT CUSTOMER_ID, CUSTOMER_NAME, CUSTOMER_PHONE FROM customers")
        checklist = cur.fetchall()
        for c in checklist:
            nstr = str(c[0]).replace("(","")
            netsr = nstr.replace(",)","")
            self.CHECKLIST.append(netsr)
            self.NameList.append(c[1])
            self.NumberList.append(c[2])
        print(str(self.NumberList))
        print(str(self.NameList))    
        print(str(self.CHECKLIST))
        con.commit()
        con.close()

    def check_all_checkbutton(self):
        con = sqlite3.connect(r"C:\KIT\DATABASE\KIT_DATABASE.db")
        cur = con.cursor()
        cur.execute("SELECT CUSTOMER_ID FROM customers")
        checklist = cur.fetchall()
        s = self.ids
        print(str(s))
        print(str(self.grid.children))
        #for x in checklist:        
        #    nstr = str(x).replace("(","")
        #    netsr = nstr.replace(",)","")
        #    n = str(int(netsr))
        #    checker = self.ids[n]
        #    checker.active()
        con.commit()
        con.close()    
    def uncheck_all(self):
        if len(self.CHECKLIST) != 0:
            self.CHECKLIST.clear()

    def send_via_whatsapp(self):
        WhatsAppSender().open()
        #print("IT'S WORKING")

    #TEXT = StringProperty(MyText)
    r = speech_recognition.Recognizer()

    #def SpeakText(command):
    #    engine = pyttsx3.init()
    #    engine.say(command)
    #    engine.runAndWait()

    def openurl(self):
        webbrowser.open("www.karthikinformationtechnology.com")

    def speaker(self):
        microphone = self.ids['mic'].state
        on = 'down'
        textmac = self.ids['searcher']
        if microphone == on:
            try:
                with speech_recognition.Microphone() as source2:
                    print("Speak Now")
                    self.r.adjust_for_ambient_noise(source2, duration=0.2)
                    audio2 = self.r.listen(source2)
                    global MyText
                    MyText = self.r.recognize_google(audio2)
                    MyText = MyText.lower()
                    #if MyText == 'hello python':
                    #    print('hello hari')
                    #elif MyText == 'get lost':
                    #    print('I am sorry that i was not so good')
                    #    print(exit())    
                    print("Speak!!!")
                    print("Did you say "+MyText)
                    #self.SpeakText(MyText)
                    self.search(MyText)
                    textmac.text = MyText
            except speech_recognition.RequestError as e:
                print("Could not request results; {0}".format(e))
            except speech_recognition.UnknownValueError:
                print("Unknown error occured")   

    def open_popup(self):
        the_popup = CustomPopup()
        the_popup.open()

    def search(self, searchit):
        #searchit = self.ids['searcher'].text
        #if str(searchit) 
        if str(searchit).lower() == 'all':
            self.grid.clear_widgets()
            for row in MEGAROWS:
                l1 = CustomerLabel(text= str(row[0]))
                l2 = CustomLabel(text= str(row[1]))
                l3 = CustomLabel(text= str(row[2]))
                l4 = CustomLabel(text= str(row[3]))
                #b2 = CustomerButton(text= 'Delete', id = str(row[0]))
                #b2.bind(on_press= CustomerButton.reload)                
                #b2.bind(on_release= lambda x:DeletePopup().open())                                
                #b1 = CustomButton(text='Edit', id= str(row[0]))
                #b1.bind(on_release= lambda x:EditPopup().popy())
                #b1.bind(on_press= CustomButton.reload)
                b1 = CustomButton(text="View", id=str(row[0]))
                b1.bind(on_press= CustomButton.reload)
                b1.bind(on_release= lambda x:ViewPopup().popy())
                self.grid.add_widget(l1)
                self.grid.add_widget(l2)
                self.grid.add_widget(l3)
                self.grid.add_widget(l4)
                self.grid.add_widget(b1)
                b2 =  CheckButton(id=str(row[0]))                
                self.grid.add_widget(b2)                                
            MEGACON.commit()
        #elif not(str(searchit) and str(searchit).strip()):
        #    labella = Label(text= 'Nothing Found')
        #    self.grid.clear_widgets()
        #    self.grid.add_widget(labella)
        else:
            if MANYTHING == 'CID':
                lister = []  
                for x in MEGAROWS:
                    if str(x[0]) == str(searchit):
                        lister.append(x)    
                for i in lister:
                    if i != ():
                        self.grid.clear_widgets()                                
                for row in lister:
                    l1 = CustomerLabel(text= str(row[0]))
                    l2 = CustomLabel(text= str(row[1]))
                    l3 = CustomLabel(text= str(row[2]))
                    l4 = CustomLabel(text= str(row[3]))
                    #b1 = CustomButton(text='Edit', id= str(row[0]))
                    #b1.bind(on_release= lambda x:EditPopup().popy())
                    #b2 = CustomerButton(text= 'Delete', id= str(row[0]))
                    #b1.bind(on_release= lambda x:EditPopup().popy())
                    #b1.bind(on_press= CustomButton.reload)
                    #b2.bind(on_release= lambda x:DeletePopup().open())
                    #b2.bind(on_press= CustomerButton.reload)
                    b1 = CustomButton(text="View", id=str(row[0]))
                    b1.bind(on_press= CustomButton.reload)
                    b1.bind(on_release= lambda x:ViewPopup().popy())                    
                    self.grid.add_widget(l1)
                    self.grid.add_widget(l2)
                    self.grid.add_widget(l3)
                    self.grid.add_widget(l4)
                    self.grid.add_widget(b1)
                    b2 =  CheckButton(id=str(row[0]))                
                    self.grid.add_widget(b2)
                    #self.grid.add_widget(b2)                                          
                MEGACON.commit()
            elif MANYTHING == 'CName':
                lister = []  
                for x in MEGAROWS:
                    if str(x[1]).lower().startswith(str(searchit).lower()):
                        lister.append(x)
                for i in lister:
                    if i != ():
                        self.grid.clear_widgets()                                
                for row in lister:
                    l1 = CustomerLabel(text= str(row[0]))
                    l2 = CustomLabel(text= str(row[1]))
                    l3 = CustomLabel(text= str(row[2]))
                    l4 = CustomLabel(text= str(row[3]))
                    #b1 = CustomButton(text='Edit', id= str(row[0]))
                    #b2 = CustomerButton(text= 'Delete', id= str(row[0]))
                    #b1.bind(on_release= lambda x:EditPopup().popy())
                    #b1.bind(on_press= CustomButton.reload)
                    #b2.bind(on_release= lambda x:DeletePopup().open())
                    #b2.bind(on_press= CustomerButton.reload)
                    b1 = CustomButton(text="View", id=str(row[0]))
                    b1.bind(on_press= CustomButton.reload)
                    b1.bind(on_release= lambda x:ViewPopup().popy())  
                    self.grid.add_widget(l1)
                    self.grid.add_widget(l2)
                    self.grid.add_widget(l3)
                    self.grid.add_widget(l4)
                    self.grid.add_widget(b1)
                    b2 =  CheckButton(id=str(row[0]))                
                    self.grid.add_widget(b2)
                    #self.grid.add_widget(b2)                                          
                MEGACON.commit()  
            elif MANYTHING == 'CCity':
                lister = []  
                for x in MEGAROWS:
                    if str(x[2]).lower().startswith(str(searchit).lower()):
                        lister.append(x)
                for i in lister:
                    if i != ():
                        self.grid.clear_widgets()                                
                for row in lister:
                    l1 = CustomerLabel(text= str(row[0]))
                    l2 = CustomLabel(text= str(row[1]))
                    l3 = CustomLabel(text= str(row[2]))
                    l4 = CustomLabel(text= str(row[3]))
                    #b1 = CustomButton(text='Edit', id= str(row[0]))
                    #b2 = CustomerButton(text= 'Delete', id= str(row[0]))
                    #b1.bind(on_release= lambda x:EditPopup().popy())
                    #b1.bind(on_press= CustomButton.reload)
                    #b2.bind(on_release= lambda x:DeletePopup().open())
                    #b2.bind(on_press= CustomerButton.reload)
                    b1 = CustomButton(text="View", id=str(row[0]))
                    b1.bind(on_press= CustomButton.reload)
                    b1.bind(on_release= lambda x:ViewPopup().popy())  
                    self.grid.add_widget(l1)
                    self.grid.add_widget(l2)
                    self.grid.add_widget(l3)
                    self.grid.add_widget(l4)
                    self.grid.add_widget(b1)
                    b2 =  CheckButton(id=str(row[0]))                
                    self.grid.add_widget(b2)
                    #self.grid.add_widget(b2)                                          
                MEGACON.commit()
            elif MANYTHING == 'CPhone':
                lister = []  
                for x in MEGAROWS:
                    if str(x[3]).lower().startswith(str(searchit).lower()):
                        lister.append(x)
                for i in lister:
                    if i != ():
                        self.grid.clear_widgets()                                
                for row in lister:
                    l1 = CustomerLabel(text= str(row[0]))
                    l2 = CustomLabel(text= str(row[1]))
                    l3 = CustomLabel(text= str(row[2]))
                    l4 = CustomLabel(text= str(row[3]))
                    #b1 = CustomButton(text='Edit', id= str(row[0]))
                    #b2 = CustomerButton(text= 'Delete', id= str(row[0]))
                    #b1.bind(on_release= lambda x:EditPopup().popy())
                    #b1.bind(on_press= CustomButton.reload)
                    #b2.bind(on_release= lambda x:DeletePopup().open())
                    #b2.bind(on_press= CustomerButton.reload)
                    b1 = CustomButton(text="View", id=str(row[0]))
                    b1.bind(on_press= CustomButton.reload)
                    b1.bind(on_release= lambda x:ViewPopup().popy())  
                    self.grid.add_widget(l1)
                    self.grid.add_widget(l2)
                    self.grid.add_widget(l3)
                    self.grid.add_widget(l4)
                    self.grid.add_widget(b1)
                    b2 =  CheckButton(id=str(row[0]))                
                    self.grid.add_widget(b2)
                    #self.grid.add_widget(b2)                                          
                MEGACON.commit()             

class Filer(Popup):
    
    def load(self, selection):
        #print(str(path)+"----"+str(selection))
        WhatsAppSender().DocList.append(r"%s"%str(selection))
        time.sleep(0.1)
        print(str(WhatsAppSender().DocList))
        self.dismiss()

class UsersPopUp(Screen):

    #def __init__(self, *args, **kwargs):
        #super(Create, self).__init__(*args, **kwargs)
        #self.GETUSERS()  

    #def deleteuser(self):
    #switchstate = BooleanProperty(False)
    #adminswitchstate = BooleanProperty(False)                  
    
    def GETUSERS(self):
        #CONNECTION = sqlite3.connect(r"C:\hariharan\Arduino_programs\h_customer.db")
        CONNECTION  = sqlite3.connect(r"C:\KIT\DATABASE\KIT_DATABASE.db")
        CURSOR = CONNECTION.cursor()
        CURSOR.execute('SELECT USER_ID, FIRSTNAME, LASTNAME, EMAIL, MOBILE, ACTIVE FROM login WHERE USER_ID != 1')
        rwer = CURSOR.fetchall()
        print("USER DONE")
        if len(self.gridder.children) != 0:
            self.gridder.clear_widgets()
            print(str(len(self.gridder.children))+' cleared children')
        #for row in rwer:
        #    print(str(row[5])+' state')             
        #    if str(row[5]) == "True":
        #        self.switchstate == True  
                #print(str(row[5])+' state')    

        for rw in rwer:
            #l0 = Label(text=str('hello'))
            l1 = CustomLabel(text=str(rw[1]))
            l2 = CustomLabel(text=str(rw[2]))
            l3 = CustomLabel(text=str(rw[3]))
            l4 = CustomLabel(text=str(rw[4]))
            #l5 = CustomLabel(text=str(rw[5]))
            #l6 = CustomLabel(text=str(rw[6]))
            #if str(rw[5]) == "True":
            #    self.switchstate = True   
            #else:
            #    self.switchstate = False               
            #s1 = Switcher(id=str(rw[0]), active= self.switchstate)
            #print(str(s1.active)+" is the state")
            #s2 = Switcher(id=str(rw[0]), active=self.adminswitchstate)
            #print(str(s2.active)+" is the state")            
            b1 = CustomButton(text="Edit", id=str(rw[0]))
            b2 = CustomerButton(text="Delete", id=str(rw[0]))
            #b1.bind(on_release= lambda x:EditPopup().popy())
            b1.bind(on_release= lambda x:EditUser().popy())
            b1.bind(on_press= CustomButton.reload)
            b2.bind(on_press= CustomerButton.reload)                
            b2.bind(on_release= lambda x:DeleteUser().open())              
            #s1.bind(active=Switcher.reload)  
            #s1.bind(active=self.activateuser)          
            #s1.active = self.switchstate
            #s1.bind(active=self.switchstate)
            #self.gridder.clear_widgets()
            self.gridder.add_widget(l1)
            self.gridder.add_widget(l2)
            self.gridder.add_widget(l3)
            self.gridder.add_widget(l4)
            #self.gridder.add_widget(l5)
            #self.gridder.add_widget(l6)
            #self.gridder.add_widget(s1)
            self.gridder.add_widget(b1)
            self.gridder.add_widget(b2)
            #self.gridder.
            print(str(len(self.gridder.children))+' children')
            #print(str(self.gridder.children))
        CONNECTION.commit()
        CONNECTION.close()
        #self.open()

class LoadDialog(FloatLayout):
    load = ObjectProperty(None)
    cancel = ObjectProperty(None)


class SaveDialog(FloatLayout):
    save = ObjectProperty(None)
    text_input = ObjectProperty(None)
    cancel = ObjectProperty(None)

class File_DropDown(ActionDropDown):
    loadfile = ObjectProperty(None)
    savefile = ObjectProperty(None)
    text_input = ObjectProperty(None)

    def create_comma_separated_value(self):
        myconnection = sqlite3.connect(r"C:\KIT\DATABASE\KIT_DATABASE.db")
        mycursor = myconnection.cursor()
        mycursor.execute("SELECT CUSTOMER_ID, CUSTOMER_NAME, CUSTOMER_ADDRESS, CUSTOMER_AREA, CUSTOMER_CITY, CUSTOMER_STATE, CUSTOMER_COUNTRY, CUSTOMER_PINCODE, CUSTOMER_PHONE, CUSTOMER_EMAIL, CUSTOMER_REMARK, DATE FROM customers")
        csvWriter = csv.writer(open(r"C:\hariharan\Arduino_programs\output.csv", "w+"))
        rows = mycursor.fetchall()
        l = ["ID", "Name", "Address", "Area", "City", "State", "Country", "Pincode", "Phone", "Email", "Remark", "Date"]
        csvWriter.writerow(l)
        csvWriter.writerows(rows)

    def dismiss_popup(self):
        self._popup.dismiss()

    def show_load(self):
        content = LoadDialog(load=self.load, cancel=self.dismiss_popup)
        self._popup = Popup(title="Load file", content=content,
                            size_hint=(0.9, 0.9))
        self._popup.open()

    def show_save(self):
        content = SaveDialog(save=self.save, cancel=self.dismiss_popup)
        self._popup = Popup(title="Save file", content=content,
                            size_hint=(None, None), size=(600, 500))
        self._popup.open()

    def load(self, path, filename):
        with open(os.path.join(path, filename[0])) as stream:
            self.text_input.text = stream.read()

        self.dismiss_popup()

    def save(self, path, filename):
        newpath = str(path)+"\\"+str(filename)+".csv"
        with open(newpath, "w+") as stream:
            print(newpath)
            myconnection = sqlite3.connect(r"C:\KIT\DATABASE\KIT_DATABASE.db")
            mycursor = myconnection.cursor()
            mycursor.execute("SELECT CUSTOMER_ID, CUSTOMER_NAME, CUSTOMER_ADDRESS, CUSTOMER_AREA, CUSTOMER_CITY, CUSTOMER_STATE, CUSTOMER_COUNTRY, CUSTOMER_PINCODE, CUSTOMER_PHONE, CUSTOMER_EMAIL, CUSTOMER_REMARK, DATE FROM customers")
            csvWriter = csv.writer(open(newpath, "w"))#(r"C:\hariharan\Arduino_programs\output.csv", "w+"))
            rows = mycursor.fetchall()
            l = ["ID", "Name", "Address", "Area", "City", "State", "Country", "Pincode", "Phone", "Email", "Remark", "Date"]
            csvWriter.writerow(l)
            csvWriter.writerows(rows)
            myconnection.commit()
            myconnection.close()
            #stream
            #stream.write(self.text_input.text)

        self.dismiss_popup()

class DataManager():
    def MEGACONNECTOR(self):
        global MEGACON
        #MEGACON = sqlite3.connect(r"C:\hariharan\Arduino_programs\h_customer.db") 
        MEGACON = sqlite3.connect(r"C:\KIT\DATABASE\KIT_DATABASE.db")
        MEGACURSOR = MEGACON.cursor()
        MEGACURSOR.execute('SELECT CUSTOMER_ID, CUSTOMER_NAME, CUSTOMER_CITY, CUSTOMER_PHONE FROM customers')
        global MEGAROWS 
        MEGAROWS = MEGACURSOR.fetchall()
        #searchfield = self.ids['searcher']
        #searchfield.text = str(mytexty)

class Admin(Screen):

    loadfile = ObjectProperty(None)
    savefile = ObjectProperty(None)
    text_input = ObjectProperty(None)

    def dismiss_popup(self):
        self._popup.dismiss()

    def show_load(self):
        content = LoadDialog(load=self.load, cancel=self.dismiss_popup)
        self._popup = Popup(title="Load file", content=content,
                            size_hint=(0.9, 0.9))
        self._popup.open()

    def show_save(self):
        content = SaveDialog(save=self.save, cancel=self.dismiss_popup)
        self._popup = Popup(title="Save file", content=content,
                            size_hint=(0.9, 0.9))
        self._popup.open()

    def load(self, path, filename):
        with open(os.path.join(path, filename[0])) as stream:
            self.text_input.text = stream.read()

        self.dismiss_popup()

    def save(self, path, filename):
        newpath = str(path)+"\\"+str(filename)+".csv"
        with open(newpath, "w+") as stream:
            print(newpath)
            myconnection = sqlite3.connect(r"C:\KIT\DATABASE\KIT_DATABASE.db")
            mycursor = myconnection.cursor()
            mycursor.execute("SELECT CUSTOMER_ID, CUSTOMER_NAME, CUSTOMER_ADDRESS, CUSTOMER_AREA, CUSTOMER_CITY, CUSTOMER_STATE, CUSTOMER_COUNTRY, CUSTOMER_PINCODE, CUSTOMER_PHONE, CUSTOMER_EMAIL, CUSTOMER_REMARK, DATE FROM customers")
            csvWriter = csv.writer(open(newpath, "w"))#(r"C:\hariharan\Arduino_programs\output.csv", "w+"))
            rows = mycursor.fetchall()
            l = ["ID", "Name", "Address", "Area", "City", "State", "Country", "Pincode", "Phone", "Email", "Remark", "Date"]
            csvWriter.writerow(l)
            csvWriter.writerows(rows)
            myconnection.commit()
            myconnection.close()
        self.dismiss_popup()
    #def save(self, path, filename):
    #    with open(os.path.join(path, filename), 'w') as stream:
    #        stream.write(self.text_input.text)

    #    self.dismiss_popup()

    #TEXT = StringProperty(MyText)
    r = speech_recognition.Recognizer()

    #def SpeakText(command):
    #    engine = pyttsx3.init()
    #    engine.say(command)
    #    engine.runAndWait()



    def plotgraph(self):
        GraphScreen().graphplotter()
    
    def openurl(self):
        webbrowser.open("www.karthikinformationtechnology.com")

    #def MEGACONNECTOR(self, mytexty):
    #    global MEGACON
        #MEGACON = sqlite3.connect(r"C:\hariharan\Arduino_programs\h_customer.db") 
    #    MEGACON = sqlite3.connect(r"C:\KIT\DATABASE\KIT_DATABASE.db")
    #    MEGACURSOR = MEGACON.cursor()
    #    MEGACURSOR.execute('SELECT CUSTOMER_ID, CUSTOMER_NAME, CUSTOMER_CITY, CUSTOMER_PHONE FROM customers')
    #    global MEGAROWS 
    #    MEGAROWS = MEGACURSOR.fetchall()
    #    searchfield = self.ids['searcher']
    #    searchfield.text = str(mytexty)
        #self.search(mytexty)
    #def __init__(self, *args, **kwargs):
    #    super(Create, self).__init__(*args, **kwargs)
        #self.dropdown = Dropper()
    #    self.MEGACONNECTOR()
        #self.search()
    #    Dropper().changefield()
    #    Database_maker().file_maker()
    #    Database_maker().table_maker()
       #self.closepop()
        #self.search()
#class Butt(Butt)
#    def file_maker(self):
#        Directory = pathlib.Path("C:\KIT\DATABASE")
#        if not Directory.exists():
#            print('No chance')

    #def getusers(self):
    #    UsersPopUp().GETUSERS()

    def speaker(self):
        microphone = self.ids['mic'].state
        on = 'down'
        textmac = self.ids['searcher']
        if microphone == on:
            try:
                with speech_recognition.Microphone() as source2:
                    print("Speak Now")
                    self.r.adjust_for_ambient_noise(source2, duration=0.2)
                    audio2 = self.r.listen(source2)
                    global MyText
                    MyText = self.r.recognize_google(audio2)
                    MyText = MyText.lower()
                    #if MyText == 'hello python':
                    #    print('hello hari')
                    #elif MyText == 'get lost':
                    #    print('I am sorry that i was not so good')
                    #    print(exit())    
                    print("Speak!!!")
                    print("Did you say "+MyText)
                    #self.SpeakText(MyText)
                    self.search(MyText)
                    textmac.text = MyText
            except speech_recognition.RequestError as e:
                print("Could not request results; {0}".format(e))
            except speech_recognition.UnknownValueError:
                print("Unknown error occured")   

    def open_popup(self):
        the_popup = CustomPopup()
        the_popup.open()
    
    '''def searcher(self,searchit):
        if str(searchit).lower() == "all":
            self.grid.clear_widgets()
            for row in MEGAROWS:
                #TableRow().datatuple = str(row)
                r0 = row[0]
                r1 = row[1]
                r2 = row[2]
                r3 = row[3]
                ROW = TableRow(r0, r1, r2, r3)
                self.grid.add_widget(ROW)
                print("dRow")
                print(str(self.grid.children))
                print(str(TableRow))
        else:
            if MANYTHING == 'CID':
                lister = []  
                for x in MEGAROWS:
                    if str(x[0]) == str(searchit):
                        lister.append(x)    
                for i in lister:
                    if i != ():
                        self.grid.clear_widgets()
                for row in lister:
                    r0 = row[0]
                    r1 = row[1]
                    r2 = row[2]
                    r3 = row[3]
                    ROW = TableRow(r0, r1, r2, r3)
                    self.grid.add_widget(ROW)
                    print("dRowid")  
                    print(str(self.grid.children))
                    print(str(TableRow))       
            elif MANYTHING == 'CName':
                lister = []  
                for x in MEGAROWS:
                    if str(x[1]).lower().startswith(str(searchit).lower()):
                        lister.append(x)              
                for i in lister:
                    if i != ():
                        self.grid.clear_widgets()
                for row in lister:
                    r0 = row[0]
                    r1 = row[1]
                    r2 = row[2]
                    r3 = row[3]
                    ROW = TableRow(r0, r1, r2, r3)
                    self.grid.add_widget(ROW)
                    print("dRowname")
                    print(str(self.grid.children))
                    print(str(TableRow))
                    print("This is the real number--->" + str(TableRow.children))
                    #for child in TableRow.children:
                    #    print(str(child.text))
            elif MANYTHING == 'CCity':
                lister = []  
                for x in MEGAROWS:
                    if str(x[2]).lower().startswith(str(searchit).lower()):
                        lister.append(x)
                for i in lister:
                    if i != ():
                        self.grid.clear_widgets()
                for row in lister:
                    r0 = row[0]
                    r1 = row[1]
                    r2 = row[2]
                    r3 = row[3]
                    ROW = TableRow(r0, r1, r2, r3)
                    self.grid.add_widget(ROW)
                    print("dRowcity")
                    print(str(self.grid.children))
                    print(str(TableRow))
            elif MANYTHING == 'CPhone':
                lister = []  
                for x in MEGAROWS:
                    if str(x[3]).lower().startswith(str(searchit).lower()):
                        lister.append(x)
                for i in lister:
                    if i != ():
                        self.grid.clear_widgets()
                for row in lister:
                    r0 = row[0]
                    r1 = row[1]
                    r2 = row[2]
                    r3 = row[3]
                    ROW = TableRow(r0, r1, r2, r3)
                    self.grid.add_widget(ROW)
                    print("dRowphone")
                    print(str(self.grid.children))
                    print(str(TableRow.children))
                     
                    #for child in len(TableRow.children)'''

    def search(self, searchit):
        #searchit = self.ids['searcher'].text
        #if str(searchit) 
        if str(searchit).lower() == 'all':
            self.grid.clear_widgets()
            for row in MEGAROWS:
                l1 = CustomerLabel(text= str(row[0]))
                l2 = CustomLabel(text= str(row[1]))
                l3 = CustomLabel(text= str(row[2]))
                l4 = CustomLabel(text= str(row[3]))
                b2 = CustomerButton(text= 'Delete', id = str(row[0]))
                b2.bind(on_press= CustomerButton.reload)                
                b2.bind(on_release= lambda x:DeletePopup().open())                                
                b1 = CustomButton(text='Edit', id= str(row[0]))
                b1.bind(on_release= lambda x:EditPopup().popy())
                b1.bind(on_press= CustomButton.reload)
                self.grid.add_widget(l1)
                self.grid.add_widget(l2)
                self.grid.add_widget(l3)
                self.grid.add_widget(l4)
                self.grid.add_widget(b1)
                self.grid.add_widget(b2)                                
            MEGACON.commit()
        #elif not(str(searchit) and str(searchit).strip()):
        #    labella = Label(text= 'Nothing Found')
        #    self.grid.clear_widgets()
        #    self.grid.add_widget(labella)
        else:
            if MANYTHING == 'CID':
                lister = []  
                for x in MEGAROWS:
                    if str(x[0]) == str(searchit):
                        lister.append(x)    
                for i in lister:
                    if i != ():
                        self.grid.clear_widgets()                                
                for row in lister:
                    l1 = CustomerLabel(text= str(row[0]))
                    l2 = CustomLabel(text= str(row[1]))
                    l3 = CustomLabel(text= str(row[2]))
                    l4 = CustomLabel(text= str(row[3]))
                    b1 = CustomButton(text='Edit', id= str(row[0]))
                    #b1.bind(on_release= lambda x:EditPopup().popy())
                    b2 = CustomerButton(text= 'Delete', id= str(row[0]))
                    b1.bind(on_release= lambda x:EditPopup().popy())
                    b1.bind(on_press= CustomButton.reload)
                    b2.bind(on_release= lambda x:DeletePopup().open())
                    b2.bind(on_press= CustomerButton.reload)
                    self.grid.add_widget(l1)
                    self.grid.add_widget(l2)
                    self.grid.add_widget(l3)
                    self.grid.add_widget(l4)
                    self.grid.add_widget(b1)
                    self.grid.add_widget(b2)                                          
                MEGACON.commit()
            elif MANYTHING == 'CName':
                lister = []  
                for x in MEGAROWS:
                    if str(x[1]).lower().startswith(str(searchit).lower()):
                        lister.append(x)              
                for i in lister:
                    if i != ():
                        self.grid.clear_widgets()                                
                for row in lister:
                    l1 = CustomerLabel(text= str(row[0]))
                    l2 = CustomLabel(text= str(row[1]))
                    l3 = CustomLabel(text= str(row[2]))
                    l4 = CustomLabel(text= str(row[3]))
                    b1 = CustomButton(text='Edit', id= str(row[0]))
                    b2 = CustomerButton(text= 'Delete', id= str(row[0]))
                    b1.bind(on_release= lambda x:EditPopup().popy())
                    b1.bind(on_press= CustomButton.reload)
                    b2.bind(on_release= lambda x:DeletePopup().open())
                    b2.bind(on_press= CustomerButton.reload)
                    self.grid.add_widget(l1)
                    self.grid.add_widget(l2)
                    self.grid.add_widget(l3)
                    self.grid.add_widget(l4)
                    self.grid.add_widget(b1)
                    self.grid.add_widget(b2)                                          
                MEGACON.commit()  
            elif MANYTHING == 'CCity':
                lister = []  
                for x in MEGAROWS:
                    if str(x[2]).lower().startswith(str(searchit).lower()):
                        lister.append(x)
                for i in lister:
                    if i != ():
                        self.grid.clear_widgets()                                
                for row in lister:
                    l1 = CustomerLabel(text= str(row[0]))
                    l2 = CustomLabel(text= str(row[1]))
                    l3 = CustomLabel(text= str(row[2]))
                    l4 = CustomLabel(text= str(row[3]))
                    b1 = CustomButton(text='Edit', id= str(row[0]))
                    b2 = CustomerButton(text= 'Delete', id= str(row[0]))
                    b1.bind(on_release= lambda x:EditPopup().popy())
                    b1.bind(on_press= CustomButton.reload)
                    b2.bind(on_release= lambda x:DeletePopup().open())
                    b2.bind(on_press= CustomerButton.reload)
                    self.grid.add_widget(l1)
                    self.grid.add_widget(l2)
                    self.grid.add_widget(l3)
                    self.grid.add_widget(l4)
                    self.grid.add_widget(b1)
                    self.grid.add_widget(b2)                                          
                MEGACON.commit()
            elif MANYTHING == 'CPhone':
                lister = []  
                for x in MEGAROWS:
                    if str(x[3]).lower().startswith(str(searchit).lower()):
                        lister.append(x)
                for i in lister:
                    if i != ():
                        self.grid.clear_widgets()                                
                for row in lister:
                    l1 = CustomerLabel(text= str(row[0]))
                    l2 = CustomLabel(text= str(row[1]))
                    l3 = CustomLabel(text= str(row[2]))
                    l4 = CustomLabel(text= str(row[3]))
                    b1 = CustomButton(text='Edit', id= str(row[0]))
                    b2 = CustomerButton(text= 'Delete', id= str(row[0]))
                    b1.bind(on_release= lambda x:EditPopup().popy())
                    b1.bind(on_press= CustomButton.reload)
                    b2.bind(on_release= lambda x:DeletePopup().open())
                    b2.bind(on_press= CustomerButton.reload)
                    self.grid.add_widget(l1)
                    self.grid.add_widget(l2)
                    self.grid.add_widget(l3)
                    self.grid.add_widget(l4)
                    self.grid.add_widget(b1)
                    self.grid.add_widget(b2)                                          
                MEGACON.commit() 

class Create(Screen):

    #TEXT = StringProperty(MyText)
    r = speech_recognition.Recognizer()

    #def SpeakText(command):
    #    engine = pyttsx3.init()
    #    engine.say(command)
    #    engine.runAndWait()

    def openurl(self):
        webbrowser.open("www.karthikinformationtechnology.com")

    #def MEGACONNECTOR(self, mytexty):
    #    global MEGACON
    #    #MEGACON = sqlite3.connect(r"C:\hariharan\Arduino_programs\h_customer.db") 
    #    MEGACON = sqlite3.connect(r"C:\KIT\DATABASE\KIT_DATABASE.db")
    #    MEGACURSOR = MEGACON.cursor()
    #    MEGACURSOR.execute('SELECT CUSTOMER_ID, CUSTOMER_NAME, CUSTOMER_CITY, CUSTOMER_PHONE FROM customers')
    #    global MEGAROWS 
    #    MEGAROWS = MEGACURSOR.fetchall()
    #    searchfield = self.ids['searcher']
    #    searchfield.text = str(mytexty)
    #def __init__(self, *args, **kwargs):
    #    super(Create, self).__init__(*args, **kwargs)
        #self.dropdown = Dropper()
    #    self.MEGACONNECTOR()
        #self.search()
    #    Dropper().changefield()
    #    Database_maker().file_maker()
    #    Database_maker().table_maker()
       #self.closepop()
        #self.search()
#class Butt(Butt)
#    def file_maker(self):
#        Directory = pathlib.Path("C:\KIT\DATABASE")
#        if not Directory.exists():
#            print('No chance')

    def speaker(self):
        microphone = self.ids['mic'].state
        on = 'down'
        textmac = self.ids['searcher']
        if microphone == on:
            try:
                with speech_recognition.Microphone() as source2:
                    print("Speak Now")
                    self.r.adjust_for_ambient_noise(source2, duration=0.2)
                    audio2 = self.r.listen(source2)
                    global MyText
                    MyText = self.r.recognize_google(audio2)
                    MyText = MyText.lower()
                    #if MyText == 'hello python':
                    #    print('hello hari')
                    #elif MyText == 'get lost':
                    #    print('I am sorry that i was not so good')
                    #    print(exit())    
                    print("Speak!!!")
                    print("Did you say "+MyText)
                    #self.SpeakText(MyText)
                    self.search(MyText)
                    textmac.text = MyText
            except speech_recognition.RequestError as e:
                print("Could not request results; {0}".format(e))
            except speech_recognition.UnknownValueError:
                print("Unknown error occured")   

    def open_popup(self):
        the_popup = CustomPopup()
        the_popup.open()

    def search(self, searchit):
        #searchit = self.ids['searcher'].text
        #if str(searchit) 
        if str(searchit).lower() == 'all':
            self.grid.clear_widgets()
            for row in MEGAROWS:
                l1 = CustomerLabel(text= str(row[0]))
                l2 = CustomLabel(text= str(row[1]))
                l3 = CustomLabel(text= str(row[2]))
                l4 = CustomLabel(text= str(row[3]))
                #b2 = CustomerButton(text= 'Delete', id = str(row[0]))
                #b2.bind(on_press= CustomerButton.reload)                
                #b2.bind(on_release= lambda x:DeletePopup().open())                                
                #b1 = CustomButton(text='Edit', id= str(row[0]))
                #b1.bind(on_release= lambda x:EditPopup().popy())
                #b1.bind(on_press= CustomButton.reload)
                b1 = CustomButton(text="View", id=str(row[0]))
                b1.bind(on_press= CustomButton.reload)
                b1.bind(on_release= lambda x:ViewPopup().popy())
                self.grid.add_widget(l1)
                self.grid.add_widget(l2)
                self.grid.add_widget(l3)
                self.grid.add_widget(l4)
                self.grid.add_widget(b1)
                #self.grid.add_widget(b2)                                
            MEGACON.commit()
        #elif not(str(searchit) and str(searchit).strip()):
        #    labella = Label(text= 'Nothing Found')
        #    self.grid.clear_widgets()
        #    self.grid.add_widget(labella)
        else:
            if MANYTHING == 'CID':
                lister = []  
                for x in MEGAROWS:
                    if str(x[0]) == str(searchit):
                        lister.append(x)    
                for i in lister:
                    if i != ():
                        self.grid.clear_widgets()                                
                for row in lister:
                    l1 = CustomerLabel(text= str(row[0]))
                    l2 = CustomLabel(text= str(row[1]))
                    l3 = CustomLabel(text= str(row[2]))
                    l4 = CustomLabel(text= str(row[3]))
                    #b1 = CustomButton(text='Edit', id= str(row[0]))
                    #b1.bind(on_release= lambda x:EditPopup().popy())
                    #b2 = CustomerButton(text= 'Delete', id= str(row[0]))
                    #b1.bind(on_release= lambda x:EditPopup().popy())
                    #b1.bind(on_press= CustomButton.reload)
                    #b2.bind(on_release= lambda x:DeletePopup().open())
                    #b2.bind(on_press= CustomerButton.reload)
                    b1 = CustomButton(text="View", id=str(row[0]))
                    b1.bind(on_press= CustomButton.reload)
                    b1.bind(on_release= lambda x:ViewPopup().popy())                    
                    self.grid.add_widget(l1)
                    self.grid.add_widget(l2)
                    self.grid.add_widget(l3)
                    self.grid.add_widget(l4)
                    self.grid.add_widget(b1)
                    #self.grid.add_widget(b2)                                          
                MEGACON.commit()
            elif MANYTHING == 'CName':
                lister = []  
                for x in MEGAROWS:
                    if str(x[1]).lower().startswith(str(searchit).lower()):
                        lister.append(x)
                for i in lister:
                    if i != ():
                        self.grid.clear_widgets()                                
                for row in lister:
                    l1 = CustomerLabel(text= str(row[0]))
                    l2 = CustomLabel(text= str(row[1]))
                    l3 = CustomLabel(text= str(row[2]))
                    l4 = CustomLabel(text= str(row[3]))
                    #b1 = CustomButton(text='Edit', id= str(row[0]))
                    #b2 = CustomerButton(text= 'Delete', id= str(row[0]))
                    #b1.bind(on_release= lambda x:EditPopup().popy())
                    #b1.bind(on_press= CustomButton.reload)
                    #b2.bind(on_release= lambda x:DeletePopup().open())
                    #b2.bind(on_press= CustomerButton.reload)
                    b1 = CustomButton(text="View", id=str(row[0]))
                    b1.bind(on_press= CustomButton.reload)
                    b1.bind(on_release= lambda x:ViewPopup().popy())  
                    self.grid.add_widget(l1)
                    self.grid.add_widget(l2)
                    self.grid.add_widget(l3)
                    self.grid.add_widget(l4)
                    self.grid.add_widget(b1)
                    #self.grid.add_widget(b2)                                          
                MEGACON.commit()  
            elif MANYTHING == 'CCity':
                lister = []  
                for x in MEGAROWS:
                    if str(x[2]).lower().startswith(str(searchit).lower()):
                        lister.append(x)
                for i in lister:
                    if i != ():
                        self.grid.clear_widgets()                                
                for row in lister:
                    l1 = CustomerLabel(text= str(row[0]))
                    l2 = CustomLabel(text= str(row[1]))
                    l3 = CustomLabel(text= str(row[2]))
                    l4 = CustomLabel(text= str(row[3]))
                    #b1 = CustomButton(text='Edit', id= str(row[0]))
                    #b2 = CustomerButton(text= 'Delete', id= str(row[0]))
                    #b1.bind(on_release= lambda x:EditPopup().popy())
                    #b1.bind(on_press= CustomButton.reload)
                    #b2.bind(on_release= lambda x:DeletePopup().open())
                    #b2.bind(on_press= CustomerButton.reload)
                    b1 = CustomButton(text="View", id=str(row[0]))
                    b1.bind(on_press= CustomButton.reload)
                    b1.bind(on_release= lambda x:ViewPopup().popy())  
                    self.grid.add_widget(l1)
                    self.grid.add_widget(l2)
                    self.grid.add_widget(l3)
                    self.grid.add_widget(l4)
                    self.grid.add_widget(b1)
                    #self.grid.add_widget(b2)                                          
                MEGACON.commit()
            elif MANYTHING == 'CPhone':
                lister = []  
                for x in MEGAROWS:
                    if str(x[3]).lower().startswith(str(searchit).lower()):
                        lister.append(x)
                for i in lister:
                    if i != ():
                        self.grid.clear_widgets()                                
                for row in lister:
                    l1 = CustomerLabel(text= str(row[0]))
                    l2 = CustomLabel(text= str(row[1]))
                    l3 = CustomLabel(text= str(row[2]))
                    l4 = CustomLabel(text= str(row[3]))
                    #b1 = CustomButton(text='Edit', id= str(row[0]))
                    #b2 = CustomerButton(text= 'Delete', id= str(row[0]))
                    #b1.bind(on_release= lambda x:EditPopup().popy())
                    #b1.bind(on_press= CustomButton.reload)
                    #b2.bind(on_release= lambda x:DeletePopup().open())
                    #b2.bind(on_press= CustomerButton.reload)
                    b1 = CustomButton(text="View", id=str(row[0]))
                    b1.bind(on_press= CustomButton.reload)
                    b1.bind(on_release= lambda x:ViewPopup().popy())  
                    self.grid.add_widget(l1)
                    self.grid.add_widget(l2)
                    self.grid.add_widget(l3)
                    self.grid.add_widget(l4)
                    self.grid.add_widget(b1)
                    #self.grid.add_widget(b2)                                          
                MEGACON.commit()                                                                                                                                                                                                    

class ClockLabel(ActionLabel):
    def __init__(self, **kwargs):
        super(ClockLabel, self).__init__(**kwargs)
        Clock.schedule_interval(self.update, 1)

    def update(self, *args):
        self.text = time.strftime('%I:%M:%S %p')

class StartDatePicker(CalendarWidget):
    pass

class ActionDatePicker(DatePicker, ActionItem):
    pass

class GraphScreen(Screen):

    #activated_date_cal = CalendarWidget()
    #i = my_activated_button_data
    #startex = str(str(i[0]) + "/" + str(i[1]) + "/" + str(i[2]))#str(date.today)
    startex = date.today()#StringProperty(CalendarWidget().active_date)
    endex = date.today()
    def openstartcalendar(self):
        #StartDatePicker().as_popup = True 
        #StartDatePicker().open()
        STARTCALENDARPOPUP().open()
    #def show_start_calendar(self):
        #DatePicker.show_popup(1, .3)
    def openendcalendar(self):
        ENDCALENDARPOPUP().open()

    def start_cal_text(self):
        #somer = App.get_running_app().graphite.ids['sct']#root.ids["GraphScreen"].sct
        i = my_activated_button_data
        mysct = self.ids['sct']
        self.startex = str(str(i[0]) + "/" + str(i[1]) + "/" + str(i[2]))
        mysct.text = str(str(i[0]) + "/" + str(i[1]) + "/" + str(i[2]))
        print("hello---->"+self.startex)
        print("hi" + mysct.text)
        print(str(mysct))
        print(str(my_activated_button_data))
        #CalendarWidget().get_active_date()
        #print(Calendar_widget().activated_date)
        #print(CalendarWidget().active_date)
    #    start_text= self.activated_date_cal.active_date
    #    print(start_text)

    def end_cal_text(self):
        pass

    def graphplotter(self): 
        connectorwala = sqlite3.connect(r"C:\KIT\DATABASE\KIT_DATABASE.db")   
        cursorwala = connectorwala.cursor()
        cursorwala.execute("SELECT CUSTOMER_ID, DATE FROM customers")
        rowsala = cursorwala.fetchall()
        print(rowsala)
        graph = Graph(xlabel='X', ylabel='Y', x_ticks_minor=5,
        x_ticks_major=25, y_ticks_major=1,
        y_grid_label=True, x_grid_label=True, padding=5,
        x_grid=True, y_grid=True, xmin=-0, xmax=100, ymin=-10, ymax=10)
        plot = MeshLinePlot(color = utils.get_color_from_hex("#8B0000"))  #[1, 0, 0, 1])
        #x = 54
        #for y in rowsala:
        plot.points = [(int(y[0]), int(y[0])) for y in rowsala]
            #print(y[0])
        #plot.points = [(x, x)]
        graph.add_plot(plot)
        self.bowbow.clear_widgets()
        self.bowbow.add_widget(graph)
        print("PLOTTED")
        #return graph

class STARTCALENDARPOPUP(Popup):
    #def call_start_cal(self):
    #    GraphScreen().start_cal_text()
        #lambda x:GraphScreen.start_cal_text    
    pass

class ENDCALENDARPOPUP(Popup):
    pass

root = Builder.load_file(r'customer_form.kv')


class LINKSApp(App):
    some_variable = Create()
    actor = Dropper()
    darkdrop = Dropman()
    #colordropper = ColorDrop()
    popit = UsersPopUp()
    graphite = GraphScreen() 
    startcalendar = STARTCALENDARPOPUP()
    filedrop = File_DropDown()
    dm = DataManager()
    def close(self):
        poper = CustomPopup()
        poper.dismiss()

    #def do_everything(self):
        #self.root = get_main_window()
        #with Login.canvas:
        #    Color(rgba=(.5, .5, .5))
        #    Rectangle(size=Login.size, pos=Login.pos)        
        #Database_maker().file_maker()
        #Database_maker().table_maker()    
        #Database_maker().admin_creater() 
        #UsersPopUp().GETUSERS()
        #DataManager().MEGACONNECTOR()
        #Create().MEGACONNECTOR(mytexty="")
        #Admin().MEGACONNECTOR(mytexty="")        
        #Login().screenimage()
        #LoginPopup().open()
        #self.search()
        #Dropper().changefield()
    def close_all_pops(self):
        if isinstance(App.get_running_app().root_window.children[0], Popup):
            App.get_running_app().root_window.children[0].dismiss()        
    
    def build(self):

        #Database_maker().file_maker()
        #Database_maker().table_maker()    
        #Database_maker().admin_creater()    
        Database_maker().file_maker()
        Database_maker().table_maker()    
        Database_maker().admin_creater()
        DataManager().MEGACONNECTOR()
        Dropper().changefield()
        MediaScreen().check_all()        
        return root
        #LoginPopup().open(print('opener'))        

LINKSApp().run()  
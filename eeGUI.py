import sys
import serial
import equation
import datetime
from ledwidget import LedWidget
import time
import math
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import Qt, pyqtSlot, QObject, pyqtSignal
from PyQt5.QtWidgets import (QApplication, QCheckBox, QGridLayout, QGroupBox, QLabel, QLineEdit, QComboBox, QDoubleSpinBox,
                             QMenu, QPushButton, QRadioButton, QVBoxLayout, QHBoxLayout, QWidget, QSlider, QDial,QSpinBox,
                             QMessageBox)
from PyQt5.QtGui import QPainter, QFont, QColor, QPen

MAX_PHY_PB_MDA  = 70
MAX_PHY_MLA     = 600
MAX_PHY_MDA1    = 3
MAX_PHY_MDA2    = 70
AVAIL_PHY_PB_MDA = 70
AVAIL_PHY_MLA   = 400
AVAIL_PHY_MDA1  = 3
AVAIL_PHY_MDA2  = 70

class QScale(QWidget):
    def __init__(self, maxV, bipolar=True):
        super().__init__()
        self.setMinimumSize(1, 10)
        self.scales = [0,0,0]
        if bipolar:
            self.scales[0] = int(-maxV)
            self.scales[1] = 0
            self.scales[2] = int(maxV)
        else:
            self.scales[0] = 0
            self.scales[1] = int(maxV/2)
            self.scales[2] = int(maxV)        
        
    def paintEvent(self, e):
        qp = QPainter()
        qp.begin(self)
        self.drawWidget(qp)
        qp.end()

    def drawWidget(self, qp):
        font = QFont("Serif", 7, QFont.Light)
        qp.setFont(font)

        size = self.size()
        w = size.width()
        h = size.height()

        metrics = qp.fontMetrics()
        fw1 = metrics.width(str(self.scales[1]))
        fw2 = metrics.width(str(self.scales[-1]))
        positions = [0, w/2-fw1/2, w-fw2]

        for i in range(3):            
            qp.drawText(positions[i], 10, str(self.scales[i]))
       
            
class QDialSlider(QWidget, QObject):
    '''New signals should only be defined in sub-classes of QObject. They must be part of the class definition and
    cannot be dynamically added as class attributes after the class has been defined.'''
    trigger = pyqtSignal()
    
    def __init__(self, name, maxV, bipolar=True, parent=None):
        super(QDialSlider, self).__init__(parent)
        self.overflow = False
        self.value = 0.0
        if(maxV>10):
            self.slider_multi = 10
        else:
            self.slider_multi = 100
        # Object
        self.edit = QDoubleSpinBox()
        self.dial = QDial()
        self.slider = QSlider(Qt.Horizontal)
        self.scale = QScale(maxV, bipolar)
        self.layout = self.CreateGroup(name)
        self.timer = QtCore.QTimer()        
        
        # Property
        self.dial.setRange(-10, 10)
        self.slider.setTickInterval(100)
        self.edit.setSingleStep(0.01)
        self.edit.setDecimals(2)
        if bipolar:
            self.edit.setRange(-maxV, maxV)
            self.slider.setRange(int(-maxV*self.slider_multi), int(maxV*self.slider_multi))
        else:
            self.edit.setRange(0, maxV)
            self.slider.setRange(0, int(maxV*self.slider_multi))
     
        # Event
        self.slider.valueChanged.connect(self.SliderChange)
        self.edit.valueChanged.connect(self.EditChange)
        self.dial.sliderPressed.connect(self.DialPress)
        self.dial.sliderReleased.connect(self.DialRelease)
        self.timer.timeout.connect(self.onTimer)
        
    def setValue(self, dvalue):
        self.value = dvalue
        
    def setOverflow(self):
        self.overflow = True
        
    #layout and style    
    def CreateGroup(self, name):
        self.edit.setFixedSize(98,32)
        self.dial.setFixedSize(80,80)
        #self.slider.setTickInterval(10)
        self.slider.setFocusPolicy(Qt.StrongFocus)
        self.slider.setTickPosition(QSlider.TicksBothSides)

        self.edit.setAlignment(Qt.AlignRight)
        self.edit.setFont(QFont("Arial",16))
        self.edit.setStyleSheet("color: rgb(36,36,36);")
        
        #layout
        hbox1 = QHBoxLayout()        
        hbox1.addWidget(self.dial)
        hbox1.addWidget(self.edit,Qt.AlignCenter)
           
        vbox = QVBoxLayout()
        vbox.addLayout(hbox1)
        vbox.addWidget(self.scale)
        vbox.addWidget(self.slider)        
        
        groupBox = QGroupBox(name) 
        groupBox.setLayout(vbox) 
        return groupBox
    
    @pyqtSlot()
    def SliderChange(self):        
        if(self.slider.hasFocus()): 
            val = self.slider.value()
            self.edit.setValue(val/self.slider_multi)
            #print('SliderChange'+str(val/self.slider_multi))

    @pyqtSlot()
    def EditChange(self):
        val = self.edit.value()
        self.slider.setValue(int(val*self.slider_multi))
        if(self.overflow):
            self.overflow = False
        else:
            self.trigger.emit()
        #print('EditChange'+str(val))

    @pyqtSlot()
    def DialPress(self):
        self.timer.start(100)
        #print('DialPress')
        
    @pyqtSlot()
    def DialRelease(self):
        self.timer.stop()
        self.dial.setValue(0)
        #print('DialRelease') 
        
    def onTimer(self):
        delta = self.dial.value()
        sign = lambda x: math.copysign(1, x)
        delta = sign(delta)*int((10**(abs(delta)/4))-0.5)/100
        self.edit.setValue(self.edit.value()+delta)
        #print('onTimer Fucking '+str(delta))

class QMdaBox(QWidget):
    trigger = pyqtSignal()
    
    def __init__(self, name, maxV, parent=None):
        super(QMdaBox, self).__init__(parent)

        # Object
        self.Vx = QDialSlider('Vx', maxV)
        self.Vy = QDialSlider('Vy', maxV)
        self.check = QCheckBox()
        self.button = QPushButton('SET')
        self.phases = []
        self.layout = self.CreateGroup(self.Vx,self.Vy, name)
        # Property
        # Event
        self.check.stateChanged.connect(self.CheckChange)
        self.button.clicked.connect(self.on_btn_set)
        
    def PhaseGroup(self):
        grid = QGridLayout()
        lable = QLabel('Equ2')
        grid.addWidget(lable, 0, 0)
        grid.addWidget(self.check, 1, 0)
        grid.addWidget(self.button, 1, 9)
        self.button.setMinimumSize(0, 26)
        names = ['P1', 'P2', 'P3','P4', 'P5', 'P6','P7', 'P8']
        for n, name in zip(range(1,9), names):
            label = QLabel(name)
            label.setAlignment(Qt.AlignCenter)
            grid.addWidget(label, 0, n)
            edit = QLineEdit()
            edit.setText('0.0')            
            edit.setMinimumSize(0, 22)
            edit.setAlignment(Qt.AlignHCenter)
            #edit.setFont(QFont("Arial",20))
            self.phases.append(edit)
            grid.addWidget(edit, 1, n)
        return grid
    
    def CreateGroup(self, VxBox, VyBox, name = "MDAx"):
        #VxBox = QMdaBox.SilderGroup(self, "Vx")
        #VyBox = QMdaBox.SilderGroup(self, "Vy")
        Phase = QMdaBox.PhaseGroup(self)
            
        #layout
        hbox1 = QHBoxLayout()        
        hbox1.addWidget(VxBox.layout)
        hbox1.addWidget(VyBox.layout)
        #hbox1.addStretch(1)    

        hbox2 = QHBoxLayout()        
        hbox2.addLayout(Phase)
        hbox2.addStretch(1)
        
        vbox = QVBoxLayout()
        vbox.addLayout(hbox1)
        vbox.addLayout(hbox2)
        vbox.addStretch(1)
        
        groupBox = QGroupBox(name)
        groupBox.setLayout(vbox) 
        return groupBox
    
    @pyqtSlot()        
    def CheckChange(self):
        self.Vx.edit.setValue(0.0)
        self.Vy.edit.setValue(0.0)
        #print("CheckChange")
        
    @pyqtSlot()
    def on_btn_set(self):        
        self.trigger.emit();

class QMlaBox(QWidget):
    trigger = pyqtSignal()
    
    def __init__(self, name, maxV, parent=None):
        super(QMlaBox, self).__init__(parent)

        # Object
        self.SldGroup = QDialSlider('', maxV,  bipolar=False)
        self.button = QPushButton('SET')
        self.button.setMinimumSize(0, 26)
        self.layout = self.CreateGroup(self.SldGroup, name)
        # Property
        # Event
        self.button.clicked.connect(self.on_btn_set)

    def CreateGroup(self, SldGroup, name = "MLA"):
        #layout
        hbox1 = QHBoxLayout()
        hbox1.addStretch(1)
        hbox1.addWidget(self.button)
        
        vbox = QVBoxLayout()
        vbox.addWidget(SldGroup.layout)
        vbox.addLayout(hbox1)
        vbox.addStretch(1)
        
        groupBox = QGroupBox(name)
        groupBox.setLayout(vbox) 
        return groupBox
    
    @pyqtSlot()
    def on_btn_set(self):        
        self.trigger.emit();
        
class Window(QWidget,QObject):
    def __init__(self, parent=None):
        super(Window, self).__init__(parent)

        # serial
        self.comboBox = QComboBox(self)
        self.btnOpen = QPushButton('OPEN', self)        
        self.timer = QtCore.QTimer()
        self.led = LedWidget()

        #body
        self.comm = self.QCommunication()
        self.pb_dma = QMdaBox(name='PB_MDA', maxV=AVAIL_PHY_PB_MDA)
        self.mda1 = QMdaBox(name='MDA1', maxV=AVAIL_PHY_MDA1)
        self.mda2 = QMdaBox(name='MDA2', maxV=AVAIL_PHY_MDA2)
        self.mla = QMlaBox(name='MLA', maxV=AVAIL_PHY_MLA)
        
        #layout
        self.led.setColor(QColor('grey'))
        self.btnOpen.setMinimumSize(0, 26)
        grid = QGridLayout()
        grid.addLayout(self.comm, 0, 0)
        grid.addWidget(self.pb_dma.layout, 1, 0)
        grid.addWidget(self.mda2.layout, 2, 0)
        grid.addWidget(self.mda1.layout, 1, 1)
        grid.addWidget(self.mla.layout, 2, 1)
        self.setLayout(grid)

        self.setWindowTitle("PyQt5 MDCA GUI v1.1 by 123inman@gmail.com")
        self.resize(600, 400)

        #Event
        self.btnOpen.clicked.connect(self.commOpen)
        self.pb_dma.trigger.connect(self.button_trigger_pb_mda)
        self.pb_dma.Vx.trigger.connect(self.slider_trigger_pb_mda)
        self.pb_dma.Vy.trigger.connect(self.slider_trigger_pb_mda)
        self.mda1.trigger.connect(self.button_trigger_mda1)
        self.mda1.Vx.trigger.connect(self.slider_trigger_mda1)
        self.mda1.Vy.trigger.connect(self.slider_trigger_mda1)
        self.mda2.trigger.connect(self.button_trigger_mda2)
        self.mda2.Vx.trigger.connect(self.slider_trigger_mda2)
        self.mda2.Vy.trigger.connect(self.slider_trigger_mda2)
        self.mla.trigger.connect(self.button_trigger_mla)
        self.mla.SldGroup.trigger.connect(self.slider_trigger_mla)
        self.timer.timeout.connect(self.myTimerEvent)

    def QCommunication(self):
        lable = QLabel('Select the connection:')
        coms= self.getSerials()
        for com in coms:
            self.comboBox.addItem(com)            
        #layout
        hbox = QHBoxLayout()
        hbox.addWidget(lable)
        hbox.addWidget(self.comboBox)
        hbox.addWidget(self.btnOpen)
        hbox.addWidget(self.led)
        hbox.addStretch(1)        
        return hbox  

    def getSerials(self):
        serials = []
        for n in range(50):
            name = 'COM'+ str(n+1)    
            try:
                serial.Serial(name, 115200, timeout=0)
            except:
                continue
            serials.append(name);      
        return serials

    @pyqtSlot()        
    def commOpen(self):
        self.comm = self.comboBox.currentText()
        if self.btnOpen.text() == 'OPEN':
            try:
                self.mySerial = serial.Serial(self.comm, 115200, timeout=0)
            except:
                QMessageBox.question(self, 'error', "Fail to open " + self.comm, QMessageBox.Ok, QMessageBox.Ok)
                return
            #if(self.mySerial.is_open):
            self.btnOpen.setText('CLOSE')
            frame = equation.init_reg_all()
            self.send_msg(frame)
            self.timer.start(5)
            self.led.setColor(QColor('green'))
            print(self.comm +' open successfully')
        else:
            self.timer.stop()
            self.btnOpen.setText('OPEN')
            self.mySerial.close()
            self.led.setColor(QColor('grey'))
            print('Comm close!')

    def send_msg(self, msg):
        try:
            self.mySerial.write(msg)
        except:
            #QMessageBox.question(self, 'error', "Please, open COM first", QMessageBox.Ok, QMessageBox.Ok)
            print('error send_msg()!')
            return
        log = datetime.datetime.now().strftime('[%H:%M:%S] ')
        log + "send:"
        log += ''.join('{:02x}'.format(x) for x in msg)
        #self.boxDbg.appendPlainText(log)
        print(log)
        
    def check_phy_phase(self, phases, Vmax):
        for phase in phases:
            if math.fabs(phase)>Vmax:
                return False            
        return True
    
    def trigger_pb_mda(self, prompt=False):
        if self.btnOpen.text() != 'CLOSE':
            if prompt:
                QMessageBox.question(self, 'error', "Please, open COM first", QMessageBox.Ok, QMessageBox.Ok)
            return
        Vx = self.pb_dma.Vx.edit.value();
        Vy = self.pb_dma.Vy.edit.value();
        if(self.pb_dma.check.isChecked()):
            phases = equation.equ2_pb_mda(Vx, Vy)
        else:
            phases = equation.equ_pb_mda(Vx, Vy)

        if(self.check_phy_phase(phases, MAX_PHY_PB_MDA)):
            frame = equation.reg_pb_mda(phases, MAX_PHY_PB_MDA) 
            self.send_msg(frame)
            for n in range(8):
                self.pb_dma.phases[n].setText(str(round(phases[n],2)))
            self.pb_dma.Vx.setValue(Vx)
            self.pb_dma.Vy.setValue(Vy)
        else:
            self.pb_dma.Vx.setOverflow();
            self.pb_dma.Vy.setOverflow();   
            self.pb_dma.Vx.edit.setValue(self.pb_dma.Vx.value)
            self.pb_dma.Vy.edit.setValue(self.pb_dma.Vy.value)            
            
    def trigger_mda1(self, prompt=False):
        if self.btnOpen.text() != 'CLOSE':
            if prompt:
                QMessageBox.question(self, 'error', "Please, open COM first", QMessageBox.Ok, QMessageBox.Ok)
            return
        Vx = self.mda1.Vx.edit.value();
        Vy = self.mda1.Vy.edit.value();
        if(self.mda1.check.isChecked()):
            phases = equation.equ_mda1(Vx, Vy)
        else:
            phases = equation.equ_mda1(Vx, Vy)

        if(self.check_phy_phase(phases, MAX_PHY_MDA1)):
            frame = equation.reg_mda1(phases, MAX_PHY_MDA1) 
            self.send_msg(frame)
            for n in range(4):
                self.mda1.phases[n].setText(str(round(phases[n],2)))
                self.mda1.phases[n+4].setText(str(round(phases[n],2)))
            self.mda1.Vx.setValue(Vx)
            self.mda1.Vy.setValue(Vy)
        else:
            self.mda1.Vx.setOverflow();
            self.mda1.Vy.setOverflow();   
            self.mda1.Vx.edit.setValue(self.mda1.Vx.value)
            self.mda1.Vy.edit.setValue(self.mda1.Vy.value)
            
    def trigger_mda2(self, prompt=False):
        if self.btnOpen.text() != 'CLOSE':
            if prompt:
                QMessageBox.question(self, 'error', "Please, open COM first", QMessageBox.Ok, QMessageBox.Ok)
            return
        Vx = self.mda2.Vx.edit.value();
        Vy = self.mda2.Vy.edit.value();
        if(self.mda2.check.isChecked()):
            phases = equation.equ_mda2(Vx, Vy)
        else:
            phases = equation.equ_mda2(Vx, Vy)

        if(self.check_phy_phase(phases, MAX_PHY_MDA2)):
            frame = equation.reg_mda2(phases, MAX_PHY_MDA2) 
            self.send_msg(frame)
            for n in range(8):
                self.mda2.phases[n].setText(str(round(phases[n],2)))
            self.mda2.Vx.setValue(Vx)
            self.mda2.Vy.setValue(Vy)
        else:
            self.mda2.Vx.setOverflow();
            self.mda2.Vy.setOverflow();   
            self.mda2.Vx.edit.setValue(self.mda2.Vx.value)
            self.mda2.Vy.edit.setValue(self.mda2.Vy.value)

    def trigger_mla(self, prompt=False):
        if self.btnOpen.text() != 'CLOSE':
            if prompt:
                QMessageBox.question(self, 'error', "Please, open COM first", QMessageBox.Ok, QMessageBox.Ok)
            return
      
        value = self.mla.SldGroup.edit.value()
        frame = equation.reg_mla(value, MAX_PHY_MLA)
        self.send_msg(frame)
            
    def slider_trigger_pb_mda(self):
        self.trigger_pb_mda()
        
    def button_trigger_pb_mda(self):
        self.trigger_pb_mda(True)

    def slider_trigger_mda1(self):
        self.trigger_mda1()
        
    def button_trigger_mda1(self):
        self.trigger_mda1((True))

    def slider_trigger_mda2(self):
        self.trigger_mda2()
        
    def button_trigger_mda2(self):
        self.trigger_mda2(True)

    def slider_trigger_mla(self):
        self.trigger_mla()
        
    def button_trigger_mla(self):
        self.trigger_mla(True)

    def myTimerEvent(self):
        readStr = self.mySerial.readline().decode("ascii")
        if(len(readStr)):
            self.led.setColor(QColor('limegreen'))
            log = datetime.datetime.now().strftime('[%H:%M:%S] ')
            log += readStr.rstrip()
            print(log)            
            #self.boxDbg.appendPlainText(str1)
        else:
            self.led.setColor(QColor('green'))
            
if __name__ == '__main__':
    app = QApplication(sys.argv)
    clock = Window()
    clock.show()
    sys.exit(app.exec_())

from PyQt5 import QtCore, QtGui, QtWidgets
from pyqtgraph import PlotWidget, plot
import sys, time, configparser
import numpy as np
import pyqtgraph as pg
import cv2, threading, subprocess

sys.settrace
np.set_printoptions(threshold = sys.maxsize)

config = configparser.ConfigParser()
config.read('config.ini')

shutter = config['default']['shutter'] #max 1,000,000
anolog_gain = config['default']['anolog_gain'] #max 100,000,000
digital_gain = config['default']['digital_gain']
x = config['default']['x']
y = config['default']['y']
deltax = config['default']['deltax']
deltay = config['default']['deltay']
y_axis_max = config['graph']['y_axis_max']

a3 = config['wavelength_calibration']['a3']
a2 = config['wavelength_calibration']['a2']
a1 = config['wavelength_calibration']['a1']
a0 = config['wavelength_calibration']['a0']
e3 = config['wavelength_calibration']['e3']
e2 = config['wavelength_calibration']['e2']
e1 = config['wavelength_calibration']['e1']
e0 = config['wavelength_calibration']['e0']

I_max_config = config['auto_scaling']['I_max']
I_thr_percentage_config = config['auto_scaling']['I_thr_percentage']
I_thr_tolerance_config = config['auto_scaling']['I_thr_tolerance']

numberof_scan_config = config['numof_scan']['numberof_scan']

st_max = 1000000
ag_max = 100000000

st1 = 0
st2 = 0
I1 = 0
I2 = 0
I_max = 0
I_thr_percentage = 0
I_thr_tolerance = 0
I_thr = 0
I_thr_top = 0
I_thr_bottom = 0

mode = 0
auto_mode = 0
y_mode = 0
flag = 0
roi_mode = 0
image_mode = 0
num_scan = numberof_scan_config

wdata = []
max_value = 0
goal_st = 0
new_y0 = 0
numb_ofscan = []

class SignalCommunication(QtCore.QObject):
    new_image = QtCore.pyqtSignal()
    new_y0 = QtCore.pyqtSignal()
    new_data = QtCore.pyqtSignal()
    new_wdata = QtCore.pyqtSignal()
    new_goal_st =  QtCore.pyqtSignal()

class Ui_mainwindow(object):
    def setupUi(self, mainwindow):
        mainwindow.setObjectName("mainwindow")
        mainwindow.resize(831, 650)
        self.centralwidget = QtWidgets.QWidget(mainwindow)
        self.centralwidget.setObjectName("centralwidget")
        self.start = QtWidgets.QPushButton(self.centralwidget)
        self.start.setGeometry(QtCore.QRect(50, 420, 75, 23))
        self.start.setObjectName("start")
        self.format_box = QtWidgets.QComboBox(self.centralwidget)
        self.format_box.setGeometry(QtCore.QRect(220, 20, 69, 22))
        self.format_box.setObjectName("format_box")
        self.format_box.addItem("")
        self.format_box.addItem("")
        self.format_box.addItem("")
        self.shutter_edit = QtWidgets.QLineEdit(self.centralwidget)
        self.shutter_edit.setGeometry(QtCore.QRect(220, 50, 104, 31))
        self.shutter_edit.setObjectName("shutter_edit")
        self.label = QtWidgets.QLabel(self.centralwidget)
        self.label.setGeometry(QtCore.QRect(110, 20, 100, 16))
        self.label.setObjectName("label")
        self.label_2 = QtWidgets.QLabel(self.centralwidget)
        self.label_2.setGeometry(QtCore.QRect(110, 60, 100, 16))
        self.label_2.setObjectName("label_2")
        self.label_3 = QtWidgets.QLabel(self.centralwidget)
        self.label_3.setGeometry(QtCore.QRect(110, 100, 100, 16))
        self.label_3.setObjectName("label_3")
        self.label_4 = QtWidgets.QLabel(self.centralwidget)
        self.label_4.setGeometry(QtCore.QRect(110, 140, 100, 16))
        self.label_4.setObjectName("label_4")
        self.anologgain_edit = QtWidgets.QLineEdit(self.centralwidget)
        self.anologgain_edit.setGeometry(QtCore.QRect(220, 90, 104, 31))
        self.anologgain_edit.setObjectName("anologgain_edit")
        self.digitalgain_edit = QtWidgets.QLineEdit(self.centralwidget)
        self.digitalgain_edit.setGeometry(QtCore.QRect(220, 130, 104, 31))
        self.digitalgain_edit.setObjectName("digitalgain_edit")
        self.label_5 = QtWidgets.QLabel(self.centralwidget)
        self.label_5.setGeometry(QtCore.QRect(60, 180, 150, 16))
        self.label_5.setObjectName("label_5")
        self.x0 = QtWidgets.QLineEdit(self.centralwidget)
        self.x0.setGeometry(QtCore.QRect(200, 170, 50, 31))
        self.x0.setObjectName("x0")
        self.y0 = QtWidgets.QLineEdit(self.centralwidget)
        self.y0.setGeometry(QtCore.QRect(260, 170, 50, 31))
        self.y0.setObjectName("y0")
        self.x1 = QtWidgets.QLineEdit(self.centralwidget)
        self.x1.setGeometry(QtCore.QRect(320, 170, 50, 31))
        self.x1.setObjectName("x1")
        self.y1 = QtWidgets.QLineEdit(self.centralwidget)
        self.y1.setGeometry(QtCore.QRect(380, 170, 50, 31))
        self.y1.setObjectName("y1")
        mainwindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(mainwindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 831, 21))
        self.menubar.setObjectName("menubar")
        mainwindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(mainwindow)
        self.statusbar.setObjectName("statusbar")
        mainwindow.setStatusBar(self.statusbar)
        
        self.pixel_graph = pg.PlotWidget(self.centralwidget)
        self.pixel_graph.setGeometry(QtCore.QRect(140, 420, 300, 200))
        
        self.wavelength_graph = pg.PlotWidget(self.centralwidget)
        self.wavelength_graph.setGeometry(QtCore.QRect(470, 420, 300, 200))
        
        self.image_frame = QtWidgets.QLabel(self.centralwidget)
        self.image_frame.setGeometry(QtCore.QRect(470, 5, 300, 200))
        
        self.continue_checkbox = QtWidgets.QCheckBox('continuous',self.centralwidget)
        self.continue_checkbox.setGeometry(QtCore.QRect(30, 445, 100, 23))
        self.continue_checkbox.setLayoutDirection(QtCore.Qt.RightToLeft)
        
        self.y_axis = QtWidgets.QPushButton(self.centralwidget)
        self.y_axis.setGeometry(QtCore.QRect(50, 470, 75, 23))
        
        self.label_6 = QtWidgets.QLabel(self.centralwidget)
        self.label_6.setGeometry(QtCore.QRect(70, 495, 100, 16))
        self.Yaxis_max = QtWidgets.QLineEdit(self.centralwidget)
        self.Yaxis_max.setGeometry(QtCore.QRect(70, 515, 50, 31))
        
        self.a3_label = QtWidgets.QLabel(self.centralwidget)
        self.a3_label.setGeometry(QtCore.QRect(470, 220, 50, 16))
        self.a2_label = QtWidgets.QLabel(self.centralwidget)
        self.a2_label.setGeometry(QtCore.QRect(470, 260, 50, 16))
        self.a1_label = QtWidgets.QLabel(self.centralwidget)
        self.a1_label.setGeometry(QtCore.QRect(470, 300, 50, 16))
        self.a0_label = QtWidgets.QLabel(self.centralwidget)
        self.a0_label.setGeometry(QtCore.QRect(470, 340, 50, 16))		
        self.a3 = QtWidgets.QLineEdit(self.centralwidget)
        self.a3.setGeometry(QtCore.QRect(500, 210, 80, 30))
        self.a2 = QtWidgets.QLineEdit(self.centralwidget)
        self.a2.setGeometry(QtCore.QRect(500, 250, 80, 30))
        self.a1 = QtWidgets.QLineEdit(self.centralwidget)
        self.a1.setGeometry(QtCore.QRect(500, 290, 80, 30))
        self.a0 = QtWidgets.QLineEdit(self.centralwidget)
        self.a0.setGeometry(QtCore.QRect(500, 330, 80, 30))
        
        self.e3_label = QtWidgets.QLabel(self.centralwidget)
        self.e3_label.setGeometry(QtCore.QRect(590, 220, 50, 16))
        self.e2_label = QtWidgets.QLabel(self.centralwidget)
        self.e2_label.setGeometry(QtCore.QRect(590, 260, 50, 16))
        self.e1_label = QtWidgets.QLabel(self.centralwidget)
        self.e1_label.setGeometry(QtCore.QRect(590, 300, 50, 16))
        self.e0_label = QtWidgets.QLabel(self.centralwidget)
        self.e0_label.setGeometry(QtCore.QRect(590, 340, 50, 16))		
        self.e3 = QtWidgets.QLineEdit(self.centralwidget)
        self.e3.setGeometry(QtCore.QRect(610, 210, 50, 30))
        self.e2 = QtWidgets.QLineEdit(self.centralwidget)
        self.e2.setGeometry(QtCore.QRect(610, 250, 50, 30))
        self.e1 = QtWidgets.QLineEdit(self.centralwidget)
        self.e1.setGeometry(QtCore.QRect(610, 290, 50, 30))
        self.e0 = QtWidgets.QLineEdit(self.centralwidget)
        self.e0.setGeometry(QtCore.QRect(610, 330, 50, 30))
        
        self.max_shutter_label = QtWidgets.QLabel(self.centralwidget)
        self.max_shutter_label.setGeometry(QtCore.QRect(330, 60, 120, 16))		
        self.max_anologgain_label = QtWidgets.QLabel(self.centralwidget)
        self.max_anologgain_label.setGeometry(QtCore.QRect(330, 100, 120, 16))
        self.max_digitalgain_label = QtWidgets.QLabel(self.centralwidget)
        self.max_digitalgain_label.setGeometry(QtCore.QRect(330, 140, 120, 16))
        
        self.auto_roi_label = QtWidgets.QLabel(self.centralwidget)
        self.auto_roi_label.setGeometry(QtCore.QRect(110, 215, 150, 16))
        self.auto_roi = QtWidgets.QPushButton(self.centralwidget)
        self.auto_roi.setGeometry(QtCore.QRect(200, 210, 75, 23))
        
        self.auto_scaling_label = QtWidgets.QLabel(self.centralwidget)
        self.auto_scaling_label.setGeometry(QtCore.QRect(110, 240, 150, 16))
        self.auto_scaling = QtWidgets.QPushButton(self.centralwidget)
        self.auto_scaling.setGeometry(QtCore.QRect(210, 240, 75, 23))
        self.I_max_label = QtWidgets.QLabel(self.centralwidget)
        self.I_max_label.setGeometry(QtCore.QRect(110, 280, 150, 16))
        self.I_thr_percentage_label = QtWidgets.QLabel(self.centralwidget)
        self.I_thr_percentage_label.setGeometry(QtCore.QRect(110, 320, 150, 16))
        self.I_thr_tolerance_label = QtWidgets.QLabel(self.centralwidget)
        self.I_thr_tolerance_label.setGeometry(QtCore.QRect(110, 360, 150, 16))
        self.I_thr_tolerance_label1 = QtWidgets.QLabel(self.centralwidget)
        self.I_thr_tolerance_label1.setGeometry(QtCore.QRect(285, 360, 150, 16))
        
        self.I_max_edit = QtWidgets.QLineEdit(self.centralwidget)
        self.I_max_edit.setGeometry(QtCore.QRect(230, 270, 50, 30))
        self.I_thr_percentage_edit = QtWidgets.QLineEdit(self.centralwidget)
        self.I_thr_percentage_edit.setGeometry(QtCore.QRect(230, 310, 50, 30))
        self.I_thr_tolerance_edit = QtWidgets.QLineEdit(self.centralwidget)
        self.I_thr_tolerance_edit.setGeometry(QtCore.QRect(230, 350, 50, 30))
        
        self.numberof_scan_label = QtWidgets.QLabel(self.centralwidget)
        self.numberof_scan_label.setGeometry(QtCore.QRect(110, 390, 150, 16))
        self.numberof_scan_edit = QtWidgets.QLineEdit(self.centralwidget)
        self.numberof_scan_edit.setGeometry(QtCore.QRect(230, 385, 50, 30))
        
        self.retranslateUi(mainwindow)
        QtCore.QMetaObject.connectSlotsByName(mainwindow)
        
        self.start.clicked.connect(self.start_clicked)
        self.y_axis.clicked.connect(self.y_axis_clicked)	
        self.auto_scaling.clicked.connect(self.auto_scaling_clicked)	
        self.auto_roi.clicked.connect(self.auto_roi_clicked)
        
        self.continue_checkbox.toggled.connect(self.continue_checkbox_check)	
            
        self.Yaxis_max.textChanged[str].connect(self.y_axis_fix)
        self.x0.textChanged[str].connect(self.roi_change)
        self.y0.textChanged[str].connect(self.roi_change)
        self.x1.textChanged[str].connect(self.roi_change)
        self.y1.textChanged[str].connect(self.roi_change)
        self.I_max_edit.textChanged[str].connect(self.auto_scaling_paremeter_change)
        self.I_thr_percentage_edit.textChanged[str].connect(self.auto_scaling_paremeter_change)
        self.I_thr_tolerance_edit.textChanged[str].connect(self.auto_scaling_paremeter_change)
        self.numberof_scan_edit.textChanged[str].connect(self.scan_number_change)
        
        signalComm.new_image.connect(self.update_image)
        signalComm.new_y0.connect(self.update_y0)
        signalComm.new_data.connect(self.update_data)
        signalComm.new_wdata.connect(self.update_wdata)
        signalComm.new_goal_st.connect(self.update_st)
        
        self.x0.setEnabled(False)
        self.y0.setEnabled(False)
        self.x1.setEnabled(False)
        self.Yaxis_max.setEnabled(False)
                
    def retranslateUi(self, mainwindow):
        global I_max, I_thr_percentage, I_thr_tolerance, I_thr, I_thr_top, I_thr_bottom
        
        _translate = QtCore.QCoreApplication.translate
        mainwindow.setWindowTitle(_translate("mainwindow", "test"))
        self.start.setText(_translate("mainwindow", "START"))
        self.format_box.setItemText(0, _translate("mainwindow", "BMP"))
        self.format_box.setItemText(1, _translate("mainwindow", "JPG"))
        self.format_box.setItemText(2, _translate("mainwindow", "RAW"))
        self.label.setText(_translate("mainwindow", "Image Format"))
        self.label_2.setText(_translate("mainwindow", "Shutter"))
        self.label_3.setText(_translate("mainwindow", "Anolog Gain"))
        self.label_4.setText(_translate("mainwindow", "Digital Gain"))
        self.label_5.setText(_translate("mainwindow", "ROI : X0 Y0 X1 Y1"))
        self.y_axis.setText(_translate("mainwindow", "AUTO"))
        self.label_6.setText(_translate("mainwindow", "Y Max"))
        self.a0_label.setText(_translate("mainwindow", "a0"))
        self.a1_label.setText(_translate("mainwindow", "a1"))
        self.a2_label.setText(_translate("mainwindow", "a2"))
        self.a3_label.setText(_translate("mainwindow", "a3"))
        self.e0_label.setText(_translate("mainwindow", "E"))
        self.e1_label.setText(_translate("mainwindow", "E"))
        self.e2_label.setText(_translate("mainwindow", "E"))
        self.e3_label.setText(_translate("mainwindow", "E"))
        self.auto_scaling.setText(_translate("mainwindow", "START"))
        self.max_shutter_label.setText(_translate("mainwindow", "Max: " + str(st_max) + "\u03BCs"))#microseconds
        self.max_anologgain_label.setText(_translate("mainwindow", "Max: " + str(ag_max)))
        self.max_digitalgain_label.setText(_translate("mainwindow", "Not Functioning"))
        self.auto_roi_label.setText(_translate("mainwindow", "ROI Scan"))
        self.auto_roi.setText(_translate("mainwindow", "AUTO"))
        self.auto_scaling_label.setText(_translate("mainwindow", "Auto Scaling"))
        self.I_max_label.setText(_translate("mainwindow", "I Max"))
        self.I_thr_percentage_label.setText(_translate("mainwindow", "Thr percentage"))
        self.I_thr_tolerance_label.setText(_translate("mainwindow", "Thr tolerance"))
        self.numberof_scan_label.setText(_translate("mainwindow", "Num of scan"))
                
        self.shutter_edit.setValidator(QtGui.QIntValidator())
        self.anologgain_edit.setValidator(QtGui.QDoubleValidator())
        self.digitalgain_edit.setValidator(QtGui.QDoubleValidator())
        self.x0.setValidator(QtGui.QIntValidator())
        self.y0.setValidator(QtGui.QIntValidator())
        self.x1.setValidator(QtGui.QIntValidator())
        self.y1.setValidator(QtGui.QIntValidator())
        self.Yaxis_max.setValidator(QtGui.QIntValidator())
        self.a0.setValidator(QtGui.QDoubleValidator())
        self.a1.setValidator(QtGui.QDoubleValidator())
        self.a2.setValidator(QtGui.QDoubleValidator())
        self.a3.setValidator(QtGui.QDoubleValidator())
        self.e0.setValidator(QtGui.QIntValidator())
        self.e1.setValidator(QtGui.QIntValidator())
        self.e2.setValidator(QtGui.QIntValidator())
        self.e3.setValidator(QtGui.QIntValidator())
        self.I_max_edit.setValidator(QtGui.QIntValidator())
        self.I_thr_percentage_edit.setValidator(QtGui.QIntValidator())
        self.I_thr_tolerance_edit.setValidator(QtGui.QIntValidator())
        self.numberof_scan_edit.setValidator(QtGui.QIntValidator())
            
        self.pixel_graph.setBackground('w')
        self.pixel_graph.setLabel('left', 'Intensity')
        self.pixel_graph.setLabel('bottom', 'Pixel')
        self.pixel_graph.setMouseEnabled(x = False, y = False)
        
        self.wavelength_graph.setBackground('w')
        self.wavelength_graph.setLabel('left', 'Intensity')
        self.wavelength_graph.setLabel('bottom', 'Wavelength')
        self.wavelength_graph.setMouseEnabled(x = False, y = False)
        
        grey = QtGui.QPixmap(300,200)
        grey.fill(QtGui.QColor('darkgrey'))
        self.image_frame.setPixmap(grey)
        
        self.shutter_edit.setText(shutter)
        self.anologgain_edit.setText(anolog_gain)
        self.digitalgain_edit.setText(digital_gain)
        self.x0.setText(x)
        self.y0.setText(y)
        self.x1.setText(deltax)
        self.y1.setText(deltay)
        self.Yaxis_max.setText(y_axis_max)
        
        self.a3.setText(a3)
        self.a2.setText(a2)
        self.a1.setText(a1)
        self.a0.setText(a0)
        self.e3.setText(e3)
        self.e2.setText(e2)
        self.e1.setText(e1)
        self.e0.setText(e0)
        
        self.I_max_edit.setText(I_max_config)
        self.I_thr_percentage_edit.setText(I_thr_percentage_config)
        self.I_thr_tolerance_edit.setText(I_thr_tolerance_config)
        
        I_max = int(ui.I_max_edit.text())
        I_thr_percentage = int(ui.I_thr_percentage_edit.text())
        I_thr_tolerance = int(ui.I_thr_tolerance_edit.text())
        I_thr = I_max * I_thr_percentage/100
        I_thr_top = I_thr + I_thr_tolerance
        I_thr_bottom = I_thr - I_thr_tolerance
        self.I_thr_tolerance_label1.setText(_translate("mainwindow", str(I_thr_top) + ' ~ ' + str(I_thr_bottom)))
        
        self.numberof_scan_edit.setText(numberof_scan_config)
        
    def start_clicked(self):
        global mode, flag
        _translate = QtCore.QCoreApplication.translate

        if ui.continue_checkbox.isChecked() == True:
            if flag == 0:
                flag = 1
                self.start.setText(_translate("mainwindow", "STOP"))
            elif flag == 1:
                flag = 0
                self.start.setText(_translate("mainwindow", "START"))
        else:
            flag = 0
            mode = 10
            
        thread1 = threading.Thread(target = thread_1)
        thread1.daemon = True
        thread1.start()
        
    def y_axis_clicked(self):
        global y_mode
        _translate = QtCore.QCoreApplication.translate
        
        if y_mode == 0: 
            yaxis = self.Yaxis_max.text()
            
            self.pixel_graph.setYRange(0, int(yaxis), padding=0)
            self.wavelength_graph.setYRange(0, int(yaxis), padding=0)
            self.y_axis.setText(_translate("mainwindow", "FIX"))
            self.Yaxis_max.setEnabled(True)
            y_mode = 1
        elif y_mode == 1:
            self.pixel_graph.enableAutoRange(axis='y')
            self.wavelength_graph.enableAutoRange(axis='y')
            self.y_axis.setText(_translate("mainwindow", "AUTO"))
            self.Yaxis_max.setEnabled(False)
            y_mode = 0
            
    def auto_scaling_clicked(self):
        global auto_mode
        
        auto_mode = 10
        
        thread2 = threading.Thread(target = thread_2)
        thread2.daemon = True
        thread2.start()
    
    def auto_roi_clicked(self):
        global roi_mode
        _translate = QtCore.QCoreApplication.translate

        if roi_mode == 0:
            self.auto_roi.setText(_translate("mainwindow", "MANUAL"))
            self.x0.setEnabled(True)
            self.y0.setEnabled(True)
            self.x1.setEnabled(True)
            roi_mode = 1
        else:
            self.auto_roi.setText(_translate("mainwindow", "AUTO"))
            self.x0.setEnabled(False)
            self.y0.setEnabled(False)
            self.x1.setEnabled(False)
            roi_mode = 0
            
    def w_cal_button_clicked(self):
        c_ui.c_graph.clear()
        x = np.arange(1, len(data)+1)
        c_ui.c_graph.plot(x, data)
        secondwindow.show()
            
    def continue_checkbox_check(self):
        global flag
        _translate = QtCore.QCoreApplication.translate
        
        if ui.continue_checkbox.isChecked() == False:
            flag = 0
            self.start.setText(_translate("mainwindow", "START"))
                        
    def y_axis_fix(self):
        yaxis = self.Yaxis_max.text()
        self.pixel_graph.setYRange(0, int(yaxis), padding=0)
        self.wavelength_graph.setYRange(0, int(yaxis), padding=0)
    
    def roi_change(self):
        self.update_image_signal()
    
    def auto_scaling_paremeter_change(self):
        _translate = QtCore.QCoreApplication.translate
        
        I_max = int(ui.I_max_edit.text())
        I_thr_percentage = int(ui.I_thr_percentage_edit.text())
        I_thr_tolerance = int(ui.I_thr_tolerance_edit.text())
        I_thr = I_max * I_thr_percentage/100
        I_thr_top = I_thr + I_thr_tolerance
        I_thr_bottom = I_thr - I_thr_tolerance
        self.I_thr_tolerance_label1.setText(_translate("mainwindow", str(I_thr_top) + '~' + str(I_thr_bottom)))
            
    def update_data(self):
        try:
            self.pixel_graph.clear()
            x = np.arange(1,len(data)+1)
            y = data
            self.pixel_graph.plot(x, y)	
            
            return 1
        except Exception as e:
            print('error:{}'.format(e))
            return 0	
    
    def update_wdata(self):
        try:
            self.wavelength_graph.clear()
            x = wdata
            y = data
            self.wavelength_graph.plot(x, y)	
            
            return 1
        except Exception as e:
            print('error:{}'.format(e))
            return 0	
            
    def update_image(self):
        try:
            imgformat = self.format_box.currentText().lower()
            imgpath = "./ttest/test.{}".format(imgformat)
            img = cv2.imread(imgpath)
            img1 = self.draw_roi(img)
            
            h, w, ch= img1.shape
            bytes_per_line = 3 * w
            convert_QT_image = QtGui.QImage(img1.data, w, h, bytes_per_line, QtGui.QImage.Format_RGB888).rgbSwapped()
            p = convert_QT_image.scaled(self.image_frame.frameGeometry().width(), self.image_frame.frameGeometry().height(), QtCore.Qt.KeepAspectRatio)
            self.image_frame.setPixmap(QtGui.QPixmap.fromImage(p))
            
            return 1
        except Exception as e:
            print('error:{}'.format(e))
            return 0
    
    def update_st(self):
        try:
            self.shutter_edit.setText(str(goal_st))
            return 1
        except Exception as e:
            print('error:{}'.format(e))
            return 0
    
    def update_y0(self):
        try:
            self.y0.setText(str(int(new_y0)))
            return 1
        except Exception as e:
            print('error:{}'.format(e))
            return 0
            
    def roi_scan(self):
        global max_value, new_y1
        
        try:
            deltay = int(self.y1.text())
            
            img = cv2.imread("./ttest/test.{}".format(self.format_box.currentText().lower()), cv2.IMREAD_GRAYSCALE)
            a1, a2 = np.where(img == np.amax(img))
            new_y1 = a1[0]-deltay/2
            if new_y1 <= 0:
                new_y1 = 0
            signalComm.new_y0.emit()
            
            return 1
        except Exception as e:
            print('error:{}'.format(e))
            return 0
            
    def draw_roi(self, img):
        x0 = int(self.x0.text())
        y0 = int(self.y0.text())
        deltax = int(self.x1.text())
        deltay = int(self.y1.text())
        x1 = x0 + deltax
        y1 = y0 + deltay
        
        roi_start_point = (x0, y0)
        roi_end_point = (x1, y1)
        roi_color = (255, 0 , 0) #GBR
        thickness = 3
        
        img1 = cv2.rectangle(img, roi_start_point, roi_end_point, roi_color, thickness)
        #cv2.imwrite("img1.bmp", img)
        return img1
                            
    def draw_spectrum_graph_signal(self):
        try:
            signalComm.new_data.emit()
            return 1
        except Exception as e:
            print('error:{}'.format(e))
            return 0	
            
    def draw_wavelength_graph_signal(self):
        try:
            signalComm.new_wdata.emit()
            return 1
        except Exception as e:
            print('error:{}'.format(e))
            return 0	
    
    def draw_both_graph_signal(self):
        try:
            signalComm.new_data.emit()
            signalComm.new_wdata.emit()
            return 1
        except Exception as e:
            print('error:{}'.format(e))
            return 0
    
    def update_shutter_signal(self):
        try:
            signalComm.new_goal_st.emit()
            return 1
        except Exception as e:
            print('error:{}'.format(e))
            return 0
    
    def update_image_signal(self):
        try:
            if image_mode == 1:
                signalComm.new_image.emit()
            return 1
        except Exception as e:
            print('error:{}'.format(e))
            return 0
    
    def update_y0_signal(self):
        try:
            signalComm.new_y0.emit()
            return 1
        except Exception as e:
            print('error:{}'.format(e))
            return 0
    
    def scan_number_change(self):
        global num_scan
        
        num_scan = self.numberof_scan_edit.text()

def takephoto():
    try:
        shutter = ui.shutter_edit.text()
        anolog_gain = ui.anologgain_edit.text()
        digital_gain = ui.digitalgain_edit.text()
        imgformat = ui.format_box.currentText().lower()
        
        imgname = "./ttest/test.{}".format(imgformat)
        subprocess.run(["libcamera-still", "--shutter", shutter, "--analoggain", anolog_gain, "-o", imgname,"--immediate","--nopreview"])
        return 1
    except Exception as e:
        print('error:{}'.format(e))
        return 0	
        
def crop_image():
    global data, max_value
    try:
        imgformat = ui.format_box.currentText().lower()
        sImagePath = "./ttest/test.{}".format(imgformat)
        
        x = int(ui.x0.text())
        y = int(ui.y0.text())
        deltax = int(ui.x1.text())
        deltay = int(ui.y1.text())
        
        nImage = cv2.imread(sImagePath, cv2.IMREAD_GRAYSCALE)
        nCrop_Img = nImage[y:y+deltay, x:x+deltax]

        nColMean = np.mean(nCrop_Img, axis = 0)
        nImgColMean = nColMean.reshape(1, len(nColMean))
        
        data = nImgColMean[0]
        a = np.argmax(data)
        max_value = data[a]
        return 1		
    except Exception as e:
        print('error:{}'.format(e))
        return None	

def sum_image():
    global new_y0
    
    try:
        deltay = int(ui.y1.text())
        
        imgformat = ui.format_box.currentText().lower()
        sImagePath = "./ttest/test.{}".format(imgformat)
        nImage = cv2.imread(sImagePath, cv2.IMREAD_GRAYSCALE)
        #nColSum = np.sum(nImage, axis = 0)
        nRowSum = np.sum(nImage, axis = 1)
        #print(np.argmax(nColSum))
        a = np.argmax(nRowSum)
        new_y0 = a-deltay/2
        if new_y0 <= 0:
            new_y0 = 0
        #ui.y0.setText(str(int(new_y0)))
        signalComm.new_y0.emit()
        return 1
    except Exception as e:
        print('error:{}'.format(e))
        return 0
                
def wavelength_convert():
    global wdata
    wdata.clear()
    try:
        a3 = float(ui.a3.text())*10**(float(ui.e3.text()))
        a2 = float(ui.a2.text())*10**(float(ui.e2.text()))
        a1 = float(ui.a1.text())*10**(float(ui.e1.text()))
        a0 = float(ui.a0.text())*10**(float(ui.e0.text()))
        
        for i in range(len(data)):
            wdata.append((a3*(i**3))+(a2*(i**2))+(a1*i)+ a0)
        
        return 1
    except Exception as e:
        print('error:{}'.format(e))
        return 0
        
def checkluminous():
    try:
        #print(I_max)
        if (max_value > I_max):
            return '0'
        elif (max_value > I_thr_top):
            return '1'
        elif (max_value < I_thr_top and max_value > I_thr_bottom):
            return '2'
        elif (max_value < I_thr_bottom):
            return '3'
    except Exception as e:
        print('error:{}'.format(e))
        return 0
        
def set_half_exp():
    global st1, I1
    
    try:
        st1 = int(ui.shutter_edit.text())
        I1 = max_value
        
        st = int(ui.shutter_edit.text())
        ui.shutter_edit.setText(str(int(st/2)))
        return 1
    except Exception as e:
        print('error:{}'.format(e))
        return 0

def set_double_exp():
    global st1, I1
    
    try:
        st1 = int(ui.shutter_edit.text())
        I1 = max_value
        
        st = int(ui.shutter_edit.text())
        ui.shutter_edit.setText(str(int(st*2)))
        return 1
    except Exception as e:
        print('error:{}'.format(e))
        return 0

def find_target_exp():
    global goal_st
    try:
        st2 = int(ui.shutter_edit.text())
        I2 = max_value
            
        goal_st = int(float(st1 + ((I_thr - I1) * ((st1 - st2)/(I1 - I2)))))
        if goal_st > st_max:
            print("Can't calculate shutter")
            goal_st = shutter
        elif goal_st < 0:
            print("Goal Error")
            goal_st = shutter
            
        signalComm.new_goal_st.emit()
        return 1
    except Exception as e:
        goal_st = shutter
        signalComm.new_goal_st.emit()
        print('error:{}'.format(e))
        return 0

def number_ofscan():
    global numb_ofscan
    
    try:
        numb_ofscan.append(data)
        return 1
    except Exception as e:
        print('error:{}'.format(e))
        return 0

def cal_number_ofscan():
    try:
        #print(np.shape(numb_ofscan))
        ncolmean = np.mean(np.asarray(numb_ofscan), axis = 0)
        #print(np.shape(ncolmean))
        return 1
    except Exception as e:
        print('error:{}'.format(e))
        return 0
            
def save_data():
    try:
        path = 'data.txt'
        f = open(path, 'w')
        for i in data:
            f.write(str(i)+"\n")
        f.close()
        print("Save Complete")
        
        return 1
    except Exception as e:
        print('error:{}'.format(e))
        return 0	
        
def find_target_exp_full(itask):
    try:
        st1 = int(ui.shutter_edit.text())
        I1 = max_value
        
        if itask == '0':
            return '10'
        elif itask == '1':
            check = set_half_exp()
            if check != 1:
                return 0
        elif itask == '2':
            return 1
        elif itask == '3':
            check = set_double_exp()
            if check != 1:
                return 0
        else:
            return 0
                    
        check = takephoto()
        if check != 1:
            return 0		
        check = crop_image()
        if check != 1:
            return 0	
        st2 = int(ui.shutter_edit.text())
        I2 = max_value
        
        goal_st = int(float(st1 + ((I_thr - I1) * ((st1 - st2)/(I1 - I2)))))
        if goal_st > st_max:
            print("Can't calculate shutter")
            return 0
        elif goal_st < 0:
            print("Goal Error")
        else:
            ui.shutter_edit.setText(str(goal_st))
        return 1		
    except Exception as e:
        print('error:{}'.format(e))
        return 0
                                                                
def main_prop():
    st = ui.shutter_edit.text()
    ag = ui.anologgain_edit.text()
    dg = ui.digitalgain_edit.text()
    x = ui.x0.text()
    y = ui.y0.text()
    deltax = ui.x1.text()
    deltay = ui.y1.text()
    imgformat = ui.format_box.currentText().lower()

def thread_1():
    global mode, image_mode, numb_ofscan
    scan_time = 0
    first_scan = 1
    
    while True:
        if mode == 0:
            if flag == 1:
                mode = 10
            else:
                break
        elif mode == 10:
            check = takephoto()
            if check == 1:
                image_mode = 1
                mode = 15
                #mode = 20
            else:
                mode = 999
        elif mode == 15:
            if first_scan == 1:
                if roi_mode == 0:
                    check = sum_image()
                    if check == 1:
                        mode = 30
                    else:
                        mode = 999
                else:
                    mode = 30
            else:
                mode = 30			
        elif mode == 20:
            if roi_mode == 0:
                check = ui.roi_scan()
                if check == 1:
                    mode = 30
                else:
                    mode = 999
            else:
                mode = 30
        elif mode == 30:
            check = crop_image()
            if check == 1:
                mode = 31
                #mode = 40
            else:
                mode = 999
        elif mode == 31:
            if int(num_scan) > 1 :
                check = number_ofscan()
                if check == 1:
                    first_scan = 0
                    scan_time += 1
                    if scan_time < int(num_scan):
                        mode = 10
                    else:
                        mode = 32
                else:
                    mode = 999
            else:
                mode = 40
        elif mode == 32:
            check = cal_number_ofscan()
            if check == 1:
                mode = 40
            else:
                mode = 999
        elif mode == 35:
            check = save_data()
            if check == 1:
                mode = 40
            else:
                mode = 999
        elif mode == 40:
            check = ui.draw_spectrum_graph_signal()
            if check == 1:
                mode = 50
            else:
                mode = 999
        elif mode == 50:
            check = ui.update_image_signal()
            if check == 1:
                mode = 60
            else:
                mode = 999
        elif mode == 60:
            check = wavelength_convert()
            if check == 1:
                mode = 70
            else:
                mode = 999
        elif mode == 70:
            check = ui.draw_wavelength_graph_signal()
            if check == 1:
                numb_ofscan.clear()
                mode = 0
                first_scan = 1
            else:
                mode = 999
        elif mode == 999:
            print("Main Function Error")
            raise Exception
    print("Main Function Complete")
    
def thread_2():
    global auto_mode
    t_times = 0
    
    while True:
        if auto_mode == 1:
            check = takephoto()
            if check == 1:
                auto_mode = 2
            else:
                auto_mode = 999
        elif auto_mode == 2:
            check = crop_image()
            if check == 1:
                auto_mode = 10
            else:
                auto_mode = 999
        elif auto_mode == 3:
            check = wavelength_convert()
            if check == 1:
                auto_mode = 4
            else:
                auto_mode = 999
        elif auto_mode == 4:
            check = ui.draw_both_graph_signal()
            if check == 1:
                auto_mode = 5
            else:
                auto_mode = 999
        elif auto_mode == 5:
            check = ui.update_image_signal()
            if check == 1:
                #auto_mode = 6
                break
            else:
                auto_mode = 999
        elif auto_mode == 6:
            check = save_data()
            if check == 1:
                break
            else:
                auto_mode = 999
        elif auto_mode == 10:
            check = checkluminous()
            if check == '0':
                auto_mode = 20
            elif check == '1':
                auto_mode = 30
            elif check == '2':
                if t_times != 0:
                    auto_mode = 3
                else:
                    break
            elif check == '3':
                auto_mode = 40
            else:
                auto_mode = 999
            t_times = 1
        elif auto_mode == 20:
            print("Spectrum Error")
            break
        elif auto_mode == 30:
            check = set_half_exp()
            if check == 1:
                auto_mode = 50
            else:
                auto_mode = 999
        elif auto_mode == 40:
            check = set_double_exp()
            if check == 1:
                auto_mode = 50
            else:
                auto_mode = 999
        elif auto_mode == 50:
            check = takephoto()
            if check == 1:
                auto_mode = 51
            else:
                auto_mode = 999
        elif auto_mode == 51:
            check = crop_image()
            if check == 1:
                auto_mode = 52
            else:
                auto_mode = 999
        elif auto_mode == 52:
            check = find_target_exp()
            if check == 1:
                auto_mode = 1
            else:
                auto_mode = 999
        elif auto_mode == 100:
            itask = checkluminous()
            check = find_target_exp_full(itask)
            if check == 1:
                break
            else:
                auto_mode = 999
        elif auto_mode == 999:
            print("Auto Scaling Error")
            raise Exception
    print('Auto Scaling Complete')

if __name__ == "__main__":
    try:		
        app = QtWidgets.QApplication(sys.argv)
        mainwindow = QtWidgets.QMainWindow()
        signalComm = SignalCommunication()	
        ui = Ui_mainwindow()
        ui.setupUi(mainwindow)
        mainwindow.show()
        sys.exit(app.exec_())
    except Exception as ex:
        print(ex)
        exit()
    




from PyQt5 import QtCore, QtGui, QtWidgets
from scipy import signal
import numpy as np
import pyqtgraph as pg
import sys, configparser, cv2, threading, subprocess

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

I_max = config['auto_scaling']['I_max']
I_thr_percentage = config['auto_scaling']['I_thr_percentage']
I_thr_tolerance = config['auto_scaling']['I_thr_tolerance']

numberof_scan_config = config['numof_scan']['numberof_scan']

w_length = config['sgfilter']['window_length']
poly_order = config['sgfilter']['polyorder']

st_max = 1000000
ag_max = 100000000

st1 = 0
st2 = 0
I1 = 0
I2 = 0

I_thr = 0
I_thr_top = 0
I_thr_bottom = 0

mode = 0
auto_mode = 0
y_mode = 0
flag = 0
roi_mode = 0
num_scan = numberof_scan_config

max_value = 0
goal_st = 0
new_y0 = 0
c_draw_wgraph = 0

wdata = []
numb_ofscan = []
ncolmean = []

class SignalCommunication(QtCore.QObject):
    new_image = QtCore.pyqtSignal()
    new_y0 = QtCore.pyqtSignal()
    new_data = QtCore.pyqtSignal()
    new_wdata = QtCore.pyqtSignal()
    new_goal_st =  QtCore.pyqtSignal()

class Ui_mainwindow(object):
    def setupUi(self, mainwindow):
        mainwindow.setObjectName("mainwindow")
        mainwindow.resize(1280, 960)
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
        self.pixel_graph.setGeometry(QtCore.QRect(140, 420, 500, 400))
        
        self.wavelength_graph = pg.PlotWidget(self.centralwidget)
        self.wavelength_graph.setGeometry(QtCore.QRect(670, 420, 500, 400))
        
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
        self.a3_label.setGeometry(QtCore.QRect(670, 220, 50, 16))
        self.a2_label = QtWidgets.QLabel(self.centralwidget)
        self.a2_label.setGeometry(QtCore.QRect(670, 260, 50, 16))
        self.a1_label = QtWidgets.QLabel(self.centralwidget)
        self.a1_label.setGeometry(QtCore.QRect(670, 300, 50, 16))
        self.a0_label = QtWidgets.QLabel(self.centralwidget)
        self.a0_label.setGeometry(QtCore.QRect(670, 340, 50, 16))		
        self.a3 = QtWidgets.QLineEdit(self.centralwidget)
        self.a3.setGeometry(QtCore.QRect(700, 210, 80, 30))
        self.a2 = QtWidgets.QLineEdit(self.centralwidget)
        self.a2.setGeometry(QtCore.QRect(700, 250, 80, 30))
        self.a1 = QtWidgets.QLineEdit(self.centralwidget)
        self.a1.setGeometry(QtCore.QRect(700, 290, 80, 30))
        self.a0 = QtWidgets.QLineEdit(self.centralwidget)
        self.a0.setGeometry(QtCore.QRect(700, 330, 80, 30))
        
        self.e3_label = QtWidgets.QLabel(self.centralwidget)
        self.e3_label.setGeometry(QtCore.QRect(790, 220, 50, 16))
        self.e2_label = QtWidgets.QLabel(self.centralwidget)
        self.e2_label.setGeometry(QtCore.QRect(790, 260, 50, 16))
        self.e1_label = QtWidgets.QLabel(self.centralwidget)
        self.e1_label.setGeometry(QtCore.QRect(790, 300, 50, 16))
        self.e0_label = QtWidgets.QLabel(self.centralwidget)
        self.e0_label.setGeometry(QtCore.QRect(790, 340, 50, 16))		
        self.e3 = QtWidgets.QLineEdit(self.centralwidget)
        self.e3.setGeometry(QtCore.QRect(810, 210, 50, 30))
        self.e2 = QtWidgets.QLineEdit(self.centralwidget)
        self.e2.setGeometry(QtCore.QRect(810, 250, 50, 30))
        self.e1 = QtWidgets.QLineEdit(self.centralwidget)
        self.e1.setGeometry(QtCore.QRect(810, 290, 50, 30))
        self.e0 = QtWidgets.QLineEdit(self.centralwidget)
        self.e0.setGeometry(QtCore.QRect(810, 330, 50, 30))
        
        self.w_cal_button = QtWidgets.QPushButton(self.centralwidget)
        self.w_cal_button.setGeometry(QtCore.QRect(670, 370, 90, 30))
        
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
        self.I_thr_percentage_label1 = QtWidgets.QLabel(self.centralwidget)
        self.I_thr_percentage_label1.setGeometry(QtCore.QRect(285, 320, 150, 16))
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
        self.numberof_scan_label1 = QtWidgets.QLabel(self.centralwidget)
        self.numberof_scan_label1.setGeometry(QtCore.QRect(285, 390, 150, 16))
        
        self.cameraspec_label = QtWidgets.QLabel(self.centralwidget)
        self.cameraspec_label.setGeometry(QtCore.QRect(800, 20, 200, 16))
        self.cameraname_label = QtWidgets.QLabel(self.centralwidget)
        self.cameraname_label.setGeometry(QtCore.QRect(800, 40, 200, 16))
        self.camerawidth_label = QtWidgets.QLabel(self.centralwidget)
        self.camerawidth_label.setGeometry(QtCore.QRect(800, 60, 200, 16))
        self.cameraheight_label = QtWidgets.QLabel(self.centralwidget)
        self.cameraheight_label.setGeometry(QtCore.QRect(800, 80, 200, 16))
        self.camerapixelsize_label = QtWidgets.QLabel(self.centralwidget)
        self.camerapixelsize_label.setGeometry(QtCore.QRect(800, 100, 200, 16))
        
        self.sg_filter_checkbox = QtWidgets.QCheckBox("SG Filter   ",self.centralwidget)
        self.sg_filter_checkbox.setGeometry(QtCore.QRect(420, 220, 95, 16))
        self.sg_filter_checkbox.setLayoutDirection(QtCore.Qt.RightToLeft)        
        self.window_length_label = QtWidgets.QLabel(self.centralwidget)
        self.window_length_label.setGeometry(QtCore.QRect(420, 260, 100, 16))
        self.window_length_edit = QtWidgets.QLineEdit(self.centralwidget)
        self.window_length_edit.setGeometry(QtCore.QRect(500, 250, 50, 30))
        self.polyorder_label = QtWidgets.QLabel(self.centralwidget)
        self.polyorder_label.setGeometry(QtCore.QRect(420, 300, 100, 16))
        self.polyorder_edit = QtWidgets.QLineEdit(self.centralwidget)
        self.polyorder_edit.setGeometry(QtCore.QRect(500, 290, 50, 30))
        
        self.statusbar.showMessage("INITIALING")
        self.retranslateUi(mainwindow)
        QtCore.QMetaObject.connectSlotsByName(mainwindow)
        
        self.start.clicked.connect(self.start_clicked)
        self.y_axis.clicked.connect(self.y_axis_clicked)	
        self.auto_scaling.clicked.connect(self.auto_scaling_clicked)	
        self.auto_roi.clicked.connect(self.auto_roi_clicked)	
        self.w_cal_button.clicked.connect(self.w_cal_button_clicked)	
        
        self.continue_checkbox.toggled.connect(self.continue_checkbox_check)
        self.sg_filter_checkbox.toggled.connect(self.sg_filter_checkbox_check)
            
        self.Yaxis_max.textChanged[str].connect(self.y_axis_fix)
        self.x0.textChanged[str].connect(self.roi_change)
        self.y0.textChanged[str].connect(self.roi_change)
        self.x1.textChanged[str].connect(self.roi_change)
        self.y1.textChanged[str].connect(self.roi_change)
        self.I_max_edit.textChanged[str].connect(self.auto_scaling_paremeter_change)
        self.I_thr_percentage_edit.textChanged[str].connect(self.auto_scaling_paremeter_change)
        self.I_thr_tolerance_edit.textChanged[str].connect(self.auto_scaling_paremeter_change)
        self.numberof_scan_edit.textChanged[str].connect(self.scan_number_change)
        self.shutter_edit.textChanged[str].connect(self.shutter_change)
        
        signalComm.new_image.connect(self.update_image)
        signalComm.new_y0.connect(self.update_y0)
        signalComm.new_data.connect(self.update_data)
        signalComm.new_wdata.connect(self.update_wdata)
        signalComm.new_goal_st.connect(self.update_st)
        
        self.x0.setEnabled(False)
        self.y0.setEnabled(False)
        self.x1.setEnabled(False)
        self.Yaxis_max.setEnabled(False)
        self.w_cal_button.setEnabled(False)
        
        self.statusbar.showMessage("DONE")
                
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
        self.w_cal_button.setText(_translate("mainwindow", "Calculate"))
        self.cameraspec_label.setText(_translate("mainwindow", "Camera Specification"))
        self.cameraname_label.setText(_translate("mainwindow", "Model : OV9281"))
        self.camerawidth_label.setText(_translate("mainwindow", "IMG Width : 1280"))
        self.cameraheight_label.setText(_translate("mainwindow", "IMG Height : 800"))
        self.camerapixelsize_label.setText(_translate("mainwindow", "Pixel Size : 3 \u03BCm x 3 \u03BCm"))
        self.window_length_label.setText(_translate("mainwindow", "W_Length"))
        self.polyorder_label.setText(_translate("mainwindow", "PolyOrder"))
            
        self.pixel_graph.setBackground('w')
        self.pixel_graph.setLabel('left', 'Intensity')
        self.pixel_graph.setLabel('bottom', 'Pixel')
        
        self.wavelength_graph.setBackground('w')
        self.wavelength_graph.setLabel('left', 'Intensity')
        self.wavelength_graph.setLabel('bottom', 'Wavelength')
        
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
        
        self.I_max_edit.setText(I_max)
        self.I_thr_percentage_edit.setText(I_thr_percentage)
        self.I_thr_tolerance_edit.setText(I_thr_tolerance)
        
        I_max = int(ui.I_max_edit.text())
        I_thr_percentage = int(ui.I_thr_percentage_edit.text())
        I_thr_tolerance = int(ui.I_thr_tolerance_edit.text())
        I_thr = I_max * I_thr_percentage/100
        I_thr_top = I_thr + I_thr_tolerance
        I_thr_bottom = I_thr - I_thr_tolerance
        self.I_thr_tolerance_label1.setText(_translate("mainwindow", str(I_thr_top) + ' ~ ' + str(I_thr_bottom)))
        self.I_thr_percentage_label1.setText(_translate("mainwindow", str(I_thr)))
        
        self.numberof_scan_edit.setText(numberof_scan_config)
        self.numberof_scan_label1.setText(_translate("mainwindow", str(((float(shutter) / 1000) * float(num_scan) + 500 * float(num_scan)) / 1000 ) + ' seconds'))
        
        self.window_length_edit.setText(w_length)
        self.polyorder_edit.setText(poly_order)
        
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
        self.window_length_edit.setValidator(QtGui.QIntValidator())
        self.polyorder_edit.setValidator(QtGui.QIntValidator())
        
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
                return
        else:
            flag = 0
            mode = 10
            
        self.w_cal_button.setEnabled(True)
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
        x = np.arange(1, len(ncolmean)+1)
        if self.sg_filter_checkbox.isChecked():
            #savgol_filter(data, window length, polyorder)
            y = signal.savgol_filter(ncolmean, int(self.window_length_edit.text()), int(self.polyorder_edit.text()))
        else:
            y = ncolmean
        c_ui.c_graph.plot(x, y)
        secondwindow.show()
            
    def continue_checkbox_check(self):
        global flag
        _translate = QtCore.QCoreApplication.translate
        
        if ui.continue_checkbox.isChecked() == False:
            flag = 0
            self.start.setText(_translate("mainwindow", "START"))
    
    def sg_filter_checkbox_check(self):
        self.draw_both_graph_signal()
        if secondwindow.isVisible():
            c_ui.c_graph.clear()
            x = np.arange(1, len(ncolmean)+1)
            if self.sg_filter_checkbox.isChecked():
                #savgol_filter(data, window length, polyorder)
                y = signal.savgol_filter(ncolmean, int(self.window_length_edit.text()), int(self.polyorder_edit.text()))
            else:
                y = ncolmean
            c_ui.c_graph.plot(x, y)
            
            if c_draw_wgraph == 1:
                check = c_ui.w_draw_wgraph()
                if check == 0:
                    raise Exception
                            
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
        self.I_thr_percentage_label1.setText(_translate("mainwindow", str(I_thr)))
        
    def scan_number_change(self):
        global num_scan
        
        num_scan = self.numberof_scan_edit.text()
        
        _translate = QtCore.QCoreApplication.translate
        self.numberof_scan_label1.setText(_translate("mainwindow", str(((float(shutter) / 1000) * float(num_scan) + 500 * float(num_scan)) / 1000 ) + ' seconds'))
    
    def shutter_change(self):
        global shutter
        
        shutter = self.shutter_edit.text()
        _translate = QtCore.QCoreApplication.translate
        self.numberof_scan_label1.setText(_translate("mainwindow", str(((float(shutter) / 1000) * float(num_scan) + 500 * float(num_scan)) / 1000 ) + ' seconds'))
        
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
        return img1
        
    def update_data(self):
        try:
            self.pixel_graph.clear()
            x = np.arange(1,len(ncolmean)+1)
            if self.sg_filter_checkbox.isChecked():
                #savgol_filter(data, window length, polyorder)
                y = signal.savgol_filter(ncolmean, int(self.window_length_edit.text()), int(self.polyorder_edit.text()))
            else:
                y = ncolmean
            self.pixel_graph.plot(x, y, pen=pg.mkPen('k'))	# k = black
            
            return 1
        except Exception as e:
            print('error:{}'.format(e))
            return 0	
    
    def update_wdata(self):
        try:
            self.wavelength_graph.clear()
            x = wdata
            if self.sg_filter_checkbox.isChecked():
                y = signal.savgol_filter(ncolmean, int(self.window_length_edit.text()), int(self.polyorder_edit.text()))
            else:
                y = ncolmean
            self.wavelength_graph.plot(x, y, pen=pg.mkPen('k'))	# k = black
            
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
    
class Ui_w_calibration(object):
    def setupUi(self, w_calibration):
        w_calibration.setObjectName("w_calibration")
        w_calibration.setEnabled(True)
        w_calibration.resize(560, 440)
        self.fill_in_table = QtWidgets.QTableView(w_calibration)
        self.fill_in_table.setGeometry(QtCore.QRect(10, 10, 190, 250))
        self.fill_in_table.setObjectName("fill_in_table")
        self.label = QtWidgets.QLabel(w_calibration)
        self.label.setGeometry(QtCore.QRect(20, 20, 100, 16))
        self.label.setObjectName("label")
        self.label_2 = QtWidgets.QLabel(w_calibration)
        self.label_2.setGeometry(QtCore.QRect(20, 40, 100, 16))
        self.label_2.setObjectName("label_2")
        self.label_3 = QtWidgets.QLabel(w_calibration)
        self.label_3.setGeometry(QtCore.QRect(20, 65, 100, 16))
        self.label_3.setObjectName("label_3")
        self.label_4 = QtWidgets.QLabel(w_calibration)
        self.label_4.setGeometry(QtCore.QRect(20, 90, 100, 16))
        self.label_4.setObjectName("label_4")
        self.label_5 = QtWidgets.QLabel(w_calibration)
        self.label_5.setGeometry(QtCore.QRect(20, 115, 100, 16))
        self.label_5.setObjectName("label_5")
        self.label_6 = QtWidgets.QLabel(w_calibration)
        self.label_6.setGeometry(QtCore.QRect(20, 140, 100, 16))
        self.label_6.setObjectName("label_6")
        self.label_7 = QtWidgets.QLabel(w_calibration)
        self.label_7.setGeometry(QtCore.QRect(20, 165, 100, 16))
        self.label_7.setObjectName("label_7")
        self.label_8 = QtWidgets.QLabel(w_calibration)
        self.label_8.setGeometry(QtCore.QRect(20, 190, 100, 16))
        self.label_8.setObjectName("label_8")
        self.label_9 = QtWidgets.QLabel(w_calibration)
        self.label_9.setGeometry(QtCore.QRect(70, 20, 100, 16))
        self.label_9.setObjectName("label_9")
        self.label_10 = QtWidgets.QLabel(w_calibration)
        self.label_10.setGeometry(QtCore.QRect(70, 40, 100, 16))
        self.label_10.setObjectName("label_10")
        self.label_11 = QtWidgets.QLabel(w_calibration)
        self.label_11.setGeometry(QtCore.QRect(70, 65, 100, 16))
        self.label_11.setObjectName("label_11")
        self.label_12 = QtWidgets.QLabel(w_calibration)
        self.label_12.setGeometry(QtCore.QRect(70, 90, 100, 16))
        self.label_12.setObjectName("label_12")
        self.label_13 = QtWidgets.QLabel(w_calibration)
        self.label_13.setGeometry(QtCore.QRect(70, 115, 100, 16))
        self.label_13.setObjectName("label_13")
        self.label_14 = QtWidgets.QLabel(w_calibration)
        self.label_14.setGeometry(QtCore.QRect(70, 140, 100, 16))
        self.label_14.setObjectName("label_14")
        self.label_15 = QtWidgets.QLabel(w_calibration)
        self.label_15.setGeometry(QtCore.QRect(70, 165, 100, 16))
        self.label_15.setObjectName("label_15")
        self.label_16 = QtWidgets.QLabel(w_calibration)
        self.label_16.setGeometry(QtCore.QRect(70, 190, 100, 16))
        self.label_16.setObjectName("label_16")
        self.pixel1 = QtWidgets.QLineEdit(w_calibration)
        self.pixel1.setGeometry(QtCore.QRect(140, 40, 50, 20))
        self.pixel1.setText("134")
        self.pixel1.setObjectName("pixel1")
        self.pixel2 = QtWidgets.QLineEdit(w_calibration)
        self.pixel2.setGeometry(QtCore.QRect(140, 65, 50, 20))
        self.pixel2.setText("182")
        self.pixel2.setObjectName("pixel2")
        self.pixel3 = QtWidgets.QLineEdit(w_calibration)
        self.pixel3.setGeometry(QtCore.QRect(140, 90, 50, 20))
        self.pixel3.setText("352")
        self.pixel3.setObjectName("pixel3")
        self.pixel4 = QtWidgets.QLineEdit(w_calibration)
        self.pixel4.setGeometry(QtCore.QRect(140, 115, 50, 20))
        self.pixel4.setText("581")
        self.pixel4.setObjectName("pixel4")
        self.pixel5 = QtWidgets.QLineEdit(w_calibration)
        self.pixel5.setGeometry(QtCore.QRect(140, 140, 50, 20))
        self.pixel5.setText("682")
        self.pixel5.setObjectName("pixel5")
        self.pixel6 = QtWidgets.QLineEdit(w_calibration)
        self.pixel6.setGeometry(QtCore.QRect(140, 165, 50, 20))
        self.pixel6.setText("752")
        self.pixel6.setObjectName("pixel6")
        self.pixel7 = QtWidgets.QLineEdit(w_calibration)
        self.pixel7.setGeometry(QtCore.QRect(140, 190, 50, 20))
        self.pixel7.setText("902")
        self.pixel7.setObjectName("pixel7")
        self.CalButton = QtWidgets.QPushButton(w_calibration)
        self.CalButton.setGeometry(QtCore.QRect(104, 220, 90, 30))
        self.tableView = QtWidgets.QTableView(w_calibration)
        self.tableView.setGeometry(QtCore.QRect(10, 270, 130, 100))
        self.tableView.setObjectName("tableView")
        self.label_17 = QtWidgets.QLabel(w_calibration)
        self.label_17.setGeometry(QtCore.QRect(20, 275, 20, 15))
        self.label_17.setObjectName("label_17")
        self.label_18 = QtWidgets.QLabel(w_calibration)
        self.label_18.setGeometry(QtCore.QRect(20, 300, 20, 15))
        self.label_18.setObjectName("label_18")
        self.label_19 = QtWidgets.QLabel(w_calibration)
        self.label_19.setGeometry(QtCore.QRect(20, 325, 20, 15))
        self.label_19.setObjectName("label_19")
        self.label_20 = QtWidgets.QLabel(w_calibration)
        self.label_20.setGeometry(QtCore.QRect(20, 350, 20, 15))
        self.label_20.setObjectName("label_20")
        self.a3_label = QtWidgets.QLabel(w_calibration)
        self.a3_label.setGeometry(QtCore.QRect(50, 275, 100, 15))
        self.a3_label.setObjectName("a3_label")
        self.a2_label = QtWidgets.QLabel(w_calibration)
        self.a2_label.setGeometry(QtCore.QRect(50, 300, 100, 15))
        self.a2_label.setObjectName("a2_label")
        self.a1_label = QtWidgets.QLabel(w_calibration)
        self.a1_label.setGeometry(QtCore.QRect(50, 325, 100, 15))
        self.a1_label.setObjectName("a1_label")
        self.a0_label = QtWidgets.QLabel(w_calibration)
        self.a0_label.setGeometry(QtCore.QRect(50, 350, 100, 15))
        self.a0_label.setObjectName("a0_label")
        
        self.c_graph = pg.PlotWidget(w_calibration)
        self.c_graph.setGeometry(QtCore.QRect(220, 10, 300, 200))
        self.c_wavelength_graph = pg.PlotWidget(w_calibration)
        self.c_wavelength_graph.setGeometry(QtCore.QRect(220, 220, 300, 200))
        
        self.pixel_label = QtWidgets.QLabel(w_calibration)
        self.pixel_label.setGeometry(QtCore.QRect(140, 20, 100, 16))
        
        self.retranslateUi(w_calibration)
        QtCore.QMetaObject.connectSlotsByName(w_calibration)
        
        self.CalButton.clicked.connect(self.w_cal_button_clicked)

    def retranslateUi(self, w_calibration):
        _translate = QtCore.QCoreApplication.translate
        w_calibration.setWindowTitle(_translate("w_calibration", "Wavelength Calibration"))
        self.label.setText(_translate("w_calibration", "NO."))
        self.label_2.setText(_translate("w_calibration", "1"))
        self.label_3.setText(_translate("w_calibration", "2"))
        self.label_4.setText(_translate("w_calibration", "3"))
        self.label_5.setText(_translate("w_calibration", "4"))
        self.label_6.setText(_translate("w_calibration", "5"))
        self.label_7.setText(_translate("w_calibration", "6"))
        self.label_8.setText(_translate("w_calibration", "7"))
        self.label_9.setText(_translate("w_calibration", "Lambda"))
        self.label_10.setText(_translate("w_calibration", "404.656"))
        self.label_11.setText(_translate("w_calibration", "435.833"))
        self.label_12.setText(_translate("w_calibration", "546.074"))
        self.label_13.setText(_translate("w_calibration", "696.543"))
        self.label_14.setText(_translate("w_calibration", "763.511"))
        self.label_15.setText(_translate("w_calibration", "811.531"))
        self.label_16.setText(_translate("w_calibration", "912.297"))
        self.CalButton.setText(_translate("w_calibration", "CALCULATE"))
        self.label_17.setText(_translate("w_calibration", "a3"))
        self.label_18.setText(_translate("w_calibration", "a2"))
        self.label_19.setText(_translate("w_calibration", "a1"))
        self.label_20.setText(_translate("w_calibration", "a0"))
        self.a3_label.setText(_translate("w_calibration", "---"))
        self.a2_label.setText(_translate("w_calibration", "---"))
        self.a1_label.setText(_translate("w_calibration", "---"))
        self.a0_label.setText(_translate("w_calibration", "---"))
        self.pixel_label.setText(_translate("w_calibration", "Pixel"))
        
        self.pixel1.setValidator(QtGui.QDoubleValidator())
        self.pixel2.setValidator(QtGui.QDoubleValidator())
        self.pixel3.setValidator(QtGui.QDoubleValidator())
        self.pixel4.setValidator(QtGui.QDoubleValidator())
        self.pixel5.setValidator(QtGui.QDoubleValidator())
        self.pixel6.setValidator(QtGui.QDoubleValidator())
        self.pixel7.setValidator(QtGui.QDoubleValidator())
        
        self.c_graph.setBackground('w')
        self.c_graph.setLabel('left', 'Intensity')
        self.c_graph.setLabel('bottom', 'Pixel')
        
        self.c_wavelength_graph.setBackground('w')
        self.c_wavelength_graph.setLabel('left', 'Intensity')
        self.c_wavelength_graph.setLabel('bottom', 'Wavelength')
        
    def w_cal_button_clicked(self):
        global c_draw_wgraph
        try:
            x1 = []
            y1 = []
            lam1 = self.pixel1.text()
            lam2 = self.pixel2.text()
            lam3 = self.pixel3.text()
            lam4 = self.pixel4.text()
            lam5 = self.pixel5.text()
            lam6 = self.pixel6.text()
            lam7 = self.pixel7.text()
            
            l1 = self.label_10.text()
            l2 = self.label_11.text()
            l3 = self.label_12.text()
            l4 = self.label_13.text()
            l5 = self.label_14.text()
            l6 = self.label_15.text()
            l7 = self.label_16.text()
            
            x1.append(float(lam1))
            x1.append(float(lam2))
            x1.append(float(lam3))
            x1.append(float(lam4))
            x1.append(float(lam5))
            x1.append(float(lam6))
            x1.append(float(lam7))
            
            y1.append(float(l1))
            y1.append(float(l2))
            y1.append(float(l3))
            y1.append(float(l4))
            y1.append(float(l5))
            y1.append(float(l6))
            y1.append(float(l7))
            
            z1 = np.polyfit(x1, y1, 3)
            p0 = []
            for i in range(len(z1)):
                e = str(z1[i]).find('e')
                if e > 0:
                    p0.extend([float(str(z1[i])[:e:]),int(str(z1[i])[e+1::])])
                else:
                    p0.append(float(str(z1[i])[:e:]))
                    
            _translate = QtCore.QCoreApplication.translate
            self.a3_label.setText(_translate("w_calibration", (str(np.around(p0[0],3)))+'e'+str(p0[1])))
            self.a2_label.setText(_translate("w_calibration", (str(np.around(p0[2],3)))+'e'+str(p0[3])))
            self.a1_label.setText(_translate("w_calibration", str(np.around(p0[4],3))))
            self.a0_label.setText(_translate("w_calibration", str(np.around(p0[5],3))))
            ui.a3.setText(str(np.around(p0[0],3)))
            ui.a2.setText(str(np.around(p0[2],3)))
            ui.a1.setText(str(np.around(p0[4],3)))
            ui.a0.setText(str(np.around(p0[5],3)))
            ui.e3.setText(str(p0[1]))
            ui.e2.setText(str(p0[3]))
            ui.e1.setText('0')
            ui.e0.setText('0')
            
            check = wavelength_convert()
            if check != 1:
                raise Exception
            check = ui.draw_wavelength_graph_signal()
            if check != 1:
                raise Exception
            check = self.w_draw_wgraph()
            if check != 1:
                raise Exception
            c_draw_wgraph = 1
            return 1
        except Exception as e:
            print('error:{}'.format(e))
            return 0
      
    def w_draw_wgraph(self):
        try:
            self.c_wavelength_graph.clear()
            x = wdata
            if ui.sg_filter_checkbox.isChecked():
                #savgol_filter(data, window length, polyorder)
                y = signal.savgol_filter(ncolmean, int(ui.window_length_edit.text()), int(ui.polyorder_edit.text()))
            else:
                y = ncolmean
            self.c_wavelength_graph.plot(x, y)	
            return 1
        except Exception as e:
            print('error:{}'.format(e))
            return 0
            
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
        nRowSum = np.sum(nImage, axis = 1)
        a = np.argmax(nRowSum)
        new_y0 = a-deltay/2
        if new_y0 <= 0:
            new_y0 = 0
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
        if (max_value >= I_max):
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
        st1 = float(ui.shutter_edit.text())
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
        st1 = float(ui.shutter_edit.text())
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
        st2 = float(ui.shutter_edit.text())
        I2 = max_value
        
        goal_st = int(st1 + ((st1 - st2)/(I1 - I2) * (I_thr - I1)))
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
    global ncolmean
    try:
        ncolmean = np.mean(np.asarray(numb_ofscan), axis = 0)

        return 1
    except Exception as e:
        print('error:{}'.format(e))
        return 0
            
def save_data():
    try:
        path = 'data.txt'
        f = open(path, 'w')
        for i in ncolmean:
            f.write(str(i)+"\n")
        f.close()
        print("Save Complete")
        
        return 1
    except Exception as e:
        print('error:{}'.format(e))
        return 0	

def thread_1():
    global mode, image_mode, numb_ofscan
    scan_time = 0
    first_scan = 1
    
    ui.statusbar.showMessage("CAPTURING IMAGE")
    
    while True:
        if mode == 0:
            if flag == 1:
                mode = 10
            else:
                break
        elif mode == 10:
            check = takephoto()
            if check == 1:
                mode = 20
            else:
                mode = 999
        elif mode == 20:
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
        elif mode == 30:
            check = crop_image()
            if check == 1:
                mode = 31
            else:
                mode = 999
        elif mode == 31:
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
        elif mode == 32:
            check = cal_number_ofscan()
            if check == 1:
                mode = 35
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
                scan_time = 0
                mode = 0
            else:
                mode = 999
        elif mode == 999:
            print("Main Function Error")
            ui.statusbar.showMessage("CAPTURE IMAGE Error")
            raise Exception
    print("Main Function Complete")
    ui.statusbar.showMessage("CAPTURE IMAGE COMPLETE")
    
def thread_2():
    global auto_mode
    t_times = 0
    first_scan = 1
    
    ui.statusbar.showMessage("AUTO SCALING")
    
    while True:
        if auto_mode == 10:
            check = takephoto()
            if check == 1:
                auto_mode = 20
            else:
                auto_mode = 999
        elif auto_mode == 20:
            if first_scan == 1:
                if roi_mode == 0:
                    check = sum_image()
                    if check == 1:
                        auto_mode = 30
                        first_scan = 0
                    else:
                        auto_mode = 999
                else:
                    auto_mode = 30
            else:
                auto_mode = 30
        elif auto_mode == 30:
            check = crop_image()
            if check == 1:
                if t_times == 0:
                    auto_mode = 40
                else:
                    auto_mode = 60
            else:
                auto_mode = 999
        elif auto_mode == 40:
            check = checkluminous()
            if check == '0': # peak(max_value) > I_max
                auto_mode = 51
            elif check == '1': # peak(max_value) > I_thr_top
                auto_mode = 50
            elif check == '2': # peak(max_value) is acceptable 
                auto_mode = 70
            elif check == '3': # peak(max_value) < I_thr_buttom
                auto_mode = 55
            else:
                auto_mode = 999
        elif auto_mode == 50:
            check = set_half_exp()
            if check == 1:
                auto_mode = 10
                t_times = 1
            else:
                auto_mode = 999
        elif auto_mode == 51:
            check = set_half_exp()
            if check == 1:
                auto_mode = 10
            else:
                auto_mode = 999
        elif auto_mode == 55:
            check = set_double_exp()
            if check == 1:
                auto_mode = 10
                t_times = 1
            else:
                auto_mode = 999
        elif auto_mode == 60:
            check = find_target_exp()
            if check == 1:
                auto_mode = 10
                t_times = 0
            else:
                auto_mode = 999
        elif auto_mode == 70:
            check = ui.draw_spectrum_graph_signal()
            if check == 1:
                auto_mode = 80
            else:
                auto_mode = 999
        elif auto_mode == 80:
            check = ui.update_image_signal()
            if check == 1:
                break
            else:
                auto_mode = 999
        elif auto_mode == 999:
            print("Auto Scaling Error")
            ui.statusbar.showMessage("AUTO SCALING Error")
            raise Exception
    print('Auto Scaling Complete')
    ui.statusbar.showMessage("AUTO SCALING Complete")
     
if __name__ == "__main__":
    try:		
        app = QtWidgets.QApplication(sys.argv)
        mainwindow = QtWidgets.QMainWindow()
        secondwindow = QtWidgets.QMainWindow()
        signalComm = SignalCommunication()	
        ui = Ui_mainwindow()
        c_ui = Ui_w_calibration()
        ui.setupUi(mainwindow)
        c_ui.setupUi(secondwindow)
        mainwindow.show()
        sys.exit(app.exec_())
    except Exception as ex:
        print(ex)
        exit()

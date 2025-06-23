# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'lab0.ui'
##
## Created by: Qt User Interface Compiler version 6.9.0
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QComboBox, QGroupBox, QLineEdit,
    QPushButton, QSizePolicy, QWidget)

class Ui_formWidget(object):
    def setupUi(self, formWidget):
        if not formWidget.objectName():
            formWidget.setObjectName(u"formWidget")
        formWidget.resize(858, 663)
        self.port_groupBox = QGroupBox(formWidget)
        self.port_groupBox.setObjectName(u"port_groupBox")
        self.port_groupBox.setGeometry(QRect(10, 0, 321, 80))
        self.port_select_comboBox = QComboBox(self.port_groupBox)
        self.port_select_comboBox.setObjectName(u"port_select_comboBox")
        self.port_select_comboBox.setGeometry(QRect(20, 30, 111, 24))
        self.connect_Button = QPushButton(self.port_groupBox)
        self.connect_Button.setObjectName(u"connect_Button")
        self.connect_Button.setGeometry(QRect(140, 30, 75, 24))
        self.disconnect_Button = QPushButton(self.port_groupBox)
        self.disconnect_Button.setObjectName(u"disconnect_Button")
        self.disconnect_Button.setGeometry(QRect(220, 30, 75, 24))
        self.graph_groupBox = QGroupBox(formWidget)
        self.graph_groupBox.setObjectName(u"graph_groupBox")
        self.graph_groupBox.setGeometry(QRect(10, 80, 791, 471))
        self.motorSpeed_widget = QWidget(self.graph_groupBox)
        self.motorSpeed_widget.setObjectName(u"motorSpeed_widget")
        self.motorSpeed_widget.setGeometry(QRect(20, 20, 751, 200))
        self.current_widget = QWidget(self.graph_groupBox)
        self.current_widget.setObjectName(u"current_widget")
        self.current_widget.setGeometry(QRect(20, 260, 751, 200))
        self.command_groupBox = QGroupBox(formWidget)
        self.command_groupBox.setObjectName(u"command_groupBox")
        self.command_groupBox.setGeometry(QRect(10, 550, 571, 101))
        self.a0_pushButton = QPushButton(self.command_groupBox)
        self.a0_pushButton.setObjectName(u"a0_pushButton")
        self.a0_pushButton.setGeometry(QRect(10, 20, 75, 24))
        self.a1_pushButton = QPushButton(self.command_groupBox)
        self.a1_pushButton.setObjectName(u"a1_pushButton")
        self.a1_pushButton.setGeometry(QRect(10, 60, 75, 24))
        self.d0_pushButton = QPushButton(self.command_groupBox)
        self.d0_pushButton.setObjectName(u"d0_pushButton")
        self.d0_pushButton.setGeometry(QRect(110, 20, 75, 24))
        self.d1_pushButton = QPushButton(self.command_groupBox)
        self.d1_pushButton.setObjectName(u"d1_pushButton")
        self.d1_pushButton.setGeometry(QRect(110, 60, 75, 24))
        self.speed_lineEdit = QLineEdit(self.command_groupBox)
        self.speed_lineEdit.setObjectName(u"speed_lineEdit")
        self.speed_lineEdit.setGeometry(QRect(220, 20, 113, 21))
        self.speed_pushButton = QPushButton(self.command_groupBox)
        self.speed_pushButton.setObjectName(u"speed_pushButton")
        self.speed_pushButton.setGeometry(QRect(360, 20, 101, 24))
        self.sampling_lineEdit = QLineEdit(self.command_groupBox)
        self.sampling_lineEdit.setObjectName(u"sampling_lineEdit")
        self.sampling_lineEdit.setGeometry(QRect(220, 60, 113, 21))
        self.sampling_pushButton = QPushButton(self.command_groupBox)
        self.sampling_pushButton.setObjectName(u"sampling_pushButton")
        self.sampling_pushButton.setGeometry(QRect(360, 60, 101, 24))
        self.reset_pushButton = QPushButton(self.command_groupBox)
        self.reset_pushButton.setObjectName(u"reset_pushButton")
        self.reset_pushButton.setGeometry(QRect(480, 40, 75, 24))
        self.control_groupBox = QGroupBox(formWidget)
        self.control_groupBox.setObjectName(u"control_groupBox")
        self.control_groupBox.setGeometry(QRect(380, 0, 251, 80))
        self.control_comboBox = QComboBox(self.control_groupBox)
        self.control_comboBox.setObjectName(u"control_comboBox")
        self.control_comboBox.setGeometry(QRect(20, 30, 131, 24))
        self.select_pushButton = QPushButton(self.control_groupBox)
        self.select_pushButton.setObjectName(u"select_pushButton")
        self.select_pushButton.setGeometry(QRect(160, 30, 75, 24))
        self.save_groupBox = QGroupBox(formWidget)
        self.save_groupBox.setObjectName(u"save_groupBox")
        self.save_groupBox.setGeometry(QRect(610, 550, 181, 101))
        self.stop_pushButton = QPushButton(self.save_groupBox)
        self.stop_pushButton.setObjectName(u"stop_pushButton")
        self.stop_pushButton.setGeometry(QRect(10, 20, 75, 24))
        self.start_pushButton = QPushButton(self.save_groupBox)
        self.start_pushButton.setObjectName(u"start_pushButton")
        self.start_pushButton.setGeometry(QRect(10, 50, 75, 24))
        self.save_pushButton = QPushButton(self.save_groupBox)
        self.save_pushButton.setObjectName(u"save_pushButton")
        self.save_pushButton.setGeometry(QRect(100, 40, 75, 24))

        self.retranslateUi(formWidget)

        QMetaObject.connectSlotsByName(formWidget)
    # setupUi

    def retranslateUi(self, formWidget):
        formWidget.setWindowTitle(QCoreApplication.translate("formWidget", u"Form", None))
        self.port_groupBox.setTitle(QCoreApplication.translate("formWidget", u"Port", None))
        self.connect_Button.setText(QCoreApplication.translate("formWidget", u"connect", None))
        self.disconnect_Button.setText(QCoreApplication.translate("formWidget", u"disconnect", None))
        self.graph_groupBox.setTitle(QCoreApplication.translate("formWidget", u"Graph", None))
        self.command_groupBox.setTitle(QCoreApplication.translate("formWidget", u"Command", None))
        self.a0_pushButton.setText(QCoreApplication.translate("formWidget", u"A0", None))
        self.a1_pushButton.setText(QCoreApplication.translate("formWidget", u"A1", None))
        self.d0_pushButton.setText(QCoreApplication.translate("formWidget", u"D0", None))
        self.d1_pushButton.setText(QCoreApplication.translate("formWidget", u"D1", None))
        self.speed_pushButton.setText(QCoreApplication.translate("formWidget", u"Set mortor speed", None))
        self.sampling_pushButton.setText(QCoreApplication.translate("formWidget", u"Set Sampling", None))
        self.reset_pushButton.setText(QCoreApplication.translate("formWidget", u"Reset", None))
        self.control_groupBox.setTitle(QCoreApplication.translate("formWidget", u"Control", None))
        self.select_pushButton.setText(QCoreApplication.translate("formWidget", u"select", None))
        self.save_groupBox.setTitle(QCoreApplication.translate("formWidget", u"Save", None))
        self.stop_pushButton.setText(QCoreApplication.translate("formWidget", u"Stop", None))
        self.start_pushButton.setText(QCoreApplication.translate("formWidget", u"Start", None))
        self.save_pushButton.setText(QCoreApplication.translate("formWidget", u"Save", None))
    # retranslateUi


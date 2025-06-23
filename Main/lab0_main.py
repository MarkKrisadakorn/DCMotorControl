from lab0 import Ui_formWidget as lab0_form
from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtWidgets import QMainWindow, QApplication, QMessageBox, QFileDialog
import sys
import serial.tools.list_ports as list_ports
import serial
import time
import threading
import numpy as np
import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PySide6.QtCore import QTimer
from queue import Queue
import csv

class MyMainWindow(QMainWindow):
    def __init__(self, parent=None):
        super(MyMainWindow, self).__init__(parent)
        self.ui = lab0_form()
        self.ui.setupUi(self)

        # Initialize matplotlib figures for motorSpeed and current
        self.motorSpeed_fig = Figure()
        self.motorSpeed_canvas = FigureCanvas(self.motorSpeed_fig)
        self.ui.motorSpeed_widget.layout = QtWidgets.QVBoxLayout(self.ui.motorSpeed_widget)
        self.ui.motorSpeed_widget.layout.addWidget(self.motorSpeed_canvas)
        self.motorSpeed_ax = self.motorSpeed_fig.add_subplot(111)
        self.motorSpeed_data = np.zeros(100)  # Preallocate array for performance

        self.current_fig = Figure()
        self.current_canvas = FigureCanvas(self.current_fig)
        self.ui.current_widget.layout = QtWidgets.QVBoxLayout(self.ui.current_widget)
        self.ui.current_widget.layout.addWidget(self.current_canvas)
        self.current_ax = self.current_fig.add_subplot(111)
        self.current_data = np.zeros(100)  # Preallocate array for performance

        # Queue for incoming data
        self.data_queue = Queue()

        # State variables
        self.is_plotting = True  # To control plotting
        self.saved_data = []  # To store data for saving
        
        # Flag to control the receive thread
        self.keep_receiving = False

        # Populate available ports
        available_ports = list_ports.comports()
        for port in available_ports:
            self.ui.port_select_comboBox.addItem(port.device)

        # Connect signals and slots
        self.ui.connect_Button.clicked.connect(self.connectSerialPort)
        self.ui.disconnect_Button.clicked.connect(self.disconnectSerialPort)
        self.ui.a0_pushButton.clicked.connect(self.sendCommand)
        self.ui.a1_pushButton.clicked.connect(self.sendCommand)
        self.ui.d0_pushButton.clicked.connect(self.sendCommand)
        self.ui.d1_pushButton.clicked.connect(self.sendCommand)
        self.ui.reset_pushButton.clicked.connect(self.sendCommand)
        self.ui.speed_pushButton.clicked.connect(self.sendCommand)
        self.ui.sampling_pushButton.clicked.connect(self.sendCommand)
        self.ui.stop_pushButton.clicked.connect(self.stop_plotting)
        self.ui.start_pushButton.clicked.connect(self.start_plotting)
        self.ui.save_pushButton.clicked.connect(self.save_data)

        # Timer for refreshing plots
        self.plot_timer = QTimer(self)
        self.plot_timer.timeout.connect(self.refresh_plots)
        self.plot_timer.start(100)  # Refresh every 100ms

        self.receive_thread = None
        self.serial_port = None

    def connectSerialPort(self):
        if self.ui.port_select_comboBox.currentText() == '':
            QMessageBox.warning(self, "Warning", "Please select a port.")
            return
        try:
            self.serial_port = serial.Serial(self.ui.port_select_comboBox.currentText(), 115200, timeout=1)
            self.ui.port_select_comboBox.setEnabled(False)
            self.ui.connect_Button.setEnabled(False)

            # Set flag to enable data reception
            self.keep_receiving = True
            
            # Start the receive_data thread
            self.receive_thread = threading.Thread(target=self.receive_data, daemon=True)
            self.receive_thread.start()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open port: {e}")

    def disconnectSerialPort(self):
        try:
            # First stop the motor by sending speed 0 command
            if hasattr(self, 'serial_port') and self.serial_port and self.serial_port.is_open:
                # Send command to stop motor
                self.serial_port.write(('s,0\n').encode('utf-8'))
                time.sleep(0.1)
                
                # Send command to disable data streaming
                self.serial_port.write(('a,0\n').encode('utf-8'))
                time.sleep(0.1)
                
                # Update UI to reflect data streaming is disabled
                self.ui.a0_pushButton.setEnabled(True)
                self.ui.a1_pushButton.setEnabled(True)
                
                # Stop the receive thread
                self.keep_receiving = False
                
                # Close the serial port
                self.serial_port.close()
                
            self.ui.port_select_comboBox.setEnabled(True)
            self.ui.connect_Button.setEnabled(True)
            
            # Stop plotting data
            self.is_plotting = False
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to close port: {e}")

    def receive_data(self):
        while self.keep_receiving:
            try:
                if self.serial_port and self.serial_port.is_open and self.serial_port.in_waiting > 0:
                    data = self.serial_port.readline().decode('utf-8').strip()
                    self.data_queue.put(data)  # Add data to the queue
            except Exception as e:
                # If an exception occurs, likely the port was closed
                self.keep_receiving = False
                break
            time.sleep(0.01)  # Small delay to prevent CPU hogging

    def stop_plotting(self):
        """Stop updating the plots."""
        self.is_plotting = False

    def start_plotting(self):
        """Clear data and resume plotting."""
        self.motorSpeed_data = np.zeros(100)
        self.current_data = np.zeros(100)
        self.saved_data = []  # Clear saved data
        self.is_plotting = True

    def save_data(self):
        """Open File Explorer to save data in .csv format."""
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Data", "", "CSV Files (*.csv)")
        if file_path:
            try:
                with open(file_path, 'w', newline='') as file:
                    writer = csv.writer(file)
                    writer.writerow(["Motor Direction", "Motor Speed", "Current"])
                    writer.writerows(self.saved_data)
                QMessageBox.information(self, "Success", "Data saved successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save data: {e}")

    def refresh_plots(self):
        """Refresh the plots if plotting is enabled."""
        if not self.is_plotting:
            return

        # Process all data in the queue
        while not self.data_queue.empty():
            data = self.data_queue.get()
            self.plot_data(data)

        # Redraw the plots
        self.motorSpeed_canvas.draw_idle()
        self.current_canvas.draw_idle()

    def plot_data(self, data):
        try:
            # Check if the data has the expected format with commas
            if ',' not in data:
                return
                
            parts = data.split(',')
            if len(parts) != 3:
                return
                
            motorDirection, motorSpeed, current = parts
            motorSpeed = float(motorSpeed)
            current = float(current)

            # Save data for exporting
            self.saved_data.append([motorDirection, motorSpeed, current])

            # Update motorSpeed data
            self.motorSpeed_data = np.roll(self.motorSpeed_data, -1)
            self.motorSpeed_data[-1] = motorSpeed

            # Update current data
            self.current_data = np.roll(self.current_data, -1)
            self.current_data[-1] = current

            # Update motorSpeed plot
            if not hasattr(self, 'motorSpeed_line'):
                self.motorSpeed_line, = self.motorSpeed_ax.plot(self.motorSpeed_data, label="Motor Speed")
                self.motorSpeed_ax.legend(loc='upper left', fontsize='small')
            else:
                self.motorSpeed_line.set_data(range(len(self.motorSpeed_data)), self.motorSpeed_data)
                self.motorSpeed_ax.relim()
                self.motorSpeed_ax.autoscale_view()

            # Update current plot
            if not hasattr(self, 'current_line'):
                self.current_line, = self.current_ax.plot(self.current_data, label="Current", color='orange')
                self.current_ax.legend(loc='upper left', fontsize='small')
            else:
                self.current_line.set_data(range(len(self.current_data)), self.current_data)
                self.current_ax.relim()
                self.current_ax.autoscale_view()

        except ValueError:
            # Invalid data format - just ignore
            pass
        except Exception as e:
            print(f"Error in plot_data: {e}")

    def sendCommand(self):
        if not hasattr(self, 'serial_port') or not self.serial_port or not self.serial_port.is_open:
            QMessageBox.warning(self, "Warning", "Please connect to a port first.")
            return

        sender = self.sender()
        command = sender.text().lower()

        if sender == self.ui.speed_pushButton:
            value = self.ui.speed_lineEdit.text()
            if not value.isdigit() or not (0 <= int(value) <= 255):
                QMessageBox.warning(self, "Warning", "Please enter a valid number for speed (0-255).")
                return
            command = f"s,{value}"
        elif sender == self.ui.sampling_pushButton:
            value = self.ui.sampling_lineEdit.text()
            if not value.isdigit():
                QMessageBox.warning(self, "Warning", "Please enter a valid number for sampling.")
                return
            command = f"i,{value}"
        else:
            match sender.text().lower():
                case 'reset':
                    command = 'r'
                case 'a0':
                    command = 'a,0'
                    self.ui.a0_pushButton.setEnabled(False)
                    self.ui.a1_pushButton.setEnabled(True)
                case 'a1':
                    command = 'a,1'
                    self.ui.a1_pushButton.setEnabled(False)
                    self.ui.a0_pushButton.setEnabled(True)
                case 'd0':
                    command = 'd,0'
                    self.ui.d0_pushButton.setEnabled(False)
                    self.ui.d1_pushButton.setEnabled(True)
                case 'd1':
                    command = 'd,1'
                    self.ui.d1_pushButton.setEnabled(False)
                    self.ui.d0_pushButton.setEnabled(True)
                case _:
                    QMessageBox.warning(self, "Warning", "Unknown command.")
                    return

        try:
            self.serial_port.write((command + '\n').encode('utf-8'))
            time.sleep(0.1)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to send command: {e}")
            # Try to reconnect or handle the error
            self.disconnectSerialPort()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    MainWindow = MyMainWindow()
    MainWindow.show()
    sys.exit(app.exec())
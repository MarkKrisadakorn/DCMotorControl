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
from P_Controller import P_Controller
from PI_Cotroller import PI_Controller
from PID_Controller import PID_Controller

class MyMainWindow(QMainWindow):
    def __init__(self, parent=None):
        super(MyMainWindow, self).__init__(parent)
        self.ui = lab0_form()
        self.ui.setupUi(self)
        self.Kp = 1.0
        self.Ki = 0.1
        self.Kd = 0.05
        
        # Scaling factor for converting RPM to PWM (0-255)
        # Based on observed behavior: 100 PWM ≈ 10,000 RPM, so PWM = RPM * 0.01
        self.rpm_to_pwm_scale = 0.01
        
        # Initialize controller variables
        self.controller = None
        self.controller_type = None
        self.setpoint = 0
        self.last_time = time.time()
        self.using_controller = False

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
        
        # Thread safety lock for shared data
        self.data_lock = threading.Lock()

        # State variables
        self.is_plotting = True  # To control plotting
        self.saved_data = []  # To store data for saving
        
        # Flag to control the receive thread
        self.keep_receiving = False

        # Populate available ports
        available_ports = list_ports.comports()
        for port in available_ports:
            self.ui.port_select_comboBox.addItem(port.device)

        # Populate Controller options
        self.ui.control_comboBox.addItem("None")
        self.ui.control_comboBox.addItem("P_Controller")
        self.ui.control_comboBox.addItem("PI_Controller")
        self.ui.control_comboBox.addItem("PID_Controller")
        self.ui.select_pushButton.clicked.connect(self.selectController)

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
        
        # Timer for controller execution
        self.controller_timer = QTimer(self)
        self.controller_timer.timeout.connect(self.execute_controller)
        self.controller_timer.start(50)  # Execute controller every 50ms

        self.receive_thread = None
        self.serial_port = None
        
        # No automatic controller initialization

    def initialize_controller(self):
        """Initialize the controller based on the selected type."""
        if not self.controller_type:
            self.using_controller = False
            return
            
        # Convert PWM setpoint to RPM equivalent for controller
        rpm_setpoint = self.setpoint / self.rpm_to_pwm_scale
        # print(f"Converting setpoint: {self.setpoint} PWM → {rpm_setpoint:.2f} RPM (scale factor: {self.rpm_to_pwm_scale})")
            
        if self.controller_type == "P_Controller":
            self.controller = P_Controller(self.Kp, rpm_setpoint)
        elif self.controller_type == "PI_Controller":
            self.controller = PI_Controller(self.Kp, self.Ki, rpm_setpoint)
        elif self.controller_type == "PID_Controller":
            self.controller = PID_Controller(self.Kp, self.Ki, self.Kd, rpm_setpoint)
        else:
            QMessageBox.warning(self, "Warning", "Unknown controller type.")
            self.using_controller = False

    def execute_controller(self):
        """Execute the control loop if controller is active."""
        if not self.using_controller or not self.controller or not hasattr(self, 'serial_port') or not self.serial_port or not self.serial_port.is_open:
            return
            
        # Get current speed from the data (most recent value) with thread safety
        current_speed = None
        with self.data_lock:
            if len(self.motorSpeed_data) > 0 and np.any(self.motorSpeed_data):
                # Convert back from display value to actual RPM for controller
                current_speed = self.motorSpeed_data[-1] * 100.0
        
        if current_speed is None:
            return  # No valid speed data available
            
        # Calculate time delta for controllers that need it
        current_time = time.time()
        dt = current_time - self.last_time
        self.last_time = current_time
        
        # Compute control output based on controller type
        try:
            if self.controller_type == "P_Controller":
                rpm_correction = self.controller.compute(current_speed)
            elif self.controller_type == "PI_Controller":
                rpm_correction = self.controller.compute(current_speed, dt)
            elif self.controller_type == "PID_Controller":
                rpm_correction = self.controller.compute(current_speed, dt)
            else:
                return
                
            # Convert RPM correction back to PWM and add to base setpoint
            control_output = self.setpoint + (rpm_correction * self.rpm_to_pwm_scale)
            
            # Debug output for monitoring
            # print(f"Controller: Current={current_speed:.1f} RPM, Correction={rpm_correction:.1f} RPM, Output={control_output:.1f} PWM")
            
        except Exception as e:
            # print(f"Error in controller computation: {e}")
            self.using_controller = False
            QMessageBox.warning(self, "Controller Error", 
                               f"Controller computation failed: {e}\nController has been disabled.")
            return
            
        # Ensure control output is within valid range for motor speed (0-255)
        control_output = max(0, min(255, int(control_output)))
        
        # Safety check: Prevent sending 0 if motor was running (avoid sudden stops)
        if control_output == 0 and current_speed > 5:  # If motor is running but output is 0
            control_output = 10  # Minimum safe speed to maintain some movement
            # print(f"Safety override: Prevented 0 output when motor running at {current_speed} RPM")
        
        # Store last control output for debugging
        self.last_control_output = control_output
        
        # Send command to motor
        try:
            command = f"s,{control_output}"
            self.serial_port.write((command + '\n').encode('utf-8'))
        except Exception as e:
            # print(f"Error sending control command: {e}")
            self.using_controller = False
            QMessageBox.warning(self, "Communication Error", 
                               f"Failed to send control command: {e}\nController has been disabled.")
            # Try to reconnect
            self.disconnectSerialPort()

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
            # Disable controller first
            self.using_controller = False
            
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


    def selectController(self):
        selected_controller = self.ui.control_comboBox.currentText()

        # If "None" is chosen, disable the controller but keep motor running
        if selected_controller == "None":
            # Disable the controller but maintain current motor speed
            self.using_controller = False
            self.controller_type = None
            
            # Get the current speed setting to maintain it with improved safety
            current_setpoint = 0
            
            # Priority 1: Use current controller setpoint if available
            if hasattr(self, 'setpoint') and self.setpoint is not None and self.setpoint > 0:
                current_setpoint = self.setpoint
                # print(f"Using current setpoint: {current_setpoint}")
                
            # Priority 2: Use valid UI input
            elif self.ui.speed_lineEdit.text() and self.ui.speed_lineEdit.text().isdigit():
                input_value = int(self.ui.speed_lineEdit.text())
                if 0 <= input_value <= 255:
                    current_setpoint = input_value
                    # print(f"Using UI input: {current_setpoint}")
                    
            # Priority 3: Use current motor speed (PREVENT STOPPING)
            elif len(self.motorSpeed_data) > 0 and np.any(self.motorSpeed_data):
                with self.data_lock:  # Thread-safe access
                    # Convert back from display value to actual RPM
                    motor_speed = self.motorSpeed_data[-1] * 100.0
                
                if motor_speed > 0:  # Only if motor is running
                    # Convert to PWM with minimum threshold to ensure movement
                    current_setpoint = min(255, max(30, int(motor_speed * self.rpm_to_pwm_scale)))
                    # print(f"Using current motor speed: {motor_speed} RPM → {current_setpoint} PWM")
                else:
                    current_setpoint = 50  # Safe low speed instead of 0
                    # print("Motor not running, using safe default: 50")


            # Maintain current motor speed by sending direct command
            if hasattr(self, 'serial_port') and self.serial_port and self.serial_port.is_open:
                try:
                    command = f"s,{current_setpoint}"
                    self.serial_port.write((command + '\n').encode('utf-8'))
                    # QMessageBox.information(self, "Info", f"Controller disabled. Motor running at speed: {current_setpoint}")
                except Exception as e:
                    # print(f"Error sending motor command: {e}")
                    QMessageBox.warning(self, "Warning", f"Failed to maintain motor speed: {e}")
            return
        
        # For actual controller selection, get current setpoint with improved safety
        setpoint_determined = False
        
        # Priority 1: Use valid UI input
        if self.ui.speed_lineEdit.text() and self.ui.speed_lineEdit.text().isdigit():
            input_value = int(self.ui.speed_lineEdit.text())
            if 0 <= input_value <= 255:  # Validate range
                self.setpoint = input_value
                setpoint_determined = True
                # print(f"Using UI setpoint: {self.setpoint}")
        
        # Priority 2: Smart handling - Use last controller output OR warn for manual input
        if not setpoint_determined:
            # Check if we have previous controller data to use
            if hasattr(self, 'last_control_output') and self.last_control_output > 0:
                # Use previous controller output automatically (smooth transition)
                self.setpoint = self.last_control_output
                self.ui.speed_lineEdit.setText(str(self.setpoint))
                setpoint_determined = True
                # print(f"Using last control output as setpoint: {self.setpoint}")
            elif len(self.motorSpeed_data) > 0 and np.any(self.motorSpeed_data):
                # No previous controller data, but motor is running - require user input
                with self.data_lock:  # Thread-safe access
                    # Convert back from display value to actual RPM
                    current_speed = self.motorSpeed_data[-1] * 100.0
                
                if current_speed > 0:  # Motor is running but no previous controller data
                    QMessageBox.warning(self, "Input Required", "Please input speed before start running")
                    return
        
        # Priority 3: Guide user to input speed
        if not setpoint_determined:
                QMessageBox.information(self, "Speed Required", "Please enter a speed value (0-255) in the speed field before selecting a controller.")
                return
        
        # Smoothly transition to the new controller
        old_controller_type = self.controller_type
        self.controller_type = selected_controller
        
        # Store the last control output if we were already using a controller
        last_control_output = None
        if self.using_controller and self.controller:
            # This would require adding code to store the last output in your controller classes
            # For now, we'll estimate it based on the current speed
            if len(self.motorSpeed_data) > 0 and np.any(self.motorSpeed_data):
                # Convert back from display value to actual RPM
                motor_speed_rpm = self.motorSpeed_data[-1] * 100.0
                last_control_output = min(255, max(0, int(motor_speed_rpm * self.rpm_to_pwm_scale)))
        
        # Initialize the new controller with validation
        if setpoint_determined:
            self.initialize_controller()
            
            # Validate controller was created successfully
            if not self.controller:
                QMessageBox.critical(self, "Controller Error", 
                                   f"Failed to initialize {selected_controller}")
                return
                
            # Send initial command with the determined setpoint
            if hasattr(self, 'serial_port') and self.serial_port and self.serial_port.is_open:
                try:
                    # Ensure setpoint is within valid range before sending
                    safe_setpoint = min(255, max(0, int(self.setpoint)))
                    command = f"s,{safe_setpoint}"
                    self.serial_port.write((command + '\n').encode('utf-8'))
                    # print(f"Sent initial command: {command}")
                except Exception as e:
                    # print(f"Error sending initial control command: {e}")
                    QMessageBox.warning(self, "Communication Error", 
                                       f"Failed to send initial command: {e}")
                    return
            
            # Activate the controller
            self.using_controller = True
            self.last_time = time.time()  # Reset timer for dt calculations
            
            # Success message with details
            QMessageBox.information(self, "Controller Activated", 
                                   f"Successfully activated {selected_controller}\n"
                                   f"Setpoint: {self.setpoint} PWM\n"
                                   f"Previous: {old_controller_type if old_controller_type else 'Manual Control'}")
            # print(f"Controller activated: {selected_controller} with setpoint {self.setpoint}")
        else:
            # This should not happen with the new logic, but just in case
            QMessageBox.critical(self, "Error", "Failed to determine appropriate setpoint for controller.")


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
        with self.data_lock:
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

            # Divide motor speed by 100 for better graph visualization
            motorSpeed_display = motorSpeed / 100.0

            # Save original data for exporting (keep original RPM values)
            self.saved_data.append([motorDirection, motorSpeed, current])

            # Update motorSpeed and current data with thread safety
            with self.data_lock:
                # Update motorSpeed data (use divided value for display)
                self.motorSpeed_data = np.roll(self.motorSpeed_data, -1)
                self.motorSpeed_data[-1] = motorSpeed_display

                # Update current data
                self.current_data = np.roll(self.current_data, -1)
                self.current_data[-1] = current

            # Update plots with thread-safe data access
            with self.data_lock:
                # Update motorSpeed plot
                if not hasattr(self, 'motorSpeed_line'):
                    self.motorSpeed_line, = self.motorSpeed_ax.plot(self.motorSpeed_data, label="Motor Speed")
                    self.motorSpeed_ax.legend(loc='upper left', fontsize = 'x-small')
                else:
                    self.motorSpeed_line.set_data(range(len(self.motorSpeed_data)), self.motorSpeed_data)
                    self.motorSpeed_ax.relim()
                    self.motorSpeed_ax.autoscale_view()

                # Update current plot
                if not hasattr(self, 'current_line'):
                    self.current_line, = self.current_ax.plot(self.current_data, label="Current", color='orange')
                    self.current_ax.legend(loc='upper left', fontsize = 'x-small')
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
                
            speed_value = int(value)
                      
            # Update setpoint for controller
            self.setpoint = speed_value
            
            # Re-initialize controller with new setpoint if a controller is already selected
            if self.controller_type and self.using_controller:
                self.initialize_controller()
            else:
                # If no controller is active, send the speed command directly
                command = f"s,{speed_value}"
        
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
                    # If resetting, disable controller but don't update UI
                    previous_controller = self.controller_type
                    self.using_controller = False
                    QMessageBox.information(self, "Info", f"Reset encoder. Controller {previous_controller} disabled.")
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
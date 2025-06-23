class PID_Controller:
    def __init__(self, Kp, Ki, Kd, setpoint):
        self.Kp = Kp
        self.Ki = Ki
        self.Kd = Kd
        self.setpoint = setpoint
        self.previous_error = 0
        self.integral = 0

    def compute(self, process_variable, TIME):
        # calculate eror
        error = self.setpoint - process_variable

        # proportional term
        P_out = self.Kp * error

        # Integral term
        self.integral += error * TIME
        I_out = self.Ki * self.integral

        #Derivative term
        derivative = (error - self.previous_error)/TIME
        D_out = self.Kd * derivative

        # compute total output
        output = P_out + I_out + D_out

        # update previous error
        self.previous_error = error

        return output
    



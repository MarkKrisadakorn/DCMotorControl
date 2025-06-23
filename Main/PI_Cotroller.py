class PI_Controller:
    def __init__(self, Kp, Ki, setpoint):
        self.Kp = Kp
        self.Ki = Ki
        self.setpoint = setpoint
        self.previous_error = 0
        self.integral = 0

    def compute(self, process_variable, dt):
        # calculate eror
        error = self.setpoint - process_variable

        # proportional term
        P_out = self.Kp * error

        # Integral term
        self.integral += error * dt
        I_out = self.Ki * self.integral

        # compute total output
        output = P_out + I_out 

        # update previous error
        self.previous_error = error

        return output
    



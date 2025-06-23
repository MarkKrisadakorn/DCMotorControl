class P_Controller:
    def __init__(self, Kp, setpoint):
        self.Kp = Kp
        self.setpoint = setpoint
        self.previous_error = 0
        self.integral = 0

    def compute(self, process_variable):
        # calculate eror
        error = self.setpoint - process_variable

        # proportional term
        P_out = self.Kp * error

        # compute total output
        output = P_out 

        # update previous error
        self.previous_error = error

        return output
    



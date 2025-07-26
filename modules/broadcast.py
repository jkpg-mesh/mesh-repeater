import time

class broadcast:
    def __init__(self,interface=None, freq=300, msg="Hello Jönköping!"):
        """
        This class handles broadcasting messages to all nodes in the network.
        :param interface: The interface to send messages through.
        :param freq: Frequency of broadcasting messages in seconds. Default is 300 seconds (5 minutes).
        :param msg: The message to broadcast. Default is "Hello Jönköping!"
        """
        self.interface = interface
        self.broadcast_freq = freq
        self.broadcast_msg = msg
        self.status = False
        self.Duty_cycle = 0.0
        self.emergancy_status = False
        self.emergancy_msg = ""
        self.emergancy_freq = freq

    def run(self):
        """ 
        This method runs the broadcast loop, sending messages at specified intervals.
        It also handles emergency messages if the emergency status is enabled.
        """
        self.status = True
        counter = 0
        while self.status:
            if self.emergancy_status == False:
                if counter>self.broadcast_freq:
                    self.Duty_cycle = self.calculate_duty_cycle()
                    if self.Duty_cycle <= 3.0:
                        # broadcast message to all nodes
                        self.interface.sendText(text=self.broadcast_msg, destinationId='^all')
                        counter=0
                    else:
                        counter = counter - 60  # Reduce counter by 60 seconds if duty cycle is high
                counter += 1
                time.sleep(1)
            elif self.emergancy_status == True:
                if counter>self.emergancy_freq:
                    # broadcast message to all nodes
                    self.interface.sendText(text=self.emergancy_msg, destinationId='^all')
                    counter=0
                counter += 1
                time.sleep(1)

    def stop(self):
        """
        This method stops the broadcast loop by setting the status to False.
        """
        self.status = False
    
    def numToHex(self,node_num):
        """ Converts a node number to a hexadecimal string prefixed with '!'.
        :param node_num: The node number to convert.
        :return: A string representing the node number in hexadecimal format.
        """
        return '!' + hex(node_num)[2:]
    
    def calculate_duty_cycle(self):
        """
        This method calculates the duty cycle of the local node based on its device metrics.
        It retrieves the air utilization metric and returns it as a float.
        :return: Duty cycle as a float.
        """
        my_node_num = self.interface.localNode.nodeNum
        local_node = self.interface.nodes.get(self.numToHex(node_num=my_node_num), {})
        metrics = local_node.get("deviceMetrics", {})
        duty_cycle = metrics.get("airUtilTx")
        return float(duty_cycle)

    def start_emergency(self, msg, freq=60):
        """
        Enables an emergency message to all nodes
        """
        self.emergancy_status = True
        self.emergancy_msg = msg
        self.emergancy_freq = freq

    def stop_emergency(self):
        """
        Stop sending emergency messages
        """
        self.emergancy_status = False
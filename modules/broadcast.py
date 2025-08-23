import time

class broadcast:
    def __init__(self,interface=None, config=None, shared_data=None):
        """
        This class handles broadcasting messages to all nodes in the network.
        :param interface: The interface to send messages through.
        :param config: Configuration dictionary containing broadcast settings.
        """
        self.interface = interface
        self.config = config
        self.status = False
        self.Duty_cycle = 0.0
        self.shared_data = shared_data

    def run(self):
        """ 
        This method runs the broadcast loop, sending messages at specified intervals.
        It also handles emergency messages if the emergency status is enabled.
        """
        self.status = True
        self.shared_data.set_counter(int(self.config.get('broadcast_freq', 300)))

        last_emergency_state = False  # Track previous state

        while self.status:
            if self.config.get("broadcast_on") != "Enabled":
                time.sleep(1)
                continue

            counter = self.shared_data.get_counter()
            emergency_on = self.config.get("emergency_on") == "Enabled"

            # Detect change in emergency state
            if emergency_on != last_emergency_state:
                if emergency_on:
                    # Emergency just enabled → reset counter for emergency freq
                    freq = int(self.config.get("emergency_freq", 300))
                    self.shared_data.set_counter(freq)
                else:
                    # Emergency just disabled → reset counter for normal broadcast freq
                    freq = int(self.config.get("broadcast_freq", 300))
                    self.shared_data.set_counter(freq)

                counter = self.shared_data.get_counter()  # refresh local counter

            last_emergency_state = emergency_on

            if counter <= 0:
                if emergency_on:
                    # Emergency broadcast
                    msg = self.config.get("emergency_message", "Error")
                    freq = int(self.config.get("emergency_freq", 300))
                    self.interface.sendText(text=msg, destinationId="^all")
                    self.shared_data.set_counter(freq)

                else:
                    # Normal broadcast
                    self.Duty_cycle = self.calculate_duty_cycle()
                    if self.Duty_cycle <= 3.0:
                        msg = self.config.get("broadcast_message", "Hello Jönköping!")
                        met = self.shared_data.get_metdata()
                        met_msg = (
                            f"\n T1:{met['temp1']:.1f}C"
                            f" T2:{met['temp2']:.1f}C"
                            f" H:{met['humidity']:.1f}%"
                            f" Pstat:{met['pressure_station']:.1f}hPa"
                            f" Psea:{met['pressure_sea']:.1f}hPa"
                        )
                        msg += met_msg
                        freq = int(self.config.get("broadcast_freq", 300))
                        self.interface.sendText(text=msg, destinationId="^all")
                        self.shared_data.set_counter(freq)
                    else:
                        # Duty cycle too high → retry sooner
                        self.shared_data.set_counter(60)
            else:
                self.shared_data.set_counter(counter - 1)

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
        if duty_cycle is None:
            return 0.0
        return float(duty_cycle)
import time
from tinydb import Query

class dbsync:
    """
    This class updates a local tinydb database  
    """

    def __init__(self, interface=None, config=None, nodesdb=None):
        """
        Initialize the dbsync class with the interface, config, and nodesdb.
        :param interface: The interface object for the meshtastic unit.
        :param config: The configuration object that contains sync frequency.
        :param nodesdb: The tinydb database object where node information will be stored.
        """
        self.interface = interface
        self.config = config
        self.nodesdb = nodesdb
        self.freq = int(self.config.get('sync_frequency',43200))
        self.status = False

    def run(self):
        """
        Run the dbsync process to periodically update the local database with the device's node information.
        This method runs in a loop, checking the device's nodes and updating the local database every `freq` seconds.
        """
        self.status = True
        counter = 0
        while self.status:
            if counter>self.freq:
                nodeQ = Query()
                # updare the local db with the device db
                for node in self.interface.nodes.values():
                    user = node.get('user', {})
                    self.nodesdb.upsert({
                        'num': node.get('num'),
                        'id': user.get('id',''),
                        'longName': user.get('longName',''),
                        'shortName': user.get('shortName',''),
                        'macaddr': user.get('macaddr',''),
                        'hwModel': user.get('hwModel','')
                    }, nodeQ.num == node.get('num'))
                counter=0
            counter += 1
            time.sleep(1)

    def stop(self):
        """
        Stop the dbsync process.
        This method sets the status to False, which will break the loop in the run method.
        """
        self.status = False

    def now(self):
        """
        Immediately update the local database with the current device node information.
        This method is useful for manually triggering an update without waiting for the next scheduled sync.
        """
        nodeQ = Query()
        # updare the local db with the device db
        for node in self.interface.nodes.values():
            user = node.get('user', {})
            self.nodesdb.upsert({
                'num': node.get('num'),
                'id': user.get('id',''),
                'longName': user.get('longName',''),
                'shortName': user.get('shortName',''),
                'macaddr': user.get('macaddr',''),
                'HarhwModel': user.get('hwModel','')
            }, nodeQ.num == node.get('num'))
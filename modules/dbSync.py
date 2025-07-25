import time
from tinydb import Query

class dbsync:
    """
    This class updates a local tinydb database  
    """

    def __init__(self, nodesdb=None, interface=None, freq=3600):
        self.nodesdb = nodesdb
        self.interface = interface
        self.freq = freq
        self.status = False

    def run(self):
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
                        'HarhwModel': user.get('hwModel','')
                    }, nodeQ.num == node.get('num'))
                counter=0
            counter += 1
            time.sleep(1)

    def stop(self):
        self.status = False

    def now(self):
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
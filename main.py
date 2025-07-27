"""
Jönköping Mesh Repeater - A Meshtastic Utility

License: MIT
Repository: https://github.com/jkpg-mesh/mesh-repeater

Description:
This application enables a Meshtastic united connected to the processing unit
to serve as a 'repeater' that can server the community base.  It was written 
with the ability to add additional modules or functions. 

Run this on a PC or Raspberry Pi connected to a Meshtastic device over USB.

The NodeBD and related functions are created since the device nodedb can only store 
100 nodes and then its starts writting over the oldest nodes.  In addition the 
last heard is controlled by the repeater app.
"""

import json, logging, os, threading, time
import meshtastic, meshtastic.serial_interface
from datetime import datetime, timedelta
from tinydb import TinyDB, Query
from pubsub import pub
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich import box

import modules.dbSync as dbSync
import modules.broadcast as broadcast
import modules.WebUI as WebUI
import tools.general as general_tools

# startup dialog functions 
def clear_screen():
    # Clears the terminal screen
    os.system('cls' if os.name == 'nt' else 'clear')

def init_startup_screen():
    global console

    console = Console(force_terminal=True)
    clear_screen()

    # Your provided ASCII art
    mesh_repeater_ascii = """
    _ _                                          _     
   (_) | ___ __   __ _       _ __ ___   ___  ___| |__  
   | | |/ / '_ \\ / _` |_____| '_ ` _ \\ / _ \\/ __| '_ \\ 
   | |   <| |_) | (_| |_____| | | | | |  __/\\__ \\ | | |
  _/ |_|\\_\\ .__/ \\__, |     |_| |_| |_|\\___||___/_| |_|
 |__/     |_|    |___/                                 
  ____                       _                         
 |  _ \\ ___ _ __   ___  __ _| |_ ___ _ __              
 | |_) / _ \\ '_ \\ / _ \\/ _` | __/ _ \\ '__|             
 |  _ <  __/ |_) |  __/ (_| | ||  __/ |                
 |_| \\_\\___| .__/ \\___|\\__,_|\\__\\___|_|                
           |_|                                         
    """

    # Apply rich styling to the ASCII art
    # You can customize the color (e.g., "bold blue", "green", "yellow on black")
    colored_ascii = Text(mesh_repeater_ascii, style="bold bright_cyan")

    # Display the ASCII art in a Panel for a structured look
    console.print(Panel(colored_ascii, box=box.ROUNDED, title="[bold magenta]System Boot Sequence[/bold magenta]",
                         border_style="green", expand=False))

# convert node id to hex number 
def numToHex(node_num):
    return '!' + hex(node_num)[2:]

# init the logging function
def init_logging():
    log_filename = f"logs/mesh_helper_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    logging.basicConfig(filename=log_filename, level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
    logging.info("Initialized logging...")
    console.print(f"[bold green]✔[/bold green]  Initialized logging...")

# Load configuration
def loadConfig(path='config/config.json'):
    try:
        with open(path, 'r',encoding="utf-8") as f:
            config = json.load(f)
            return config
    except Exception as e:
        logging.error(f"Failed to load config: {e}")
        console.print(f"[bold red]❌[/bold red]  Initialized configuration...")
        return None

# Save configuration
def saveConfig(config, path='config/config.json'):
    try:
        with open(path, 'w',encoding="utf-8") as f:
            json.dump(config, f, indent=4)
            logging.info("Configuration saved successfully...")
            console.print(f"[bold green]✔[/bold green]  Configuration saved successfully...")
    except Exception as e:
        logging.error(f"Failed to save config: {e}")
        console.print(f"[bold red]❌[/bold red]  Failed to save configuration...") 

# init the configuration 
def init_config():
    global config
    config = loadConfig()

    if config == None:
        pass
    else:
        logging.info("Initialized configuration...")
        console.print(f"[bold green]✔[/bold green]  Initialized configuration...")

# init the Tinydb 
def init_db():
    global Nodes, NodeActivities

    db = TinyDB(config.get('database_path', ''))
    Nodes = db.table('Nodes')
    NodeActivities = db.table('NodeActivities')

    sync_now = dbSync.dbsync(nodesdb=Nodes, interface=interface)
    sync_now.now()
    
    logging.info("Initialized Nodedb...")
    console.print(f"[bold green]✔[/bold green]  Initialized Nodedb...")

# update or insert node information
def upsert_nodedb(packet):
    Activity_Time = datetime.now().strftime('%Y%m%d_%H%M%S')
    node = Query()
    decoded = packet.get('decoded')
    user_data = decoded.get('user',{})

    node_num = packet.get('from')
    node_id = packet.get('fromId')
    Long_Name = user_data.get('longName', '')
    Short_Name = user_data.get('shortName', '')
    MacAddr = user_data.get('macaddr', '')
    Hardware_Model = user_data.get('hwModel', '')
    node_activity = packet['decoded']['portnum']

    Nodes.upsert({
        'num': node_num,
        'id': node_id,
        'longName': Long_Name,
        'shortName': Short_Name,
        'macaddr': MacAddr,
        'hwModel': Hardware_Model
    }, node.num == node_num)

    NodeActivities.insert({
        'Num': node_num,
        'id': node_id,
        'Time_Heard': Activity_Time,
        'Activity': node_activity
    })

def upsert_nodedb_activity(packet):
    Activity_Time = datetime.now().strftime('%Y%m%d_%H%M%S')
    node_num = packet.get('from')
    node_id = packet.get('fromId')
    node_activity = packet['decoded']['portnum']
    NodeActivities.insert({
        'Num': node_num,
        'id': node_id,
        'Time_Heard': Activity_Time,
        'Activity': node_activity
    })

# init thr additional modules
def init_modules():
    global broadcaster, syncer
    syncer = dbSync.dbsync(nodesdb=Nodes, interface=interface, freq=config.get('sync_frequency', 7200))
    thread1 = threading.Thread(target=syncer.run, daemon=True)
    thread1.start()
    broadcaster = broadcast.broadcast(interface=interface, freq=config.get('broadcast_freq', 300), msg=config.get('broadcast_message', "Hello Jönköping!"))
    thread2 = threading.Thread(target=broadcaster.run, daemon=True)
    thread2.start()
    webui = WebUI.WebUI(interface=interface, nodesdb=Nodes)
    webui_thread = threading.Thread(target=webui.start, daemon=True)
    webui_thread.start()
    logging.info("Initialized Modules...")
    console.print(f"[bold green]✔[/bold green]  Initialized Modules...")

# command handler function
def command_handler(packet):
    message = packet['decoded']['text']
    # Split by whitespace
    parts = message.strip().split()
    if not parts:
        return "Empty command."

    cmd = parts[0]
    args = parts[1:]

    match cmd:
        case "/info":
            msg = "Welcome to jkpg-mesh! Available commands:\n"
            msg = msg+ "/users - online users\n"
            msg = msg+ "/signal - get signal report\n"
            msg = msg+ "Please wait 10sec before sending sending cmd."
            return msg
        case "/signal":
            # extract rssi and snr from packet and formats return message
            rssi = packet.get('rxRssi')
            snr = packet.get('rxSnr')
            if rssi is not None:
                rssi_msg = f"{round(rssi, 2)} dBm"
            else:
                rssi_msg = "--.-- dBm"
            if snr is not None:
                snr_msg = f"{round(snr, 2)} dB"
            else:
                snr_msg = "--.-- dB"
            msg = f"Repeater received you RSSI: {rssi_msg}  Received SNR: {snr_msg}"
            return msg
        case "/users":
            # Get all nodes active last few minutes from the database and format the return message
            msg = "Recent users:\n"
            nodesAct = Query()
            future_time = datetime.now() - timedelta(minutes=config.get('active_users', 10))
            formatted = future_time.strftime('%Y%m%d_%H%M%S')
            results = NodeActivities.search(nodesAct.Time_Heard >= formatted)
            unique_nums = list({entry['Num'] for entry in results if 'Num' in entry})

            for num in unique_nums:
                nodes = Query()
                node_info = Nodes.search(nodes.num == num)
                for match in node_info:
                    line = f"{match.get('shortName', 'Unknown Node')}\n"
                    if len(msg) + len(line) <= 200:
                        msg += line
                    else:
                        break  # stop adding if we reach the limit
            return msg
        case "/distance":
            # calculate the distance from the repeater to the given coordinates
            try:
                lat2 = float(args[0])
                lon2 = float(args[1])
            except Exception as e:
                return "Please check format /distance 57.1234 14.1234"

            theTools = general_tools.general()
            distance = theTools.get_distance(
                            config.get('repeatar_lat', 0.0),
                            config.get('repeatar_lon', 0.0),
                            lat2, 
                            lon2)
            return f"Your distance from repeater: {round(distance,2)} km"
        case "/admin":
            # Handle admin commands nut how do i do this secure
            msg = ""
            admin_cmd = args[0]
            match admin_cmd:
                case _:
                    msg = "Unknown admin command."
            return msg
        case _:
            return None

# Callback for when a packet is received
def onReceive(packet, interface):
    try:
        # print("-------------------------------------------------------")
        # print(packet)
        # print("-------------------------------------------------------")
        match packet['decoded']['portnum']:
            case "TELEMETRY_APP":
                #Still need to understand what we will do here 
                pass
            case "TEXT_MESSAGE_APP":
                fromId = packet['fromId']
                body = packet['decoded']['text']
                logging.debug(f"Text package message: {body}")
                upsert_nodedb_activity(packet)
                msg = command_handler(packet)
                if msg != None:
                    sendMessage(interface=interface, toID=fromId, message=msg)
            case "POSITION_APP":
                #Still need to understand what we will do here 
                pass
            case "NODEINFO_APP":
                # check if log in DB, if not add. 
                logging.info(f"Id: {packet['decoded']['user']['id']}")
                logging.info(f"Long Name: {packet['decoded']['user']['longName']}") 
                logging.info(f"Short Name: {packet['decoded']['user']['shortName']}") 
                logging.info(f"Hardware Model: {packet['decoded']['user']['hwModel']}")
                upsert_nodedb(packet)
            case "ALERT_APP":
                #Still need to understand what we will do here 
                pass
            case _:
                #Still need to understand what we will do here 
                pass
    except Exception as e:
        logging.warning(f"Error parsing packet: {e}")

# Callback for when the connection is established
def onConnection(interface, topic=pub.AUTO_TOPIC):
    logging.info("Connected to Meshtastic device.")
    myUser = interface.getMyUser()
    logging.info(f"Unit Long Name: {myUser['longName']}")
    logging.info("Unit Short Name: "+myUser['shortName'])
    logging.info(f"Unit Id: {myUser['id']}")
    logging.info(f"Model: {myUser['hwModel']}")

# Callback for when the connection is lost
def onConnectionLost(interface):
    logging.info("Connection lost")

# Send a message to a specific node
def sendMessage(interface, toID, message):
    logging.debug(f"Sending message to {toID}: {message}")
    interface.sendText(text=message, destinationId=toID)

# init Meshtastic
def init_meshunit():
    global interface, MeshError

    interface = None # Initialize interface to None outside the try block

    try:
        # Start the Meshtastic serial interface
        # This might print "No Serial Meshtastic device detected..." if none is found
        interface = meshtastic.serial_interface.SerialInterface()
        logging.info("Meshtastic interface attempting connection...")

        # Give the interface a moment to connect or fail to connect
        time.sleep(3) # A short delay to allow connection attempts

        #Used to check if connected to serial device
        myLongName = interface.getLongName()
        console.print(f"[bold green]✔[/bold green]  Initialized Meshtastic interface...")

        # Subscribe to Meshtastic events
        time.sleep(0.5)
        pub.subscribe(onReceive, "meshtastic.receive")
        console.print(f"[bold green]✔[/bold green]  Initialized onReceive...")
        time.sleep(0.5)
        pub.subscribe(onConnection, "meshtastic.connection.established")
        console.print(f"[bold green]✔[/bold green]  Initialized onConnection...")
        time.sleep(0.5)
        pub.subscribe(onConnectionLost, "meshtastic.connection.lost")
        console.print(f"[bold green]✔[/bold green]  Initialized onConnectionLost...")

        logging.info("Meshtastic function started...")
        console.print(f"[bold green]✔[/bold green]  Meshtastic function started...")

    except Exception as e:
        # Catch any other unexpected errors during the process
        logging.error(f"An unexpected error occurred: {e}")
        console.print(f"[bold red]❌[/bold red]  Meshtastic function started...")
        MeshError = str(e)

# mani function
def main():
    init_startup_screen()
    init_logging()
    init_config()
    init_meshunit()
    init_db()
    init_modules()
    
    logging.info("Initialized Repeater ...")
    console.print(f"[bold green]✔[/bold green]  Initialized Repeater ...")

    while True:
        time.sleep(0.1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logging.info("KeyboardInterrupt caught. Exiting...")
        console.print(f"[bold green]✔[/bold green]  KeyboardInterrupt caught. Exiting...")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # This ensures the connection is closed cleanly whether there was an error or not
        saveConfig(config)
        console.print(f"[bold green]✔[/bold green]  Saving configuration...")
        logging.info("Closing the Meshtastic interface...")
        console.print(f"[bold green]✔[/bold green]  Closing the Meshtastic interface...")
        interface.close()
        logging.info("Meshtastic interface closed...")
        console.print(f"[bold green]✔[/bold green]  Meshtastic interface closed...")
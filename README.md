# Jönköping Mesh Beacon - A Meshtastic Utility

License: MIT  
Repository: https://github.com/jkpg-mesh/mesh-repeater

## Description
This application acts as a **beacon node** for the Meshtastic mesh network in Jönköping.  
It is designed to run on a PC or Raspberry Pi connected to a Meshtastic device via USB.

Unlike a traditional repeater, this utility periodically broadcasts its presence, synchronizes node information, and provides a web interface for monitoring network activity.  
It helps the community by serving as a stable, always-on node that announces itself and tracks active users.

### Key Features
- **Beacon Functionality:** Periodically broadcasts a customizable message to the mesh.
- **Node Database:** Stores extended node info and recent activity beyond the device’s built-in limits.
- **Web UI:** Optional web interface for viewing active nodes and network status.
- **Command Handling:** Responds to basic commands (e.g., `/info`, `/users`, `/signal`, `/distance`) sent via Meshtastic text messages.
- **Extensible:** Easily add new modules or features.

## Requirements
- meshtastic
- tinydb
- rich
- pubsub
- flask

## Usage
1. Connect your Meshtastic device via USB.
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Run the application:
   ```
   python main.py
   ```
4. Access the web interface (if enabled) for node status and activity.

## Notes
- This utility is intended as a **beacon** or “anchor” node, not a message repeater.
- Node activity and user presence are tracked in a local database for improved visibility.
- Configuration options are available in `config/config.json`.

---

For more details, see the [repository](https://github.com/jkpg-mesh/mesh-repeater).
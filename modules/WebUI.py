import logging
import meshtastic.serial_interface
from flask import Flask, render_template, request, flash, redirect, url_for

class WebUI:
    def __init__(self, 
                 interface: meshtastic.serial_interface.SerialInterface = None, 
                 nodesdb=None, 
                 Activity=None,
                 logfiles = None, 
                 config=None,
                 shared_data=None):
        """Initialize the WebUI."""
        self.app = None
        self.interface = interface
        self.nodesdb = nodesdb
        self.nodeactivity = Activity
        self.logfiles = logfiles
        self.config = config if config else {}
        self.shared_data = shared_data
        self.initFlask()

    def initFlask(self):
        """Initialize the Flask application and register routes."""
        self.app = Flask(__name__)
        self.app.config['SECRET_KEY'] = '123456789'
        self.app.config['TEMPLATES_AUTO_RELOAD'] = True
        self.app.logger.setLevel('ERROR')  # Suppress Flask startup messages

        # Suppress Werkzeug request logs
        log = logging.getLogger('werkzeug')
        log.setLevel(logging.ERROR)

        self.app.add_url_rule("/", "index", self.index)
        self.app.add_url_rule("/setup", "setup", self.setup, methods=['GET', 'POST'])
        self.app.add_url_rule("/nodes", "nodes", self.nodes)
        self.app.add_url_rule("/activity", "activity", self.activity)
        self.app.add_url_rule("/logfile", "logfile", self.logfile)
        self.app.add_url_rule("/weather", "weather", self.weather)
        self.app.add_url_rule("/gps", "gps_live", self.gps_live)
        self.app.add_url_rule("/gps_ui", "gps_ui", self.gps_ui)
        self.app.add_url_rule("/messages", "messages", self.messages, methods=['GET', 'POST'])
        self.app.add_url_rule("/get_messages", "get_messages", self.get_messages)
        self.app.add_url_rule("/send_message", "send_message", self.send_message, methods=['POST'])
    
    def index(self):
        """Route for the main index page."""
        info = self.interface.getMyNodeInfo()
        return render_template('index.html', 
                               info=info, 
                               reload_seconds=self.shared_data.get_counter(),
                               broadcast=self.config.get('broadcast_on', 'Disabled'),
                               emergency=self.config.get('emergency_on', 'Disabled'),
                               METdata=self.shared_data.get_metdata())
    
    def setup(self):
        """Route for the setup page (handles GET and POST)."""
        config_items = []
        # Prepare config items with value and description
        for key, value in self.config.items():
            if not key.endswith('_desc'):
                desc = self.config.get(f"{key}_desc", key)
                config_items.append({'key': key, 'value': value, 'desc': desc})

        if request.method == 'POST':
            # Update config values from form
            for item in config_items:
                new_val = request.form.get(item['key'])
                if new_val is not None:
                    self.config[item['key']] = new_val
            flash('Configuration updated successfully! ✅', 'success')
            # Optionally, save config to file here
            return redirect(url_for('setup'))

        return render_template('setup.html', config_items=config_items)

    def nodes(self):
        """
        Route for the nodes page.
        Retrieves all nodes from the database and renders them in the template.
        """
        nodes = self.nodesdb.all()
        return render_template('nodes.html', nodes=nodes)
    
    def activity(self):
        """
        Route for the activity page.
        Retrieves all node activities from the database and renders them in the template.
        """
        activities = self.nodeactivity.all()
        return render_template('activity.html', activity=activities)
    
    def logfile(self):
        """Route for the logfile page.
        Reads the log file and renders its content in the template.
        """
        with open(self.logfiles, 'r') as file:
            log_content = file.read()
        return render_template('logfile.html', info=log_content)

    def weather(self):
        """
        Route for the weather page. Reads MET data log and passes it to the template for graphing.
        """
        import os, json
        met_log_path = os.path.join("logs", "met_data.jsonl")
        met_data = []
        try:
            with open(met_log_path, "r") as f:
                for line in f:
                    try:
                        entry = json.loads(line)
                        met_data.append(entry)
                    except Exception:
                        continue
        except Exception as e:
            met_data = []
        # Sort by timestamp just in case
        met_data.sort(key=lambda x: x.get("timestamp", 0))
        return render_template('weather.html', met_data=met_data)

    def gps_ui(self):
        return render_template("gps.html")

    def gps_live(self):
            """
            Endpoint for live GPS data. Returns JSON for AJAX polling.
            """
            pos = self.shared_data.get_gps_pos()
            fix =self.shared_data.get_gps_fix()
            sats = self.shared_data.get_satellites_in_view()

            gps_data = {
                'fix': fix,
                'latitude': pos.get('latitude', 0),
                'longitude': pos.get('longitude', 0),
                'altitude': pos.get('altitude', 0),
                'altitude_units': pos.get('altitude_units', 0),
                'timestamp': self.shared_data.get_gps_time(),
                'satellites': sats
            }
            from flask import jsonify
            return jsonify(gps_data)

    def messages(self):
        """Main messaging UI page."""
        return render_template("messages.html")

    def get_messages(self):
        """Return list of messages for AJAX polling."""
        from flask import jsonify
        # Assuming shared_data holds message history
        # Example: self.shared_data.messages = [{'from':'me','text':'hi'}, {'from':'node','text':'reply'}]
        return jsonify(self.shared_data.get_messages())

    def send_message(self):
        """Send a new message to the mesh."""
        from flask import request, jsonify
        msg = request.form.get("message", "").strip()
        if msg:
            try:
                # Send using Meshtastic interface
                self.interface.sendText(text=msg, destinationId="^all")
                # Log to shared_data for UI
                self.shared_data.add_message("me", msg)
                return jsonify({"status": "ok", "message": msg})
            except Exception as e:
                return jsonify({"status": "error", "error": str(e)})
        return jsonify({"status": "error", "error": "Empty message"})

    def start(self):
        """Start the WebUI server thread.
        This method runs the Flask app in a separate thread.
        """
        try:
            self.app.run(debug=False, host='0.0.0.0', port=5000)
        except Exception as e:
            print(f"Error starting WebUI: {e}")

    def stop(self):
        """Stop the WebUI server."""
        pass

    def status(self):
        """Get the status of the WebUI."""
        return "WebUI is running"
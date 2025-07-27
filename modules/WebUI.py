import meshtastic.serial_interface
from flask import Flask, render_template, request, flash, redirect, url_for

class WebUI:
    def __init__(self, 
                 interface: meshtastic.serial_interface.SerialInterface = None, 
                 nodesdb=None, 
                 Activity=None,
                 logfiles = None, 
                 config=None):
        """Initialize the WebUI."""
        self.app = None
        self.interface = interface
        self.nodesdb = nodesdb
        self.nodeactivity = Activity
        self.logfiles = logfiles
        self.config = config if config else {}
        self.initFlask()

    def initFlask(self):
        """Initialize the Flask application and register routes."""
        self.app = Flask(__name__)
        self.app.config['SECRET_KEY'] = '123456789'
        self.app.config['TEMPLATES_AUTO_RELOAD'] = True
        self.app.add_url_rule("/", "index", self.index)
        self.app.add_url_rule("/setup", "setup", self.setup, methods=['GET', 'POST'])
        self.app.add_url_rule("/nodes", "nodes", self.nodes)
        self.app.add_url_rule("/activity", "activity", self.activity)
        self.app.add_url_rule("/logfile", "logfile", self.logfile)
        
    def index(self):
        """Route for the main index page."""
        info = self.interface.getMyNodeInfo()
        return render_template('index.html', info=info)

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
import meshtastic.serial_interface
from flask import Flask, render_template, request, flash, redirect, url_for

class WebUI:
    def __init__(self, interface: meshtastic.serial_interface.SerialInterface = None, nodesdb=None):
        """Initialize the WebUI."""
        self.app = None
        self.interface = interface
        self.nodesdb = nodesdb
        self.site_settings = {
            'broadcast_message': 'This is the default broadcast message.'
        }
        self.initFlask()

    def initFlask(self):
        """Initialize the Flask application and register routes."""
        self.app = Flask(__name__)
        self.app.config['SECRET_KEY'] = 'a-secure-random-string-is-best'
        self.app.add_url_rule("/", "index", self.index)
        self.app.add_url_rule("/setup", "setup", self.setup, methods=['GET', 'POST'])

    def index(self):
        """Route for the main index page."""
        info = self.interface.getMyNodeInfo()
        return render_template('index.html', info=info)

    def setup(self):
        """Route for the setup page (handles GET and POST)."""
        # This part need to updated to really update the information 
        if request.method == 'POST':
            new_message = request.form.get('broadcast_message')
            self.site_settings['broadcast_message'] = new_message
            flash('Broadcast message saved successfully! ✅', 'success')
            return redirect(url_for('setup'))
        return render_template('setup.html', current_message=self.site_settings['broadcast_message'])

    def start(self):
        """Start the WebUI server thread."""
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
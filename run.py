import os
from app import create_app

app = create_app(os.environ.get('FLASK_CONFIG', 'development'))

if __name__ == '__main__':
    # Default Flask port is 5000
    # Use app.run(host='0.0.0.0') for external access if needed
    app.run(debug=app.config.get('DEBUG', True))

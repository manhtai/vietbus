import os
from app import create_app, mongo
from app.data.data_to_mongo import bus_stops_to_mongo, bus_routes_to_mongo
from flask.ext.script import Manager, Shell

app = create_app(os.getenv('CONFIG_ENV') or 'default')
manager = Manager(app)

def make_shell_context():
    return dict(app=app, mongo=mongo)
manager.add_command("shell", Shell(make_context=make_shell_context))

@manager.command
def init_db():
    """Run deployment tasks."""
    bus_stops_to_mongo()
    bus_routes_to_mongo()

if __name__ == '__main__':
    manager.run()

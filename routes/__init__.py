from routes.core import core_bp
from routes.harness import harness_bp
from routes.mesh import mesh_bp
from routes.transceiver import transceiver_bp
from routes.journalism import journalism_bp
from routes.financial import financial_bp


def register_blueprints(app):
    app.register_blueprint(core_bp)
    app.register_blueprint(harness_bp)
    app.register_blueprint(mesh_bp)
    app.register_blueprint(transceiver_bp)
    app.register_blueprint(journalism_bp)
    app.register_blueprint(financial_bp)

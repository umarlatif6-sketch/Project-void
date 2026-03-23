from routes.auth import auth_bp
from routes.core import core_bp
from routes.harness import harness_bp
from routes.mesh import mesh_bp
from routes.transceiver import transceiver_bp
from routes.journalism import journalism_bp
from routes.financial import financial_bp
from routes.messenger import messenger_bp
from routes.payments import payments_bp
from routes.vigilance import vigilance_bp
from routes.fairy import fairy_bp
from routes.node import node_bp
from routes.marketplace import marketplace_bp
from routes.admin import admin_bp
from routes.chronicle import chronicle_bp


def register_blueprints(app):
    app.register_blueprint(auth_bp)
    app.register_blueprint(core_bp)
    app.register_blueprint(harness_bp)
    app.register_blueprint(mesh_bp)
    app.register_blueprint(transceiver_bp)
    app.register_blueprint(journalism_bp)
    app.register_blueprint(financial_bp)
    app.register_blueprint(messenger_bp)
    app.register_blueprint(payments_bp)
    app.register_blueprint(vigilance_bp)
    app.register_blueprint(fairy_bp)
    app.register_blueprint(node_bp)
    app.register_blueprint(marketplace_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(chronicle_bp)

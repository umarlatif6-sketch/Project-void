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
from routes.sovereign_node import sovereign_node_bp
from routes.beehive_demo import beehive_demo_bp
from routes.apply_interussia import apply_interussia_bp
from routes.mycovoid import mycovoid_bp
from routes.qisync import qisync_bp
from routes.game import game_bp
from routes.gridul import gridul_bp
from routes.peace import peace_bp
from routes.genesis import genesis_bp
from routes.prior_art import prior_art_bp
from routes.archive import archive_bp
from routes.brand import brand_bp
from routes.crystallization import crystallization_bp
from routes.plane import plane_bp
from routes.void_master_document import void_master_document_bp
from routes.inner_voice import inner_voice_bp
from routes.agent_vision import agent_vision_bp
from routes.mesa import mesa_bp
from routes.founders_room import founders_room_bp
from routes.hex_flower import hex_flower_bp
from routes.transmissions import transmissions_bp
from routes.origin_map import origin_map_bp
from routes.voidecho import voidecho_bp
from routes.void_language import void_language_bp


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
    app.register_blueprint(sovereign_node_bp)
    app.register_blueprint(beehive_demo_bp)
    app.register_blueprint(apply_interussia_bp)
    app.register_blueprint(mycovoid_bp)
    app.register_blueprint(qisync_bp)
    app.register_blueprint(game_bp)
    app.register_blueprint(gridul_bp)
    app.register_blueprint(peace_bp)
    app.register_blueprint(genesis_bp)
    app.register_blueprint(prior_art_bp)
    app.register_blueprint(archive_bp)
    app.register_blueprint(brand_bp)
    app.register_blueprint(crystallization_bp)
    app.register_blueprint(plane_bp)
    app.register_blueprint(void_master_document_bp)
    app.register_blueprint(inner_voice_bp)
    app.register_blueprint(agent_vision_bp)
    app.register_blueprint(mesa_bp)
    app.register_blueprint(founders_room_bp)
    app.register_blueprint(hex_flower_bp)
    app.register_blueprint(transmissions_bp)
    app.register_blueprint(origin_map_bp)
    app.register_blueprint(voidecho_bp)
    app.register_blueprint(void_language_bp)

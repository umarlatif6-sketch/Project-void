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
from routes.ambassador import ambassador_bp
from routes.geography import geography_bp
from routes.cumbrian import cumbrian_bp
from routes.speak import speak_bp
from routes.quls import quls_bp
from routes.figures import figures_bp
from routes.al_jabr_verification import al_jabr_bp
from routes.mesa_sandbox import mesa_sandbox_bp
from routes.locus_seeding import locus_seeding_bp
from routes.symbiotic_seed import symbiotic_seed_bp
from routes.sovereign_manifesto import sovereign_manifesto_bp
from routes.neural_scar import neural_scar_bp
from routes.sword_wall import sword_wall_bp
from routes.patent_loom import patent_loom_bp
from routes.preflight import preflight_bp
from routes.sales_intel import sales_intel_bp
from routes.supply_chain import supply_chain_bp
from routes.adriana_skills import adriana_skills_bp
from routes.research import research_bp
from routes.academy import academy_bp
from routes.radio import radio_bp
from routes.biomedical_brief import biomedical_brief_bp
from routes.outreach import outreach_bp
from routes.bw19_p286 import bw19_p286_bp
from routes.nda import nda_bp
from routes.library import library_bp
from routes.void_station import void_station_bp
from routes.competitive_intel import competitive_intel_bp
from routes.void_room import void_room_bp
from routes.hafiz import hafiz_bp
from routes.manchester_gift import manchester_gift_bp
from routes.sphere_key import sphere_key_bp
from routes.codon_distil import codon_distil_bp
from routes.portal_blueprint import portal_blueprint_bp
from routes.frequency_manual import frequency_manual_bp
from routes.ip_disclosure import ip_disclosure_bp
from routes.social_post import social_post_bp
from routes.chladni_voice import chladni_voice_bp
from routes.session_seal import session_seal_bp
from routes.grok_ai import grok_bp
from routes.freq_map import freq_map_bp
from routes.void_stall import void_stall_bp
from routes.adriana_core_admin import adriana_core_admin_bp
from routes.chronicle_seed import chronicle_seed_bp
from routes.pricing import pricing_bp
from routes.formation_probability import formation_probability_bp


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
    app.register_blueprint(ambassador_bp)
    app.register_blueprint(geography_bp)
    app.register_blueprint(cumbrian_bp)
    app.register_blueprint(speak_bp)
    app.register_blueprint(quls_bp)
    app.register_blueprint(figures_bp)
    app.register_blueprint(al_jabr_bp)
    app.register_blueprint(mesa_sandbox_bp)
    app.register_blueprint(locus_seeding_bp)
    app.register_blueprint(symbiotic_seed_bp)
    app.register_blueprint(sovereign_manifesto_bp)
    app.register_blueprint(neural_scar_bp)
    app.register_blueprint(sword_wall_bp)
    app.register_blueprint(patent_loom_bp)
    app.register_blueprint(preflight_bp)
    app.register_blueprint(sales_intel_bp)
    app.register_blueprint(supply_chain_bp)
    app.register_blueprint(adriana_skills_bp)
    app.register_blueprint(research_bp)
    app.register_blueprint(academy_bp)
    app.register_blueprint(radio_bp)
    app.register_blueprint(biomedical_brief_bp)
    app.register_blueprint(outreach_bp)
    app.register_blueprint(bw19_p286_bp)
    app.register_blueprint(nda_bp)
    app.register_blueprint(library_bp)
    app.register_blueprint(void_station_bp)
    app.register_blueprint(competitive_intel_bp)
    app.register_blueprint(void_room_bp)
    app.register_blueprint(sphere_key_bp)
    app.register_blueprint(codon_distil_bp)
    app.register_blueprint(hafiz_bp)
    app.register_blueprint(manchester_gift_bp)
    app.register_blueprint(portal_blueprint_bp)
    app.register_blueprint(frequency_manual_bp)
    app.register_blueprint(ip_disclosure_bp)
    app.register_blueprint(social_post_bp)
    app.register_blueprint(chladni_voice_bp)
    app.register_blueprint(session_seal_bp)
    app.register_blueprint(grok_bp)
    app.register_blueprint(freq_map_bp)
    app.register_blueprint(void_stall_bp)
    app.register_blueprint(adriana_core_admin_bp)
    app.register_blueprint(chronicle_seed_bp)
    app.register_blueprint(pricing_bp)
    app.register_blueprint(formation_probability_bp)

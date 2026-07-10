#!/usr/bin/env python3
"""
Ambassador Outreach Generation — PROJECT VOID
==============================================

Generates personalized outreach in three formats (email, X thread, WhatsApp)
for all 36 named ambassador prospects.

Voice: "Quiet alignment" — not asking for funding, simply noting alignment.
"""

import json
import csv
from datetime import datetime
from pathlib import Path

# ── AMBASSADOR DATA ────────────────────────────────────────────────────────

AMBASSADORS = [
    {
        "name": "Harlo Holmes",
        "org": "Freedom of the Press Foundation",
        "title": "Chief Information Security Officer & Director of Digital Security",
        "email": "harlo@freedom.press",
        "trigger": "SecureDrop dependency on centralised infrastructure is a known pain point",
        "alignment": "SecureDrop is brilliant but centralised — VoidEcho offers the same trust model without a server to subpoena.",
        "tier": "Press Freedom & Journalism"
    },
    {
        "name": "David Lublin",
        "org": "Freedom of the Press Foundation",
        "title": "Director of Engineering — SecureDrop",
        "email": "david@freedom.press",
        "trigger": "As the engineer behind SecureDrop he understands why document transfer needs to be invisible not just encrypted.",
        "alignment": "Document transfer that leaves no metadata signature.",
        "tier": "Press Freedom & Journalism"
    },
    {
        "name": "Micah Lee",
        "org": "The Intercept",
        "title": "Director of Information Security",
        "email": "micah.lee@theintercept.com",
        "trigger": "Built OnionShare and worked the Snowden transfer — he already knows why sound is a better carrier than metadata.",
        "alignment": "The carrier being music is not decorative — it is structural.",
        "tier": "Press Freedom & Journalism"
    },
    {
        "name": "Logan Williams",
        "org": "Bellingcat",
        "title": "Data Scientist & Technical Investigator",
        "email": "logan@bellingcat.com",
        "trigger": "Bellingcat operates in regimes that surveil file transfers — steganography in audio is operationally invisible.",
        "alignment": "Acoustic document transfer is invisible to metadata analysis.",
        "tier": "Press Freedom & Journalism"
    },
    {
        "name": "Justin Galvin",
        "org": "ProPublica",
        "title": "Chief Information Security Officer",
        "email": "justin.galvin@propublica.org",
        "trigger": "Newsroom security leadership who would recognise acoustic document transfer as a category shift.",
        "alignment": "A document inside music has no metadata to analyse.",
        "tier": "Press Freedom & Journalism"
    },
    {
        "name": "Aatishya Verma",
        "org": "Committee to Protect Journalists",
        "title": "Digital Security Technologist",
        "email": "aatishya.verma@cpj.org",
        "trigger": "CPJ documents journalist arrests frequently caused by seized device evidence.",
        "alignment": "Audio is invisible to a checkpoint search.",
        "tier": "Press Freedom & Journalism"
    },
    {
        "name": "Erik De Pasquelle",
        "org": "Reporters Without Borders",
        "title": "Head of Digital Security",
        "email": "erik.depasquelle@rsf.org",
        "trigger": "RSF operates in countries where a journalist's device is a death sentence.",
        "alignment": "Sound carries what a folder cannot.",
        "tier": "Press Freedom & Journalism"
    },
    {
        "name": "Clare Robinson",
        "org": "PEN America",
        "title": "Director of Digital Safety and Free Expression",
        "email": "clare.robinson@pen.org",
        "trigger": "Writers under surveillance need document transfer that cannot be found.",
        "alignment": "VoidEcho's carrier is music not metadata.",
        "tier": "Press Freedom & Journalism"
    },
    {
        "name": "Bernardo Jurema",
        "org": "Forbidden Stories",
        "title": "Senior Digital Security Advisor",
        "email": "bjurema@forbiddenstories.org",
        "trigger": "Forbidden Stories carries documents across borders for journalists who cannot.",
        "alignment": "A sound file is the only carrier a border agent cannot decode.",
        "tier": "Press Freedom & Journalism"
    },
    {
        "name": "Cindy Cohn",
        "org": "Electronic Frontier Foundation",
        "title": "Executive Director",
        "email": "cindy@eff.org",
        "trigger": "The EFF's founding argument is that surveillance infrastructure must be denied.",
        "alignment": "Acoustic steganography removes the infrastructure entirely.",
        "tier": "Press Freedom & Journalism"
    },
    {
        "name": "Eva Galperin",
        "org": "Electronic Frontier Foundation",
        "title": "Director of Cybersecurity",
        "email": "eva@eff.org",
        "trigger": "Eva tracks stalkerware and state spyware.",
        "alignment": "A document inside music evades every known detection pattern.",
        "tier": "Press Freedom & Journalism"
    },
    {
        "name": "Isabela Bagueros",
        "org": "Tor Project",
        "title": "Executive Director",
        "email": "isabela@torproject.org",
        "trigger": "Tor faces traffic analysis attacks that acoustic steganography sidesteps entirely.",
        "alignment": "VoidEcho makes the payload unrecognisable as a payload.",
        "tier": "Press Freedom & Journalism"
    },
    {
        "name": "Gus Hosein",
        "org": "Privacy International",
        "title": "Executive Director",
        "email": "gus@privacyinternational.org",
        "trigger": "PI actively investigates surveillance tools used against activists and journalists.",
        "alignment": "Metadata analysis defeats most secure comms — a document hidden in music has no metadata to analyse.",
        "tier": "Press Freedom & Journalism"
    },
    {
        "name": "Brett Solomon",
        "org": "Access Now",
        "title": "Co-Founder & Executive Director",
        "email": "brett@accessnow.org",
        "trigger": "Access Now's Digital Security Helpline serves journalists and activists under active attack.",
        "alignment": "Acoustic document transfer is the channel that does not exist in an attacker's playbook.",
        "tier": "Digital Rights & Emergency Response"
    },
    {
        "name": "Bernie Krause",
        "org": "Wild Sanctuary",
        "title": "Founder & Soundscape Ecologist",
        "email": "bernie@wildsanctuary.com",
        "trigger": "His life's work is information encoded in natural sound.",
        "alignment": "VoidEcho is the technical proof that sound has always been a transmission medium.",
        "tier": "Bioacoustics & Soundscape"
    },
    {
        "name": "Dr. Christopher Clark",
        "org": "Cornell Lab of Ornithology",
        "title": "Senior Scientist — Bioacoustics Research Program",
        "email": "crc10@cornell.edu",
        "trigger": "Clark has spent decades proving that whales transmit complex signals through ocean noise.",
        "alignment": "VoidEcho is the digital expression of that same principle.",
        "tier": "Bioacoustics & Marine Acoustics"
    },
    {
        "name": "Dr. Katy Payne",
        "org": "Cornell Lab of Ornithology",
        "title": "Bioacoustics Researcher",
        "email": "katy.payne@cornell.edu",
        "trigger": "Payne proved that non-human minds compose structured sound over time.",
        "alignment": "VoidEcho encodes structured data in exactly the same frequency space.",
        "tier": "Bioacoustics & Marine Acoustics"
    },
    {
        "name": "Dr. Peter Tyack",
        "org": "University of St Andrews — SMRU",
        "title": "Professor of Marine Mammal Biology",
        "email": "plt@st-andrews.ac.uk",
        "trigger": "Tyack's work on dolphin and whale communication shows infrasonic transmission of complex social signals.",
        "alignment": "VoidEcho operates in the same acoustic register.",
        "tier": "Marine Mammal Acoustics"
    },
    {
        "name": "Hildegard Westerkamp",
        "org": "Simon Fraser University",
        "title": "Composer & Acoustic Researcher",
        "email": "hildegard.westerkamp@gmail.com",
        "trigger": "She has spent a career arguing that we listen wrongly to our environment.",
        "alignment": "VoidEcho asks the same question and answers it with hidden transmission.",
        "tier": "Acoustic Ecology"
    },
    {
        "name": "WFAE Board",
        "org": "World Forum for Acoustic Ecology",
        "title": "Community of Acoustic Ecology Researchers",
        "email": "wfae@sfu.ca",
        "trigger": "The WFAE community already understands that sound carries meaning beyond the audible.",
        "alignment": "VoidEcho makes that literal.",
        "tier": "Acoustic Ecology"
    },
    {
        "name": "Dr. Paul Gardner-Stephen",
        "org": "Serval Project / Flinders University",
        "title": "Founder — Serval Project / Associate Professor",
        "email": "paul.gardner-stephen@flinders.edu.au",
        "trigger": "Serval was built for disaster zones where infrastructure fails.",
        "alignment": "VoidEcho carries documents through a channel that does not require a network at all.",
        "tier": "Mesh Networking"
    },
    {
        "name": "Nico Pace",
        "org": "AlterMundi",
        "title": "Director & Network Architect",
        "email": "nico@altermundi.net",
        "trigger": "AlterMundi exists because centralised internet is a political weapon.",
        "alignment": "Acoustic steganography is the channel that exists even when the network does not.",
        "tier": "Community Networks"
    },
    {
        "name": "Arantxa Serantes",
        "org": "NetHood",
        "title": "Co-Founder & Director",
        "email": "info@nethood.org",
        "trigger": "NetHood's whole argument is that network infrastructure must be community-owned.",
        "alignment": "VoidEcho extends that to the transmission layer.",
        "tier": "Community Networks"
    },
    {
        "name": "Meshtastic Core Team",
        "org": "Meshtastic Project",
        "title": "Open Source Mesh Network Community",
        "email": "hello@meshtastic.org",
        "trigger": "Meshtastic has grown to 500k+ nodes globally.",
        "alignment": "VoidEcho gives them a carrier that exists inside any audio file.",
        "tier": "LoRa Mesh Networking"
    },
    {
        "name": "Daniel Kahn Gillmor",
        "org": "ACLU — Speech Privacy Technology Project",
        "title": "Staff Technologist — ACLU",
        "email": "dkg@aclu.org",
        "trigger": "Gillmor designs privacy-preserving cryptographic protocols.",
        "alignment": "He'll recognise acoustic steganography as the channel that sidesteps every surveillance architecture.",
        "tier": "Civil Liberties"
    },
    {
        "name": "Jim Killock",
        "org": "Open Rights Group",
        "title": "Executive Director",
        "email": "jim.killock@openrightsgroup.org",
        "trigger": "ORG fights UK surveillance legislation.",
        "alignment": "VoidEcho is built in the UK as a direct technical counter to that legislation.",
        "tier": "Digital Rights — UK"
    },
    {
        "name": "Silkie Carlo",
        "org": "Big Brother Watch",
        "title": "Director",
        "email": "silkie.carlo@bigbrotherwatch.org.uk",
        "trigger": "Carlo campaigns against surveillance by exposing what it looks like in practice.",
        "alignment": "VoidEcho shows what resistance looks like in practice.",
        "tier": "UK Surveillance"
    },
    {
        "name": "Tony Bunyan",
        "org": "Statewatch",
        "title": "Founder & Researcher",
        "email": "statewatch@statewatch.org",
        "trigger": "Statewatch has documented surveillance infrastructure for thirty years.",
        "alignment": "VoidEcho is the infrastructure-less counter to everything they have documented.",
        "tier": "EU Surveillance"
    },
    {
        "name": "Ron Deibert",
        "org": "Citizen Lab — University of Toronto",
        "title": "Director",
        "email": "rdeibert@citizenlab.ca",
        "trigger": "Citizen Lab has traced spyware to phone metadata.",
        "alignment": "Acoustic steganography is the transfer layer that leaves no metadata to trace.",
        "tier": "Spyware Research"
    },
    {
        "name": "Stephanie Hankey",
        "org": "Tactical Tech",
        "title": "Co-Founder",
        "email": "info@tacticaltech.org",
        "trigger": "Tactical Tech teaches activists to shrink their digital footprint.",
        "alignment": "A document inside music has no footprint at all.",
        "tier": "Digital Security"
    },
    {
        "name": "Marwa Fatafta",
        "org": "Access Now — Digital Security Helpline",
        "title": "MENA Policy Manager",
        "email": "marwa@accessnow.org",
        "trigger": "Fatafta works with journalists in MENA where digital surveillance is existential.",
        "alignment": "Acoustic transfer is the only channel a regime's toolchain cannot intercept.",
        "tier": "Emergency Digital Security"
    },
    {
        "name": "Sam Gregory",
        "org": "WITNESS",
        "title": "Program Director",
        "email": "sam@witness.org",
        "trigger": "WITNESS exists because evidence transmission is life or death.",
        "alignment": "VoidEcho gives defenders a channel that looks like nothing.",
        "tier": "Human Rights"
    },
    {
        "name": "Renata Avila",
        "org": "Global Voices",
        "title": "CEO — Open Knowledge Foundation / GV Board",
        "email": "renata@okfn.org",
        "trigger": "Avila sits at the intersection of open knowledge and digital sovereignty.",
        "alignment": "VoidEcho is both in a single product.",
        "tier": "Citizen Media"
    },
    {
        "name": "Mary Lawlor",
        "org": "Frontline Defenders",
        "title": "Former Executive Director / UN Special Rapporteur",
        "email": "info@frontlinedefenders.org",
        "trigger": "As the UN Special Rapporteur for Human Rights Defenders she has the platform to make VoidEcho visible.",
        "alignment": "To everyone who needs it.",
        "tier": "Human Rights Defenders"
    },
    {
        "name": "Agnes Callamard",
        "org": "Article 19",
        "title": "Former Executive Director / UN Special Rapporteur",
        "email": "info@article19.org",
        "trigger": "Callamard has documented how surveillance kills journalists.",
        "alignment": "She'll understand immediately why the carrier being music is not decorative but structural.",
        "tier": "Freedom of Expression"
    },
]

# ── EMAIL TEMPLATE ─────────────────────────────────────────────────────────

EMAIL_TEMPLATE = """Subject: VoidEcho — Acoustic Steganography for {org}

Hi {name},

{org} has spent years solving a specific problem: how to transfer sensitive information safely.

PROJECT VOID approaches the same problem from a different angle: what if the carrier itself was invisible?

{trigger}

VoidEcho is a steganographic document transfer system that hides payloads in ambient audio at 432 Hz. The carrier is music. The metadata is zero. The infrastructure is sovereign.

{alignment}

We're reaching out because your work suggests you'd recognise immediately why this matters.

No ask. Just alignment.

— PROJECT VOID
https://github.com/umarlatif6-sketch/Project-void
"""

# ── X THREAD TEMPLATE ──────────────────────────────────────────────────────

X_THREAD_TEMPLATE = """1/ {org} has spent years solving a specific problem: how to transfer sensitive information safely.

PROJECT VOID approaches the same problem from a different angle: what if the carrier itself was invisible?

2/ {trigger}

3/ VoidEcho is a steganographic document transfer system that hides payloads in ambient audio at 432 Hz.

The carrier is music.
The metadata is zero.
The infrastructure is sovereign.

4/ {alignment}

5/ We're reaching out because your work suggests you'd recognise immediately why this matters.

No ask. Just alignment.

— PROJECT VOID
github.com/umarlatif6-sketch/Project-void
"""

# ── WHATSAPP TEMPLATE ──────────────────────────────────────────────────────

WHATSAPP_TEMPLATE = """{name},

{org} has spent years solving a specific problem: how to transfer sensitive information safely.

PROJECT VOID approaches the same problem differently: what if the carrier itself was invisible?

{trigger}

VoidEcho hides payloads in ambient audio at 432 Hz. Carrier: music. Metadata: zero. Infrastructure: sovereign.

{alignment}

Your work suggests you'd recognise immediately why this matters.

No ask. Just alignment.

— PROJECT VOID
github.com/umarlatif6-sketch/Project-void
"""

# ── GENERATION ─────────────────────────────────────────────────────────────

def generate_outreach():
    """Generate outreach in all three formats for all ambassadors."""
    outreach_data = []
    
    for ambassador in AMBASSADORS:
        email = EMAIL_TEMPLATE.format(
            org=ambassador["org"],
            name=ambassador["name"],
            trigger=ambassador["trigger"],
            alignment=ambassador["alignment"]
        )
        
        x_thread = X_THREAD_TEMPLATE.format(
            org=ambassador["org"],
            trigger=ambassador["trigger"],
            alignment=ambassador["alignment"]
        )
        
        whatsapp = WHATSAPP_TEMPLATE.format(
            name=ambassador["name"],
            org=ambassador["org"],
            trigger=ambassador["trigger"],
            alignment=ambassador["alignment"]
        )
        
        outreach_data.append({
            "name": ambassador["name"],
            "org": ambassador["org"],
            "title": ambassador["title"],
            "email": ambassador["email"],
            "tier": ambassador["tier"],
            "formats": {
                "email": email,
                "x_thread": x_thread,
                "whatsapp": whatsapp
            },
            "generated_at": datetime.now().isoformat(),
            "status": "pending"
        })
    
    return outreach_data

def save_outreach(outreach_data, output_file):
    """Save outreach data to JSON file."""
    with open(output_file, 'w') as f:
        json.dump(outreach_data, f, indent=2)
    print(f"✓ Outreach generated: {output_file}")
    print(f"  Total ambassadors: {len(outreach_data)}")
    print(f"  Formats: email, x_thread, whatsapp")

if __name__ == "__main__":
    output_file = Path(__file__).parent.parent / "data" / "ambassador_outreach_20260710.json"
    outreach_data = generate_outreach()
    save_outreach(outreach_data, output_file)

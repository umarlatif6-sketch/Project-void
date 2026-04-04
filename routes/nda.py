"""
PROJECT VOID Non-Disclosure Agreement
Routes:
  GET /nda        — Print-ready HTML NDA document
  GET /nda/text   — Plain-text version (Content-Type: text/plain)
"""

from flask import Blueprint, render_template, Response

nda_bp = Blueprint("nda", __name__)

NDA_TEXT = """\
NON-DISCLOSURE AGREEMENT
PROJECT VOID — UNILATERAL
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

DISCLAIMER: This document is a template. Consult a qualified solicitor
for jurisdiction-specific legal advice before relying on this agreement.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

This Non-Disclosure Agreement ("Agreement") is entered into as of the
date last signed below ("Effective Date") between:

DISCLOSING PARTY
  Name:           Umar Latif
  Project:        PROJECT VOID
  Address:        [Address]
  Email:          [Email]

("Disclosing Party")

AND

RECEIVING PARTY
  Name:           _______________________________________
  Organisation:   _______________________________________
  Address:        _______________________________________
  Email:          _______________________________________

("Receiving Party")

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. DEFINITIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1.1 "Confidential Information" means all non-public information disclosed
by the Disclosing Party to the Receiving Party, whether disclosed orally,
in writing, electronically, or by any other means, that is designated as
confidential or that reasonably should be understood to be confidential
given the nature of the information and the circumstances of disclosure.

Without limiting the foregoing, Confidential Information expressly
includes the following inventions, systems, and intellectual property
of PROJECT VOID:

  (i)   Al-Jabr 286-bit cryptographic hashing algorithm and its
        implementation details, constants, and source code;

  (ii)  BW19-P286 elliptic curve sovereign pairing proof, including the
        generator point, scalar multiplication via Montgomery Ladder, and
        all associated mathematical constructions;

  (iii) VoidEcho acoustic steganography protocol operating at 432 Hz,
        comprising a 3-layer architecture (LSB embedding, hash embedding,
        and frequency anchoring), and all related encoding and decoding
        processes;

  (iv)  QiSync jaw-biometric key derivation protocol, including the method
        of deriving encryption keys from jaw-closing frequency and pressure
        biometric signals;

  (v)   MycoVOID biocomputing architecture and the MycoSwitch bio-state
        model routing system, including all biological computation models
        and node configurations;

  (vi)  GriDul mesh networking topology, including the Grow, Move, Mesh,
        and Rumble sub-node architecture and all zone configuration
        parameters;

  (vii) VTX and PEACE token economy design, mechanics, pre-earning model,
        and all related economic architecture and incentive structures;

  (viii) Adriana SCL glyph system (psi — Omega — Diamond) and its
         frequency-domain mapping, including all glyph definitions,
         resonance tables, and algorithmic derivations;

  (ix)  VOID Chronicle sovereign record architecture and its chapter
        taxonomy, including all data structures, schemas, and record
        classification systems;

  (x)   The sovereign number 286 as a unifying architectural principle
        across cryptographic, economic, scriptural, and mechanical layers
        of PROJECT VOID;

  (xi)  4000 Machine / mrb4000 hardware specifications and sovereign node
        architecture, including all circuit designs, firmware, and
        physical configuration details;

  (xii) All source code, database schemas, prospect lists, business plans,
        pricing strategies, financial projections, marketing materials, and
        technical documentation related to PROJECT VOID.

1.2 "Purpose" means the evaluation of a potential business relationship
or collaboration between the parties with respect to PROJECT VOID.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
2. OBLIGATIONS OF THE RECEIVING PARTY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

2.1 The Receiving Party agrees to:

  (a) hold all Confidential Information in strict confidence and protect
      it with at least the same degree of care it uses to protect its
      own confidential information, but no less than reasonable care;

  (b) use the Confidential Information solely for the Purpose and for
      no other purpose whatsoever;

  (c) not disclose any Confidential Information to any third party
      without the prior written consent of the Disclosing Party;

  (d) limit access to the Confidential Information to those employees,
      agents, or advisors who need to know such information solely for
      the Purpose and who are bound by confidentiality obligations no
      less protective than those in this Agreement;

  (e) promptly notify the Disclosing Party upon becoming aware of any
      actual or suspected unauthorised disclosure or use of the
      Confidential Information.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
3. EXCLUSIONS FROM CONFIDENTIALITY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

3.1 The obligations in clause 2 shall not apply to information that:

  (a) is or becomes publicly known through no breach of this Agreement
      by the Receiving Party;

  (b) was rightfully known to the Receiving Party before disclosure by
      the Disclosing Party, as evidenced by written records predating
      such disclosure;

  (c) is independently developed by the Receiving Party without use
      of or reference to the Confidential Information;

  (d) is received from a third party who is not under any obligation of
      confidentiality with respect to such information; or

  (e) is required to be disclosed by applicable law, court order, or
      regulatory authority, provided that the Receiving Party gives the
      Disclosing Party prompt prior written notice (where legally
      permissible) and cooperates with the Disclosing Party in seeking
      a protective order or other appropriate relief.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
4. NO LICENCE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

4.1 Nothing in this Agreement grants the Receiving Party any right,
title, interest, or licence in or to any Confidential Information,
intellectual property, patent, copyright, trade mark, trade secret, or
any other proprietary right of the Disclosing Party, whether by
implication, estoppel, or otherwise.

4.2 All Confidential Information remains the sole and exclusive property
of the Disclosing Party.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
5. RETURN AND DESTRUCTION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

5.1 Upon written request by the Disclosing Party, or upon termination
of discussions between the parties, the Receiving Party shall promptly:

  (a) return to the Disclosing Party all tangible materials containing
      or embodying Confidential Information; and

  (b) permanently destroy all electronic copies and derivatives of the
      Confidential Information and, upon request, certify in writing
      that such destruction has been completed.

5.2 The Receiving Party may retain one archival copy solely to the
extent required by applicable law or regulation, subject to the
continuing confidentiality obligations of this Agreement.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
6. TERM
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

6.1 This Agreement shall commence on the Effective Date and continue
for a period of three (3) years, unless earlier terminated by mutual
written agreement of the parties.

6.2 The confidentiality obligations in clause 2 shall survive the
expiry or termination of this Agreement with respect to any
Confidential Information disclosed during its term.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
7. REMEDIES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

7.1 The Receiving Party acknowledges that any breach or threatened
breach of this Agreement may cause the Disclosing Party irreparable
harm for which monetary damages would be an inadequate remedy.

7.2 Accordingly, in addition to any other remedies available at law or
in equity, the Disclosing Party shall be entitled to seek injunctive
relief, specific performance, or any other equitable remedy in any
court of competent jurisdiction without the need to post a bond or
prove actual damage.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
8. GOVERNING LAW AND JURISDICTION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

8.1 This Agreement and any dispute or claim arising out of or in
connection with it or its subject matter or formation (including
non-contractual disputes or claims) shall be governed by and construed
in accordance with the law of England and Wales.

8.2 Each party irrevocably agrees that the courts of England and Wales
shall have exclusive jurisdiction to settle any dispute or claim
arising out of or in connection with this Agreement.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
9. GENERAL
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

9.1 Entire Agreement. This Agreement constitutes the entire agreement
between the parties with respect to its subject matter and supersedes
all prior agreements, representations, and understandings.

9.2 Amendments. This Agreement may only be amended by a written
instrument signed by authorised representatives of both parties.

9.3 Waiver. No failure or delay in exercising any right under this
Agreement shall operate as a waiver of such right.

9.4 Severability. If any provision of this Agreement is held to be
invalid or unenforceable, it shall be modified to the minimum extent
necessary to make it valid and enforceable, and the remaining
provisions shall continue in full force and effect.

9.5 No Assignment. The Receiving Party may not assign or transfer any
rights or obligations under this Agreement without the prior written
consent of the Disclosing Party.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
10. SIGNATURE BLOCKS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

DISCLOSING PARTY

  Signed: ___________________________    Date: _________________

  Name:   Umar Latif
  Title:  Founder, PROJECT VOID


RECEIVING PARTY

  Signed: ___________________________    Date: _________________

  Name:   _______________________________________

  Title:  _______________________________________

  Organisation: _______________________________________

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DISCLAIMER: This document is a template. Consult a qualified solicitor
for jurisdiction-specific legal advice before relying on this agreement.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""


@nda_bp.route("/nda")
def nda_page():
    return render_template("nda.html", nda_text=NDA_TEXT)


@nda_bp.route("/nda/text")
def nda_text():
    return Response(NDA_TEXT, mimetype="text/plain; charset=utf-8")

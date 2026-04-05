"""
Library of the VOID — Flask Routes
289 collections · 289 books each · 19 pages each · 1,586,899 total pages
"""

from flask import Blueprint, render_template, abort
from void_engine.al_jabr_286 import fatiha_286_hexdigest_from_str, SOVEREIGN_BIT_DEPTH
from void_engine.library_data import (
    TOTAL_COLLECTIONS, BOOKS_PER_COLLECTION, PAGES_PER_BOOK,
    TOTAL_BOOKS, TOTAL_PAGES, COLLECTION_1_AUTHORS,
    get_live_database_snapshot, get_book_1_pages,
    get_book_4_pages,
    get_collection_meta, get_book_meta,
)
from void_engine.void_script import CANONICAL_GLYPHS, DOMAIN_COLORS, get_glyphs_by_role

library_bp = Blueprint("library", __name__)


@library_bp.route("/library")
def library_index():
    return render_template(
        "library.html",
        total_collections=TOTAL_COLLECTIONS,
        books_per_collection=BOOKS_PER_COLLECTION,
        pages_per_book=PAGES_PER_BOOK,
        total_books=TOTAL_BOOKS,
        total_pages=TOTAL_PAGES,
        sovereign_bits=SOVEREIGN_BIT_DEPTH,
        collection_1_authors=COLLECTION_1_AUTHORS,
    )


@library_bp.route("/library/collection/<int:coll_num>")
def library_collection(coll_num):
    if coll_num < 1 or coll_num > TOTAL_COLLECTIONS:
        abort(404)
    meta = get_collection_meta(coll_num)
    books = []
    for b in range(1, BOOKS_PER_COLLECTION + 1):
        books.append(get_book_meta(coll_num, b))
    return render_template(
        "library_collection.html",
        collection=meta,
        books=books,
        total_collections=TOTAL_COLLECTIONS,
        books_per_collection=BOOKS_PER_COLLECTION,
        pages_per_book=PAGES_PER_BOOK,
    )


@library_bp.route("/library/collection/<int:coll_num>/book/<int:book_num>")
def library_book(coll_num, book_num):
    if coll_num < 1 or coll_num > TOTAL_COLLECTIONS:
        abort(404)
    if book_num < 1 or book_num > BOOKS_PER_COLLECTION:
        abort(404)

    meta = get_book_meta(coll_num, book_num)
    collection = get_collection_meta(coll_num)

    pages = None
    if coll_num == 1 and book_num == 1:
        snap = get_live_database_snapshot()
        pages = get_book_1_pages(snap)
        book_hash = fatiha_286_hexdigest_from_str(
            f"VOID-C{coll_num:04d}-B{book_num:04d}-LIVE"
        )[:72].upper()
        if pages:
            pages[0]["content"] = book_hash

    elif coll_num == 1 and book_num == 4:
        pages = get_book_4_pages()

    return render_template(
        "library_book.html",
        book=meta,
        collection=collection,
        pages=pages,
        total_collections=TOTAL_COLLECTIONS,
        books_per_collection=BOOKS_PER_COLLECTION,
    )


@library_bp.route("/library/book/<int:book_num>")
def library_book_legacy(book_num):
    from flask import redirect, url_for
    return redirect(url_for("library.library_book", coll_num=1, book_num=book_num))


@library_bp.route("/script")
def void_script_reference():
    roles = [
        ("entity",    "Entities",    "Subjects — sensors, subsystems, and agents that carry state."),
        ("condition", "Conditions",  "Qualifiers — thresholds, checks, and modes that govern transitions."),
        ("action",    "Actions",     "Operations — commands that fire, loop, spark, or seal a state."),
    ]
    glyphs_by_role = {}
    for role, _, _ in roles:
        glyphs_with_color = []
        for char, meta in CANONICAL_GLYPHS.items():
            if meta["role"] == role:
                glyphs_with_color.append((char, {
                    **meta,
                    "color": DOMAIN_COLORS.get(meta["domain"], "#c9a84c"),
                }))
        glyphs_by_role[role] = glyphs_with_color
    return render_template(
        "void_script.html",
        roles=roles,
        glyphs_by_role=glyphs_by_role,
        total_glyphs=len(CANONICAL_GLYPHS),
    )

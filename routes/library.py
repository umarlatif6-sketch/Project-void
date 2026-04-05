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

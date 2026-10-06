"""Ticket book: the ticketing workbook for one event, as a desktop app engine.

Real event data stays in the user's encrypted .ticketbook file; this package and its tests use invented data only.
"""
from .model import BookError, new_book, normalize
from .ledger import compute
from .forecast import forecast, preview, candidate
from .store import BookFile, WrongPassword

__version__ = '2.0.0'

"""Pacote de modelos SQLAlchemy.

Importar todos os modelos aqui garante que o Alembic os detecte nas migrations.
"""

from __future__ import annotations

from app.models.appointment import Appointment
from app.models.conversation import Conversation
from app.models.lead import Lead

__all__ = ["Lead", "Conversation", "Appointment"]

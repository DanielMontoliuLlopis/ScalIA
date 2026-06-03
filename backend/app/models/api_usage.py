import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ApiUsage(Base):
    """Rastreo de uso de APIs (OpenAI, etc).

    Se registra cada llamada a LLM con tokens consumidos.
    Costes calculados localmente basado en precios públicos.
    """

    __tablename__ = "api_usage"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    plan_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("plans.id"), nullable=True, index=True
    )

    # OpenAI
    model: Mapped[str] = mapped_column(String(50), nullable=False, default="gpt-4o")
    agent_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)  # ej: CopyAgent

    prompt_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    completion_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Costes en USD (calculados localmente)
    cost_usd: Mapped[float] = mapped_column(Numeric(10, 6), nullable=False, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)

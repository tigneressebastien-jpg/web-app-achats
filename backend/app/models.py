from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class PlatformParamModel(Base):
    __tablename__ = "platform_params"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    code_erp: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    pf_rapide: Mapped[str | None] = mapped_column(String(128), nullable=True)
    pf_lente: Mapped[str | None] = mapped_column(String(128), nullable=True)
    actif: Mapped[bool] = mapped_column(Boolean, default=True)
    lent_avec_pourcentage: Mapped[bool] = mapped_column(Boolean, default=False)


class ImportBatchModel(Base):
    __tablename__ = "import_batches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    filename: Mapped[str] = mapped_column(String(255))
    source_type: Mapped[str] = mapped_column(String(32))
    imported_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    rows: Mapped[list["ErpRowModel"]] = relationship(back_populates="batch")


class ErpRowModel(Base):
    __tablename__ = "erp_rows"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    batch_id: Mapped[int] = mapped_column(ForeignKey("import_batches.id"))
    code_article: Mapped[str] = mapped_column(String(64), index=True)
    libelle_article: Mapped[str] = mapped_column(String(255))
    code_plateforme_erp: Mapped[str] = mapped_column(String(32), index=True)
    prevision: Mapped[float] = mapped_column(Float, default=0)
    solde_previsionnel_j1: Mapped[float] = mapped_column(Float, default=0)

    batch: Mapped[ImportBatchModel] = relationship(back_populates="rows")


class ConsigneModel(Base):
    __tablename__ = "consignes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    code_article: Mapped[str] = mapped_column(String(64), index=True)
    plateforme: Mapped[str] = mapped_column(String(128), index=True)
    texte_consigne: Mapped[str] = mapped_column(String(255))
    valeur_consigne: Mapped[float] = mapped_column(Float, default=0)
    acheteur: Mapped[str] = mapped_column(String(64), default="Seb", index=True)


class CalculationRunModel(Base):
    __tablename__ = "calculation_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    buyer: Mapped[str] = mapped_column(String(64), default="Seb", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    status: Mapped[str] = mapped_column(String(32), default="created")

    results: Mapped[list["CalculationResultModel"]] = relationship(back_populates="run")
    logs: Mapped[list["CalculationLogModel"]] = relationship(back_populates="run")


class CalculationResultModel(Base):
    __tablename__ = "calculation_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("calculation_runs.id"))
    code_article: Mapped[str] = mapped_column(String(64), index=True)
    libelle_article: Mapped[str] = mapped_column(String(255))
    code_plateforme_erp: Mapped[str] = mapped_column(String(32), index=True)
    pf_rapide: Mapped[str | None] = mapped_column(String(128), nullable=True)
    pf_lente: Mapped[str | None] = mapped_column(String(128), nullable=True)
    besoin_rapide: Mapped[float] = mapped_column(Float, default=0)
    besoin_lent: Mapped[float] = mapped_column(Float, default=0)
    besoin_total: Mapped[float] = mapped_column(Float, default=0)
    consigne_appliquee: Mapped[str | None] = mapped_column(String(64), nullable=True)

    run: Mapped[CalculationRunModel] = relationship(back_populates="results")


class CalculationLogModel(Base):
    __tablename__ = "calculation_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("calculation_runs.id"))
    level: Mapped[str] = mapped_column(String(16), default="INFO")
    message: Mapped[str] = mapped_column(Text)
    context_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    run: Mapped[CalculationRunModel] = relationship(back_populates="logs")

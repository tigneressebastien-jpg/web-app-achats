from __future__ import annotations

from app.models import ErpRowModel, ImportBatchModel
from app.services.besoin_service import ErpRow
from app.services.import_service import ErpImportPreview
from sqlalchemy.orm import Session


def save_erp_import_preview(
    db: Session,
    *,
    filename: str,
    preview: ErpImportPreview,
) -> ImportBatchModel:
    batch = ImportBatchModel(filename=filename, source_type=preview.source_type)
    db.add(batch)
    db.flush()

    for row in preview.rows:
        db.add(
            ErpRowModel(
                batch_id=batch.id,
                code_article=row.code_article,
                libelle_article=row.libelle_article,
                code_plateforme_erp=row.code_plateforme_erp,
                prevision=row.prevision,
                solde_previsionnel_j1=row.solde_previsionnel_j1,
            )
        )

    db.commit()
    db.refresh(batch)
    return batch


def get_import_batch(db: Session, batch_id: int) -> ImportBatchModel | None:
    return (
        db.query(ImportBatchModel)
        .filter(ImportBatchModel.id == batch_id)
        .one_or_none()
    )


def list_import_batches(db: Session) -> list[ImportBatchModel]:
    return (
        db.query(ImportBatchModel)
        .order_by(ImportBatchModel.imported_at.desc(), ImportBatchModel.id.desc())
        .all()
    )


def erp_row_model_to_domain(row: ErpRowModel) -> ErpRow:
    return ErpRow(
        code_article=row.code_article,
        libelle_article=row.libelle_article,
        code_plateforme_erp=row.code_plateforme_erp,
        prevision=row.prevision,
        solde_previsionnel_j1=row.solde_previsionnel_j1,
    )

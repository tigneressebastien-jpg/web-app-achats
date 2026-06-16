from __future__ import annotations

from sqlalchemy.orm import Session

from app.models import ConsigneModel


def upsert_consigne(
    db: Session,
    *,
    code_article: str,
    texte_consigne: str,
    plateforme_erp: str | None = None,
    plateforme: str | None = None,
    valeur_consigne: float = 0,
    acheteur: str = "Seb",
) -> ConsigneModel:
    code_article_normalise = _require_text(code_article, "code_article")
    plateforme_erp_normalisee = _require_plateforme_erp(plateforme_erp or plateforme)
    texte_normalise = _require_text(texte_consigne, "texte_consigne")
    acheteur_normalise = _require_text(acheteur, "acheteur")

    existing = get_consigne_for_erp_row(
        db,
        acheteur=acheteur_normalise,
        code_article=code_article_normalise,
        plateforme_erp=plateforme_erp_normalisee,
    )

    if existing is None:
        existing = ConsigneModel(
            acheteur=acheteur_normalise,
            code_article=code_article_normalise,
            plateforme=plateforme_erp_normalisee,
            texte_consigne=texte_normalise,
            valeur_consigne=float(valeur_consigne),
        )
        db.add(existing)
    else:
        existing.texte_consigne = texte_normalise
        existing.valeur_consigne = float(valeur_consigne)

    db.commit()
    db.refresh(existing)
    return existing


def get_consigne_for_erp_row(
    db: Session,
    *,
    acheteur: str,
    code_article: str,
    plateforme_erp: str,
) -> ConsigneModel | None:
    acheteur_normalise = _require_text(acheteur, "acheteur")
    code_article_normalise = _require_text(code_article, "code_article")
    plateforme_erp_normalisee = _require_plateforme_erp(plateforme_erp)

    return (
        db.query(ConsigneModel)
        .filter(ConsigneModel.acheteur == acheteur_normalise)
        .filter(ConsigneModel.code_article == code_article_normalise)
        .filter(ConsigneModel.plateforme == plateforme_erp_normalisee)
        .one_or_none()
    )


def list_consignes(
    db: Session,
    *,
    acheteur: str | None = None,
    code_article: str | None = None,
    plateforme_erp: str | None = None,
    plateforme: str | None = None,
) -> list[ConsigneModel]:
    query = db.query(ConsigneModel)

    if acheteur:
        query = query.filter(ConsigneModel.acheteur == acheteur.strip())
    if code_article:
        query = query.filter(ConsigneModel.code_article == code_article.strip())
    plateforme_filter = plateforme_erp or plateforme
    if plateforme_filter:
        query = query.filter(ConsigneModel.plateforme == _require_plateforme_erp(plateforme_filter))

    return (
        query.order_by(
            ConsigneModel.acheteur.asc(),
            ConsigneModel.code_article.asc(),
            ConsigneModel.plateforme.asc(),
            ConsigneModel.id.asc(),
        )
        .all()
    )


def _require_text(value: str | None, field_name: str) -> str:
    text = (value or "").strip()
    if not text:
        raise ValueError(f"{field_name} obligatoire")
    return text


def _require_plateforme_erp(value: str | None) -> str:
    return _require_text(value, "plateforme_erp").upper()

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models import ConsigneModel


def upsert_consigne(
    db: Session,
    *,
    code_article: str,
    plateforme: str,
    texte_consigne: str,
    valeur_consigne: float = 0,
    acheteur: str = "Seb",
) -> ConsigneModel:
    code_article_normalise = _require_text(code_article, "code_article")
    plateforme_normalisee = _require_text(plateforme, "plateforme")
    texte_normalise = _require_text(texte_consigne, "texte_consigne")
    acheteur_normalise = _require_text(acheteur, "acheteur")

    existing = (
        db.query(ConsigneModel)
        .filter(ConsigneModel.acheteur == acheteur_normalise)
        .filter(ConsigneModel.code_article == code_article_normalise)
        .filter(ConsigneModel.plateforme == plateforme_normalisee)
        .one_or_none()
    )

    if existing is None:
        existing = ConsigneModel(
            acheteur=acheteur_normalise,
            code_article=code_article_normalise,
            plateforme=plateforme_normalisee,
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


def list_consignes(
    db: Session,
    *,
    acheteur: str | None = None,
    code_article: str | None = None,
    plateforme: str | None = None,
) -> list[ConsigneModel]:
    query = db.query(ConsigneModel)

    if acheteur:
        query = query.filter(ConsigneModel.acheteur == acheteur.strip())
    if code_article:
        query = query.filter(ConsigneModel.code_article == code_article.strip())
    if plateforme:
        query = query.filter(ConsigneModel.plateforme == plateforme.strip())

    return (
        query.order_by(
            ConsigneModel.acheteur.asc(),
            ConsigneModel.code_article.asc(),
            ConsigneModel.plateforme.asc(),
            ConsigneModel.id.asc(),
        )
        .all()
    )


def _require_text(value: str, field_name: str) -> str:
    text = (value or "").strip()
    if not text:
        raise ValueError(f"{field_name} obligatoire")
    return text

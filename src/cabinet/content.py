"""Everything the practice says about itself. Bracketed values must be filled in before launch."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Consultation:
    kind: str
    duration: str
    price: str


@dataclass(frozen=True, slots=True)
class Practice:
    name: str
    profession: str
    city: str
    intro: str
    lead: str
    background: str
    approach: str
    consultations: tuple[Consultation, ...]
    address_lines: tuple[str, ...]
    access: str
    phone_display: str
    phone_e164: str
    email: str
    registration: str
    siret: str
    host_name: str
    host_address: str


PRACTICE = Practice(
    name="Hannah Schreiber",
    profession="Psychologue",
    city="Saales",
    intro="Approche centrée sur la personne",
    lead="Consultations de psychologie à la Maison de Services de Saales.",
    background="[Formation, diplômes et parcours professionnel — à compléter]",
    approach=(
        "[Présentation de l’approche centrée sur la personne, "
        "telle que pratiquée au cabinet — à compléter]"
    ),
    consultations=(
        Consultation(
            kind="[Type de consultation — à compléter]",
            duration="[Durée — à compléter]",
            price="[Tarif — à compléter]",
        ),
    ),
    address_lines=("Maison de Services", "30 Grand Rue", "67420 Saales"),
    access="[Notes d’accès : stationnement, étage, accessibilité — à compléter]",
    phone_display="07 45 09 20 50",
    phone_e164="+33745092050",
    email="schreiber.hannah.psy@gmail.com",
    registration="[N° ADELI / RPPS]",
    siret="[N° SIRET]",
    host_name="Railway Corporation",
    host_address="[Adresse de l'hébergeur, à reprendre de ses mentions légales]",
)

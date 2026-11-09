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
    intro: str
    about: tuple[str, ...]
    consultations: tuple[Consultation, ...]
    address_lines: tuple[str, ...]
    access: str
    phone_display: str
    phone_e164: str
    email: str
    registration: str
    host_name: str
    host_address: str


PRACTICE = Practice(
    name="Hannah Schreiber",
    profession="Psychologue",
    intro="Approche centrée sur la personne",
    about=(
        "[Parcours, formation et approche thérapeutique.]",
        "[Motifs de consultation accompagnés.]",
    ),
    consultations=(
        Consultation(kind="[Consultation adulte]", duration="[45 min]", price="[00 €]"),
    ),
    address_lines=("Maison de Services", "30 Grand Rue", "67420 Saales"),
    access="[Transports, stationnement, accessibilité.]",
    phone_display="07 45 09 20 50",
    phone_e164="+33745092050",
    email="schreiber.hannah.psy@gmail.com",
    registration="[Numéro ADELI ou RPPS]",
    host_name="Railway Corporation",
    host_address="[Adresse de l'hébergeur, à reprendre de ses mentions légales]",
)

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
    background: tuple[str, ...]
    approach: str
    audience: str
    consultations: tuple[Consultation, ...]
    reimbursement: str
    complement: str
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
    profession="Psychologue et psychothérapeute",
    city="Saales",
    intro="Approche centrée sur la personne",
    lead="Consultations de psychologie pour adultes et adolescents à la Maison de Services de Saales.",
    background=(
        (
            "Après un master en psychologie obtenu en Allemagne et reconnu en France, j’ai exercé "
            "plusieurs années dans des structures variées, auprès de publics différents et avec "
            "diverses approches thérapeutiques : à la MEDIAN Klinik Mühlengrund (Reinhardshausen, "
            "Allemagne), puis à la Maison d’enfance de la Combe et à la clinique de réhabilitation "
            "de Senones. J’exerce aujourd’hui aussi à la Résidence de Saales."
        ),
        (
            "Formée à l’approche centrée sur la personne auprès de la Gesellschaft für angewandte "
            "Psychologie de Marburg, je me suis installée comme psychologue libérale. J’ai également "
            "suivi trois ans de formation à l’École lyonnaise de plantes médicinales et savoirs "
            "naturels."
        ),
    ),
    approach=(
        "Mon approche est avant tout humaine : les ressources se trouvent chez la personne. "
        "La thérapie est un travail d’équipe entre la psychothérapeute et la personne qui "
        "consulte. Selon les besoins qui apparaissent au fil de la thérapie, j’intègre des "
        "éléments des thérapies cognitives et comportementales, de l’approche systémique et "
        "de l’approche psychodynamique."
    ),
    audience="Adultes et adolescents",
    consultations=(
        Consultation(
            kind="Séance de psychothérapie",
            duration="50\u00a0minutes",
            price="55\u00a0€",
        ),
    ),
    reimbursement="Les consultations ne sont pas remboursées par l’Assurance maladie.",
    complement=(
        "Si vous le souhaitez, je peux aussi vous proposer des conseils en herboristerie, "
        "en complément du suivi. Ils ne font pas partie de la psychothérapie et ne remplacent "
        "pas un avis ou un traitement médical."
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

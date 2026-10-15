from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse

import os
import uuid

from django.core.validators import FileExtensionValidator

# ---------- Contacts (base commune) ----------

class ContactBase(models.Model):
    ordre = models.PositiveIntegerField("Ordre", default=0, db_index=True)
    nom = models.CharField("Nom", max_length=100)
    prenom = models.CharField("Prénom", max_length=100, blank=True)
    fonction = models.CharField("Fonction", max_length=150, blank=True)
    telephone = models.CharField("Téléphone", max_length=30, blank=True)
    email = models.EmailField("Mail", blank=True)
    notes = models.TextField("Notes", blank=True)

    class Meta:
        abstract = True
        ordering = ["ordre", "nom", "prenom"]

    def __str__(self):
        return f"{self.prenom} {self.nom}".strip()


# ---------- Entités réutilisables d'une FDR à l'autre ----------

class Lieu(models.Model):
    nom = models.CharField(max_length=200)
    logo = models.ImageField("Logo", upload_to="logos_lieux/", blank=True)
    adresse = models.TextField(blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = "lieux"
        ordering = ["nom"]

    def __str__(self):
        return self.nom


class ContactLieu(ContactBase):
    lieu = models.ForeignKey(Lieu, on_delete=models.CASCADE, related_name="contacts")

    class Meta(ContactBase.Meta):
        verbose_name = "contact du lieu"
        verbose_name_plural = "contacts du lieu"


class Compagnie(models.Model):
    nom = models.CharField(max_length=200)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["nom"]

    def __str__(self):
        return self.nom


class ContactCompagnie(ContactBase):
    compagnie = models.ForeignKey(Compagnie, on_delete=models.CASCADE, related_name="contacts")

    class Meta(ContactBase.Meta):
        verbose_name = "contact de la compagnie"
        verbose_name_plural = "contacts de la compagnie"


class Hebergement(models.Model):
    """Catalogue d'hébergements (description, photos... à enrichir plus tard)."""
    nom = models.CharField(max_length=200)
    adresse = models.TextField(blank=True)
    description = models.TextField(blank=True)
    # Plus tard : photo = models.ImageField(upload_to="hebergements/", blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = "hébergement"
        verbose_name_plural = "hébergements"
        ordering = ["nom"]

    def __str__(self):
        return self.nom


def chemin_fichier_spectacle(instance, nom):
    # préfixe aléatoire : les URL des fichiers ne sont pas devinables
    return f"spectacles/{uuid.uuid4().hex[:12]}_{nom}"


class Spectacle(models.Model):
    nom = models.CharField(max_length=200)
    compagnie = models.ForeignKey(Compagnie, on_delete=models.PROTECT, related_name="spectacles")
    duree = models.CharField("Durée", max_length=100, blank=True)
    lien = models.URLField("Lien", blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["nom"]
        constraints = [
            models.UniqueConstraint(fields=["compagnie", "nom"], name="spectacle_unique_par_compagnie"),
        ]

    def __str__(self):
        return self.nom

    def get_absolute_url(self):
        return reverse("roadmap:spectacle_detail", args=[self.pk])

class ContactSpectacle(ContactBase):
    spectacle = models.ForeignKey(Spectacle, on_delete=models.CASCADE, related_name="contacts")

    class Meta(ContactBase.Meta):
        verbose_name = "contact du spectacle"
        verbose_name_plural = "contacts du spectacle"


class FichierSpectacle(models.Model):
    spectacle = models.ForeignKey(Spectacle, on_delete=models.CASCADE, related_name="fichiers")
    titre = models.CharField("Intitulé", max_length=150, blank=True,
                             help_text="Ex. : Fiche technique, Plan de feu")
    fichier = models.FileField(
        upload_to=chemin_fichier_spectacle,
        validators=[FileExtensionValidator(["pdf", "jpg", "jpeg", "png"])],
    )

    class Meta:
        verbose_name = "fichier du spectacle"
        verbose_name_plural = "fichiers du spectacle"
        ordering = ["titre"]

    @property
    def nom_affiche(self):
        return self.titre or os.path.basename(self.fichier.name)

    def __str__(self):
        return self.nom_affiche

# ---------- La feuille de route ----------

class FDR(models.Model):
    class Statut(models.TextChoices):
        BROUILLON = "brouillon", "Brouillon"
        ENVOYE = "envoye", "Envoyé"
        VALIDE = "valide", "Validé"

    class Type(models.TextChoices):
        SPECTACLE = "spectacle", "Spectacle"
        RESIDENCE = "residence", "Residence"
        SOIREE = "soiree", "Soirée"

    spectacle = models.ForeignKey("Spectacle", on_delete=models.PROTECT, related_name="fdrs")
    compagnie = models.ForeignKey(Compagnie, on_delete=models.PROTECT, related_name="fdrs")
    statut = models.CharField(
        "Statut", max_length=10, choices=Statut.choices, default=Statut.BROUILLON,
    )
    type = models.CharField(
        "Type", max_length=10, choices=Type.choices, default=Type.SPECTACLE,
    )
    date = models.DateField("Date (début)")
    date_fin = models.DateField(
        "Date de fin", null=True, blank=True,
        help_text="À laisser vide si l'événement n'a lieu qu'un seul jour.",
    )
    heure = models.CharField(
        "Heure", max_length=200, blank=True,
        help_text='Texte libre, ex. : "14h30 (scolaire) + 20h (TP)"',
    )
    lieu = models.ForeignKey(Lieu, on_delete=models.PROTECT, related_name="fdrs")
    notes = models.TextField(blank=True)
    cree_le = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "feuille de route"
        verbose_name_plural = "feuilles de route"
        ordering = ["-date"]

    def __str__(self):
        return f"{self.spectacle} – {self.compagnie} ({self.date:%d/%m/%Y})"

    def clean(self):
        erreurs = {}
        if self.date_fin and self.date and self.date_fin < self.date:
            erreurs["date_fin"] = "La date de fin doit être après la date de début."
        if self.spectacle_id and self.compagnie_id and self.spectacle.compagnie_id != self.compagnie_id:
            erreurs["spectacle"] = "Ce spectacle n'appartient pas à la compagnie choisie."
        if erreurs:
            raise ValidationError(erreurs)

    @property
    def contacts_compagnie(self):
        return list(self.compagnie.contacts.all()) + list(self.spectacle.contacts.all())

    def get_absolute_url(self):
        return reverse("roadmap:detail", args=[self.pk])

    @property
    def grille_repas(self):
        moments = ("matin", "midi", "soir")
        groupes = ("cie", "orga")
        totaux = {"total": 0, "cie": 0, "orga": 0, "matin": 0, "midi": 0, "soir": 0}
        jours = {}
        for r in self.repas.all():  # utilise le prefetch de la vue
            if r.nombre == 0:       # une ligne à 0 est ignorée à l'affichage
                continue
            j = jours.setdefault(r.date, {
                "date": r.date, "total": 0,
                **{f"{m}_{g}": {"repas": [], "nombre": 0} for m in moments for g in groupes},
            })
            j[f"{r.moment}_{r.groupe}"]["repas"].append(r)
            j[f"{r.moment}_{r.groupe}"]["nombre"] += r.nombre
            j["total"] += r.nombre
            totaux["total"] += r.nombre
            totaux[r.groupe] += r.nombre
            totaux[r.moment] += r.nombre
        return {"jours": [jours[d] for d in sorted(jours)], "totaux": totaux}


class ContactPrestataire(ContactBase):
    """Prestataires et autres intervenants, propres à une FDR."""
    fdr = models.ForeignKey(FDR, on_delete=models.CASCADE, related_name="prestataires")

    class Meta(ContactBase.Meta):
        verbose_name = "prestataire / intervenant"
        verbose_name_plural = "prestataires / intervenants"


class Transport(models.Model):
    class Moyen(models.TextChoices):
        TRAIN = "train", "Train"
        AVION = "avion", "Avion"
        VOITURE = "voiture", "Voiture"
        VAN = "van", "Van / utilitaire"
        BUS = "bus", "Bus / car"
        AUTRE = "autre", "Autre"

    fdr = models.ForeignKey(FDR, on_delete=models.CASCADE, related_name="transports")
    date = models.DateField()
    qui = models.CharField("Qui", max_length=150)
    depart = models.CharField("De", max_length=150)
    arrivee = models.CharField("À", max_length=150)
    moyen = models.CharField("Moyen de transport", max_length=20, choices=Moyen.choices)
    heure_depart = models.TimeField("Heure de départ", null=True, blank=True)
    heure_arrivee = models.TimeField("Heure d'arrivée", null=True, blank=True)
    note = models.TextField(blank=True)

    class Meta:
        verbose_name = "voyage / transport"
        verbose_name_plural = "voyages et transports"
        ordering = ["date", "heure_depart"]

    def __str__(self):
        return f"{self.qui} : {self.depart} → {self.arrivee} ({self.date:%d/%m})"


class HebergementFDR(models.Model):
    """Hébergement choisi (dans le catalogue) pour une FDR."""
    fdr = models.ForeignKey(FDR, on_delete=models.CASCADE, related_name="hebergements")
    hebergement = models.ForeignKey(Hebergement, on_delete=models.PROTECT)
    distance = models.CharField("Distance depuis le lieu", max_length=100, blank=True)
    chambres_single = models.PositiveIntegerField("Chambres single", default=0)
    chambres_double = models.PositiveIntegerField("Chambres double", default=0)
    chambres_twin = models.PositiveIntegerField("Chambres twin", default=0)
    note = models.TextField(blank=True)

    class Meta:
        verbose_name = "hébergement de la FDR"
        verbose_name_plural = "hébergements de la FDR"

    def __str__(self):
        return f"{self.hebergement} ({self.fdr})"

class Repas(models.Model):
    class Moment(models.TextChoices):
        MATIN = "matin", "Matin"
        MIDI = "midi", "Midi"
        SOIR = "soir", "Soir"

    class Groupe(models.TextChoices):
        CIE = "cie", "Compagnie"
        ORGA = "orga", "Organisation"

    class Type(models.TextChoices):
        SURPLACE = "surplace", "Sur place"
        RESTAURANT = "resto", "Restaurant"
        DEFRAIEMENT = "defr", "Défraiement"
        CANTINE = "cantine", "Cantine"
        HEBERGEMENT = "hebergement", "Hébergement"
        DECENTR = "decentr", "Décentralisé"

    fdr = models.ForeignKey(FDR, on_delete=models.CASCADE, related_name="repas")
    date = models.DateField()
    moment = models.CharField(max_length=12, choices=Moment.choices)
    groupe = models.CharField("Pour", max_length=12, choices=Groupe.choices)
    type = models.CharField(max_length=12, choices=Type.choices, default=Type.RESTAURANT)
    lieu = models.CharField("Lieu / restaurant", max_length=200, blank=True)
    nombre = models.PositiveIntegerField("Nombre", default=0)
    regime = models.CharField("Régime alimentaire", max_length=255, blank=True)
    note = models.TextField(blank=True)

    class Meta:
        verbose_name = "repas"
        verbose_name_plural = "repas"
        ordering = ["date", "moment", "groupe"]  # matin < midi < soir, cie < orga

    def __str__(self):
        return f"{self.date:%d/%m} {self.get_moment_display()} – {self.get_groupe_display()} ({self.nombre})"

class Deroulement(models.Model):
    fdr = models.ForeignKey(FDR, on_delete=models.CASCADE, related_name="deroulement")
    date = models.DateField()
    heure_debut = models.TimeField("Début")
    heure_fin = models.TimeField("Fin", null=True, blank=True)
    mission = models.CharField(max_length=255)
    personnel = models.CharField(max_length=255, blank=True)

    class Meta:
        verbose_name = "déroulement"
        verbose_name_plural = "déroulement"
        ordering = ["date", "heure_debut"]

    def __str__(self):
        return f"{self.date:%d/%m} {self.heure_debut:%H:%M} – {self.mission}"

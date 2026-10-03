from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse


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


# ---------- La feuille de route ----------

class FDR(models.Model):
    spectacle = models.CharField(max_length=200)
    compagnie = models.ForeignKey(Compagnie, on_delete=models.PROTECT, related_name="fdrs")
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
        if self.date_fin and self.date and self.date_fin < self.date:
            raise ValidationError({"date_fin": "La date de fin doit être après la date de début."})

    def get_absolute_url(self):
        return reverse("roadmap:detail", args=[self.pk])

    @property
    def resume_repas(self):
        jours = {}
        for r in self.repas.all():  # utilise le prefetch de la vue
            j = jours.setdefault(r.date, {"date": r.date, "matin": 0, "midi": 0, "soir": 0})
            j["matin"] += r.cie_matin
            j["midi"] += r.cie_midi + r.orga_midi
            j["soir"] += r.cie_soir + r.orga_soir

        liste = [jours[d] for d in sorted(jours)]
        for j in liste:
            j["total"] = j["matin"] + j["midi"] + j["soir"]

        total = {k: sum(j[k] for j in liste) for k in ("matin", "midi", "soir", "total")}
        return {"jours": liste, "total": total}

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


class Restauration(models.Model):
    class Type(models.TextChoices):
        SURPLACE = "surplace", "Sur place"
        RESTAURANT = "resto", "Restaurant"
        DEFRAIEMENT = "defr", "Défraiement"
        CANTINE = "cantine", "Cantine"
        HEBERGEMENT = "hebergement", "Hébergement"

    fdr = models.ForeignKey(FDR, on_delete=models.CASCADE, related_name="repas")
    date = models.DateField()
    type = models.CharField(max_length=15, choices=Type.choices)
    cie_matin = models.PositiveIntegerField("Cie – matin", default=0)
    cie_midi = models.PositiveIntegerField("Cie – midi", default=0)
    cie_soir = models.PositiveIntegerField("Cie – soir", default=0)
    orga_midi = models.PositiveIntegerField("Orga – midi", default=0)
    orga_soir = models.PositiveIntegerField("Orga – soir", default=0)
    regime = models.CharField("Régime alimentaire", max_length=255, blank=True)
    note = models.TextField(blank=True)

    class Meta:
        verbose_name = "restauration"
        verbose_name_plural = "restauration"
        ordering = ["date"]

    def __str__(self):
        return f"{self.get_type_display()} – {self.date:%d/%m/%Y}"

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

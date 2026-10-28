"""Couche de données de l'application Partir en appart! v2 (phase P1).

Ce module ne dépend pas de Streamlit : les tests peuvent l'importer sans
réseau. Il contient les constantes du projet, le chargement des profils,
le hachage des mots de passe, les deux magasins (mémoire et Supabase REST)
et les fonctions métier : inscription, connexion, progression et
réinitialisation du mot de passe par le prof.

Tables Supabase (nouvelles, préfixe appart2_) :
  appart2_comptes  : identifiant, nom_affiche, nom_norm, groupe,
                     cas_numero, mdp_hash, cree_le
  appart2_dossiers : identifiant, donnees (JSON), maj_le
La table de la v1 (dossiers_appart) n'est jamais touchée.
"""
import hashlib
import hmac
import json
import os
import unicodedata
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

TZ = ZoneInfo("America/Toronto")

# ---------------------------------------------------------------- constantes
GROUPES = ["502", "505", "507", "508"]
CODE_PROF = "1959"  # Console du prof : phase P3. Aucune interface en P1.
LONGUEUR_MIN_MOT_DE_PASSE = 6

PIECES = ["Ma chambre", "La chambre de mon coloc", "Cuisine", "Salon",
          "Salle de bain", "Entrée et rangement"]

SECTIONS = [
    ("S1", "Mon profil et mes revenus"),
    ("S2", "Mon logement"),
    ("S3", "Mon installation"),
    ("S4", "Mes services et forfaits"),
    ("S5", "Transport et épicerie"),
    ("S6", "Mon budget, prévu et vécu"),
    ("S7", "Ma réflexion"),
]

SQL_CREATION = [
    """
    CREATE TABLE IF NOT EXISTS appart2_comptes (
        identifiant TEXT PRIMARY KEY,
        nom_affiche TEXT,
        nom_norm TEXT,
        groupe TEXT,
        cas_numero INT,
        mdp_hash TEXT,
        cree_le TEXT
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS appart2_dossiers (
        identifiant TEXT PRIMARY KEY,
        donnees JSONB,
        maj_le TEXT
    );
    """,
]

MESSAGE_MAUVAIS_MOT_DE_PASSE = (
    "Mot de passe incorrect. Réessaie, ou demande à ton enseignant "
    "de le réinitialiser."
)


def maintenant_str():
    return datetime.now(TZ).strftime("%Y-%m-%d %H:%M:%S")


# ------------------------------------------------------------------- profils
_cache_profils = None


def _chemins_profils():
    candidats = []
    env = os.environ.get("APPART2_PROFILS")
    if env:
        candidats.append(Path(env))
    ici = Path(__file__).resolve().parent
    candidats.append(ici / "profils.json")
    candidats.append(ici.parent / "profils.json")
    return candidats


def charger_profils():
    """Retourne la liste des 30 profils, triée par numéro."""
    global _cache_profils
    if _cache_profils is None:
        for chemin in _chemins_profils():
            if chemin.exists():
                doc = json.loads(chemin.read_text(encoding="utf-8"))
                profils = doc["profils"] if isinstance(doc, dict) else doc
                _cache_profils = sorted(profils, key=lambda p: p["numero"])
                break
        else:
            raise FileNotFoundError(
                "profils.json introuvable (cherché : "
                + ", ".join(str(c) for c in _chemins_profils()) + ")")
    return _cache_profils


def profil_par_numero(numero):
    for p in charger_profils():
        if int(p["numero"]) == int(numero):
            return p
    return None


# ----------------------------------------------------------------------- noms
def normaliser_nom(texte):
    """Minuscules, sans accents, espaces simples. Sert à reconnaître un nom."""
    t = unicodedata.normalize("NFD", (texte or "").strip().lower())
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    return " ".join(t.split())


def nom_normalise_complet(prenom, nom):
    return normaliser_nom(f"{prenom} {nom}")


def nom_affiche(prenom, nom):
    return f"{(prenom or '').strip()} {(nom or '').strip()}".strip()


def identifiant_pour(prenom, nom, groupe):
    slug = nom_normalise_complet(prenom, nom).replace(" ", "-")
    return f"{slug}__{groupe}"


# --------------------------------------------------------------- mots de passe
def hacher_mot_de_passe(mot_de_passe, sel=None):
    """Hachage PBKDF2-SHA256 avec sel aléatoire. Jamais de mot de passe en clair."""
    if sel is None:
        sel = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", mot_de_passe.encode("utf-8"), sel, 100_000)
    return f"pbkdf2${sel.hex()}${dk.hex()}"


def verifier_mot_de_passe(mot_de_passe, stocke):
    try:
        algo, sel_hex, hash_hex = (stocke or "").split("$")
    except ValueError:
        return False
    if algo != "pbkdf2":
        return False
    dk = hashlib.pbkdf2_hmac("sha256", (mot_de_passe or "").encode("utf-8"),
                             bytes.fromhex(sel_hex), 100_000)
    return hmac.compare_digest(dk.hex(), hash_hex)


# ------------------------------------------------------------------- magasins
class MagasinIndisponible(Exception):
    pass


class MagasinMemoire:
    """Magasin en mémoire : tests locaux et repli si Supabase est injoignable."""
    mode = "memoire"

    def __init__(self):
        self.comptes = {}
        self.dossiers = {}

    def creer_compte(self, compte):
        self.comptes[compte["identifiant"]] = dict(compte)

    def compte_par_identifiant(self, identifiant):
        c = self.comptes.get(identifiant)
        return dict(c) if c else None

    def comptes_par_nom_norm(self, nom_norm):
        return [dict(c) for c in self.comptes.values()
                if c["nom_norm"] == nom_norm]

    def cas_pris(self, groupe, cas_numero):
        return any(c["groupe"] == groupe and int(c["cas_numero"]) == int(cas_numero)
                   for c in self.comptes.values())

    def sauvegarder_dossier(self, identifiant, donnees):
        # Copie profonde par JSON : imite la sérialisation de Supabase et
        # évite que l'appelant modifie le dossier stocké par référence.
        self.dossiers[identifiant] = json.loads(json.dumps(donnees))

    def charger_dossier(self, identifiant):
        d = self.dossiers.get(identifiant)
        return json.loads(json.dumps(d)) if d is not None else None

    def maj_mdp_hash(self, identifiant, nouveau_hash):
        if identifiant in self.comptes:
            self.comptes[identifiant]["mdp_hash"] = nouveau_hash
            return True
        return False


class MagasinSupabase:
    """Magasin Supabase, accès REST (même projet que la simulation boursière)."""
    mode = "supabase"

    def __init__(self, url, cle):
        self.base = url.rstrip("/")
        self.cle = cle

    def _req(self, methode, path, data=None, prefer=None):
        req = urllib.request.Request(self.base + path, method=methode,
                                     data=json.dumps(data).encode() if data is not None else None)
        req.add_header("apikey", self.cle)
        req.add_header("Authorization", f"Bearer {self.cle}")
        if data is not None:
            req.add_header("Content-Type", "application/json")
        if prefer:
            req.add_header("Prefer", prefer)
        try:
            with urllib.request.urlopen(req, timeout=15) as rep:
                corps = rep.read().decode("utf-8")
                return json.loads(corps) if corps else None
        except Exception as e:
            raise MagasinIndisponible(str(e)) from e

    def tester(self):
        try:
            self._req("GET", "/rest/v1/appart2_comptes?select=identifiant&limit=1")
            return True
        except MagasinIndisponible:
            return False

    def creer_compte(self, compte):
        self._req("POST", "/rest/v1/appart2_comptes", compte,
                  prefer="return=representation")

    def compte_par_identifiant(self, identifiant):
        rows = self._req("GET", "/rest/v1/appart2_comptes?identifiant=eq."
                         + urllib.parse.quote(identifiant) + "&select=*")
        return rows[0] if rows else None

    def comptes_par_nom_norm(self, nom_norm):
        return self._req("GET", "/rest/v1/appart2_comptes?nom_norm=eq."
                         + urllib.parse.quote(nom_norm) + "&select=*") or []

    def cas_pris(self, groupe, cas_numero):
        rows = self._req("GET", "/rest/v1/appart2_comptes?groupe=eq."
                         + urllib.parse.quote(str(groupe))
                         + f"&cas_numero=eq.{int(cas_numero)}&select=identifiant")
        return bool(rows)

    def sauvegarder_dossier(self, identifiant, donnees):
        self._req("POST", "/rest/v1/appart2_dossiers",
                  {"identifiant": identifiant, "donnees": donnees,
                   "maj_le": maintenant_str()},
                  prefer="resolution=merge-duplicates,return=representation")

    def charger_dossier(self, identifiant):
        rows = self._req("GET", "/rest/v1/appart2_dossiers?identifiant=eq."
                         + urllib.parse.quote(identifiant) + "&select=donnees")
        return rows[0]["donnees"] if rows else None

    def maj_mdp_hash(self, identifiant, nouveau_hash):
        rows = self._req("PATCH", "/rest/v1/appart2_comptes?identifiant=eq."
                         + urllib.parse.quote(identifiant),
                         {"mdp_hash": nouveau_hash}, prefer="return=representation")
        return bool(rows)


def creer_magasin(config=None):
    """Supabase si la config est présente et joignable, sinon magasin mémoire."""
    config = config or {}
    url = config.get("APPART2_SUPABASE_URL") or os.environ.get("APPART2_SUPABASE_URL")
    cle = config.get("APPART2_SUPABASE_KEY") or os.environ.get("APPART2_SUPABASE_KEY")
    if url and cle:
        magasin = MagasinSupabase(url, cle)
        if magasin.tester():
            return magasin
    return MagasinMemoire()


# ------------------------------------------------------------------- dossiers
def nouveau_dossier(profil):
    return {
        "cas_numero": int(profil["numero"]),
        "progression": {code: "a_faire" for code, _ in SECTIONS},
        "pieces": {piece: "a_faire" for piece in PIECES},
        "solde": float(profil["epargne_depart"]),
        "cree_le": maintenant_str(),
        "imprevus": [],
    }


def nom_section(code_section):
    for code, nom in SECTIONS:
        if code == code_section:
            return nom
    return code_section


def section_courante(dossier):
    """Première section pas encore terminée, ou None si tout est fait."""
    progression = (dossier or {}).get("progression", {})
    for code, _ in SECTIONS:
        if progression.get(code) != "fait":
            return code
    return None


def definir_progression(magasin, identifiant, code_section, etat):
    """Met à jour l'état d'une section dans le dossier stocké, et le retourne."""
    if code_section not in [c for c, _ in SECTIONS]:
        raise ValueError(f"Section inconnue : {code_section}")
    if etat not in ("a_faire", "en_cours", "fait"):
        raise ValueError(f"État inconnu : {etat}")
    dossier = magasin.charger_dossier(identifiant)
    if dossier is None:
        raise ValueError(f"Dossier introuvable : {identifiant}")
    dossier.setdefault("progression", {})[code_section] = etat
    magasin.sauvegarder_dossier(identifiant, dossier)
    return dossier


# --------------------------------------------------------------------- métier
def inscrire(magasin, prenom, nom, groupe, cas_numero,
             mot_de_passe, confirmation):
    """Inscription d'un élève. Retourne un dict ok / message / identifiant."""
    def refus(message):
        return {"ok": False, "message": message, "identifiant": None}

    if not (prenom or "").strip() or not (nom or "").strip():
        return refus("Écris ton prénom et ton nom de famille.")
    if groupe not in GROUPES:
        return refus("Choisis ton groupe dans la liste.")
    try:
        cas = int(cas_numero)
    except (TypeError, ValueError):
        return refus("Le numéro de ton cas doit être entre 1 et 30.")
    profil = profil_par_numero(cas)
    if profil is None:
        return refus("Le numéro de ton cas doit être entre 1 et 30.")
    if len(mot_de_passe or "") < LONGUEUR_MIN_MOT_DE_PASSE:
        return refus("Ton mot de passe est trop court : il faut au moins "
                     f"{LONGUEUR_MIN_MOT_DE_PASSE} caractères.")
    if mot_de_passe != confirmation:
        return refus("Les deux mots de passe ne sont pas pareils. "
                     "Écris le même mot de passe deux fois.")

    identifiant = identifiant_pour(prenom, nom, groupe)
    nom_norm = nom_normalise_complet(prenom, nom)
    for autre in magasin.comptes_par_nom_norm(nom_norm):
        if autre["groupe"] == groupe:
            return refus("Tu as déjà un compte. Va dans « Je me connecte ».")
    if magasin.cas_pris(groupe, cas):
        return refus("Ce cas est déjà pris dans ton groupe, vérifie ton numéro.")

    compte = {
        "identifiant": identifiant,
        "nom_affiche": nom_affiche(prenom, nom),
        "nom_norm": nom_norm,
        "groupe": groupe,
        "cas_numero": cas,
        "mdp_hash": hacher_mot_de_passe(mot_de_passe),
        "cree_le": maintenant_str(),
    }
    magasin.creer_compte(compte)
    magasin.sauvegarder_dossier(identifiant, nouveau_dossier(profil))
    return {"ok": True, "message": "Ton compte est créé. Bienvenue dans ton appart!",
            "identifiant": identifiant}


def connecter(magasin, prenom, nom, mot_de_passe):
    """Connexion. Retourne un dict ok / message / compte / dossier."""
    nom_norm = nom_normalise_complet(prenom, nom)
    candidats = magasin.comptes_par_nom_norm(nom_norm)
    if not candidats:
        return {"ok": False,
                "message": "On ne trouve pas ton compte. Vérifie ton nom, "
                           "ou inscris-toi si c'est ta première fois.",
                "compte": None, "dossier": None}
    for compte in candidats:
        if verifier_mot_de_passe(mot_de_passe, compte["mdp_hash"]):
            dossier = magasin.charger_dossier(compte["identifiant"])
            return {"ok": True, "message": "Bon retour dans ton appart!",
                    "compte": compte, "dossier": dossier}
    return {"ok": False, "message": MESSAGE_MAUVAIS_MOT_DE_PASSE,
            "compte": None, "dossier": None}


def reinitialiser_mot_de_passe(magasin, identifiant, nouveau_mot_de_passe):
    """Réinitialisation par le prof (fonction testable, interface en phase P3)."""
    if len(nouveau_mot_de_passe or "") < LONGUEUR_MIN_MOT_DE_PASSE:
        return False, ("Le nouveau mot de passe est trop court : il faut "
                       f"au moins {LONGUEUR_MIN_MOT_DE_PASSE} caractères.")
    if magasin.compte_par_identifiant(identifiant) is None:
        return False, "Compte introuvable."
    ok = magasin.maj_mdp_hash(identifiant, hacher_mot_de_passe(nouveau_mot_de_passe))
    return (True, "Mot de passe réinitialisé.") if ok else (False, "Échec de la réinitialisation.")

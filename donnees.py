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
import secrets
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

    def comptes_du_groupe(self, groupe):
        return [dict(c) for c in self.comptes.values()
                if c["groupe"] == str(groupe)]

    def sauvegarder_dossier(self, identifiant, donnees):
        # Copie profonde par JSON : imite la sérialisation de Supabase et
        # évite que l'appelant modifie le dossier stocké par référence.
        self.dossiers[identifiant] = json.loads(json.dumps(donnees))

    def charger_dossier(self, identifiant):
        d = self.dossiers.get(identifiant)
        return json.loads(json.dumps(d)) if d is not None else None

    def identifiant_par_jeton(self, jeton):
        for identifiant, d in self.dossiers.items():
            if d.get("jeton_session") and d["jeton_session"] == jeton:
                return identifiant
        return None

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

    def comptes_du_groupe(self, groupe):
        return self._req("GET", "/rest/v1/appart2_comptes?groupe=eq."
                         + urllib.parse.quote(str(groupe))
                         + "&select=*&order=nom_affiche") or []

    def sauvegarder_dossier(self, identifiant, donnees):
        self._req("POST", "/rest/v1/appart2_dossiers",
                  {"identifiant": identifiant, "donnees": donnees,
                   "maj_le": maintenant_str()},
                  prefer="resolution=merge-duplicates,return=representation")

    def charger_dossier(self, identifiant):
        rows = self._req("GET", "/rest/v1/appart2_dossiers?identifiant=eq."
                         + urllib.parse.quote(identifiant) + "&select=donnees")
        return rows[0]["donnees"] if rows else None

    def identifiant_par_jeton(self, jeton):
        champ = urllib.parse.quote("donnees->>jeton_session")
        rows = self._req("GET", "/rest/v1/appart2_dossiers?" + champ
                         + "=eq." + urllib.parse.quote(str(jeton))
                         + "&select=identifiant")
        return rows[0]["identifiant"] if rows else None

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


# ------------------------------------------------------ sessions persistantes
def nouveau_jeton_session(magasin, identifiant):
    """Crée le jeton de session persistante d'un élève et le range dans
    son dossier. Un seul jeton actif : un nouveau remplace l'ancien.
    Le jeton voyage dans l'adresse de la page pour survivre au
    rafraîchissement ; il ne donne accès qu'au dossier de son élève."""
    dossier = magasin.charger_dossier(identifiant)
    if dossier is None:
        return None
    jeton = secrets.token_urlsafe(24)
    dossier["jeton_session"] = jeton
    magasin.sauvegarder_dossier(identifiant, dossier)
    return jeton


def identifiant_par_jeton(magasin, jeton):
    """Retrouve l'élève derrière un jeton de session. None si le jeton
    est absent, révoqué ou inconnu ; une panne du magasin ne bloque
    jamais l'écran d'accès."""
    if not jeton:
        return None
    try:
        return magasin.identifiant_par_jeton(jeton)
    except Exception:
        return None


def revoquer_jeton_session(magasin, identifiant):
    """Invalide le jeton de session (déconnexion, réinitialisation du
    mot de passe) : l'ancienne adresse ne rouvre plus le dossier."""
    try:
        dossier = magasin.charger_dossier(identifiant)
        if dossier is not None and dossier.get("jeton_session"):
            dossier["jeton_session"] = None
            magasin.sauvegarder_dossier(identifiant, dossier)
    except Exception:
        pass


# ------------------------------------------------------------------- dossiers
def nouveau_dossier(profil):
    return {
        "cas_numero": int(profil["numero"]),
        "progression": {code: "a_faire" for code, _ in SECTIONS},
        "pieces": {piece: "a_faire" for piece in PIECES},
        "solde": float(profil["epargne_depart"]),
        "cree_le": maintenant_str(),
        "imprevus": [],
        "s2": s2_par_defaut(),
        "s3": s3_par_defaut(),
        "s4": s4_par_defaut(),
        "s5": s5_par_defaut(),
        "s6": s6_par_defaut(),
        "s7": s7_par_defaut(),
        "vie": vie_par_defaut(),
    }


def s2_par_defaut():
    """Structure vide de la S2 : 3 annonces à comparer, un choix, une
    justification et la référence de la capture (fidèle à la v1)."""
    return {
        "annonces": [
            {"adresse": "", "loyer": None, "inclusions": "",
             "distance_km": None, "remarque": ""}
            for _ in range(3)
        ],
        "choix": None,
        "justification": "",
        "capture": "",
    }


def obtenir_s2(dossier):
    """La S2 du dossier, complétée par la structure vide si elle manque
    (les dossiers créés en phase P1 n'ont pas encore de S2)."""
    s2 = (dossier or {}).get("s2")
    if not isinstance(s2, dict):
        return s2_par_defaut()
    defaut = s2_par_defaut()
    for cle, valeur in defaut.items():
        s2.setdefault(cle, valeur)
    while len(s2["annonces"]) < 3:
        s2["annonces"].append({"adresse": "", "loyer": None, "inclusions": "",
                                "distance_km": None, "remarque": ""})
    return s2


def enregistrer_s2(magasin, identifiant, s2):
    """Écrit la S2 dans le dossier stocké et retourne le dossier."""
    dossier = magasin.charger_dossier(identifiant)
    if dossier is None:
        raise ValueError(f"Dossier introuvable : {identifiant}")
    dossier["s2"] = s2
    magasin.sauvegarder_dossier(identifiant, dossier)
    return dossier


def s2_manquants(s2):
    """Ce qu'il manque pour terminer la S2 (liste vide = elle est complète)."""
    manques = []
    for i, a in enumerate(s2.get("annonces", []), start=1):
        if not (a.get("adresse") or "").strip() or not a.get("loyer"):
            manques.append(f"Annonce {i} : il faut au moins l'adresse "
                           "ou le secteur, et le loyer.")
    if s2.get("choix") is None:
        manques.append("Choisis une des 3 annonces.")
    if not (s2.get("justification") or "").strip():
        manques.append("Écris ta justification du choix.")
    if not (s2.get("capture") or "").strip():
        manques.append("Écris la référence de ta capture de l'annonce choisie.")
    return manques


def loyer_choisi(s2):
    """Le loyer de l'annonce choisie, ou None si rien n'est choisi."""
    choix = (s2 or {}).get("choix")
    annonces = (s2 or {}).get("annonces", [])
    if choix is None or not (0 <= int(choix) < len(annonces)):
        return None
    return annonces[int(choix)].get("loyer")


# ------------------------------------------------------------------------ S3
PLAFOND_INSTALLATION = 3500.0
PIECE_COLOC = "La chambre de mon coloc"

# Seuils de niveau par pièce : (MINIMAL, MOYEN, MAXIMAL), en nombre
# d'articles prouvés. Barème validé par Mathieu le 28 octobre 2026.
# JAMAIS affichés aux élèves (décision de Mathieu, 28 oct. 2026) :
# à eux de juger si leur pièce est complète ; il explique les niveaux
# en introduction de classe. Aucun message de l'app ne les révèle.
SEUILS_S3 = {
    "Ma chambre": (8, 13, 17),
    "Cuisine": (11, 21, 28),
    "Salon": (3, 6, 12),
    "Salle de bain": (10, 13, 17),
    "Entrée et rangement": (6, 13, 16),
}
SEUILS_ELECTRO = (2, 4, 6)


def _fmt_montant(valeur):
    return f"{float(valeur):,.2f}".replace(",", " ").replace(".", ",") + " $"


def article_par_defaut(piece):
    """Article vide ajouté dans une pièce : usagé, personnel dans la
    chambre de l'élève, partagé dans les pièces communes (fidèle à la v1).
    Le champ lien est la preuve de l'achat (règle de Mathieu, 28 oct. 2026) :
    sans lien valide, l'achat ne compte pas."""
    return {"nom": "", "prix": None, "etat": "usagé", "lien": "",
            "type": "personnel" if piece == "Ma chambre" else "partagé"}


def electro_par_defaut():
    return {"nom": "", "prix": None, "etat": "usagé", "lien": ""}


def s3_par_defaut():
    """Structure vide de la S3 : les 6 pièces, les électroménagers et la
    note sur la chambre du coloc (fidèle à la v1)."""
    return {
        "pieces": {piece: [] for piece in PIECES},
        "electro": [],
        "note_coloc": "",
    }


def obtenir_s3(dossier):
    """La S3 du dossier, complétée par la structure vide si elle manque
    (les dossiers créés avant la phase P2 n'ont pas encore de S3)."""
    s3 = (dossier or {}).get("s3")
    if not isinstance(s3, dict):
        return s3_par_defaut()
    defaut = s3_par_defaut()
    for cle, valeur in defaut.items():
        s3.setdefault(cle, valeur)
    if not isinstance(s3["pieces"], dict):
        s3["pieces"] = {}
    for piece in PIECES:
        if not isinstance(s3["pieces"].get(piece), list):
            s3["pieces"][piece] = []
    if not isinstance(s3["electro"], list):
        s3["electro"] = []
    for liste in list(s3["pieces"].values()) + [s3["electro"]]:
        for a in liste:
            if isinstance(a, dict) and "lien" not in a:
                a["lien"] = a.get("capture") or ""
    return s3


def enregistrer_s3(magasin, identifiant, s3):
    """Écrit la S3 dans le dossier stocké et retourne le dossier."""
    dossier = magasin.charger_dossier(identifiant)
    if dossier is None:
        raise ValueError(f"Dossier introuvable : {identifiant}")
    dossier["s3"] = s3
    magasin.sauvegarder_dossier(identifiant, dossier)
    return dossier


def articles_nommes(articles):
    """Nombre d'articles dont le nom est écrit (les lignes vides ne
    comptent pas dans le niveau d'une pièce)."""
    return sum(1 for a in articles or [] if (a.get("nom") or "").strip())


def lien_valide(lien):
    """Un lien de preuve plausible : http(s), un domaine avec un point,
    aucun espace. La vérification réelle se fait par l'enseignant en
    cliquant le lien ; ici on refuse ce qui ne peut pas être un lien."""
    t = (lien or "").strip().lower()
    if " " in t or not (t.startswith("http://") or t.startswith("https://")):
        return False
    domaine = t.split("://", 1)[1].split("/")[0]
    return "." in domaine and len(domaine) >= 4


def article_prouve(article):
    """Un achat qui existe : un nom, un prix et un lien de preuve valide.
    Sans les trois, l'achat n'a jamais existé et ne compte nulle part
    (ni niveau, ni total)."""
    return (bool((article.get("nom") or "").strip())
            and bool(article.get("prix"))
            and lien_valide(article.get("lien")))


def article_entame(article):
    """Un article commencé (au moins un champ rempli) mais pas prouvé."""
    commence = (bool((article.get("nom") or "").strip())
                or bool(article.get("prix"))
                or bool((article.get("lien") or "").strip()))
    return commence and not article_prouve(article)


def nombre_prouves(articles):
    """Nombre d'achats qui comptent (prouvés) dans une liste d'articles."""
    return sum(1 for a in articles or [] if article_prouve(a))


def manques_article(article):
    """Ce qui manque à un article pour que l'achat compte."""
    manques = []
    if not (article.get("nom") or "").strip():
        manques.append("un nom")
    if not article.get("prix"):
        manques.append("un prix")
    if not lien_valide(article.get("lien")):
        manques.append("un lien de preuve valide")
    return manques


def niveau_s3(nombre, seuils):
    """Niveau atteint pour un nombre d'articles prouvés :
    None sous le MINIMAL, puis MINIMAL, MOYEN, MAXIMAL."""
    minimal, moyen, maximal = seuils
    if nombre >= maximal:
        return "MAXIMAL"
    if nombre >= moyen:
        return "MOYEN"
    if nombre >= minimal:
        return "MINIMAL"
    return None


def part_article(article):
    """La part de l'élève pour un article : le prix au complet si
    personnel, la moitié si partagé. Un prix absent compte pour 0."""
    prix = article.get("prix") or 0
    return float(prix) / 2 if article.get("type") == "partagé" else float(prix)


def totaux_piece(s3, piece):
    """(total des prix, part de l'élève) pour une pièce, en ne comptant
    QUE les achats prouvés : un achat sans preuve n'existe pas."""
    articles = [a for a in (s3.get("pieces") or {}).get(piece, [])
                if article_prouve(a)]
    total = sum(float(a.get("prix") or 0) for a in articles)
    part = sum(part_article(a) for a in articles)
    return total, part


def totaux_electro(s3):
    """(total des électroménagers prouvés, part de l'élève = la moitié)."""
    total = sum(float(a.get("prix") or 0)
                for a in s3.get("electro", []) if article_prouve(a))
    return total, total / 2


def nombre_sans_preuve(s3):
    """Nombre d'articles commencés mais non prouvés, dans toute la S3."""
    n = 0
    for articles in (s3.get("pieces") or {}).values():
        n += sum(1 for a in articles if article_entame(a))
    n += sum(1 for a in s3.get("electro", []) if article_entame(a))
    return n


def total_installation(s3):
    """La part de l'élève pour toute l'installation : les 5 pièces
    facturables (la chambre du coloc coûte 0 $) + la part électro."""
    total = totaux_electro(s3)[1]
    for piece in PIECES:
        if piece == PIECE_COLOC:
            continue
        total += totaux_piece(s3, piece)[1]
    return total


def totaux_s3(s3):
    """Le total de l'installation S3 : la part de l'élève pour les
    pièces facturables et les électroménagers (achats prouvés
    seulement). Fonction ajoutée à la P4 : l'instantané de complétion
    de la S3 l'appelait sans qu'elle existe, et l'erreur avalée par
    le filet de _montants_section laissait l'instantané vide, donc
    l'installation n'aurait jamais été chargée au calendrier."""
    return {"total": _arrondir2(total_installation(s3))}


def s3_manquants(s3):
    """Ce qu'il manque pour terminer la S3 (liste vide = elle est complète).

    Il faut : chaque pièce facturable et les électroménagers au niveau
    MINIMAL au moins, aucun article à moitié rempli, et le total de
    l'installation sous le plafond de 3 500 $.
    """
    manques = []

    def verifier_articles(articles, endroit):
        for j, a in enumerate(articles or [], start=1):
            if article_entame(a):
                nom = (a.get("nom") or "").strip()
                quoi = f"article {j}" + (f" « {nom} »" if nom else "")
                manques.append(
                    f"{endroit}, {quoi} : il manque "
                    + ", ".join(manques_article(a))
                    + " pour que cet achat compte. Sans preuve, "
                    "l'achat ne compte pas : complète-le ou retire-le.")

    for piece in PIECES:
        if piece == PIECE_COLOC:
            continue
        articles = (s3.get("pieces") or {}).get(piece, [])
        verifier_articles(articles, piece)
        nombre = nombre_prouves(articles)
        if niveau_s3(nombre, SEUILS_S3[piece]) is None:
            manques.append(
                f"{piece} : pas encore assez d'achats prouvés pour que "
                "la pièce fonctionne. Pense à l'essentiel pour y vivre, "
                "chaque achat avec son lien de preuve.")

    electro = s3.get("electro", [])
    verifier_articles(electro, "Électroménagers")
    nombre_e = nombre_prouves(electro)
    if niveau_s3(nombre_e, SEUILS_ELECTRO) is None:
        manques.append(
            "Électroménagers : pas encore assez d'achats prouvés pour "
            "que la cuisine et la lessive fonctionnent. Pense aux gros "
            "essentiels, chaque achat avec son lien de preuve.")

    total = total_installation(s3)
    if total > PLAFOND_INSTALLATION:
        manques.append(
            "Ton installation dépasse le plafond de 3 500 $ de "
            f"{_fmt_montant(total - PLAFOND_INSTALLATION)}.")
    return manques


# ------------------------------------------------------------------------ S4
# Tarif D d'Hydro-Québec au 1er avril 2026 (constantes.md, fidèle à la v1) :
# redevance d'accès 0,46154 $ par jour, calculée sur 30 jours ; tranche 1
# à 0,07065 $/kWh jusqu'à 1 200 kWh (40 kWh par jour) ; tranche 2 à
# 0,11142 $/kWh au-delà ; taxes de 14,975 %.
TARIF_D = {
    "acces_jour": 0.46154,
    "jours": 30,
    "tranche1_taux": 0.07065,
    "tranche1_max_kwh": 1200,
    "tranche2_taux": 0.11142,
    "taxes": 0.14975,
}
BAREME_KWH = {"petit": 1050, "moyen": 1350, "grand": 1700}
TAILLES_ELEC = ["petit", "moyen", "grand", "manuel"]


def _arrondir2(valeur):
    """Arrondi monétaire à 2 décimales, moitié vers le haut, comme le
    Math.round de la v1 (le round de Python descendrait 66,305 à 66,30
    alors que la référence des constantes est 66,31)."""
    from decimal import Decimal, ROUND_HALF_UP
    return float(Decimal(str(float(valeur))).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP))


def s4_par_defaut():
    """Structure vide de la S4 (fidèle à la v1) : l'électricité (taille
    ou saisie manuelle des kWh), internet (prix pour l'appartement,
    partagé), le cellulaire et l'assurance (personnels)."""
    return {
        "electricite": {"taille": "", "kwh_manuel": None},
        "internet": {"fournisseur": "", "prix": None, "capture": ""},
        "cellulaire": {"fournisseur": "", "prix": None, "capture": ""},
        "assurance": {"compagnie": "", "prix": None},
    }


def obtenir_s4(dossier):
    """La S4 du dossier, complétée par la structure vide si elle manque
    (les dossiers créés avant la S4 n'en ont pas)."""
    s4 = (dossier or {}).get("s4")
    if not isinstance(s4, dict):
        return s4_par_defaut()
    defaut = s4_par_defaut()
    for cle, valeur in defaut.items():
        s4.setdefault(cle, valeur)
        if isinstance(valeur, dict) and isinstance(s4[cle], dict):
            for sous_cle, sous_valeur in valeur.items():
                s4[cle].setdefault(sous_cle, sous_valeur)
    return s4


def enregistrer_s4(magasin, identifiant, s4):
    """Écrit la S4 dans le dossier stocké et retourne le dossier."""
    dossier = magasin.charger_dossier(identifiant)
    if dossier is None:
        raise ValueError(f"Dossier introuvable : {identifiant}")
    dossier["s4"] = s4
    magasin.sauvegarder_dossier(identifiant, dossier)
    return dossier


def resoudre_kwh(electricite):
    """La consommation mensuelle en kWh selon la taille choisie, ou la
    saisie manuelle (fidèle au resoudreKwh de la v1)."""
    elec = electricite or {}
    taille = elec.get("taille") or ""
    if taille == "manuel":
        return float(elec.get("kwh_manuel") or 0)
    if taille in BAREME_KWH:
        return float(BAREME_KWH[taille])
    return 0.0


def calculer_electricite(kwh):
    """Le calcul complet du tarif D, démarche comprise (fidèle au
    calculerElectricite de la v1, mêmes arrondis). La part est la
    moitié : l'électricité est un coût partagé avec le coloc."""
    k = max(0.0, float(kwh or 0))
    if k <= 0:
        return {"kwh": 0, "acces": 0.0, "tranche1_kwh": 0,
                "tranche1": 0.0, "tranche2_kwh": 0, "tranche2": 0.0,
                "sous_total": 0.0, "taxes": 0.0, "total": 0.0, "part": 0.0}
    acces_brut = TARIF_D["acces_jour"] * TARIF_D["jours"]
    t1_kwh = min(k, TARIF_D["tranche1_max_kwh"])
    t2_kwh = max(0.0, k - TARIF_D["tranche1_max_kwh"])
    t1_brut = t1_kwh * TARIF_D["tranche1_taux"]
    t2_brut = t2_kwh * TARIF_D["tranche2_taux"]
    sous_total = _arrondir2(acces_brut + t1_brut + t2_brut)
    total = _arrondir2(sous_total * (1 + TARIF_D["taxes"]))
    return {
        "kwh": int(k) if float(k).is_integer() else k,
        "acces": _arrondir2(acces_brut),
        "tranche1_kwh": int(t1_kwh) if float(t1_kwh).is_integer() else t1_kwh,
        "tranche1": _arrondir2(t1_brut),
        "tranche2_kwh": int(t2_kwh) if float(t2_kwh).is_integer() else t2_kwh,
        "tranche2": _arrondir2(t2_brut),
        "sous_total": sous_total,
        "taxes": _arrondir2(sous_total * TARIF_D["taxes"]),
        "total": total,
        "part": _arrondir2(total / 2),
    }


def totaux_s4(s4):
    """Les montants mensuels de la S4, en parts de l'élève : électricité
    et internet partagés à 50 %, cellulaire et assurance personnels.
    C'est ce qui sortira de son compte chaque mois de vie (P3)."""
    s4 = s4 or {}
    elec = calculer_electricite(resoudre_kwh(s4.get("electricite")))
    internet_total = float((s4.get("internet") or {}).get("prix") or 0)
    internet_part = _arrondir2(internet_total / 2)
    cellulaire = _arrondir2(float((s4.get("cellulaire") or {}).get("prix") or 0))
    assurance = _arrondir2(float((s4.get("assurance") or {}).get("prix") or 0))
    return {
        "electricite_total": elec["total"],
        "electricite_part": elec["part"],
        "internet_total": _arrondir2(internet_total),
        "internet_part": internet_part,
        "cellulaire": cellulaire,
        "assurance": assurance,
        "total_mensuel_part": _arrondir2(
            elec["part"] + internet_part + cellulaire + assurance),
    }


def s4_manquants(s4):
    """Ce qu'il manque pour terminer la S4 (fidèle aux contrôles de la
    v1 : taille d'électricité, captures internet et cellulaire)."""
    manques = []
    s4 = s4 or {}
    elec = s4.get("electricite") or {}
    taille = elec.get("taille") or ""
    if not taille:
        manques.append("Électricité : choisis la taille de ton "
                       "appartement, le calcul du tarif D n'est pas fait.")
    elif taille == "manuel" and resoudre_kwh(elec) <= 0:
        manques.append("Électricité : ta saisie manuelle est à 0 kWh, "
                       "aucun calcul n'est possible.")
    internet = s4.get("internet") or {}
    if not (internet.get("fournisseur") or "").strip():
        manques.append("Internet : écris le nom du fournisseur.")
    if not internet.get("prix"):
        manques.append("Internet : écris le prix mensuel pour l'appartement.")
    if not (internet.get("capture") or "").strip():
        manques.append("Internet : écris la référence de ta capture du forfait.")
    cellulaire = s4.get("cellulaire") or {}
    if not (cellulaire.get("fournisseur") or "").strip():
        manques.append("Cellulaire : écris le nom du fournisseur.")
    if not cellulaire.get("prix"):
        manques.append("Cellulaire : écris le prix mensuel de ton forfait.")
    if not (cellulaire.get("capture") or "").strip():
        manques.append("Cellulaire : écris la référence de ta capture du forfait.")
    assurance = s4.get("assurance") or {}
    if not (assurance.get("compagnie") or "").strip():
        manques.append("Assurance habitation : écris le nom de la compagnie.")
    if not assurance.get("prix"):
        manques.append("Assurance habitation : écris le prix mensuel.")
    return manques


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
    if ok:
        revoquer_jeton_session(magasin, identifiant)
    return (True, "Mot de passe réinitialisé.") if ok else (False, "Échec de la réinitialisation.")


# ---------------------------------------------------------------- S5
# Fidèle à la v1 (src/outil-template.html) : transport {mode, cout,
# justification} ; menus de 7 jours x 4 repas, chaque repas {nom,
# ingredients: [{nom, prix, portionsAchat, portionsUtilisees}]}.
# Coût d'un ingrédient : prix x portions utilisées / portions de l'achat.

JOURS = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi",
         "Dimanche"]
TYPES_REPAS = [("dejeuner", "Déjeuner"), ("diner", "Dîner"),
               ("souper", "Souper"), ("collations", "Collations")]
MODES_TRANSPORT = {
    "a-pied": "À pied",
    "velo": "Vélo",
    "autobus-sttr": "Autobus STTR",
    "auto": "Auto",
}
REPERE_STTR = 81.0
FOURCHETTE_EPICERIE = (120.0, 190.0)


def _repas_vide():
    return {"nom": "", "ingredients": []}


def s5_par_defaut():
    return {
        "transport": {"mode": "", "cout": None, "justification": ""},
        "menus": [
            {"jour": jour,
             **{code: _repas_vide() for code, _ in TYPES_REPAS}}
            for jour in JOURS
        ],
    }


def obtenir_s5(dossier):
    """S5 du dossier, avec migration à la volée si elle manque ou si un
    jour / un repas manque (dossiers créés avant la S5)."""
    s5 = dossier.get("s5")
    if not isinstance(s5, dict):
        s5 = s5_par_defaut()
        dossier["s5"] = s5
        return s5
    if not isinstance(s5.get("transport"), dict):
        s5["transport"] = {"mode": "", "cout": None, "justification": ""}
    menus = s5.get("menus")
    if not isinstance(menus, list) or len(menus) != len(JOURS):
        s5["menus"] = s5_par_defaut()["menus"]
        return s5
    for i, jour in enumerate(JOURS):
        if not isinstance(menus[i], dict):
            menus[i] = {"jour": jour,
                        **{c: _repas_vide() for c, _ in TYPES_REPAS}}
            continue
        menus[i]["jour"] = jour
        for code, _ in TYPES_REPAS:
            repas = menus[i].get(code)
            if not isinstance(repas, dict):
                menus[i][code] = _repas_vide()
            else:
                repas.setdefault("nom", "")
                if not isinstance(repas.get("ingredients"), list):
                    repas["ingredients"] = []
    return s5


def enregistrer_s5(magasin, identifiant, s5):
    """Écrit la S5 dans le dossier et le sauvegarde. Renvoie le dossier."""
    dossier = magasin.charger_dossier(identifiant)
    if dossier is None:
        raise ValueError("Dossier introuvable pour " + str(identifiant))
    dossier["s5"] = s5
    magasin.sauvegarder_dossier(identifiant, dossier)
    return dossier


def cout_ingredient(ligne):
    """Coût réel d'un ingrédient : prix x portions utilisées / portions
    de l'achat (arrondi au cent, comme la v1). Sans portions d'achat,
    on prend les portions utilisées ; sans portion utilisée, 0."""
    if not ligne:
        return 0.0
    prix = float(ligne.get("prix") or 0)
    pa = float(ligne.get("portionsAchat") or 0)
    pu = float(ligne.get("portionsUtilisees") or 0)
    if pa <= 0:
        pa = pu if pu > 0 else 1.0
    if pu <= 0:
        return 0.0
    return _arrondir2(prix * pu / pa)


def calculer_epicerie(menus):
    """Totaux de la semaine type : achats inscrits (prix bruts),
    nourriture utilisée (au prorata des portions), part de l'élève
    (50 %) et part mensuelle (semaine x 4,33)."""
    achats = 0.0
    utilisee = 0.0
    for jour in menus or []:
        if not isinstance(jour, dict):
            continue
        for code, _ in TYPES_REPAS:
            repas = jour.get(code) or {}
            for ligne in repas.get("ingredients") or []:
                if not isinstance(ligne, dict):
                    continue
                achats += float(ligne.get("prix") or 0)
                utilisee += cout_ingredient(ligne)
    achats = _arrondir2(achats)
    utilisee = _arrondir2(utilisee)
    semaine_part = _arrondir2(utilisee / 2)
    return {
        "achats_totale": achats,
        "semaine_utilisee": utilisee,
        "semaine_part": semaine_part,
        "mois_part": _arrondir2(semaine_part * 4.33),
        "mois_total": _arrondir2(utilisee * 4.33),
    }


def s5_manquants(s5):
    """Ce qui manque pour déclarer la S5 terminée, dans l'ordre de la
    page : transport, puis les menus (règles de la v1 : aucune case de
    repas vide, chaque repas a ses ingrédients chiffrés avec portions,
    jamais de prix à 0 $)."""
    manques = []
    transport = (s5 or {}).get("transport") or {}
    if not (transport.get("mode") or ""):
        manques.append("Le mode de transport n'est pas choisi.")
    repas_vides, sans_ingredients, prix_zero, portions = [], [], [], []
    for jour in (s5 or {}).get("menus") or []:
        if not isinstance(jour, dict):
            continue
        for code, libelle in TYPES_REPAS:
            repas = jour.get(code) or {}
            etiquette = f"{jour.get('jour', '?')} · {libelle.lower()}"
            if not (repas.get("nom") or "").strip():
                repas_vides.append(etiquette)
                continue
            lignes = [l for l in repas.get("ingredients") or []
                      if isinstance(l, dict)
                      and ((l.get("nom") or "").strip()
                           or (l.get("prix") or 0) > 0)]
            if not lignes:
                sans_ingredients.append(etiquette)
                continue
            for l in lignes:
                nom = (l.get("nom") or "?").strip()
                if (l.get("nom") or "").strip() and not (l.get("prix") or 0):
                    prix_zero.append(f"{etiquette} : {nom}")
                pa = l.get("portionsAchat") or 0
                pu = l.get("portionsUtilisees") or 0
                if pa < 1:
                    portions.append(f"{etiquette} : portions de l'achat "
                                    f"manquantes pour « {nom} »")
                elif pu > pa:
                    portions.append(f"{etiquette} : plus de portions "
                                    f"utilisées qu'achetées pour « {nom} »")
                elif pu <= 0:
                    portions.append(f"{etiquette} : aucune portion "
                                    f"utilisée pour « {nom} »")
    if repas_vides:
        manques.append(
            f"{len(repas_vides)} case(s) de repas encore vide(s) "
            f"(aucune ne peut rester vide) : "
            + " ; ".join(repas_vides[:3])
            + (" ; ..." if len(repas_vides) > 3 else ""))
    if sans_ingredients:
        manques.append(
            f"{len(sans_ingredients)} repas sans aucun ingrédient : "
            + " ; ".join(sans_ingredients[:3])
            + (" ; ..." if len(sans_ingredients) > 3 else ""))
    if prix_zero:
        manques.append("Prix à 0 $ : " + " ; ".join(prix_zero[:3])
                       + (" ; ..." if len(prix_zero) > 3 else ""))
    if portions:
        manques.append("Portions à vérifier : " + " ; ".join(portions[:3])
                       + (" ; ..." if len(portions) > 3 else ""))
    return manques


# ---------------------------------------------------------------- vie
# P3 : le calendrier de vie et la console. Une semaine réelle (dimanche
# au samedi, décalée par les pauses du prof) vaut un mois de vie.
# Application paresseuse : à la connexion, on applique les mois dus
# avec les montants en vigueur à la fermeture de chaque mois (les
# instantanés pris à la complétion des sections, sinon les montants
# de référence : « la vie n'attend pas »).

from datetime import date as _date, timedelta as _timedelta

MOIS_MAX = 9

REFERENCES_VIE = {
    "loyer_total": 1075.0,
    "loyer_part": 537.50,
    "epicerie_mois_part": 335.58,   # 155 $ x 4,33 / 2
    "elec_part": 66.31,             # taille moyenne 1 350 kWh
    "internet_part": 35.0,          # 70 $ / 2
    "cellulaire": 47.50,
    "assurance": 27.50,
    "transport": 81.0,              # repère STTR
}

# Mois de vie d'échéance par section (jalons traduits : fin mars = mois
# 4, mi-avril = mois 6, début mai = mois 9).
ECHEANCES_VIE = {"S1": 4, "S2": 4, "S3": 6, "S4": 6, "S5": 6,
                 "S6": 9, "S7": 9}

BANQUE_CHOIX_VIE = [
    {"id": "frigo-bruit", "titre": "Le frigo fait un drôle de bruit",
     "texte": "Depuis deux jours, le frigo ronfle comme un tracteur. "
              "Ton coloc dit que ce n'est rien. Tu fais quoi ?",
     "options": [
         {"libelle": "Appeler un réparateur tout de suite",
          "montant": -120.0,
          "pourquoi": "La visite du réparateur, la pièce qui force et "
                      "la main-d'œuvre : 120 $. Le frigo repart et ton "
                      "épicerie est sauvée."},
         {"libelle": "Acheter un frigo usagé et revendre l'ancien",
          "montant": -200.0,
          "pourquoi": "Un frigo usagé fiable, livré chez toi : 200 $. "
                      "C'est plus cher qu'une réparation, mais tu "
                      "repars avec un appareil qui fonctionne."},
         {"libelle": "Attendre, ça va peut-être passer",
          "montant": -260.0,
          "pourquoi": "Le frigo finit par lâcher pour de bon. Tu perds "
                      "l'épicerie qu'il contenait (environ 60 $) et tu "
                      "dois acheter un remplacement en urgence, sans "
                      "le temps de magasiner (200 $). Total : 260 $. "
                      "Attendre t'a coûté plus cher que réparer tout "
                      "de suite."}],
     "defaut": 2},
    {"id": "heures-sup", "titre": "Des heures supplémentaires offertes",
     "texte": "Ton employeur cherche quelqu'un pour des quarts de plus "
              "ce mois-ci. C'est fatigant, mais ça paie.",
     "options": [
         {"libelle": "Accepter les heures supplémentaires",
          "montant": 180.0,
          "pourquoi": "Les quarts de plus ce mois-ci, à ton taux "
                      "horaire, paie nette : environ 180 $ de plus "
                      "dans tes poches."},
         {"libelle": "Refuser et garder tes soirées", "montant": 0.0,
          "pourquoi": "Aucun montant : tu gardes tes soirées, et ta "
                      "paie reste celle de ton profil."}],
     "defaut": 1},
    {"id": "ecran-fissure", "titre": "L'écran de ton cellulaire est fissuré",
     "texte": "Il fonctionne encore, mais la fissure traverse l'écran. "
              "Tu fais quoi ?",
     "options": [
         {"libelle": "Faire réparer l'écran", "montant": -110.0,
          "pourquoi": "Changer un écran en atelier : environ 110 $. "
                      "Ton appareil repart comme avant."},
         {"libelle": "Acheter un appareil usagé", "montant": -240.0,
          "pourquoi": "Un appareil usagé correct : environ 240 $. "
                      "C'est le prix pour repartir avec un autre "
                      "téléphone tout de suite."},
         {"libelle": "Endurer la fissure", "montant": -180.0,
          "pourquoi": "La fissure s'étend, l'écran finit par ne plus "
                      "répondre et l'appareil devient inutilisable : "
                      "tu dois le remplacer en catastrophe pour 180 $, "
                      "sans avoir pu magasiner."}],
     "defaut": 2},
    {"id": "sortie-vendredi", "titre": "Une sortie s'organise vendredi",
     "texte": "Des amis (et ton coloc) sortent vendredi soir : souper "
              "et activité. Ça coûte de l'argent, mais la vie sociale "
              "compte aussi.",
     "options": [
         {"libelle": "Participer à la sortie", "montant": -60.0,
          "pourquoi": "Souper et activité entre amis : environ 60 $ "
                      "pour ta part de la soirée."},
         {"libelle": "Rester à l'appartement cette fois",
          "montant": 0.0,
          "pourquoi": "Aucun montant : tu ne dépenses rien ce "
                      "vendredi, et tu gardes ton argent pour le "
                      "reste du mois."}],
     "defaut": 1},
    {"id": "dent-douleur", "titre": "Une dent te fait mal",
     "texte": "Une rage de dent commence. Elle ne partira pas toute "
              "seule, la question c'est quand tu t'en occupes.",
     "options": [
         {"libelle": "Aller chez le dentiste maintenant",
          "montant": -140.0,
          "pourquoi": "Un examen et un traitement tout de suite : "
                      "environ 140 $. Le problème est réglé avant "
                      "qu'il grossisse."},
         {"libelle": "Attendre que ça passe", "montant": -230.0,
          "pourquoi": "La douleur empire et tu finis chez le "
                      "dentiste en urgence : le traitement coûte "
                      "environ 230 $. Attendre a ajouté 90 $ à la "
                      "facture."}],
     "defaut": 1},
    {"id": "coloc-cuisine", "titre": "Ton coloc cuisine en grosses quantités",
     "texte": "Ton coloc propose de cuisiner de grosses quantités pour "
              "la semaine et de partager les ingrédients. Ta part des "
              "courses baisse ce mois-ci si tu embarques.",
     "options": [
         {"libelle": "Embarquer et payer ta part des ingrédients",
          "montant": -30.0,
          "pourquoi": "Ta part des ingrédients achetés en grosses "
                      "quantités pour cuisiner la semaine : 30 $, "
                      "payés tout de suite. C'est le prix du partage."},
         {"libelle": "Continuer chacun de votre bord", "montant": 0.0,
          "pourquoi": "Aucun montant : chacun continue ses courses "
                      "de son bord, rien ne change."}],
     "defaut": 1},
]

BANQUE_BILANS = [
    "Qu'est-ce qui t'a coûté le plus cher ce mois-ci ?",
    "Ta décision de ce mois-ci : tu la referais ?",
    "Ton solde te surprend-il, en bien ou en mal ?",
    "Quel montant t'a semblé le plus injuste ce mois-ci ?",
    "Si tu pouvais changer UNE décision de ce mois-ci, ce serait laquelle ?",
    "Te sens-tu plus en contrôle que le mois passé ?",
    "Quel imprévu t'a le plus appris ce mois-ci ?",
    "Ton coloc et toi : les comptes sont-ils justes ?",
    "En un mot : ce mois-ci, ton argent a travaillé pour toi ou contre toi ?",
]


def vie_par_defaut():
    return {"mouvements": [], "mois_appliques": 0, "completions": {},
            "decisions": {}, "bilans": {}, "connexions": [],
            "installation_payee": False, "annonces": [],
            "a_appliquer": [], "gele": False, "reglages": {}}


def obtenir_vie(dossier):
    vie = dossier.get("vie")
    if not isinstance(vie, dict):
        vie = vie_par_defaut()
        dossier["vie"] = vie
        return vie
    for cle, defaut in vie_par_defaut().items():
        vie.setdefault(cle, defaut)
    return vie


# --- Paramètres de temps par groupe (rangés dans un pseudo-dossier) ---

def _identifiant_parametres(groupe):
    return "__groupe_" + str(groupe)


def parametres_par_defaut(groupe):
    return {"type": "parametres_groupe", "groupe": str(groupe),
            "lance_le": None, "pauses": [], "classement_visible": True}


def obtenir_parametres(magasin, groupe):
    params = magasin.charger_dossier(_identifiant_parametres(groupe))
    if not isinstance(params, dict) or params.get("type") != "parametres_groupe":
        return parametres_par_defaut(groupe)
    params.setdefault("lance_le", None)
    params.setdefault("pauses", [])
    params.setdefault("classement_visible", True)
    return params


def basculer_classement(magasin, groupe):
    """Affiche ou masque le classement du groupe (interrupteur du
    prof, plan v2 section 7). Renvoie le nouvel état visible."""
    params = obtenir_parametres(magasin, groupe)
    params["classement_visible"] = not params.get("classement_visible",
                                                  True)
    _sauver_parametres(magasin, params)
    return params["classement_visible"]


def _sauver_parametres(magasin, params):
    magasin.sauvegarder_dossier(
        _identifiant_parametres(params["groupe"]), params)


def lancer_calendrier(magasin, groupe, date_lancement):
    """Lance (ou relance à une nouvelle date) le calendrier du groupe."""
    params = obtenir_parametres(magasin, groupe)
    params["lance_le"] = _vers_str(date_lancement)
    _sauver_parametres(magasin, params)
    return params


def basculer_pause(magasin, groupe, aujourdhui):
    """Ouvre une pause aujourd'hui, ou ferme la pause ouverte.
    Renvoie True si le calendrier est maintenant en pause."""
    params = obtenir_parametres(magasin, groupe)
    pauses = params.setdefault("pauses", [])
    if pauses and pauses[-1].get("fin") is None:
        pauses[-1]["fin"] = _vers_str(aujourdhui)
        _sauver_parametres(magasin, params)
        return False
    pauses.append({"debut": _vers_str(aujourdhui), "fin": None})
    _sauver_parametres(magasin, params)
    return True


def _vers_date(valeur):
    if isinstance(valeur, _date):
        return valeur
    return _date.fromisoformat(str(valeur)[:10])


def _vers_str(valeur):
    return _vers_date(valeur).isoformat()


def _ancre(params):
    """Dimanche de la semaine de lancement : le jour 1 du mois 1."""
    lance = _vers_date(params["lance_le"])
    return lance - _timedelta(days=(lance.weekday() + 1) % 7)


def _en_pause(params, jour):
    for pause in params.get("pauses", []):
        debut = _vers_date(pause["debut"])
        fin = pause.get("fin")
        if fin is None:
            if jour >= debut:
                return True
        elif debut <= jour < _vers_date(fin):
            return True
    return False


def calendrier_en_pause(params, aujourdhui=None):
    aujourdhui = _vers_date(aujourdhui) if aujourdhui else _date.today()
    return bool(params.get("lance_le")) and _en_pause(params, aujourdhui)


def _jours_effectifs(params, jour):
    """Nombre de jours non en pause entre l'ancre (incluse) et la
    veille du jour donné : c'est l'horloge du calendrier de vie."""
    if not params.get("lance_le"):
        return 0
    ancre = _ancre(params)
    jour = _vers_date(jour)
    if jour <= ancre:
        return 0
    total = 0
    courant = ancre
    while courant < jour:
        if not _en_pause(params, courant):
            total += 1
        courant += _timedelta(days=1)
    return total


def mois_de_vie(params, aujourdhui=None):
    """Mois de vie en cours (1 à 9+) à la date donnée ; 0 si le
    calendrier n'est pas lancé ou pas encore commencé."""
    if not params.get("lance_le"):
        return 0
    aujourdhui = _vers_date(aujourdhui) if aujourdhui else _date.today()
    if aujourdhui < _ancre(params):
        return 0
    return _jours_effectifs(params, aujourdhui) // 7 + 1


def mois_fermes(params, aujourdhui=None):
    """Nombre de mois de vie complètement écoulés (fermés) à la date
    donnée : c'est eux, et eux seuls, que l'application paresseuse
    applique. Le mois en cours se vit, il ne se comptabilise pas
    encore."""
    if not params.get("lance_le"):
        return 0
    aujourdhui = _vers_date(aujourdhui) if aujourdhui else _date.today()
    if aujourdhui < _ancre(params):
        return 0
    return _jours_effectifs(params, aujourdhui) // 7


def date_fermeture_mois(params, mois):
    """Date réelle du dernier jour du mois de vie donné (le samedi de
    sa semaine), en tenant compte des pauses. None si une pause
    ouverte empêche de la connaître."""
    if not params.get("lance_le") or mois < 1:
        return None
    if any(p.get("fin") is None for p in params.get("pauses", [])):
        # Une pause ouverte décale la fermeture d'une durée inconnue.
        if _en_pause(params, _date.today()):
            return None
    ancre = _ancre(params)
    cible = 7 * mois
    compte = 0
    courant = ancre
    for _ in range(800):
        if not _en_pause(params, courant):
            compte += 1
            if compte == cible:
                return courant
        courant += _timedelta(days=1)
    return None


# --- Complétions datées et instantanés de montants ---

def _montants_section(dossier, code):
    """Les montants mensuels qu'une section alimente, calculés sur son
    contenu actuel. Sert d'instantané à la complétion."""
    try:
        if code == "S2":
            s2 = obtenir_s2(dossier)
            choix = s2.get("choix")
            annonces = s2.get("annonces") or []
            if choix is not None and 0 <= int(choix) < len(annonces):
                loyer = float(annonces[int(choix)].get("loyer") or 0)
                if loyer > 0:
                    return {"loyer_total": loyer,
                            "loyer_part": _arrondir2(loyer / 2)}
            return {}
        if code == "S3":
            t = totaux_s3(dossier.get("s3") or s3_par_defaut())
            return {"installation": float(t["total"])}
        if code == "S4":
            t = totaux_s4(obtenir_s4(dossier))
            return {"elec_part": t["electricite_part"],
                    "internet_part": t["internet_part"],
                    "cellulaire": t["cellulaire"],
                    "assurance": t["assurance"]}
        if code == "S5":
            s5 = obtenir_s5(dossier)
            t = calculer_epicerie(s5["menus"])
            cout = s5["transport"].get("cout")
            return {"epicerie_mois_part": t["mois_part"],
                    "transport": float(cout) if cout else 0.0}
        if code == "S6":
            s6 = obtenir_s6(dossier)
            return {"categorie_ecart": s6.get("categorie_ecart") or ""}
    except Exception:
        return {}
    return {}


def marquer_section_faite(magasin, identifiant, code_section):
    """Marque la section terminée ET consigne sa complétion : la date
    réelle et un instantané de ses montants. La première date reste
    la référence pour les retards ; l'instantané se rafraîchit si
    l'élève refait la section."""
    if code_section not in [c for c, _ in SECTIONS]:
        raise ValueError(f"Section inconnue : {code_section}")
    dossier = magasin.charger_dossier(identifiant)
    if dossier is None:
        raise ValueError(f"Dossier introuvable : {identifiant}")
    dossier.setdefault("progression", {})[code_section] = "fait"
    vie = obtenir_vie(dossier)
    completions = vie.setdefault("completions", {})
    precedente = completions.get(code_section) or {}
    completions[code_section] = {
        "date": precedente.get("date") or _date.today().isoformat(),
        "montants": _montants_section(dossier, code_section),
    }
    magasin.sauvegarder_dossier(identifiant, dossier)
    return dossier


def retard_section(code, date_completion, params):
    """Mois de retard d'une section terminée à la date donnée
    (0 = dans sa fenêtre). Compare la date de complétion à la
    fermeture du mois d'échéance du groupe."""
    echeance = ECHEANCES_VIE.get(code)
    if echeance is None or not date_completion:
        return 0
    fermeture = date_fermeture_mois(params, echeance)
    if fermeture is None:
        return 0
    if _vers_date(date_completion) <= fermeture:
        return 0
    mois_completion = mois_de_vie(params, _vers_date(date_completion))
    return max(0, mois_completion - echeance)


def facteur_section(code, date_completion, params):
    """Facteur de la fenêtre notée : 1,0 à temps, moins 25 % par mois
    de retard entamé, plancher à 60 %."""
    retard = retard_section(code, date_completion, params)
    return max(0.60, 1.0 - 0.25 * retard)


# --- Les réglages du prochain mois (« Prépare ton prochain mois ») ---
# Pendant le mois en cours, l'élève règle trois leviers tirés de ses
# propres chiffres ; ils s'appliquent au mois suivant, jamais
# rétroactivement. Heures : écart d'heures par semaine (converti en
# paie nette au prorata du profil). Épicerie et électricité : facteur
# appliqué au montant du mois (le sien ou la référence).
REGLAGES_HEURES = {"garder": 0, "plus": 4, "moins": -4}
REGLAGES_FACTEURS = {
    "epicerie": {"serrer": 0.90, "normal": 1.0, "mieux": 1.10},
    "electricite": {"econome": 0.90, "normal": 1.0, "confort": 1.10},
}


def _delta_heures(profil, code):
    """L'effet mensuel net d'un réglage d'heures, au prorata du
    profil : taux horaire x écart hebdomadaire x 4,33 semaines,
    converti en net avec le ratio net/brut du profil."""
    ecart = REGLAGES_HEURES.get(code, 0)
    if not ecart:
        return 0.0
    brut = float(profil.get("revenu_brut_mensuel") or 0)
    net = float(profil.get("revenu_net_mensuel") or 0)
    ratio = (net / brut) if brut else 0.85
    return _arrondir2(float(profil.get("taux_horaire") or 0)
                      * ecart * 4.33 * ratio)


# --- Génération et application des mouvements ---

def _montant_pour(dossier, code, cle, fermeture):
    """Le montant d'une section pour un mois qui ferme à la date
    donnée : son instantané si elle était terminée à temps pour ce
    mois, sinon le montant de référence (« la vie n'attend pas »)."""
    vie = obtenir_vie(dossier)
    completion = (vie.get("completions") or {}).get(code) or {}
    if completion.get("date") and fermeture is not None:
        if _vers_date(completion["date"]) <= fermeture:
            montants = completion.get("montants") or {}
            if cle in montants:
                return float(montants[cle])
    return REFERENCES_VIE[cle]


def choix_pour_mois(identifiant, mois):
    """Le choix de vie d'un mois, tiré de la banque de façon stable
    pour un élève donné (même élève + même mois = même choix)."""
    base = sum(ord(c) for c in str(identifiant)) + int(mois) * 7
    return BANQUE_CHOIX_VIE[base % len(BANQUE_CHOIX_VIE)]


def generer_mouvements_mois(dossier, profil, params, mois, identifiant=""):
    """Les mouvements automatiques d'un mois de vie, calculés avec ce
    qui était en vigueur à sa fermeture. Renvoie (mouvements, vie
    modifiée ou non) ; ne sauvegarde rien."""
    vie = obtenir_vie(dossier)
    fermeture = date_fermeture_mois(params, mois)
    paie = (float(profil.get("revenu_net_mensuel") or 0)
            + float(profil.get("autre_revenu_mensuel") or 0)
            + float(profil.get("aide_parents_mensuelle") or 0))
    mouvements = []

    def ajoute(jour, libelle, montant, source="auto", pourquoi=None):
        if montant:
            mouvement = {
                "mois": mois, "jour": jour, "libelle": libelle,
                "montant": _arrondir2(montant), "source": source,
                "date_reelle": _date.today().isoformat()}
            if pourquoi:
                mouvement["pourquoi"] = pourquoi
            mouvements.append(mouvement)

    ajoute(1, "Paie du mois (revenu net, autres revenus et aide des "
              "parents)", paie)
    # Les réglages préparés le mois passé s'appliquent à ce mois-ci.
    reglages = (vie.get("reglages") or {}).get(str(mois)) or {}
    delta_h = _delta_heures(profil, reglages.get("heures", "garder"))
    if delta_h:
        ajoute(1, "Heures de travail ajustées (ton réglage)", delta_h)
    if mois == 1:
        ajoute(1, "Premier loyer (mois complet, à l'entrée)",
               -_montant_pour(dossier, "S2", "loyer_total", fermeture))
    else:
        ajoute(1, "Loyer, ta part (50 %)",
               -_montant_pour(dossier, "S2", "loyer_part", fermeture))
    if not vie.get("installation_payee"):
        completion_s3 = (vie.get("completions") or {}).get("S3") or {}
        if completion_s3.get("date") and fermeture is not None:
            if _vers_date(completion_s3["date"]) <= fermeture:
                inst = (completion_s3.get("montants") or {}).get(
                    "installation")
                if inst:
                    ajoute(1, "Installation dans l'appartement "
                              "(ameublement et électroménagers)", -inst)
                    vie["installation_payee"] = True
    facteur_epi = REGLAGES_FACTEURS["epicerie"].get(
        reglages.get("epicerie", "normal"), 1.0)
    lib_epi = "Épicerie du mois (ta part de la semaine type)"
    if facteur_epi != 1.0:
        lib_epi += ", ajustée selon ton réglage"
    ajoute(5, lib_epi,
           -_montant_pour(dossier, "S5", "epicerie_mois_part", fermeture)
           * facteur_epi)
    facteur_elec = REGLAGES_FACTEURS["electricite"].get(
        reglages.get("electricite", "normal"), 1.0)
    lib_elec = "Électricité, ta part (50 %)"
    if facteur_elec != 1.0:
        lib_elec += ", ajustée selon ton réglage"
    ajoute(10, lib_elec,
           -_montant_pour(dossier, "S4", "elec_part", fermeture)
           * facteur_elec)
    ajoute(10, "Internet, ta part (50 %)",
           -_montant_pour(dossier, "S4", "internet_part", fermeture))
    ajoute(15, "Cellulaire",
           -_montant_pour(dossier, "S4", "cellulaire", fermeture))
    ajoute(15, "Assurance habitation",
           -_montant_pour(dossier, "S4", "assurance", fermeture))
    ajoute(15, "Transport",
           -_montant_pour(dossier, "S5", "transport", fermeture))
    # Décision du mois jamais prise : l'option par défaut s'applique.
    decisions = vie.setdefault("decisions", {})
    if str(mois) not in decisions:
        choix = choix_pour_mois(identifiant, mois)
        option = choix["options"][choix["defaut"]]
        ajoute(14, f"Décision manquée : {choix['titre']} "
                   f"({option['libelle']})", option["montant"],
               source="decision", pourquoi=option.get("pourquoi"))
        decisions[str(mois)] = {"choix_id": choix["id"],
                                "option": choix["defaut"],
                                "defaut": True,
                                "montant": option["montant"],
                                "pourquoi": option.get("pourquoi") or ""}
    return mouvements


def appliquer_vie(magasin, identifiant, groupe, profil, aujourdhui=None):
    """Applique les mois de vie dus (application paresseuse, à la
    connexion) et consigne la connexion. Renvoie la liste des
    mouvements nouvellement appliqués."""
    aujourdhui = _vers_date(aujourdhui) if aujourdhui else _date.today()
    dossier = magasin.charger_dossier(identifiant)
    if dossier is None:
        return []
    vie = obtenir_vie(dossier)
    params = obtenir_parametres(magasin, groupe)
    nouveaux = []
    if params.get("lance_le") and not vie.get("gele"):
        cible = min(mois_fermes(params, aujourdhui), MOIS_MAX)
        for mois in range(int(vie.get("mois_appliques") or 0) + 1,
                          cible + 1):
            mouvements = generer_mouvements_mois(
                dossier, profil, params, mois, identifiant)
            programmes = vie.setdefault("a_appliquer", [])
            dus = [a for a in programmes
                   if int(a.get("mois") or 0) <= mois]
            vie["a_appliquer"] = [a for a in programmes
                                  if int(a.get("mois") or 0) > mois]
            for a in dus:
                mouvements.append({
                    "mois": mois, "jour": None,
                    "libelle": a["libelle"],
                    "montant": _arrondir2(a["montant"]),
                    "source": a.get("source", "imprevu"),
                    "date_reelle": _date.today().isoformat()})
            for m in mouvements:
                vie["mouvements"].append(m)
                dossier["solde"] = _arrondir2(
                    float(dossier.get("solde") or 0) + m["montant"])
                nouveaux.append(m)
            vie["mois_appliques"] = mois
    jour_str = aujourdhui.isoformat()
    connexions = vie.setdefault("connexions", [])
    if jour_str not in connexions:
        connexions.append(jour_str)
    magasin.sauvegarder_dossier(identifiant, dossier)
    return nouveaux


def ajouter_mouvement(magasin, identifiant, libelle, montant,
                      source="correction", mois=None, aujourdhui=None,
                      pourquoi=None):
    """Un mouvement manuel au journal (imprévu du prof, événement,
    correction) : il bouge le solde tout de suite. Le pourquoi, quand
    il y en a un, explique le montant à l'élève dans son journal :
    aucun retrait d'argent face à un choix sans explication."""
    aujourdhui = _vers_date(aujourdhui) if aujourdhui else _date.today()
    dossier = magasin.charger_dossier(identifiant)
    if dossier is None:
        raise ValueError(f"Dossier introuvable : {identifiant}")
    vie = obtenir_vie(dossier)
    mouvement = {"mois": mois, "jour": None, "libelle": libelle,
                 "montant": _arrondir2(montant), "source": source,
                 "date_reelle": aujourdhui.isoformat()}
    if pourquoi:
        mouvement["pourquoi"] = pourquoi
    vie["mouvements"].append(mouvement)
    dossier["solde"] = _arrondir2(
        float(dossier.get("solde") or 0) + mouvement["montant"])
    magasin.sauvegarder_dossier(identifiant, dossier)
    return mouvement


def enregistrer_decision(magasin, identifiant, mois, index_option,
                         aujourdhui=None):
    """L'élève tranche le choix de vie du mois en cours : l'effet
    s'applique tout de suite au journal et au solde."""
    aujourdhui = _vers_date(aujourdhui) if aujourdhui else _date.today()
    dossier = magasin.charger_dossier(identifiant)
    if dossier is None:
        raise ValueError(f"Dossier introuvable : {identifiant}")
    vie = obtenir_vie(dossier)
    if str(mois) in (vie.get("decisions") or {}):
        raise ValueError("Décision déjà prise pour ce mois.")
    choix = choix_pour_mois(identifiant, mois)
    if not (0 <= index_option < len(choix["options"])):
        raise ValueError("Option inconnue.")
    option = choix["options"][index_option]
    vie.setdefault("decisions", {})[str(mois)] = {
        "choix_id": choix["id"], "option": index_option,
        "defaut": False, "montant": option["montant"],
        "pourquoi": option.get("pourquoi") or ""}
    magasin.sauvegarder_dossier(identifiant, dossier)
    return ajouter_mouvement(
        magasin, identifiant,
        f"Ta décision : {choix['titre']} ({option['libelle']})",
        option["montant"], source="decision", mois=mois,
        aujourdhui=aujourdhui, pourquoi=option.get("pourquoi"))


def enregistrer_bilan(magasin, identifiant, mois, reponse_choix,
                      phrase):
    """Le bilan éclair du mois : un choix + une phrase, gardés pour
    nourrir la S6 et la S7."""
    dossier = magasin.charger_dossier(identifiant)
    if dossier is None:
        raise ValueError(f"Dossier introuvable : {identifiant}")
    vie = obtenir_vie(dossier)
    vie.setdefault("bilans", {})[str(mois)] = {
        "question": BANQUE_BILANS[(int(mois) - 1) % len(BANQUE_BILANS)],
        "choix": reponse_choix, "phrase": phrase or "",
        "date": _date.today().isoformat()}
    magasin.sauvegarder_dossier(identifiant, dossier)
    return dossier


def enregistrer_reglages(magasin, identifiant, mois_courant, heures,
                         epicerie, electricite, aujourdhui=None):
    """Le plan du mois suivant, préparé pendant le mois en cours.
    Ajustable tant que le mois en cours n'est pas fermé ; les effets
    tombent à la génération du mois visé, jamais avant."""
    aujourdhui = _vers_date(aujourdhui) if aujourdhui else _date.today()
    if not (1 <= int(mois_courant) < MOIS_MAX):
        raise ValueError("Il n'y a pas de mois suivant à préparer.")
    if heures not in REGLAGES_HEURES:
        raise ValueError("Réglage d'heures inconnu.")
    if epicerie not in REGLAGES_FACTEURS["epicerie"]:
        raise ValueError("Réglage d'épicerie inconnu.")
    if electricite not in REGLAGES_FACTEURS["electricite"]:
        raise ValueError("Réglage d'électricité inconnu.")
    dossier = magasin.charger_dossier(identifiant)
    if dossier is None:
        raise ValueError(f"Dossier introuvable : {identifiant}")
    vie = obtenir_vie(dossier)
    vie.setdefault("reglages", {})[str(int(mois_courant) + 1)] = {
        "heures": heures, "epicerie": epicerie,
        "electricite": electricite, "date": aujourdhui.isoformat()}
    magasin.sauvegarder_dossier(identifiant, dossier)
    return dossier


def projeter_mois(dossier, profil, params, mois_cible, reglages=None):
    """Projection d'un mois de vie : les mouvements qu'il donnerait
    avec les réglages fournis (ou ceux déjà notés si reglages=None),
    sans la décision par défaut. Renvoie (mouvements, total). Sert à
    montrer à l'élève l'effet de son plan avant de le garder."""
    import copy as _copy
    copie = _copy.deepcopy(dossier)
    vie = obtenir_vie(copie)
    if reglages is not None:
        vie.setdefault("reglages", {})[str(mois_cible)] = reglages
    mouvements = generer_mouvements_mois(
        copie, profil, params, int(mois_cible), "")
    mouvements = [m for m in mouvements
                  if not str(m.get("libelle", "")).startswith(
                      "Décision manquée")]
    total = _arrondir2(sum(m["montant"] for m in mouvements))
    return mouvements, total


def position_dans_mois(params, aujourdhui=None):
    """(mois en cours, jour de vie 1 à 30) : où on est rendu dans le
    mois de vie, pour encercler le prochain mouvement sur la porte."""
    if not params.get("lance_le"):
        return (0, 0)
    aujourdhui = _vers_date(aujourdhui) if aujourdhui else _date.today()
    if aujourdhui < _ancre(params):
        return (0, 0)
    jours = _jours_effectifs(params, aujourdhui)
    return (jours // 7 + 1, (jours % 7 + 1) * 30 // 7)


# --- Banque d'imprévus du prof et annonces ---

BANQUE_IMPREVUS = [
    {"id": "frigo", "titre": "Le frigo lâche", "montant": -175.0,
     "pourquoi": "Un remplacement en urgence par un appareil usagé "
                 "livré chez toi : 175 $."},
    {"id": "degat-eau", "titre": "Dégât d'eau : franchise d'assurance",
     "montant": -250.0,
     "pourquoi": "C'est la franchise de ton assurance habitation : "
                 "le montant que tu paies de ta poche avant que "
                 "l'assurance couvre le reste des dommages."},
    {"id": "dentiste", "titre": "Dentiste en urgence", "montant": -140.0,
     "pourquoi": "Un examen et un traitement en urgence : environ "
                 "140 $."},
    {"id": "cell-fracasse", "titre": "Cellulaire fracassé",
     "montant": -120.0,
     "pourquoi": "La réparation de l'écran en atelier : environ "
                 "120 $."},
    {"id": "portable", "titre": "L'ordinateur portable lâche",
     "montant": -300.0,
     "pourquoi": "Un portable usagé de dépannage pour continuer tes "
                 "cours : environ 300 $."},
    {"id": "contravention", "titre": "Contravention", "montant": -100.0,
     "pourquoi": "Le montant de l'amende : 100 $, à payer tel quel."},
    {"id": "heures-coupees", "titre": "Heures coupées au travail "
     "(paie réduite de 20 % pour un mois)", "special": "heures_coupees",
     "pourquoi": "Ton employeur coupe tes heures ce mois-ci : ta "
                 "paie baisse de 20 %, et c'est ce montant-là qui "
                 "manque dans ton compte."},
    {"id": "coloc-retard", "titre": "Le coloc paie son loyer en retard "
     "(tu avances sa part, remboursée le mois suivant)",
     "special": "coloc_retard",
     "pourquoi": "Tu avances la part de loyer de ton coloc pour que "
                 "le loyer complet soit payé à temps au propriétaire. "
                 "Il te la rembourse le mois suivant : l'argent "
                 "revient, mais il manque dans ton compte ce mois-ci."},
    {"id": "heures-sup", "titre": "Heures supplémentaires payées",
     "montant": 180.0,
     "pourquoi": "Les quarts supplémentaires que tu as faits, paie "
                 "nette : environ 180 $ de plus dans tes poches."},
    {"id": "impot", "titre": "Remboursement d'impôt", "montant": 220.0,
     "pourquoi": "Ton remboursement d'impôt arrive dans ton compte : "
                 "220 $ de plus."},
    {"id": "coloc-cuisine", "titre": "Le coloc cuisine de grosses "
     "quantités (crédit d'épicerie)", "montant": 90.0,
     "pourquoi": "Cuisiner en grosses quantités avec ton coloc fait "
                 "baisser ta part d'épicerie : 90 $ d'économisés ce "
                 "mois-ci, remis dans ton compte."},
]


def poser_annonce(magasin, identifiant, texte, aujourdhui=None):
    """Une fenêtre d'annonce que l'élève verra à sa prochaine
    connexion (patron des avis de la simulation boursière)."""
    aujourdhui = _vers_date(aujourdhui) if aujourdhui else _date.today()
    dossier = magasin.charger_dossier(identifiant)
    if dossier is None:
        return
    vie = obtenir_vie(dossier)
    vie.setdefault("annonces", []).append(
        {"texte": texte, "date": aujourdhui.isoformat(), "vu": False})
    magasin.sauvegarder_dossier(identifiant, dossier)


def annonces_non_vues(dossier):
    vie = obtenir_vie(dossier)
    return [a for a in vie.get("annonces") or [] if not a.get("vu")]


def marquer_annonces_vues(magasin, identifiant):
    dossier = magasin.charger_dossier(identifiant)
    if dossier is None:
        return
    vie = obtenir_vie(dossier)
    for annonce in vie.get("annonces") or []:
        annonce["vu"] = True
    magasin.sauvegarder_dossier(identifiant, dossier)


def programmer_mouvement(magasin, identifiant, mois, libelle, montant,
                         source="imprevu"):
    """Un montant qui tombera à l'application du mois donné (par
    exemple le remboursement de la part du coloc)."""
    dossier = magasin.charger_dossier(identifiant)
    if dossier is None:
        return
    vie = obtenir_vie(dossier)
    vie.setdefault("a_appliquer", []).append(
        {"mois": int(mois), "libelle": libelle,
         "montant": _arrondir2(montant), "source": source})
    magasin.sauvegarder_dossier(identifiant, dossier)


# --- Journal du prof : tout le chaos est consigné ---

def consigner_prof(magasin, texte, aujourdhui=None):
    aujourdhui = _vers_date(aujourdhui) if aujourdhui else _date.today()
    journal = magasin.charger_dossier("__journal_prof") or \
        {"type": "journal_prof", "entrees": []}
    journal.setdefault("entrees", []).append(
        {"date": aujourdhui.isoformat(), "texte": texte})
    magasin.sauvegarder_dossier("__journal_prof", journal)


def lire_journal_prof(magasin):
    journal = magasin.charger_dossier("__journal_prof") or {}
    return list(journal.get("entrees") or [])


def basculer_gel(magasin, identifiant):
    """Gèle ou dégèle le calendrier d'UN élève (pause individuelle) :
    pendant le gel, aucun mois ne s'applique à son dossier ; au
    dégel, les mois dus s'appliquent d'un coup, comme une absence.
    Renvoie True si le dossier est maintenant gelé."""
    dossier = magasin.charger_dossier(identifiant)
    if dossier is None:
        raise ValueError(f"Dossier introuvable : {identifiant}")
    vie = obtenir_vie(dossier)
    vie["gele"] = not vie.get("gele")
    magasin.sauvegarder_dossier(identifiant, dossier)
    return vie["gele"]


# --- P4 : score de vie, classement, S6 et S7 ---
# Le score de vie (plan v2, section 7) est un jeu de motivation :
# 100 points, 100 % relatifs au profil, jamais de dollars bruts dans
# le classement, et il ne compte jamais dans la note. Chaque
# composante rend ses points AVEC les montants et la raison, en
# langage simple : l'élève sait ce qui lui a coûté des points et
# pourquoi, comme pour les choix de vie (règle du pourquoi).

CATEGORIES_MOUVEMENTS = [
    ("paie", "Paie"),
    ("heures", "Ajustement d'heures (tes réglages)"),
    ("loyer", "Loyer"),
    ("installation", "Installation (une seule fois)"),
    ("epicerie", "Épicerie"),
    ("electricite", "Électricité"),
    ("internet", "Internet"),
    ("cellulaire", "Cellulaire"),
    ("assurance", "Assurance habitation"),
    ("transport", "Transport"),
    ("decisions", "Tes décisions"),
    ("imprevus", "Imprévus reçus"),
    ("evenements", "Événements de classe"),
    ("corrections", "Corrections de ton enseignant"),
    ("autres", "Autres mouvements"),
]

_DEPENSES_RECURRENTES = ("loyer", "epicerie", "electricite",
                         "internet", "cellulaire", "assurance",
                         "transport")


def categoriser_mouvement(mouvement):
    """La catégorie d'un mouvement du journal, d'après sa source et
    son libellé. Sert au score, à la S6 et au dossier résumé."""
    source = mouvement.get("source") or "auto"
    libelle = mouvement.get("libelle") or ""
    if source == "imprevu":
        return "imprevus"
    if source == "decision":
        return "decisions"
    if source == "evenement":
        return "evenements"
    if source == "correction":
        return "corrections"
    if libelle.startswith("Paie du mois"):
        return "paie"
    if libelle.startswith("Heures de travail ajustées"):
        return "heures"
    if "loyer" in libelle.lower():
        return "loyer"
    if libelle.startswith("Installation"):
        return "installation"
    if libelle.startswith("Épicerie"):
        return "epicerie"
    if libelle.startswith("Électricité"):
        return "electricite"
    if libelle.startswith("Internet"):
        return "internet"
    if libelle.startswith("Cellulaire"):
        return "cellulaire"
    if libelle.startswith("Assurance"):
        return "assurance"
    if libelle.startswith("Transport"):
        return "transport"
    return "autres"


def _soldes_fin_mois(dossier, profil):
    """Le solde à la fin de chaque mois fermé, reconstruit depuis
    l'épargne de départ du profil et le journal : les montants
    relatifs du score partent toujours de là, jamais du solde brut
    comparé à d'autres."""
    vie = obtenir_vie(dossier)
    n = int(vie.get("mois_appliques") or 0)
    mouvements = vie.get("mouvements") or []
    solde = float((profil or {}).get("epargne_depart") or 0)
    hors = sum(float(m.get("montant") or 0) for m in mouvements
               if not m.get("mois"))
    soldes = {}
    for mois in range(1, n + 1):
        total = sum(float(m.get("montant") or 0) for m in mouvements
                    if m.get("mois") == mois)
        solde += total + (hors if mois == 1 else 0)
        soldes[mois] = _arrondir2(solde)
    return soldes


def prevu_mensuel(dossier):
    """Le mois type prévu de l'élève, par clé de montant : ses vrais
    montants quand la section est terminée, le montant de référence
    sinon (le même principe que le calendrier : la vie n'attend
    pas)."""
    vie = obtenir_vie(dossier)
    completions = vie.get("completions") or {}
    cles = {"S2": ("loyer_total", "loyer_part"),
            "S4": ("elec_part", "internet_part", "cellulaire",
                   "assurance"),
            "S5": ("epicerie_mois_part", "transport")}
    prevu = {}
    for code, liste in cles.items():
        completion = completions.get(code) or {}
        instantane = completion.get("montants") or {}
        frais = _montants_section(dossier, code)
        for cle in liste:
            if cle in instantane:
                prevu[cle] = float(instantane[cle])
            elif completion.get("date") and cle in frais:
                prevu[cle] = float(frais[cle])
            elif cle in frais and float(frais[cle]) > 0:
                # Un contenu déjà rempli mais pas encore terminé :
                # ses vrais montants valent mieux que la référence.
                # Un zéro d'une section vide, lui, ne remplace
                # jamais la référence (la vie n'attend pas).
                prevu[cle] = float(frais[cle])
            else:
                prevu[cle] = REFERENCES_VIE[cle]
    s3 = (completions.get("S3") or {}).get("montants") or {}
    if "installation" in s3:
        prevu["installation"] = float(s3["installation"])
    else:
        prevu["installation"] = float(
            _montants_section(dossier, "S3").get("installation") or 0.0)
    return prevu


def _paie_profil(profil):
    profil = profil or {}
    return (float(profil.get("revenu_net_mensuel") or 0)
            + float(profil.get("autre_revenu_mensuel") or 0)
            + float(profil.get("aide_parents_mensuelle") or 0))


def calculer_score_vie(dossier, profil):
    """Le score de vie complet : total sur 100 et, par composante,
    les points, le maximum, les montants qui comptent et une
    explication en langage simple. Aucun montant brut d'un autre
    élève n'entre jamais ici."""
    vie = obtenir_vie(dossier)
    mouvements = vie.get("mouvements") or []
    n = int(vie.get("mois_appliques") or 0)
    soldes = _soldes_fin_mois(dossier, profil)
    solde_actuel = float(dossier.get("solde") or 0)

    # Budget (40) : les mois fermés terminés avec un solde positif.
    if n > 0:
        sains = sum(1 for s in soldes.values() if s >= 0)
        pts_budget = 40.0 * sains / n
        plus_bas = min(soldes.values())
        penalite = 0.0
        texte = (f"Sur tes {n} mois fermés, {sains} se sont terminés "
                 f"avec un solde positif. Chaque mois terminé dans le "
                 f"rouge enlève sa part des 40 points. Ton solde le "
                 f"plus bas à une fin de mois : "
                 f"{_fmt_montant(plus_bas)}.")
        if plus_bas < -100.0:
            penalite = min(10.0, pts_budget)
            pts_budget -= penalite
            texte += (" Il est descendu sous -100 $ : 10 points de "
                      "plus en moins, parce qu'un trou de plus de "
                      "100 $ est long à remonter.")
    else:
        sains, plus_bas, penalite = 0, None, 0.0
        pts_budget = 0.0
        texte = ("Aucun mois n'est encore fermé : cette partie du "
                 "score commencera à la fermeture de ton premier "
                 "mois. L'objectif : terminer chaque mois avec un "
                 "solde positif, et ne jamais descendre sous -100 $.")
    budget = {"points": _arrondir2(pts_budget), "max": 40,
              "explication": texte,
              "details": {"mois_fermes": n, "mois_sains": sains,
                          "plus_bas": plus_bas, "penalite": penalite}}

    # Réserve (20) : le solde actuel comparé à SES dépenses d'un
    # mois. Un mois complet de dépenses en réserve = le plein score.
    depenses = 0.0
    if n > 0:
        total_dep = sum(-float(m.get("montant") or 0)
                        for m in mouvements
                        if float(m.get("montant") or 0) < 0
                        and categoriser_mouvement(m)
                        in _DEPENSES_RECURRENTES)
        depenses = total_dep / n
    if depenses <= 0:
        prevu = prevu_mensuel(dossier)
        depenses = (prevu["loyer_part"] + prevu["epicerie_mois_part"]
                    + prevu["elec_part"] + prevu["internet_part"]
                    + prevu["cellulaire"] + prevu["assurance"]
                    + prevu["transport"])
    ratio = (solde_actuel / depenses) if depenses > 0 else 0.0
    pts_reserve = 20.0 * min(1.0, max(0.0, ratio))
    if ratio >= 1.0:
        texte_r = (f"Il te reste {_fmt_montant(solde_actuel)}, soit "
                   f"plus d'un mois complet de tes dépenses "
                   f"({_fmt_montant(depenses)} par mois) : le plein "
                   f"score. Ta réserve peut absorber un gros "
                   f"imprévu sans te mettre dans le rouge.")
    elif ratio > 0:
        texte_r = (f"Il te reste {_fmt_montant(solde_actuel)}, soit "
                   f"{ratio:.1f} mois de tes dépenses "
                   f"({_fmt_montant(depenses)} par mois). L'objectif "
                   f"est un mois complet : chaque dollar gardé de "
                   f"côté te rapproche des 20 points.")
    else:
        texte_r = (f"Ton solde est à {_fmt_montant(solde_actuel)} : "
                   f"aucune réserve pour l'instant. Tes dépenses "
                   f"courantes sont d'environ "
                   f"{_fmt_montant(depenses)} par mois, c'est ce "
                   f"montant-là qu'il faudrait réussir à garder de "
                   f"côté pour le plein score.")
    reserve = {"points": _arrondir2(pts_reserve), "max": 20,
               "explication": texte_r,
               "details": {"solde": solde_actuel,
                           "depenses_mois": _arrondir2(depenses),
                           "ratio": _arrondir2(ratio)}}

    # Appartement (20) : les niveaux de la S3, pièce par pièce, et
    # le plafond d'installation respecté.
    s3 = obtenir_s3(dossier)
    fractions = {"MAXIMAL": 1.0, "MOYEN": 2.0 / 3.0, "MINIMAL": 1.0 / 3.0,
                 None: 0.0}
    niveaux = {}
    somme = 0.0
    blocs = 0
    for piece, seuils in SEUILS_S3.items():
        niveau = niveau_s3(nombre_prouves(
            (s3.get("pieces") or {}).get(piece, [])), seuils)
        niveaux[piece] = niveau or "incomplet"
        somme += fractions[niveau]
        blocs += 1
    niveau_e = niveau_s3(nombre_prouves(s3.get("electro") or []),
                         SEUILS_ELECTRO)
    niveaux["Électroménagers"] = niveau_e or "incomplet"
    somme += fractions[niveau_e]
    blocs += 1
    installation = total_installation(s3)
    pts_appart = 20.0 * (somme / blocs if blocs else 0)
    depasse = installation > PLAFOND_INSTALLATION
    if depasse:
        pts_appart = max(0.0, pts_appart - 5.0)
    morceaux = ", ".join(f"{p} : {niveaux[p]}" for p in niveaux)
    texte_a = (f"Tes niveaux, pièce par pièce : {morceaux}. Chaque "
               f"pièce compte pour sa part des 20 points (MINIMAL "
               f"vaut un tiers, MOYEN deux tiers, MAXIMAL le tout). "
               f"Ton installation coûte {_fmt_montant(installation)} "
               f"sur un plafond de {_fmt_montant(PLAFOND_INSTALLATION)}.")
    if depasse:
        texte_a += (" Tu dépasses le plafond : 5 points en moins, "
                    "parce que le plafond fait partie du défi.")
    appartement = {"points": _arrondir2(pts_appart), "max": 20,
                   "explication": texte_a,
                   "details": {"niveaux": niveaux,
                               "installation": _arrondir2(installation),
                               "plafond_depasse": depasse}}

    # Imprévus (20) : chaque imprévu négatif reçu doit être absorbé,
    # c'est-à-dire le solde revenu positif au plus tard à la fin du
    # mois suivant.
    recus = [m for m in mouvements
             if categoriser_mouvement(m) == "imprevus"
             and float(m.get("montant") or 0) < 0]
    absorb = 0
    for m in recus:
        mois_imp = int(m.get("mois") or 0)
        if mois_imp >= 1 and n > mois_imp:
            if soldes.get(mois_imp + 1, -1) >= 0:
                absorb += 1
        elif mois_imp >= 1 and n == mois_imp:
            if solde_actuel >= 0:
                absorb += 1
    if recus:
        pts_imp = 20.0 * absorb / len(recus)
        cout_total = -sum(float(m.get("montant") or 0) for m in recus)
        texte_i = (f"Tu as reçu {len(recus)} imprévu"
                   f"{'s' if len(recus) > 1 else ''} qui coûte de "
                   f"l'argent, {_fmt_montant(cout_total)} au total. "
                   f"{absorb} a été absorbé : ton solde était revenu "
                   f"positif au plus tard le mois suivant. C'est ça, "
                   f"absorber un imprévu : il te frappe, mais il ne "
                   f"te traîne pas dans le rouge pendant des mois.")
    else:
        pts_imp = 20.0
        texte_i = ("Aucun imprévu payant reçu pour l'instant : le "
                   "plein score, provisoirement. Le jour où un "
                   "imprévu te coûtera de l'argent, il faudra que ton "
                   "solde soit revenu positif au plus tard le mois "
                   "suivant pour garder ces points.")
    imprevus = {"points": _arrondir2(pts_imp), "max": 20,
                "explication": texte_i,
                "details": {"recus": len(recus), "absorbes": absorb}}

    total = _arrondir2(pts_budget + pts_reserve + pts_appart
                       + pts_imp)
    return {"total": total, "budget": budget, "reserve": reserve,
            "appartement": appartement, "imprevus": imprevus,
            "mois_fermes": n}


def classement_groupe(magasin, groupe, profils):
    """Le classement du groupe : les scores de vie, triés, avec le
    contexte du profil de chacun (jamais de dollars bruts)."""
    lignes = []
    for compte in magasin.comptes_du_groupe(groupe):
        dossier = magasin.charger_dossier(compte["identifiant"])
        if dossier is None:
            continue
        try:
            profil = profils[int(compte["cas_numero"])]
        except Exception:
            continue
        score = calculer_score_vie(dossier, profil)
        lignes.append({
            "identifiant": compte["identifiant"],
            "nom": compte.get("nom_affiche") or compte["identifiant"],
            "cas": int(compte["cas_numero"]),
            "revenu_profil": _arrondir2(_paie_profil(profil)),
            "score": score,
        })
    lignes.sort(key=lambda l: (-l["score"]["total"],
                               -l["score"]["reserve"]["points"],
                               l["nom"]))
    for rang, ligne in enumerate(lignes, start=1):
        ligne["rang"] = rang
    return lignes


def podiums_categories(classement):
    """Le premier de chaque composante : plusieurs gagnants, pas un
    seul champion (plan v2, section 7)."""
    podiums = {}
    for cle, nom in (("budget", "Budget le mieux tenu"),
                     ("reserve", "Meilleure réserve"),
                     ("appartement", "Appartement le plus complet"),
                     ("imprevus", "Imprévus le mieux absorbés")):
        if classement:
            meilleur = max(
                classement,
                key=lambda l: l["score"][cle]["points"])
            podiums[nom] = {"nom": meilleur["nom"],
                            "points": meilleur["score"][cle]["points"],
                            "max": meilleur["score"][cle]["max"]}
    return podiums


# --- S6 : le budget prévu confronté au vécu ---

def s6_par_defaut():
    return {"categorie_ecart": "", "pourquoi_ecart": "",
            "changement": ""}


def obtenir_s6(dossier):
    s6 = (dossier or {}).get("s6")
    if not isinstance(s6, dict):
        return s6_par_defaut()
    defaut = s6_par_defaut()
    for cle, valeur in defaut.items():
        s6.setdefault(cle, valeur)
    return s6


def enregistrer_s6(magasin, identifiant, s6):
    dossier = magasin.charger_dossier(identifiant)
    if dossier is None:
        raise ValueError(f"Dossier introuvable : {identifiant}")
    dossier["s6"] = s6
    magasin.sauvegarder_dossier(identifiant, dossier)
    return dossier


def comparer_prevu_vecu(dossier, profil, params=None):
    """Le tableau de la S6 : par catégorie, ce qui était prévu (les
    montants des sections, répétés sur les mois fermés) et ce qui
    s'est vraiment passé (le journal), avec l'écart. Chaque ligne
    porte une explication de l'écart, générée depuis les faits du
    dossier : sections terminées en retard (mois au montant de
    référence), réglages appliqués, décisions et imprévus. Les
    paramètres du groupe servent à compter les mois où le montant
    de référence s'est appliqué."""
    vie = obtenir_vie(dossier)
    mouvements = vie.get("mouvements") or []
    n = int(vie.get("mois_appliques") or 0)
    prevu = prevu_mensuel(dossier)
    paie = _paie_profil(profil)
    reglages = vie.get("reglages") or {}
    mois_serres = sum(1 for r in reglages.values()
                      if r.get("epicerie") == "serrer")
    mois_mieux = sum(1 for r in reglages.values()
                     if r.get("epicerie") == "mieux")
    mois_econo = sum(1 for r in reglages.values()
                     if r.get("electricite") == "econome")
    mois_confort = sum(1 for r in reglages.values()
                       if r.get("electricite") == "confort")
    completions = vie.get("completions") or {}

    def mois_reference(code):
        """Les mois fermés où le montant de référence s'est appliqué
        faute de section terminée avant leur fermeture."""
        completion = completions.get(code) or {}
        if not completion.get("date"):
            return n
        if params is None or n == 0:
            return 0
        date_c = _vers_date(completion["date"])
        compteur = 0
        for mois in range(1, n + 1):
            fermeture = date_fermeture_mois(params, mois)
            if fermeture is None or date_c > fermeture:
                compteur += 1
        return compteur

    lignes = []

    def ligne(cle_cat, nom, prevu_total, pourquoi):
        vecu = sum(float(m.get("montant") or 0) for m in mouvements
                   if categoriser_mouvement(m) == cle_cat)
        lignes.append({
            "categorie": cle_cat, "nom": nom,
            "prevu": _arrondir2(prevu_total), "vecu": _arrondir2(vecu),
            "ecart": _arrondir2(vecu - prevu_total),
            "pourquoi": pourquoi})

    ligne("paie", "Paie", paie * n,
          "Ta paie est celle de ton profil, elle entre au complet "
          "chaque mois. Si le vécu dépasse le prévu, ce sont tes "
          "heures supplémentaires ou tes réglages d'heures.")
    ligne("heures", "Ajustement d'heures (tes réglages)", 0.0,
          "Ce montant n'existe que si tu as réglé tes heures pour le "
          "mois suivant dans Ma vie : travailler plus ou moins, ça "
          "se voit ici, en argent.")
    if n >= 1:
        prevu_loyer = prevu["loyer_total"] + prevu["loyer_part"] * (n - 1)
    else:
        prevu_loyer = 0.0
    ref_s2 = mois_reference("S2")
    ligne("loyer", "Loyer", -prevu_loyer,
          ("Le premier mois, le loyer complet tombe à l'entrée ; "
           "ensuite, ta part de 50 % chaque mois. "
           + (f"Pendant {ref_s2} mois, c'est le loyer de référence "
              f"qui s'est appliqué parce que ta S2 n'était pas "
              f"terminée : la vie n'attend pas." if ref_s2 else
              "Ta S2 était terminée à temps : c'est ton vrai loyer "
              "qui s'est appliqué dès le départ.")))
    ligne("installation", "Installation (une seule fois)",
          -prevu["installation"],
          "Ton ameublement et tes électroménagers, payés une seule "
          "fois au premier mois où ta S3 était terminée. Si le vécu "
          "est à 0, c'est que ta S3 n'était pas terminée avant la "
          "fermeture d'un mois.")
    ref_s5 = mois_reference("S5")
    ligne("epicerie", "Épicerie", -prevu["epicerie_mois_part"] * n,
          ("Ta part de la semaine type de ta S5, répétée chaque mois. "
           + (f"Tu as serré ton épicerie {mois_serres} mois "
              f"(-10 % par tes réglages). " if mois_serres else "")
           + (f"Tu l'as bonifiée {mois_mieux} mois (+10 %). "
              if mois_mieux else "")
           + (f"Pendant {ref_s5} mois, le montant de référence "
              f"s'est appliqué parce que ta S5 n'était pas terminée."
              if ref_s5 else "")))
    ref_s4 = mois_reference("S4")
    ligne("electricite", "Électricité", -prevu["elec_part"] * n,
          ("Ta part de 50 % du calcul Hydro de ta S4. "
           + (f"Réglage économe appliqué {mois_econo} mois (-10 %). "
              if mois_econo else "")
           + (f"Réglage confort appliqué {mois_confort} mois "
              f"(+10 %). " if mois_confort else "")
           + (f"Pendant {ref_s4} mois, le montant de référence "
              f"s'est appliqué parce que ta S4 n'était pas terminée."
              if ref_s4 else "")))
    ligne("internet", "Internet", -prevu["internet_part"] * n,
          "Ta part de 50 % du forfait de ta S4, chaque mois.")
    ligne("cellulaire", "Cellulaire", -prevu["cellulaire"] * n,
          "Ton forfait personnel de ta S4, chaque mois.")
    ligne("assurance", "Assurance habitation",
          -prevu["assurance"] * n,
          "Ton assurance de ta S4, chaque mois.")
    ligne("transport", "Transport", -prevu["transport"] * n,
          "Le coût mensuel du transport de ta S5, chaque mois.")
    decisions = vie.get("decisions") or {}
    nb_defaut = sum(1 for d in decisions.values() if d.get("defaut"))
    ligne("decisions", "Tes décisions", 0.0,
          ("Aucun montant prévu : les décisions arrivent avec la "
           "vie. "
           + (f"{nb_defaut} décision{'s' if nb_defaut > 1 else ''} "
              f"a été appliquée par défaut parce que tu n'avais pas "
              f"tranché avant la fermeture : c'est l'option "
              f"souvent la plus chère qui s'applique toute seule."
              if nb_defaut else
              "Tu as tranché chacune de tes décisions toi-même.")))
    ligne("imprevus", "Imprévus reçus", 0.0,
          "Par définition, un imprévu ne se prévoit pas. Ce qui "
          "compte, c'est de l'absorber sans rester dans le rouge.")
    ligne("evenements", "Événements de classe", 0.0,
          "Les événements que ton enseignant a appliqués au groupe.")
    ligne("corrections", "Corrections de ton enseignant", 0.0,
          "Les ajustements que ton enseignant a faits à ton compte, "
          "avec son motif dans ton journal.")
    ligne("autres", "Autres mouvements", 0.0,
          "Ce qui ne rentre pas dans les autres catégories, par "
          "exemple le remboursement de la part avancée à ton coloc.")
    lignes = [l for l in lignes
              if l["prevu"] != 0 or l["vecu"] != 0
              or l["categorie"] in ("decisions", "imprevus")]
    total_prevu = _arrondir2(sum(l["prevu"] for l in lignes))
    total_vecu = _arrondir2(sum(l["vecu"] for l in lignes))
    return {"mois": n, "lignes": lignes, "total_prevu": total_prevu,
            "total_vecu": total_vecu,
            "ecart_total": _arrondir2(total_vecu - total_prevu)}


# --- S7 : la réflexion, le mot de la fin ---

def s7_par_defaut():
    return {"appris": "", "decision_couteuse": "", "conseil": ""}


def obtenir_s7(dossier):
    s7 = (dossier or {}).get("s7")
    if not isinstance(s7, dict):
        return s7_par_defaut()
    defaut = s7_par_defaut()
    for cle, valeur in defaut.items():
        s7.setdefault(cle, valeur)
    return s7


def enregistrer_s7(magasin, identifiant, s7):
    dossier = magasin.charger_dossier(identifiant)
    if dossier is None:
        raise ValueError(f"Dossier introuvable : {identifiant}")
    dossier["s7"] = s7
    magasin.sauvegarder_dossier(identifiant, dossier)
    return dossier


def s7_manquants(s7):
    manques = []
    if not (s7.get("appris") or "").strip():
        manques.append("ce que l'argent t'a appris")
    if not (s7.get("decision_couteuse") or "").strip():
        manques.append("ta décision la plus coûteuse")
    if not (s7.get("conseil") or "").strip():
        manques.append("ton conseil à ton moi de mars")
    return manques

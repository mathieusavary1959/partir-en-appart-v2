"""Partir en appart! v2 : application Streamlit (phase P1).

Squelette : inscription avec mot de passe, connexion, accueil « Mon appart »
fidèle à la maquette v3 (accueil simplifié), section S1 en lecture et
progression sauvegardée. Le calendrier de vie, la console du prof et les
sections S2 à S7 arrivent aux phases suivantes (voir RAPPORT_P1.md).
La couche de données vit dans donnees.py (magasin mémoire ou Supabase REST).
"""
import streamlit as st

import donnees

st.set_page_config(page_title="Partir en appart!", layout="wide")

# --------------------------------------------------------------------- style
# Palette 3 validée : fond presque noir, un seul accent jaune moutarde.
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Work+Sans:wght@400;600;700;800&display=swap');
:root{
  --fond:#0E0D0B; --panneau:#171512; --panneau2:#1E1B16; --bord:#35312A;
  --texte:#F5F2EA; --doux:#A79E8D; --accent:#E3B505; --accent-texte:#1A1402;
}
.stApp{ background:var(--fond); color:var(--texte); font-family:"Work Sans",sans-serif; }
.block-container{ max-width:1180px; padding-top:1.4rem; }
[data-testid="stHeader"]{ background:transparent; }
h1,h2,h3{ color:var(--texte); font-family:"Work Sans",sans-serif; }
p, li, label{ color:var(--texte); }

/* Widgets Streamlit dans la palette */
.stButton > button{
  border-radius:999px; border:1px solid var(--bord); background:var(--panneau);
  color:var(--texte); font-weight:700; padding:.45rem 1.1rem;
}
.stButton > button:hover{ border-color:var(--accent); color:var(--accent); }
.stButton > button[kind="primary"]{
  background:var(--accent); border-color:var(--accent); color:var(--accent-texte);
}
.stButton > button[kind="primary"]:hover{ color:var(--accent-texte); opacity:.92; }
.stButton > button:disabled{ opacity:.45; }
.stTextInput input{
  background:var(--panneau) !important; color:var(--texte) !important;
  border:1px solid var(--bord) !important; border-radius:10px;
}
[data-baseweb="select"] > div{
  background:var(--panneau); border-color:var(--bord); color:var(--texte);
  border-radius:10px;
}
.stCheckbox label span, .stRadio label span{ color:var(--texte); }

/* Blocs repris de la maquette v3 */
.marque{ font-family:"Bebas Neue",sans-serif; font-size:54px; letter-spacing:.03em; line-height:.95; }
.marque span{ color:var(--accent); }
.sous{ color:var(--doux); font-size:14px; margin-top:4px; }
.puces{ display:flex; gap:10px; flex-wrap:wrap; margin-top:12px; }
.puce{ background:var(--panneau); border:1px solid var(--bord); border-radius:999px;
  padding:7px 14px; font-size:13.5px; font-weight:600; }
.puce b{ color:var(--accent); }
.bandeau{ display:grid; grid-template-columns:1.2fr 1fr; gap:16px; margin-top:16px; }
.solde{ background:linear-gradient(180deg,var(--panneau2),var(--panneau));
  border:1px solid var(--bord); border-radius:16px; padding:22px 24px;
  box-shadow:0 12px 34px -20px rgba(227,181,5,.5); }
.solde .etiquette, .prochain .etiquette{ color:var(--doux); font-size:12px; font-weight:700;
  text-transform:uppercase; letter-spacing:.1em; }
.solde .montant{ font-size:56px; font-weight:800; margin-top:4px; font-variant-numeric:tabular-nums; }
.solde .precision, .prochain .precision{ color:var(--doux); font-size:13.5px; margin-top:5px; line-height:1.45; }
.prochain{ background:var(--panneau); border:1px solid var(--bord); border-radius:16px;
  padding:22px 24px; display:flex; flex-direction:column; justify-content:center; }
.prochain .quoi{ font-size:21px; font-weight:800; margin-top:6px; line-height:1.3; }
.prochain .quoi b{ color:var(--accent); }
.carte{ background:var(--panneau); border:1px solid var(--bord); border-radius:16px;
  padding:20px; margin-top:16px; }
.carte h2{ font-family:"Bebas Neue",sans-serif; font-weight:400; font-size:27px;
  letter-spacing:.05em; margin:0; }
.carte .aide{ color:var(--doux); font-size:13.5px; margin:3px 0 14px; }
.plan{ display:grid; grid-template-columns:1fr 1fr 1fr; gap:10px; }
.piece{ border:1.5px solid var(--bord); border-radius:12px; padding:14px 15px;
  background:var(--panneau2); min-height:104px; position:relative; }
.piece .nom{ font-family:"Bebas Neue",sans-serif; font-size:22px; letter-spacing:.05em; padding-right:96px; }
.piece .contenu{ color:var(--doux); font-size:13px; line-height:1.5; margin-top:5px; }
.etat{ position:absolute; top:12px; right:12px; font-size:10.5px; font-weight:800;
  letter-spacing:.07em; padding:4px 9px; border-radius:999px;
  text-transform:uppercase; white-space:nowrap; }
.etat.complet{ background:var(--accent); color:var(--accent-texte); }
.etat.partiel{ border:1.5px solid var(--accent); color:var(--accent); }
.etat.afaire{ border:1.5px solid var(--bord); color:var(--doux); }
.piece.remplie{ border-color:rgba(227,181,5,.55); box-shadow:inset 0 0 0 1px rgba(227,181,5,.22); }
.action{ margin-top:16px; background:var(--accent); color:var(--accent-texte);
  border-radius:16px; padding:20px 24px; }
.action .quoi{ font-family:"Bebas Neue",sans-serif; font-size:27px; letter-spacing:.04em; }
.action .aide{ font-size:13.5px; font-weight:600; margin-top:2px; }
.etapes{ display:grid; grid-template-columns:repeat(7,1fr); gap:10px; margin-top:16px; }
.etape{ background:var(--panneau); border:1px solid var(--bord); border-radius:12px; padding:12px 13px; }
.etape .code{ font-family:"Bebas Neue",sans-serif; font-size:19px; letter-spacing:.05em; }
.etape .nom{ color:var(--doux); font-size:12px; line-height:1.35; min-height:32px; }
.etape .mot{ font-size:11px; font-weight:800; text-transform:uppercase; letter-spacing:.06em; margin-top:6px; color:var(--doux); }
.etape.fait .mot{ color:var(--accent); }
.etape.encours{ border-color:var(--accent); }
.etape.encours .mot{ color:var(--accent); }
.ligne{ display:flex; justify-content:space-between; gap:16px; padding:8px 0;
  border-bottom:1px solid var(--bord); font-size:15px; }
.ligne .valeur{ font-weight:700; font-variant-numeric:tabular-nums; text-align:right; }
.ligne.total .valeur{ color:var(--accent); }
.bloc-accent{ border-left:4px solid var(--accent); }
footer-note{ }
.pied{ color:var(--doux); font-size:12.5px; margin-top:22px; text-align:center; line-height:1.6; }
@media (max-width:980px){
  .bandeau{ grid-template-columns:1fr; }
  .etapes{ grid-template-columns:repeat(3,1fr); }
  .plan{ grid-template-columns:1fr 1fr; }
}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# ------------------------------------------------------- base de données
@st.cache_resource
def init_db():
    """Crée les tables appart2_ si la connexion Postgres est configurée.

    Même patron que la simulation boursière. Sans secrets (test local),
    l'étape est sautée et le magasin mémoire prend le relais.
    """
    try:
        from sqlalchemy import text
        conn = st.connection("postgres", type="sql")
        with conn.session as session:
            for instruction in donnees.SQL_CREATION:
                session.execute(text(instruction))
            session.commit()
    except Exception:
        pass


@st.cache_resource
def obtenir_magasin():
    config = {}
    try:
        config = {
            "APPART2_SUPABASE_URL": st.secrets.get("APPART2_SUPABASE_URL"),
            "APPART2_SUPABASE_KEY": st.secrets.get("APPART2_SUPABASE_KEY"),
        }
    except Exception:
        config = {}
    return donnees.creer_magasin(config)


init_db()
MAGASIN = obtenir_magasin()
PROFILS = {int(p["numero"]): p for p in donnees.charger_profils()}

# ------------------------------------------------------------------- utilitaires
def fmt_montant(valeur):
    """2 100,00 $ : format français simple."""
    return f"{float(valeur):,.2f}".replace(",", " ").replace(".", ",") + " $"


def aller(page):
    st.session_state["page"] = page
    st.rerun()


def deconnecter():
    for cle in ("identifiant", "compte", "page"):
        st.session_state.pop(cle, None)
    st.rerun()


def entete_marque(sous_titre):
    st.markdown(
        f"<div class='marque'>PARTIR EN <span>APPART!</span></div>"
        f"<div class='sous'>{sous_titre}</div>",
        unsafe_allow_html=True)


AIDES_ETAPES = {
    "S1": "Lis ton profil en entier : tes revenus, ton atout, ton handicap et ton coloc.",
    "S2": "Compare 3 annonces de 4 et demi à Trois-Rivières.",
    "S3": "Meuble tes six pièces sans dépasser le plafond de 3 500 $.",
    "S4": "Choisis tes forfaits et fais ton calcul d'électricité.",
    "S5": "Planifie ton transport et ta semaine d'épicerie.",
    "S6": "Écris ton budget prévu. Le calendrier va le tester pour vrai.",
    "S7": "Raconte ce que la vie en appart t'a appris.",
}

# ------------------------------------------------------------- écrans publics
def ecran_acces():
    entete_marque("Ton premier appartement, pour vrai. Trois-Rivières, en colocation.")
    ecran = st.radio("Que veux-tu faire?",
                     ["Je me connecte", "Je m'inscris (première fois)"],
                     horizontal=True, key="ecran_acces")
    if ecran == "Je m'inscris (première fois)":
        formulaire_inscription()
    else:
        formulaire_connexion()


def formulaire_inscription():
    st.subheader("Inscription")
    st.write("Inscris-toi avec le cas que tu as pigé en classe. "
             "Choisis un mot de passe que tu vas retenir : sans lui, "
             "tu ne pourras pas rouvrir ton dossier.")
    prenom = st.text_input("Ton prénom", key="insc_prenom")
    nom = st.text_input("Ton nom de famille", key="insc_nom")
    groupe = st.selectbox("Ton groupe", donnees.GROUPES, key="insc_groupe")
    cas = st.selectbox("Le numéro de ton cas pigé en classe",
                       list(range(1, 31)), key="insc_cas")
    profil = PROFILS[int(cas)]
    st.markdown(
        "<div class='carte'><h2>Ton cas : " + profil["prenom"] + "</h2>"
        "<div class='aide'>" + profil["situation_detail"] + "</div>"
        "<div>C'est le cas numéro " + str(profil["numero"]) +
        ". Si ce n'est pas ton cas, change le numéro ci-dessus.</div></div>",
        unsafe_allow_html=True)
    confirme = st.checkbox("C'est bien mon cas.", key="insc_confirme")
    mot_de_passe = st.text_input(
        "Choisis un mot de passe (au moins 6 caractères)",
        type="password", key="insc_mdp", autocomplete="new-password")
    if mot_de_passe:
        st.caption(f"{len(mot_de_passe)} caractères saisis. "
                   "Ne dis ton mot de passe à personne.")
    else:
        st.caption("Ne dis ton mot de passe à personne.")
    confirmation = st.text_input(
        "Écris ton mot de passe une deuxième fois",
        type="password", key="insc_mdp2", autocomplete="new-password")
    if st.button("Créer mon compte", type="primary", disabled=not confirme):
        res = donnees.inscrire(MAGASIN, prenom, nom, groupe, cas,
                               mot_de_passe, confirmation)
        if res["ok"]:
            st.session_state["identifiant"] = res["identifiant"]
            st.session_state["page"] = "accueil"
            st.success(res["message"])
            st.rerun()
        else:
            st.error(res["message"])


def formulaire_connexion():
    st.subheader("Connexion")
    st.write("Entre ton nom et ton mot de passe pour rouvrir ton dossier, "
             "là où tu l'avais laissé.")
    prenom = st.text_input("Ton prénom", key="conn_prenom")
    nom = st.text_input("Ton nom de famille", key="conn_nom")
    mot_de_passe = st.text_input("Ton mot de passe",
                                 type="password", key="conn_mdp")
    if st.button("Ouvrir mon dossier", type="primary"):
        res = donnees.connecter(MAGASIN, prenom, nom, mot_de_passe)
        if res["ok"]:
            st.session_state["identifiant"] = res["compte"]["identifiant"]
            st.session_state["page"] = "accueil"
            st.success(res["message"])
            st.rerun()
        else:
            st.error(res["message"])


# ------------------------------------------------------------- écrans élève
def barre_navigation(page):
    onglets = [("accueil", "Accueil"), ("vie", "Ma vie"), ("score", "Mon score"),
               ("imprevus", "Mes imprévus"), ("sections", "Mes sections S1 à S7")]
    actif = "sections" if page == "s1" else page
    cols = st.columns(len(onglets))
    for col, (code, nom) in zip(cols, onglets):
        with col:
            if st.button(nom, key=f"nav_{code}",
                         type="primary" if code == actif else "secondary",
                         use_container_width=True):
                aller(code)


def entete_eleve(compte, profil):
    col_titre, col_bouton = st.columns([5, 1])
    with col_titre:
        entete_marque("Ton premier appartement, pour vrai. "
                      f"Trois-Rivières, en colocation avec {profil['coloc']['prenom']}.")
        st.markdown(
            "<div class='puces'>"
            f"<div class='puce'>{compte['nom_affiche']} · <b>Cas {compte['cas_numero']} : {profil['prenom']}</b></div>"
            f"<div class='puce'>Groupe {compte['groupe']}</div>"
            "<div class='puce'>Mois de vie : <b>pas encore commencé</b></div>"
            "</div>",
            unsafe_allow_html=True)
    with col_bouton:
        if st.button("Me déconnecter"):
            deconnecter()


def html_pieces(profil, dossier):
    coloc = profil["coloc"]
    etats = {"a_faire": ("afaire", "À faire"),
             "partielle": ("partiel", "Partielle"),
             "complete": ("complet", "Complète")}
    contenus = {
        "Ma chambre": "Ta chambre à toi. Rien pour le moment : tu la meubleras dans la section S3.",
        "Cuisine": f"Pièce commune avec {coloc['prenom']}. Rien pour le moment : tu la meubleras dans la section S3.",
        "Salon": f"Pièce commune avec {coloc['prenom']}. Rien pour le moment : tu le meubleras dans la section S3.",
        "Salle de bain": f"Pièce commune avec {coloc['prenom']}. Rien pour le moment : tu la meubleras dans la section S3.",
        "Entrée et rangement": f"Pièce commune avec {coloc['prenom']}. Rien pour le moment : section S3.",
    }
    morceaux = []
    for piece in donnees.PIECES:
        if piece == "La chambre de mon coloc":
            classe_etat, mot = "afaire", "Coloc"
            contenu = (f"{coloc['prenom']} apporte ses meubles, ça ne te coûte rien. "
                       f"{coloc['handicap']}")
            remplie = ""
        else:
            etat_piece = dossier.get("pieces", {}).get(piece, "a_faire")
            classe_etat, mot = etats.get(etat_piece, etats["a_faire"])
            contenu = contenus[piece]
            remplie = " remplie" if etat_piece == "complete" else ""
        morceaux.append(
            f"<div class='piece{remplie}'><div class='nom'>{piece}</div>"
            f"<span class='etat {classe_etat}'>{mot}</span>"
            f"<div class='contenu'>{contenu}</div></div>")
    return "<div class='plan'>" + "".join(morceaux) + "</div>"


def html_pastilles(dossier):
    courante = donnees.section_courante(dossier)
    progression = dossier.get("progression", {})
    morceaux = []
    for code, nom in donnees.SECTIONS:
        etat = progression.get(code, "a_faire")
        if etat == "fait":
            classe, mot = "etape fait", "Fait"
        elif code == courante:
            classe, mot = "etape encours", "En cours"
        else:
            classe, mot = "etape", "À faire"
        morceaux.append(
            f"<div class='{classe}'><div class='code'>{code}</div>"
            f"<div class='nom'>{nom}</div><div class='mot'>{mot}</div></div>")
    return "<div class='etapes'>" + "".join(morceaux) + "</div>"


def page_accueil(compte, dossier, profil):
    solde = float(dossier.get("solde", profil["epargne_depart"]))
    st.markdown(
        "<div class='bandeau'>"
        "<section class='solde'><div class='etiquette'>Il me reste</div>"
        f"<div class='montant'>{fmt_montant(solde)}</div>"
        "<div class='precision'>C'est ton épargne de départ. Elle bougera quand "
        "le calendrier de vie commencera.</div></section>"
        "<section class='prochain'><div class='etiquette'>Prochain mouvement</div>"
        "<div class='quoi'>Le calendrier de vie n'a <b>pas encore commencé</b></div>"
        "<div class='precision'>Ton enseignant va le lancer en classe. "
        "En attendant, lis ton profil dans la section S1.</div></section>"
        "</div>",
        unsafe_allow_html=True)

    st.markdown(
        "<section class='carte'><h2>Mon appartement</h2>"
        "<div class='aide'>Tes six pièces. Une pièce se remplit quand tu la "
        "meubles, dans la section S3.</div>"
        + html_pieces(profil, dossier) + "</section>",
        unsafe_allow_html=True)

    courante = donnees.section_courante(dossier)
    if courante:
        nom = donnees.nom_section(courante)
        st.markdown(
            "<section class='action'>"
            f"<div class='quoi'>Ma prochaine étape : {nom[0].lower() + nom[1:]} ({courante})</div>"
            f"<div class='aide'>{AIDES_ETAPES[courante]}</div></section>",
            unsafe_allow_html=True)
        if st.button(f"Aller à la section {courante}", type="primary"):
            aller("s1" if courante == "S1" else "sections")
    else:
        st.success("Tu as terminé toutes tes sections. Beau travail!")

    st.markdown(html_pastilles(dossier), unsafe_allow_html=True)


def rang(label, valeur):
    return (f"<div class='ligne'><div>{label}</div>"
            f"<div class='valeur'>{valeur}</div></div>")


def page_s1(compte, dossier, profil):
    if st.button("Retour à l'accueil"):
        aller("accueil")
    coloc = profil["coloc"]
    total_mois = (float(profil["revenu_net_mensuel"])
                  + float(profil["aide_parents_mensuelle"])
                  + float(profil["autre_revenu_mensuel"]))

    st.markdown(
        "<section class='carte'><h2>S1 : Ton cas, " + profil["prenom"] + "</h2>"
        "<div class='aide'>Cas numéro " + str(profil["numero"]) +
        ", pigé en classe. Lis tout : c'est ta vie pour les prochains mois.</div>"
        f"<div>{profil['situation_detail']}</div></section>",
        unsafe_allow_html=True)

    lignes = [
        rang("Ton travail", profil["employeur"]),
        rang("Ton taux horaire", fmt_montant(profil["taux_horaire"]) + " de l'heure"),
        rang("Tes heures de travail", f"{profil['heures_semaine']} h par semaine"),
        rang("Ton revenu brut par mois", fmt_montant(profil["revenu_brut_mensuel"])),
        rang("Ton revenu net par mois", fmt_montant(profil["revenu_net_mensuel"])),
        rang("L'aide de tes parents par mois", fmt_montant(profil["aide_parents_mensuelle"])),
        rang("Ton autre revenu par mois", fmt_montant(profil["autre_revenu_mensuel"])),
        "<div class='ligne total'><div>Total qui entre chaque mois</div>"
        f"<div class='valeur'>{fmt_montant(total_mois)}</div></div>",
        rang("Ton épargne de départ", fmt_montant(profil["epargne_depart"])),
        rang("Ta ville d'origine", profil["ville_origine"]),
        rang("Ton transport", profil["transport"]),
    ]
    if profil.get("ecole"):
        lignes.insert(0, rang("Ton école", profil["ecole"]))
    if profil.get("programme"):
        lignes.insert(1, rang("Ton programme", profil["programme"]))
    st.markdown(
        "<section class='carte'><h2>Ton argent et ton départ</h2>"
        + "".join(lignes) + "</section>",
        unsafe_allow_html=True)

    st.markdown(
        "<section class='carte bloc-accent'><h2>Ton atout</h2>"
        f"<div>{profil['atout']}</div></section>",
        unsafe_allow_html=True)
    st.markdown(
        "<section class='carte bloc-accent'><h2>Ton handicap</h2>"
        f"<div>{profil['handicap']}</div></section>",
        unsafe_allow_html=True)

    lignes_coloc = [
        rang("Son travail", coloc["occupation"]),
        rang("Son revenu par mois, environ", fmt_montant(coloc["revenu_mensuel_approx"])),
        rang("Les coûts partagés", "50 % chacun, toujours"),
    ]
    st.markdown(
        "<section class='carte'><h2>Ton coloc : " + coloc["prenom"] + "</h2>"
        f"<div class='aide'>{coloc['description']}</div>"
        + "".join(lignes_coloc)
        + f"<div style='margin-top:10px'>Son handicap : {coloc['handicap']}</div></section>",
        unsafe_allow_html=True)

    deja_fait = dossier.get("progression", {}).get("S1") == "fait"
    if deja_fait:
        st.success("Tu as déjà lu et compris ton profil. La S1 est terminée.")
    elif st.button("J'ai lu et je comprends mon profil", type="primary"):
        donnees.definir_progression(MAGASIN, compte["identifiant"], "S1", "fait")
        st.success("S1 terminée. Bienvenue dans ton appart!")
        aller("accueil")


def page_sections(compte, dossier, profil):
    st.markdown("<section class='carte'><h2>Mes sections</h2>"
                "<div class='aide'>Ton travail, section par section. "
                "La S1 est prête ; les autres arrivent plus tard.</div></section>",
                unsafe_allow_html=True)
    progression = dossier.get("progression", {})
    courante = donnees.section_courante(dossier)
    for code, nom in donnees.SECTIONS:
        etat = progression.get(code, "a_faire")
        mot = "Fait" if etat == "fait" else ("En cours" if code == courante else "À faire")
        col_texte, col_bouton = st.columns([4, 1])
        with col_texte:
            st.markdown(f"**{code} : {nom}** ({mot})")
            st.caption(AIDES_ETAPES[code])
        with col_bouton:
            if code == "S1":
                if st.button("Ouvrir la S1", key="ouvrir_s1"):
                    aller("s1")
            else:
                st.caption("Arrive plus tard")


def page_attente(titre, texte, phase):
    st.markdown(
        f"<section class='carte'><h2>{titre}</h2><div>{texte}</div></section>",
        unsafe_allow_html=True)
    st.caption(f"Page en construction ({phase}).")


# ----------------------------------------------------------------------- main
def main():
    if not st.session_state.get("identifiant"):
        ecran_acces()
        st.markdown(
            "<div class='pied'>Partir en appart! : un projet d'éducation "
            "financière. Trois-Rivières, en colocation.</div>",
            unsafe_allow_html=True)
        return

    identifiant = st.session_state["identifiant"]
    compte = MAGASIN.compte_par_identifiant(identifiant)
    dossier = MAGASIN.charger_dossier(identifiant)
    if compte is None or dossier is None:
        deconnecter()
        return
    profil = PROFILS[int(compte["cas_numero"])]

    entete_eleve(compte, profil)
    page = st.session_state.get("page", "accueil")
    barre_navigation(page)

    if page == "accueil":
        page_accueil(compte, dossier, profil)
    elif page == "s1":
        page_s1(compte, dossier, profil)
    elif page == "sections":
        page_sections(compte, dossier, profil)
    elif page == "vie":
        page_attente(
            "Ma vie",
            "Ici, tu verras le calendrier de ta vie en appart : ta paie, "
            "ton loyer, tes factures, mois après mois. Le calendrier "
            "commence quand ton enseignant le lance en classe.",
            "phase P3")
    elif page == "score":
        page_attente(
            "Mon score",
            "Ici, tu verras ton score de vie : comment tu tiens ton budget, "
            "ta réserve, ton appartement et les imprévus. Le score est "
            "toujours comparé à ton profil, jamais à l'argent des autres.",
            "phase P4")
    elif page == "imprevus":
        page_attente(
            "Mes imprévus",
            "C'est ici que tu inscriras le numéro de ta carte d'imprévu "
            "quand tu en pigeras une en classe, et que tu verras les "
            "surprises de ton enseignant.",
            "phase P3")

    if MAGASIN.mode == "memoire":
        st.markdown(
            "<div class='pied'>Mode test local : les données sont gardées "
            "en mémoire seulement, le temps de la session.</div>",
            unsafe_allow_html=True)


main()

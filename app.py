"""Partir en appart! v2 : application Streamlit (phase P1, univers figé).

Univers figé le 28 octobre 2026 : « la porte de frigo » (voir la charte
files/charte-univers-frigo.md du dossier du projet et la maquette v7).
Inscription avec mot de passe, connexion, accueil en porte de frigo,
section S1 en lecture, section S2 (les 3 annonces comparées, le choix,
la justification, la capture) et section S3 (le jour de l'emménagement :
les boîtes de déménagement par pièce, chaque achat prouvé par son lien,
la facture d'électroménagers, le reçu de caisse sous le plafond de
3 500 $) fonctionnelles, progression sauvegardée. La session survit au
rafraîchissement de la page grâce à un jeton dans un cookie du
navigateur, révoqué à la déconnexion et à la réinitialisation du mot
de passe.
Le calendrier de vie, la console du prof et les sections S4 à S7
arrivent aux phases suivantes.
La couche de données vit dans donnees.py (magasin mémoire ou Supabase REST).
"""
import datetime
import html

import streamlit as st

import donnees

try:
    import extra_streamlit_components as stx
except Exception:
    stx = None

# Garde-fou de déploiement : si le processus en ligne garde en mémoire une
# ancienne version du module donnees (rechargement partiel de Streamlit
# Cloud), on force son rechargement avant d'aller plus loin.
if not hasattr(donnees, "PIECE_COLOC") or not hasattr(donnees, "nouveau_jeton_session") \
        or not hasattr(donnees, "calculer_electricite"):
    import importlib
    importlib.reload(donnees)

st.set_page_config(page_title="Partir en appart!", layout="wide")

# --------------------------------------------------------------------- style
# Univers « la porte de frigo » : mur de cuisine sombre, porte émaillée,
# papiers épinglés. Bebas Neue (structure), Work Sans (interface),
# Caveat (tout ce qui est « écrit à la main » dans l'univers).
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Caveat:wght@600;700&family=Special+Elite&family=Work+Sans:wght@400;500;600;700;800&display=swap');
:root{
  --mur:#1C1F27; --texte:#F5F2EA; --gris:#A7AEC2;
  --jaune:#FFD23F; --jaune-texte:#1C1F27; --encre:#2A2620; --crayon:#D93A2B;
  --vert:#1E9E4A;
}
.stApp{
  background-color:var(--mur);
  background-image:linear-gradient(rgba(255,255,255,.035) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,.035) 1px,transparent 1px);
  background-size:118px 118px;
  color:var(--texte); font-family:"Work Sans",sans-serif;
}
.block-container{ max-width:1180px; padding-top:1.2rem; }
[data-testid="stHeader"]{ background:transparent; }
h1,h2,h3{ color:var(--texte); }
p, li, label{ color:var(--texte); }
.stCaption, [data-testid="stCaptionContainer"] p{ color:var(--gris) !important; }

/* Widgets : les formulaires sont des papiers sur le mur */
.stTextInput input{
  background:#FFFFFF !important; color:var(--encre) !important;
  border:2px solid #CFC9B6 !important; border-radius:8px;
  box-shadow:0 6px 14px rgba(0,0,0,.35);
}
[data-baseweb="select"] > div{
  background:#FFFFFF; border:2px solid #CFC9B6; color:var(--encre); border-radius:8px;
  box-shadow:0 6px 14px rgba(0,0,0,.35);
}
[data-baseweb="select"] span{ color:var(--encre) !important; }
.stButton > button{
  border-radius:999px; border:1.5px solid #454B5C; background:#2B2F3A;
  color:var(--texte); font-weight:700; padding:.45rem 1.1rem;
}
.stButton > button:hover{ border-color:var(--jaune); color:var(--jaune); }
.stButton > button[kind="primary"]{
  background:var(--jaune); border-color:var(--jaune); color:var(--jaune-texte);
  box-shadow:0 10px 24px rgba(255,210,63,.25);
}
.stButton > button[kind="primary"]:hover{ color:var(--jaune-texte); opacity:.93; }
.stButton > button:disabled{ opacity:.45; }
.stCheckbox label span, .stRadio label span{ color:var(--texte); }

/* La lampe suspendue et son cône de lumière */
.stApp::before{ content:""; position:fixed; top:0; left:50%; transform:translateX(-50%); width:980px; height:720px; z-index:0;
  background:linear-gradient(180deg,rgba(255,240,200,.16),rgba(255,240,200,.04) 55%,transparent 78%);
  clip-path:polygon(43% 0,57% 0,100% 100%,0 100%); pointer-events:none; }
.block-container{ position:relative; z-index:1; }
.pf-lampe{ text-align:center; height:74px; }
.pf-lampe .fil{ width:3px; height:28px; background:#0E0F13; margin:0 auto; }
.pf-lampe .abat{ width:138px; height:46px; margin:-2px auto 0; background:linear-gradient(180deg,#2E3442,#1A1E28);
  clip-path:polygon(32% 0,68% 0,100% 100%,0 100%); }
.pf-lampe .ampoule{ width:24px; height:24px; border-radius:50%; margin:-14px auto 0;
  background:radial-gradient(circle at 50% 42%,#FFF6D8,#FFD98A 60%,rgba(255,217,138,0));
  box-shadow:0 0 40px 18px rgba(255,224,150,.32); }
/* Les barres de boutons du haut (navigation et choix d'accès) :
   une piste sombre, des pastilles ; l'actif est blanc à texte foncé. */
.st-key-nav_bar [data-testid="stHorizontalBlock"], .st-key-acces_bar [data-testid="stHorizontalBlock"]{
  background:#2B2F3A; border:1.5px solid #454B5C; border-radius:999px; padding:6px; gap:6px; align-items:center; }
.st-key-nav_bar .stButton > button, .st-key-acces_bar .stButton > button{
  width:100%; border:none !important; background:transparent; color:#C9CEDA; border-radius:999px;
  font-family:"Bebas Neue",sans-serif; font-size:17px; letter-spacing:.07em; padding:6px 4px; box-shadow:none; }
.st-key-nav_bar .stButton > button:hover, .st-key-acces_bar .stButton > button:hover{ color:var(--texte); }
.st-key-nav_bar .stButton > button[kind="primary"], .st-key-acces_bar .stButton > button[kind="primary"]{
  background:var(--texte); color:#1C1F27; box-shadow:none; }
.st-key-nav_bar .stButton > button[kind="primary"]:hover, .st-key-acces_bar .stButton > button[kind="primary"]:hover{ color:#1C1F27; opacity:.92; }
.st-key-nav_bar .stButton > button p, .st-key-acces_bar .stButton > button p{
  font-family:inherit; font-size:inherit; letter-spacing:inherit; color:inherit; }
/* Le mur : titre et identité */
.marque{ font-family:"Bebas Neue",sans-serif; font-size:56px; letter-spacing:.03em; line-height:.95; text-shadow:0 4px 0 rgba(0,0,0,.4); }
.marque span{ color:var(--jaune); }
.sous{ color:var(--gris); font-size:14.5px; margin-top:4px; }
.puces{ display:flex; gap:10px; flex-wrap:wrap; margin-top:12px; }
.puce{ background:#2B2F3A; border:1.5px solid #454B5C; border-radius:999px;
  padding:7px 14px; font-size:13.5px; font-weight:600; color:var(--texte); }
.puce b{ color:var(--jaune); }

/* Feuilles de papier (écrans de travail : S1, sections, attentes) */
.carte{ background:#FFFFFF; color:var(--encre); border-radius:4px;
  padding:22px 24px; margin-top:16px; position:relative;
  box-shadow:0 14px 30px rgba(0,0,0,.45); }
.carte h2{ font-family:"Bebas Neue",sans-serif; font-weight:400; font-size:27px;
  letter-spacing:.05em; margin:0; color:var(--encre); }
.carte p, .carte div, .carte li{ color:var(--encre); }
.carte .aide{ color:#4A453C; font-size:13.5px; margin:3px 0 14px; }
.ligne{ display:flex; justify-content:space-between; gap:16px; padding:8px 0;
  border-bottom:1px dashed #C9C2AE; font-size:15px; color:var(--encre); }
.ligne .valeur{ font-weight:700; font-variant-numeric:tabular-nums; text-align:right; }
.ligne.total .valeur{ color:var(--crayon); }
.bloc-accent{ border-left:5px solid var(--jaune); }

/* Le bouton étape, avec le reflet brillant de la maquette */
.action{ margin-top:18px; background:var(--jaune); color:var(--jaune-texte);
  border-radius:14px; padding:18px 24px; position:relative; overflow:hidden;
  box-shadow:0 14px 34px rgba(255,210,63,.22); }
.action::after{ content:""; position:absolute; top:0; bottom:0; width:26%; left:-30%;
  background:linear-gradient(100deg,transparent,rgba(255,255,255,.55),transparent);
  animation:pfbrille 3.4s ease-in-out infinite; }
@keyframes pfbrille{ 0%{left:-30%;} 60%,100%{left:110%;} }
.action .quoi{ font-family:"Bebas Neue",sans-serif; font-size:27px; letter-spacing:.04em; }
.action .aide{ font-size:13.5px; font-weight:600; margin-top:2px; }

.pied{ color:#6E7484; font-size:12.5px; margin-top:22px; text-align:center; line-height:1.6; }
/* L'étape du bas : UN seul élément jaune, le bouton lui-même, pleine largeur. */
.etape-titre{ font-family:"Bebas Neue",sans-serif; font-size:19px; letter-spacing:.2em; color:var(--jaune); margin-top:22px; }
.etape-aide{ color:var(--gris); font-size:13.5px; margin-top:2px; }
.st-key-etape_bar .stButton > button{
  position:relative; overflow:hidden; width:100%; border:none; border-radius:14px;
  background:var(--jaune); color:var(--jaune-texte);
  font-family:"Bebas Neue",sans-serif; font-size:28px; letter-spacing:.04em;
  padding:15px 24px; box-shadow:0 14px 34px rgba(255,210,63,.22); }
.st-key-etape_bar .stButton > button:hover{ color:var(--jaune-texte); opacity:.94; }
.st-key-etape_bar .stButton > button::after{
  content:""; position:absolute; top:0; bottom:0; width:26%; left:-30%;
  background:linear-gradient(100deg,transparent,rgba(255,255,255,.55),transparent);
  animation:pfbrille 3.4s ease-in-out infinite; }
.st-key-etape_bar .stButton > button p{ font-family:inherit; font-size:inherit; letter-spacing:inherit; color:inherit; }

/* ============ LA PORTE DE FRIGO (accueil et bandeau d'accès) ============ */
@keyframes pbalA{from{transform:rotate(-1.6deg);}to{transform:rotate(-0.7deg);}}
@keyframes pbalB{from{transform:rotate(0.1deg);}to{transform:rotate(1.0deg);}}
@keyframes pbalC{from{transform:rotate(-0.5deg);}to{transform:rotate(0.4deg);}}
@keyframes pbalD{from{transform:rotate(0.5deg);}to{transform:rotate(1.3deg);}}
@keyframes pbalE{from{transform:rotate(-2.0deg);}to{transform:rotate(-1.2deg);}}
@keyframes pbalCle{from{transform:rotate(-4deg);}to{transform:rotate(4deg);}}
@keyframes plumiere{0%,70%{transform:translateX(-140%) skewX(-14deg);}92%,100%{transform:translateX(260%) skewX(-14deg);}}
.pf-balA{animation:pbalA 6.2s ease-in-out infinite alternate;transform-origin:50% -8px;}
.pf-balB{animation:pbalB 7.4s ease-in-out infinite alternate;transform-origin:50% -8px;}
.pf-balC{animation:pbalC 5.4s ease-in-out infinite alternate;transform-origin:50% -8px;}
.pf-balD{animation:pbalD 8.1s ease-in-out infinite alternate;transform-origin:50% -8px;}
.pf-balE{animation:pbalE 6.8s ease-in-out infinite alternate;transform-origin:50% -8px;}

.pf-porte{ position:relative; border-radius:28px; overflow:hidden; margin-top:18px;
  background:linear-gradient(158deg,#F6F2E7 0%,#E9E3D2 48%,#D8D1BA 82%,#CFC7AC 100%);
  box-shadow:0 40px 90px rgba(0,0,0,.65), inset 0 2px 0 rgba(255,255,255,.95), inset 0 -5px 12px rgba(0,0,0,.18); }
.pf-porte::after{ content:""; position:absolute; top:0; bottom:0; width:30%; left:0; pointer-events:none; z-index:6;
  background:linear-gradient(100deg,transparent,rgba(255,255,255,.18),transparent); animation:plumiere 11s ease-in-out infinite; }
.pf-congelo{ position:relative; padding:18px 28px 16px; border-bottom:3px solid rgba(42,38,32,.25);
  display:flex; gap:26px; align-items:center; box-shadow:0 3px 5px rgba(42,38,32,.18); }
.pf-congelo::after{ content:""; position:absolute; right:16px; top:50%; margin-top:-6px; width:150px; height:12px; border-radius:6px;
  background:linear-gradient(90deg,#C6BFA9,#8F8875 70%); box-shadow:2px 3px 6px rgba(0,0,0,.35), inset 0 1px 0 rgba(255,255,255,.6); }
.pf-charniere{ position:absolute; right:0; width:9px; height:34px; background:linear-gradient(90deg,#6E6759,#4A453C); z-index:5; border-radius:3px 0 0 3px; }
.pf-ch1{ top:196px; } .pf-ch2{ top:520px; }
.pf-poignee{ position:absolute; right:14px; top:36px; width:11px; height:210px; border-radius:6px; z-index:4;
  background:linear-gradient(90deg,#C6BFA9,#8F8875 70%); box-shadow:2px 3px 6px rgba(0,0,0,.35), inset 0 1px 0 rgba(255,255,255,.6); }
.pf-plinthe{ height:14px; background:linear-gradient(180deg,#31363F,#22262E); margin-top:36px; border-radius:2px; }
.pf-sol{ perspective:520px; overflow:hidden; }
.pf-reflet{ height:46px; background:linear-gradient(180deg,rgba(233,227,210,.18),transparent); filter:blur(3px); }
.pf-plancher{ height:120px; transform:rotateX(57deg); transform-origin:top center; margin-top:-20px;
  background:repeating-linear-gradient(90deg,rgba(0,0,0,.28) 0 2px,transparent 2px 190px),repeating-linear-gradient(180deg,rgba(0,0,0,.20) 0 2px,transparent 2px 44px),linear-gradient(180deg,#4A3826,#2C2115); border-radius:4px; }
.pf-coloc .cafe{ position:absolute; right:10px; bottom:6px; width:25px; height:25px; border-radius:50%; opacity:.16; border:3px solid #7A4A21; z-index:1; }
.pf-energuide .fleche{ position:absolute; top:-1px; left:30%; transform:translateX(-50%); width:0; height:0;
  border-left:7px solid transparent; border-right:7px solid transparent; border-top:9px solid #191919; }
.pf-polaroid{ position:relative; }
.pf-polaroid::after{ content:""; position:absolute; inset:0; background:linear-gradient(200deg,rgba(255,255,255,.20),transparent 45%); pointer-events:none; }
.pf-lettres{ display:flex; gap:6px; align-items:center; }
.pf-lettre{ font-family:"Bebas Neue",sans-serif; font-size:34px; line-height:1; width:39px; height:43px; border-radius:8px;
  display:flex; align-items:center; justify-content:center; color:#FFFFFF;
  background-image:radial-gradient(circle at 32% 26%,rgba(255,255,255,.55),rgba(255,255,255,0) 46%);
  text-shadow:0 2px 0 rgba(0,0,0,.25); box-shadow:0 5px 9px rgba(42,38,32,.42), inset 0 -4px 0 rgba(0,0,0,.18); }
.pf-l1{background-color:#D93A2B;transform:rotate(-4deg);} .pf-l2{background-color:#2E7CD6;transform:rotate(3deg);}
.pf-l3{background-color:#E3B505;transform:rotate(-2deg);} .pf-l4{background-color:#2FA84F;transform:rotate(4deg);}
.pf-l5{background-color:#FF7A45;transform:rotate(-3deg);} .pf-l6{background-color:#2ED3C6;transform:rotate(2deg);}
.pf-l7{background-color:#B388FF;transform:rotate(-4deg);}
.pf-plaque{ display:inline-block; background:linear-gradient(180deg,#D5CFBC,#AEA88F); color:#4A453C;
  font-family:"Bebas Neue",sans-serif; font-size:13.5px; letter-spacing:.28em; padding:5px 12px 3px; border-radius:4px;
  box-shadow:inset 0 1px 0 rgba(255,255,255,.75), 0 1px 2px rgba(0,0,0,.25); }
.pf-marque{ position:absolute; top:12px; right:24px; font-family:"Bebas Neue",sans-serif;
  font-size:14px; letter-spacing:.34em; color:#7A7261; }
.pf-polaroid{ background:#FFFFFF; padding:7px 7px 5px; border-radius:3px; width:158px; flex:none;
  box-shadow:0 12px 24px rgba(42,38,32,.4); transform:rotate(2.5deg); }
.pf-polaroid .legende{ font-family:"Caveat",cursive; font-size:18px; color:var(--encre); text-align:center; line-height:1.15; margin-top:2px; }
.pf-clezone{ margin-left:auto; text-align:center; flex:none; padding-right:186px; }
.pf-crochet{ width:17px; height:17px; border-radius:50%; margin:0 auto;
  background:radial-gradient(circle at 35% 30%,#F2EDE0,#8F8875 75%); box-shadow:0 2px 4px rgba(0,0,0,.35); }
.pf-cle{ transform-origin:50% 0; animation:pbalCle 5.5s ease-in-out infinite alternate; filter:drop-shadow(2px 3px 3px rgba(0,0,0,.35)); }
.pf-cle-legende{ font-family:"Caveat",cursive; font-size:18px; color:#5A5344; line-height:1.1; margin-top:2px; }

.pf-principale{ position:relative; padding:24px 28px 28px; }
.pf-grille{ display:grid; gap:18px; grid-template-columns:1.05fr 1fr 1fr;
  grid-template-areas:"solde calendrier calendrier" "croquis croquis liste" "coloc epicerie liste" "energuide energuide vide"; }
.pf-papier{ position:relative; border-radius:3px; padding:15px 17px 13px; color:var(--encre);
  box-shadow:0 12px 24px rgba(42,38,32,.35); }
.pf-papier::before{ content:""; position:absolute; inset:0; border-radius:3px; pointer-events:none; opacity:.05; z-index:0;
  background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='120' height='120'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='2'/%3E%3CfeColorMatrix type='saturate' values='0'/%3E%3C/filter%3E%3Crect width='120' height='120' filter='url(%23n)'/%3E%3C/svg%3E"); }
.pf-papier > *{ position:relative; z-index:1; }
.pf-papier, .pf-papier div, .pf-papier span, .pf-papier td, .pf-papier li, .pf-papier p{ color:var(--encre); }
.pf-papier .pf-autocollant, .pf-papier .pf-autocollant div{ color:#FFFFFF; }
.pf-aimant{ position:absolute; top:-8px; left:50%; margin-left:-8px; width:16px; height:16px; border-radius:50%; z-index:3;
  box-shadow:0 2px 4px rgba(0,0,0,.4), inset 0 -2px 3px rgba(0,0,0,.25); }
.pf-arouge{background:radial-gradient(circle at 35% 30%,rgba(255,255,255,.8),rgba(255,255,255,0) 45%),#D93A2B;}
.pf-ajaune{background:radial-gradient(circle at 35% 30%,rgba(255,255,255,.8),rgba(255,255,255,0) 45%),#E3B505;}
.pf-ableu{background:radial-gradient(circle at 35% 30%,rgba(255,255,255,.8),rgba(255,255,255,0) 45%),#2E7CD6;}
.pf-avert{background:radial-gradient(circle at 35% 30%,rgba(255,255,255,.8),rgba(255,255,255,0) 45%),#2FA84F;}
.pf-ruban{ position:absolute; width:74px; height:20px; top:-9px; left:22px; transform:rotate(-5deg); z-index:3;
  background:linear-gradient(180deg,rgba(255,220,130,.88),rgba(245,205,105,.82));
  clip-path:polygon(2% 6%,7% 0,93% 3%,98% 0,100% 45%,97% 94%,92% 100%,8% 97%,3% 100%,0 55%);
  box-shadow:0 2px 4px rgba(0,0,0,.2); }

.pf-solde{ grid-area:solde; background:linear-gradient(180deg,#FFF3A6,#FFE873); }
.pf-solde::after{ content:""; position:absolute; right:0; bottom:0; width:34px; height:34px; border-radius:0 0 3px 0;
  background:linear-gradient(315deg,rgba(230,220,190,0) 47%,rgba(0,0,0,.16) 50%,#FFF8C4 54%,#F2DC72 100%); }
.pf-solde .main{ font-family:"Caveat",cursive; font-size:27px; line-height:1; }
.pf-solde .montant{ font-family:"Bebas Neue",sans-serif; font-size:50px; line-height:1.02; }
.pf-solde .detail{ font-size:13px; margin-top:2px; }
.pf-solde .detail b{ color:var(--crayon); }

.pf-cal{ grid-area:calendrier; background:#FFFFFF; }
.pf-cal .titre{ font-family:"Bebas Neue",sans-serif; font-size:19px; letter-spacing:.14em; display:flex; justify-content:space-between; }
.pf-cal .titre .mois{ color:var(--crayon); }
.pf-cal table{ width:100%; border-collapse:collapse; margin-top:5px; font-size:14px; }
.pf-cal td{ padding:4px 2px; border-bottom:1px dashed #C9C2AE; }
.pf-cal tr:last-child td{ border-bottom:none; }
.pf-cal tr.passe td{ opacity:.5; text-decoration:line-through; }
.pf-cal td.moins{ color:#A93226; font-weight:700; text-align:right; white-space:nowrap; }
.pf-cal td.plus{ text-align:right; white-space:nowrap; }
.pf-cal .rdv{ font-family:"Caveat",cursive; font-size:16.5px; color:#4A4234; margin-top:7px; border-top:1px dashed #C9C2AE; padding-top:5px; }
.pf-cal .jour{ font-family:"Bebas Neue",sans-serif; font-size:16px; width:44px; }
.pf-cal .cercle{ display:inline-block; border:2.5px solid var(--crayon); padding:0 7px; transform:rotate(-3deg);
  border-radius:52% 48% 55% 45%/48% 55% 45% 52%; }
.pf-cal .plus{ color:var(--vert); font-weight:700; text-align:right; }
.pf-cal .avenir{ color:#4A453C; text-align:right; font-size:13px; font-weight:600; }

.pf-croquis{ grid-area:croquis; background:#FFFFFF; }
.pf-croquis svg{ width:100%; height:auto; display:block; }
.pf-polaroid svg{ width:100%; height:auto; display:block; }
.pf-croquis .titre{ font-family:"Caveat",cursive; font-size:26px; line-height:1; }
.pf-croquis .note{ font-size:13px; margin-top:5px; }
.pf-croquis .note b{ color:var(--crayon); }
.pf-autocollant{ position:absolute; right:-12px; bottom:-14px; width:74px; height:74px; border-radius:50%; z-index:4;
  background:radial-gradient(circle at 35% 28%,#4CC96B,#2FA84F 70%); border:3px solid #FFFFFF; transform:rotate(-9deg);
  box-shadow:0 8px 16px rgba(42,38,32,.4); color:#FFFFFF; display:flex; flex-direction:column; align-items:center; justify-content:center;
  font-family:"Bebas Neue",sans-serif; text-align:center; line-height:1; }
.pf-autocollant .gros{ font-size:15px; letter-spacing:.05em; }
.pf-autocollant .petit{ font-size:13px; margin-top:2px; }

.pf-liste{ grid-area:liste; color:var(--encre); padding-top:11px;
  background:repeating-linear-gradient(180deg,#FFFFFF 0 30px,#D8E2F0 30px 31px); }
.pf-liste .titre{ font-family:"Caveat",cursive; font-size:28px; line-height:1; }
.pf-liste ul{ list-style:none; margin-top:7px; }
.pf-liste li{ font-family:"Caveat",cursive; font-size:22px; line-height:30px; display:flex; gap:9px; align-items:baseline; }
.pf-liste .case{ flex:none; width:14px; height:14px; border:2px solid #6E6759; border-radius:3px; position:relative; top:1px; transform:rotate(-1.5deg); }
.pf-liste li.fait .case::after{ content:"✓"; position:absolute; left:0; top:-10px; font-size:19px; color:var(--vert); font-weight:700; transform:rotate(-6deg); }
.pf-liste li.fait{ color:#4A453C; text-decoration:line-through; text-decoration-color:var(--vert); }
.pf-liste li.encours span.nom{ box-shadow:inset 0 -8px 0 rgba(255,210,63,.55); }
.pf-liste .consigne{ font-family:"Work Sans",sans-serif; font-size:12.5px; color:#4A453C; margin-top:7px; line-height:1.45; }

.pf-coloc{ grid-area:coloc; background:linear-gradient(180deg,#DCEBF7,#C9DDF2); }
.pf-coloc .main{ font-family:"Caveat",cursive; font-size:22px; line-height:1.18; }
.pf-coloc .sig{ font-family:"Caveat",cursive; font-size:21px; text-align:right; }

.pf-epicerie{ grid-area:epicerie; color:var(--encre); padding-top:10px;
  background:repeating-linear-gradient(180deg,#FFFDF4 0 27px,#E4DCC4 27px 28px); }
.pf-epicerie .titre{ font-family:"Caveat",cursive; font-size:25px; line-height:1; }
.pf-epicerie .txt{ font-family:"Caveat",cursive; font-size:20px; line-height:1.3; margin-top:4px; color:#4A453C; }

.pf-energuide{ grid-area:energuide; background:#FFFFFF; display:flex; gap:15px; align-items:center; padding:11px 17px; }
.pf-energuide .bloc-noir{ background:#191919; color:#FFFFFF; font-family:"Bebas Neue",sans-serif; font-size:18px;
  letter-spacing:.14em; padding:8px 12px 6px; border-radius:3px; text-align:center; line-height:1.05; }
.pf-energuide .echelle{ flex:1; }
.pf-energuide .rangee{ display:flex; align-items:center; gap:8px; font-size:12.5px; color:#4A453C; margin-top:3px; }
.pf-energuide .barres-wrap{ flex:1; position:relative; padding-top:9px; }
.pf-energuide .fleche{ position:absolute; top:-1px; left:30%; transform:translateX(-50%); width:0; height:0;
  border-left:7px solid transparent; border-right:7px solid transparent; border-top:9px solid #191919; }
.pf-energuide .barres{ display:flex; gap:3px; }
.pf-energuide .barres i{ height:11px; flex:1; border-radius:2px; }
.pf-energuide .b1{background:#2FA84F;} .pf-energuide .b2{background:#7CC24A;} .pf-energuide .b3{background:#E3B505;}
.pf-energuide .b4{background:#FF7A45;} .pf-energuide .b5{background:#D93A2B;}
.pf-energuide .niveau{ font-family:"Bebas Neue",sans-serif; font-size:29px; color:var(--vert); }
.pf-energuide .explication{ font-size:12.5px; color:#4A453C; line-height:1.4; }

.pf-vide{ grid-area:vide; border:2.5px dashed #8A8172; border-radius:6px; display:flex; flex-direction:column;
  align-items:center; justify-content:center; color:#5A5344; text-align:center; padding:14px; position:relative;
  background:rgba(255,255,255,.45); }
.pf-vide .titre{ font-family:"Bebas Neue",sans-serif; font-size:15px; letter-spacing:.16em; }
.pf-vide .txt{ font-size:12.5px; margin-top:4px; line-height:1.45; }

.pf-mots{ display:flex; gap:8px; margin-top:20px; align-items:center; }
.pf-mot{ background:#FFFFFF; color:#33302A; font-weight:700; font-size:11.5px; letter-spacing:.07em;
  padding:3px 8px; border-radius:2px; box-shadow:0 3px 6px rgba(42,38,32,.35); }
.pf-m1{transform:rotate(-2deg);} .pf-m2{transform:rotate(1.5deg);} .pf-m3{transform:rotate(-1deg);}
.pf-m4{transform:rotate(3deg);background:var(--jaune);}

.s2-bandeau{ position:relative; border-radius:22px; margin-top:16px; padding:20px 26px 16px; overflow:hidden;
  background:linear-gradient(158deg,#F6F2E7,#E9E3D2 55%,#D8D1BA);
  box-shadow:0 24px 50px rgba(0,0,0,.55), inset 0 2px 0 rgba(255,255,255,.9); }
.s2-bandeau .journal{ font-family:"Special Elite",monospace; font-size:13px; letter-spacing:.3em; color:#5A5344; }
.s2-bandeau .titre{ font-family:"Bebas Neue",sans-serif; font-size:44px; line-height:1.02; color:var(--encre); }
.s2-bandeau .titre span{ color:var(--crayon); }
.s2-bandeau .aide{ color:#4A453C; font-size:14px; margin-top:5px; max-width:780px; }
.st-key-s2_carte_0, .st-key-s2_carte_1, .st-key-s2_carte_2{
  position:relative; background:linear-gradient(180deg,#FBF7EA,#F1EAD3); border-radius:2px;
  padding:18px 15px 10px; box-shadow:0 14px 28px rgba(0,0,0,.45); margin-top:24px; }
.st-key-s2_carte_0{ transform:rotate(-.8deg); }
.st-key-s2_carte_1{ transform:rotate(.5deg); }
.st-key-s2_carte_2{ transform:rotate(-.4deg); }
.st-key-s2_carte_0 p, .st-key-s2_carte_1 p, .st-key-s2_carte_2 p{ color:var(--encre); }
.st-key-s2_carte_0 label p, .st-key-s2_carte_1 label p, .st-key-s2_carte_2 label p{
  font-family:"Special Elite",monospace; font-size:11.5px; letter-spacing:.1em;
  text-transform:uppercase; color:#4A453C !important; }
.st-key-s2_carte_0 .stTextInput input, .st-key-s2_carte_1 .stTextInput input, .st-key-s2_carte_2 .stTextInput input{
  background:transparent !important; border:none !important; border-bottom:2px solid #B9B09A !important;
  border-radius:0 !important; box-shadow:none !important; color:var(--encre) !important; font-weight:600; }
.st-key-s2_carte_0 [data-testid="stNumberInput"] > div, .st-key-s2_carte_1 [data-testid="stNumberInput"] > div,
.st-key-s2_carte_2 [data-testid="stNumberInput"] > div{
  background:transparent; border:none; border-bottom:2px solid #B9B09A; border-radius:0; box-shadow:none; }
.st-key-s2_carte_0 [data-testid="stNumberInput"] input, .st-key-s2_carte_1 [data-testid="stNumberInput"] input,
.st-key-s2_carte_2 [data-testid="stNumberInput"] input{ background:transparent !important; color:var(--encre) !important; font-weight:700; }
.s2-photo{ background:#FFFFFF; padding:6px 6px 3px; border-radius:2px; transform:rotate(-1.2deg);
  box-shadow:0 6px 14px rgba(42,38,32,.3); margin-bottom:10px; }
.s2-photo svg{ width:100%; height:auto; display:block; }
.s2-photo .legende{ font-family:"Caveat",cursive; font-size:15.5px; color:#4A453C; text-align:center; line-height:1.15; }
.s2-nom{ font-family:"Bebas Neue",sans-serif; font-size:25px; color:var(--encre); letter-spacing:.06em; }
.pf-encercle{ position:absolute; top:150px; right:12px; z-index:5; transform:rotate(-8deg);
  border:3px solid var(--crayon); border-radius:52% 48% 55% 45%/48% 55% 45% 52%;
  color:var(--crayon); font-family:"Caveat",cursive; font-weight:700; font-size:21px;
  padding:1px 13px 0; background:rgba(255,255,255,.3); }
.st-key-s2_choix_zone{ position:relative; background:#FFFFFF; border-radius:3px; padding:16px 20px 8px;
  box-shadow:0 14px 28px rgba(0,0,0,.45); margin-top:26px; border-left:6px solid var(--crayon); }
.st-key-s2_choix_zone p, .st-key-s2_choix_zone label span{ color:var(--encre) !important; }
.st-key-s2_choix_zone .stRadio label span, .st-key-s2_choix_zone .stRadio label p{ font-family:"Caveat",cursive !important; font-size:21px !important; color:var(--encre) !important; }
.s2-choix-titre{ font-family:"Special Elite",monospace; letter-spacing:.16em; font-size:13px; color:var(--crayon); margin-bottom:2px; }
.st-key-s2_justif{ position:relative; margin-top:20px; padding:14px 18px 6px; border-radius:3px;
  background:repeating-linear-gradient(180deg,#FFFDF4 0 27px,#E4DCC4 27px 28px);
  box-shadow:0 14px 28px rgba(0,0,0,.45); }
.st-key-s2_justif p, .st-key-s2_justif label p{ color:var(--encre) !important; }
.st-key-s2_justif label p{ font-family:"Caveat",cursive !important; font-size:22px !important; }
.st-key-s2_justif [data-baseweb="textarea"]{ background:transparent !important; border:none !important; box-shadow:none !important; }
.st-key-s2_justif .stTextArea > div{ background:transparent !important; border:none !important; }
.st-key-s2_justif [data-baseweb="textarea"] > div{ background:transparent !important; }
.st-key-s2_justif textarea{ background:transparent !important; border:none !important; box-shadow:none !important;
  font-family:"Caveat",cursive !important; font-size:21px !important; line-height:28px !important; color:var(--encre) !important; }
.st-key-s2_capture_zone{ margin-top:20px; padding:14px 18px 4px; border:2.5px dashed #8A8172; border-radius:6px;
  background:rgba(255,255,255,.82); }
.st-key-s2_capture_zone label p{ color:var(--encre) !important; font-family:"Special Elite",monospace;
  font-size:12.5px; letter-spacing:.08em; }
.s2-bail{ background:#FFFFFF; color:var(--encre); border:3px double #4A453C; border-radius:4px;
  padding:16px 22px 12px; margin-top:22px; box-shadow:0 14px 28px rgba(0,0,0,.45); }
.s2-bail .titre{ font-family:"Bebas Neue",sans-serif; font-size:26px; letter-spacing:.08em; color:var(--encre); }
.s2-bail .sig{ font-family:"Caveat",cursive; font-size:21px; margin-top:10px; color:var(--encre); }
.s2-bail .sig .nom{ border-bottom:2px solid #4A453C; padding:0 14px; }

/* ============ S3 : LE JOUR DE L'EMMÉNAGEMENT ============ */
.s3-bandeau{ position:relative; border-radius:14px; margin-top:16px; padding:32px 26px 16px; overflow:hidden;
  background:repeating-linear-gradient(0deg, rgba(90,60,20,.05) 0 2px, transparent 2px 9px),
  linear-gradient(160deg,#DCB57F,#C8A166 55%,#B98F52);
  box-shadow:0 24px 50px rgba(0,0,0,.55), inset 0 2px 0 rgba(255,255,255,.35); }
.s3-bandeau::before{ content:""; position:absolute; top:0; left:6%; right:6%; height:20px;
  background:linear-gradient(180deg,rgba(255,226,150,.85),rgba(240,205,110,.7));
  box-shadow:0 2px 5px rgba(0,0,0,.22); }
.s3-bandeau .chantier{ font-family:"Special Elite",monospace; font-size:13px; letter-spacing:.26em; color:#8C2B1D; }
.s3-bandeau .titre{ font-family:"Bebas Neue",sans-serif; font-size:46px; line-height:1.02; color:#3A2410; }
.s3-bandeau .titre span{ color:#8C2B1D; }
.s3-bandeau .fraf{ position:absolute; right:22px; top:42px; transform:rotate(9deg);
  border:3.5px solid #8C2B1D; color:#8C2B1D; border-radius:6px; padding:2px 12px 0;
  font-family:"Bebas Neue",sans-serif; font-size:21px; letter-spacing:.22em; opacity:.85; }
.s3-bandeau .aide{ color:#43301A; font-size:14.5px; margin-top:6px; max-width:860px; font-weight:600; }
.s3-bandeau .aide b{ color:#8C2B1D; }
.s3-plan{ position:relative; background:#FFFFFF; border-radius:3px; padding:20px 22px 12px; margin-top:28px;
  box-shadow:0 14px 30px rgba(0,0,0,.45); }
.s3-plan .titre{ font-family:"Caveat",cursive; font-size:26px; color:var(--encre); line-height:1; }
.s3-plan svg{ width:100%; height:auto; display:block; }
.s3-plan .note{ font-size:13px; color:#4A453C; margin-top:10px; }
.s3-plan .note b{ color:var(--crayon); }
.s3-grille{ display:grid; margin-top:12px; grid-template-columns:repeat(12,1fr);
  grid-template-areas:
  "chambre chambre chambre chambre chambre chambre coloc coloc coloc coloc coloc coloc"
  "bain bain bain cuisine cuisine cuisine cuisine entree entree entree entree entree"
  "bain bain bain cuisine cuisine cuisine cuisine salon salon salon salon salon"; }
.s3-cellule{ border:3px solid #2A2620; margin:-1.5px; padding:12px 14px 10px;
  background:#FFFFFF; min-height:88px; }
.s3-cellule .nom{ font-family:"Caveat",cursive; font-size:28px; font-weight:700;
  color:var(--encre); line-height:1; }
.s3-cellule .etat{ font-family:"Work Sans",sans-serif; font-size:12px; font-weight:800;
  letter-spacing:.14em; text-transform:uppercase; margin-top:4px; }
.s3-cellule .compte{ font-family:"Special Elite",monospace; font-size:11.5px;
  color:#5A5344; margin-top:2px; }
.s3-cellule.aucun .etat{ color:#A39B85; }
.s3-cellule.minimal{ background:repeating-linear-gradient(45deg,#FFFFFF 0 10px,#F4F1E6 10px 20px); }
.s3-cellule.minimal .etat{ color:#6E6759; }
.s3-cellule.moyen{ background:#EAF6EC; }
.s3-cellule.moyen .etat{ color:#1E9E4A; }
.s3-cellule.maximal{ background:#FBF3D9; }
.s3-cellule.maximal .etat{ color:#B07B1E; }
.s3-cellule.coloc{ background:repeating-linear-gradient(45deg,#FFFFFF 0 10px,#EFEDE6 10px 20px); }
.s3-cellule.coloc .etat{ color:#8A8172; text-transform:none; letter-spacing:0;
  font-weight:600; font-size:13.5px; }
@media (max-width:760px){
  .s3-grille{ grid-template-columns:1fr;
    grid-template-areas:"chambre" "coloc" "bain" "cuisine" "entree" "salon"; }
}
.st-key-s3_piece_0, .st-key-s3_piece_1, .st-key-s3_piece_2,
.st-key-s3_piece_3, .st-key-s3_piece_4, .st-key-s3_piece_5{
  position:relative; border-radius:8px; padding:36px 16px 12px; margin-top:30px;
  background:repeating-linear-gradient(0deg, rgba(90,60,20,.045) 0 2px, transparent 2px 9px),
  linear-gradient(180deg,#E0BE8A,#CEA96C 60%,#C29B5C);
  box-shadow:0 16px 32px rgba(0,0,0,.5), inset 0 2px 0 rgba(255,255,255,.3); }
.st-key-s3_piece_0::before, .st-key-s3_piece_1::before, .st-key-s3_piece_2::before,
.st-key-s3_piece_3::before, .st-key-s3_piece_4::before, .st-key-s3_piece_5::before{
  content:""; position:absolute; top:0; left:50%; transform:translateX(-50%);
  width:150px; height:22px; border-radius:0 0 3px 3px;
  background:linear-gradient(180deg,rgba(255,226,150,.92),rgba(240,205,110,.78));
  box-shadow:0 2px 4px rgba(0,0,0,.2); }
.st-key-s3_piece_0{ transform:rotate(-.4deg); } .st-key-s3_piece_1{ transform:rotate(.35deg); }
.st-key-s3_piece_2{ transform:rotate(-.3deg); } .st-key-s3_piece_3{ transform:rotate(.45deg); }
.st-key-s3_piece_4{ transform:rotate(-.35deg); } .st-key-s3_piece_5{ transform:rotate(.3deg); }
.st-key-s3_piece_0 [data-testid="stMarkdownContainer"] p, .st-key-s3_piece_1 [data-testid="stMarkdownContainer"] p,
.st-key-s3_piece_2 [data-testid="stMarkdownContainer"] p, .st-key-s3_piece_3 [data-testid="stMarkdownContainer"] p,
.st-key-s3_piece_4 [data-testid="stMarkdownContainer"] p, .st-key-s3_piece_5 [data-testid="stMarkdownContainer"] p,
.st-key-s3_piece_0 [data-testid="stMarkdownContainer"] li, .st-key-s3_piece_1 [data-testid="stMarkdownContainer"] li,
.st-key-s3_piece_2 [data-testid="stMarkdownContainer"] li, .st-key-s3_piece_3 [data-testid="stMarkdownContainer"] li,
.st-key-s3_piece_4 [data-testid="stMarkdownContainer"] li, .st-key-s3_piece_5 [data-testid="stMarkdownContainer"] li{ color:#3A2410; }
.st-key-s3_piece_0 [data-testid="stExpander"] summary p, .st-key-s3_piece_1 [data-testid="stExpander"] summary p,
.st-key-s3_piece_2 [data-testid="stExpander"] summary p, .st-key-s3_piece_3 [data-testid="stExpander"] summary p,
.st-key-s3_piece_4 [data-testid="stExpander"] summary p, .st-key-s3_piece_5 [data-testid="stExpander"] summary p,
.st-key-s3_electro_bloc [data-testid="stExpander"] summary p{ color:var(--encre) !important; }
.st-key-s3_piece_0 [data-testid="stExpander"] summary p, .st-key-s3_piece_1 [data-testid="stExpander"] summary p,
.st-key-s3_piece_2 [data-testid="stExpander"] summary p, .st-key-s3_piece_3 [data-testid="stExpander"] summary p,
.st-key-s3_piece_4 [data-testid="stExpander"] summary p, .st-key-s3_piece_5 [data-testid="stExpander"] summary p{ color:#3A2410 !important; }
.st-key-s3_piece_0 .stButton > button p, .st-key-s3_piece_1 .stButton > button p,
.st-key-s3_piece_2 .stButton > button p, .st-key-s3_piece_3 .stButton > button p,
.st-key-s3_piece_4 .stButton > button p, .st-key-s3_piece_5 .stButton > button p,
.st-key-s3_electro_bloc .stButton > button p{ color:var(--texte) !important; }
.st-key-s3_piece_0 label p, .st-key-s3_piece_1 label p, .st-key-s3_piece_2 label p,
.st-key-s3_piece_3 label p, .st-key-s3_piece_4 label p, .st-key-s3_piece_5 label p{
  font-family:"Special Elite",monospace; font-size:11.5px; letter-spacing:.1em;
  text-transform:uppercase; color:#5A4020 !important; }
.st-key-s3_piece_0 .stTextInput input, .st-key-s3_piece_1 .stTextInput input, .st-key-s3_piece_2 .stTextInput input,
.st-key-s3_piece_3 .stTextInput input, .st-key-s3_piece_4 .stTextInput input, .st-key-s3_piece_5 .stTextInput input{
  background:transparent !important; border:none !important; border-bottom:2px solid #8A6B3F !important;
  border-radius:0 !important; box-shadow:none !important; color:#2E1C08 !important; font-weight:600; }
.st-key-s3_piece_0 [data-testid="stNumberInput"] > div, .st-key-s3_piece_1 [data-testid="stNumberInput"] > div,
.st-key-s3_piece_2 [data-testid="stNumberInput"] > div, .st-key-s3_piece_3 [data-testid="stNumberInput"] > div,
.st-key-s3_piece_4 [data-testid="stNumberInput"] > div, .st-key-s3_piece_5 [data-testid="stNumberInput"] > div{
  background:transparent; border:none; border-bottom:2px solid #8A6B3F; border-radius:0; box-shadow:none; }
.st-key-s3_piece_0 [data-testid="stNumberInput"] input, .st-key-s3_piece_1 [data-testid="stNumberInput"] input,
.st-key-s3_piece_2 [data-testid="stNumberInput"] input, .st-key-s3_piece_3 [data-testid="stNumberInput"] input,
.st-key-s3_piece_4 [data-testid="stNumberInput"] input, .st-key-s3_piece_5 [data-testid="stNumberInput"] input{
  background:transparent !important; color:#2E1C08 !important; font-weight:700; }
.s3-piece-nom{ font-family:"Caveat",cursive; font-weight:700; font-size:35px; color:#3A2410;
  letter-spacing:.01em; line-height:1; }
.s3-facture-nom{ font-family:"Bebas Neue",sans-serif; font-size:26px; color:var(--encre);
  letter-spacing:.05em; line-height:1.05; }
.s3-compte{ font-family:"Special Elite",monospace; font-size:12px; letter-spacing:.06em;
  color:#5A4020; margin-top:3px; }
.s3-compte .sans{ color:#B3271A; font-weight:700; }
.s3-tampon{ display:inline-block; transform:rotate(-7deg); border:3px solid; border-radius:6px;
  padding:1px 11px 0; font-family:"Bebas Neue",sans-serif; font-size:18px; letter-spacing:.14em;
  white-space:nowrap; }
.s3-tampon.minimal{ color:#5A5344; border-color:#5A5344; }
.s3-tampon.moyen{ color:#14632F; border-color:#1E9E4A; }
.s3-tampon.maximal{ color:#7A5410; border-color:#B07B1E; background:rgba(255,210,63,.22); }
.s3-sous{ display:flex; justify-content:space-between; gap:16px; border-top:2px dashed #8A6B3F;
  padding-top:8px; margin-top:2px; font-size:14.5px; color:#3A2410; }
.st-key-s3_electro_bloc .s3-sous{ border-top:2px dashed #B9B09A; color:var(--encre); }
.s3-sous .part{ font-weight:800; }
.s3-preuves{ display:flex; flex-wrap:wrap; gap:6px; margin-top:10px; align-items:center; }
.s3-preuves .titre{ font-family:"Special Elite",monospace; font-size:11.5px;
  letter-spacing:.1em; color:#5A4020; }
.st-key-s3_electro_bloc .s3-preuves .titre{ color:#4A453C; }
.s3-preuve{ font-family:"Special Elite",monospace; font-size:11.5px; letter-spacing:.02em;
  padding:2px 9px; border-radius:999px; border:1.8px solid; }
.s3-preuve.ok{ color:#14532D; border-color:#1E9E4A; background:rgba(30,158,74,.15); }
.s3-preuve.ko{ color:#8C1D12; border-color:#B3271A; background:rgba(179,39,26,.13); }
.st-key-s3_electro_bloc{ position:relative; background:#FFFFFF; border:3px double #4A453C; border-radius:4px;
  padding:18px 18px 10px; margin-top:30px; box-shadow:0 14px 28px rgba(0,0,0,.45); }
.st-key-s3_electro_bloc [data-testid="stMarkdownContainer"] p,
.st-key-s3_electro_bloc [data-testid="stMarkdownContainer"] li{ color:var(--encre); }
.st-key-s3_electro_bloc label p{ font-family:"Special Elite",monospace; font-size:11.5px;
  letter-spacing:.1em; text-transform:uppercase; color:#4A453C !important; }
.st-key-s3_electro_bloc .stTextInput input{
  background:transparent !important; border:none !important; border-bottom:2px solid #B9B09A !important;
  border-radius:0 !important; box-shadow:none !important; color:var(--encre) !important; font-weight:600; }
.st-key-s3_electro_bloc [data-testid="stNumberInput"] > div{
  background:transparent; border:none; border-bottom:2px solid #B9B09A; border-radius:0; box-shadow:none; }
.st-key-s3_electro_bloc [data-testid="stNumberInput"] input{
  background:transparent !important; color:var(--encre) !important; font-weight:700; }
.st-key-s3_electro_bloc .stButton > button{ padding-left:.5rem; padding-right:.5rem; }
.s3-recu{ background:#FFFFFF; color:var(--encre); border-radius:2px; padding:20px 24px 26px;
  margin:32px auto 34px; max-width:560px; position:relative;
  filter:drop-shadow(0 14px 16px rgba(0,0,0,.45)); }
.s3-recu::after{ content:""; position:absolute; left:0; right:0; bottom:-10px; height:10px;
  background:linear-gradient(45deg, transparent 33.333%, #FFFFFF 33.333%, #FFFFFF 66.667%, transparent 66.667%),
  linear-gradient(-45deg, transparent 33.333%, #FFFFFF 33.333%, #FFFFFF 66.667%, transparent 66.667%);
  background-size:20px 40px; background-position:0 -20px; }
.s3-recu .magasin{ text-align:center; font-family:"Special Elite",monospace; font-size:12px;
  letter-spacing:.22em; color:#4A453C; }
.s3-recu .titre{ font-family:"Special Elite",monospace; text-align:center; font-size:20px;
  letter-spacing:.12em; color:var(--encre); margin-top:2px; }
.s3-recu .ligne{ font-family:"Special Elite",monospace; font-size:13.5px; }
.s3-sanspreuve{ color:#B3271A; font-weight:700; font-size:13.5px; margin-top:10px; }
.s3-codebarre{ height:32px; margin-top:14px;
  background:repeating-linear-gradient(90deg,#2A2620 0 2px,transparent 2px 5px,#2A2620 5px 6px,transparent 6px 10px,#2A2620 10px 13px,transparent 13px 16px,#2A2620 16px 17px,transparent 17px 21px,#2A2620 21px 24px,transparent 24px 27px); }
.s3-recu .merci{ text-align:center; font-family:"Special Elite",monospace; font-size:11.5px;
  letter-spacing:.14em; color:#4A453C; margin-top:6px; }
.s3-jauge{ height:18px; border-radius:999px; background:#E7E0CB; overflow:hidden;
  margin-top:12px; border:1.5px solid #B9B09A; }
.s3-jauge .remplissage{ height:100%; background:linear-gradient(90deg,#2FA84F,#7CC24A); }
.s3-jauge .remplissage.presque{ background:linear-gradient(90deg,#E3B505,#FF7A45); }
.s3-jauge .remplissage.depasse{ background:linear-gradient(90deg,#D93A2B,#B01E12); }
.s3-jauge-txt{ font-size:13.5px; color:#4A453C; margin-top:5px; font-weight:600; }
.s3-jauge-txt b{ color:var(--crayon); }
.st-key-s3_piece_0 [data-testid="stCaptionContainer"] p, .st-key-s3_piece_1 [data-testid="stCaptionContainer"] p,
.st-key-s3_piece_2 [data-testid="stCaptionContainer"] p, .st-key-s3_piece_3 [data-testid="stCaptionContainer"] p,
.st-key-s3_piece_4 [data-testid="stCaptionContainer"] p, .st-key-s3_piece_5 [data-testid="stCaptionContainer"] p{
  color:#43301A !important; font-family:"Special Elite",monospace; font-size:11.5px;
  letter-spacing:.1em; text-transform:uppercase; }
.st-key-s3_electro_bloc [data-testid="stCaptionContainer"] p{
  color:#4A453C !important; font-family:"Special Elite",monospace; font-size:11.5px;
  letter-spacing:.1em; text-transform:uppercase; }

/* S4 : le pic à factures. Chaque facture est un bon de commande comme
   chez Ti-Paul : papier crème en dégradé, trou du pic en haut au centre,
   en-tête centré à la machine à écrire, le reste tapé au kilomètre.
   Chaque service garde sa couleur (en-tête et pastille de l'addition). */
.s4-bandeau{ background:linear-gradient(175deg,#F7F1E3,#EEE4CE); color:var(--encre);
  border-radius:4px; padding:30px 34px 20px; margin:30px 0 6px; position:relative;
  transform:rotate(-.4deg); box-shadow:0 20px 44px rgba(0,0,0,.55); text-align:center; }
.s4-bandeau::before{ content:""; position:absolute; top:10px; left:50%;
  transform:translateX(-50%); width:20px; height:20px; border-radius:50%;
  background:#14161C; box-shadow:inset 0 2px 5px rgba(0,0,0,.85), 0 1px 0 rgba(255,255,255,.35); }
.s4-bandeau .entete{ font-family:"Special Elite",monospace; font-size:12.5px;
  letter-spacing:.3em; color:#6B6257; margin-top:8px; }
.s4-bandeau .titre{ font-family:"Bebas Neue",sans-serif; font-size:46px;
  letter-spacing:.03em; line-height:1.02; color:var(--encre); margin-top:6px; }
.s4-bandeau .titre span{ color:#B3271A; }
.s4-bandeau .aide{ font-size:14.5px; color:#4A4234; margin:8px auto 0; max-width:68ch;
  text-align:left; }
.st-key-s4_facture_elec, .st-key-s4_facture_internet,
.st-key-s4_facture_cell, .st-key-s4_facture_ass{
  background:linear-gradient(175deg,#F7F1E3,#EEE4CE); color:var(--encre);
  border-radius:4px; position:relative; padding:34px 22px 14px; margin-top:34px;
  box-shadow:0 20px 44px rgba(0,0,0,.55); }
.st-key-s4_facture_elec{ transform:rotate(-.45deg); }
.st-key-s4_facture_internet{ transform:rotate(.5deg); }
.st-key-s4_facture_cell{ transform:rotate(-.55deg); }
.st-key-s4_facture_ass{ transform:rotate(.4deg); }
.st-key-s4_facture_elec::before, .st-key-s4_facture_internet::before,
.st-key-s4_facture_cell::before, .st-key-s4_facture_ass::before{
  content:""; position:absolute; top:10px; left:50%; transform:translateX(-50%);
  width:20px; height:20px; border-radius:50%; background:#14161C;
  box-shadow:inset 0 2px 5px rgba(0,0,0,.85), 0 1px 0 rgba(255,255,255,.35); z-index:3; }
.st-key-s4_facture_elec label p, .st-key-s4_facture_internet label p,
.st-key-s4_facture_cell label p, .st-key-s4_facture_ass label p{
  font-family:"Special Elite",monospace; font-size:11.5px; letter-spacing:.1em;
  text-transform:uppercase; color:#6B6257 !important; }
.st-key-s4_facture_elec [data-testid="stMarkdownContainer"] p,
.st-key-s4_facture_internet [data-testid="stMarkdownContainer"] p,
.st-key-s4_facture_cell [data-testid="stMarkdownContainer"] p,
.st-key-s4_facture_ass [data-testid="stMarkdownContainer"] p,
.st-key-s4_facture_elec [data-testid="stMarkdownContainer"] li,
.st-key-s4_facture_internet [data-testid="stMarkdownContainer"] li,
.st-key-s4_facture_cell [data-testid="stMarkdownContainer"] li,
.st-key-s4_facture_ass [data-testid="stMarkdownContainer"] li{ color:var(--encre); }
.st-key-s4_facture_elec .stTextInput input, .st-key-s4_facture_internet .stTextInput input,
.st-key-s4_facture_cell .stTextInput input, .st-key-s4_facture_ass .stTextInput input{
  background:transparent !important; border:none !important; border-bottom:2px solid #C9BFA5 !important;
  border-radius:0 !important; box-shadow:none !important; color:var(--encre) !important; font-weight:600; }
.st-key-s4_facture_elec [data-testid="stNumberInput"] > div,
.st-key-s4_facture_internet [data-testid="stNumberInput"] > div,
.st-key-s4_facture_cell [data-testid="stNumberInput"] > div,
.st-key-s4_facture_ass [data-testid="stNumberInput"] > div{
  background:transparent; border:none; border-bottom:2px solid #C9BFA5; border-radius:0; box-shadow:none; }
.st-key-s4_facture_elec [data-testid="stNumberInput"] input,
.st-key-s4_facture_internet [data-testid="stNumberInput"] input,
.st-key-s4_facture_cell [data-testid="stNumberInput"] input,
.st-key-s4_facture_ass [data-testid="stNumberInput"] input{
  background:transparent !important; color:var(--encre) !important; font-weight:700; }
.st-key-s4_facture_elec [data-testid="stSelectbox"] > div > div{
  background:transparent !important; border:none !important; border-bottom:2px solid #C9BFA5 !important;
  border-radius:0 !important; box-shadow:none !important; color:var(--encre) !important; font-weight:600; }
.s4-mention{ font-family:"Special Elite",monospace; font-size:12px; letter-spacing:.3em;
  text-transform:uppercase; text-align:center; }
.s4-service{ font-family:"Bebas Neue",sans-serif; font-size:29px; letter-spacing:.04em;
  color:var(--encre); line-height:1.05; text-align:center; margin-top:2px; }
.s4-pied{ display:flex; justify-content:space-between; font-family:"Special Elite",monospace;
  font-size:11.5px; letter-spacing:.14em; color:#6B6257; margin-top:12px;
  border-top:1.5px dashed #C9BFA5; padding-top:8px; text-transform:uppercase; }
.s4-part{ font-family:"Special Elite",monospace; font-size:13.5px; color:#4A4234;
  border-top:2px dashed #C9BFA5; margin-top:10px; padding-top:8px; }
.s4-part b{ color:var(--encre); font-size:15px; }
.s4-tampon{ position:absolute; top:-16px; right:-4px; transform:rotate(-11deg);
  font-family:"Special Elite",monospace; font-weight:700; font-size:14px;
  letter-spacing:.18em; color:#2E7D32; border:3px double #2E7D32; border-radius:4px;
  padding:3px 10px; background:rgba(247,241,227,.65); z-index:4; }
.s4-demarche{ margin-top:6px; }
.s4-demarche .ligne{ display:flex; justify-content:space-between; gap:14px;
  font-family:"Special Elite",monospace; font-size:13.5px; color:#3A352B;
  border-bottom:1px dotted #B4A888; padding:4px 0; }
.s4-demarche .ligne.total{ font-weight:700; color:var(--encre); font-size:15px;
  border-bottom:3px double #3A352B; }
.s4-demarche .part{ background:#FFE066; color:var(--encre); font-weight:700;
  font-family:"Special Elite",monospace; font-size:15px; display:flex;
  justify-content:space-between; gap:14px; padding:7px 10px; margin-top:10px;
  transform:rotate(-.6deg); box-shadow:0 3px 6px rgba(0,0,0,.25); }
.s4-total{ background:linear-gradient(175deg,#F7F1E3,#EEE4CE); color:var(--encre);
  border-radius:4px; padding:36px 26px 24px; margin:40px auto 34px; max-width:520px;
  position:relative; filter:drop-shadow(0 16px 18px rgba(0,0,0,.5)); }
.s4-total::before{ content:""; position:absolute; top:10px; left:50%;
  transform:translateX(-50%); width:20px; height:20px; border-radius:50%;
  background:#14161C; box-shadow:inset 0 2px 5px rgba(0,0,0,.85), 0 1px 0 rgba(255,255,255,.35); }
.s4-total::after{ content:""; position:absolute; left:0; right:0; bottom:-10px; height:10px;
  background:linear-gradient(45deg, transparent 33.333%, #EEE4CE 33.333%, #EEE4CE 66.667%, transparent 66.667%),
  linear-gradient(-45deg, transparent 33.333%, #EEE4CE 33.333%, #EEE4CE 66.667%, transparent 66.667%);
  background-size:20px 40px; background-position:0 -20px; }
.s4-total .titre{ font-family:"Special Elite",monospace; text-align:center; font-size:19px;
  letter-spacing:.12em; color:var(--encre); }
.s4-total .ligne{ display:flex; justify-content:space-between; gap:14px;
  font-family:"Special Elite",monospace; font-size:13.5px; color:#3A352B;
  border-bottom:1px dotted #B4A888; padding:5px 0; }
.s4-total .ligne .pastille{ display:inline-block; width:10px; height:10px; border-radius:50%;
  margin-right:8px; }
.s4-total .total{ display:flex; justify-content:space-between; gap:14px;
  font-family:"Special Elite",monospace; font-weight:700; font-size:16.5px; color:var(--encre);
  border-top:3px double #3A352B; margin-top:8px; padding-top:8px; }
.s4-total .note{ text-align:center; font-size:12.5px; color:#4A4234; margin-top:10px; }

/* S5 : le panier et la passe. Le transport est une vraie passe plastifiée
   (bande magnétique en haut, bandeau de couleur selon le mode choisi) ;
   l'épicerie est une liste de semainier : papier ligné, marge rouge à
   gauche, jours en onglets au-dessus. Rien à voir avec les boîtes de la
   S3 ni avec les bons de la S4. */
.s5-bandeau{ position:relative; background:#FFFDF4; color:var(--encre);
  border:3px solid #B02A20; box-shadow:0 0 0 5px #FFFDF4, 0 0 0 7px #B02A20,
  0 18px 44px rgba(0,0,0,.5); border-radius:4px; padding:22px 26px 18px;
  transform:rotate(-.3deg); margin:26px 0 8px; }
.s5-bandeau p, .s5-bandeau div{ color:var(--encre); }
.s5-bandeau .magasin{ font-family:"Special Elite",monospace; font-size:13px;
  letter-spacing:.3em; color:#B02A20; text-align:center; }
.s5-bandeau h2{ text-align:center; font-size:clamp(28px,3.4vw,42px);
  margin:6px 0 8px; color:var(--encre); }
.s5-bandeau .aide{ color:#3A352B; max-width:640px; margin:0 auto;
  text-align:left; }
.s5-burst{ position:absolute; top:-24px; right:-14px; width:104px; height:104px;
  border-radius:50%; background:var(--jaune); color:#14161C;
  transform:rotate(12deg); display:flex; align-items:center;
  justify-content:center; text-align:center; font-family:"Bebas Neue",sans-serif;
  font-size:17px; line-height:1.15; padding:10px;
  box-shadow:0 8px 20px rgba(0,0,0,.45); }
.st-key-s5_passe{ position:relative; border-radius:16px; color:#E8EEF2;
  background:linear-gradient(#0D1114,#0D1114) top/100% 26px no-repeat,
  linear-gradient(135deg,#2A4A63,#16222C);
  padding:44px 24px 18px; box-shadow:0 16px 40px rgba(0,0,0,.55);
  margin-top:26px; }
.st-key-s5_passe p, .st-key-s5_passe label, .st-key-s5_passe div{ color:#E8EEF2; }
.st-key-s5_passe .passe-titre{ font-family:"Special Elite",monospace;
  font-size:13px; letter-spacing:.28em; color:#9FB6C4; }
.s5-mode-band{ border-radius:10px; padding:10px 16px; margin:10px 0 4px;
  display:flex; justify-content:space-between; align-items:baseline; gap:14px; }
.s5-mode-band .mode{ font-family:"Bebas Neue",sans-serif; font-size:30px;
  letter-spacing:.04em; }
.s5-mode-band .prix{ font-family:"Special Elite",monospace; font-size:19px;
  font-weight:700; }
.st-key-s5_liste{ position:relative; margin-top:8px;
  background:
   linear-gradient(90deg, transparent 0 52px, rgba(200,60,50,.55) 52px 54px, transparent 54px),
   repeating-linear-gradient(#FBF6E9 0 33px, #DCD2B8 33px 34px);
  border-radius:4px; box-shadow:0 16px 40px rgba(0,0,0,.5);
  padding:20px 26px 22px 72px; color:var(--encre); }
.st-key-s5_liste label,
.st-key-s5_liste [data-testid="stWidgetLabel"] p,
.st-key-s5_liste [data-testid="stMarkdownContainer"],
.st-key-s5_liste [data-testid="stMarkdownContainer"] p{ color:var(--encre); }
.st-key-s5_passe [data-testid="stTextArea"] textarea{
  background:#F2F6F9 !important; color:#14202A !important; }
.st-key-s5_liste .stButton > button,
.st-key-s5_liste .stButton > button p,
.st-key-s5_liste .stButton > button [data-testid="stMarkdownContainer"]{
  color:var(--texte) !important; }
.st-key-s5_liste .stButton > button:hover,
.st-key-s5_liste .stButton > button:hover p{ color:var(--jaune) !important; }
.st-key-s5_liste [data-testid="stWidgetLabel"] p,
.st-key-s5_liste [data-baseweb="input"] input,
.st-key-s5_liste [data-testid="stNumberInput"] input{
  color:var(--encre) !important; }
.st-key-s5_liste [data-baseweb="input"],
.st-key-s5_liste [data-testid="stNumberInput"] > div{
  background:rgba(255,255,255,.55) !important; border:none !important;
  border-bottom:2px solid #8A7B5C !important; border-radius:6px 6px 0 0 !important;
  box-shadow:none !important; }
.s5-jour-titre{ font-family:"Caveat",cursive; font-size:38px; font-weight:700;
  color:var(--encre); line-height:1; }
.s5-repas-titre{ font-family:"Special Elite",monospace; font-size:15px;
  letter-spacing:.18em; color:#7A2E22; border-bottom:2px dashed #B4A888;
  padding-bottom:4px; margin:18px 0 2px; }
.s5-repas-cout{ font-family:"Special Elite",monospace; font-size:14px;
  color:#3A352B; text-align:right; }
.s5-totaux{ border-top:3px double #3A352B; margin-top:22px; padding-top:10px; }
.s5-totaux .ligne{ display:flex; justify-content:space-between; gap:14px;
  font-family:"Special Elite",monospace; font-size:14.5px; color:#3A352B;
  padding:4px 0; }
.s5-totaux .grand{ font-size:18px; font-weight:700; color:var(--encre);
  border-top:2px solid #3A352B; margin-top:6px; padding-top:8px; }
.s5-alerte{ font-family:"Special Elite",monospace; font-size:13.5px;
  color:#8A5A00; margin-top:8px; }

@media (max-width:980px){
  .pf-grille{ grid-template-columns:1fr; grid-template-areas:"solde" "calendrier" "croquis" "liste" "coloc" "epicerie" "energuide" "vide"; }
  .pf-congelo{ flex-wrap:wrap; }
  .pf-clezone{ padding-right:0; }
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
def fmt_montant(valeur, signe=False):
    """2 100,00 $ : format français simple. Avec signe : +2 100,00 $."""
    texte = f"{abs(float(valeur)):,.2f}".replace(",", " ").replace(".", ",") + " $"
    if signe:
        return ("+" if float(valeur) >= 0 else "−") + texte
    return texte


def aller(page):
    st.session_state["page"] = page
    # La page est aussi préparée pour le cookie « appart2_page » : après
    # un rafraîchissement, l'élève revient sur la page où il était, pas
    # à l'accueil (demande de Mathieu, 28 oct. 2026). Dépôt différé au
    # début de l'exécution suivante, comme le jeton de session.
    st.session_state["_page_a_deposer"] = page
    st.rerun()


NOM_COOKIE_JETON = "appart2_jeton"
NOM_COOKIE_PAGE = "appart2_page"
PAGES_CONNUES = {"accueil", "vie", "score", "imprevus", "sections", "console",
                 "s1", "s2", "s3", "s4", "s5"}


def deconnecter():
    st.session_state["_cookie_a_supprimer"] = True
    identifiant = st.session_state.get("identifiant")
    if identifiant:
        donnees.revoquer_jeton_session(MAGASIN, identifiant)
    for cle in ("identifiant", "compte", "page", "console_ok",
                "_annonces_montre", "_nouveaux_mouvements"):
        st.session_state.pop(cle, None)
    st.rerun()


def ouvrir_session(identifiant):
    """Ouvre la session de l'élève et prépare son jeton de session
    persistante (cookie de 90 jours) : un rafraîchissement de la page
    ne le déconnecte plus. Le jeton est seulement PRÉPARÉ ici ; main()
    le dépose dans le cookie au début de l'exécution suivante, parce
    qu'un st.rerun() immédiat jetterait le composant d'écriture avant
    que le navigateur ait enregistré le cookie (constaté en test).
    Le jeton dans l'adresse a été abandonné le 28 oct. 2026 : sur
    Streamlit Cloud, l'application ne reçoit pas les paramètres de
    l'adresse après un vrai rechargement (vérifié en production)."""
    st.session_state["identifiant"] = identifiant
    st.session_state["page"] = "accueil"
    # Connexion fraîche par mot de passe : on repart de l'accueil, et le
    # cookie de page est écrasé pour ne pas restaurer la page d'un autre
    # compte sur le même navigateur.
    st.session_state["_page_a_deposer"] = "accueil"
    jeton = donnees.nouveau_jeton_session(MAGASIN, identifiant)
    if jeton:
        st.session_state["_jeton_a_deposer"] = jeton


def _traiter_cookie_en_attente(cm):
    """Au début de chaque exécution, avant toute restauration : supprime
    le cookie si une déconnexion l'a demandé (ce qui le retire aussi du
    relevé local du gestionnaire), puis dépose le jeton en attente."""
    if cm is None:
        return
    if st.session_state.pop("_cookie_a_supprimer", False):
        for nom_cookie in (NOM_COOKIE_JETON, NOM_COOKIE_PAGE):
            try:
                cm.delete(nom_cookie)
            except Exception:
                pass
    jeton = st.session_state.pop("_jeton_a_deposer", None)
    if jeton:
        try:
            cm.set(NOM_COOKIE_JETON, jeton,
                   expires_at=datetime.datetime.now()
                   + datetime.timedelta(days=90),
                   max_age=90 * 24 * 3600)
        except Exception:
            pass
    page = st.session_state.pop("_page_a_deposer", None)
    if page in PAGES_CONNUES:
        try:
            cm.set(NOM_COOKIE_PAGE, page,
                   expires_at=datetime.datetime.now()
                   + datetime.timedelta(days=90),
                   max_age=90 * 24 * 3600)
        except Exception:
            pass


def restaurer_session(cm):
    """Si le cookie du navigateur porte un jeton valide, rouvre le
    dossier sans redemander le mot de passe (rafraîchissement, retour
    sur la page). Le jeton est révoqué à la déconnexion et à chaque
    réinitialisation du mot de passe par le prof."""
    if st.session_state.get("identifiant"):
        return
    jeton = None
    if cm is not None:
        try:
            jeton = cm.get(NOM_COOKIE_JETON)
        except Exception:
            jeton = None
    if jeton:
        identifiant = donnees.identifiant_par_jeton(MAGASIN, jeton)
        if identifiant:
            st.session_state["identifiant"] = identifiant
            # Restaurer aussi la page où l'élève était (cookie de page),
            # pas seulement sa session : un rafraîchissement le ramène
            # à sa section, jamais à l'accueil par défaut.
            page = None
            try:
                page = cm.get(NOM_COOKIE_PAGE)
            except Exception:
                page = None
            st.session_state["page"] = page if page in PAGES_CONNUES else "accueil"


def entete_marque(sous_titre):
    st.markdown(
        "<div class='pf-lampe'><div class='fil'></div><div class='abat'></div>"
        "<div class='ampoule'></div></div>"
        f"<div class='marque'>PARTIR EN <span>APPART!</span></div>"
        f"<div class='sous'>{sous_titre}</div>",
        unsafe_allow_html=True)


SVG_POLAROID = (
    "<svg viewBox='0 0 156 96' width='100%' height='auto' aria-label='Photo de l immeuble'>"
    "<defs><linearGradient id='pfciel' x1='0' y1='0' x2='0' y2='1'>"
    "<stop offset='0' stop-color='#A8CCE8'/><stop offset='1' stop-color='#D8EAF5'/></linearGradient></defs>"
    "<rect x='0' y='0' width='156' height='96' fill='url(#pfciel)'/>"
    "<circle cx='133' cy='17' r='10' fill='#FFD23F'/>"
    "<rect x='16' y='24' width='68' height='72' fill='#8A8172'/>"
    "<g fill='#FFF3A6'><rect x='24' y='36' width='10' height='10'/><rect x='42' y='36' width='10' height='10'/>"
    "<rect x='60' y='36' width='10' height='10'/><rect x='24' y='54' width='10' height='10'/>"
    "<rect x='42' y='54' width='10' height='10'/><rect x='60' y='54' width='10' height='10'/>"
    "<rect x='24' y='72' width='10' height='10'/><rect x='42' y='72' width='10' height='10'/></g>"
    "<g><rect x='97' y='58' width='3' height='26' fill='#6E6759'/>"
    "<rect x='88' y='44' width='22' height='15' fill='#FFFFFF' stroke='#D93A2B' stroke-width='1.6'/>"
    "<text x='99' y='55' font-family='Bebas Neue, sans-serif' font-size='8.5' fill='#D93A2B' text-anchor='middle'>À LOUER</text></g>"
    "<rect x='118' y='68' width='20' height='15' fill='#B07B4F'/><rect x='136' y='72' width='15' height='11' fill='#C98F5F'/>"
    "<rect x='0' y='90' width='156' height='6' fill='#7A9A5B'/></svg>")

SVG_CLE = (
    "<svg class='pf-cle' width='48' height='64' viewBox='0 0 52 70' aria-label='Ta clé'>"
    "<defs><linearGradient id='pfor' x1='0' y1='0' x2='1' y2='1'>"
    "<stop offset='0' stop-color='#E8C95A'/><stop offset='.55' stop-color='#C9A227'/>"
    "<stop offset='1' stop-color='#9A7B1A'/></linearGradient></defs>"
    "<circle cx='17' cy='15' r='10.5' fill='none' stroke='url(#pfor)' stroke-width='5.5'/>"
    "<rect x='14.5' y='24' width='5' height='32' fill='url(#pfor)'/>"
    "<rect x='19.5' y='43' width='8.5' height='4.5' fill='url(#pfor)'/>"
    "<rect x='19.5' y='51' width='6.5' height='4.5' fill='url(#pfor)'/>"
    "<g transform='rotate(14 38 34)'><rect x='29' y='22' width='19' height='25' rx='4' fill='#2E7CD6'/>"
    "<circle cx='38.5' cy='27.5' r='2.4' fill='#E9E3D2'/>"
    "<text x='38.5' y='41' font-family='Caveat, cursive' font-size='11.5' font-weight='700' fill='#FFFFFF' text-anchor='middle'>402</text></g></svg>")


def bandeau_frigo(plaque, legende_cle):
    """Le haut de la porte : lettres aimantées, polaroid, clé. Sur l'accès
    comme sur l'accueil, c'est la signature de l'univers."""
    lettres = "".join(
        f"<span class='pf-lettre pf-l{i}'>{c}</span>"
        for i, c in enumerate("APPART!", start=1))
    st.markdown(
        "<div class='pf-porte' style='margin-top:14px;'><div class='pf-congelo'>"
        "<div class='pf-marque'>ARCTIQUE</div>"
        f"<div><div class='pf-lettres'>{lettres}</div>"
        f"<div style='margin-top:9px;'><span class='pf-plaque'>{plaque}</span></div></div>"
        f"<div class='pf-polaroid'>{SVG_POLAROID}"
        "<div class='legende'>Le jour des clés!</div></div>"
        f"<div class='pf-clezone'><div class='pf-crochet'></div>{SVG_CLE}"
        f"<div class='pf-cle-legende'>{legende_cle}</div></div>"
        "</div></div>",
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
    bandeau_frigo("BIENVENUE · TON PREMIER APPART",
                  "Ta clé arrive<br>à la fin de la S2")
    choix = st.session_state.get("ecran_acces", "connexion")
    with st.container(key="acces_bar"):
        col_conn, col_insc = st.columns(2)
        with col_conn:
            if st.button("Je me connecte", key="acces_conn",
                         type="primary" if choix == "connexion" else "secondary",
                         use_container_width=True):
                st.session_state["ecran_acces"] = "connexion"
                st.rerun()
        with col_insc:
            if st.button("Je m'inscris (première fois)", key="acces_insc",
                         type="primary" if choix == "inscription" else "secondary",
                         use_container_width=True):
                st.session_state["ecran_acces"] = "inscription"
                st.rerun()
    if choix == "inscription":
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
            ouvrir_session(res["identifiant"])
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
            ouvrir_session(res["compte"]["identifiant"])
            st.success(res["message"])
            st.rerun()
        else:
            st.error(res["message"])


# ------------------------------------------------------------- écrans élève
def barre_navigation(page):
    onglets = [("accueil", "Accueil"), ("vie", "Ma vie"), ("score", "Mon score"),
               ("imprevus", "Mes imprévus"), ("sections", "Mes sections S1 à S7")]
    actif = "sections" if page in ("s1", "s2", "s3", "s4", "s5") else page
    with st.container(key="nav_bar"):
        cols = st.columns([1.1, 1, 1.2, 1.4, 2.2, 1.5])
        for col, (code, nom) in zip(cols, onglets):
            with col:
                if st.button(nom, key=f"nav_{code}",
                             type="primary" if code == actif else "secondary",
                             use_container_width=True):
                    if code != actif:
                        aller(code)
        with cols[5]:
            if st.button("Me déconnecter", key="nav_deco",
                         use_container_width=True):
                deconnecter()


def entete_eleve(compte, profil):
    entete_marque("Ton premier appartement, pour vrai. "
                  f"Trois-Rivières, en colocation avec {profil['coloc']['prenom']}.")
    params = donnees.obtenir_parametres(MAGASIN, compte["groupe"])
    mois, _ = donnees.position_dans_mois(params)
    if donnees.calendrier_en_pause(params):
        texte_mois = "en pause"
    elif mois >= 1:
        texte_mois = f"mois {min(mois, donnees.MOIS_MAX)} de {donnees.MOIS_MAX}"
    else:
        texte_mois = "pas encore commencé"
    st.markdown(
        "<div class='puces'>"
        f"<div class='puce'>{compte['nom_affiche']} · <b>Cas {compte['cas_numero']} : {profil['prenom']}</b></div>"
        f"<div class='puce'>Groupe {compte['groupe']}</div>"
        f"<div class='puce'>Mois de vie : <b>{texte_mois}</b></div>"
        "</div>",
        unsafe_allow_html=True)


def html_liste_sections(dossier):
    courante = donnees.section_courante(dossier)
    progression = dossier.get("progression", {})
    morceaux = []
    for code, nom in donnees.SECTIONS:
        etat = progression.get(code, "a_faire")
        if etat == "fait":
            classe = "fait"
        elif code == courante:
            classe = "encours"
        else:
            classe = ""
        morceaux.append(
            f"<li class='{classe}'><span class='case'></span>"
            f"<span class='nom'>{code} · {nom}</span></li>")
    return "".join(morceaux)


def html_porte_accueil(compte, dossier, profil):
    """La porte de frigo de l'accueil, remplie avec les vraies données
    de l'élève : son solde, sa paie, son coloc, ses sections."""
    coloc = profil["coloc"]
    solde = float(dossier.get("solde", profil["epargne_depart"]))
    paie = (float(profil["revenu_net_mensuel"])
            + float(profil["aide_parents_mensuelle"])
            + float(profil["autre_revenu_mensuel"]))
    lettres = "".join(
        f"<span class='pf-lettre pf-l{i}'>{c}</span>"
        for i, c in enumerate("APPART!", start=1))
    params = donnees.obtenir_parametres(MAGASIN, compte["groupe"])
    mois_courant, jour_vie = donnees.position_dans_mois(params)
    bloc_mois, detail_solde = _bloc_ton_mois(
        compte, dossier, profil, params, mois_courant, jour_vie, paie)
    croquis = (
        "<svg viewBox='0 0 320 168' width='100%' height='auto' aria-label='Croquis de l appartement'>"
        "<g fill='none' stroke='#2A2620' stroke-width='3'>"
        "<rect x='4' y='4' width='312' height='160'/><rect x='4' y='4' width='150' height='82'/>"
        "<rect x='154' y='4' width='162' height='82'/><rect x='4' y='86' width='66' height='78'/>"
        "<rect x='70' y='86' width='118' height='78'/><rect x='188' y='86' width='128' height='40'/>"
        "<rect x='188' y='126' width='128' height='38'/></g>"
        "<g font-family='Caveat, cursive' font-size='19' fill='#2A2620' text-anchor='middle'>"
        "<text x='79' y='50'>ma chambre</text>"
        f"<text x='235' y='50'>{coloc['prenom']}</text>"
        "<text x='37' y='130'>bain</text><text x='129' y='130'>cuisine</text>"
        "<text x='252' y='111'>entrée</text><text x='252' y='150'>salon</text></g></svg>")
    return (
        "<div class='pf-porte'>"
        "<div class='pf-charniere pf-ch1'></div><div class='pf-charniere pf-ch2'></div>"
        "<div class='pf-congelo'><div class='pf-marque'>ARCTIQUE</div>"
        f"<div><div class='pf-lettres'>{lettres}</div>"
        f"<div style='margin-top:9px;'><span class='pf-plaque'>BIENVENUE CHEZ {profil['prenom'].upper()}</span></div></div>"
        f"<div class='pf-polaroid'>{SVG_POLAROID}<div class='legende'>Le jour des clés!</div></div>"
        f"<div class='pf-clezone'><div class='pf-crochet'></div>{SVG_CLE}"
        + ("<div class='pf-cle-legende'>Ta clé<br>est arrivée!</div>"
           if dossier.get("progression", {}).get("S2") == "fait"
           else "<div class='pf-cle-legende'>Ta clé arrive<br>à la fin de la S2</div>")
        + "</div>"
        "</div>"
        "<div class='pf-principale'><div class='pf-poignee'></div><div class='pf-grille'>"

        "<div class='pf-papier pf-solde pf-balA'><div class='pf-aimant pf-arouge'></div>"
        "<div class='main'>Il te reste</div>"
        f"<div class='montant'>{fmt_montant(solde)}</div>"
        f"<div class='detail'>{detail_solde}</div></div>"

        + bloc_mois +
        "<div class='pf-papier pf-croquis'><div class='pf-ruban'></div>"
        "<div class='titre'>L'appart, vu d'en haut</div>"
        f"{croquis}"
        "<div class='note'>S3, meubler : vise le niveau <b>MOYEN</b> dans chaque "
        "pièce. La liste complète des articles possibles est dans la section.</div>"
        "<div class='pf-autocollant'><div class='gros'>BAC VERT</div>"
        "<div class='petit'>MARDI</div></div></div>"

        "<div class='pf-papier pf-liste'><div class='pf-aimant pf-ajaune'></div>"
        "<div class='titre'>Mon déménagement</div>"
        f"<ul>{html_liste_sections(dossier)}</ul>"
        "<div class='consigne'>Coche au crayon, comme pour vrai. Ton enseignant "
        "lance le calendrier quand la classe est prête.</div></div>"

        "<div class='pf-papier pf-coloc'><div class='pf-aimant pf-ableu'></div>"
        f"<div class='main'>{coloc['description']}</div>"
        f"<div class='sig'>- {coloc['prenom']}, ton coloc</div><div class='cafe'></div></div>"

        "<div class='pf-papier pf-epicerie'><div class='pf-aimant pf-avert'></div>"
        "<div class='titre'>Épicerie de la semaine</div>"
        "<div class='txt'>Ta première liste apparaîtra ici, à la S5.</div></div>"

        "<div class='pf-papier pf-energuide'><div class='pf-aimant pf-ajaune'></div>"
        "<div class='bloc-noir'>SCORE<br>DE VIE</div>"
        "<div class='echelle'>"
        "<div class='rangee'><span>Ton niveau, comparé aux élèves du même cas que toi :</span></div>"
        "<div class='rangee'><div class='barres-wrap'><div class='fleche'></div><div class='barres'>"
        "<i class='b1'></i><i class='b2'></i><i class='b3'></i><i class='b4'></i><i class='b5'></i>"
        "</div></div><span class='niveau'>?</span></div>"
        "<div class='explication'>Comme l'étiquette ÉnerGuide d'un vrai frigo : "
        "A est le meilleur niveau, E le plus faible. Ton niveau arrive avec tes "
        "premiers choix.</div></div></div>"

        "<div class='pf-vide'><div class='pf-aimant pf-arouge'></div>"
        "<div class='titre'>MOTS DE TON PROF ET IMPRÉVUS</div>"
        "<div class='txt'>Ils apparaîtront ici, épinglés sur ta porte, quand ils "
        "arriveront dans ta vie d'appart.</div></div>"

        "</div>"
        "<div class='pf-mots'><span class='pf-mot pf-m1'>PAYER</span>"
        "<span class='pf-mot pf-m2'>LE</span><span class='pf-mot pf-m3'>LOYER</span>"
        "<span class='pf-mot pf-m4'>LE 1ER !</span></div>"
        "</div></div>")


def page_accueil(compte, dossier, profil):
    nouveaux = st.session_state.get("_nouveaux_mouvements")
    if nouveaux:
        total = sum(m["montant"] for m in nouveaux)
        lignes = "".join(
            f"<div class='ligne'><div>{_court(m['libelle'])} "
            f"(mois {m['mois']})</div><div class='valeur'>"
            f"{fmt_montant(m['montant'], signe=True)}</div></div>"
            for m in nouveaux)
        st.markdown(
            "<section class='carte bloc-accent'><h2>Pendant ton absence</h2>"
            "<div class='aide'>La vie a continué pendant que tu n'étais "
            "pas là. Voici ce qui s'est passé, en toute transparence : "
            "rien n'est caché, tout est dans Ma vie.</div>"
            + lignes
            + "<div class='ligne total'><div>En tout</div>"
            f"<div class='valeur'>{fmt_montant(total, signe=True)}</div></div>"
            "</section>", unsafe_allow_html=True)
        if st.button("J'ai vu, merci"):
            st.session_state.pop("_nouveaux_mouvements", None)
            st.rerun()
    st.markdown(html_porte_accueil(compte, dossier, profil), unsafe_allow_html=True)
    st.markdown(
        "<div class='pf-plinthe'></div><div class='pf-sol'>"
        "<div class='pf-reflet'></div><div class='pf-plancher'></div></div>",
        unsafe_allow_html=True)

    courante = donnees.section_courante(dossier)
    if courante:
        nom = donnees.nom_section(courante)
        st.markdown(
            "<div class='etape-titre'>MA PROCHAINE ÉTAPE</div>"
            f"<div class='etape-aide'>{AIDES_ETAPES[courante]}</div>",
            unsafe_allow_html=True)
        with st.container(key="etape_bar"):
            if st.button(f"{courante} · {nom} →", type="primary",
                         use_container_width=True):
                aller(courante.lower() if courante in ("S1", "S2", "S3") else "sections")
    else:
        st.success("Tu as terminé toutes tes sections. Beau travail!")


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
        donnees.marquer_section_faite(MAGASIN, compte["identifiant"], "S1")
        st.success("S1 terminée. Bienvenue dans ton appart!")
        aller("accueil")


def _recueillir_s2():
    """Lit les widgets de la page S2 et reconstruit la structure S2."""
    annonces = []
    for i in range(3):
        annonces.append({
            "adresse": st.session_state.get(f"s2_a{i}_adresse", ""),
            "loyer": st.session_state.get(f"s2_a{i}_loyer"),
            "inclusions": st.session_state.get(f"s2_a{i}_inclusions", ""),
            "distance_km": st.session_state.get(f"s2_a{i}_distance"),
            "remarque": st.session_state.get(f"s2_a{i}_remarque", ""),
        })
    return {
        "annonces": annonces,
        "choix": st.session_state.get("s2_choix"),
        "justification": st.session_state.get("s2_justification", ""),
        "capture": st.session_state.get("s2_capture", ""),
    }


def page_s2(compte, dossier, profil):
    if st.button("Retour à l'accueil"):
        aller("accueil")
    s2 = donnees.obtenir_s2(dossier)
    deja_fait = dossier.get("progression", {}).get("S2") == "fait"
    choix_affiche = st.session_state.get("s2_choix", s2.get("choix"))

    st.markdown(
        "<div class='s2-bandeau'>"
        "<div class='journal'>LES PETITES ANNONCES · TROIS-RIVIÈRES · 4 ET DEMI SEULEMENT</div>"
        "<div class='titre'>S2 · TROUVER <span>SON LOGEMENT</span></div>"
        "<div class='aide'>Compare 3 annonces réelles. Repère de prix : loyer entre "
        "950 $ et 1 200 $ par mois. Découpe tes 3 annonces, épingle-les ici, puis "
        "encercle celle que tu choisis au crayon rouge. Même si une annonce dit "
        "« chauffé », note-la telle quelle : le calcul d'électricité se fait "
        "à la S4, pour tout le monde.</div></div>",
        unsafe_allow_html=True)
    if deja_fait:
        st.success("Tu as déjà choisi ton logement : ta clé est arrivée. "
                   "Tu peux quand même modifier tes annonces et réenregistrer.")

    aimants = ["pf-arouge", "pf-ableu", "pf-ajaune"]
    colonnes = st.columns(3)
    for i, annonce in enumerate(s2["annonces"]):
        with colonnes[i]:
            with st.container(key=f"s2_carte_{i}"):
                st.markdown(
                    f"<div class='pf-aimant {aimants[i]}'></div>"
                    "<div class='s2-photo'>" + SVG_POLAROID +
                    "<div class='legende'>Ta capture remplacera cette photo</div></div>"
                    f"<div class='s2-nom'>ANNONCE {i + 1}</div>",
                    unsafe_allow_html=True)
                if choix_affiche == i:
                    st.markdown("<div class='pf-encercle'>Choisie!</div>",
                                unsafe_allow_html=True)
                st.text_input("Adresse ou secteur", value=annonce.get("adresse") or "",
                              key=f"s2_a{i}_adresse")
                st.number_input("Loyer ($)", value=annonce.get("loyer"),
                                min_value=0.0, step=1.0, format="%.2f",
                                key=f"s2_a{i}_loyer")
                st.number_input("Distance de l'école ou du travail (km)",
                                value=annonce.get("distance_km"),
                                min_value=0.0, step=0.1, format="%.1f",
                                key=f"s2_a{i}_distance")
                st.text_input("Inclusions", value=annonce.get("inclusions") or "",
                              key=f"s2_a{i}_inclusions",
                              placeholder="Ex. chauffé, déneigement, stationnement")
                st.text_input("Remarque", value=annonce.get("remarque") or "",
                              key=f"s2_a{i}_remarque",
                              placeholder="Étage, état, bruit, sous-sol...")

    def libelle_choix(i):
        a = s2["annonces"][i]
        adresse = (a.get("adresse") or "").strip()
        if adresse and a.get("loyer"):
            return f"Annonce {i + 1} : {adresse} ({fmt_montant(a['loyer'])})"
        return f"Annonce {i + 1}"

    with st.container(key="s2_choix_zone"):
        st.markdown("<div class='s2-choix-titre'>TON CHOIX, AU CRAYON ROUGE</div>"
                    "<p style='font-size:13.5px;color:#4A453C'>Le loyer est un coût "
                    "partagé : ton coloc paie l'autre moitié.</p>",
                    unsafe_allow_html=True)
        choix_initial = s2.get("choix")
        st.radio("Quelle annonce choisis-tu ?", [0, 1, 2],
                 index=int(choix_initial) if choix_initial is not None else None,
                 format_func=libelle_choix, key="s2_choix")

    with st.container(key="s2_justif"):
        st.markdown("<div class='pf-aimant pf-avert'></div>", unsafe_allow_html=True)
        st.text_area("Justification du choix", value=s2.get("justification") or "",
                     key="s2_justification", height=112,
                     placeholder="Pourquoi cette annonce-là plutôt que les deux autres? "
                     "Parle du prix, des inclusions, du secteur et de la distance.")

    with st.container(key="s2_capture_zone"):
        st.text_input("Référence de la capture de l'annonce choisie",
                      value=s2.get("capture") or "", key="s2_capture",
                      placeholder="Nom du fichier de capture déposé dans Classroom")

    choix_vif = st.session_state.get("s2_choix")
    if choix_vif is not None:
        loyer_vif = st.session_state.get(f"s2_a{int(choix_vif)}_loyer")
        adresse_vive = (st.session_state.get(f"s2_a{int(choix_vif)}_adresse") or "").strip()
        if loyer_vif:
            st.markdown(
                "<div class='s2-bail'><div class='titre'>TON BAIL · BROUILLON</div>"
                + rang("L'appartement choisi", adresse_vive or "Adresse à compléter")
                + rang("Loyer total, par mois", fmt_montant(loyer_vif))
                + "<div class='ligne total'><div>Ta part (50 %)</div>"
                + f"<div class='valeur'>{fmt_montant(float(loyer_vif) / 2)}</div></div>"
                + "<div class='sig'>Signé : <span class='nom'>" + profil["prenom"]
                + "</span> et <span class='nom'>" + profil["coloc"]["prenom"]
                + "</span>, ton coloc. Le vrai bail se signe dans ta tête : "
                + "à partir de la S6, ce loyer sort de ton compte chaque mois.</div></div>",
                unsafe_allow_html=True)

    col_enr, col_fin = st.columns(2)
    with col_enr:
        if st.button("Enregistrer", use_container_width=True):
            donnees.enregistrer_s2(MAGASIN, compte["identifiant"], _recueillir_s2())
            st.success("Tes annonces sont enregistrées.")
    with col_fin:
        if st.button("J'ai terminé mon logement", type="primary",
                     use_container_width=True):
            saisie = _recueillir_s2()
            donnees.enregistrer_s2(MAGASIN, compte["identifiant"], saisie)
            manques = donnees.s2_manquants(saisie)
            if manques:
                for manque in manques:
                    st.error(manque)
            else:
                donnees.marquer_section_faite(MAGASIN, compte["identifiant"], "S2")
                st.success("S2 terminée. Ta clé est arrivée, bienvenue chez toi!")
                aller("accueil")


# ------------------------------------------------------------------ S3 (data)
# Listes de référence de la S3 (listes-s3-exhaustives.md) : des idées pour
# s'inspirer, jamais une liste à copier. L'élève meuble librement.
IDEES_S3 = {
    "Ma chambre": [
        "Base de lit", "Matelas", "Draps, couette et oreiller",
        "Rangement pour les vêtements (commode ou garde-robe portatif)",
        "Cintres (un paquet)", "Bureau ou petite table de travail",
        "Chaise de bureau", "Lampe de bureau", "Protège-matelas",
        "Rideaux ou stores", "Panier à linge sale", "Corbeille à papier",
        "Multiprise ou rallonge", "Table de chevet", "Lampe de chevet",
        "Miroir", "Tapis de chambre",
    ],
    "Cuisine": [
        "Table pour manger", "Chaises (au moins 2)",
        "Vaisselle de base (assiettes, bols, verres, tasses)",
        "Ustensiles (fourchettes, couteaux, cuillères)",
        "Batterie de cuisine (chaudrons, poêle, plaque)",
        "Ustensiles de cuisson (spatule, louche, planche, couteau, ouvre-boîte)",
        "Mitaines de four et sous-plats", "Linges à vaisselle et torchons",
        "Poubelle de cuisine avec couvercle", "Contenants pour les restes",
        "Éponges et liquide à vaisselle",
        "Couteaux de cuisine (chef, pain, éplucheur)", "Bols à mélanger",
        "Passoire", "Tasses et cuillères à mesurer", "Fouet et pinces de cuisine",
        "Séchoir à vaisselle", "Bac de recyclage",
        "Pellicule plastique, aluminium et papier parchemin",
        "Produits nettoyants de cuisine", "Essuie-tout", "Grille-pain",
        "Bouilloire électrique", "Cafetière", "Étagère de rangement",
        "Horloge ou minuterie", "Ouvre-bouteille et tire-bouchon",
        "Râpe et presse-ail",
    ],
    "Salon": [
        "Divan ou fauteuils (2 personnes)", "Table basse ou d'appoint",
        "Lampe de salon", "Petit meuble ou étagère de rangement",
        "Corbeille à papier", "Multiprise ou rallonge",
        "Meuble ou support pour la télévision", "Rideaux ou stores",
        "Tapis de salon", "Coussins", "Horloge murale", "Couverture ou jeté",
    ],
    "Salle de bain": [
        "Rideau de douche avec anneaux", "Tapis de bain", "Serviettes de bain",
        "Débarbouillettes", "Serviettes à mains", "Poubelle de salle de bain",
        "Ventouse (débouchoir)", "Brosse de toilette",
        "Papier toilette (stock de départ)", "Savon pour les mains",
        "Petit rangement (étagère ou panier)", "Gobelet et porte-brosses à dents",
        "Nettoyant pour salle de bain et brosse à récurer",
        "Porte-serviettes ou crochets", "Miroir", "Pèse-personne",
        "Séchoir à linge pliable",
    ],
    "Entrée et rangement": [
        "Porte-manteaux ou crochets", "Rangement pour chaussures et bottes",
        "Tapis d'entrée", "Balai et porte-poussière", "Vadrouille et seau",
        "Sacs à poubelle (stock de départ)", "Aspirateur",
        "Étagère ou boîtes de rangement", "Nettoyants de base",
        "Ampoules de rechange et piles", "Lampe de poche",
        "Boîte à outils de base", "Trousse de premiers soins",
        "Petit rangement pour clés et courrier", "Pelle à neige", "Sel déglaçant",
    ],
}
IDEES_ELECTRO = ["Réfrigérateur", "Cuisinière (four et plaques)", "Laveuse",
                 "Sécheuse", "Micro-ondes", "Lave-vaisselle"]


def html_plan_s3(brouillon, profil):
    """Le plan de l'appartement, en grille dessinée à l'encre : chaque
    pièce y montre son état réel (niveau et achats prouvés), à taille
    lisible. L'ancien plan en dessin vectoriel ne sortait pas bien :
    noms démesurés, pièces vides, meubles illisibles (retour de Mathieu,
    28 oct. 2026)."""
    zones = {"Ma chambre": ("chambre", "ma chambre"),
             donnees.PIECE_COLOC: ("coloc", None),
             "Salle de bain": ("bain", "bain"),
             "Cuisine": ("cuisine", "cuisine"),
             "Entrée et rangement": ("entree", "entrée"),
             "Salon": ("salon", "salon")}
    cellules = []
    for piece in ("Ma chambre", donnees.PIECE_COLOC, "Salle de bain",
                  "Cuisine", "Entrée et rangement", "Salon"):
        zone, libelle = zones[piece]
        if piece == donnees.PIECE_COLOC:
            cellules.append(
                f"<div class='s3-cellule coloc' style='grid-area:{zone}'>"
                f"<div class='nom'>{html.escape(profil['coloc']['prenom'])}</div>"
                "<div class='etat'>il apporte ses meubles</div></div>")
            continue
        articles = brouillon["pieces"][piece]
        nombre = donnees.nombre_prouves(articles)
        niveau = donnees.niveau_s3(nombre, donnees.SEUILS_S3[piece])
        classe = (niveau or "aucun").lower()
        etat = niveau if niveau else "à meubler"
        cellules.append(
            f"<div class='s3-cellule {classe}' style='grid-area:{zone}'>"
            f"<div class='nom'>{libelle}</div>"
            f"<div class='etat'>{etat}</div>"
            f"<div class='compte'>{nombre} achat(s) prouvé(s)</div></div>")
    return ("<div class='s3-plan'><div class='pf-ruban'></div>"
            "<div class='titre'>Ton appart, vu d'en haut</div>"
            "<div class='s3-grille'>" + "".join(cellules) + "</div>"
            "<div class='note'>Chaque pièce se remplit à mesure que tes "
            "achats <b>prouvés</b> s'ajoutent : <b>MINIMAL</b> elle "
            "fonctionne, <b>MOYEN</b> elle est complète, <b>MAXIMAL</b> le "
            "confort est là. Un achat sans lien de preuve ne meuble "
            "rien.</div></div>")


def _s3_gen():
    return st.session_state.get("s3_gen", 0)


def _init_brouillon_s3(compte, dossier):
    """Brouillon de travail de la S3, gardé dans la session : initialisé
    depuis le dossier à la première ouverture pour ce compte, puis
    synchronisé avec les widgets déjà affichés à chaque passage."""
    import copy
    proprietaire = st.session_state.get("s3_proprietaire")
    if proprietaire != compte["identifiant"] or "s3_brouillon" not in st.session_state:
        st.session_state["s3_brouillon"] = copy.deepcopy(donnees.obtenir_s3(dossier))
        st.session_state["s3_proprietaire"] = compte["identifiant"]
        st.session_state["s3_gen"] = _s3_gen() + 1
        return st.session_state["s3_brouillon"]
    brouillon = st.session_state["s3_brouillon"]
    _synchroniser_s3(brouillon)
    return brouillon


def _synchroniser_s3(brouillon):
    """Recopie dans le brouillon les valeurs des widgets affichés au
    passage précédent (les clés portent la génération courante)."""
    gen = _s3_gen()
    etat = st.session_state
    for i, piece in enumerate(donnees.PIECES):
        if piece == donnees.PIECE_COLOC:
            continue
        for j, article in enumerate(brouillon["pieces"][piece]):
            for champ in ("nom", "prix", "etat", "type", "lien"):
                cle = f"s3_p{i}_{champ}_{j}_g{gen}"
                if cle in etat:
                    article[champ] = etat[cle]
            if piece == "Ma chambre":
                article["type"] = "personnel"
    for j, article in enumerate(brouillon["electro"]):
        for champ in ("nom", "prix", "etat", "lien"):
            cle = f"s3_e_{champ}_{j}_g{gen}"
            if cle in etat:
                article[champ] = etat[cle]
    if "s3_note_coloc" in etat:
        brouillon["note_coloc"] = etat["s3_note_coloc"]


def _tampon_html(niveau):
    if niveau is None:
        return ""
    return f"<div class='s3-tampon {niveau.lower()}'>{niveau}</div>"


def _puces_preuve(articles):
    """La rangée d'étiquettes de preuve sous une boîte : un achat prouvé
    en vert, un achat commencé sans preuve en rouge. La règle du lien
    doit se voir, pas seulement se lire."""
    concernes = [a for a in articles
                 if donnees.article_prouve(a) or donnees.article_entame(a)]
    if not concernes:
        return
    puces = []
    for a in concernes:
        prouve = donnees.article_prouve(a)
        nom = html.escape((a.get("nom") or "sans nom").strip()[:26])
        puces.append(
            f"<span class='s3-preuve {'ok' if prouve else 'ko'}'>"
            f"{'✓' if prouve else '✗'} {nom}</span>")
    st.markdown(
        "<div class='s3-preuves'><span class='titre'>ÉTIQUETTES DE PREUVE :</span>"
        + "".join(puces) + "</div>",
        unsafe_allow_html=True)


def page_s3(compte, dossier, profil):
    if st.button("Retour à l'accueil"):
        aller("accueil")
    brouillon = _init_brouillon_s3(compte, dossier)
    gen = _s3_gen()
    deja_fait = dossier.get("progression", {}).get("S3") == "fait"

    st.markdown(
        "<div class='s3-bandeau'>"
        "<div class='fraf'>FRAGILE</div>"
        "<div class='chantier'>JOUR D'EMMÉNAGEMENT · LE CAMION EST DANS LA COUR</div>"
        "<div class='titre'>S3 · MEUBLER <span>L'APPART</span></div>"
        "<div class='aide'>Le camion est arrivé : à toi de tout installer, "
        "sans dépasser le plafond de 3 500 $ (ta part seulement). "
        "Tu meubles chaque boîte à ta façon : à toi de juger ce qu'il faut "
        "pour qu'une pièce fonctionne, soit complète, puis confortable. "
        "<b>Pour chaque article, colle le lien de l'annonce ou du produit : "
        "c'est ta preuve d'achat.</b> Un lien absent, ou un lien qui ne "
        "fonctionne pas, et l'achat n'a jamais existé : il ne compte ni "
        "dans la pièce, ni dans le total. Ton enseignant vérifiera les "
        "liens un par un. La chambre de ton coloc ne te coûte rien : "
        "il apporte ses meubles.</div></div>",
        unsafe_allow_html=True)
    if deja_fait:
        st.success("Tu as déjà meublé ton appartement. Tu peux quand même "
                   "modifier tes bons et réenregistrer.")

    st.markdown(html_plan_s3(brouillon, profil), unsafe_allow_html=True)

    for i, piece in enumerate(donnees.PIECES):
        with st.container(key=f"s3_piece_{i}"):
            if piece == donnees.PIECE_COLOC:
                st.markdown(
                    "<div class='s3-piece-nom'>La chambre de mon coloc</div>"
                    "<div class='s3-compte'>0 $ POUR TOI · IL APPORTE SES MEUBLES</div>",
                    unsafe_allow_html=True)
                st.write("Ton coloc meuble sa chambre lui-même. Écris une ligne "
                         "pour dire ce qu'il apporte, et c'est réglé.")
                st.text_input(
                    "Sa chambre, en une ligne", value=brouillon["note_coloc"],
                    key="s3_note_coloc",
                    placeholder="Ex. Il apporte son lit, son bureau et sa commode.")
                st.markdown(
                    "<div class='s3-sous'><span>Total de la pièce</span>"
                    "<span class='part'>Ta part : 0,00 $</span></div>",
                    unsafe_allow_html=True)
                continue

            articles = brouillon["pieces"][piece]
            nombre = donnees.nombre_prouves(articles)
            sans_preuve = sum(1 for a in articles if donnees.article_entame(a))
            niveau = donnees.niveau_s3(nombre, donnees.SEUILS_S3[piece])
            col_nom, col_tampon = st.columns([3, 1])
            with col_nom:
                compte_html = f"{nombre} ACHAT(S) PROUVÉ(S)"
                if sans_preuve:
                    compte_html += (f" · <span class='sans'>{sans_preuve} "
                                    "SANS PREUVE</span>")
                st.markdown(
                    f"<div class='s3-piece-nom'>{piece}</div>"
                    f"<div class='s3-compte'>{compte_html}</div>",
                    unsafe_allow_html=True)
            with col_tampon:
                st.markdown(_tampon_html(niveau), unsafe_allow_html=True)

            entetes = st.columns([3.2, 1.1, 1.1, 1.1, 0.7])
            for col, texte in zip(entetes, ["Article", "Prix ($)", "État", "Type", ""]):
                with col:
                    st.caption(texte)
            for j, article in enumerate(articles):
                c_nom, c_prix, c_etat, c_type, c_ret = st.columns([3.2, 1.1, 1.1, 1.1, 0.7])
                with c_nom:
                    st.text_input("Article", value=article.get("nom") or "",
                                  key=f"s3_p{i}_nom_{j}_g{gen}",
                                  label_visibility="collapsed",
                                  placeholder="Nom de l'article")
                with c_prix:
                    st.number_input("Prix ($)", value=article.get("prix"),
                                    min_value=0.0, step=1.0, format="%.2f",
                                    key=f"s3_p{i}_prix_{j}_g{gen}",
                                    label_visibility="collapsed")
                with c_etat:
                    st.selectbox("État", ["neuf", "usagé"],
                                 index=0 if article.get("etat") == "neuf" else 1,
                                 key=f"s3_p{i}_etat_{j}_g{gen}",
                                 label_visibility="collapsed")
                with c_type:
                    if piece == "Ma chambre":
                        st.markdown("<div style='padding-top:8px;font-size:13.5px;"
                                    "color:#4A453C'>Personnel</div>",
                                    unsafe_allow_html=True)
                    else:
                        st.selectbox("Type", ["partagé", "personnel"],
                                     index=0 if article.get("type") == "partagé" else 1,
                                     key=f"s3_p{i}_type_{j}_g{gen}",
                                     label_visibility="collapsed")
                with c_ret:
                    if st.button("Retirer", key=f"s3_p{i}_ret_{j}",
                                 use_container_width=True):
                        _synchroniser_s3(brouillon)
                        brouillon["pieces"][piece].pop(j)
                        st.session_state["s3_gen"] = gen + 1
                        st.rerun()
                st.text_input(
                    "Lien de preuve", value=article.get("lien") or "",
                    key=f"s3_p{i}_lien_{j}_g{gen}",
                    label_visibility="collapsed",
                    placeholder="Colle le lien de l'annonce ou du produit "
                                "(c'est ta preuve d'achat)")
            if st.button("Ajouter un article", key=f"s3_p{i}_ajout"):
                _synchroniser_s3(brouillon)
                brouillon["pieces"][piece].append(donnees.article_par_defaut(piece))
                st.session_state["s3_gen"] = gen + 1
                st.rerun()
            total_piece, part_piece = donnees.totaux_piece(brouillon, piece)
            st.markdown(
                "<div class='s3-sous'><span>Total de la pièce : "
                f"{fmt_montant(total_piece)}</span>"
                f"<span class='part'>Ta part : {fmt_montant(part_piece)}</span></div>",
                unsafe_allow_html=True)
            _puces_preuve(articles)
            with st.expander(f"Idées d'articles pour {piece.lower()}"):
                st.write(" · ".join(IDEES_S3[piece]))

    with st.container(key="s3_electro_bloc"):
        electro = brouillon["electro"]
        nombre_e = donnees.nombre_prouves(electro)
        sans_preuve_e = sum(1 for a in electro if donnees.article_entame(a))
        niveau_e = donnees.niveau_s3(nombre_e, donnees.SEUILS_ELECTRO)
        col_nom, col_tampon = st.columns([3, 1])
        with col_nom:
            compte_e = f"{nombre_e} ACHAT(S) PROUVÉ(S) · COÛT PARTAGÉ, TA PART 50 %"
            if sans_preuve_e:
                compte_e += (f" · <span class='sans'>{sans_preuve_e} "
                             "SANS PREUVE</span>")
            st.markdown(
                "<div class='s3-facture-nom'>Électroménagers · la facture</div>"
                f"<div class='s3-compte' style='color:#5A5344'>{compte_e}</div>",
                unsafe_allow_html=True)
        with col_tampon:
            st.markdown(_tampon_html(niveau_e), unsafe_allow_html=True)
        entetes = st.columns([3.0, 1.2, 1.1, 1.8, 0.9])
        for col, texte in zip(entetes, ["Article", "Prix ($)", "État", "Lien de preuve", ""]):
            with col:
                st.caption(texte)
        for j, article in enumerate(electro):
            c_nom, c_prix, c_etat, c_cap, c_ret = st.columns([3.0, 1.2, 1.1, 1.8, 0.9])
            with c_nom:
                st.text_input("Article", value=article.get("nom") or "",
                              key=f"s3_e_nom_{j}_g{gen}",
                              label_visibility="collapsed",
                              placeholder="Nom de l'électroménager")
            with c_prix:
                st.number_input("Prix ($)", value=article.get("prix"),
                                min_value=0.0, step=1.0, format="%.2f",
                                key=f"s3_e_prix_{j}_g{gen}",
                                label_visibility="collapsed")
            with c_etat:
                st.selectbox("État", ["neuf", "usagé"],
                             index=0 if article.get("etat") == "neuf" else 1,
                             key=f"s3_e_etat_{j}_g{gen}",
                             label_visibility="collapsed")
            with c_cap:
                st.text_input("Lien de preuve", value=article.get("lien") or "",
                              key=f"s3_e_lien_{j}_g{gen}",
                              label_visibility="collapsed",
                              placeholder="Lien de l'annonce ou du produit")
            with c_ret:
                if st.button("Retirer", key=f"s3_e_ret_{j}",
                             use_container_width=True):
                    _synchroniser_s3(brouillon)
                    brouillon["electro"].pop(j)
                    st.session_state["s3_gen"] = gen + 1
                    st.rerun()
        if st.button("Ajouter un électroménager", key="s3_e_ajout"):
            _synchroniser_s3(brouillon)
            brouillon["electro"].append(donnees.electro_par_defaut())
            st.session_state["s3_gen"] = gen + 1
            st.rerun()
        total_e, part_e = donnees.totaux_electro(brouillon)
        st.markdown(
            "<div class='s3-sous'><span>Total des électroménagers : "
            f"{fmt_montant(total_e)}</span>"
            f"<span class='part'>Ta part : {fmt_montant(part_e)}</span></div>",
            unsafe_allow_html=True)
        _puces_preuve(electro)
        with st.expander("Idées d'électroménagers"):
            st.write(" · ".join(IDEES_ELECTRO))

    total = donnees.total_installation(brouillon)
    pct = min(total / donnees.PLAFOND_INSTALLATION * 100, 100)
    classe_jauge = "depasse" if total > donnees.PLAFOND_INSTALLATION else (
        "presque" if pct >= 85 else "")
    lignes_recu = []
    for piece in donnees.PIECES:
        if piece == donnees.PIECE_COLOC:
            continue
        lignes_recu.append(rang(f"{piece} · ta part",
                                fmt_montant(donnees.totaux_piece(brouillon, piece)[1])))
    lignes_recu.append(rang("Électroménagers · ta part", fmt_montant(part_e)))
    lignes_recu.append(
        "<div class='ligne total'><div>TOTAL DE TON INSTALLATION</div>"
        f"<div class='valeur'>{fmt_montant(total)}</div></div>")
    sans_preuve_total = donnees.nombre_sans_preuve(brouillon)
    st.markdown(
        "<div class='s3-recu'>"
        "<div class='magasin'>MEUBLES & CIE · TROIS-RIVIÈRES</div>"
        "<div class='titre'>REÇU D'INSTALLATION</div>"
        + "".join(lignes_recu)
        + (f"<div class='s3-sanspreuve'>{sans_preuve_total} article(s) "
           "sans preuve : ils ne comptent pas dans ce reçu.</div>"
           if sans_preuve_total else "")
        + f"<div class='s3-jauge'><div class='remplissage {classe_jauge}' "
        + f"style='width:{pct:.1f}%'></div></div>"
        + f"<div class='s3-jauge-txt'>{fmt_montant(total)} sur 3 500,00 $ de plafond"
        + (f" · <b>dépassé de {fmt_montant(total - donnees.PLAFOND_INSTALLATION)}</b>"
           if total > donnees.PLAFOND_INSTALLATION else "")
        + "</div>"
        + "<div class='s3-codebarre'></div>"
        + f"<div class='merci'>CAS {int(profil['numero']):02d} · S3 · "
        "MERCI, BON EMMÉNAGEMENT</div></div>",
        unsafe_allow_html=True)

    col_enr, col_fin = st.columns(2)
    with col_enr:
        if st.button("Enregistrer", use_container_width=True):
            _synchroniser_s3(brouillon)
            donnees.enregistrer_s3(MAGASIN, compte["identifiant"], brouillon)
            st.success("Tes boîtes sont enregistrées.")
    with col_fin:
        if st.button("J'ai terminé mon installation", type="primary",
                     use_container_width=True):
            _synchroniser_s3(brouillon)
            donnees.enregistrer_s3(MAGASIN, compte["identifiant"], brouillon)
            manques = donnees.s3_manquants(brouillon)
            if manques:
                for manque in manques:
                    st.error(manque)
            else:
                donnees.marquer_section_faite(MAGASIN, compte["identifiant"], "S3")
                st.success("S3 terminée. Ton appart est meublé, bon emménagement!")
                aller("accueil")


# ------------------------------------------------------------------------ S4
LIBELLES_TAILLE = {
    "": "Choisis la taille de ton appartement",
    "petit": "Petit (3 et demi ou petit 4 et demi) : 1 050 kWh par mois",
    "moyen": "Moyen (4 et demi standard) : 1 350 kWh par mois",
    "grand": "Grand (grand 4 et demi ou 5 et demi) : 1 700 kWh par mois",
    "manuel": "Je saisis ma consommation moi-même (kWh)",
}


def _recueillir_s4():
    """Lit les widgets de la page S4 et reconstruit la structure S4."""
    return {
        "electricite": {
            "taille": st.session_state.get("s4_taille", ""),
            "kwh_manuel": st.session_state.get("s4_kwh_manuel"),
        },
        "internet": {
            "fournisseur": st.session_state.get("s4_internet_fournisseur", ""),
            "prix": st.session_state.get("s4_internet_prix"),
            "capture": st.session_state.get("s4_internet_capture", ""),
        },
        "cellulaire": {
            "fournisseur": st.session_state.get("s4_cell_fournisseur", ""),
            "prix": st.session_state.get("s4_cell_prix"),
            "capture": st.session_state.get("s4_cell_capture", ""),
        },
        "assurance": {
            "compagnie": st.session_state.get("s4_ass_compagnie", ""),
            "prix": st.session_state.get("s4_ass_prix"),
        },
    }


def page_s4(compte, dossier, profil):
    if st.button("Retour à l'accueil"):
        aller("accueil")
    s4 = donnees.obtenir_s4(dossier)
    deja_fait = dossier.get("progression", {}).get("S4") == "fait"

    st.markdown(
        "<div class='s4-bandeau'>"
        "<div class='entete'>PARTIR EN APPART! · BLOC DE FACTURES Nº 4</div>"
        "<div class='titre'>S4 · TES FACTURES, <span>SUR LE PIC</span></div>"
        "<div class='aide'>À côté du frigo, il y a le pic à factures : "
        "chaque facture s'y accroche, comme un bon de commande en cuisine. "
        "Choisis la taille de ton appartement : ton électricité se calcule "
        "toute seule, au tarif D d'Hydro-Québec, ligne par ligne. Magasine "
        "ensuite tes forfaits (repères : internet 55 $ à 85 $, cellulaire "
        "35 $ à 60 $, assurance 20 $ à 35 $) et garde une capture de chaque "
        "forfait comme preuve. L'électricité et internet se partagent avec "
        "ton coloc ; le cellulaire et l'assurance, c'est 100 % à toi. "
        "Quand une facture est complète, elle reçoit son tampon.</div></div>",
        unsafe_allow_html=True)
    if deja_fait:
        st.success("Tes factures sont déjà sur le pic. Tu peux quand même "
                   "les modifier et réenregistrer.")

    # --- Bon nº 1 : l'électricité, le calcul se fait devant l'élève. ---
    elec = s4["electricite"]
    taille_stockee = elec.get("taille") or ""
    # Valeurs vives (session, sinon le dossier) : elles servent au tampon
    # de l'en-tête, rendu avant les champs mais lu sur l'état courant.
    taille_vive = st.session_state.get("s4_taille", taille_stockee)
    elec_vive = {"taille": taille_vive,
                 "kwh_manuel": st.session_state.get(
                     "s4_kwh_manuel", elec.get("kwh_manuel"))}
    calcul = donnees.calculer_electricite(donnees.resoudre_kwh(elec_vive))
    with st.container(key="s4_facture_elec"):
        st.markdown(
            "<div class='s4-mention' style='color:#00549A'>Bon nº 01 · À partager</div>"
            "<div class='s4-service'>ÉLECTRICITÉ · TARIF D D'HYDRO-QUÉBEC</div>"
            + ("<div class='s4-tampon'>VÉRIFIÉE</div>"
               if calcul["kwh"] > 0 else ""),
            unsafe_allow_html=True)
        options_taille = ["", "petit", "moyen", "grand", "manuel"]
        st.selectbox("Taille de l'appartement", options_taille,
                     index=options_taille.index(taille_stockee)
                     if taille_stockee in options_taille else 0,
                     format_func=lambda t: LIBELLES_TAILLE[t],
                     key="s4_taille")
        taille_vive = st.session_state.get("s4_taille", taille_stockee)
        if taille_vive == "manuel":
            st.number_input("Ta consommation mensuelle (kWh)",
                            value=elec.get("kwh_manuel"),
                            min_value=0.0, step=10.0, format="%.0f",
                            key="s4_kwh_manuel")
        elec_vive = {"taille": taille_vive,
                     "kwh_manuel": st.session_state.get(
                         "s4_kwh_manuel", elec.get("kwh_manuel"))}
        calcul = donnees.calculer_electricite(donnees.resoudre_kwh(elec_vive))
        if calcul["kwh"] > 0:
            lignes = [
                ("Redevance d'accès (30 jours × 0,46154 $)",
                 fmt_montant(calcul["acces"])),
                (f"Tranche 1 : {calcul['tranche1_kwh']} kWh × 0,07065 $",
                 fmt_montant(calcul["tranche1"])),
            ]
            if calcul["tranche2_kwh"] > 0:
                lignes.append(
                    (f"Tranche 2 : {calcul['tranche2_kwh']} kWh × 0,11142 $",
                     fmt_montant(calcul["tranche2"])))
            lignes.append(("Sous-total", fmt_montant(calcul["sous_total"])))
            lignes.append(("Taxes (14,975 %)", fmt_montant(calcul["taxes"])))
            html = "<div class='s4-demarche'>"
            html += "".join(
                f"<div class='ligne'><div>{lib}</div><div>{val}</div></div>"
                for lib, val in lignes)
            html += ("<div class='ligne total'><div>TOTAL POUR L'APPARTEMENT</div>"
                     f"<div>{fmt_montant(calcul['total'])}</div></div>"
                     "<div class='part'><div>TA PART (50 %)</div>"
                     f"<div>{fmt_montant(calcul['part'])}</div></div></div>")
            st.markdown(html, unsafe_allow_html=True)
        else:
            st.markdown("<div class='s4-part'>Choisis ta taille : ton calcul "
                        "apparaîtra ici, ligne par ligne, comme sur une "
                        "vraie facture.</div>", unsafe_allow_html=True)
        st.markdown("<div class='s4-pied'><span>Hydro-Québec · Tarif D</span>"
                    "<span>Partir en appart!</span></div>",
                    unsafe_allow_html=True)

    # --- Bons nº 02 à 04 : internet, cellulaire, assurance, côte à côte. ---
    def _vif(cle, defaut):
        return st.session_state.get(cle, defaut)

    internet = s4["internet"]
    cellulaire = s4["cellulaire"]
    assurance = s4["assurance"]
    internet_ok = bool(
        (_vif("s4_internet_fournisseur", internet.get("fournisseur") or "") or "").strip()
        and _vif("s4_internet_prix", internet.get("prix"))
        and (_vif("s4_internet_capture", internet.get("capture") or "") or "").strip())
    cell_ok = bool(
        (_vif("s4_cell_fournisseur", cellulaire.get("fournisseur") or "") or "").strip()
        and _vif("s4_cell_prix", cellulaire.get("prix"))
        and (_vif("s4_cell_capture", cellulaire.get("capture") or "") or "").strip())
    ass_ok = bool(
        (_vif("s4_ass_compagnie", assurance.get("compagnie") or "") or "").strip()
        and _vif("s4_ass_prix", assurance.get("prix")))
    colonnes = st.columns(3)
    with colonnes[0]:
        with st.container(key="s4_facture_internet"):
            st.markdown(
                "<div class='s4-mention' style='color:#0E7C66'>Bon nº 02 · À partager</div>"
                "<div class='s4-service'>INTERNET</div>"
                + ("<div class='s4-tampon'>VÉRIFIÉE</div>" if internet_ok else ""),
                unsafe_allow_html=True)
            st.text_input("Fournisseur", value=internet.get("fournisseur") or "",
                          key="s4_internet_fournisseur",
                          placeholder="Ex. Bell, Vidéotron, Fizz, Oricom...")
            st.number_input("Prix mensuel pour l'appartement ($)",
                            value=internet.get("prix"),
                            min_value=0.0, step=1.0, format="%.2f",
                            key="s4_internet_prix")
            st.text_input("Référence de la capture du forfait",
                          value=internet.get("capture") or "",
                          key="s4_internet_capture",
                          placeholder="Nom du fichier déposé dans Classroom")
            prix_vif = st.session_state.get("s4_internet_prix",
                                            internet.get("prix"))
            if prix_vif:
                st.markdown(
                    "<div class='s4-part'>TOTAL APPARTEMENT : <b>"
                    + fmt_montant(prix_vif) + "</b><br>TA PART (50 %) : <b>"
                    + fmt_montant(float(prix_vif) / 2) + "</b></div>",
                    unsafe_allow_html=True)
            st.markdown("<div class='s4-pied'><span>Internet</span>"
                        "<span>Partir en appart!</span></div>",
                        unsafe_allow_html=True)

    cellulaire = s4["cellulaire"]
    with colonnes[1]:
        with st.container(key="s4_facture_cell"):
            st.markdown(
                "<div class='s4-mention' style='color:#B25F00'>Bon nº 03 · Personnel</div>"
                "<div class='s4-service'>CELLULAIRE</div>"
                + ("<div class='s4-tampon'>VÉRIFIÉE</div>" if cell_ok else ""),
                unsafe_allow_html=True)
            st.text_input("Fournisseur", value=cellulaire.get("fournisseur") or "",
                          key="s4_cell_fournisseur",
                          placeholder="Ex. Fizz, Public Mobile, Koodo...")
            st.number_input("Prix mensuel ($)", value=cellulaire.get("prix"),
                            min_value=0.0, step=1.0, format="%.2f",
                            key="s4_cell_prix")
            st.text_input("Référence de la capture du forfait",
                          value=cellulaire.get("capture") or "",
                          key="s4_cell_capture",
                          placeholder="Nom du fichier déposé dans Classroom")
            st.markdown("<div class='s4-pied'><span>Cellulaire</span>"
                        "<span>Partir en appart!</span></div>",
                        unsafe_allow_html=True)

    assurance = s4["assurance"]
    with colonnes[2]:
        with st.container(key="s4_facture_ass"):
            st.markdown(
                "<div class='s4-mention' style='color:#5B8C2A'>Bon nº 04 · Personnel</div>"
                "<div class='s4-service'>ASSURANCE HABITATION</div>"
                + ("<div class='s4-tampon'>VÉRIFIÉE</div>" if ass_ok else ""),
                unsafe_allow_html=True)
            st.text_input("Compagnie", value=assurance.get("compagnie") or "",
                          key="s4_ass_compagnie",
                          placeholder="Ex. Beneva, Desjardins, Intact, Sonnet...")
            st.number_input("Prix mensuel ($)", value=assurance.get("prix"),
                            min_value=0.0, step=1.0, format="%.2f",
                            key="s4_ass_prix")
            st.markdown("<div class='s4-part'>Elle te protège si tu mets le "
                        "feu, si tu inondes le voisin ou si on te vole. "
                        "Aucune capture demandée pour celle-ci.</div>",
                        unsafe_allow_html=True)
            st.markdown("<div class='s4-pied'><span>Assurance locataire</span>"
                        "<span>Partir en appart!</span></div>",
                        unsafe_allow_html=True)

    # --- L'addition du mois : ce qui sortira du compte. ---
    saisie_vive = _recueillir_s4()
    totaux = donnees.totaux_s4(saisie_vive)
    st.markdown(
        "<div class='s4-total'><div class='titre'>L'ADDITION DU MOIS</div>"
        "<div class='ligne'><div><span class='pastille' style='background:#00549A'>"
        "</span>Électricité (ta part)</div><div>"
        + fmt_montant(totaux["electricite_part"]) + "</div></div>"
        "<div class='ligne'><div><span class='pastille' style='background:#0E7C66'>"
        "</span>Internet (ta part)</div><div>"
        + fmt_montant(totaux["internet_part"]) + "</div></div>"
        "<div class='ligne'><div><span class='pastille' style='background:#E07B00'>"
        "</span>Cellulaire</div><div>"
        + fmt_montant(totaux["cellulaire"]) + "</div></div>"
        "<div class='ligne'><div><span class='pastille' style='background:#5B8C2A'>"
        "</span>Assurance habitation</div><div>"
        + fmt_montant(totaux["assurance"]) + "</div></div>"
        "<div class='total'><div>CE QUI SORT DE TON COMPTE</div><div>"
        + fmt_montant(totaux["total_mensuel_part"]) + "</div></div>"
        "<div class='note'>Chaque mois de vie, ces factures tomberont dans "
        "ton journal, aux jours 10 et 15. Mieux vaut les choisir que les "
        "subir.<br>MERCI · PARTIR EN APPART!</div></div>",
        unsafe_allow_html=True)

    col_enr, col_fin = st.columns(2)
    with col_enr:
        if st.button("Enregistrer", use_container_width=True):
            donnees.enregistrer_s4(MAGASIN, compte["identifiant"],
                                   _recueillir_s4())
            st.success("Tes factures sont enregistrées.")
    with col_fin:
        if st.button("J'ai terminé mes services", type="primary",
                     use_container_width=True):
            saisie = _recueillir_s4()
            donnees.enregistrer_s4(MAGASIN, compte["identifiant"], saisie)
            manques = donnees.s4_manquants(saisie)
            if manques:
                for manque in manques:
                    st.error(manque)
            else:
                donnees.marquer_section_faite(MAGASIN, compte["identifiant"], "S4")
                st.success("S4 terminée. Toutes tes factures sont sur le pic!")
                aller("accueil")


# ---------------------------------------------------------------- page S5
def _copie_menus(menus):
    import copy
    copie = copy.deepcopy(menus)
    for jour in copie:
        for code, _ in donnees.TYPES_REPAS:
            repas = jour.setdefault(code, {"nom": "", "ingredients": []})
            if not repas.get("ingredients"):
                repas["ingredients"] = [
                    {"nom": "", "prix": None, "portionsAchat": None,
                     "portionsUtilisees": None}]
    return copie


def _snapshot_s5():
    """Relit les champs visibles du jour courant (seul jour affiché) et
    les range dans le brouillon des menus gardé en session."""
    brouillon = st.session_state.get("_s5_brouillon")
    if brouillon is None:
        return
    gen = st.session_state.get("_s5_gen", 0)
    j = st.session_state.get("_s5_jour", 0)
    jour = brouillon[j]
    for code, _ in donnees.TYPES_REPAS:
        repas = jour[code]
        cle_nom = f"s5_nom_{j}_{code}_g{gen}"
        if cle_nom in st.session_state:
            repas["nom"] = st.session_state[cle_nom]
        n = max(len(repas.get("ingredients") or []), 1)
        lignes = []
        for i in range(n):
            lignes.append({
                "nom": st.session_state.get(
                    f"s5_i_{j}_{code}_{i}_nom_g{gen}", ""),
                "prix": st.session_state.get(
                    f"s5_i_{j}_{code}_{i}_prix_g{gen}"),
                "portionsAchat": st.session_state.get(
                    f"s5_i_{j}_{code}_{i}_pa_g{gen}"),
                "portionsUtilisees": st.session_state.get(
                    f"s5_i_{j}_{code}_{i}_pu_g{gen}"),
            })
        repas["ingredients"] = lignes


def _aller_jour_s5(j):
    _snapshot_s5()
    st.session_state["_s5_jour"] = j


def _ajouter_ingredient_s5(j, code):
    _snapshot_s5()
    st.session_state["_s5_brouillon"][j][code]["ingredients"].append(
        {"nom": "", "prix": None, "portionsAchat": None,
         "portionsUtilisees": None})
    st.session_state["_s5_gen"] = st.session_state.get("_s5_gen", 0) + 1


def _retirer_ingredient_s5(j, code, i):
    _snapshot_s5()
    lignes = st.session_state["_s5_brouillon"][j][code]["ingredients"]
    if 0 <= i < len(lignes):
        del lignes[i]
    st.session_state["_s5_gen"] = st.session_state.get("_s5_gen", 0) + 1


def _menus_nettoyes(brouillon):
    """Retire les lignes d'ingrédients restées complètement vides avant
    l'enregistrement (le dossier reste fidèle à la v1)."""
    import copy
    menus = copy.deepcopy(brouillon)
    for jour in menus:
        for code, _ in donnees.TYPES_REPAS:
            repas = jour[code]
            repas["ingredients"] = [
                l for l in repas.get("ingredients") or []
                if (l.get("nom") or "").strip()
                or (l.get("prix") or 0) > 0
                or (l.get("portionsAchat") or 0) > 0
                or (l.get("portionsUtilisees") or 0) > 0]
    return menus


def _jour_complet(jour):
    for code, _ in donnees.TYPES_REPAS:
        repas = jour.get(code) or {}
        if not (repas.get("nom") or "").strip():
            return False
        lignes = [l for l in repas.get("ingredients") or []
                  if (l.get("nom") or "").strip()]
        if not lignes:
            return False
    return True


def page_s5(compte, dossier, profil):
    if st.button("Retour à l'accueil", key="s5_retour"):
        _snapshot_s5()
        aller("accueil")
    identifiant = compte["identifiant"]
    s5 = donnees.obtenir_s5(dossier)
    if st.session_state.get("_s5_charge") != identifiant:
        st.session_state["_s5_brouillon"] = _copie_menus(s5["menus"])
        st.session_state["_s5_gen"] = 0
        st.session_state["_s5_jour"] = 0
        st.session_state["_s5_charge"] = identifiant
    brouillon = st.session_state["_s5_brouillon"]
    gen = st.session_state["_s5_gen"]
    jour_idx = st.session_state["_s5_jour"]
    transport = s5["transport"]

    if dossier.get("progression", {}).get("S5") == "fait":
        st.success("Ton transport et tes menus sont déjà planifiés. "
                   "Tu peux quand même les corriger ici.")

    st.markdown(
        "<div class='s5-bandeau'>"
        "<div class='magasin'>MARCHÉ DE LA COLOC · CIRCULAIRE DE LA SEMAINE</div>"
        "<h2>S5 · TON TRANSPORT ET TES MENUS</h2>"
        "<div class='aide'>Deux planifications qui reviennent chaque mois : "
        "comment tu te déplaces, et ce que tu manges. Choisis d'abord ta "
        "passe de transport. Ensuite, remplis ton semainier : 7 jours, "
        "4 repas par jour, aucune case vide. Pour chaque repas, écris son "
        "nom, puis ses ingrédients : le prix de l'article au magasin, le "
        "nombre de portions dans l'achat et le nombre de portions "
        "utilisées pour ce repas. L'outil divise le prix selon les "
        "portions utilisées : c'est le coût réel de la nourriture mangée. "
        "Si un même article sert dans deux repas (un pain, un bloc de "
        "fromage), inscris-le dans chaque repas où tu l'utilises.</div>"
        "<div class='s5-burst'>7 JOURS<br>28 REPAS</div></div>",
        unsafe_allow_html=True)

    # --- La passe de transport. ---
    modes = list(donnees.MODES_TRANSPORT)
    mode_stocke = transport.get("mode") or ""
    with st.container(key="s5_passe"):
        st.markdown("<div class='passe-titre'>LAISSEZ-PASSER · "
                    "TROIS-RIVIÈRES</div>", unsafe_allow_html=True)
        mode_vif = st.session_state.get("s5_mode", mode_stocke)
        couleurs_mode = {"a-pied": ("#2E7D32", "#FFFFFF"),
                         "velo": ("#F2A007", "#14161C"),
                         "autobus-sttr": ("#00549A", "#FFFFFF"),
                         "auto": ("#546E7A", "#FFFFFF")}
        fond, encre = couleurs_mode.get(mode_vif, ("#37474F", "#FFFFFF"))
        cout_vif = st.session_state.get("s5_cout", transport.get("cout"))
        prix_txt = (fmt_montant(cout_vif) + " / mois"
                    if cout_vif else "À CHOISIR")
        nom_mode = donnees.MODES_TRANSPORT.get(
            mode_vif, "CHOISIS TA PASSE")
        st.markdown(
            f"<div class='s5-mode-band' style='background:{fond};color:{encre}'>"
            f"<span class='mode'>{nom_mode.upper()}</span>"
            f"<span class='prix'>{prix_txt}</span></div>",
            unsafe_allow_html=True)
        st.selectbox(
            "Choisis ta passe (ton mode de transport)",
            modes,
            index=modes.index(mode_stocke) if mode_stocke in modes else None,
            placeholder="Choisis ton mode de transport",
            format_func=lambda m: donnees.MODES_TRANSPORT[m],
            key="s5_mode")
        st.number_input(
            "Coût mensuel de ton transport ($)",
            min_value=0.0, step=1.0,
            value=float(transport["cout"]) if transport.get("cout") else None,
            placeholder="Ex. 81",
            help="Repère STTR : laissez-passer mensuel général 81 $ par "
                 "mois en 2026. À pied, ça peut être 0 $.",
            key="s5_cout")
        st.text_area(
            "Pourquoi ce transport ? (justification)",
            value=transport.get("justification") or "",
            placeholder="Ex. Le cégep est à 25 minutes à pied, "
                        "l'autobus passe aux 30 minutes...",
            key="s5_justif")

    def _lire_transport():
        return {
            "mode": st.session_state.get("s5_mode", mode_stocke) or "",
            "cout": st.session_state.get("s5_cout", transport.get("cout")),
            "justification": st.session_state.get(
                "s5_justif", transport.get("justification") or ""),
        }

    # --- Le semainier : un onglet par jour. ---
    st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)
    colonnes_jours = st.columns(7)
    for j, nom_jour in enumerate(donnees.JOURS):
        with colonnes_jours[j]:
            coche = " ✓" if _jour_complet(brouillon[j]) else ""
            st.button(f"{nom_jour}{coche}", key=f"s5_jour_btn_{j}",
                      type="primary" if j == jour_idx else "secondary",
                      on_click=_aller_jour_s5, args=(j,),
                      use_container_width=True)

    # --- La liste du jour, sur le papier ligné. ---
    jour = brouillon[jour_idx]
    with st.container(key="s5_liste"):
        remplis = sum(1 for c, _ in donnees.TYPES_REPAS
                      if (jour[c].get("nom") or "").strip())
        st.markdown(
            f"<div class='s5-jour-titre'>{donnees.JOURS[jour_idx]}</div>"
            f"<div class='pf-note'>{remplis} repas sur 4 nommés pour "
            "cette journée.</div>",
            unsafe_allow_html=True)
        for code, libelle in donnees.TYPES_REPAS:
            repas = jour[code]
            st.markdown(f"<div class='s5-repas-titre'>{libelle.upper()}</div>",
                        unsafe_allow_html=True)
            st.text_input(
                f"Nom du repas ({libelle.lower()})",
                value=repas.get("nom") or "",
                placeholder="Ex. Spaghetti sauce à la viande",
                key=f"s5_nom_{jour_idx}_{code}_g{gen}")
            lignes = repas.get("ingredients") or []
            if not lignes:
                lignes = [{"nom": "", "prix": None, "portionsAchat": None,
                           "portionsUtilisees": None}]
            lignes_lues = []
            for i, ligne in enumerate(lignes):
                c_nom, c_prix, c_pa, c_pu, c_cout, c_ret = st.columns(
                    [3.1, 1.25, 1.3, 1.3, 1.15, 0.95])
                with c_nom:
                    st.text_input(
                        "Ingrédient", value=ligne.get("nom") or "",
                        placeholder="Ex. Pâtes (boîte)",
                        key=f"s5_i_{jour_idx}_{code}_{i}_nom_g{gen}",
                        label_visibility="collapsed" if i else "visible")
                with c_prix:
                    st.number_input(
                        "Prix ($)", min_value=0.0, step=0.25,
                        value=(float(ligne["prix"])
                               if ligne.get("prix") else None),
                        placeholder="0,00",
                        key=f"s5_i_{jour_idx}_{code}_{i}_prix_g{gen}",
                        label_visibility="collapsed" if i else "visible")
                with c_pa:
                    st.number_input(
                        "Portions achetées", min_value=0.0, step=1.0,
                        value=(float(ligne["portionsAchat"])
                               if ligne.get("portionsAchat") else None),
                        placeholder="Ex. 6",
                        key=f"s5_i_{jour_idx}_{code}_{i}_pa_g{gen}",
                        label_visibility="collapsed" if i else "visible")
                with c_pu:
                    st.number_input(
                        "Portions utilisées", min_value=0.0, step=1.0,
                        value=(float(ligne["portionsUtilisees"])
                               if ligne.get("portionsUtilisees") else None),
                        placeholder="Ex. 2",
                        key=f"s5_i_{jour_idx}_{code}_{i}_pu_g{gen}",
                        label_visibility="collapsed" if i else "visible")
                with c_cout:
                    lu = {"prix": st.session_state.get(
                              f"s5_i_{jour_idx}_{code}_{i}_prix_g{gen}",
                              ligne.get("prix")),
                          "portionsAchat": st.session_state.get(
                              f"s5_i_{jour_idx}_{code}_{i}_pa_g{gen}",
                              ligne.get("portionsAchat")),
                          "portionsUtilisees": st.session_state.get(
                              f"s5_i_{jour_idx}_{code}_{i}_pu_g{gen}",
                              ligne.get("portionsUtilisees"))}
                    lignes_lues.append(lu)
                    st.markdown(
                        "<div class='s5-repas-cout'>"
                        + ("Coût" if i == 0 else "") + "<br>"
                        + fmt_montant(donnees.cout_ingredient(lu)) + "</div>",
                        unsafe_allow_html=True)
                with c_ret:
                    if i == 0:
                        st.markdown("<div class='s5-repas-cout'> </div>",
                                    unsafe_allow_html=True)
                    st.button("Retirer", key=f"s5_ret_{jour_idx}_{code}_{i}",
                              on_click=_retirer_ingredient_s5,
                              args=(jour_idx, code, i))
            cout_repas = sum(
                donnees.cout_ingredient(l) for l in lignes_lues)
            col_vide, col_btn, col_cout = st.columns([2.2, 1.6, 1.4])
            with col_btn:
                st.button("+ Un ingrédient de plus",
                          key=f"s5_ajout_{jour_idx}_{code}",
                          on_click=_ajouter_ingredient_s5,
                          args=(jour_idx, code))
            with col_cout:
                st.markdown(
                    "<div class='s5-repas-cout'>Coût de ce repas "
                    f"(2 pers.) : {fmt_montant(cout_repas)}</div>",
                    unsafe_allow_html=True)
        # Totaux de la semaine, lus sur les menus fusionnés.
        _snapshot_s5()
        totaux = donnees.calculer_epicerie(
            _menus_nettoyes(st.session_state["_s5_brouillon"]))
        bas, haut = donnees.FOURCHETTE_EPICERIE
        alerte = ""
        if 0 < totaux["achats_totale"] and not (
                bas <= totaux["achats_totale"] <= haut):
            alerte = ("<div class='s5-alerte'>Repère : les achats d'une "
                      "semaine pour 2 personnes coûtent entre 120 $ et "
                      "190 $. Vérifie ta liste.</div>")
        st.markdown(
            "<div class='s5-totaux'>"
            "<div class='ligne'><span>Achats inscrits dans les menus "
            f"(2 personnes)</span><span>{fmt_montant(totaux['achats_totale'])}</span></div>"
            "<div class='ligne'><span>Nourriture utilisée dans la semaine "
            f"(2 personnes)</span><span>{fmt_montant(totaux['semaine_utilisee'])}</span></div>"
            "<div class='ligne'><span>Ta part de nourriture utilisée "
            f"(50 %)</span><span>{fmt_montant(totaux['semaine_part'])}</span></div>"
            "<div class='ligne grand'><span>Ta part pour le mois "
            f"(semaine utilisée x 4,33)</span><span>{fmt_montant(totaux['mois_part'])}</span></div>"
            "</div>" + alerte,
            unsafe_allow_html=True)

    def _enregistrer():
        _snapshot_s5()
        s5_neuf = {"transport": _lire_transport(),
                   "menus": _menus_nettoyes(
                       st.session_state["_s5_brouillon"])}
        donnees.enregistrer_s5(MAGASIN, identifiant, s5_neuf)
        return s5_neuf

    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
    col_enr, col_term = st.columns(2)
    with col_enr:
        if st.button("Enregistrer", use_container_width=True,
                     key="s5_enregistrer"):
            _enregistrer()
            st.success("Ton transport et tes menus sont enregistrés.")
    with col_term:
        if st.button("J'ai terminé ma semaine", type="primary",
                     use_container_width=True, key="s5_terminer"):
            s5_neuf = _enregistrer()
            manquants = donnees.s5_manquants(s5_neuf)
            if manquants:
                st.error("Il te manque des choses avant de terminer :")
                for manque in manquants:
                    st.warning(manque)
            else:
                donnees.marquer_section_faite(MAGASIN, identifiant, "S5")
                st.success("S5 terminée. Ta semaine est planifiée "
                           "au complet!")
                aller("accueil")



def page_sections(compte, dossier, profil):
    st.markdown("<section class='carte'><h2>Mes sections</h2>"
                "<div class='aide'>Ton travail, section par section. "
                "La S1, la S2, la S3, la S4 et la S5 sont prêtes ; les autres arrivent plus tard.</div></section>",
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
            if code in ("S1", "S2", "S3", "S4", "S5"):
                if st.button(f"Ouvrir la {code}", key=f"ouvrir_{code.lower()}"):
                    aller(code.lower())
            else:
                st.caption("Arrive plus tard")


def page_attente(titre, texte, phase):
    st.markdown(
        f"<section class='carte'><h2>{titre}</h2><div>{texte}</div></section>",
        unsafe_allow_html=True)
    st.caption(f"Page en construction ({phase}).")


# ----------------------------------------------------------------------- main
def main():
    cm = None
    if stx is not None:
        try:
            cm = stx.CookieManager()
        except Exception:
            cm = None
    _traiter_cookie_en_attente(cm)
    restaurer_session(cm)
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

    nouveaux = donnees.appliquer_vie(MAGASIN, identifiant,
                                      compte["groupe"], profil)
    if nouveaux:
        st.session_state["_nouveaux_mouvements"] = nouveaux
        dossier = MAGASIN.charger_dossier(identifiant)
    non_vues = donnees.annonces_non_vues(dossier)
    if non_vues and st.session_state.get("_annonces_montre") != len(non_vues):
        st.session_state["_annonces_montre"] = len(non_vues)
        dialogue_annonces(identifiant, non_vues)

    entete_eleve(compte, profil)
    page = st.session_state.get("page", "accueil")
    barre_navigation(page)

    if page == "accueil":
        page_accueil(compte, dossier, profil)
    elif page == "s1":
        page_s1(compte, dossier, profil)
    elif page == "s2":
        page_s2(compte, dossier, profil)
    elif page == "s3":
        page_s3(compte, dossier, profil)
    elif page == "s4":
        page_s4(compte, dossier, profil)
    elif page == "s5":
        page_s5(compte, dossier, profil)
    elif page == "sections":
        page_sections(compte, dossier, profil)
    elif page == "vie":
        page_vie(compte, dossier, profil)
    elif page == "console":
        page_console(compte)
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

    with st.container(key="acces_bar"):
        if st.button("Console du prof", key="vers_console"):
            aller("console")

    if MAGASIN.mode == "memoire":
        st.markdown(
            "<div class='pied'>Mode test local : les données sont gardées "
            "en mémoire seulement, le temps de la session.</div>",
            unsafe_allow_html=True)



def _court(libelle):
    """Version courte d'un libellé de mouvement, pour la porte."""
    texte = libelle.split("(")[0].strip().rstrip(",")
    return texte[:1].upper() + texte[1:] if texte else libelle


def _bloc_ton_mois(compte, dossier, profil, params, mois_courant,
                   jour_vie, paie):
    """Le papier TON MOIS de la porte, vivant : avant le lancement,
    l'aperçu des jours repères ; après, les mouvements du mois en
    cours, les passés rayés au crayon, le prochain encerclé en rouge,
    et l'état des deux rendez-vous du mois."""
    if not params.get("lance_le") or mois_courant < 1:
        bloc = (
            "<div class='pf-papier pf-cal'><div class='pf-aimant pf-ableu'></div>"
            "<div class='titre'><span>TON MOIS</span><span class='mois'>PAS ENCORE COMMENCÉ</span></div>"
            "<table>"
            f"<tr><td class='jour'><span class='cercle'>J1</span></td><td>Paie</td>"
            f"<td class='plus'>+{fmt_montant(paie)}</td><td>Loyer, ta part</td>"
            "<td class='avenir'>à la S2</td></tr>"
            "<tr><td class='jour'>J5</td><td>Épicerie du mois, ta part</td>"
            "<td class='avenir'>à la S5</td><td></td><td></td></tr>"
            "<tr><td class='jour'>J10</td><td>Hydro et internet, ta part</td>"
            "<td class='avenir'>à la S4</td><td></td><td></td></tr>"
            "<tr><td class='jour'>J15</td><td>Cellulaire, assurance, transport</td>"
            "<td class='avenir'>à la S5</td><td></td><td></td></tr>"
            "</table></div>")
        return bloc, ("C'est ton épargne de départ. Prochain mouvement : "
                      "<b>jour 1, paie et loyer</b>, quand le calendrier "
                      "va commencer.")
    import copy as _copy
    dossier_copie = _copy.deepcopy(dossier)
    mouvements = donnees.generer_mouvements_mois(
        dossier_copie, profil, params, min(mois_courant, donnees.MOIS_MAX),
        compte["identifiant"])
    par_jour = {}
    for m in mouvements:
        par_jour.setdefault(m["jour"], []).append(m)
    lignes = []
    prochain = None
    for jour in sorted(par_jour):
        groupe = par_jour[jour]
        passe = jour < jour_vie
        if not passe and prochain is None:
            prochain = groupe[0]
        cellule_jour = (f"<span class='cercle'>J{jour}</span>"
                        if not passe and prochain is groupe[0]
                        else f"J{jour}")
        for i, m in enumerate(groupe):
            signe = "plus" if m["montant"] > 0 else "moins"
            lignes.append(
                f"<tr class='{'passe' if passe else ''}'>"
                f"<td class='jour'>{cellule_jour if i == 0 else ''}</td>"
                f"<td>{_court(m['libelle'])}</td>"
                f"<td class='{signe}'>{fmt_montant(abs(m['montant']))}</td></tr>")
    vie = donnees.obtenir_vie(dossier)
    cle = str(min(mois_courant, donnees.MOIS_MAX))
    decision = (vie.get("decisions") or {}).get(cle)
    bilan = (vie.get("bilans") or {}).get(cle)
    txt_decision = "prise ✓" if decision else "à prendre dans Ma vie"
    txt_bilan = "fait ✓" if bilan else "à faire dans Ma vie"
    bloc = (
        "<div class='pf-papier pf-cal'><div class='pf-aimant pf-ableu'></div>"
        f"<div class='titre'><span>TON MOIS</span><span class='mois'>MOIS "
        f"{min(mois_courant, donnees.MOIS_MAX)} DE {donnees.MOIS_MAX}</span></div>"
        "<table>" + "".join(lignes) + "</table>"
        f"<div class='rdv'>Ta décision du mois : <b>{txt_decision}</b> · "
        f"Ton bilan éclair : <b>{txt_bilan}</b></div></div>")
    if prochain is not None:
        detail = (f"Prochain mouvement : <b>jour {prochain['jour']}, "
                  f"{_court(prochain['libelle']).lower()}</b> "
                  f"({fmt_montant(prochain['montant'], signe=True)}).")
    else:
        detail = "Tous les mouvements du mois sont passés. Le prochain mois s'en vient."
    return bloc, detail


def page_vie(compte, dossier, profil):
    if st.button("Retour à l'accueil"):
        aller("accueil")
    st.markdown("## Ma vie")
    params = donnees.obtenir_parametres(MAGASIN, compte["groupe"])
    vie = donnees.obtenir_vie(dossier)
    mois_courant, _ = donnees.position_dans_mois(params)
    if not params.get("lance_le"):
        st.markdown(
            "<section class='carte'><h2>Le calendrier n'a pas commencé</h2>"
            "<div>Ton enseignant le lancera en classe. D'ici là, avance "
            "tes sections : quand la vie va commencer, tes montants "
            "seront déjà les tiens.</div></section>",
            unsafe_allow_html=True)
        return
    if donnees.calendrier_en_pause(params):
        st.info("Le calendrier est sur pause (ton enseignant l'a mis en "
                "attente). La vie reprendra bientôt.")
    mois_courant = min(mois_courant, donnees.MOIS_MAX)

    # --- Les deux rendez-vous du mois en cours ---
    if mois_courant >= 1:
        st.markdown("<section class='carte bloc-accent'><h2>Tes deux "
                    "rendez-vous du mois</h2>"
                    "<div class='aide'>Chaque mois de vie, tu as un rôle "
                    "à jouer deux fois : décider, puis regarder ton mois "
                    "en face. C'est ça, vivre le projet.</div></section>",
                    unsafe_allow_html=True)
        cle = str(mois_courant)
        decision = (vie.get("decisions") or {}).get(cle)
        st.markdown(f"### 1. Ta décision du mois {mois_courant}")
        if decision:
            choix = next((c for c in donnees.BANQUE_CHOIX_VIE
                          if c["id"] == decision["choix_id"]), None)
            if choix:
                opt = choix["options"][decision["option"]]
                mention = " (choix par défaut : tu n'avais pas décidé)" \
                    if decision.get("defaut") else ""
                st.success(f"Décidé : {opt['libelle']} "
                           f"({fmt_montant(decision['montant'], signe=True)})"
                           f"{mention}")
        else:
            choix = donnees.choix_pour_mois(compte["identifiant"],
                                            mois_courant)
            st.markdown(f"**{choix['titre']}**")
            st.write(choix["texte"])
            choix_idx = st.radio(
                "Tu fais quoi ?",
                options=list(range(len(choix["options"]))),
                format_func=lambda i: (
                    f"{choix['options'][i]['libelle']} "
                    f"({fmt_montant(choix['options'][i]['montant'], signe=True)})"),
                key=f"decision_radio_{mois_courant}")
            if st.button("Je décide", type="primary"):
                try:
                    donnees.enregistrer_decision(
                        MAGASIN, compte["identifiant"], mois_courant,
                        int(choix_idx))
                    st.success("Décision prise et notée dans ton journal.")
                    st.rerun()
                except ValueError as erreur:
                    st.error(str(erreur))
        st.markdown(f"### 2. Ton bilan éclair du mois {mois_courant}")
        bilan = (vie.get("bilans") or {}).get(cle)
        if bilan:
            st.success(f"Question : {bilan['question']}")
            st.write(f"Ta réponse : {bilan['choix']}"
                     + (f" — {bilan['phrase']}" if bilan["phrase"] else ""))
        else:
            question = donnees.BANQUE_BILANS[
                (mois_courant - 1) % len(donnees.BANQUE_BILANS)]
            st.write(f"**{question}**")
            reponse = st.radio(
                "En un mot :",
                ["Ça s'est bien passé", "C'était serré",
                 "C'était difficile"],
                key=f"bilan_radio_{mois_courant}")
            phrase = st.text_input(
                "En une phrase, pourquoi ?",
                key=f"bilan_phrase_{mois_courant}")
            if st.button("Je note mon bilan"):
                donnees.enregistrer_bilan(
                    MAGASIN, compte["identifiant"], mois_courant,
                    reponse, phrase.strip())
                st.success("Bilan noté. Il te servira pour ta S6 et ta S7.")
                st.rerun()

    # --- Le journal des mouvements, mois par mois ---
    st.markdown("### Ton journal, mois par mois")
    mouvements = vie.get("mouvements") or []
    if not mouvements:
        st.write("Rien pour l'instant : le premier mois n'est pas encore "
                 "terminé. Reviens après la première semaine.")
    par_mois = {}
    for m in mouvements:
        par_mois.setdefault(m.get("mois") or 0, []).append(m)
    for mois in sorted(par_mois, reverse=True):
        groupe = par_mois[mois]
        total = sum(m["montant"] for m in groupe)
        titre = f"Mois {mois}" if mois else "Hors calendrier"
        lignes = "".join(
            f"<div class='ligne'><div>{_court(m['libelle'])}</div>"
            f"<div class='valeur'>{fmt_montant(m['montant'], signe=True)}</div></div>"
            for m in groupe)
        st.markdown(
            f"<section class='carte'><h2>{titre}</h2>" + lignes
            + "<div class='ligne total'><div>Solde du mois</div>"
            f"<div class='valeur'>{fmt_montant(total, signe=True)}</div></div>"
            "</section>", unsafe_allow_html=True)
    st.markdown(
        f"<div class='note-crayon'>Tu t'es connecté "
        f"{len(vie.get('connexions') or [])} jour"
        f"{'s' if len(vie.get('connexions') or []) > 1 else ''} "
        f"depuis le début du projet.</div>")


CODE_PROF = "1959"


@st.dialog("Un mot de ton enseignant")
def dialogue_annonces(identifiant, annonces):
    for annonce in annonces:
        st.write(annonce["texte"])
    if st.button("J'ai compris"):
        donnees.marquer_annonces_vues(MAGASIN, identifiant)
        st.rerun()


def _etat_groupe(groupe):
    params = donnees.obtenir_parametres(MAGASIN, groupe)
    if not params.get("lance_le"):
        return params, "non lancé"
    mois, _ = donnees.position_dans_mois(params)
    if donnees.calendrier_en_pause(params):
        return params, f"en pause (mois {min(mois, donnees.MOIS_MAX)})"
    return params, f"mois {min(mois, donnees.MOIS_MAX)} de {donnees.MOIS_MAX}"


def page_console(compte):
    if st.button("Retour à l'accueil"):
        aller("accueil")
    st.markdown("## Console du prof")
    if not st.session_state.get("console_ok"):
        code = st.text_input("Code du prof", type="password",
                             key="console_code")
        if st.button("Ouvrir la console"):
            if code == CODE_PROF:
                st.session_state["console_ok"] = True
                st.rerun()
            else:
                st.error("Code incorrect.")
        return

    st.markdown("### Le temps, par groupe")
    for groupe in donnees.GROUPES:
        params, etat = _etat_groupe(groupe)
        cols = st.columns([1, 2, 2, 2])
        cols[0].markdown(f"**Groupe {groupe}**")
        cols[1].write(etat)
        if not params.get("lance_le"):
            with cols[2]:
                jour = st.date_input("Lancement", key=f"lancer_{groupe}")
            with cols[3]:
                if st.button("Lancer le calendrier", key=f"go_{groupe}"):
                    donnees.lancer_calendrier(MAGASIN, groupe, jour)
                    donnees.consigner_prof(
                        MAGASIN, f"Calendrier lancé pour le groupe "
                        f"{groupe} le {jour}.")
                    st.rerun()
        else:
            with cols[3]:
                en_pause = donnees.calendrier_en_pause(params)
                if st.button("Reprendre" if en_pause else "Mettre en pause",
                             key=f"pause_{groupe}"):
                    donnees.basculer_pause(
                        MAGASIN, groupe,
                        __import__('datetime').date.today())
                    donnees.consigner_prof(
                        MAGASIN, f"Calendrier du groupe {groupe} : "
                        f"{'repris' if en_pause else 'mis en pause'}.")
                    st.rerun()

    st.markdown("### La classe")
    groupe = st.selectbox("Groupe", donnees.GROUPES, key="console_groupe")
    params, _ = _etat_groupe(groupe)
    mois_courant, _ = donnees.position_dans_mois(params)
    lignes = []
    for c in MAGASIN.comptes_du_groupe(groupe):
        d = MAGASIN.charger_dossier(c["identifiant"]) or {}
        vie = donnees.obtenir_vie(d)
        faites = sum(1 for v in (d.get("progression") or {}).values()
                     if v == "fait")
        retards = []
        for code, comp in (vie.get("completions") or {}).items():
            f = donnees.facteur_section(code, comp.get("date"), params)
            if f < 1.0:
                retards.append(f"{code} ({int(f * 100)} %)")
        cle = str(min(mois_courant, donnees.MOIS_MAX))
        lignes.append({
            "Élève": c["nom_affiche"], "Cas": c["cas_numero"],
            "Sections": f"{faites}/7",
            "Solde": fmt_montant(d.get("solde") or 0),
            "Mois atteint": vie.get("mois_appliques") or 0,
            "Décision": "faite" if cle in (vie.get("decisions") or {})
                        else "à faire",
            "Bilan": "fait" if cle in (vie.get("bilans") or {})
                     else "à faire",
            "Retards": ", ".join(retards) or "-",
            "Connexions": len(vie.get("connexions") or []),
            "Gelé": "oui" if vie.get("gele") else "-",
        })
    if lignes:
        st.dataframe(lignes, use_container_width=True, hide_index=True)
    else:
        st.write("Aucun compte dans ce groupe pour l'instant.")

    comptes_groupe = MAGASIN.comptes_du_groupe(groupe)
    noms = {c["identifiant"]: c["nom_affiche"] for c in comptes_groupe}

    if comptes_groupe:
        st.markdown("**Pause individuelle** : geler un élève arrête SON "
                    "calendrier (aucun mois ne s'applique à son dossier) "
                    "sans toucher au groupe. Au dégel, les mois dus "
                    "s'appliquent d'un coup, comme après une absence.")
        cols_gel = st.columns([3, 1])
        with cols_gel[0]:
            eleve_gel = st.selectbox("Élève", list(noms),
                                     format_func=lambda i: noms[i],
                                     key="gel_eleve")
        with cols_gel[1]:
            d_gel = MAGASIN.charger_dossier(eleve_gel) or {}
            est_gele = donnees.obtenir_vie(d_gel).get("gele")
            if st.button("Dégeler" if est_gele else "Geler",
                         key="gel_bouton"):
                donnees.basculer_gel(MAGASIN, eleve_gel)
                donnees.consigner_prof(
                    MAGASIN, f"Calendrier {'gelé' if not est_gele else 'dégelé'} "
                    f"pour {noms[eleve_gel]} (groupe {groupe}).")
                st.rerun()

    st.markdown("### Imprévu ciblé")
    choix_imp = st.selectbox(
        "Imprévu", [i["titre"] for i in donnees.BANQUE_IMPREVUS]
        + ["Personnalisé…"], key="imp_choix")
    cible = st.radio("Cible", ["Un élève", "Tout le groupe"],
                     key="imp_cible", horizontal=True)
    identifiant_cible = None
    if cible == "Un élève" and comptes_groupe:
        identifiant_cible = st.selectbox(
            "Élève", list(noms), format_func=lambda i: noms[i],
            key="imp_eleve")
    montant_perso = None
    libelle_perso = None
    if choix_imp == "Personnalisé…":
        libelle_perso = st.text_input("Libellé (vu par l'élève)",
                                      key="imp_libelle")
        montant_perso = st.number_input(
            "Montant (négatif = un coût, positif = un gain)",
            value=0.0, step=10.0, key="imp_montant")
    if st.button("Appliquer l'imprévu", type="primary"):
        imp = next((i for i in donnees.BANQUE_IMPREVUS
                    if i["titre"] == choix_imp), None)
        cibles = [identifiant_cible] if cible == "Un élève"             else list(noms)
        for ident in [c for c in cibles if c]:
            c = MAGASIN.compte_par_identifiant(ident)
            profil_e = PROFILS[int(c["cas_numero"])]
            d = MAGASIN.charger_dossier(ident) or {}
            mois_e = min(mois_courant, donnees.MOIS_MAX) or None
            if imp and imp.get("special") == "heures_coupees":
                paie_e = (float(profil_e["revenu_net_mensuel"])
                          + float(profil_e["autre_revenu_mensuel"])
                          + float(profil_e["aide_parents_mensuelle"]))
                montant = -round(paie_e * 0.20, 2)
                libelle = ("Heures coupées au travail : ta paie du mois "
                           "est réduite de 20 %")
            elif imp and imp.get("special") == "coloc_retard":
                fermeture = donnees.date_fermeture_mois(params, mois_e or 1)
                part = donnees._montant_pour(d, "S2", "loyer_part",
                                             fermeture)
                montant = -part
                libelle = ("Tu avances la part de loyer de ton coloc "
                           "(il te remboursera le mois prochain)")
                donnees.programmer_mouvement(
                    MAGASIN, ident, (mois_e or 1) + 1,
                    "Remboursement de ton coloc : sa part de loyer",
                    part)
            elif imp:
                montant = imp["montant"]
                libelle = imp["titre"]
            else:
                montant = float(montant_perso or 0)
                libelle = libelle_perso or "Imprévu"
            donnees.ajouter_mouvement(MAGASIN, ident, libelle, montant,
                                      source="imprevu", mois=mois_e)
            donnees.poser_annonce(
                MAGASIN, ident,
                f"Surprise de ton enseignant : {libelle} "
                f"({fmt_montant(montant, signe=True)}). C'est déjà dans "
                f"ton journal, dans Ma vie.")
        donnees.consigner_prof(
            MAGASIN, f"Imprévu « {choix_imp} » appliqué à "
            f"{cible.lower()} du groupe {groupe}.")
        st.success("Imprévu appliqué et annoncé aux élèves concernés.")

    st.markdown("### Événement et annonce pour un groupe")
    texte_annonce = st.text_area("Texte de l'annonce", key="evt_texte")
    montant_evt = st.number_input(
        "Effet en argent pour chaque élève (0 = annonce simple)",
        value=0.0, step=10.0, key="evt_montant")
    if st.button("Envoyer au groupe"):
        for ident in noms:
            if montant_evt:
                donnees.ajouter_mouvement(
                    MAGASIN, ident, texte_annonce or "Événement de classe",
                    float(montant_evt), source="evenement",
                    mois=min(mois_courant, donnees.MOIS_MAX) or None)
            if texte_annonce:
                donnees.poser_annonce(MAGASIN, ident, texte_annonce)
        donnees.consigner_prof(
            MAGASIN, f"Événement/annonce au groupe {groupe} : "
            f"« {texte_annonce} » ({fmt_montant(montant_evt, signe=True)}).")
        st.success("C'est envoyé.")

    st.markdown("### Correction en lot")
    montant_corr = st.number_input("Montant pour chaque élève du groupe",
                                   value=0.0, step=10.0, key="corr_montant")
    motif = st.text_input("Motif (il paraît dans leur journal)",
                          key="corr_motif")
    if st.button("Appliquer la correction"):
        for ident in noms:
            donnees.ajouter_mouvement(
                MAGASIN, ident, f"Correction : {motif or 'ajustement'}",
                float(montant_corr), source="correction",
                mois=min(mois_courant, donnees.MOIS_MAX) or None)
        donnees.consigner_prof(
            MAGASIN, f"Correction en lot groupe {groupe} : "
            f"{fmt_montant(montant_corr, signe=True)} — {motif}.")
        st.success("Correction appliquée à tout le groupe.")

    st.markdown("### Mot de passe oublié")
    if comptes_groupe:
        eleve_mdp = st.selectbox("Élève", list(noms),
                                 format_func=lambda i: noms[i],
                                 key="mdp_eleve")
        nouveau = st.text_input("Nouveau mot de passe (à lui remettre "
                                "en classe)", key="mdp_nouveau")
        if st.button("Réinitialiser le mot de passe"):
            if len(nouveau or "") >= 6:
                donnees.reinitialiser_mot_de_passe(
                    MAGASIN, eleve_mdp, nouveau)
                donnees.consigner_prof(
                    MAGASIN, f"Mot de passe réinitialisé pour "
                    f"{noms[eleve_mdp]} (groupe {groupe}).")
                st.success("Mot de passe réinitialisé.")
            else:
                st.error("Six caractères minimum.")

    st.markdown("### Journal du prof")
    entrees = donnees.lire_journal_prof(MAGASIN)
    if entrees:
        for entree in entrees[-30:][::-1]:
            st.write(f"{entree['date']} — {entree['texte']}")
    else:
        st.write("Rien pour l'instant : tout ce que tu injecteras "
                 "paraîtra ici.")


main()

"""Partir en appart! v2 : application Streamlit (phase P1, univers figé).

Univers figé le 28 octobre 2026 : « la porte de frigo » (voir la charte
files/charte-univers-frigo.md du dossier du projet et la maquette v7).
Inscription avec mot de passe, connexion, accueil en porte de frigo,
section S1 en lecture, section S2 (les 3 annonces comparées, le choix,
la justification, la capture) et section S3 (le plan qui se meuble, les
bons de commande par pièce, la facture d'électroménagers, le reçu sous
le plafond de 3 500 $) fonctionnelles, progression sauvegardée.
Le calendrier de vie, la console du prof et les sections S4 à S7
arrivent aux phases suivantes.
La couche de données vit dans donnees.py (magasin mémoire ou Supabase REST).
"""
import streamlit as st

import donnees

# Garde-fou de déploiement : si le processus en ligne garde en mémoire une
# ancienne version du module donnees (rechargement partiel de Streamlit
# Cloud), on force son rechargement avant d'aller plus loin.
if not hasattr(donnees, "PIECE_COLOC"):
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

/* ============ S3 : LE PLAN QUI SE MEUBLE ============ */
.s3-bandeau{ position:relative; border-radius:22px; margin-top:16px; padding:26px 26px 16px; overflow:hidden;
  background:repeating-linear-gradient(0deg, rgba(42,38,32,.055) 0 1px, transparent 1px 26px),
  repeating-linear-gradient(90deg, rgba(42,38,32,.055) 0 1px, transparent 1px 26px),
  linear-gradient(160deg,#FDFDF8,#F1EEDF 60%,#E4DEC8);
  box-shadow:0 24px 50px rgba(0,0,0,.55), inset 0 2px 0 rgba(255,255,255,.9); }
.s3-bandeau::before{ content:""; position:absolute; top:0; left:7%; right:7%; height:17px;
  background:linear-gradient(180deg,rgba(255,220,130,.75),rgba(245,205,105,.6));
  box-shadow:0 2px 4px rgba(0,0,0,.18); }
.s3-bandeau .chantier{ font-family:"Special Elite",monospace; font-size:13px; letter-spacing:.28em; color:#7A4A21; }
.s3-bandeau .titre{ font-family:"Bebas Neue",sans-serif; font-size:44px; line-height:1.02; color:var(--encre); }
.s3-bandeau .titre span{ color:#B07B1E; }
.s3-bandeau .aide{ color:#4A453C; font-size:14px; margin-top:5px; max-width:840px; }
.s3-plan{ position:relative; background:#FFFFFF; border-radius:3px; padding:20px 22px 12px; margin-top:28px;
  box-shadow:0 14px 30px rgba(0,0,0,.45); }
.s3-plan .titre{ font-family:"Caveat",cursive; font-size:26px; color:var(--encre); line-height:1; }
.s3-plan svg{ width:100%; height:auto; display:block; }
.s3-plan .note{ font-size:13px; color:#4A453C; margin-top:4px; }
.s3-plan .note b{ color:var(--crayon); }
.st-key-s3_piece_0, .st-key-s3_piece_1, .st-key-s3_piece_2,
.st-key-s3_piece_3, .st-key-s3_piece_4, .st-key-s3_piece_5{
  position:relative; background:linear-gradient(180deg,#FFFDF4,#F7F1DE); border-radius:2px;
  padding:18px 16px 10px; box-shadow:0 14px 28px rgba(0,0,0,.45); margin-top:28px; }
.st-key-s3_piece_0{ transform:rotate(-.5deg); } .st-key-s3_piece_1{ transform:rotate(.45deg); }
.st-key-s3_piece_2{ transform:rotate(-.4deg); } .st-key-s3_piece_3{ transform:rotate(.55deg); }
.st-key-s3_piece_4{ transform:rotate(-.45deg); } .st-key-s3_piece_5{ transform:rotate(.4deg); }
.st-key-s3_piece_0 [data-testid="stMarkdownContainer"] p, .st-key-s3_piece_1 [data-testid="stMarkdownContainer"] p,
.st-key-s3_piece_2 [data-testid="stMarkdownContainer"] p, .st-key-s3_piece_3 [data-testid="stMarkdownContainer"] p,
.st-key-s3_piece_4 [data-testid="stMarkdownContainer"] p, .st-key-s3_piece_5 [data-testid="stMarkdownContainer"] p,
.st-key-s3_piece_0 [data-testid="stMarkdownContainer"] li, .st-key-s3_piece_1 [data-testid="stMarkdownContainer"] li,
.st-key-s3_piece_2 [data-testid="stMarkdownContainer"] li, .st-key-s3_piece_3 [data-testid="stMarkdownContainer"] li,
.st-key-s3_piece_4 [data-testid="stMarkdownContainer"] li, .st-key-s3_piece_5 [data-testid="stMarkdownContainer"] li{ color:var(--encre); }
.st-key-s3_piece_0 [data-testid="stExpander"] summary p, .st-key-s3_piece_1 [data-testid="stExpander"] summary p,
.st-key-s3_piece_2 [data-testid="stExpander"] summary p, .st-key-s3_piece_3 [data-testid="stExpander"] summary p,
.st-key-s3_piece_4 [data-testid="stExpander"] summary p, .st-key-s3_piece_5 [data-testid="stExpander"] summary p,
.st-key-s3_electro_bloc [data-testid="stExpander"] summary p{ color:var(--encre) !important; }
.st-key-s3_piece_0 .stButton > button p, .st-key-s3_piece_1 .stButton > button p,
.st-key-s3_piece_2 .stButton > button p, .st-key-s3_piece_3 .stButton > button p,
.st-key-s3_piece_4 .stButton > button p, .st-key-s3_piece_5 .stButton > button p,
.st-key-s3_electro_bloc .stButton > button p{ color:var(--texte) !important; }
.st-key-s3_piece_0 label p, .st-key-s3_piece_1 label p, .st-key-s3_piece_2 label p,
.st-key-s3_piece_3 label p, .st-key-s3_piece_4 label p, .st-key-s3_piece_5 label p{
  font-family:"Special Elite",monospace; font-size:11.5px; letter-spacing:.1em;
  text-transform:uppercase; color:#4A453C !important; }
.st-key-s3_piece_0 .stTextInput input, .st-key-s3_piece_1 .stTextInput input, .st-key-s3_piece_2 .stTextInput input,
.st-key-s3_piece_3 .stTextInput input, .st-key-s3_piece_4 .stTextInput input, .st-key-s3_piece_5 .stTextInput input{
  background:transparent !important; border:none !important; border-bottom:2px solid #B9B09A !important;
  border-radius:0 !important; box-shadow:none !important; color:var(--encre) !important; font-weight:600; }
.st-key-s3_piece_0 [data-testid="stNumberInput"] > div, .st-key-s3_piece_1 [data-testid="stNumberInput"] > div,
.st-key-s3_piece_2 [data-testid="stNumberInput"] > div, .st-key-s3_piece_3 [data-testid="stNumberInput"] > div,
.st-key-s3_piece_4 [data-testid="stNumberInput"] > div, .st-key-s3_piece_5 [data-testid="stNumberInput"] > div{
  background:transparent; border:none; border-bottom:2px solid #B9B09A; border-radius:0; box-shadow:none; }
.st-key-s3_piece_0 [data-testid="stNumberInput"] input, .st-key-s3_piece_1 [data-testid="stNumberInput"] input,
.st-key-s3_piece_2 [data-testid="stNumberInput"] input, .st-key-s3_piece_3 [data-testid="stNumberInput"] input,
.st-key-s3_piece_4 [data-testid="stNumberInput"] input, .st-key-s3_piece_5 [data-testid="stNumberInput"] input{
  background:transparent !important; color:var(--encre) !important; font-weight:700; }
.s3-piece-nom{ font-family:"Bebas Neue",sans-serif; font-size:25px; color:var(--encre);
  letter-spacing:.05em; line-height:1.05; }
.s3-compte{ font-family:"Special Elite",monospace; font-size:12px; letter-spacing:.06em;
  color:#5A5344; margin-top:2px; }
.s3-tampon{ display:inline-block; transform:rotate(-7deg); border:3px solid; border-radius:6px;
  padding:1px 11px 0; font-family:"Bebas Neue",sans-serif; font-size:18px; letter-spacing:.14em;
  white-space:nowrap; }
.s3-tampon.minimal{ color:#6E6759; border-color:#6E6759; }
.s3-tampon.moyen{ color:var(--vert); border-color:var(--vert); }
.s3-tampon.maximal{ color:#B07B1E; border-color:#C9A227; background:rgba(255,210,63,.18); }
.s3-sous{ display:flex; justify-content:space-between; gap:16px; border-top:2px dashed #B9B09A;
  padding-top:8px; margin-top:2px; font-size:14.5px; color:var(--encre); }
.s3-sous .part{ font-weight:800; }
.st-key-s3_electro_bloc{ position:relative; background:#FFFFFF; border:3px double #4A453C; border-radius:4px;
  padding:18px 18px 10px; margin-top:28px; box-shadow:0 14px 28px rgba(0,0,0,.45); }
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
.s3-recu{ background:#FFFFFF; color:var(--encre); border-radius:3px; padding:18px 22px 14px;
  margin-top:28px; position:relative; box-shadow:0 14px 30px rgba(0,0,0,.45); }
.s3-recu .titre{ font-family:"Bebas Neue",sans-serif; font-size:26px; letter-spacing:.06em; color:var(--encre); }
.s3-jauge{ height:18px; border-radius:999px; background:#E7E0CB; overflow:hidden;
  margin-top:12px; border:1.5px solid #B9B09A; }
.s3-jauge .remplissage{ height:100%; background:linear-gradient(90deg,#2FA84F,#7CC24A); }
.s3-jauge .remplissage.presque{ background:linear-gradient(90deg,#E3B505,#FF7A45); }
.s3-jauge .remplissage.depasse{ background:linear-gradient(90deg,#D93A2B,#B01E12); }
.s3-jauge-txt{ font-size:13.5px; color:#4A453C; margin-top:5px; font-weight:600; }
.s3-jauge-txt b{ color:var(--crayon); }
.st-key-s3_piece_0 [data-testid="stCaptionContainer"] p, .st-key-s3_piece_1 [data-testid="stCaptionContainer"] p,
.st-key-s3_piece_2 [data-testid="stCaptionContainer"] p, .st-key-s3_piece_3 [data-testid="stCaptionContainer"] p,
.st-key-s3_piece_4 [data-testid="stCaptionContainer"] p, .st-key-s3_piece_5 [data-testid="stCaptionContainer"] p,
.st-key-s3_electro_bloc [data-testid="stCaptionContainer"] p{
  color:#4A453C !important; font-family:"Special Elite",monospace; font-size:11.5px;
  letter-spacing:.1em; text-transform:uppercase; }

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
    actif = "sections" if page in ("s1", "s2", "s3") else page
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
    st.markdown(
        "<div class='puces'>"
        f"<div class='puce'>{compte['nom_affiche']} · <b>Cas {compte['cas_numero']} : {profil['prenom']}</b></div>"
        f"<div class='puce'>Groupe {compte['groupe']}</div>"
        "<div class='puce'>Mois de vie : <b>pas encore commencé</b></div>"
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
        "<div class='detail'>C'est ton épargne de départ. Prochain mouvement : "
        "<b>jour 1, paie et loyer</b>, quand le calendrier va commencer.</div></div>"

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
        "</table></div>"

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
        donnees.definir_progression(MAGASIN, compte["identifiant"], "S1", "fait")
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
                donnees.definir_progression(MAGASIN, compte["identifiant"],
                                            "S2", "fait")
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


def _meubles_svg(piece, niveau):
    """Petits meubles dessinés à l'encre pour une pièce du plan, selon le
    niveau atteint : chaque palier ajoute ses meubles (cumulatif)."""
    if piece == donnees.PIECE_COLOC:
        return ("<g fill='none' stroke='#A39B85' stroke-width='2'>"
                "<rect x='172' y='46' width='52' height='28'/>"
                "<rect x='172' y='46' width='52' height='8'/>"
                "<rect x='268' y='52' width='28' height='16'/></g>")
    if niveau is None:
        return ""
    m = []
    if piece == "Ma chambre":
        m += ["<rect x='12' y='42' width='54' height='30'/>",
              "<rect x='12' y='42' width='54' height='9'/>",
              "<rect x='17' y='45' width='14' height='5' fill='#2A2620' stroke='none' opacity='.25'/>",
              "<rect x='104' y='58' width='42' height='18'/>",
              "<line x1='118' y1='76' x2='118' y2='82'/>",
              "<line x1='138' y1='76' x2='138' y2='82'/>"]
        if niveau in ("MOYEN", "MAXIMAL"):
            m += ["<rect x='104' y='36' width='42' height='18'/>",
                  "<line x1='104' y1='45' x2='146' y2='45'/>",
                  "<line x1='136' y1='58' x2='136' y2='47'/>",
                  "<polygon points='130,47 142,47 139,41 133,41'/>"]
        if niveau == "MAXIMAL":
            m += ["<ellipse cx='58' cy='79' rx='36' ry='5'/>",
                  "<circle cx='147' cy='17' r='6.5'/>"]
    elif piece == "Cuisine":
        m += ["<rect x='76' y='116' width='106' height='9'/>",
              "<rect x='86' y='117' width='15' height='7'/>",
              "<rect x='148' y='128' width='32' height='32'/>",
              "<circle cx='157' cy='137' r='4'/><circle cx='171' cy='137' r='4'/>",
              "<circle cx='157' cy='150' r='4'/><circle cx='171' cy='150' r='4'/>"]
        if niveau in ("MOYEN", "MAXIMAL"):
            m += ["<rect x='78' y='126' width='22' height='36'/>",
                  "<line x1='78' y1='136' x2='100' y2='136'/>",
                  "<rect x='110' y='134' width='28' height='18'/>",
                  "<rect x='104' y='138' width='5' height='10'/>",
                  "<rect x='139' y='138' width='5' height='10'/>"]
        if niveau == "MAXIMAL":
            m += ["<rect x='158' y='107' width='17' height='9'/>",
                  "<rect x='140' y='108' width='8' height='8'/>"]
    elif piece == "Salon":
        m += ["<rect x='196' y='142' width='48' height='12'/>",
              "<line x1='196' y1='147' x2='244' y2='147'/>",
              "<line x1='310' y1='134' x2='310' y2='152'/>",
              "<polygon points='304,134 316,134 313,128 307,128'/>"]
        if niveau in ("MOYEN", "MAXIMAL"):
            m += ["<rect x='232' y='157' width='22' height='4'/>",
                  "<rect x='256' y='144' width='18' height='16'/>",
                  "<line x1='256' y1='152' x2='274' y2='152'/>"]
        if niveau == "MAXIMAL":
            m += ["<rect x='284' y='130' width='24' height='14'/>",
                  "<rect x='290' y='144' width='12' height='4'/>",
                  "<ellipse cx='262' cy='161' rx='20' ry='2.5'/>",
                  "<rect x='200' y='144' width='7' height='7'/>",
                  "<rect x='230' y='144' width='7' height='7'/>"]
    elif piece == "Salle de bain":
        m += ["<rect x='9' y='118' width='52' height='21' rx='9'/>",
              "<line x1='55' y1='118' x2='55' y2='113'/>",
              "<rect x='10' y='146' width='15' height='11'/>"]
        if niveau in ("MOYEN", "MAXIMAL"):
            m += ["<rect x='32' y='144' width='13' height='13'/>",
                  "<ellipse cx='38.5' cy='144' rx='6.5' ry='3'/>",
                  "<rect x='50' y='140' width='13' height='17'/>"]
        if niveau == "MAXIMAL":
            m += ["<line x1='54' y1='114' x2='54' y2='128'/>",
                  "<line x1='60' y1='114' x2='60' y2='128'/>",
                  "<line x1='54' y1='120' x2='60' y2='120'/>",
                  "<rect x='40' y='122' width='20' height='7'/>"]
    elif piece == "Entrée et rangement":
        m += ["<line x1='210' y1='94' x2='210' y2='120'/>",
              "<line x1='210' y1='99' x2='217' y2='96'/>",
              "<line x1='210' y1='107' x2='217' y2='104'/>",
              "<line x1='210' y1='115' x2='217' y2='112'/>",
              "<rect x='238' y='116' width='58' height='8'/>"]
        if niveau in ("MOYEN", "MAXIMAL"):
            m += ["<rect x='296' y='94' width='17' height='24'/>",
                  "<line x1='296' y1='102' x2='313' y2='102'/>",
                  "<line x1='296' y1='110' x2='313' y2='110'/>",
                  "<line x1='228' y1='100' x2='222' y2='118'/>",
                  "<rect x='218' y='116' width='8' height='5'/>"]
        if niveau == "MAXIMAL":
            m += ["<rect x='246' y='94' width='19' height='9'/>",
                  "<rect x='249' y='87' width='14' height='7'/>"]
    return ("<g fill='none' stroke='#2A2620' stroke-width='2'>"
            + "".join(m) + "</g>")


# (pièce, libellé sur le plan, x du nom, y du nom, x du niveau, y du niveau)
_PLAN_PIECES = [
    ("Ma chambre", "ma chambre", 12, 20, 12, 33),
    (donnees.PIECE_COLOC, None, 162, 20, 162, 33),
    ("Salle de bain", "bain", 10, 101, 10, 114),
    ("Cuisine", "cuisine", 78, 101, 78, 114),
    ("Entrée et rangement", "entrée", 194, 100, 194, 113),
    ("Salon", "salon", 194, 139, 194, 162),
]
_COULEURS_NIVEAU = {None: "#A39B85", "MINIMAL": "#6E6759",
                    "MOYEN": "#1E9E4A", "MAXIMAL": "#B07B1E"}


def html_plan_s3(brouillon, profil):
    """Le plan de l'appartement, dessiné à l'encre : les pièces se
    meublent à mesure que leur niveau monte."""
    murs = (
        "<g fill='none' stroke='#2A2620' stroke-width='3'>"
        "<rect x='4' y='4' width='312' height='160'/><rect x='4' y='4' width='150' height='82'/>"
        "<rect x='154' y='4' width='162' height='82'/><rect x='4' y='86' width='66' height='78'/>"
        "<rect x='70' y='86' width='118' height='78'/><rect x='188' y='86' width='128' height='40'/>"
        "<rect x='188' y='126' width='128' height='38'/></g>")
    morceaux = [murs]
    for piece, libelle, nx, ny, lx, ly in _PLAN_PIECES:
        if piece == donnees.PIECE_COLOC:
            nom = profil["coloc"]["prenom"]
            niveau = None
            texte_niveau = "il apporte ses meubles"
        else:
            nom = libelle
            nombre = donnees.articles_nommes(brouillon["pieces"][piece])
            niveau = donnees.niveau_s3(nombre, donnees.SEUILS_S3[piece])
            texte_niveau = niveau if niveau else "à meubler"
        morceaux.append(_meubles_svg(piece, niveau))
        morceaux.append(
            f"<text x='{nx}' y='{ny}' font-family='Caveat, cursive' "
            f"font-size='18' fill='#2A2620'>{nom}</text>")
        morceaux.append(
            f"<text x='{lx}' y='{ly}' font-family='Work Sans, sans-serif' "
            f"font-size='9.5' font-weight='700' letter-spacing='1' "
            f"fill='{_COULEURS_NIVEAU[niveau]}'>{texte_niveau}</text>")
    svg = ("<svg viewBox='0 0 320 168' width='100%' height='auto' "
           "aria-label='Plan de l appartement qui se meuble'>"
           + "".join(morceaux) + "</svg>")
    return ("<div class='s3-plan'><div class='pf-ruban'></div>"
            "<div class='titre'>Ton appart, vu d'en haut</div>"
            + svg +
            "<div class='note'>Chaque pièce se meuble quand son niveau monte : "
            "<b>MINIMAL</b> elle fonctionne, <b>MOYEN</b> elle est complète "
            "(c'est le niveau visé), <b>MAXIMAL</b> le confort est là.</div></div>")


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
            for champ in ("nom", "prix", "etat", "type"):
                cle = f"s3_p{i}_{champ}_{j}_g{gen}"
                if cle in etat:
                    article[champ] = etat[cle]
            if piece == "Ma chambre":
                article["type"] = "personnel"
    for j, article in enumerate(brouillon["electro"]):
        for champ in ("nom", "prix", "etat", "capture"):
            cle = f"s3_e_{champ}_{j}_g{gen}"
            if cle in etat:
                article[champ] = etat[cle]
    if "s3_note_coloc" in etat:
        brouillon["note_coloc"] = etat["s3_note_coloc"]


def _tampon_html(niveau):
    if niveau is None:
        return ""
    return f"<div class='s3-tampon {niveau.lower()}'>{niveau}</div>"


def page_s3(compte, dossier, profil):
    if st.button("Retour à l'accueil"):
        aller("accueil")
    brouillon = _init_brouillon_s3(compte, dossier)
    gen = _s3_gen()
    deja_fait = dossier.get("progression", {}).get("S3") == "fait"

    st.markdown(
        "<div class='s3-bandeau'>"
        "<div class='chantier'>JOUR D'EMMÉNAGEMENT · LES BOÎTES SONT DANS L'ENTRÉE</div>"
        "<div class='titre'>S3 · MEUBLER <span>L'APPART</span></div>"
        "<div class='aide'>Plafond d'installation : 3 500 $ pour tout meubler, "
        "ta part seulement. Meuble chaque pièce jusqu'au niveau MOYEN : c'est "
        "le niveau visé. Tu choisis tes articles librement ; les idées de "
        "chaque bon sont là pour t'inspirer, pas pour être copiées. "
        "La chambre de ton coloc ne te coûte rien : il apporte ses meubles.</div></div>",
        unsafe_allow_html=True)
    if deja_fait:
        st.success("Tu as déjà meublé ton appartement. Tu peux quand même "
                   "modifier tes bons et réenregistrer.")

    st.markdown(html_plan_s3(brouillon, profil), unsafe_allow_html=True)

    aimants = ["pf-arouge", "pf-ableu", "pf-ajaune", "pf-avert", "pf-arouge", "pf-ableu"]
    for i, piece in enumerate(donnees.PIECES):
        with st.container(key=f"s3_piece_{i}"):
            st.markdown(f"<div class='pf-aimant {aimants[i]}'></div>",
                        unsafe_allow_html=True)
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
            nombre = donnees.articles_nommes(articles)
            seuils = donnees.SEUILS_S3[piece]
            niveau = donnees.niveau_s3(nombre, seuils)
            col_nom, col_tampon = st.columns([3, 1])
            with col_nom:
                st.markdown(
                    f"<div class='s3-piece-nom'>{piece}</div>"
                    f"<div class='s3-compte'>{nombre} ARTICLE(S) · MINIMAL À {seuils[0]}"
                    f" · MOYEN À {seuils[1]} · MAXIMAL À {seuils[2]}</div>",
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
            with st.expander(f"Idées d'articles pour {piece.lower()}"):
                st.write(" · ".join(IDEES_S3[piece]))

    with st.container(key="s3_electro_bloc"):
        electro = brouillon["electro"]
        nombre_e = donnees.articles_nommes(electro)
        niveau_e = donnees.niveau_s3(nombre_e, donnees.SEUILS_ELECTRO)
        col_nom, col_tampon = st.columns([3, 1])
        with col_nom:
            st.markdown(
                "<div class='s3-piece-nom'>Électroménagers · la facture</div>"
                f"<div class='s3-compte'>{nombre_e} ARTICLE(S) · MINIMAL À "
                f"{donnees.SEUILS_ELECTRO[0]} · MOYEN À {donnees.SEUILS_ELECTRO[1]}"
                f" · MAXIMAL À {donnees.SEUILS_ELECTRO[2]} · COÛT PARTAGÉ, TA PART 50 %</div>",
                unsafe_allow_html=True)
        with col_tampon:
            st.markdown(_tampon_html(niveau_e), unsafe_allow_html=True)
        entetes = st.columns([3.0, 1.2, 1.1, 1.8, 0.9])
        for col, texte in zip(entetes, ["Article", "Prix ($)", "État", "Capture", ""]):
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
                st.text_input("Capture", value=article.get("capture") or "",
                              key=f"s3_e_capture_{j}_g{gen}",
                              label_visibility="collapsed",
                              placeholder="Nom du fichier de capture")
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
    st.markdown(
        "<div class='s3-recu'><div class='pf-aimant pf-arouge'></div>"
        "<div class='titre'>LE REÇU DE L'INSTALLATION</div>"
        + "".join(lignes_recu)
        + f"<div class='s3-jauge'><div class='remplissage {classe_jauge}' "
        + f"style='width:{pct:.1f}%'></div></div>"
        + f"<div class='s3-jauge-txt'>{fmt_montant(total)} sur 3 500,00 $ de plafond"
        + (f" · <b>dépassé de {fmt_montant(total - donnees.PLAFOND_INSTALLATION)}</b>"
           if total > donnees.PLAFOND_INSTALLATION else "")
        + "</div></div>",
        unsafe_allow_html=True)

    col_enr, col_fin = st.columns(2)
    with col_enr:
        if st.button("Enregistrer", use_container_width=True):
            _synchroniser_s3(brouillon)
            donnees.enregistrer_s3(MAGASIN, compte["identifiant"], brouillon)
            st.success("Tes bons de commande sont enregistrés.")
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
                donnees.definir_progression(MAGASIN, compte["identifiant"],
                                            "S3", "fait")
                st.success("S3 terminée. Ton appart est meublé, bon emménagement!")
                aller("accueil")


def page_sections(compte, dossier, profil):
    st.markdown("<section class='carte'><h2>Mes sections</h2>"
                "<div class='aide'>Ton travail, section par section. "
                "La S1, la S2 et la S3 sont prêtes ; les autres arrivent plus tard.</div></section>",
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
            if code in ("S1", "S2", "S3"):
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
    elif page == "s2":
        page_s2(compte, dossier, profil)
    elif page == "s3":
        page_s3(compte, dossier, profil)
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

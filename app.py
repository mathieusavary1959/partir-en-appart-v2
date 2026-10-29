"""Partir en appart! v2 : application Streamlit (phase P1, univers figé).

Univers figé le 28 octobre 2026 : « la porte de frigo » (voir la charte
files/charte-univers-frigo.md du dossier du projet et la maquette v7).
Inscription avec mot de passe, connexion, accueil en porte de frigo,
section S1 en lecture et section S2 (les 3 annonces comparées, le choix,
la justification, la capture) fonctionnelles, progression sauvegardée.
Le calendrier de vie, la console du prof et les sections S3 à S7
arrivent aux phases suivantes.
La couche de données vit dans donnees.py (magasin mémoire ou Supabase REST).
"""
import streamlit as st

import donnees

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
    actif = "sections" if page in ("s1", "s2") else page
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
                aller(courante.lower() if courante in ("S1", "S2") else "sections")
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


def page_sections(compte, dossier, profil):
    st.markdown("<section class='carte'><h2>Mes sections</h2>"
                "<div class='aide'>Ton travail, section par section. "
                "La S1 et la S2 sont prêtes ; les autres arrivent plus tard.</div></section>",
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
            if code in ("S1", "S2"):
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

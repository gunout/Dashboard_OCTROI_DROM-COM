# dashboard_octroi_mer_drom_com_fixed.py
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import time
import random
import warnings
from functools import lru_cache
warnings.filterwarnings('ignore')

# Configuration de la page
st.set_page_config(
    page_title="Dashboard Octroi de Mer - DROM-COM",
    page_icon="🏝️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personnalisé
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        background: linear-gradient(45deg, #0055A4, #EF4135, #FFD700);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 2rem;
        font-weight: bold;
    }
    .live-badge {
        background: linear-gradient(45deg, #0055A4, #00A3E0);
        color: white;
        padding: 0.3rem 1rem;
        border-radius: 20px;
        font-weight: bold;
        display: inline-block;
        animation: pulse 2s infinite;
    }
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.05); }
        100% { transform: scale(1); }
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #0055A4;
        margin: 0.5rem 0;
    }
    .section-header {
        color: #0055A4;
        border-bottom: 2px solid #EF4135;
        padding-bottom: 0.5rem;
        margin-top: 2rem;
    }
    .sector-card {
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        border-left: 5px solid #0055A4;
        background-color: #f8f9fa;
    }
    .revenue-change {
        padding: 0.5rem;
        border-radius: 5px;
        margin: 0.2rem 0;
        font-size: 0.9rem;
        font-weight: bold;
    }
    .positive { background-color: #d4edda; border-left: 4px solid #28a745; color: #155724; }
    .negative { background-color: #f8d7da; border-left: 4px solid #dc3545; color: #721c24; }
    .neutral { background-color: #e2e3e5; border-left: 4px solid #6c757d; color: #383d41; }
    .sector-badge {
        display: inline-block;
        padding: 0.25rem 0.5rem;
        border-radius: 15px;
        font-size: 0.75rem;
        font-weight: 600;
        margin-right: 0.5rem;
        margin-bottom: 0.5rem;
    }
    .territory-flag {
        padding: 0.5rem 1rem;
        border-radius: 10px;
        text-align: center;
        margin: 1rem 0;
        color: white;
    }
    .reunion-flag { background: linear-gradient(90deg, #0055A4 33%, #EF4135 33%, #EF4135 66%, #FFFFFF 66%); }
    .guadeloupe-flag { background: linear-gradient(90deg, #ED2939 50%, #002395 50%); }
    .martinique-flag { background: linear-gradient(90deg, #009739 33%, #002395 33%, #002395 66%, #FCD116 66%); }
    .guyane-flag { background: linear-gradient(90deg, #009739 50%, #FCD116 50%); }
    .mayotte-flag { background: linear-gradient(90deg, #FFFFFF 25%, #ED2939 25%, #ED2939 50%, #002395 50%, #002395 75%, #FCD116 75%); }
    .spierre-flag { background: linear-gradient(90deg, #002395 33%, #FFFFFF 33%, #FFFFFF 66%, #ED2939 66%); }
    .stbarth-flag { background: linear-gradient(90deg, #FFFFFF 50%, #FCD116 50%); }
    .stmartin-flag { background: linear-gradient(90deg, #ED2939 50%, #002395 50%); }
    .wallis-flag { background: linear-gradient(90deg, #ED2939 33%, #002395 33%, #002395 66%, #FCD116 66%); }
    .polynesie-flag { background: linear-gradient(90deg, #ED2939 25%, #FFFFFF 25%, #FFFFFF 50%, #FCD116 50%, #FCD116 75%, #002395 75%); }
    .caledonie-flag { background: linear-gradient(90deg, #002395 33%, #FCD116 33%, #FCD116 66%, #ED2939 66%); }
    .territory-selector {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        border: 2px solid #0055A4;
        margin-bottom: 1rem;
    }
    .loading-spinner {
        display: flex;
        justify-content: center;
        align-items: center;
        height: 200px;
    }
</style>
""", unsafe_allow_html=True)

# Initialisation de l'état de session
if 'territories_data' not in st.session_state:
    st.session_state.territories_data = {}
if 'selected_territory' not in st.session_state:
    st.session_state.selected_territory = 'REUNION'
if 'last_update' not in st.session_state:
    st.session_state.last_update = datetime.now()

# Fonctions globales avec cache pour éviter les problèmes de hashage
@st.cache_data(ttl=3600)
def get_territories_definitions():
    """Définit les territoires DROM-COM"""
    return {
        'REUNION': {
            'nom_complet': 'La Réunion',
            'type': 'DROM',
            'population': 860000,
            'superficie': 2511,
            'pib': 19.8,
            'drapeau': 'reunion-flag',
            'monnaie': 'EUR',
            'taux_octroi_actif': True
        },
        'GUADELOUPE': {
            'nom_complet': 'Guadeloupe',
            'type': 'DROM',
            'population': 384000,
            'superficie': 1628,
            'pib': 9.1,
            'drapeau': 'guadeloupe-flag',
            'monnaie': 'EUR',
            'taux_octroi_actif': True
        },
        'MARTINIQUE': {
            'nom_complet': 'Martinique',
            'type': 'DROM',
            'population': 376000,
            'superficie': 1128,
            'pib': 8.9,
            'drapeau': 'martinique-flag',
            'monnaie': 'EUR',
            'taux_octroi_actif': True
        },
        'GUYANE': {
            'nom_complet': 'Guyane',
            'type': 'DROM',
            'population': 290000,
            'superficie': 83534,
            'pib': 4.8,
            'drapeau': 'guyane-flag',
            'monnaie': 'EUR',
            'taux_octroi_actif': True
        },
        'MAYOTTE': {
            'nom_complet': 'Mayotte',
            'type': 'DROM',
            'population': 270000,
            'superficie': 374,
            'pib': 2.4,
            'drapeau': 'mayotte-flag',
            'monnaie': 'EUR',
            'taux_octroi_actif': True
        },
        'STPIERRE': {
            'nom_complet': 'Saint-Pierre-et-Miquelon',
            'type': 'COM',
            'population': 6000,
            'superficie': 242,
            'pib': 0.2,
            'drapeau': 'spierre-flag',
            'monnaie': 'EUR',
            'taux_octroi_actif': True
        },
        'STBARTH': {
            'nom_complet': 'Saint-Barthélemy',
            'type': 'COM',
            'population': 10000,
            'superficie': 21,
            'pib': 0.6,
            'drapeau': 'stbarth-flag',
            'monnaie': 'EUR',
            'taux_octroi_actif': False
        },
        'STMARTIN': {
            'nom_complet': 'Saint-Martin',
            'type': 'COM',
            'population': 32000,
            'superficie': 54,
            'pib': 0.9,
            'drapeau': 'stmartin-flag',
            'monnaie': 'EUR',
            'taux_octroi_actif': False
        },
        'WALLIS': {
            'nom_complet': 'Wallis-et-Futuna',
            'type': 'COM',
            'population': 11500,
            'superficie': 142,
            'pib': 0.2,
            'drapeau': 'wallis-flag',
            'monnaie': 'XPF',
            'taux_octroi_actif': True
        },
        'POLYNESIE': {
            'nom_complet': 'Polynésie française',
            'type': 'COM',
            'population': 280000,
            'superficie': 4167,
            'pib': 7.2,
            'drapeau': 'polynesie-flag',
            'monnaie': 'XPF',
            'taux_octroi_actif': True
        },
        'CALEDONIE': {
            'nom_complet': 'Nouvelle-Calédonie',
            'type': 'COM',
            'population': 271000,
            'superficie': 18575,
            'pib': 9.7,
            'drapeau': 'caledonie-flag',
            'monnaie': 'XPF',
            'taux_octroi_actif': True
        }
    }

@st.cache_data(ttl=3600)
def get_secteurs_definitions(territory_code):
    """Définit les secteurs économiques pour un territoire donné"""
    # Facteurs d'ajustement selon le territoire
    territory_factor = {
        'REUNION': 1.0,
        'GUADELOUPE': 0.95,
        'MARTINIQUE': 0.9,
        'GUYANE': 0.7,
        'MAYOTTE': 0.5,
        'STPIERRE': 0.3,
        'STBARTH': 0.4,
        'STMARTIN': 0.45,
        'WALLIS': 0.25,
        'POLYNESIE': 0.8,
        'CALEDONIE': 0.85
    }
    
    factor = territory_factor.get(territory_code, 1.0)
    
    # Secteurs de base avec ajustements selon le territoire
    secteurs_base = {
        'AGRICULTURE': {
            'nom_complet': 'Produits Agricoles',
            'categorie': 'Alimentation',
            'sous_categorie': 'Fruits & Légumes',
            'taux_normal': 2.5,
            'taux_reduit': 1.3,
            'taux_specifique': 0.0,
            'couleur': '#28a745',
            'poids_total': 15.2 * factor,
            'volume_importation': 450000 * factor,
            'description': 'Fruits, légumes, produits agricoles frais'
        },
        'AGROALIMENTAIRE': {
            'nom_complet': 'Industrie Agroalimentaire',
            'categorie': 'Alimentation',
            'sous_categorie': 'Produits Transformés',
            'taux_normal': 3.2,
            'taux_reduit': 1.8,
            'taux_specifique': 0.5,
            'couleur': '#20c997',
            'poids_total': 22.8 * factor,
            'volume_importation': 320000 * factor,
            'description': 'Produits alimentaires transformés'
        },
        'BOISSONS': {
            'nom_complet': 'Boissons et Alcools',
            'categorie': 'Alimentation',
            'sous_categorie': 'Liquides',
            'taux_normal': 5.8,
            'taux_reduit': 3.2,
            'taux_specifique': 8.5,
            'couleur': '#fd7e14',
            'poids_total': 8.5 * factor,
            'volume_importation': 180000 * factor,
            'description': 'Boissons alcoolisées et non-alcoolisées'
        },
        'BTP': {
            'nom_complet': 'Matériaux de Construction',
            'categorie': 'Industrie',
            'sous_categorie': 'Matériaux',
            'taux_normal': 4.2,
            'taux_reduit': 2.1,
            'taux_specifique': 1.5,
            'couleur': '#6f42c1',
            'poids_total': 12.3 * factor,
            'volume_importation': 280000 * factor,
            'description': 'Ciment, fer, matériaux construction'
        },
        'AUTOMOBILE': {
            'nom_complet': 'Véhicules et Pièces',
            'categorie': 'Transport',
            'sous_categorie': 'Véhicules',
            'taux_normal': 6.5,
            'taux_reduit': 3.8,
            'taux_specifique': 12.2,
            'couleur': '#dc3545',
            'poids_total': 9.8 * factor,
            'volume_importation': 75000 * factor,
            'description': 'Voitures, pièces détachées'
        },
        'ENERGIE': {
            'nom_complet': 'Produits Pétroliers',
            'categorie': 'Énergie',
            'sous_categorie': 'Carburants',
            'taux_normal': 3.8,
            'taux_reduit': 2.2,
            'taux_specifique': 0.8,
            'couleur': '#ffc107',
            'poids_total': 14.7 * factor,
            'volume_importation': 420000 * factor,
            'description': 'Carburants, lubrifiants'
        },
        'BIENS_EQUIPEMENT': {
            'nom_complet': 'Biens d\'Équipement',
            'categorie': 'Industrie',
            'sous_categorie': 'Machines',
            'taux_normal': 4.8,
            'taux_reduit': 2.9,
            'taux_specifique': 3.2,
            'couleur': '#6610f2',
            'poids_total': 7.2 * factor,
            'volume_importation': 95000 * factor,
            'description': 'Machines, équipements industriels'
        },
        'BIENS_CONSOMMATION': {
            'nom_complet': 'Biens de Consommation',
            'categorie': 'Commerce',
            'sous_categorie': 'Divers',
            'taux_normal': 5.2,
            'taux_reduit': 3.1,
            'taux_specifique': 4.5,
            'couleur': '#e83e8c',
            'poids_total': 16.5 * factor,
            'volume_importation': 210000 * factor,
            'description': 'Électroménager, meubles, textiles'
        },
        'PHARMACEUTIQUE': {
            'nom_complet': 'Produits Pharmaceutiques',
            'categorie': 'Santé',
            'sous_categorie': 'Médicaments',
            'taux_normal': 1.2,
            'taux_reduit': 0.8,
            'taux_specifique': 0.3,
            'couleur': '#0066CC',
            'poids_total': 4.8 * factor,
            'volume_importation': 65000 * factor,
            'description': 'Médicaments, produits santé'
        },
        'TIC': {
            'nom_complet': 'Technologies Information',
            'categorie': 'High-Tech',
            'sous_categorie': 'Électronique',
            'taux_normal': 4.5,
            'taux_reduit': 2.7,
            'taux_specifique': 6.8,
            'couleur': '#17a2b8',
            'poids_total': 5.2 * factor,
            'volume_importation': 88000 * factor,
            'description': 'Ordinateurs, téléphones, électronique'
        }
    }
    
    # Ajustements spécifiques selon le territoire
    if territory_code == 'POLYNESIE':
        secteurs_base['TOURISME'] = {
            'nom_complet': 'Tourisme et Hôtellerie',
            'categorie': 'Services',
            'sous_categorie': 'Tourisme',
            'taux_normal': 3.5,
            'taux_reduit': 1.5,
            'taux_specifique': 0.0,
            'couleur': '#0077be',
            'poids_total': 18.0 * factor,
            'volume_importation': 150000 * factor,
            'description': 'Équipements touristiques, produits pour hôtellerie'
        }
    
    elif territory_code == 'CALEDONIE':
        secteurs_base['MINIER'] = {
            'nom_complet': 'Industrie Minière',
            'categorie': 'Industrie',
            'sous_categorie': 'Mines',
            'taux_normal': 2.8,
            'taux_reduit': 1.2,
            'taux_specifique': 0.0,
            'couleur': '#8B4513',
            'poids_total': 15.0 * factor,
            'volume_importation': 120000 * factor,
            'description': 'Équipements miniers, produits métallurgiques'
        }
    
    elif territory_code == 'GUYANE':
        secteurs_base['SPATIAL'] = {
            'nom_complet': 'Industrie Spatiale',
            'categorie': 'High-Tech',
            'sous_categorie': 'Aérospatiale',
            'taux_normal': 1.5,
            'taux_reduit': 0.5,
            'taux_specifique': 0.0,
            'couleur': '#1a1a2e',
            'poids_total': 8.0 * factor,
            'volume_importation': 50000 * factor,
            'description': 'Équipements spatiaux, technologies aérospatiales'
        }
    
    elif territory_code in ['STBARTH', 'STMARTIN']:
        secteurs_base['LUXE'] = {
            'nom_complet': 'Produits de Luxe',
            'categorie': 'Commerce',
            'sous_categorie': 'Luxe',
            'taux_normal': 6.0,
            'taux_reduit': 3.0,
            'taux_specifique': 8.0,
            'couleur': '#c0c0c0',
            'poids_total': 20.0 * factor,
            'volume_importation': 80000 * factor,
            'description': 'Produits de luxe, montres, bijoux, haute couture'
        }
    
    return secteurs_base

@st.cache_data(ttl=1800)
def generate_historical_data(territory_code, secteurs):
    """Génère les données historiques optimisées"""
    dates = pd.date_range('2022-01-01', datetime.now(), freq='M')
    data = []
    
    for date in dates:
        # Impact COVID simplifié
        if date.year == 2022:
            covid_impact = random.uniform(0.9, 1.1)
        else:
            covid_impact = random.uniform(1.0, 1.2)
        
        # Variation saisonnière
        if territory_code in ['REUNION', 'MAYOTTE']:
            if date.month in [12, 1, 2]:
                seasonal_impact = random.uniform(1.1, 1.3)
            elif date.month in [6, 7, 8]:
                seasonal_impact = random.uniform(0.9, 1.1)
            else:
                seasonal_impact = random.uniform(0.95, 1.05)
        else:
            if date.month in [6, 7, 8]:
                seasonal_impact = random.uniform(1.1, 1.3)
            elif date.month in [12, 1, 2]:
                seasonal_impact = random.uniform(0.9, 1.1)
            else:
                seasonal_impact = random.uniform(0.95, 1.05)
        
        for secteur_code, info in secteurs.items():
            base_revenue = info['poids_total'] * random.uniform(0.8, 1.2) * 1000000
            revenu = base_revenue * covid_impact * seasonal_impact * random.uniform(0.95, 1.05)
            volume = info['volume_importation'] * random.uniform(0.8, 1.2)
            
            data.append({
                'date': date,
                'territoire': territory_code,
                'secteur': secteur_code,
                'revenu_octroi': revenu,
                'volume_importation': volume,
                'categorie': info['categorie'],
                'taux_moyen': info['taux_normal'] * random.uniform(0.9, 1.1)
            })
    
    return pd.DataFrame(data)

@st.cache_data(ttl=300)
def generate_current_data(territory_code, secteurs, historical_data):
    """Génère les données courantes optimisées"""
    current_data = []
    
    for secteur_code, info in secteurs.items():
        # Dernières données historiques
        last_data = historical_data[historical_data['secteur'] == secteur_code].iloc[-1]
        
        # Variation mensuelle simulée
        change_pct = random.uniform(-0.08, 0.08)
        change_abs = last_data['revenu_octroi'] * change_pct
        
        current_data.append({
            'territoire': territory_code,
            'secteur': secteur_code,
            'nom_complet': info['nom_complet'],
            'categorie': info['categorie'],
            'revenu_mensuel': last_data['revenu_octroi'] + change_abs,
            'variation_pct': change_pct * 100,
            'variation_abs': change_abs,
            'volume_importation': info['volume_importation'] * random.uniform(0.8, 1.2),
            'taux_normal': info['taux_normal'],
            'taux_reduit': info['taux_reduit'],
            'taux_specifique': info['taux_specifique'],
            'poids_total': info['poids_total'],
            'revenu_annee_precedente': last_data['revenu_octroi'] * random.uniform(0.9, 1.1),
            'projection_annee_courante': last_data['revenu_octroi'] * random.uniform(1.05, 1.15)
        })
    
    return pd.DataFrame(current_data)

@st.cache_data(ttl=600)
def generate_product_data(territory_code):
    """Génère les données par produit optimisées"""
    produits_base = [
        {'produit': 'Véhicules particuliers', 'secteur': 'AUTOMOBILE', 'taux_octroi': 12.2, 'volume': 12000},
        {'produit': 'Carburants', 'secteur': 'ENERGIE', 'taux_octroi': 2.2, 'volume': 420000},
        {'produit': 'Boissons alcoolisées', 'secteur': 'BOISSONS', 'taux_octroi': 8.5, 'volume': 85000},
        {'produit': 'Matériaux construction', 'secteur': 'BTP', 'taux_octroi': 2.1, 'volume': 280000},
        {'produit': 'Produits alimentaires', 'secteur': 'AGROALIMENTAIRE', 'taux_octroi': 1.8, 'volume': 320000},
        {'produit': 'Fruits et légumes', 'secteur': 'AGRICULTURE', 'taux_octroi': 1.3, 'volume': 450000},
        {'produit': 'Équipements électroniques', 'secteur': 'TIC', 'taux_octroi': 2.7, 'volume': 88000},
        {'produit': 'Médicaments', 'secteur': 'PHARMACEUTIQUE', 'taux_octroi': 0.8, 'volume': 65000},
        {'produit': 'Meubles et ameublement', 'secteur': 'BIENS_CONSOMMATION', 'taux_octroi': 3.1, 'volume': 45000},
        {'produit': 'Machines industrielles', 'secteur': 'BIENS_EQUIPEMENT', 'taux_octroi': 2.9, 'volume': 35000},
    ]
    
    # Ajout de produits spécifiques selon le territoire
    if territory_code == 'POLYNESIE':
        produits_base.extend([
            {'produit': 'Équipements hôteliers', 'secteur': 'TOURISME', 'taux_octroi': 1.5, 'volume': 25000},
            {'produit': 'Produits de plage', 'secteur': 'TOURISME', 'taux_octroi': 3.0, 'volume': 15000},
            {'produit': 'Matériel de plongée', 'secteur': 'TOURISME', 'taux_octroi': 2.5, 'volume': 8000}
        ])
    
    elif territory_code == 'CALEDONIE':
        produits_base.extend([
            {'produit': 'Équipements miniers', 'secteur': 'MINIER', 'taux_octroi': 1.2, 'volume': 12000},
            {'produit': 'Produits métallurgiques', 'secteur': 'MINIER', 'taux_octroi': 2.8, 'volume': 18000}
        ])
    
    elif territory_code == 'GUYANE':
        produits_base.extend([
            {'produit': 'Composants spatiaux', 'secteur': 'SPATIAL', 'taux_octroi': 0.5, 'volume': 5000},
            {'produit': 'Équipements de télécommunication', 'secteur': 'SPATIAL', 'taux_octroi': 1.0, 'volume': 8000}
        ])
    
    elif territory_code in ['STBARTH', 'STMARTIN']:
        produits_base.extend([
            {'produit': 'Montres de luxe', 'secteur': 'LUXE', 'taux_octroi': 6.0, 'volume': 2000},
            {'produit': 'Bijoux précieux', 'secteur': 'LUXE', 'taux_octroi': 8.0, 'volume': 1500},
            {'produit': 'Haute couture', 'secteur': 'LUXE', 'taux_octroi': 5.0, 'volume': 3000}
        ])
    
    # Ajustement des volumes selon le territoire
    territory_factor = {
        'REUNION': 1.0, 'GUADELOUPE': 0.95, 'MARTINIQUE': 0.9, 'GUYANE': 0.7,
        'MAYOTTE': 0.5, 'STPIERRE': 0.3, 'STBARTH': 0.4, 'STMARTIN': 0.45,
        'WALLIS': 0.25, 'POLYNESIE': 0.8, 'CALEDONIE': 0.85
    }
    
    factor = territory_factor.get(territory_code, 1.0)
    for produit in produits_base:
        produit['volume'] *= factor
    
    return pd.DataFrame(produits_base)

@st.cache_data(ttl=3600)
def generate_comparison_data(territories):
    """Génère les données de comparaison entre territoires"""
    comparison_data = []
    
    for territory_code, territory_info in territories.items():
        if not territory_info['taux_octroi_actif']:
            continue
            
        secteurs = get_secteurs_definitions(territory_code)
        total_revenue = sum(
            secteur_info['poids_total'] * random.uniform(0.8, 1.2) * 1000000
            for secteur_info in secteurs.values()
        )
        
        comparison_data.append({
            'territoire': territory_code,
            'nom_complet': territory_info['nom_complet'],
            'type': territory_info['type'],
            'population': territory_info['population'],
            'superficie': territory_info['superficie'],
            'pib': territory_info['pib'],
            'revenu_octroi_total': total_revenue,
            'revenu_par_habitant': total_revenue / territory_info['population'],
            'taux_octroi_actif': territory_info['taux_octroi_actif']
        })
    
    return pd.DataFrame(comparison_data)

class OctroiMerDashboard:
    def __init__(self):
        self.territories = get_territories_definitions()
        
    def get_territory_data(self, territory_code):
        """Récupère les données d'un territoire avec cache"""
        if territory_code not in st.session_state.territories_data:
            with st.spinner(f"Chargement des données pour {self.territories[territory_code]['nom_complet']}..."):
                secteurs = get_secteurs_definitions(territory_code)
                historical_data = generate_historical_data(territory_code, secteurs)
                current_data = generate_current_data(territory_code, secteurs, historical_data)
                product_data = generate_product_data(territory_code)
                
                st.session_state.territories_data[territory_code] = {
                    'secteurs': secteurs,
                    'historical_data': historical_data,
                    'current_data': current_data,
                    'product_data': product_data,
                    'last_update': datetime.now()
                }
        
        return st.session_state.territories_data[territory_code]
    
    def update_live_data(self, territory_code):
        """Met à jour les données en temps réel"""
        if territory_code in st.session_state.territories_data:
            data = st.session_state.territories_data[territory_code]
            current_data = data['current_data'].copy()
            
            # Mise à jour légère des données
            for idx in current_data.index:
                if random.random() < 0.3:  # 30% de chance de changement
                    variation = random.uniform(-0.02, 0.02)
                    current_data.loc[idx, 'revenu_mensuel'] *= (1 + variation)
                    current_data.loc[idx, 'variation_pct'] = variation * 100
                    current_data.loc[idx, 'volume_importation'] *= random.uniform(0.98, 1.02)
            
            st.session_state.territories_data[territory_code]['current_data'] = current_data
            st.session_state.territories_data[territory_code]['last_update'] = datetime.now()
    
    def display_territory_selector(self):
        """Affiche le sélecteur de territoire optimisé"""
        st.markdown('<div class="territory-selector">', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            territory_options = {v['nom_complet']: k for k, v in self.territories.items() if v['taux_octroi_actif']}
            
            # Utilisation de session_state pour éviter le rerun
            current_name = self.territories[st.session_state.selected_territory]['nom_complet']
            selected_territory_name = st.selectbox(
                "🌍 SÉLECTIONNEZ UN TERRITOIRE:",
                options=list(territory_options.keys()),
                index=list(territory_options.keys()).index(current_name),
                key="territory_selector_main"
            )
            
            new_territory = territory_options[selected_territory_name]
            if new_territory != st.session_state.selected_territory:
                st.session_state.selected_territory = new_territory
                # Précharger les données en arrière-plan
                self.get_territory_data(new_territory)
                st.success(f"✅ Changement vers {selected_territory_name} effectué!")
        
        with col2:
            territory_info = self.territories[st.session_state.selected_territory]
            st.metric("Type", territory_info['type'])
        
        with col3:
            st.metric("Population", f"{territory_info['population']:,}")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    def display_header(self):
        """Affiche l'en-tête du dashboard"""
        territory_info = self.territories[st.session_state.selected_territory]
        
        st.markdown(f'<h1 class="main-header">🏝️ Dashboard Octroi de Mer - {territory_info["nom_complet"]}</h1>', 
                   unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown('<div class="live-badge">🔴 DONNÉES FISCALES EN TEMPS RÉEL</div>', 
                       unsafe_allow_html=True)
            st.markdown(f"**Surveillance et analyse des recettes de l'Octroi de Mer par secteur économique**")
        
        # Bannière drapeau du territoire
        st.markdown(f"""
        <div class="territory-flag {territory_info['drapeau']}">
            <strong>{territory_info['nom_complet']} - Octroi de Mer</strong><br>
            <small>Type: {territory_info['type']} | Population: {territory_info['population']:,} | PIB: {territory_info['pib']} M€</small>
        </div>
        """, unsafe_allow_html=True)
        
        current_time = datetime.now().strftime('%H:%M:%S')
        st.sidebar.markdown(f"**🕐 Dernière mise à jour: {current_time}**")
    
    def display_key_metrics(self):
        """Affiche les métriques clés de l'Octroi de Mer"""
        data = self.get_territory_data(st.session_state.selected_territory)
        current_data = data['current_data']
        
        st.markdown('<h3 class="section-header">📊 INDICATEURS CLÉS OCTROI DE MER</h3>', 
                   unsafe_allow_html=True)
        
        # Calcul des métriques
        revenu_total = current_data['revenu_mensuel'].sum()
        variation_moyenne = current_data['variation_pct'].mean()
        volume_total = current_data['volume_importation'].sum()
        secteurs_hausse = len(current_data[current_data['variation_pct'] > 0])
        
        revenu_annuel_projete = revenu_total * 12
        territory_info = self.territories[st.session_state.selected_territory]
        revenu_par_habitant = revenu_total / territory_info['population'] * 1000
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Revenu Mensuel Octroi de Mer",
                f"{revenu_total/1e6:.1f} M€",
                f"{variation_moyenne:+.2f}%",
                delta_color="normal"
            )
        
        with col2:
            st.metric(
                "Revenu Annuel Projeté",
                f"{revenu_annuel_projete/1e6:.1f} M€",
                f"{random.uniform(2, 8):.1f}% vs année précédente"
            )
        
        with col3:
            st.metric(
                "Secteurs en Croissance",
                f"{secteurs_hausse}/{len(current_data)}",
                f"{secteurs_hausse - (len(current_data) - secteurs_hausse):+d} vs décroissance"
            )
        
        with col4:
            volume_total_formatted = f"{volume_total/1000:.0f}K"
            st.metric(
                "Volume Total Importations",
                volume_total_formatted,
                f"{random.randint(-5, 10)}% vs mois dernier"
            )
        
        # Métriques spécifiques au territoire
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "Revenu par Habitant",
                f"{revenu_par_habitant:.1f} €",
                f"{random.uniform(-5, 5):.1f}% vs moyenne DROM-COM"
            )
        
        with col2:
            st.metric(
                "Taux d'Octroi Moyen",
                f"{current_data['taux_normal'].mean():.1f}%",
                f"{random.uniform(-2, 2):.1f}% vs période précédente"
            )
        
        with col3:
            st.metric(
                "Contribution au PIB",
                f"{(revenu_annuel_projete/territory_info['pib']/1e6)*100:.2f}%",
                f"{random.uniform(-1, 3):.1f}% vs objectif"
            )
    
    def create_octroi_overview(self):
        """Crée la vue d'ensemble de l'Octroi de Mer"""
        data = self.get_territory_data(st.session_state.selected_territory)
        
        st.markdown('<h3 class="section-header">🏛️ VUE D\'ENSEMBLE OCTROI DE MER</h3>', 
                   unsafe_allow_html=True)
        
        tab1, tab2, tab3, tab4 = st.tabs(["Évolution Revenus", "Répartition Secteurs", "Top Contribuables", "Analyse Taux"])
        
        with tab1:
            col1, col2 = st.columns(2)
            
            with col1:
                # Évolution des revenus totaux
                evolution_totale = data['historical_data'].groupby('date')['revenu_octroi'].sum().reset_index()
                evolution_totale['revenu_mensuel_M'] = evolution_totale['revenu_octroi'] / 1e6
                
                fig = px.line(evolution_totale, 
                             x='date', 
                             y='revenu_mensuel_M',
                             title=f'Évolution des Revenus - {self.territories[st.session_state.selected_territory]["nom_complet"]}',
                             color_discrete_sequence=['#0055A4'])
                fig.update_layout(yaxis_title="Revenus (Millions €)")
                st.plotly_chart(fig, config={'displayModeBar': False})
            
            with col2:
                # Performance par catégorie
                performance_categories = data['current_data'].groupby('categorie').agg({
                    'variation_pct': 'mean',
                    'revenu_mensuel': 'sum'
                }).reset_index()
                
                fig = px.bar(performance_categories, 
                            x='categorie', 
                            y='variation_pct',
                            title='Performance Mensuelle par Catégorie (%)',
                            color='categorie',
                            color_discrete_sequence=px.colors.qualitative.Set3)
                fig.update_layout(yaxis_title="Variation (%)")
                st.plotly_chart(fig, config={'displayModeBar': False})
        
        with tab2:
            col1, col2 = st.columns(2)
            
            with col1:
                fig = px.pie(data['current_data'], 
                            values='revenu_mensuel', 
                            names='secteur',
                            title='Répartition des Revenus par Secteur',
                            color_discrete_sequence=px.colors.qualitative.Set3)
                st.plotly_chart(fig, config={'displayModeBar': False})
            
            with col2:
                fig = px.bar(data['current_data'], 
                            x='secteur', 
                            y='volume_importation',
                            title='Volume d\'Importation par Secteur',
                            color_discrete_sequence=px.colors.qualitative.Set3)
                fig.update_layout(yaxis_title="Volume d'Importation")
                st.plotly_chart(fig, config={'displayModeBar': False})
        
        with tab3:
            col1, col2 = st.columns(2)
            
            with col1:
                top_contributeurs = data['current_data'].nlargest(10, 'revenu_mensuel')
                fig = px.bar(top_contributeurs, 
                            x='revenu_mensuel', 
                            y='secteur',
                            orientation='h',
                            title='Top 10 des Secteurs Contribuant aux Revenus',
                            color='revenu_mensuel',
                            color_continuous_scale='Blues')
                st.plotly_chart(fig, config={'displayModeBar': False})
            
            with col2:
                top_croissance = data['current_data'].nlargest(10, 'variation_pct')
                fig = px.bar(top_croissance, 
                            x='variation_pct', 
                            y='secteur',
                            orientation='h',
                            title='Top 10 des Croissances Sectorielles (%)',
                            color='variation_pct',
                            color_continuous_scale='Greens')
                st.plotly_chart(fig, config={'displayModeBar': False})
        
        with tab4:
            st.subheader("Analyse des Taux d'Octroi de Mer")
            
            fig = px.scatter(data['product_data'], 
                           x='taux_octroi', 
                           y='volume',
                           size='volume',
                           color='secteur',
                           title='Taux d\'Octroi vs Volume d\'Importation',
                           hover_name='produit',
                           size_max=40)
            st.plotly_chart(fig, config={'displayModeBar': False})
            
            st.dataframe(data['product_data'][['produit', 'secteur', 'taux_octroi', 'volume']], 
                        use_container_width=True)
    
    def create_secteurs_live(self):
        """Affiche les secteurs en temps réel"""
        data = self.get_territory_data(st.session_state.selected_territory)
        
        st.markdown('<h3 class="section-header">🏢 SECTEURS ÉCONOMIQUES EN TEMPS RÉEL</h3>', 
                   unsafe_allow_html=True)
        
        tab1, tab2, tab3 = st.tabs(["Tableau des Revenus", "Analyse Catégorie", "Simulateur"])
        
        with tab1:
            col1, col2, col3 = st.columns(3)
            with col1:
                categorie_filtre = st.selectbox("Catégorie:", 
                                              ['Toutes'] + list(data['current_data']['categorie'].unique()))
            with col2:
                performance_filtre = st.selectbox("Performance:", 
                                                ['Tous', 'En croissance', 'En décroissance', 'Stable'])
            with col3:
                tri_filtre = st.selectbox("Trier par:", 
                                        ['Revenu mensuel', 'Variation %', 'Volume importation', 'Taux normal'])
            
            # Application des filtres
            secteurs_filtres = data['current_data'].copy()
            if categorie_filtre != 'Toutes':
                secteurs_filtres = secteurs_filtres[secteurs_filtres['categorie'] == categorie_filtre]
            if performance_filtre == 'En croissance':
                secteurs_filtres = secteurs_filtres[secteurs_filtres['variation_pct'] > 0]
            elif performance_filtre == 'En décroissance':
                secteurs_filtres = secteurs_filtres[secteurs_filtres['variation_pct'] < 0]
            elif performance_filtre == 'Stable':
                secteurs_filtres = secteurs_filtres[secteurs_filtres['variation_pct'] == 0]
            
            # Tri
            if tri_filtre == 'Revenu mensuel':
                secteurs_filtres = secteurs_filtres.sort_values('revenu_mensuel', ascending=False)
            elif tri_filtre == 'Variation %':
                secteurs_filtres = secteurs_filtres.sort_values('variation_pct', ascending=False)
            elif tri_filtre == 'Volume importation':
                secteurs_filtres = secteurs_filtres.sort_values('volume_importation', ascending=False)
            elif tri_filtre == 'Taux normal':
                secteurs_filtres = secteurs_filtres.sort_values('taux_normal', ascending=False)
            
            # Affichage optimisé
            for _, secteur in secteurs_filtres.iterrows():
                change_class = "positive" if secteur['variation_pct'] > 0 else "negative" if secteur['variation_pct'] < 0 else "neutral"
                
                col1, col2, col3, col4, col5 = st.columns([1, 2, 1, 1, 1])
                with col1:
                    st.markdown(f"**{secteur['secteur']}**")
                    st.markdown(f"*{secteur['categorie']}*")
                with col2:
                    st.markdown(f"**{secteur['nom_complet']}**")
                    st.markdown(f"Taux normal: {secteur['taux_normal']}%")
                with col3:
                    st.markdown(f"**{secteur['revenu_mensuel']/1000:.0f}K€**")
                    st.markdown(f"Taux réduit: {secteur['taux_reduit']}%")
                with col4:
                    variation_str = f"{secteur['variation_pct']:+.2f}%"
                    st.markdown(f"**{variation_str}**")
                    st.markdown(f"{secteur['variation_abs']/1000:+.0f}K€")
                with col5:
                    st.markdown(f"<div class='revenue-change {change_class}'>{variation_str}</div>", 
                               unsafe_allow_html=True)
                    st.markdown(f"Vol: {secteur['volume_importation']:,.0f}")
                
                st.markdown("---")
        
        with tab2:
            categorie_selectionnee = st.selectbox("Sélectionnez une catégorie:", 
                                                data['current_data']['categorie'].unique())
            
            if categorie_selectionnee:
                secteurs_categorie = data['current_data'][
                    data['current_data']['categorie'] == categorie_selectionnee
                ]
                
                col1, col2 = st.columns(2)
                
                with col1:
                    fig = px.bar(secteurs_categorie, 
                                x='secteur', 
                                y='variation_pct',
                                title=f'Performance des Secteurs - {categorie_selectionnee}',
                                color='variation_pct',
                                color_continuous_scale='RdYlGn')
                    st.plotly_chart(fig, config={'displayModeBar': False})
                
                with col2:
                    fig = px.pie(secteurs_categorie, 
                                values='revenu_mensuel', 
                                names='secteur',
                                title=f'Répartition des Revenus - {categorie_selectionnee}')
                    st.plotly_chart(fig, config={'displayModeBar': False})
        
        with tab3:
            st.subheader("Simulateur de Calcul d'Octroi de Mer")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                produit_selectionne = st.selectbox("Produit:", 
                                                 data['product_data']['produit'].unique())
                valeur_produit = st.number_input("Valeur du produit (€)", 
                                               min_value=0.0, value=1000.0)
            
            with col2:
                volume_import = st.number_input("Volume/Quantité", 
                                              min_value=1, value=100)
                type_taux = st.selectbox("Type de taux:", 
                                       ["Normal", "Réduit", "Spécifique"])
            
            with col3:
                pays_origine = st.selectbox("Pays d'origine:", 
                                          ["France", "UE", "Pays tiers", "DOM"])
                calculer = st.button("Calculer l'Octroi de Mer")
            
            if calculer:
                produit_data = data['product_data'][
                    data['product_data']['produit'] == produit_selectionne
                ].iloc[0]
                
                if type_taux == "Normal":
                    taux_applique = data['secteurs'][produit_data['secteur']]['taux_normal']
                elif type_taux == "Réduit":
                    taux_applique = data['secteurs'][produit_data['secteur']]['taux_reduit']
                else:
                    taux_applique = data['secteurs'][produit_data['secteur']]['taux_specifique']
                
                montant_octroi = valeur_produit * (taux_applique / 100)
                
                st.success(f"""
                **Résultat du calcul:**
                - Produit: {produit_selectionne}
                - Secteur: {produit_data['secteur']}
                - Taux appliqué: {taux_applique}%
                - Valeur imposable: {valeur_produit:,.2f}€
                - **Montant Octroi de Mer: {montant_octroi:,.2f}€**
                """)
    
    def create_categorie_analysis(self):
        """Analyse par catégorie détaillée"""
        data = self.get_territory_data(st.session_state.selected_territory)
        
        st.markdown('<h3 class="section-header">📊 ANALYSE PAR CATÉGORIE DÉTAILLÉE</h3>', 
                   unsafe_allow_html=True)
        
        tab1, tab2, tab3 = st.tabs(["Performance Catégorielle", "Comparaison Catégories", "Tendances"])
        
        with tab1:
            categorie_performance = data['current_data'].groupby('categorie').agg({
                'variation_pct': 'mean',
                'volume_importation': 'sum',
                'revenu_mensuel': 'sum',
                'secteur': 'count'
            }).reset_index()
            
            col1, col2 = st.columns(2)
            
            with col1:
                fig = px.bar(categorie_performance, 
                            x='categorie', 
                            y='variation_pct',
                            title='Performance Moyenne par Catégorie (%)',
                            color='variation_pct',
                            color_continuous_scale='RdYlGn')
                st.plotly_chart(fig, config={'displayModeBar': False})
            
            with col2:
                fig = px.scatter(categorie_performance, 
                               x='revenu_mensuel', 
                               y='variation_pct',
                               size='volume_importation',
                               color='categorie',
                               title='Performance vs Revenus par Catégorie',
                               hover_name='categorie',
                               size_max=60)
                st.plotly_chart(fig, config={'displayModeBar': False})
        
        with tab2:
            categorie_evolution = data['historical_data'].groupby([
                data['historical_data']['date'].dt.to_period('M').dt.to_timestamp(),
                'categorie'
            ])['revenu_octroi'].sum().reset_index()
            
            fig = px.line(categorie_evolution, 
                         x='date', 
                         y='revenu_octroi',
                         color='categorie',
                         title=f'Évolution Comparative - {self.territories[st.session_state.selected_territory]["nom_complet"]}',
                         color_discrete_sequence=px.colors.qualitative.Set3)
            fig.update_layout(yaxis_title="Revenus Octroi de Mer (€)")
            st.plotly_chart(fig, config={'displayModeBar': False})
        
        with tab3:
            st.subheader("Tendances et Perspectives par Catégorie")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("""
                ### 📈 Catégories en Croissance
                
                **🏭 BTP & Construction:**
                - Boom immobilier
                - Projets d'infrastructure publique
                - Reconstruction post-catastrophe
                
                **💊 Santé & Pharmaceutique:**
                - Vieillissement de la population
                - Investissements santé publique
                - Innovations médicales
                
                **🛒 Biens de Consommation:**
                - Croissance démographique
                - Augmentation pouvoir d'achat
                - Développement retail
                """)
            
            with col2:
                st.markdown("""
                ### 📉 Catégories en Décroissance
                
                **⛽ Énergie Traditionnelle:**
                - Transition vers énergies renouvelables
                - Politiques environnementales
                - Électrification transports
                
                **🚗 Automobile:**
                - Saturation du marché
                - Prix élevés des véhicules
                - Alternative transports publics
                
                **🍷 Boissons Alcoolisées:**
                - Campagnes santé publique
                - Changement habitudes consommation
                - Fiscalité accrue
                """)
    
    def create_evolution_analysis(self):
        """Analyse de l'évolution des revenus"""
        data = self.get_territory_data(st.session_state.selected_territory)
        
        st.markdown('<h3 class="section-header">📈 ÉVOLUTION DES REVENUS</h3>', 
                   unsafe_allow_html=True)
        
        tab1, tab2, tab3 = st.tabs(["Analyse Historique", "Saisonnalité", "Projections"])
        
        with tab1:
            col1, col2 = st.columns(2)
            
            with col1:
                cumulative_data = data['historical_data'].copy()
                cumulative_data['date_group'] = cumulative_data['date'].dt.to_period('M').dt.to_timestamp()
                monthly_totals = cumulative_data.groupby('date_group')['revenu_octroi'].sum().reset_index()
                monthly_totals['cumulative_revenue'] = monthly_totals['revenu_octroi'].cumsum()
                
                fig = px.line(monthly_totals, 
                             x='date_group', 
                             y='cumulative_revenue',
                             title=f'Revenus Cumulatifs - {self.territories[st.session_state.selected_territory]["nom_complet"]} (€)')
                st.plotly_chart(fig, config={'displayModeBar': False})
            
            with col2:
                monthly_heatmap = monthly_totals.copy()
                monthly_heatmap['annee'] = monthly_heatmap['date_group'].dt.year
                monthly_heatmap['mois'] = monthly_heatmap['date_group'].dt.month
                
                heatmap_data = monthly_heatmap.pivot_table(
                    index='annee',
                    columns='mois',
                    values='revenu_octroi',
                    aggfunc='sum'
                ) / 1e6
                
                fig = px.imshow(heatmap_data,
                               title=f'Revenus Mensuels par Année - {self.territories[st.session_state.selected_territory]["nom_complet"]} (M€)',
                               color_continuous_scale='Blues',
                               aspect="auto")
                st.plotly_chart(fig, config={'displayModeBar': False})
        
        with tab2:
            saisonnalite_data = data['historical_data'].copy()
            saisonnalite_data['mois'] = saisonnalite_data['date'].dt.month
            
            saisonnalite_moyenne = saisonnalite_data.groupby('mois')['revenu_octroi'].mean().reset_index()
            saisonnalite_moyenne['revenu_M'] = saisonnalite_moyenne['revenu_octroi'] / 1e6
            
            fig = px.line(saisonnalite_moyenne, 
                         x='mois', 
                         y='revenu_M',
                         title=f'Saisonnalité des Revenus - {self.territories[st.session_state.selected_territory]["nom_complet"]}',
                         markers=True)
            fig.update_layout(xaxis_title="Mois", yaxis_title="Revenus Moyens (Millions €)")
            fig.update_xaxes(tickvals=list(range(1, 13)), 
                           ticktext=['Jan', 'Fév', 'Mar', 'Avr', 'Mai', 'Jun', 
                                   'Jul', 'Aoû', 'Sep', 'Oct', 'Nov', 'Dec'])
            st.plotly_chart(fig, config={'displayModeBar': False})
        
        with tab3:
            st.subheader("Projections des Revenus")
            
            derniere_date = data['historical_data']['date'].max()
            dates_futures = pd.date_range(derniere_date + timedelta(days=30), 
                                        periods=12, freq='M')
            
            projections = []
            revenu_base = data['current_data']['revenu_mensuel'].sum()
            
            for i, date in enumerate(dates_futures):
                croissance = random.uniform(0.01, 0.03)
                revenu_projete = revenu_base * (1 + croissance) ** (i + 1)
                projections.append({
                    'date': date,
                    'revenu_projete': revenu_projete,
                    'type': 'Projection'
                })
            
            projections_df = pd.DataFrame(projections)
            
            historique_recent = data['historical_data'][
                data['historical_data']['date'] >= (derniere_date - timedelta(days=365))
            ].groupby('date')['revenu_octroi'].sum().reset_index()
            historique_recent['type'] = 'Historique'
            
            comparaison_data = pd.concat([
                historique_recent.rename(columns={'revenu_octroi': 'valeur'}),
                projections_df.rename(columns={'revenu_projete': 'valeur'})
            ])
            
            fig = px.line(comparaison_data, 
                         x='date', 
                         y='valeur',
                         color='type',
                         title=f'Projection des Revenus - {self.territories[st.session_state.selected_territory]["nom_complet"]} - 12 Mois',
                         color_discrete_sequence=['#0055A4', '#EF4135'])
            fig.update_layout(yaxis_title="Revenus (€)")
            st.plotly_chart(fig, config={'displayModeBar': False})
    
    def create_territory_comparison(self):
        """Crée une vue de comparaison entre territoires"""
        comparison_data = generate_comparison_data(self.territories)
        
        st.markdown('<h3 class="section-header">🌍 COMPARAISON INTER-TERRITOIRES</h3>', 
                   unsafe_allow_html=True)
        
        tab1, tab2, tab3 = st.tabs(["Vue d'Ensemble", "Performance", "Analyse Détaillée"])
        
        with tab1:
            col1, col2 = st.columns(2)
            
            with col1:
                fig = px.bar(comparison_data, 
                            x='nom_complet', 
                            y='revenu_octroi_total',
                            title='Revenus Totaux par Territoire',
                            color='type',
                            color_discrete_map={'DROM': '#0055A4', 'COM': '#EF4135'})
                fig.update_layout(yaxis_title="Revenus (€)")
                st.plotly_chart(fig, config={'displayModeBar': False})
            
            with col2:
                fig = px.bar(comparison_data, 
                            x='nom_complet', 
                            y='revenu_par_habitant',
                            title='Revenus par Habitant',
                            color='type',
                            color_discrete_map={'DROM': '#0055A4', 'COM': '#EF4135'})
                fig.update_layout(yaxis_title="Revenus par Habitant (€)")
                st.plotly_chart(fig, config={'displayModeBar': False})
        
        with tab2:
            col1, col2 = st.columns(2)
            
            with col1:
                fig = px.scatter(comparison_data, 
                               x='pib', 
                               y='revenu_octroi_total',
                               size='population',
                               color='type',
                               title='Revenus Octroi de Mer vs PIB',
                               hover_name='nom_complet',
                               color_discrete_map={'DROM': '#0055A4', 'COM': '#EF4135'},
                               size_max=60)
                fig.update_layout(xaxis_title="PIB (M€)", yaxis_title="Revenus Octroi de Mer (€)")
                st.plotly_chart(fig, config={'displayModeBar': False})
            
            with col2:
                fig = px.scatter(comparison_data, 
                               x='population', 
                               y='revenu_par_habitant',
                               size='superficie',
                               color='type',
                               title='Population vs Revenus par Habitant',
                               hover_name='nom_complet',
                               color_discrete_map={'DROM': '#0055A4', 'COM': '#EF4135'},
                               size_max=60)
                fig.update_layout(xaxis_title="Population", yaxis_title="Revenus par Habitant (€)")
                st.plotly_chart(fig, config={'displayModeBar': False})
        
        with tab3:
            st.subheader("Tableau Comparatif Détaillé")
            
            territoires_a_comparer = st.multiselect(
                "Sélectionnez les territoires à comparer:",
                options=comparison_data['nom_complet'].tolist(),
                default=comparison_data['nom_complet'].tolist()[:5]
            )
            
            if territoires_a_comparer:
                donnees_filtrees = comparison_data[
                    comparison_data['nom_complet'].isin(territoires_a_comparer)
                ]
                
                donnees_filtrees['densite'] = donnees_filtrees['population'] / donnees_filtrees['superficie']
                donnees_filtrees['pib_par_habitant'] = donnees_filtrees['pib'] * 1e6 / donnees_filtrees['population']
                donnees_filtrees['contribution_octroi_pib'] = (donnees_filtrees['revenu_octroi_total'] * 12) / (donnees_filtrees['pib'] * 1e6) * 100
                
                # Create the display dataframe with renamed columns
                display_df = donnees_filtrees[
                    ['nom_complet', 'type', 'population', 'superficie', 'pib', 
                     'revenu_octroi_total', 'revenu_par_habitant', 'densite', 
                     'pib_par_habitant', 'contribution_octroi_pib']
                ].rename(columns={
                    'nom_complet': 'Territoire',
                    'type': 'Type',
                    'population': 'Population',
                    'superficie': 'Superficie (km²)',
                    'pib': 'PIB (M€)',
                    'revenu_octroi_total': 'Revenu Mensuel (€)',
                    'revenu_par_habitant': 'Revenu/Habitant (€)',
                    'densite': 'Densité (hab/km²)',
                    'pib_par_habitant': 'PIB/Habitant (€)',
                    'contribution_octroi_pib': 'Contribution Octroi/PIB (%)'
                })
                
                # Sort by the renamed column
                display_df = display_df.sort_values('Revenu Mensuel (€)', ascending=False)
                
                st.dataframe(display_df, use_container_width=True)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    fig = px.bar(donnees_filtrees, 
                                x='nom_complet', 
                                y='contribution_octroi_pib',
                                title='Contribution Octroi de Mer au PIB (%)',
                                color='type',
                                color_discrete_map={'DROM': '#0055A4', 'COM': '#EF4135'})
                    fig.update_layout(yaxis_title="Contribution au PIB (%)")
                    st.plotly_chart(fig, config={'displayModeBar': False})
                
                with col2:
                    fig = px.bar(donnees_filtrees, 
                                x='nom_complet', 
                                y='pib_par_habitant',
                                title='PIB par Habitant (€)',
                                color='type',
                                color_discrete_map={'DROM': '#0055A4', 'COM': '#EF4135'})
                    fig.update_layout(yaxis_title="PIB par Habitant (€)")
                    st.plotly_chart(fig, config={'displayModeBar': False})
    
    def create_sidebar(self):
        """Crée la sidebar avec les contrôles"""
        st.sidebar.markdown("## 🎛️ CONTRÔLES D'ANALYSE")
        
        st.sidebar.markdown("### 📅 Période d'analyse")
        date_debut = st.sidebar.date_input("Date de début", 
                                         value=datetime.now() - timedelta(days=365))
        date_fin = st.sidebar.date_input("Date de fin", 
                                       value=datetime.now())
        
        st.sidebar.markdown("### 🏢 Sélection des catégories")
        data = self.get_territory_data(st.session_state.selected_territory)
        categories_selectionnees = st.sidebar.multiselect(
            "Catégories à afficher:",
            list(data['current_data']['categorie'].unique()),
            default=list(data['current_data']['categorie'].unique())[:3]
        )
        
        st.sidebar.markdown("### ⚙️ Options")
        auto_refresh = st.sidebar.checkbox("Rafraîchissement automatique", value=False)
        show_details = st.sidebar.checkbox("Afficher détails techniques", value=False)
        comparison_mode = st.sidebar.checkbox("Mode comparaison", value=False)
        
        if st.sidebar.button("🔄 Rafraîchir les données"):
            self.update_live_data(st.session_state.selected_territory)
            st.success("Données mises à jour!")
        
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 💹 INDICATEURS ÉCONOMIQUES")
        
        indicateurs = {
            'Inflation': {'valeur': 2.8 + random.uniform(-0.2, 0.2), 'variation': random.uniform(-0.1, 0.1)},
            'Croissance PIB': {'valeur': 3.2 + random.uniform(-0.3, 0.3), 'variation': random.uniform(-0.2, 0.2)},
            'Taux Chômage': {'valeur': 18.5 + random.uniform(-0.5, 0.5), 'variation': random.uniform(-0.3, 0.1)},
            'Importations Total': {'valeur': 4.8 + random.uniform(-0.2, 0.2), 'variation': random.uniform(-1, 2)}
        }
        
        for indicateur, data in indicateurs.items():
            st.sidebar.metric(
                indicateur,
                f"{data['valeur']:.1f}%",
                f"{data['variation']:+.1f}%"
            )
        
        return {
            'date_debut': date_debut,
            'date_fin': date_fin,
            'categories_selectionnees': categories_selectionnees,
            'auto_refresh': auto_refresh,
            'show_details': show_details,
            'comparison_mode': comparison_mode
        }

    def run_dashboard(self):
        """Exécute le dashboard complet"""
        # Préchargement des données du territoire sélectionné
        self.get_territory_data(st.session_state.selected_territory)
        
        # Affichage du sélecteur de territoire
        self.display_territory_selector()
        
        # Sidebar
        controls = self.create_sidebar()
        
        # Header
        self.display_header()
        
        # Métriques clés
        self.display_key_metrics()
        
        # Navigation par onglets
        if controls['comparison_mode']:
            tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
                "🌍 Comparaison Territoires", 
                "📈 Vue d'Ensemble", 
                "🏢 Secteurs", 
                "📊 Catégories", 
                "📈 Évolution", 
                "💡 Insights",
                "ℹ️ À Propos"
            ])
            
            with tab1:
                self.create_territory_comparison()
            
            with tab2:
                self.create_octroi_overview()
            
            with tab3:
                self.create_secteurs_live()
            
            with tab4:
                self.create_categorie_analysis()
            
            with tab5:
                self.create_evolution_analysis()
            
            with tab6:
                st.markdown("## 💡 INSIGHTS STRATÉGIQUES")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("""
                    ### 🎯 TENDANCES FISCALES INTER-TERRITOIRES
                    
                    **📈 Dynamiques Sectorielles:**
                    - Forte croissance BTP et construction (tous territoires)
                    - Spécialisations selon territoires (tourisme, mines, etc.)
                    - Déclin progressif énergies fossiles
                    
                    **🏝️ Facteurs Spécifiques:**
                    - Taille et densité de population
                    - Spécialisations économiques
                    - Proximité géographique
                    
                    **💰 Impact Économique:**
                    - Financement services publics
                    - Soutien à l'économie locale
                    - Redistribution territoriale
                    """)
                
                with col2:
                    st.markdown("""
                    ### 🚨 DÉFIS ET OPPORTUNITÉS
                    
                    **⚡ Défis à Relever:**
                    - Évolution réglementaire européenne
                    - Contrôles douaniers renforcés
                    - Fraude et optimisation fiscale
                    
                    **💡 Opportunités:**
                    - Digitalisation des procédures
                    - Élargissement assiette fiscale
                    - Cooperation régionale
                    
                    **🔮 Perspectives:**
                    - Croissance modérée des revenus
                    - Diversification des sources
                    - Modernisation continue
                    """)
                
                st.markdown("""
                ### 📋 RECOMMANDATIONS OPÉRATIONNELLES
                
                1. **Optimisation Contrôle:** Renforcer les contrôles sur les secteurs à forts enjeux
                2. **Digitalisation:** Accélérer la dématérialisation des déclarations
                3. **Formation:** Former les agents aux nouvelles réglementations
                4. **Communication:** Améliorer l'information des contribuables
                5. **Innovation:** Développer de nouveaux outils d'analyse de données
                6. **Harmonisation:** Standardiser les procédures entre territoires
                7. **Spécialisation:** Adapter les contrôles aux spécificités territoriales
                """)
            
            with tab7:
                st.markdown("## 📋 À propos de ce dashboard")
                st.markdown(f"""
                Ce dashboard présente une analyse en temps réel des recettes de l'Octroi de Mer 
                pour l'ensemble des DROM-COM.
                
                **Territoire actuel:** {self.territories[st.session_state.selected_territory]['nom_complet']}
                
                **Couverture:**
                - {len([t for t in self.territories.values() if t['taux_octroi_actif']])} territoires avec Octroi de Mer actif
                - 10+ secteurs économiques principaux par territoire
                - Données historiques depuis 2022
                - Analyse par catégorie et produit
                
                **⚡ Performance:**
                - Cache intelligent pour un chargement rapide
                - Mises à jour en temps réel optimisées
                - Navigation fluide entre territoires
                
                **⚠️ Avertissement:** 
                Ce dashboard est un outil d'aide à la décision.
                Les données peuvent être sujettes à révision.
                """)
                
                st.markdown("---")
                st.markdown("""
                **📞 Contact:**
                - Direction Générale des Douanes et Droits Indirects
                - Site web: www.douane.gouv.fr
                - Email: contact@douane.finances.gouv.fr
                """)
        else:
            tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
                "📈 Vue d'Ensemble", 
                "🏢 Secteurs", 
                "📊 Catégories", 
                "📈 Évolution", 
                "💡 Insights",
                "ℹ️ À Propos"
            ])
            
            with tab1:
                self.create_octroi_overview()
            
            with tab2:
                self.create_secteurs_live()
            
            with tab3:
                self.create_categorie_analysis()
            
            with tab4:
                self.create_evolution_analysis()
            
            with tab5:
                st.markdown("## 💡 INSIGHTS STRATÉGIQUES")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown(f"""
                    ### 🎯 TENDANCES FISCALES - {self.territories[st.session_state.selected_territory]['nom_complet']}
                    
                    **📈 Dynamiques Sectorielles:**
                    - Forte croissance BTP et construction
                    - Stabilité secteur agroalimentaire
                    - Déclin progressif énergies fossiles
                    
                    **🏝️ Facteurs Locaux:**
                    - Croissance démographique soutenue
                    - Développement infrastructures
                    - Tourisme en augmentation
                    """)
                
                with col2:
                    st.markdown("""
                    ### 🚨 DÉFIS ET OPPORTUNITÉS
                    
                    **⚡ Défis à Relever:**
                    - Évolution réglementaire européenne
                    - Contrôles douaniers renforcés
                    - Fraude et optimisation fiscale
                    
                    **💡 Opportunités:**
                    - Digitalisation des procédures
                    - Élargissement assiette fiscale
                    - Cooperation régionale
                    """)
                
                st.markdown("""
                ### 📋 RECOMMANDATIONS OPÉRATIONNELLES
                
                1. **Optimisation Contrôle:** Renforcer les contrôles sur les secteurs à forts enjeux
                2. **Digitalisation:** Accélérer la dématérialisation des déclarations
                3. **Formation:** Former les agents aux nouvelles réglementations
                4. **Communication:** Améliorer l'information des contribuables
                5. **Innovation:** Développer de nouveaux outils d'analyse de données
                """)
            
            with tab6:
                st.markdown("## 📋 À propos de ce dashboard")
                st.markdown(f"""
                Ce dashboard présente une analyse en temps réel des recettes de l'Octroi de Mer 
                à {self.territories[st.session_state.selected_territory]['nom_complet']}.
                
                **Couverture:**
                - {len(self.get_territory_data(st.session_state.selected_territory)['secteurs'])} secteurs économiques principaux
                - Données historiques depuis 2022
                - Analyse par catégorie et produit
                
                **⚡ Performance:**
                - Cache intelligent pour un chargement rapide
                - Mises à jour en temps réel optimisées
                
                **⚠️ Avertissement:** 
                Ce dashboard est un outil d'aide à la décision.
                Les données peuvent être sujettes à révision.
                """)
                
                st.markdown("---")
                st.markdown("""
                **📞 Contact:**
                - Direction Générale des Douanes et Droits Indirects
                - Site web: www.douane.gouv.fr
                - Email: contact@douane.finances.gouv.fr
                """)
        
        # Mise à jour automatique désactivée par défaut pour éviter les ralentissements
        if controls['auto_refresh']:
            time.sleep(30)
            st.rerun()

# Lancement du dashboard
if __name__ == "__main__":
    dashboard = OctroiMerDashboard()
    dashboard.run_dashboard()

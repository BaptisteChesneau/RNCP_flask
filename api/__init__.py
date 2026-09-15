from flask import Blueprint

# Création du Blueprint 'api'
api_bp = Blueprint("api", __name__)

# Import des routes pour qu'elles soient enregistrées
from api import messages_api
from django.contrib.auth.backends import ModelBackend


class UniSphereBackend(ModelBackend):
    """
    Authentifie aussi les comptes inactifs pour pouvoir afficher
    un message dédié (« compte désactivé ») côté formulaire de connexion.
    """

    def user_can_authenticate(self, user):
        return True

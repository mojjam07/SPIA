import logging
from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import AuthenticationFailed

logger = logging.getLogger(__name__)

class CookieTokenAuthentication(TokenAuthentication):
    """
    Custom authentication class that reads the token from the 'auth_token' cookie.
    """
    def authenticate(self, request):
        token = request.COOKIES.get('auth_token')
        if not token:
            logger.warning("Authentication failed: No auth_token cookie found in request.")
            return None
        try:
            return self.authenticate_credentials(token)
        except AuthenticationFailed as e:
            logger.warning(f"Authentication failed: Invalid token. Details: {str(e)}")
            raise e

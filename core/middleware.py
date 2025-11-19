from django.utils import translation
from django.utils.deprecation import MiddlewareMixin


class UserLanguageMiddleware(MiddlewareMixin):
    """
    Middleware to activate user's preferred language from their profile.
    This runs after LocaleMiddleware to override the default language selection.
    """
    def process_request(self, request):
        if request.user.is_authenticated:
            try:
                # Get user's language preference from profile
                language = request.user.profile.language
                if language:
                    # Activate the user's preferred language
                    translation.activate(language)
                    request.LANGUAGE_CODE = language
            except:
                # If profile doesn't exist or has no language, use default
                pass


from django.shortcuts import render
from django.http import HttpResponseNotFound

def custom_404_handler(request, exception):
    """Custom 404 error page"""
    return render(request, 'pages/error.html', {
        'error_code': '404',
        'error_title': 'Page Not Found',
        'error_message': 'The page you are looking for does not exist or may have been moved.'
    }, status=404)

def custom_500_handler(request):
    """Custom 500 error page"""
    return render(request, 'pages/error.html', {
        'error_code': '500',
        'error_title': 'Server Error',
        'error_message': 'A server error occurred. Please try again later.'
    }, status=500)

def custom_403_handler(request, exception):
    """Custom 403 error page"""
    return render(request, 'pages/error.html', {
        'error_code': '403',
        'error_title': 'Access Denied',
        'error_message': 'You do not have permission to access this page.'
    }, status=403)

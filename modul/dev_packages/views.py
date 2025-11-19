from django.http import JsonResponse, HttpRequest, HttpResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from .services import SERVICES
from .services import python_service, ruby_service, node_service, php_service, rust_service, go_service, dotnet_service
from .services import cve_scanner


@login_required
def index_view(request: HttpRequest) -> HttpResponse:
    return render(request, 'modules/dev_packages/index.html')


@require_GET
@login_required
def summary_api(request: HttpRequest) -> JsonResponse:
    scope = request.GET.get('scope', 'global')
    force_refresh = request.GET.get('refresh', 'false').lower() == 'true'
    
    cache_key = f'dev_packages_summary_{scope}'
    
    # Try cache first (unless force refresh)
    if not force_refresh:
        cached_data = cache.get(cache_key)
        if cached_data:
            return JsonResponse(cached_data)
    
    managers = {}
    total = 0
    for name, svc in SERVICES.items():
        try:
            if hasattr(svc, 'detect') and not svc.detect():
                continue
            # We don't have updates yet; expose presence and installed count for UI
            items = svc.list_installed(scope)
            count = 0  # updates placeholder
            critical = 0
            managers[name] = {
                'count': count,
                'critical': critical,
                'installed': len(items),
            }
            total += count
        except Exception:
            continue
    
    data = {'managers': managers, 'total_updates': total, 'scope': scope}
    
    # Cache for 5 minutes
    cache.set(cache_key, data, timeout=300)
    
    return JsonResponse(data)


@require_GET
@login_required
def installed_api(request: HttpRequest) -> JsonResponse:
    scope = request.GET.get('scope', 'global')
    force_refresh = request.GET.get('refresh', 'false').lower() == 'true'
    include_cves = request.GET.get('cves', 'false').lower() == 'true'
    
    cache_key = f'dev_packages_installed_{scope}'
    cve_cache_key = f'dev_packages_cves_{scope}'
    
    # Try cache first (unless force refresh)
    if not force_refresh:
        cached_data = cache.get(cache_key)
        if cached_data and not include_cves:
            return JsonResponse(cached_data, safe=False)
    
    result = {}
    for name, svc in SERVICES.items():
        try:
            items = svc.list_installed(scope)
            # Fallback: if project scope is empty, try global to show system-level packages
            if scope == 'project' and not items:
                items = svc.list_installed('global')
        except Exception:
            items = []
        result[name] = items
    
    # If CVE scanning is requested, scan all packages
    if include_cves:
        try:
            cve_results = cve_scanner.scan_packages(result)
            # Add CVE information to each package
            for manager, packages in result.items():
                manager_cves = cve_results.get(manager, {})
                for pkg in packages:
                    pkg_name = pkg.get('name', '')
                    if pkg_name in manager_cves:
                        pkg['cves'] = manager_cves[pkg_name]
                        # Add summary counts
                        pkg['cve_count'] = len(manager_cves[pkg_name])
                        # Count by severity
                        severity_counts = {}
                        for vuln in manager_cves[pkg_name]:
                            severity = vuln.get('severity', 'UNKNOWN')
                            if isinstance(severity, dict):
                                severity = severity.get('severity', 'UNKNOWN')
                            severity_counts[severity] = severity_counts.get(severity, 0) + 1
                        pkg['cve_severity'] = severity_counts
                    else:
                        pkg['cves'] = []
                        pkg['cve_count'] = 0
                        pkg['cve_severity'] = {}
        except Exception as e:
            # If CVE scanning fails, continue without CVE data
            print(f"CVE scanning error: {str(e)}")
            pass
    
    # Cache for 5 minutes
    cache.set(cache_key, result, timeout=300)
    
    return JsonResponse(result, safe=False)


@require_GET
@login_required
def updates_api(request: HttpRequest) -> JsonResponse:
    scope = request.GET.get('scope', 'global')
    force_refresh = request.GET.get('refresh', 'false').lower() == 'true'
    
    cache_key = f'dev_packages_updates_{scope}'
    
    # Try cache first (unless force refresh)
    if not force_refresh:
        cached_data = cache.get(cache_key)
        if cached_data:
            return JsonResponse(cached_data)
    
    result = {}
    for name, svc in SERVICES.items():
        try:
            if hasattr(svc, 'list_outdated'):
                items = svc.list_outdated(scope)
            else:
                items = []
        except Exception:
            items = []
        result[name] = items
    
    data = {'success': True, 'data': result, 'scope': scope}
    
    # Cache for 5 minutes
    cache.set(cache_key, data, timeout=300)
    
    return JsonResponse(data)


@require_GET
@login_required
def detail_api(request: HttpRequest, manager: str, name: str) -> JsonResponse:
    if manager == 'pip':
        data = python_service.get_details(name)
        return JsonResponse({'manager': manager, **data})
    if manager == 'gem':
        data = ruby_service.get_details(name)
        return JsonResponse({'manager': manager, **data})
    if manager == 'npm':
        data = node_service.get_details(name)
        return JsonResponse({'manager': manager, **data})
    if manager == 'composer':
        data = php_service.get_details(name)
        return JsonResponse({'manager': manager, **data})
    if manager == 'cargo':
        data = rust_service.get_details(name)
        return JsonResponse({'manager': manager, **data})
    if manager == 'go':
        data = go_service.get_details(name)
        return JsonResponse({'manager': manager, **data})
    if manager == 'dotnet':
        data = dotnet_service.get_details(name)
        return JsonResponse({'manager': manager, **data})
    # Default empty for other managers (to be implemented)
    return JsonResponse({'manager': manager, 'name': name, 'fields': {}, 'dependencies': []})


@require_GET
@login_required
def cves_api(request: HttpRequest) -> JsonResponse:
    """API endpoint to get CVE information for packages"""
    scope = request.GET.get('scope', 'global')
    force_refresh = request.GET.get('refresh', 'false').lower() == 'true'
    
    cache_key = f'dev_packages_cves_{scope}'
    
    # Try cache first (unless force refresh)
    if not force_refresh:
        cached_data = cache.get(cache_key)
        if cached_data:
            return JsonResponse(cached_data)
    
    # Get installed packages
    packages_by_manager = {}
    for name, svc in SERVICES.items():
        try:
            if hasattr(svc, 'detect') and not svc.detect():
                continue
            items = svc.list_installed(scope)
            if scope == 'project' and not items:
                items = svc.list_installed('global')
        except Exception:
            items = []
        packages_by_manager[name] = items
    
    # Scan for CVEs
    try:
        cve_results = cve_scanner.scan_packages(packages_by_manager)
        
        # Cache for 1 hour (CVE data doesn't change frequently)
        cache.set(cache_key, cve_results, timeout=3600)
        
        return JsonResponse({'success': True, 'data': cve_results, 'scope': scope})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_GET
@login_required
def package_cves_api(request: HttpRequest, manager: str, name: str) -> JsonResponse:
    """API endpoint to get CVE information for a specific package"""
    version = request.GET.get('version', '')
    
    if not version:
        return JsonResponse({'success': False, 'error': 'Version parameter is required'}, status=400)
    
    try:
        cves = cve_scanner.get_package_cves(manager, name, version)
        return JsonResponse({'success': True, 'package': name, 'version': version, 'manager': manager, 'cves': cves})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)



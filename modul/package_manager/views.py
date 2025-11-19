import json
from django.http import JsonResponse, HttpRequest, HttpResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET
from django.contrib.auth.decorators import login_required
from .services.scanner import PackageScanner


scanner = PackageScanner()


@login_required
def index_view(request: HttpRequest) -> HttpResponse:
    return render(request, 'modules/package_manager/index.html')


@require_GET
@login_required
def summary_api(request: HttpRequest) -> JsonResponse:
    summary = scanner.get_updates_summary()
    return JsonResponse(summary, safe=False)


@require_GET
@login_required
def installed_api(request: HttpRequest) -> JsonResponse:
    installed = scanner.get_installed_packages()
    return JsonResponse(installed, safe=False)


@require_GET
@login_required
def detail_api(request: HttpRequest, manager: str, package_name: str) -> JsonResponse:
    details = scanner.get_package_details(manager, package_name)
    return JsonResponse(details, safe=False)


@require_GET
@login_required
def updates_api(request: HttpRequest) -> JsonResponse:
    data = scanner.get_upgradeable_packages()
    return JsonResponse({'success': True, 'data': data})



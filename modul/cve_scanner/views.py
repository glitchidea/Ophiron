import json
import os
from django.http import JsonResponse, HttpRequest, HttpResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_POST

from .os import main as os_main


BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))


def get_cache_paths(os_type: str):
    """Get cache paths for a given OS type"""
    cache_dir = os.path.join(BASE_DIR, "cache", os_type)
    matched_path = os.path.join(cache_dir, "matched.json")
    installed_path = os.path.join(cache_dir, "installed.json")
    return matched_path, installed_path


def get_os_display_name(os_handler):
    """Get display name for the OS"""
    if os_handler is None:
        return "Unknown"
    current_os = os_main.detect_os()
    if current_os == "arch":
        return "Arch Linux"
    elif current_os == "fedora":
        return "Fedora"
    elif current_os == "ubuntu":
        return "Ubuntu"
    elif current_os == "debian":
        return "Debian"
    return "Unknown"


@require_GET
def index_view(request: HttpRequest) -> HttpResponse:
    os_handler = os_main.get_handler()
    matched = []
    totals = {"installed": 0, "advisories": 0, "matched": 0}

    # Load from cache if exists to render quickly
    current_os = os_main.detect_os()
    if current_os:
        matched_path, installed_path = get_cache_paths(current_os)
        
        if os.path.exists(matched_path):
            try:
                with open(matched_path, "r", encoding="utf-8") as f:
                    mobj = json.load(f)
                    matched = mobj.get("matched", [])
                    totals["matched"] = len(matched)
            except Exception:
                pass
        
        if os.path.exists(installed_path):
            try:
                with open(installed_path, "r", encoding="utf-8") as f:
                    iobj = json.load(f)
                    totals["installed"] = len(iobj.get("packages", []))
            except Exception:
                pass

    context = {
        "os_name": get_os_display_name(os_handler),
        "matched": matched,
        "totals": totals,
    }
    return render(request, "modules/cve_scanner/index.html", context)


@require_POST
def scan_view(request: HttpRequest) -> JsonResponse:
    handler = os_main.get_handler()
    if handler is None:
        return JsonResponse({"error": "Unsupported OS"}, status=400)

    try:
        result = handler.run_scan(force_refresh=bool(request.GET.get("refresh")), use_system=True)
        return JsonResponse({"ok": True, **result})
    except Exception as exc:
        return JsonResponse({"ok": False, "error": str(exc)}, status=500)


"""Known entry URLs beyond pure link discovery (paths are relative to host)."""

from urllib.parse import urljoin


def default_seed_paths(site_base: str) -> list[str]:
    """High-value hub pages + plausible IA routes (some may 404; crawler skips them)."""
    base = site_base.rstrip("/")
    rel = [
        "/",
        "/pages/projects-overview.html",
        "/pages/publications.html",
        "/pages/teaching.html",
        "/pages/methods-infrastructure.html",
        "/pages/questionnaires.html",
        "/past_project",
        "/pages/core-topic-xr.html",
        "/pages/core-topic-ass-tech.html",
        "/pages/core-topic-biosensors.html",
        "/pages/contact.html",
        "/pages/about.html",
        "/pages/imprint.html",
        "/pages/team.html",
        "/pages/people.html",
        "/pages/group-members.html",
    ]
    return [urljoin(base + "/", p.lstrip("/")) for p in rel]

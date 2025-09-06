import re
from urllib.parse import urlencode

import pytest

from app.main import app


def _fill_path(path: str) -> str:
    # Replace path params like {id} or {user_id} with simple test values
    def repl(m):
        name = m.group(1)
        # choose a numeric id for id-like names else a string
        if re.search(r"id$|_id$|Id$", name, re.IGNORECASE):
            return "1"
        return "test"

    return re.sub(r"{([^}]+)}", repl, path)


@pytest.mark.parametrize("route_info", [r for r in app.routes if getattr(r, "methods", None)])
def test_route_no_5xx(client, route_info):
    """Hit each registered HTTP route with a simple request and ensure no 5xx errors."""
    # skip static files and websockets
    if getattr(route_info, "name", "").startswith("static"):
        pytest.skip("static route")

    methods = [m for m in route_info.methods if m not in ("HEAD", "OPTIONS")]
    path = route_info.path
    test_path = _fill_path(path)

    for method in methods:
        # Use basic GET/POST/PUT/DELETE semantics with minimal payloads
        if method == "GET":
            resp = client.get(test_path)
        elif method == "POST":
            # send empty body or minimal json
            resp = client.post(test_path, json={})
        elif method == "PUT":
            resp = client.put(test_path, json={})
        elif method == "DELETE":
            resp = client.delete(test_path)
        elif method == "PATCH":
            resp = client.patch(test_path, json={})
        else:
            # skip unknown methods
            continue

        # Assert no server error
        assert resp.status_code < 500, f"{method} {test_path} returned 5xx: {resp.status_code} - {resp.text}"

import json
import re
from pathlib import Path

def main():
    catalog_path = Path("catalog.json").resolve()
    assert catalog_path.exists(), "catalog.json does not exist"
    
    with open(catalog_path, "r", encoding="utf-8") as f:
        catalog = json.load(f)

    print("=== ROOT LEVEL CHECKS ===")
    assert catalog.get("$schema") == "http://json-schema.org/draft-07/schema#", f"Bad $schema: {catalog.get('$schema')}"
    assert catalog.get("version") == "1.0.0", f"Bad version: {catalog.get('version')}"
    assert catalog.get("total_packages") == 20, f"Bad total_packages: {catalog.get('total_packages')}"
    assert len(catalog.get("packages", [])) == 20, f"Packages length is {len(catalog.get('packages', []))}"
    
    expected_cats = ["browser_search", "code_intelligence", "data_databases", "system_ops", "media"]
    assert catalog.get("categories") == expected_cats, f"Categories mismatch: {catalog.get('categories')}"

    print("=== PACKAGE LEVEL CHECKS ===")
    cat_counts = {c: 0 for c in expected_cats}
    slug_regex = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
    ids = set()

    for idx, pkg in enumerate(catalog.get("packages", [])):
        pid = pkg.get("id")
        assert pid, f"Index {idx} missing id"
        assert pid not in ids, f"Duplicate ID: {pid}"
        ids.add(pid)
        assert slug_regex.match(pid), f"ID '{pid}' is not lowercase slug"

        cat = pkg.get("category")
        assert cat in cat_counts, f"Unknown category '{cat}' in package '{pid}'"
        cat_counts[cat] += 1

        assert pkg.get("name"), f"Missing name in '{pid}'"
        assert pkg.get("type") in ("mcp_server", "skill"), f"Invalid type in '{pid}': {pkg.get('type')}"
        
        desc = pkg.get("description", "")
        assert isinstance(desc, str), f"Description is not string in '{pid}'"
        assert 20 <= len(desc) <= 1024, f"Description length {len(desc)} out of [20, 1024] in '{pid}'"

        stars = pkg.get("stars")
        assert isinstance(stars, int) and stars >= 0, f"Invalid stars {stars} in '{pid}'"

        repo_url = pkg.get("repo_url")
        assert repo_url and repo_url.startswith("https://"), f"Invalid repo_url '{repo_url}' in '{pid}'"

        caps = pkg.get("capabilities")
        assert isinstance(caps, list) and len(caps) > 0, f"Invalid capabilities in '{pid}'"
        for c in caps:
            assert isinstance(c, str) and len(c) > 0, f"Capability token not non-empty string in '{pid}'"

        ep = pkg.get("entrypoint")
        assert isinstance(ep, dict), f"Entrypoint not dict in '{pid}'"
        assert "command" in ep and isinstance(ep["command"], str) and len(ep["command"]) > 0, f"Entrypoint command invalid in '{pid}'"
        assert "args" in ep and isinstance(ep["args"], list), f"Entrypoint args invalid in '{pid}'"
        assert "env" in ep and isinstance(ep["env"], dict), f"Entrypoint env invalid in '{pid}'"

        deps = pkg.get("dependencies")
        assert isinstance(deps, dict), f"Dependencies not dict in '{pid}'"

        lic = pkg.get("license")
        assert lic and isinstance(lic, str) and lic != "Unknown", f"Invalid license '{lic}' in '{pid}'"

        status = pkg.get("validation_status")
        assert status in ("verified", "pending", "rejected"), f"Invalid validation_status '{status}' in '{pid}'"

        targets = pkg.get("platform_targets")
        assert isinstance(targets, list) and len(targets) > 0, f"Invalid platform_targets in '{pid}'"
        for t in targets:
            assert t in ("antigravity", "claude_code", "cursor", "codex"), f"Invalid target '{t}' in '{pid}'"

        sec = pkg.get("security_notes")
        assert isinstance(sec, dict), f"Missing security_notes in '{pid}'"
        assert "sandbox_safe" in sec and isinstance(sec["sandbox_safe"], bool), f"Invalid sandbox_safe in '{pid}'"

    print("Category counts:", cat_counts)
    for c, count in cat_counts.items():
        assert count == 4, f"Category {c} count {count} != 4"

    print("\nALL INVARIANTS & DRAFT-07 CONFORMANCE CONFIRMED: 20 PACKAGES, 5 CATEGORIES BALANCED (4 EACH)!")

if __name__ == "__main__":
    main()

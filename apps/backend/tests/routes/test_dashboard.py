"""
test_dashboard.py — Phase 7.5: Tests for the Dashboard route.

Covers:
- GET /me/dashboard → returns correct counts
- GET /me/dashboard → returns zeros when no data exists
"""


def test_get_dashboard(
    client,
    repository,
    agent_run,
    succeeded_agent_run,
    usage_record,
    test_user,
):
    """GET /me/dashboard returns correct aggregated counts."""
    response = client.get("/me/dashboard")
    assert response.status_code == 200
    data = response.json()

    # 1 repository
    assert data["repository_count"] == 1

    # agent_run is queued → counts as active; succeeded_agent_run is succeeded → not active
    assert data["active_run_count"] == 1

    # 1 succeeded run
    assert data["succeeded_run_count"] == 1

    # usage_record has run_count=5
    assert data["today_run_count"] == 5

    # test_user has daily_run_quota=15
    assert data["daily_run_quota"] == 15


def test_get_dashboard_empty(client, test_user):
    """GET /me/dashboard returns zeros when user has no data."""
    response = client.get("/me/dashboard")
    assert response.status_code == 200
    data = response.json()
    assert data["repository_count"] == 0
    assert data["active_run_count"] == 0
    assert data["succeeded_run_count"] == 0
    assert data["today_run_count"] == 0
    assert data["daily_run_quota"] == 15

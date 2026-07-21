from extensions import db
from models.user import User, UserRole


def test_dashboard_stats_endpoint(client):
    """Test GET /api/dashboard/stats returns correct user metrics."""
    res_signup = client.post("/api/auth/signup", json={
        "username": "dashuser",
        "email": "dashuser@example.com",
        "password": "password123",
        "full_name": "Dash User",
        "bio": "Developer",
    })
    token = res_signup.get_json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    client.post("/api/fellows", json={"name": "Alice Smith", "relation": "Friend"}, headers=headers)
    client.post("/api/fellows", json={"name": "Bob Jones", "relation": "Colleague"}, headers=headers)

    res_stats = client.get("/api/dashboard/stats", headers=headers)
    assert res_stats.status_code == 200
    data = res_stats.get_json()
    assert data["total_fellows"] == 2
    assert data["recent_fellows_7d"] == 2
    assert data["profile_completeness_pct"] > 0
    assert data["is_verified"] is False


def test_fellows_search_pagination_sorting(client):
    """Test GET /api/fellows with q, page, limit, sort, and order parameters."""
    res_signup = client.post("/api/auth/signup", json={
        "username": "queryuser",
        "email": "queryuser@example.com",
        "password": "password123",
    })
    token = res_signup.get_json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    client.post("/api/fellows", json={"name": "Charlie Brown", "relation": "Classmate", "email": "charlie@example.com"}, headers=headers)
    client.post("/api/fellows", json={"name": "Alpha Beta", "relation": "Doctor", "email": "alpha@example.com"}, headers=headers)
    client.post("/api/fellows", json={"name": "Zebra Zoo", "relation": "Classmate", "email": "zebra@example.com"}, headers=headers)

    # Search filter
    res_search = client.get("/api/fellows?q=Classmate", headers=headers)
    assert res_search.status_code == 200
    search_data = res_search.get_json()
    assert search_data["total"] == 2
    assert len(search_data["items"]) == 2

    # Pagination
    res_page1 = client.get("/api/fellows?limit=2&page=1", headers=headers)
    assert res_page1.status_code == 200
    page1_data = res_page1.get_json()
    assert page1_data["total"] == 3
    assert page1_data["pages"] == 2
    assert len(page1_data["items"]) == 2

    # Sorting
    res_sort = client.get("/api/fellows?sort=name&order=asc", headers=headers)
    assert res_sort.status_code == 200
    sorted_items = res_sort.get_json()["items"]
    assert sorted_items[0]["name"] == "Alpha Beta"
    assert sorted_items[-1]["name"] == "Zebra Zoo"


def test_admin_view_all_fellows(app, client):
    """Test Admin user can view all system fellows with all=true."""
    t1 = client.post("/api/auth/signup", json={"username": "u1", "email": "u1@example.com", "password": "password123"}).get_json()["access_token"]
    client.post("/api/fellows", json={"name": "U1 Fellow"}, headers={"Authorization": f"Bearer {t1}"})

    t2 = client.post("/api/auth/signup", json={"username": "admin2", "email": "admin2@example.com", "password": "password123"}).get_json()["access_token"]
    with app.app_context():
        admin_user = User.query.filter_by(email="admin2@example.com").first()
        admin_user.role = UserRole.ADMIN
        db.session.commit()

    client.post("/api/fellows", json={"name": "Admin Fellow"}, headers={"Authorization": f"Bearer {t2}"})

    res_my = client.get("/api/fellows?all=false", headers={"Authorization": f"Bearer {t2}"})
    assert res_my.get_json()["total"] == 1

    res_all = client.get("/api/fellows?all=true", headers={"Authorization": f"Bearer {t2}"})
    assert res_all.get_json()["total"] == 2
    assert res_all.get_json()["is_admin_all"] is True

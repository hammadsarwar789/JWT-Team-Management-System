import time
from auth.utils import generate_token


def test_dashboard_stats_endpoint(client):
    """Test GET /api/dashboard/stats returns correct user metrics."""
    # Signup user
    res_signup = client.post("/api/auth/signup", json={
        "username": "dashuser",
        "email": "dashuser@example.com",
        "password": "password123",
        "full_name": "Dash User",
        "bio": "Developer",
    })
    token = res_signup.get_json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Add 2 fellows
    client.post("/api/fellows", json={"name": "Alice Smith", "relation": "Friend"}, headers=headers)
    client.post("/api/fellows", json={"name": "Bob Jones", "relation": "Colleague"}, headers=headers)

    # Get stats
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

    # Add 3 fellows
    client.post("/api/fellows", json={"name": "Charlie Brown", "relation": "Classmate", "email": "charlie@example.com"}, headers=headers)
    client.post("/api/fellows", json={"name": "Alpha Beta", "relation": "Doctor", "email": "alpha@example.com"}, headers=headers)
    client.post("/api/fellows", json={"name": "Zebra Zoo", "relation": "Classmate", "email": "zebra@example.com"}, headers=headers)

    # 1. Test Search (q=Classmate) -> should match Charlie Brown and Zebra Zoo
    res_search = client.get("/api/fellows?q=Classmate", headers=headers)
    assert res_search.status_code == 200
    search_data = res_search.get_json()
    assert search_data["total"] == 2
    assert len(search_data["items"]) == 2

    # 2. Test Pagination (limit=2, page=1)
    res_page1 = client.get("/api/fellows?limit=2&page=1", headers=headers)
    assert res_page1.status_code == 200
    page1_data = res_page1.get_json()
    assert page1_data["total"] == 3
    assert page1_data["pages"] == 2
    assert len(page1_data["items"]) == 2

    # 3. Test Sorting (sort=name&order=asc) -> Alpha Beta first, Zebra Zoo last
    res_sort = client.get("/api/fellows?sort=name&order=asc", headers=headers)
    assert res_sort.status_code == 200
    sorted_items = res_sort.get_json()["items"]
    assert sorted_items[0]["name"] == "Alpha Beta"
    assert sorted_items[-1]["name"] == "Zebra Zoo"


def test_admin_view_all_fellows(client, mock_db):
    """Test Admin user can view all system fellows with all=true."""
    from extensions import users_collection
    from models.user import UserRole

    # User 1
    t1 = client.post("/api/auth/signup", json={"username": "u1", "email": "u1@example.com", "password": "password123"}).get_json()["access_token"]
    client.post("/api/fellows", json={"name": "U1 Fellow"}, headers={"Authorization": f"Bearer {t1}"})

    # Admin User 2
    t2 = client.post("/api/auth/signup", json={"username": "admin2", "email": "admin2@example.com", "password": "password123"}).get_json()["access_token"]
    users_collection.update_one({"email": "admin2@example.com"}, {"$set": {"role": UserRole.ADMIN}})
    client.post("/api/fellows", json={"name": "Admin Fellow"}, headers={"Authorization": f"Bearer {t2}"})

    # Admin my contacts only view (all=false)
    res_my = client.get("/api/fellows?all=false", headers={"Authorization": f"Bearer {t2}"})
    assert res_my.get_json()["total"] == 1

    # Admin all view (all system contacts)
    res_all = client.get("/api/fellows?all=true", headers={"Authorization": f"Bearer {t2}"})
    assert res_all.get_json()["total"] == 2
    assert res_all.get_json()["is_admin_all"] is True




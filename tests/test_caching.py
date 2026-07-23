def test_endpoint_caching_and_invalidation(client):
    reg = client.post("/api/v1/auth/signup", json={
        "username": "cacheuser",
        "email": "cache@example.com",
        "password": "password123"
    })
    token = reg.get_json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Add a fellow
    client.post("/api/v1/fellows", json={"name": "Fellow One"}, headers=headers)

    # First GET -> Cache MISS
    res1 = client.get("/api/v1/fellows", headers=headers)
    assert res1.status_code == 200
    assert res1.headers.get("X-Cache") == "MISS"

    # Second GET -> Cache HIT
    res2 = client.get("/api/v1/fellows", headers=headers)
    assert res2.status_code == 200
    assert res2.headers.get("X-Cache") == "HIT"

    # Add another fellow -> Cache should be invalidated
    client.post("/api/v1/fellows", json={"name": "Fellow Two"}, headers=headers)

    # Third GET -> Cache MISS again (fresh query result)
    res3 = client.get("/api/v1/fellows", headers=headers)
    assert res3.status_code == 200
    assert res3.headers.get("X-Cache") == "MISS"
    data = res3.get_json()
    assert len(data.get("items", data.get("fellows", []))) == 2


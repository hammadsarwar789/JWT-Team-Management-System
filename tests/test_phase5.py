import io


def test_export_import_fellows(client):
    """Test CSV & JSON export and import endpoints."""
    res_signup = client.post("/api/v1/auth/signup", json={
        "username": "expuser",
        "email": "expuser@example.com",
        "password": "password123",
    })
    token = res_signup.get_json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    client.post("/api/v1/fellows", json={"name": "Exporter One", "email": "one@example.com", "relation": "Friend"}, headers=headers)
    client.post("/api/v1/fellows", json={"name": "Exporter Two", "email": "two@gmail.com", "relation": "Colleague"}, headers=headers)

    # Export CSV
    res_csv = client.get("/api/v1/fellows/export?format=csv", headers=headers)
    assert res_csv.status_code == 200
    assert "text/csv" in res_csv.mimetype
    csv_text = res_csv.data.decode("utf-8")
    assert "Exporter One" in csv_text
    assert "Exporter Two" in csv_text

    # Export JSON
    res_json = client.get("/api/v1/fellows/export?format=json", headers=headers)
    assert res_json.status_code == 200
    assert "application/json" in res_json.mimetype

    # Import CSV into a new user
    res_new_user = client.post("/api/v1/auth/signup", json={
        "username": "impuser",
        "email": "impuser@example.com",
        "password": "password123",
    })
    token2 = res_new_user.get_json()["access_token"]
    headers2 = {"Authorization": f"Bearer {token2}"}

    csv_data = "name,email,relation,notes\nImported Candidate,imported@domain.com,Classmate,Test note\n"
    data = {
        "file": (io.BytesIO(csv_data.encode("utf-8")), "contacts.csv")
    }

    res_import = client.post(
        "/api/v1/fellows/import",
        data=data,
        content_type="multipart/form-data",
        headers=headers2,
    )
    assert res_import.status_code == 200
    assert res_import.get_json()["count"] == 1

    res_list = client.get("/api/v1/fellows", headers=headers2)
    assert res_list.get_json()["total"] == 1


def test_contact_file_attachment(client):
    """Test attaching a document file to a fellow contact."""
    res_signup = client.post("/api/v1/auth/signup", json={
        "username": "attachuser",
        "email": "attachuser@example.com",
        "password": "password123",
    })
    token = res_signup.get_json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    res_add = client.post("/api/v1/fellows", json={"name": "Fellow With File"}, headers=headers)
    fellow_id = res_add.get_json()["id"]

    data = {
        "file": (io.BytesIO(b"Dummy PDF content"), "resume.pdf")
    }
    res_attach = client.post(
        f"/api/v1/fellows/{fellow_id}/attachments",
        data=data,
        content_type="multipart/form-data",
        headers=headers,
    )
    assert res_attach.status_code == 200
    fellow = res_attach.get_json()["fellow"]
    assert len(fellow["attachments"]) == 1
    assert fellow["attachments"][0]["filename"] == "resume.pdf"

    res_del_att = client.delete(f"/api/v1/fellows/{fellow_id}/attachments/resume.pdf", headers=headers)
    assert res_del_att.status_code == 200


def test_analytics_summary_endpoint(client):
    """Test GET /api/v1/analytics/summary endpoint."""
    res_signup = client.post("/api/v1/auth/signup", json={
        "username": "analyticsuser",
        "email": "analyticsuser@example.com",
        "password": "password123",
    })
    token = res_signup.get_json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    client.post("/api/v1/fellows", json={"name": "A1", "email": "a1@gmail.com", "relation": "Friend"}, headers=headers)
    client.post("/api/v1/fellows", json={"name": "A2", "email": "a2@gmail.com", "relation": "Friend"}, headers=headers)
    client.post("/api/v1/fellows", json={"name": "A3", "email": "a3@company.org", "relation": "Colleague"}, headers=headers)

    res_analytics = client.get("/api/v1/analytics/summary", headers=headers)
    assert res_analytics.status_code == 200
    data = res_analytics.get_json()
    assert data["total_contacts"] == 3
    assert data["relations"]["Friend"] == 2
    assert data["relations"]["Colleague"] == 1
    assert data["email_domains"]["gmail.com"] == 2

def test_create_account(api_client):
    resp = api_client.post("/account", json={"account_number": "1234"})
    assert resp.status_code == 200
    result = resp.json()
    result.pop("id")
    assert result == {
        "number": "1234",
        "balance": 0,
        "version": 1,
    }


def test_deposit(api_client):
    account_id = api_client.post("/account", json={"account_number": "1234"}).json()[
        "id"
    ]
    resp = api_client.post(f"/account/{account_id}/deposit", json={"amount": 100})
    assert resp.status_code == 200

    resp = api_client.get(f"/account/{account_id}")
    result = resp.json()
    result.pop("id")
    assert result == {
        "number": "1234",
        "balance": 100,
        "version": 2,
    }


def test_withdraw(api_client):
    account_id = api_client.post("/account", json={"account_number": "1234"}).json()[
        "id"
    ]
    resp = api_client.post(f"/account/{account_id}/withdraw", json={"amount": 100})
    assert resp.status_code == 200

    resp = api_client.get(f"/account/{account_id}")
    result = resp.json()
    result.pop("id")
    assert result == {
        "number": "1234",
        "balance": -100,
        "version": 2,
    }


def test_transfer(api_client, run_background_processing):
    from_account_id = api_client.post(
        "/account", json={"account_number": "1234"}
    ).json()["id"]
    to_account_id = api_client.post("/account", json={"account_number": "5678"}).json()[
        "id"
    ]
    resp = api_client.post(
        "/transfer",
        json={
            "from_account_id": from_account_id,
            "to_account_id": to_account_id,
            "amount": 100,
        },
    )
    assert resp.status_code == 200
    result = resp.json()
    transfer_id = result.pop("id")
    assert result == {
        "from_account_id": from_account_id,
        "to_account_id": to_account_id,
        "amount": 100,
        "status": "initial",
    }

    run_background_processing(3)

    resp = api_client.get(f"/transfer/{transfer_id}")
    assert resp.status_code == 200
    assert resp.json()["status"] == "withdrawn"

    run_background_processing(3)

    resp = api_client.get(f"/transfer/{transfer_id}")
    assert resp.status_code == 200
    assert resp.json()["status"] == "finished"

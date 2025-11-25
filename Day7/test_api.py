# tests/integration/test_api.py
def test_create_product_api(client):
    product_data = {
        "name": "API Test Product",
        "description": "API Test Description",
        "price": 29.99,
        "quantity": 50,
        "category": "Books",
    }

    response = client.post("/products/", json=product_data)

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == product_data["name"]
    assert data["price"] == product_data["price"]
    assert "id" in data


def test_get_products_api(client):
    response = client.get("/products/")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

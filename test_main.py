from fastapi.testclient import TestClient

from FastAPITask.main import app

client = TestClient(app)


def test_asin():
    response = client.get('/get_price/B004F829LQ')
    assert response.status_code == 200
    assert response.json()['price'] == 9.04

    response2 = client.get('/get_price/B07VRQWBMR')
    assert response2.status_code == 200
    assert response2.json()['price'] == 57.01

    response3 = client.get('/get_price/B07VMM5LKH')
    assert response3.status_code == 200
    assert response3.json()['price'] == 44.04

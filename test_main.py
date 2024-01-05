from fastapi.testclient import TestClient

from FastAPITask.main import app

client = TestClient(app)


def test_asin():
    response = client.get('/get_price/B004F829LQ')
    assert response.status_code == 200
    assert response.json()['text'] == 'Product is unavailable or has no price'

    response2 = client.get('/get_price/B0CNWVZSM4')
    assert response2.status_code == 200
    assert response2.json()['price'] == 9.80

    response3 = client.get('/get_price/B07VMM5LKH')
    assert response3.status_code == 200
    assert response3.json()['price'] == 44.04

    response4 = client.get('/get_price/B09MV14LJB')
    assert response4.status_code == 200
    assert response4.json()['text'] == 'Product is unavailable or has no price'

    response5 = client.get('/get_price/B074PH7YMC')
    assert response5.status_code == 200
    assert response5.json()['text'] == 'Product is unavailable or has no price'



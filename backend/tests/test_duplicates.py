from app.services.duplicates import haversine_m

def test_haversine_same_point():
    assert haversine_m(19.69, 72.77, 19.69, 72.77) == 0

def test_haversine_nearby_points():
    distance = haversine_m(19.69, 72.77, 19.6901, 72.77)
    assert 10 < distance < 12

from django.test import TestCase
from .models import Aircraft

class AircraftModelTest(TestCase):
    def setUp(self):
        self.aircraft = Aircraft.objects.create(name='TB2')

    def test_aircraft_str(self):
        self.assertEqual(str(self.aircraft), 'TB2')

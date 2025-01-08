from django.db import models
from django.contrib.auth.models import User

class Aircraft(models.Model):
    name = models.CharField(max_length=50)
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return self.name
    
class PartType(models.Model):
    name = models.CharField(max_length=50)
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return self.name
    

class Team(models.Model):
    name = models.CharField(max_length=50)
    responsible_part = models.ForeignKey(PartType, on_delete=models.CASCADE,null=True)
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class Personnel(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username
    
STATUS_CHOICES = [
    ('stock', 'Stokta'),
    ('used', 'Kullanılmış')
]

class AircraftPartRequirement(models.Model):
    """Her uçak modeli için gerekli parça sayısını tutan model"""
    aircraft = models.ForeignKey(Aircraft, on_delete=models.CASCADE)
    part_type = models.ForeignKey(PartType, on_delete=models.CASCADE)
    required_quantity = models.PositiveIntegerField()
    
    class Meta:
        unique_together = ['aircraft', 'part_type']

    def __str__(self):
        return f"{self.aircraft.name} - {self.part_type.name}: {self.required_quantity}"

class Part(models.Model):
    part_type = models.ForeignKey(PartType, on_delete=models.CASCADE, null=True)
    aircraft = models.ForeignKey(Aircraft, on_delete=models.CASCADE)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='stock')
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.part_type.name} ({self.aircraft.name})"
    
    def clean(self):
        from django.core.exceptions import ValidationError
        # Üretim takımının sorumlu olduğu parça tipini kontrol et
        if self.team.responsible_part != self.part_type:
            raise ValidationError(
                f"{self.team.name} takımı {self.part_type.name} üretemez."
            )
    
class ProducedAircraft(models.Model):
    aircraft = models.ForeignKey(Aircraft, on_delete=models.CASCADE)
    parts = models.ManyToManyField(Part,through='AircraftPart' )
    date = models.DateTimeField(auto_now_add=True)
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.aircraft.name} - {self.date.strftime('%Y-%m-%d %H:%M:%S')}"

class AircraftPart(models.Model):
    produced_aircraft = models.ForeignKey(ProducedAircraft, on_delete=models.CASCADE)
    part = models.ForeignKey(Part, on_delete=models.CASCADE)

    def save(self, *args, **kwargs):
        if self.part.status != 'stock':
            raise ValueError("Bu parça zaten kullanılmış ")
        self.part.status = 'used'
        self.part.save()
        super().save(*args, **kwargs)
        Part.objects.filter(id=self.part.id).update(status='used')

class PartStock(models.Model):
    part_type = models.ForeignKey(PartType, on_delete=models.CASCADE)
    stock_quantity = models.PositiveIntegerField(default=0)
    is_deleted = models.BooleanField(default=False)
    aircraft = models.ForeignKey(
        Aircraft, 
        on_delete=models.CASCADE,
        null=True,  # Geçici olarak null'a izin ver
        default=None  # Varsayılan değer None
    )

    class Meta:
        unique_together = ['part_type', 'aircraft']

    def __str__(self):
        return f"{self.part_type.name} - {self.stock_quantity}"



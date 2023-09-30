from django.db import models

# Create your models here.

class Car(models.Model):
    make = models.CharField(max_length=255, verbose_name="Car Make")
    car_model = models.CharField(max_length=255, verbose_name="Car Model")
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    mileage = models.PositiveIntegerField()
    owners = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.make} {self.car_model}"
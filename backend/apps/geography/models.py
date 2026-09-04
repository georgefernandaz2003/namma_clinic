from django.db import models

class State(models.Model):
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=10, unique=True)

    def __str__(self):
        return self.name

class District(models.Model):
    state = models.ForeignKey(State, on_delete=models.CASCADE, related_name='districts')
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)

    def __str__(self):
        return f"{self.name} ({self.state.name})"

class Zone(models.Model):
    district = models.ForeignKey(District, on_delete=models.CASCADE, related_name='zones')
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20)

    def __str__(self):
        return f"{self.name} - {self.district.name}"

class Ward(models.Model):
    zone = models.ForeignKey(Zone, on_delete=models.CASCADE, related_name='wards')
    ward_number = models.IntegerField()
    name = models.CharField(max_length=100)
    population = models.IntegerField(default=20000)
    slum_population = models.IntegerField(default=5000)

    def __str__(self):
        return f"Ward {self.ward_number}: {self.name} ({self.zone.name})"

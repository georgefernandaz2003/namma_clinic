from django.db import models

class WellnessSession(models.Model):
    facility = models.ForeignKey('facilities.Facility', on_delete=models.CASCADE)
    session_type = models.CharField(max_length=50, default='Yoga & Meditation')
    instructor_name = models.CharField(max_length=150, default='Certified AYUSH Yoga Instructor')
    session_date = models.DateField()
    session_time = models.CharField(max_length=30, default='07:00 AM - 08:00 AM')
    venue = models.CharField(max_length=150, default='Namma Clinic Wellness Area / Local Park')
    participants_count = models.IntegerField(default=25)
    incentive_amount_rs = models.DecimalField(max_digits=6, decimal_places=2, default=250.00)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.session_type} on {self.session_date} ({self.participants_count} attendees)"

from django.db import models

class ComplianceItem(models.Model):
    requirement_id = models.CharField(max_length=50, unique=True)
    requirement_text = models.TextField()
    source_document = models.CharField(max_length=100) # ULB ROK Booklet or K Mati Proposal
    classification = models.CharField(max_length=50) # OFFICIAL BOOKLET REQUIREMENT, K MATI PROPOSAL, DERIVED TECHNICAL REQUIREMENT, DEMO ENHANCEMENT
    application_module = models.CharField(max_length=100)
    status = models.CharField(max_length=30, choices=[
        ('FULLY_COVERED', 'Fully Covered'),
        ('PARTIALLY_COVERED', 'Partially Covered'),
        ('NOT_IMPLEMENTED', 'Not Implemented'),
        ('OUT_OF_DIGITAL_SCOPE', 'Out of Digital Scope')
    ], default='FULLY_COVERED')
    explanation = models.TextField()

    def __str__(self):
        return f"[{self.status}] {self.requirement_id}: {self.requirement_text[:40]}"

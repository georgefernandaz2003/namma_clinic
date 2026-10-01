from rest_framework import serializers
from apps.patients.models import Patient, Household, PatientDocument

class PatientSerializer(serializers.ModelSerializer):
    ward_name = serializers.ReadOnlyField(source='ward.name')
    district_name = serializers.ReadOnlyField(source='district.name')
    facility_name = serializers.ReadOnlyField(source='registered_at_facility.facility_name')

    class Meta:
        model = Patient
        fields = '__all__'

    def validate(self, attrs):
        facility = attrs.get('registered_at_facility') or getattr(self.instance, 'registered_at_facility', None)
        district = attrs.get('district') or getattr(self.instance, 'district', None)
        ward = attrs.get('ward') or getattr(self.instance, 'ward', None)

        if facility:
            facility_dist = getattr(facility, 'district', None)
            if facility_dist:
                if not district:
                    attrs['district'] = facility_dist
                elif district.id != facility_dist.id:
                    raise serializers.ValidationError({
                        'district': f"Patient district ({district.name}) must match registration facility district ({facility_dist.name})."
                    })
        if ward and district:
            ward_dist = getattr(ward, 'district', None)
            if ward_dist and ward_dist.id != district.id:
                raise serializers.ValidationError({
                    'ward': f"Patient ward ({ward.name}) does not belong to district ({district.name})."
                })
        return attrs

class HouseholdSerializer(serializers.ModelSerializer):
    ward_name = serializers.ReadOnlyField(source='ward.name')

    class Meta:
        model = Household
        fields = '__all__'

import os

ALLOWED_DOCUMENT_EXTENSIONS = ['.pdf', '.jpg', '.jpeg', '.png', '.doc', '.docx']
MAX_FILE_SIZE_BYTES = 15 * 1024 * 1024  # 15 MB

class PatientDocumentSerializer(serializers.ModelSerializer):
    uploaded_by_name = serializers.SerializerMethodField()
    uploaded_by_role = serializers.SerializerMethodField()
    facility_name = serializers.ReadOnlyField(source='facility.facility_name')
    document_type_display = serializers.CharField(source='get_document_type_display', read_only=True)
    download_url = serializers.SerializerMethodField()

    class Meta:
        model = PatientDocument
        fields = [
            'id', 'patient', 'facility', 'facility_name', 'title', 'document_type',
            'document_type_display', 'file', 'file_name', 'file_size', 'mime_type',
            'document_date', 'uploaded_by', 'uploaded_by_name', 'uploaded_by_role',
            'uploaded_at', 'description', 'status', 'download_url'
        ]
        read_only_fields = ['patient', 'uploaded_by', 'uploaded_at', 'facility', 'file_name', 'file_size', 'mime_type']

    def get_uploaded_by_name(self, obj):
        if obj.uploaded_by:
            return obj.uploaded_by.full_name or obj.uploaded_by.username
        return 'Healthcare Staff'

    def get_uploaded_by_role(self, obj):
        if obj.uploaded_by:
            return getattr(obj.uploaded_by, 'role', '')
        return ''

    def get_download_url(self, obj):
        if obj.id and obj.patient_id:
            return f"/api/patients/{obj.patient_id}/documents/{obj.id}/download/"
        return ""

    def validate_file(self, value):
        if not value:
            raise serializers.ValidationError("File attachment is required.")
        
        ext = os.path.splitext(value.name)[1].lower()
        if ext not in ALLOWED_DOCUMENT_EXTENSIONS:
            raise serializers.ValidationError(
                f"Unsupported file type '{ext}'. Allowed medical document formats: PDF, JPG, JPEG, PNG, DOC, DOCX."
            )
        
        if value.size > MAX_FILE_SIZE_BYTES:
            size_mb = round(value.size / (1024 * 1024), 2)
            raise serializers.ValidationError(
                f"File size ({size_mb}MB) exceeds the allowed limit of 15MB."
            )
        
        return value

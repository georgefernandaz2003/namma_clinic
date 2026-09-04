from rest_framework import serializers, viewsets, permissions
from apps.integrations.models import IntegrationConfiguration

class IntegrationConfigurationSerializer(serializers.ModelSerializer):
    class Meta:
        model = IntegrationConfiguration
        fields = '__all__'

class IntegrationConfigurationViewSet(viewsets.ModelViewSet):
    queryset = IntegrationConfiguration.objects.all()
    serializer_class = IntegrationConfigurationSerializer
    permission_classes = [permissions.IsAuthenticated]

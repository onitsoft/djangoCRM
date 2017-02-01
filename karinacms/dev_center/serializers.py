from .models import Dev
from rest_framework import serializers

class DevSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
		model = Dev
		fields = ('first_name', 'last_name', 'phone',)
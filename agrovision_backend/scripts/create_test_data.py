import os
from decimal import Decimal
import django
from django.utils import timezone

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth.models import User
from cultivos.models import Cultivo
from lotes.models import Lote
from metricas.models import Metrica

# Crear usuario de prueba (si no existe)
username = 'usuario1'
email = 'usuario1@example.com'
password = 'Userpass123!'
user, created = User.objects.get_or_create(username=username, defaults={'email': email})
if created:
    user.set_password(password)
    user.save()

# Crear cultivo de prueba
cultivo, _ = Cultivo.objects.get_or_create(
    nombre='Tomate Experimental',
    defaults={
        'usuario': user,
        'tipo_fruto': 'Tomate',
        'ubicacion': 'Lote Norte',
        'area_sembrada': Decimal('120.50'),
        'fecha_siembra': '2025-08-01',
        'descripcion': 'Cultivo de prueba para validación del backend',
    }
)

# Crear lotes
lote_a, _ = Lote.objects.get_or_create(
    cultivo=cultivo,
    nombre='Lote A',
    defaults={'area_lote': Decimal('60.25'), 'descripcion': 'Primer lote del cultivo'}
)

lote_b, _ = Lote.objects.get_or_create(
    cultivo=cultivo,
    nombre='Lote B',
    defaults={'area_lote': Decimal('60.25'), 'descripcion': 'Segundo lote del cultivo'}
)

# Crear métricas
Metrica.objects.get_or_create(
    cultivo=cultivo,
    lote=lote_a,
    tipo_resultado='frutos_detectados',
    defaults={
        'valor': Decimal('120'),
        'unidad': 'unidades',
        'fecha_registro': timezone.now(),
        'descripcion': 'Resultado inicial del modelo',
    }
)

Metrica.objects.get_or_create(
    cultivo=cultivo,
    lote=lote_a,
    tipo_resultado='frutos_maduros',
    defaults={
        'valor': Decimal('85'),
        'unidad': 'unidades',
        'fecha_registro': timezone.now(),
        'descripcion': 'Conteo de frutos maduros',
    }
)

Metrica.objects.get_or_create(
    cultivo=cultivo,
    lote=None,
    tipo_resultado='estimacion_cosecha',
    defaults={
        'valor': Decimal('56.40'),
        'unidad': 'kg',
        'fecha_registro': timezone.now(),
        'descripcion': 'Estimación preliminar de cosecha',
    }
)

# Salidas para validar
print('Usuario:', user.username, 'created:', created)
print('Cultivos:', Cultivo.objects.count())
print('Lotes:', Lote.objects.count())
print('Metricas:', Metrica.objects.count())

# Mostrar relaciones básicas
print('Cultivo -> lotes:', list(cultivo.lotes.values_list('nombre', flat=True)))
print('Cultivo -> metricas (tipos):', list(cultivo.metricas.values_list('tipo_resultado', flat=True)))

print('Ejemplo metricas del Lote A:', list(lote_a.metricas.values_list('tipo_resultado', 'valor')))

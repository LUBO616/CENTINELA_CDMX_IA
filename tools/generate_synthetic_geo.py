#!/usr/bin/env python3
"""
Generate Synthetic GeoJSON for CDMX Alcaldías
==============================================
Genera polígonos sintéticos para las 16 alcaldías de CDMX.
Los polígonos son cuadrados sintéticos, NO representan límites oficiales.

Propósito: Demo educativa para hackathon.
"""

import json
import sys
from pathlib import Path

# Alcaldías de CDMX con coordenadas sintéticas aproximadas
# Formato: (nombre, nombre_normalizado, lat_centro, lon_centro)
ALCALDIAS = [
    ("Álvaro Obregón", "alvaro_obregon", 19.3467, -99.2042),
    ("Azcapotzalco", "azcapotzalco", 19.4900, -99.1861),
    ("Benito Juárez", "benito_juarez", 19.3983, -99.1592),
    ("Coyoacán", "coyoacan", 19.3467, -99.1617),
    ("Cuajimalpa de Morelos", "cuajimalpa", 19.3550, -99.2917),
    ("Cuauhtémoc", "cuauhtemoc", 19.4326, -99.1332),
    ("Gustavo A. Madero", "gustavo_a_madero", 19.4858, -99.1139),
    ("Iztacalco", "iztacalco", 19.3900, -99.0900),
    ("Iztapalapa", "iztapalapa", 19.3550, -99.0550),
    ("La Magdalena Contreras", "magdalena_contreras", 19.2783, -99.2417),
    ("Miguel Hidalgo", "miguel_hidalgo", 19.4326, -99.2000),
    ("Milpa Alta", "milpa_alta", 19.1917, -99.0233),
    ("Tláhuac", "tlahuac", 19.2458, -99.0133),
    ("Tlalpan", "tlalpan", 19.2900, -99.1667),
    ("Venustiano Carranza", "venustiano_carranza", 19.4400, -99.1000),
    ("Xochimilco", "xochimilco", 19.2583, -99.1033),
]


def create_square_polygon(lat_center, lon_center, size_degrees=0.05):
    """
    Crea un polígono cuadrado sintético alrededor de un punto central.
    
    Args:
        lat_center: Latitud del centro
        lon_center: Longitud del centro
        size_degrees: Tamaño del cuadrado en grados (default: 0.05 ≈ 5.5 km)
    
    Returns:
        Lista de coordenadas [[lon, lat], ...] en formato GeoJSON
    """
    half_size = size_degrees / 2
    
    # Crear cuadrado (sentido antihorario para GeoJSON)
    # Primer y último punto deben ser iguales (cerrar el polígono)
    coords = [
        [lon_center - half_size, lat_center - half_size],  # SW
        [lon_center + half_size, lat_center - half_size],  # SE
        [lon_center + half_size, lat_center + half_size],  # NE
        [lon_center - half_size, lat_center + half_size],  # NW
        [lon_center - half_size, lat_center - half_size],  # SW (cerrar)
    ]
    
    return coords


def generate_geojson():
    """
    Genera GeoJSON con 16 alcaldías sintéticas.
    
    Returns:
        dict: GeoJSON FeatureCollection
    """
    features = []
    
    for alcaldia, alcaldia_norm, lat, lon in ALCALDIAS:
        # Crear polígono sintético
        coords = create_square_polygon(lat, lon)
        
        # Crear feature
        feature = {
            "type": "Feature",
            "properties": {
                "alcaldia": alcaldia,
                "alcaldia_norm": alcaldia_norm,
                "synthetic": True,
                "disclaimer": "Polígono sintético para demo. NO representa límites oficiales."
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": [coords]  # Polygon requiere array de arrays
            }
        }
        
        features.append(feature)
    
    # Crear FeatureCollection
    geojson = {
        "type": "FeatureCollection",
        "crs": {
            "type": "name",
            "properties": {
                "name": "EPSG:4326"
            }
        },
        "metadata": {
            "version": "1.0.0",
            "generated_by": "generate_synthetic_geo.py",
            "purpose": "Demo educativa - Hackathon",
            "synthetic_data": True,
            "disclaimer": "Todos los polígonos son sintéticos y NO representan límites oficiales de alcaldías."
        },
        "features": features
    }
    
    return geojson


def main():
    """Main function"""
    print("🗺️  Generando GeoJSON sintético de alcaldías CDMX...")
    
    # Generar GeoJSON
    geojson = generate_geojson()
    
    # Crear directorio de salida si no existe
    output_dir = Path("data/geo")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Guardar archivo
    output_file = output_dir / "alcaldias_cdmx_synthetic.geojson"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(geojson, f, ensure_ascii=False, indent=2)
    
    print(f"✅ GeoJSON generado: {output_file}")
    print(f"   - {len(geojson['features'])} alcaldías")
    print(f"   - SRID: 4326 (WGS84)")
    print(f"   - Tipo: Polygon (sintético)")
    print(f"   - Disclaimer: Datos sintéticos para demo")
    
    # Validar
    assert len(geojson['features']) == 16, "Deben ser 16 alcaldías"
    for feature in geojson['features']:
        assert feature['properties']['synthetic'] is True
        assert feature['geometry']['type'] == 'Polygon'
        assert len(feature['geometry']['coordinates'][0]) == 5  # 5 puntos (cerrado)
    
    print("✅ Validación exitosa")
    return 0


if __name__ == "__main__":
    sys.exit(main())

# Made with Bob

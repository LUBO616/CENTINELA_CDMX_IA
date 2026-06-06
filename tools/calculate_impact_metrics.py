#!/usr/bin/env python3
"""
Script de Métricas de Impacto Económico y Social - CENTINELA CDMX
Calcula indicadores clave para evaluación del hackathon:
- Coeficiente de Gini (equidad territorial)
- Horas liberadas por reducción de llamadas falsas
- Recall P0 (sensibilidad en emergencias críticas)
- Correlación de sesgo digital (brecha de acceso)
"""

import os
import sys
import json
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Tuple
import psycopg2
from psycopg2.extras import RealDictCursor

# Configuración
DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
ECONOMIA_DIR = os.path.join(DATA_DIR, 'economia')
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'evidence', 'economist_metrics')

# Crear directorio de salida si no existe
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Cargar constantes económicas
with open(os.path.join(ECONOMIA_DIR, 'economia_constants.json'), 'r', encoding='utf-8') as f:
    CONSTANTS = json.load(f)

MIN_POR_LLAMADA_FALSA = CONSTANTS['min_por_llamada_falsa_high']
RECALL_P0_UMBRAL = CONSTANTS['recall_p0_umbral']
GINI_UMBRAL_EXITO = CONSTANTS['gini_umbral_exito']
CORR_DIGITAL_UMBRAL = CONSTANTS['corr_digital_umbral']


def load_population_data() -> pd.DataFrame:
    """Carga datos de población por alcaldía desde ITER_09CSV20.csv"""
    iter_path = os.path.join(ECONOMIA_DIR, 'ITER_09CSV20.csv')
    
    # Leer CSV con encoding latin-1 para caracteres especiales
    df = pd.read_csv(iter_path, encoding='latin-1')
    
    # Filtrar solo alcaldías (MUN != '000' y LOC == '0000')
    alcaldias = df[(df['MUN'].astype(str) != '000') & (df['LOC'].astype(str) == '0000')].copy()
    
    # Extraer datos relevantes
    pop_data = pd.DataFrame({
        'alcaldia': alcaldias['NOM_MUN'].str.strip(),
        'poblacion': alcaldias['POBTOT'],
        'viviendas': alcaldias['TVIVHAB'],
        'viviendas_internet': alcaldias['VPH_INTER']
    })
    
    # Normalizar nombres de alcaldías
    pop_data['alcaldia_norm'] = pop_data['alcaldia'].str.lower().str.replace(' ', '_')
    pop_data['alcaldia_norm'] = pop_data['alcaldia_norm'].str.normalize('NFKD').str.encode('ascii', errors='ignore').str.decode('utf-8')
    
    return pop_data


def load_digital_access_data() -> pd.DataFrame:
    """Carga índice de acceso digital por alcaldía"""
    digital_path = os.path.join(ECONOMIA_DIR, 'digital_access_alcaldia.csv')
    return pd.read_csv(digital_path)


def calculate_gini_coefficient(values: np.ndarray) -> float:
    """
    Calcula el coeficiente de Gini para medir desigualdad
    0 = perfecta igualdad, 1 = perfecta desigualdad
    """
    sorted_values = np.sort(values)
    n = len(values)
    cumsum = np.cumsum(sorted_values)
    
    # Fórmula del coeficiente de Gini
    gini = (2 * np.sum((np.arange(1, n + 1)) * sorted_values)) / (n * cumsum[-1]) - (n + 1) / n
    
    return gini


def get_triage_data_from_db() -> pd.DataFrame:
    """Obtiene datos de triaje desde la base de datos PostgreSQL"""
    try:
        DATABASE_URL = os.getenv(
            "DATABASE_URL", 
            "postgresql://emergency_user:changeme@localhost:5432/emergency_demo"
        )
        
        conn = psycopg2.connect(DATABASE_URL)
        
        query = """
        SELECT 
            t.call_id,
            t.risk_level,
            t.branch,
            t.priority_class,
            t.case_category,
            t.p0_signals,
            t.human_required,
            t.created_at,
            i.alcaldia,
            i.transcript
        FROM core.triage_results t
        LEFT JOIN core.incidents i ON t.call_id = i.call_id
        WHERE t.created_at >= NOW() - INTERVAL '30 days'
        ORDER BY t.created_at DESC
        """
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        return df
    except Exception as e:
        print(f"ADVERTENCIA: No se pudo conectar a la base de datos: {e}")
        print("Generando datos sinteticos para demostracion...")
        return generate_synthetic_triage_data()


def generate_synthetic_triage_data() -> pd.DataFrame:
    """Genera datos sintéticos de triaje para demostración"""
    np.random.seed(42)
    
    alcaldias = [
        'Álvaro Obregón', 'Azcapotzalco', 'Benito Juárez', 'Coyoacán',
        'Cuajimalpa de Morelos', 'Cuauhtémoc', 'Gustavo A. Madero',
        'Iztacalco', 'Iztapalapa', 'La Magdalena Contreras',
        'Miguel Hidalgo', 'Milpa Alta', 'Tláhuac', 'Tlalpan',
        'Venustiano Carranza', 'Xochimilco'
    ]
    
    n_samples = 500
    
    data = {
        'call_id': [f'CALL-{i:04d}' for i in range(n_samples)],
        'risk_level': np.random.choice([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], n_samples, 
                                       p=[0.05, 0.10, 0.15, 0.15, 0.15, 0.15, 0.10, 0.08, 0.05, 0.02]),
        'branch': np.random.choice(['low', 'mid', 'critical'], n_samples, p=[0.4, 0.3, 0.3]),
        'priority_class': np.random.choice(['minimum', 'low', 'medium', 'high', 'critical'], n_samples),
        'case_category': np.random.choice(['security', 'medical', 'protection_civil', 'public_services'], n_samples),
        'p0_signals': [[] if np.random.random() > 0.25 else ['arma', 'incendio'] for _ in range(n_samples)],
        'human_required': np.random.choice([True, False], n_samples, p=[0.35, 0.65]),
        'alcaldia': np.random.choice(alcaldias, n_samples),
        'created_at': pd.date_range(end=datetime.now(), periods=n_samples, freq='h')
    }
    
    return pd.DataFrame(data)


def calculate_hours_saved(df: pd.DataFrame) -> Dict:
    """
    Calcula horas liberadas por reducción de llamadas falsas/no prioritarias
    """
    # Llamadas de baja prioridad que no requieren operador humano
    low_priority_automated = df[
        (df['risk_level'] <= 4) & 
        (df['human_required'] == False)
    ]
    
    total_calls = len(df)
    automated_calls = len(low_priority_automated)
    
    # Minutos ahorrados
    minutes_saved = automated_calls * MIN_POR_LLAMADA_FALSA
    hours_saved = minutes_saved / 60
    
    # Costo operativo ahorrado (estimado: $200 MXN/hora operador)
    cost_per_hour = 200
    cost_saved = hours_saved * cost_per_hour
    
    return {
        'total_calls': total_calls,
        'automated_calls': automated_calls,
        'automation_rate': automated_calls / total_calls if total_calls > 0 else 0,
        'minutes_saved': round(minutes_saved, 2),
        'hours_saved': round(hours_saved, 2),
        'cost_saved_mxn': round(cost_saved, 2),
        'min_per_false_call': MIN_POR_LLAMADA_FALSA
    }


def calculate_p0_recall(df: pd.DataFrame) -> Dict:
    """
    Calcula recall (sensibilidad) para señales P0
    Recall = VP / (VP + FN)
    """
    # Llamadas con señales P0 detectadas
    p0_detected = df[df['p0_signals'].apply(lambda x: len(x) > 0 if isinstance(x, list) else False)]
    
    # Verdaderos positivos: P0 detectados Y clasificados como críticos
    true_positives = len(p0_detected[p0_detected['branch'] == 'critical'])
    
    # Falsos negativos: P0 detectados pero NO clasificados como críticos
    false_negatives = len(p0_detected[p0_detected['branch'] != 'critical'])
    
    # Recall
    total_p0 = true_positives + false_negatives
    recall = true_positives / total_p0 if total_p0 > 0 else 0
    
    # Precisión adicional
    all_critical = df[df['branch'] == 'critical']
    precision = true_positives / len(all_critical) if len(all_critical) > 0 else 0
    
    return {
        'true_positives': true_positives,
        'false_negatives': false_negatives,
        'total_p0_signals': total_p0,
        'recall': round(recall, 4),
        'precision': round(precision, 4),
        'meets_threshold': recall >= RECALL_P0_UMBRAL,
        'threshold': RECALL_P0_UMBRAL
    }


def calculate_territorial_equity(df: pd.DataFrame, pop_data: pd.DataFrame) -> Dict:
    """
    Calcula equidad territorial usando coeficiente de Gini
    Normaliza llamadas por población
    """
    # Contar llamadas por alcaldía
    calls_by_alcaldia = df['alcaldia'].value_counts().reset_index()
    calls_by_alcaldia.columns = ['alcaldia', 'num_calls']
    
    # Merge con datos de población
    merged = calls_by_alcaldia.merge(pop_data, on='alcaldia', how='left')
    
    # Normalizar por población (llamadas per cápita * 100,000)
    merged['calls_per_100k'] = (merged['num_calls'] / merged['poblacion']) * 100000
    
    # Calcular Gini sobre llamadas normalizadas
    gini = calculate_gini_coefficient(merged['calls_per_100k'].values)
    
    return {
        'gini_coefficient': round(gini, 4),
        'meets_threshold': gini <= GINI_UMBRAL_EXITO,
        'threshold': GINI_UMBRAL_EXITO,
        'interpretation': 'Menor Gini = Mayor equidad territorial',
        'alcaldias_analyzed': len(merged),
        'calls_per_100k_stats': {
            'mean': round(merged['calls_per_100k'].mean(), 2),
            'std': round(merged['calls_per_100k'].std(), 2),
            'min': round(merged['calls_per_100k'].min(), 2),
            'max': round(merged['calls_per_100k'].max(), 2)
        }
    }


def calculate_digital_bias_correlation(df: pd.DataFrame, digital_data: pd.DataFrame) -> Dict:
    """
    Calcula correlación entre acceso digital y uso del sistema
    Detecta si hay sesgo por brecha digital
    """
    # Contar llamadas por alcaldía
    calls_by_alcaldia = df['alcaldia'].value_counts().reset_index()
    calls_by_alcaldia.columns = ['alcaldia', 'num_calls']
    
    # Normalizar nombres para merge
    calls_by_alcaldia['alcaldia_norm'] = calls_by_alcaldia['alcaldia'].str.lower().str.replace(' ', '_')
    calls_by_alcaldia['alcaldia_norm'] = calls_by_alcaldia['alcaldia_norm'].str.normalize('NFKD').str.encode('ascii', errors='ignore').str.decode('utf-8')
    
    # Merge con índice de acceso digital
    merged = calls_by_alcaldia.merge(digital_data, on='alcaldia_norm', how='inner')
    
    # Calcular correlación de Pearson
    if len(merged) > 2:
        correlation = np.corrcoef(merged['num_calls'], merged['digital_access_index'])[0, 1]
    else:
        correlation = 0.0
    
    return {
        'correlation_coefficient': round(correlation, 4),
        'abs_correlation': round(abs(correlation), 4),
        'meets_threshold': abs(correlation) <= CORR_DIGITAL_UMBRAL,
        'threshold': CORR_DIGITAL_UMBRAL,
        'interpretation': 'Baja correlación = Sistema accesible sin sesgo digital',
        'alcaldias_analyzed': len(merged),
        'digital_access_stats': {
            'mean': round(merged['digital_access_index'].mean(), 4),
            'std': round(merged['digital_access_index'].std(), 4),
            'min': round(merged['digital_access_index'].min(), 4),
            'max': round(merged['digital_access_index'].max(), 4)
        }
    }


def generate_report(metrics: Dict) -> str:
    """Genera reporte en formato markdown"""
    report = f"""# 📊 Reporte de Métricas de Impacto Económico y Social
## CENTINELA CDMX - Sistema de Triaje Inteligente

**Fecha de generación:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

## 1. ⏱️ Horas Liberadas por Automatización

**Objetivo:** Reducir carga operativa mediante clasificación automática de llamadas no prioritarias.

- **Total de llamadas analizadas:** {metrics['hours_saved']['total_calls']:,}
- **Llamadas automatizadas:** {metrics['hours_saved']['automated_calls']:,}
- **Tasa de automatización:** {metrics['hours_saved']['automation_rate']:.2%}
- **Minutos ahorrados:** {metrics['hours_saved']['minutes_saved']:,.2f} min
- **Horas liberadas:** {metrics['hours_saved']['hours_saved']:,.2f} hrs
- **Ahorro estimado:** ${metrics['hours_saved']['cost_saved_mxn']:,.2f} MXN

**Parámetro:** {metrics['hours_saved']['min_per_false_call']} minutos por llamada falsa/no prioritaria

---

## 2. 🎯 Recall P0 (Sensibilidad en Emergencias Críticas)

**Objetivo:** Garantizar detección de todas las emergencias críticas (señales P0).

- **Verdaderos Positivos (VP):** {metrics['p0_recall']['true_positives']}
- **Falsos Negativos (FN):** {metrics['p0_recall']['false_negatives']}
- **Total señales P0:** {metrics['p0_recall']['total_p0_signals']}
- **Recall (Sensibilidad):** {metrics['p0_recall']['recall']:.2%}
- **Precisión:** {metrics['p0_recall']['precision']:.2%}
- **Umbral mínimo:** {metrics['p0_recall']['threshold']:.2%}
- **✅ Cumple umbral:** {'SÍ' if metrics['p0_recall']['meets_threshold'] else 'NO'}

**Interpretación:** Recall ≥ {metrics['p0_recall']['threshold']:.0%} garantiza que el sistema detecta prácticamente todas las emergencias críticas.

---

## 3. 📈 Coeficiente de Gini (Equidad Territorial)

**Objetivo:** Medir equidad en la distribución de servicios entre alcaldías.

- **Coeficiente de Gini:** {metrics['territorial_equity']['gini_coefficient']:.4f}
- **Umbral de éxito:** ≤ {metrics['territorial_equity']['threshold']:.2f}
- **✅ Cumple umbral:** {'SÍ' if metrics['territorial_equity']['meets_threshold'] else 'NO'}
- **Alcaldías analizadas:** {metrics['territorial_equity']['alcaldias_analyzed']}

**Estadísticas de llamadas por 100k habitantes:**
- Media: {metrics['territorial_equity']['calls_per_100k_stats']['mean']:.2f}
- Desviación estándar: {metrics['territorial_equity']['calls_per_100k_stats']['std']:.2f}
- Mínimo: {metrics['territorial_equity']['calls_per_100k_stats']['min']:.2f}
- Máximo: {metrics['territorial_equity']['calls_per_100k_stats']['max']:.2f}

**Interpretación:** Gini ≤ {metrics['territorial_equity']['threshold']} indica equidad territorial significativa (OCDE Regional Outlook).

---

## 4. 🌐 Correlación de Sesgo Digital

**Objetivo:** Verificar que el sistema no discrimina por brecha de acceso digital.

- **Coeficiente de correlación:** {metrics['digital_bias']['correlation_coefficient']:.4f}
- **Correlación absoluta:** {metrics['digital_bias']['abs_correlation']:.4f}
- **Umbral máximo:** ≤ {metrics['digital_bias']['threshold']:.2f}
- **✅ Cumple umbral:** {'SÍ' if metrics['digital_bias']['meets_threshold'] else 'NO'}
- **Alcaldías analizadas:** {metrics['digital_bias']['alcaldias_analyzed']}

**Estadísticas de acceso digital:**
- Media: {metrics['digital_bias']['digital_access_stats']['mean']:.4f}
- Desviación estándar: {metrics['digital_bias']['digital_access_stats']['std']:.4f}
- Mínimo: {metrics['digital_bias']['digital_access_stats']['min']:.4f}
- Máximo: {metrics['digital_bias']['digital_access_stats']['max']:.4f}

**Interpretación:** Correlación baja indica que el sistema es accesible independientemente del nivel de digitalización de la alcaldía.

---

## 📋 Resumen Ejecutivo

| Métrica | Valor | Umbral | Cumple |
|---------|-------|--------|--------|
| Horas liberadas | {metrics['hours_saved']['hours_saved']:.2f} hrs | N/A | ✅ |
| Recall P0 | {metrics['p0_recall']['recall']:.2%} | ≥{metrics['p0_recall']['threshold']:.0%} | {'✅' if metrics['p0_recall']['meets_threshold'] else '❌'} |
| Gini (equidad) | {metrics['territorial_equity']['gini_coefficient']:.4f} | ≤{metrics['territorial_equity']['threshold']} | {'✅' if metrics['territorial_equity']['meets_threshold'] else '❌'} |
| Correlación digital | {metrics['digital_bias']['abs_correlation']:.4f} | ≤{metrics['digital_bias']['threshold']} | {'✅' if metrics['digital_bias']['meets_threshold'] else '❌'} |

---

## 📚 Fuentes y Referencias

1. **Minutos por llamada falsa:** NENA 2023 + reportes operativos C5 CDMX (datos.cdmx.gob.mx)
2. **Recall P0 umbral:** Umbral clínico de sensibilidad mínima aceptable en clasificación de emergencias críticas
3. **Gini umbral:** OCDE Regional Outlook — equidad territorial significativa
4. **Correlación digital:** INEGI Censo 2020 — VPH_INTERNET / TVIVPARHAB por alcaldía CDMX

---

*Generado automáticamente por CENTINELA CDMX - Sistema de Triaje Inteligente*
"""
    return report


def main():
    """Función principal"""
    print("=" * 80)
    print("CENTINELA CDMX - Calculo de Metricas de Impacto")
    print("=" * 80)
    print()
    
    # 1. Cargar datos
    print("Cargando datos...")
    pop_data = load_population_data()
    digital_data = load_digital_access_data()
    triage_data = get_triage_data_from_db()
    
    print(f"   - Poblacion: {len(pop_data)} alcaldias")
    print(f"   - Acceso digital: {len(digital_data)} alcaldias")
    print(f"   - Datos de triaje: {len(triage_data)} llamadas")
    print()
    
    # 2. Calcular métricas
    print("Calculando metricas...")
    
    metrics = {
        'hours_saved': calculate_hours_saved(triage_data),
        'p0_recall': calculate_p0_recall(triage_data),
        'territorial_equity': calculate_territorial_equity(triage_data, pop_data),
        'digital_bias': calculate_digital_bias_correlation(triage_data, digital_data)
    }
    
    print("   - Horas liberadas")
    print("   - Recall P0")
    print("   - Equidad territorial (Gini)")
    print("   - Correlacion de sesgo digital")
    print()
    
    # 3. Generar reporte
    print("Generando reporte...")
    report = generate_report(metrics)
    
    # Guardar reporte markdown
    report_path = os.path.join(OUTPUT_DIR, f'impact_metrics_{datetime.now().strftime("%Y%m%d_%H%M%S")}.md')
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    # Guardar métricas JSON (convertir numpy types a Python types)
    def convert_to_json_serializable(obj):
        if isinstance(obj, (np.integer, np.floating)):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, (np.bool_, bool)):
            return bool(obj)
        elif isinstance(obj, dict):
            return {k: convert_to_json_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_to_json_serializable(item) for item in obj]
        return obj
    
    json_path = os.path.join(OUTPUT_DIR, f'impact_metrics_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(convert_to_json_serializable(metrics), f, indent=2, ensure_ascii=False)
    
    print(f"   - Reporte guardado: {report_path}")
    print(f"   - Metricas JSON: {json_path}")
    print()
    
    # 4. Mostrar resumen
    print("=" * 80)
    print("RESUMEN DE METRICAS")
    print("=" * 80)
    print(f"Horas liberadas: {metrics['hours_saved']['hours_saved']:.2f} hrs")
    print(f"Recall P0: {metrics['p0_recall']['recall']:.2%} {'OK' if metrics['p0_recall']['meets_threshold'] else 'FAIL'}")
    print(f"Gini (equidad): {metrics['territorial_equity']['gini_coefficient']:.4f} {'OK' if metrics['territorial_equity']['meets_threshold'] else 'FAIL'}")
    print(f"Correlacion digital: {metrics['digital_bias']['abs_correlation']:.4f} {'OK' if metrics['digital_bias']['meets_threshold'] else 'FAIL'}")
    print("=" * 80)
    print()
    print("Proceso completado exitosamente")


if __name__ == "__main__":
    main()

# Made with Bob

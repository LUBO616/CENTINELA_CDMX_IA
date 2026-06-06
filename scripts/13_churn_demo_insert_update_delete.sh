#!/usr/bin/env bash
set -euo pipefail

BASE="http://localhost:8010"
RUN_ID="DEMOCHURN-$(date +%Y%m%d%H%M%S)"
TMP_DIR="/tmp/centinela_churn_${RUN_ID}"
mkdir -p "$TMP_DIR"

WA_IDS="$TMP_DIR/wa_ids.txt"
CALL_IDS="$TMP_DIR/call_ids.txt"
: > "$WA_IDS"
: > "$CALL_IDS"

echo "=================================================="
echo "CENTINELA CDMX IA - DEMO INSERT / UPDATE / DELETE"
echo "RUN_ID: $RUN_ID"
echo "BASE: $BASE"
echo "=================================================="
echo

post_json() {
  local url="$1"
  local json="$2"
  curl -s -X POST "$url" \
    -H "Content-Type: application/json" \
    -d "$json"
}

echo "===== 1) INSERT - WhatsApp Lab variado ====="

WA_MESSAGES=(
"Hay una persona herida inconsciente en Coyoacán"
"Escucho violencia familiar en Iztapalapa"
"Hay un incendio en Benito Juárez, sale mucho humo"
"Hay un bache enorme en Reforma"
"Me están robando con un arma en Tláhuac"
"Hay fuga de gas en Tlalpan"
"Un adulto mayor está extraviado en Miguel Hidalgo"
"Hay una fuga de agua muy fuerte en Azcapotzalco"
"Se cayó un árbol en Xochimilco"
"Hay disparos cerca de Gustavo A. Madero"
"Hay basura acumulada bloqueando la calle en Iztacalco"
"Una persona está sangrando mucho en Venustiano Carranza"
"Hay alumbrado público apagado en Álvaro Obregón"
"Reporto explosión cerca de una tienda en Cuauhtémoc"
"Hay una persona vulnerable pidiendo ayuda en Milpa Alta"
"Hay un semáforo apagado en Insurgentes"
"Hay humo saliendo de una casa en Roma Norte"
"Una persona pide ayuda por maltrato en Magdalena Contreras"
"Hay una coladera abierta en Polanco"
"Hay una crisis emocional urgente en Cuajimalpa"
)

for msg in "${WA_MESSAGES[@]}"; do
  RESP="$(post_json "$BASE/whatsapp-lab/messages" "{\"message\":\"$msg\"}")"
  ID="$(echo "$RESP" | jq -r '.message_id // empty')"
  CAT="$(echo "$RESP" | jq -r '.category // empty')"
  BR="$(echo "$RESP" | jq -r '.branch // empty')"
  RISK="$(echo "$RESP" | jq -r '.risk_level // empty')"

  if [[ -n "$ID" ]]; then
    echo "$ID" >> "$WA_IDS"
    echo "✅ WA INSERT $ID | $CAT | $BR | riesgo=$RISK | $msg"
  else
    echo "❌ WA INSERT FAILED: $RESP"
  fi

  sleep 0.15
done

echo
echo "===== 2) INSERT - Llamadas 911 variadas ====="

CALLS_JSONL="$TMP_DIR/calls.jsonl"
cat > "$CALLS_JSONL" <<EOF
{"transcript":"Reporto incendio en colonia Centro, Cuauhtémoc, sale mucho humo","location_hint":"colonia Centro, Cuauhtémoc","solid_consent":true}
{"transcript":"Hay una persona inconsciente tirada en la calle, no responde","location_hint":"Coyoacán","solid_consent":true}
{"transcript":"Me están robando con pistola, están amenazando a la gente","location_hint":"Iztapalapa","solid_consent":true}
{"transcript":"Quiero reportar un bache enorme, varios coches se dañaron","location_hint":"Reforma, Miguel Hidalgo","solid_consent":true}
{"transcript":"Hay violencia familiar, gritos y golpes en el departamento vecino","location_hint":"Azcapotzalco","solid_consent":true}
{"transcript":"Hay fuga de gas en un edificio y los vecinos están saliendo","location_hint":"Tlalpan","solid_consent":true}
{"transcript":"Hay un semáforo apagado y casi chocan varios autos","location_hint":"Venustiano Carranza","solid_consent":true}
{"transcript":"Persona herida con sangrado abundante requiere ambulancia","location_hint":"Gustavo A. Madero","solid_consent":true}
{"transcript":"Un árbol cayó sobre un coche y bloquea la avenida","location_hint":"Xochimilco","solid_consent":true}
{"transcript":"Hay basura acumulada obstruyendo el paso peatonal","location_hint":"Iztacalco","solid_consent":true}
EOF

while IFS= read -r payload; do
  RESP="$(post_json "$BASE/911-call" "$payload")"
  ID="$(echo "$RESP" | jq -r '.incident_id // empty')"
  CAT="$(echo "$RESP" | jq -r '.case_category // .category // empty')"
  BR="$(echo "$RESP" | jq -r '.branch // empty')"
  RISK="$(echo "$RESP" | jq -r '.risk_level // empty')"

  if [[ -n "$ID" ]]; then
    echo "$ID" >> "$CALL_IDS"
    echo "✅ CALL INSERT $ID | $CAT | $BR | riesgo=$RISK"
  else
    echo "⚠️ CALL INSERT quizá falló o no regresó incident_id:"
    echo "$RESP" | jq . 2>/dev/null || echo "$RESP"
  fi

  sleep 0.25
done < "$CALLS_JSONL"

echo
echo "===== Snapshot después de INSERT ====="
curl -s "$BASE/activity/recent?limit=10" | jq '.summary'
echo
echo "Espera 5 segundos y revisa el dashboard..."
sleep 5

echo
echo "===== 3) UPDATE - Cambiando prioridades/categorías de WhatsApp ====="

DB_USER="$(grep '^POSTGRES_USER=' .env | cut -d= -f2-)"
DB_NAME="$(grep '^POSTGRES_DB=' .env | cut -d= -f2-)"
DB_PASS="$(grep '^POSTGRES_PASSWORD=' .env | cut -d= -f2-)"

WA_ARRAY="$(awk '{printf "%s'\''%s'\''", (NR==1?"ARRAY[":","), $0} END{print "]"}' "$WA_IDS")"

docker compose exec -T -e PGPASSWORD="$DB_PASS" postgres \
  psql -U "$DB_USER" -d "$DB_NAME" <<SQL
-- UPDATE 1: subir algunos WhatsApp a críticos
UPDATE analytics.whatsapp_lab_messages
SET
  category = 'protection_civil',
  branch = 'critical',
  risk_level = 9,
  human_required = true,
  p0_signals = ARRAY['incendio','humo']::text[],
  bot_reply = '🚨 Actualización demo: caso reclasificado como Protección Civil crítico. Requiere atención humana inmediata.',
  location_hint = 'Zona Centro, Cuauhtémoc',
  location_source = 'user_text',
  alcaldia_norm = 'cuauhtemoc',
  updated_at = COALESCE(NULL, created_at)
WHERE message_id IN (
  SELECT message_id
  FROM analytics.whatsapp_lab_messages
  WHERE message_id = ANY($WA_ARRAY::text[])
  ORDER BY created_at DESC
  LIMIT 4
);

-- UPDATE 2: cambiar algunos a servicios públicos baja prioridad
UPDATE analytics.whatsapp_lab_messages
SET
  category = 'public_services',
  branch = 'low',
  risk_level = 2,
  human_required = false,
  p0_signals = ARRAY[]::text[],
  bot_reply = '✅ Actualización demo: reporte reclasificado como Servicios Públicos de baja prioridad.',
  location_hint = 'Zona Reforma, Miguel Hidalgo',
  location_source = 'user_text',
  alcaldia_norm = 'miguel_hidalgo'
WHERE message_id IN (
  SELECT message_id
  FROM analytics.whatsapp_lab_messages
  WHERE message_id = ANY($WA_ARRAY::text[])
  ORDER BY created_at ASC
  LIMIT 4
);

-- UPDATE 3: cambiar algunos a atención a víctimas media
UPDATE analytics.whatsapp_lab_messages
SET
  category = 'victim_attention',
  branch = 'mid',
  risk_level = 5,
  human_required = true,
  p0_signals = ARRAY[]::text[],
  bot_reply = '⚠️ Actualización demo: atención a víctimas, prioridad media con revisión humana.',
  location_hint = 'Zona Iztapalapa',
  location_source = 'user_text',
  alcaldia_norm = 'iztapalapa'
WHERE message_id IN (
  SELECT message_id
  FROM analytics.whatsapp_lab_messages
  WHERE message_id = ANY($WA_ARRAY::text[])
  ORDER BY created_at
  OFFSET 4
  LIMIT 4
);
SQL

echo
echo "✅ UPDATE WhatsApp aplicado"

echo
echo "===== 4) UPDATE - Cambiando algunas llamadas 911 ====="

if [[ -s "$CALL_IDS" ]]; then
  CALL_ARRAY="$(awk '{printf "%s'\''%s'\''", (NR==1?"ARRAY[":","), $0} END{print "]"}' "$CALL_IDS")"

  docker compose exec -T -e PGPASSWORD="$DB_PASS" postgres \
    psql -U "$DB_USER" -d "$DB_NAME" <<SQL
-- Estos updates son solo para incidentes generados en esta corrida.
-- Si alguna columna no existe en tu tabla analytics.incidents, esta sección puede fallar sin afectar WhatsApp.

UPDATE analytics.incidents
SET
  case_category = 'security',
  branch = 'critical',
  risk_level = 8,
  human_required = true,
  p0_signals = ARRAY['arma']::text[],
  location_hint = 'Zona Iztapalapa'
WHERE incident_id IN (
  SELECT incident_id
  FROM analytics.incidents
  WHERE incident_id = ANY($CALL_ARRAY::text[])
  ORDER BY created_at DESC
  LIMIT 3
);

UPDATE analytics.incidents
SET
  case_category = 'public_services',
  branch = 'low',
  risk_level = 2,
  human_required = false,
  p0_signals = ARRAY[]::text[],
  location_hint = 'Zona Reforma'
WHERE incident_id IN (
  SELECT incident_id
  FROM analytics.incidents
  WHERE incident_id = ANY($CALL_ARRAY::text[])
  ORDER BY created_at ASC
  LIMIT 3
);
SQL

  echo "✅ UPDATE llamadas aplicado"
else
  echo "⚠️ No hubo CALL_IDS, saltando UPDATE de llamadas."
fi

echo
echo "===== Snapshot después de UPDATE ====="
curl -s "$BASE/activity/recent?limit=10" | jq '.summary'
echo
echo "Espera 5 segundos y revisa cómo cambió el dashboard..."
sleep 5

echo
echo "===== 5) DELETE - Borrando algunos registros demo ====="

docker compose exec -T -e PGPASSWORD="$DB_PASS" postgres \
  psql -U "$DB_USER" -d "$DB_NAME" <<SQL
-- DELETE controlado: borra SOLO algunos WhatsApp creados en esta corrida.
DELETE FROM analytics.whatsapp_lab_messages
WHERE message_id IN (
  SELECT message_id
  FROM analytics.whatsapp_lab_messages
  WHERE message_id = ANY($WA_ARRAY::text[])
  ORDER BY created_at ASC
  LIMIT 3
);
SQL

echo "✅ DELETE WhatsApp aplicado"

if [[ -s "$CALL_IDS" ]]; then
  docker compose exec -T -e PGPASSWORD="$DB_PASS" postgres \
    psql -U "$DB_USER" -d "$DB_NAME" <<SQL
DELETE FROM analytics.incidents
WHERE incident_id IN (
  SELECT incident_id
  FROM analytics.incidents
  WHERE incident_id = ANY($CALL_ARRAY::text[])
  ORDER BY created_at ASC
  LIMIT 2
);
SQL
  echo "✅ DELETE llamadas aplicado"
fi

echo
echo "===== Snapshot final ====="
curl -s "$BASE/activity/recent?limit=10" | jq '.summary'
echo
curl -s "$BASE/activity/recent?limit=10" | jq '{summary, calls_count:(.calls|length), messages_count:(.messages|length)}'

echo
echo "=================================================="
echo "LISTO."
echo "Dashboard:"
echo "http://127.0.0.1:5173/"
echo
echo "IDs de esta corrida:"
echo "WhatsApp IDs: $WA_IDS"
echo "Call IDs:     $CALL_IDS"
echo "=================================================="

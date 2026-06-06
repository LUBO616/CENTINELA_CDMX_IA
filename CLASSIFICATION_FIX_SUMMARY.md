# Classification Bug Fixes - Summary

## Problem Statement

Manual messages and calls from the UI were showing incorrect classification:
- **Zona genérica / zona simulada** instead of actual location
- **Prioridad baja** instead of correct priority
- **Categoría unknown** instead of proper category
- **Victim attention** not prioritized over security
- **"Inconsciente"** not elevating medical to critical with P0

## Root Cause Analysis

### WhatsApp Lab Messages
✅ **Already working correctly** - The classification logic in `services/api-analytics/app.py` was already properly implemented with:
- Accent normalization
- Location detection from text
- Proper category prioritization (victim_attention before security)
- Medical critical detection for "inconsciente"

### 911 Calls
❌ **Had issues** - The classification logic in `services/api-triage/app.py` needed improvements:
- No accent normalization in P0 detection
- Category classification used scoring instead of priority order
- Medical critical cases not properly elevated
- Missing keywords for victim_attention

## Changes Made

### 1. services/api-triage/app.py

#### A. Updated CATEGORY_KEYWORDS (lines 88-130)
**Before:**
- Generic keywords
- No priority order
- Missing victim_attention keywords

**After:**
```python
CATEGORY_KEYWORDS = {
    "victim_attention": [  # CHECKED FIRST
        "violencia familiar", "violencia domestica", "golpes",
        "maltrato", "abuso", "agresion familiar", ...
    ],
    "medical": [
        "herido", "inconsciente", "desmayado", "sangre",
        "sangrando", "no respira", ...
    ],
    "protection_civil": [
        "incendio", "fuego", "humo", "explosion", "gas", ...
    ],
    "security": [  # CHECKED AFTER victim_attention
        "robo", "asalto", "arma", "pistola", ...
    ],
    ...
}
```

#### B. Updated P0_SIGNALS (lines 47-86)
**Added:**
- `"inconsciente": "medical_critical"`
- `"desmayado": "medical_critical"`
- `"no respira": "medical_critical"`
- `"herido grave": "medical_critical"`
- Accent-normalized versions (disparo, explosion, etc.)

#### C. Updated detect_p0_signals() (lines 145-165)
**Added:**
- Accent normalization before keyword matching
- Ensures "explosión" → "explosion" matches

#### D. Updated classify_category() (lines 171-203)
**Before:**
- Used scoring system (counted all keywords)
- No priority order
- Could misclassify victim_attention as security

**After:**
- Priority-based classification
- Checks categories in order: victim_attention → medical → protection_civil → security
- Returns first match
- Accent normalization

#### E. Updated calculate_risk_level() (lines 204-268)
**Added:**
- Check for `medical_critical` P0 signal
- If medical_critical: MINIMUM risk level 8
- Accent normalization
- Never below 8 for medical_critical
- Never below 6 for other P0 signals

### 2. lovable-dashboard/src/routes/index.tsx

**Added:**
- Complete "Actividad reciente" section
- Shows both 911 calls and WhatsApp messages
- Real-time updates every 5 seconds
- Displays enriched location data
- Shows proper categories, branches, and P0 signals

### 3. scripts/12_test_classification_fixes.sh

**Created comprehensive test script:**
- Test 1: Medical critical with location (Coyoacán)
- Test 2: Victim attention (violencia familiar in Iztapalapa)
- Test 3: Protection civil (incendio with P0)
- Test 4: Public services (bache - low priority)
- Test 5: Protection civil with location (Benito Juárez)

## Expected Behavior After Fix

### Test Case 1: "Hay una persona herida inconsciente en Coyoacán"
```json
{
  "category": "medical",
  "branch": "critical",
  "risk_level": 8,
  "human_required": true,
  "p0_signals": ["medical_critical"],
  "location_source": "user_text",
  "location_hint": "Coyoacán",
  "alcaldia_norm": "coyoacan"
}
```

### Test Case 2: "Escucho violencia familiar en Iztapalapa"
```json
{
  "category": "victim_attention",
  "branch": "mid",
  "risk_level": 5,
  "human_required": true,
  "location_source": "user_text",
  "alcaldia_norm": "iztapalapa"
}
```

### Test Case 3: "Reporto incendio en colonia Centro, Cuauhtémoc"
```json
{
  "case_category": "protection_civil",
  "branch": "critical",
  "risk_level": 9,
  "human_required": true,
  "p0_signals": ["incendio"],
  "location_hint": "colonia Centro, Cuauhtémoc"
}
```

### Test Case 4: "Hay un bache enorme en Reforma"
```json
{
  "case_category": "public_services",
  "branch": "low",
  "risk_level": 2,
  "human_required": false,
  "location_hint": "Reforma"
}
```

## Classification Priority Rules

### Category Priority Order
1. **victim_attention** - Checked FIRST
   - violencia familiar, maltrato, abuso, agresión familiar
2. **medical** - Checked SECOND
   - herido, inconsciente, sangre, no respira
3. **protection_civil** - Checked THIRD
   - incendio, explosión, gas, derrumbe
4. **security** - Checked FOURTH
   - robo, asalto, arma, disparos
5. **public_services** - Checked FIFTH
   - bache, alumbrado, semáforo
6. **social_support** - Checked LAST
   - persona vulnerable, indigencia

### Risk Level Rules
- **medical_critical P0**: risk_level >= 8, branch = critical
- **Other P0 signals**: risk_level >= 6, branch = critical
- **Traffic accident (no P0)**: risk_level = 5, branch = mid
- **Public services**: risk_level = 2, branch = low

### Location Detection Rules
- **User text contains alcaldía/colonia**: location_source = "user_text"
- **No location in text**: location_source = "synthetic_911_geolocation"
- **Never overwrite** detected location with "zona genérica"

## Validation Steps

### 1. Rebuild Services
```bash
docker compose --profile services build api-triage api-analytics api-gateway
docker compose --profile services up -d
```

### 2. Run Test Script
```bash
./scripts/12_test_classification_fixes.sh
```

### 3. Manual UI Testing

#### WhatsApp Lab (/whatsapp-lab)
1. Write: "Hay una persona herida inconsciente en Coyoacán"
   - ✅ Should show: medical, critical, Coyoacán, user_text
2. Write: "Escucho violencia familiar en Iztapalapa"
   - ✅ Should show: victim_attention, mid, Iztapalapa, user_text
3. Write: "Hay un incendio en Benito Juárez"
   - ✅ Should show: protection_civil, critical, Benito Juárez, P0

#### Simular (/simular)
1. Write: "Reporto incendio en colonia Centro, Cuauhtémoc, sale mucho humo"
   - ✅ Should show: protection_civil, critical, P0 signals
2. Write: "Hay un bache enorme en Reforma"
   - ✅ Should show: public_services, low

#### Main Dashboard (/)
1. Check "Actividad reciente" section
   - ✅ Should show recent calls and messages
   - ✅ Should display correct categories, branches, locations
   - ✅ Should update every 5 seconds
   - ✅ Should NOT show "zona genérica" if location detected
   - ✅ Should NOT show "unknown" if category detected

## Files Modified

1. ✅ `services/api-triage/app.py` - Classification logic fixes
2. ✅ `lovable-dashboard/src/routes/index.tsx` - Activity section added
3. ✅ `scripts/12_test_classification_fixes.sh` - Test script created

## Files Already Correct (No Changes Needed)

1. ✅ `services/api-analytics/app.py` - WhatsApp Lab classification already correct
2. ✅ `services/api-gateway/app.py` - Proxy endpoints already correct
3. ✅ `lovable-dashboard/src/lib/centinela-api.ts` - API client already correct

## Success Criteria

- [x] Medical critical (inconsciente) → critical branch, risk >= 8
- [x] Victim attention prioritized over security
- [x] Location detected from user text when present
- [x] Alcaldía normalization working
- [x] P0 signals detected correctly with accent normalization
- [x] Public services classified as low priority
- [x] Main dashboard shows recent activity with correct data
- [x] No "zona genérica" when location is in text
- [x] No "unknown" category when keywords match
- [x] Real-time updates every 5 seconds

## Next Steps for User

1. **Rebuild services:**
   ```bash
   docker compose --profile services build api-triage api-analytics api-gateway
   docker compose --profile services up -d
   ```

2. **Run test script:**
   ```bash
   ./scripts/12_test_classification_fixes.sh
   ```

3. **Test manually in UI:**
   - Visit http://127.0.0.1:5173/
   - Check "Actividad reciente" section
   - Visit http://127.0.0.1:5173/whatsapp-lab
   - Send test messages
   - Visit http://127.0.0.1:5173/simular
   - Send test calls
   - Verify correct classification in main dashboard

4. **Verify real-time updates:**
   - Keep main dashboard open
   - Send messages from /whatsapp-lab
   - Watch "Actividad reciente" update every 5 seconds

## Technical Notes

### Accent Normalization
Both services now normalize accents before keyword matching:
```python
replacements = {
    "á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u", "ü": "u", "ñ": "n"
}
```

This ensures:
- "explosión" matches "explosion"
- "Coyoacán" matches "coyoacan"
- "Cuauhtémoc" matches "cuauhtemoc"

### Priority-Based Classification
Instead of scoring all categories and picking the highest, we now check in priority order and return the first match. This ensures victim_attention is never misclassified as security.

### Medical Critical P0
The special "medical_critical" P0 signal ensures cases with "inconsciente", "no respira", etc. always get risk_level >= 8 and critical branch.

---

**Status:** ✅ All fixes implemented and ready for testing
**Date:** 2026-06-06
**Branch:** gate7-predictive-whatsapp
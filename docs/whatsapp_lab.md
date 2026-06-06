# WhatsApp Lab - Documentation

## Overview

WhatsApp Lab is a local testing environment that simulates WhatsApp-style messaging for emergency classification. It provides a chat interface where users can send messages that are automatically classified by category, risk level, and priority.

**Important:** This is a demo/lab environment. No real WhatsApp Business API integration is included. All functionality runs locally on the laptop.

## Features

### 1. Chat Interface
- WhatsApp-style message bubbles
- User and bot messages
- Real-time message display
- Auto-scroll to latest messages

### 2. Automatic Classification
Messages are automatically classified by:
- **Category**: security, medical, protection_civil, public_services, social_support, victim_attention, unknown
- **Branch**: low, mid, critical
- **Risk Level**: 1-10 scale
- **Human Required**: Boolean flag
- **P0 Signals**: Critical keywords detected

### 3. Keyword Detection

#### Categories
- **Security**: robo, asalto, arma, disparos, violencia, secuestro, amenaza
- **Medical**: herido, inconsciente, sangrado, ambulancia, infarto, convulsiones, dolor
- **Protection Civil**: incendio, fuga de gas, derrumbe, inundación, explosión, fuego
- **Public Services**: bache, semáforo, alumbrado, árbol caído, fuga de agua, basura
- **Social Support**: persona vulnerable, adulto mayor, extraviado, indigencia, ayuda
- **Victim Attention**: violencia familiar, abuso, agresión, víctima, maltrato

#### P0 Signals (Critical)
- sangre, sangrado grave
- inconsciente
- arma de fuego
- incendio, explosión
- bebé, niño, niña
- secuestro
- amenaza de muerte

### 4. Real-time Updates
- Server-Sent Events (SSE) for live updates
- Automatic refresh when new messages arrive
- Live connection status indicator
- Event counter

### 5. Privacy Features
- Phone numbers are hashed (SHA-256, first 16 chars)
- PII redaction in messages:
  - Phone numbers → [PHONE]
  - Email addresses → [EMAIL]
  - Credit card numbers → [CARD]
- No storage of raw phone numbers
- All data marked as synthetic

## Architecture

### Database Schema

```sql
CREATE TABLE analytics.whatsapp_lab_messages (
    id SERIAL PRIMARY KEY,
    message_id TEXT UNIQUE NOT NULL,
    from_hash TEXT NOT NULL,
    profile_name TEXT,
    message_text TEXT NOT NULL,
    message_text_redacted TEXT NOT NULL,
    category VARCHAR(50),
    branch VARCHAR(20) CHECK (branch IN ('low', 'mid', 'critical')),
    risk_level INTEGER CHECK (risk_level BETWEEN 1 AND 10),
    human_required BOOLEAN DEFAULT FALSE,
    p0_signals TEXT[],
    bot_reply TEXT,
    source VARCHAR(20) DEFAULT 'webchat',
    synthetic BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    processed_at TIMESTAMP
);
```

### API Endpoints

#### POST /whatsapp-lab/messages
Create and classify a new message.

**Request:**
```json
{
  "from_number": "+525512345678",
  "profile_name": "Usuario Demo",
  "message": "Hay un incendio en mi edificio"
}
```

**Response:**
```json
{
  "message_id": "msg_abc123",
  "category": "protection_civil",
  "branch": "critical",
  "risk_level": 9,
  "human_required": true,
  "p0_signals": ["incendio"],
  "bot_reply": "✅ Recibimos tu reporte. Se clasificó como Protección Civil con prioridad crítica. Un operador humano debe revisar el caso. Folio: msg_abc123",
  "created_at": "2026-06-06T18:00:00.000Z"
}
```

#### GET /whatsapp-lab/messages/recent?limit=50
Get recent messages.

**Response:**
```json
{
  "messages": [...],
  "count": 50
}
```

#### GET /whatsapp-lab/summary
Get summary statistics.

**Response:**
```json
{
  "total_messages": 1234,
  "last_24h": 156,
  "by_branch": {
    "critical": 45,
    "mid": 67,
    "low": 44
  },
  "by_category": {
    "security": 34,
    "medical": 28,
    ...
  },
  "human_required_count": 89,
  "p0_count": 23,
  "generated_at": "2026-06-06T18:00:00.000Z"
}
```

#### GET /whatsapp-lab/events
Server-Sent Events endpoint for real-time updates.

**Events:**
- `connected`: Initial connection
- `whatsapp_lab_update`: New message inserted/updated/deleted
- `heartbeat`: Keep-alive every 15 seconds

### PostgreSQL NOTIFY/LISTEN

Triggers on `analytics.whatsapp_lab_messages`:
- `notify_whatsapp_lab_insert`
- `notify_whatsapp_lab_update`
- `notify_whatsapp_lab_delete`

Channel: `whatsapp_lab_updates`

## Frontend Components

### Route: /whatsapp-lab

**Components:**
- Summary cards (total, critical, human required, P0)
- Chat interface with message bubbles
- Category distribution sidebar
- Example messages for quick testing
- Export PDF button

**Features:**
- Real-time SSE connection
- Auto-scroll to latest message
- Message classification badges
- Live connection indicator

## Testing

### Manual Testing
1. Navigate to http://127.0.0.1:5173/whatsapp-lab
2. Type a message in the input field
3. Press Enter or click Send
4. Observe the classification in the bot response

### Automated Testing
```bash
./scripts/12_test_whatsapp_lab.sh
```

Tests 5 scenarios:
1. Incendio (protection_civil/critical)
2. Bache (public_services/low)
3. Herido (medical/critical with P0)
4. Robo (security/critical)
5. Violencia familiar (victim_attention)

## PDF Export

Click "Exportar PDF" button to generate a printable report.

**Print CSS:**
- Hides navigation and interactive elements
- Removes background colors
- Preserves structure and borders
- Optimizes page breaks
- Shows print-only disclaimer

## Security & Privacy

### Data Protection
- Phone numbers hashed before storage
- PII redacted from message text
- No raw phone numbers in database
- All data marked as synthetic

### Local Only
- No external API calls
- No WhatsApp Business API integration
- All processing happens locally
- No data leaves the laptop

## Limitations

1. **No Real WhatsApp Integration**: This is a simulator, not connected to WhatsApp Business API
2. **Keyword-Based Classification**: Uses simple keyword matching, not ML
3. **Demo Data Only**: All data is synthetic and for testing purposes
4. **Local Environment**: Designed for laptop/lab use, not production

## Future Enhancements

Potential improvements (not implemented):
- Machine learning classification
- Multi-language support
- Image/media handling
- WhatsApp Business API integration
- Advanced NLP for intent detection
- Sentiment analysis
- Location extraction

## Troubleshooting

### SSE Not Connecting
- Check that api-analytics is running
- Verify PostgreSQL NOTIFY/LISTEN is working
- Check browser console for errors
- Ensure CORS is properly configured

### Messages Not Classifying
- Verify keywords are in the message
- Check api-analytics logs
- Ensure database triggers are active
- Test with example messages

### PDF Export Issues
- Use Chrome/Edge for best results
- Check print CSS is loaded
- Verify print-only elements are visible
- Adjust browser print settings

## Related Documentation

- [SSE Real-time Updates](./sse_realtime_updates.md)
- [API Contract](./api_contract.md)
- [Privacy & Legal](./legal_privacy.md)
- [Architecture](./architecture.md)
export interface Reading {
    id: string;
    v: number;
    seq: number | null;
    uptime_s: number | null;
    valid: boolean;
    temp_c: number | null;
    humidity_pct: number | null;
    gas_raw: number | null;
    motion: boolean | null;
    received_at: string;
}

export interface Device {
    id: string;
    last_seen: string;
    online: boolean;
}

export interface Event {
    type: string;
    source: string;
    confidence: number | null;
    details: Record<string, unknown> | null;
    received_at: string;
}

export interface WebSocketMessage {
    type: 'reading' | 'event' | 'command';
    payload: Reading | Event | Record<string, unknown>;
}
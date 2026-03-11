/**
 * MemoryOS — Ingest Load Test (k6)
 * 
 * Tests: INGEST ACK latency SLO (p99 ≤ 80ms at 500 concurrent writes)
 * PRD Reference: §10.1 (SLO Layer: INGEST ACK)
 * Phase A Exit Criterion: Ingest ACK p99 ≤ 80ms at 500 concurrent writes
 * 
 * Usage:
 *   k6 run tests/load/ingest.js --summary-export artifacts/load/ingest.json
 *   k6 run tests/load/ingest.js --vus 500 --duration 60s  # Phase A gate
 */

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Counter, Trend } from 'k6/metrics';
import { uuidv4 } from 'https://jslib.k6.io/k6-utils/1.4.0/index.js';

// Custom metrics aligned to PRD §10.1
const ingestAckDuration = new Trend('memoryos_ingest_ack_ms', true);
const ingestSuccess = new Counter('memoryos_ingest_success');
const ingestError = new Counter('memoryos_ingest_error');

// Configuration
const BASE_URL = __ENV.MEMORYOS_BASE_URL || 'http://localhost:8000/v1';
const API_KEY = __ENV.MEMORYOS_API_KEY || 'test-api-key';
const REPO_ID = __ENV.MEMORYOS_REPO_ID || '00000000-0000-0000-0000-000000000001';

export const options = {
  // Default: ramp to Phase A gate target
  stages: [
    { duration: '10s', target: 50 },    // warm-up
    { duration: '30s', target: 200 },   // ramp
    { duration: '60s', target: 500 },   // sustained at Phase A gate target
    { duration: '10s', target: 0 },     // cool-down
  ],
  thresholds: {
    // PRD §10.1: INGEST ACK p99 ≤ 80ms
    'memoryos_ingest_ack_ms': ['p(99)<80'],
    // Standard HTTP checks
    'http_req_failed': ['rate<0.01'],   // < 1% error rate
    'http_req_duration': ['p(95)<100'], // general HTTP p95
  },
};

// Generate realistic memory content
function generateMemoryContent() {
  const templates = [
    'User prefers to use Python for data analysis tasks rather than R.',
    'The API endpoint /api/v2/users has a rate limit of 100 requests per minute.',
    'Project deadline was moved from March 15 to March 22 to accommodate testing.',
    'The database migration requires PostgreSQL 16 for JSON path query support.',
    'Agent observed that response latency increases during peak hours (2-4 PM UTC).',
    'User confirmed preference for concise summaries over detailed explanations.',
    'The CI pipeline fails intermittently on the integration test for Kafka consumers.',
    'Team agreed to use event sourcing pattern for the memory write path.',
  ];
  return templates[Math.floor(Math.random() * templates.length)];
}

export default function () {
  const payload = JSON.stringify({
    content: generateMemoryContent(),
    source_type: 'OBSERVATION',
    priority: 'normal',
    branch: 'main',
    data_class: 'GENERAL',
  });

  const params = {
    headers: {
      'Content-Type': 'application/json',
      'X-API-Key': API_KEY,
      'Idempotency-Key': uuidv4(),
    },
  };

  const response = http.post(
    `${BASE_URL}/repos/${REPO_ID}/memory`,
    payload,
    params
  );

  // Track custom metric
  ingestAckDuration.add(response.timings.duration);

  const success = check(response, {
    'status is 200 or 202': (r) => r.status === 200 || r.status === 202,
    'has commit_hash': (r) => {
      try {
        const body = JSON.parse(r.body);
        return body.commit_hash && body.commit_hash.length === 64;
      } catch {
        return false;
      }
    },
    'has action': (r) => {
      try {
        const body = JSON.parse(r.body);
        return ['WRITTEN', 'DEDUPLICATED', 'QUEUED', 'SANDBOXED', 'BLOCKED'].includes(body.action);
      } catch {
        return false;
      }
    },
  });

  if (success) {
    ingestSuccess.add(1);
  } else {
    ingestError.add(1);
  }

  // Minimal think time between requests
  sleep(0.1);
}

export function handleSummary(data) {
  return {
    'stdout': textSummary(data, { indent: ' ', enableColors: true }),
  };
}

import { textSummary } from 'https://jslib.k6.io/k6-summary/0.0.3/index.js';

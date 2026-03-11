/**
 * MemoryOS — Retrieval Load Test (k6)
 *
 * Tests: RETRIEVAL latency SLO (p99 ≤ 350ms at 200 concurrent retrievals)
 * PRD Reference: §10.1 (SLO Layer: RETRIEVAL)
 * Phase A Exit Criterion: Retrieval p99 ≤ 350ms at 200 concurrent retrievals
 *
 * Usage:
 *   k6 run tests/load/retrieve.js --summary-export artifacts/load/retrieve.json
 *   k6 run tests/load/retrieve.js --vus 200 --duration 60s  # Phase A gate
 */

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Counter, Trend } from 'k6/metrics';

// Custom metrics aligned to PRD §10.1
const retrievalDuration = new Trend('memoryos_retrieval_ms', true);
const retrievalSuccess = new Counter('memoryos_retrieval_success');
const retrievalError = new Counter('memoryos_retrieval_error');

// Configuration
const BASE_URL = __ENV.MEMORYOS_BASE_URL || 'http://localhost:8000/v1';
const API_KEY = __ENV.MEMORYOS_API_KEY || 'test-api-key';
const REPO_ID = __ENV.MEMORYOS_REPO_ID || '00000000-0000-0000-0000-000000000001';

export const options = {
  stages: [
    { duration: '10s', target: 50 },    // warm-up
    { duration: '30s', target: 100 },   // ramp
    { duration: '60s', target: 200 },   // sustained at Phase A gate target
    { duration: '10s', target: 0 },     // cool-down
  ],
  thresholds: {
    // PRD §10.1: RETRIEVAL p99 ≤ 350ms
    'memoryos_retrieval_ms': ['p(99)<350'],
    'http_req_failed': ['rate<0.01'],
    'http_req_duration': ['p(95)<400'],
  },
};

// Diverse query set for realistic retrieval patterns
function generateQuery() {
  const queries = [
    'What does the user prefer for data analysis?',
    'What are the API rate limits?',
    'When is the project deadline?',
    'What database version is required?',
    'What happens during peak hours?',
    'How does the user prefer summaries?',
    'What are the known CI pipeline issues?',
    'What architecture patterns were decided?',
    'What are the user communication preferences?',
    'What tools does the team use?',
  ];
  return queries[Math.floor(Math.random() * queries.length)];
}

export default function () {
  const payload = JSON.stringify({
    query: generateQuery(),
    token_budget: 2000,
    include_tiers: ['WORKING', 'EPISODIC', 'SEMANTIC'],
    branch: 'main',
    min_confidence: 0.3,
    min_importance: 0.0,
  });

  const params = {
    headers: {
      'Content-Type': 'application/json',
      'X-API-Key': API_KEY,
    },
  };

  const response = http.post(
    `${BASE_URL}/repos/${REPO_ID}/retrieve`,
    payload,
    params
  );

  retrievalDuration.add(response.timings.duration);

  const success = check(response, {
    'status is 200': (r) => r.status === 200,
    'has memories array': (r) => {
      try {
        const body = JSON.parse(r.body);
        return Array.isArray(body.memories);
      } catch {
        return false;
      }
    },
    'has token_count': (r) => {
      try {
        const body = JSON.parse(r.body);
        return typeof body.token_count === 'number';
      } catch {
        return false;
      }
    },
    'token_count within budget': (r) => {
      try {
        const body = JSON.parse(r.body);
        return body.token_count <= 2000;
      } catch {
        return false;
      }
    },
  });

  if (success) {
    retrievalSuccess.add(1);
  } else {
    retrievalError.add(1);
  }

  sleep(0.2);
}

import { textSummary } from 'https://jslib.k6.io/k6-summary/0.0.3/index.js';

export function handleSummary(data) {
  return {
    'stdout': textSummary(data, { indent: ' ', enableColors: true }),
  };
}

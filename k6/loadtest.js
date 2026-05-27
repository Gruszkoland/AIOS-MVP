import { check, group, sleep } from 'k6';
import http from 'k6/http';
import { Counter, Rate, Trend } from 'k6/metrics';

// Performance metrics
const errorRate = new Rate('errors');
const apiLatency = new Trend('api_latency');
const dbLatency = new Trend('db_latency');
const p95Latency = new Trend('p95_latency');
const requestsPerSecond = new Counter('requests');

export const options = {
  vus: __ENV.VUS || 50,
  duration: __ENV.DURATION || '5m',
  thresholds: {
    'errors': ['rate<0.01'],  // Error rate < 1%
    'api_latency': ['p(95)<500', 'p(99)<1000'],  // p95 < 500ms, p99 < 1s
    'db_latency': ['p(95)<200', 'p(99)<500'],    // DB p95 < 200ms
    'http_req_duration': ['p(95)<600'],           // HTTP p95 < 600ms
    'http_req_failed': ['rate<0.01'],             // HTTP failure < 1%
  },
  stages: [
    { duration: '1m', target: __ENV.VUS || 50 },
    { duration: '3m', target: __ENV.VUS || 50 },
    { duration: '1m', target: 0 },
  ],
  ext: {
    loadimpact: {
      projectID: __ENV.LOADIMPACT_PROJECT_ID || null,
      name: 'ADRION 369 Load Test',
    },
  },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8003';
const API_HEALTH_URL = `${BASE_URL}/health`;
const JOBS_URL = `${BASE_URL}/api/v1/jobs`;
const BIDS_URL = `${BASE_URL}/api/v1/bids`;

export function setup() {
  console.log(`Load test starting: BASE_URL=${BASE_URL}, VUS=${options.vus}, DURATION=${options.duration}`);

  // Health check before test
  const res = http.get(API_HEALTH_URL, {
    tags: { name: 'health_check' },
  });

  check(res, {
    'health check passed': (r) => r.status === 200,
    'service ready': (r) => r.json('status') === 'ready',
  }) || (__ENV.STRICT && __stop());

  return { baseUrl: BASE_URL };
}

export default function (data) {
  const baseUrl = data.baseUrl;

  group('1. Health & Liveness Checks', () => {
    const healthRes = http.get(`${baseUrl}/health`, {
      tags: { name: 'health' },
    });
    apiLatency.add(healthRes.timings.duration, { endpoint: 'health' });
    check(healthRes, {
      'health status 200': (r) => r.status === 200,
      'health response time < 100ms': (r) => r.timings.duration < 100,
    }) || (errorRate.add(1));
    requestsPerSecond.add(1);

    sleep(0.5);

    const liveRes = http.get(`${baseUrl}/health/live`, {
      tags: { name: 'health_live' },
    });
    apiLatency.add(liveRes.timings.duration, { endpoint: 'health_live' });
    check(liveRes, {
      'liveness check status 200': (r) => r.status === 200,
    }) || (errorRate.add(1));
    requestsPerSecond.add(1);

    sleep(0.5);

    const readyRes = http.get(`${baseUrl}/health/ready`, {
      tags: { name: 'health_ready' },
    });
    apiLatency.add(readyRes.timings.duration, { endpoint: 'health_ready' });
    check(readyRes, {
      'readiness check status 200': (r) => r.status === 200,
    }) || (errorRate.add(1));
    requestsPerSecond.add(1);
  });

  sleep(1);

  group('2. Job Endpoints', () => {
    // GET /api/v1/jobs
    const jobsRes = http.get(JOBS_URL, {
      tags: { name: 'get_jobs' },
    });
    apiLatency.add(jobsRes.timings.duration, { endpoint: 'jobs' });
    check(jobsRes, {
      'jobs list status 200': (r) => r.status === 200,
      'jobs response time < 500ms': (r) => r.timings.duration < 500,
      'jobs response valid JSON': (r) => r.json() !== null,
    }) || (errorRate.add(1));
    requestsPerSecond.add(1);

    sleep(0.5);

    // POST /api/v1/jobs
    const jobPayload = {
      name: `test-job-${Date.now()}`,
      description: 'Load test job',
      status: 'pending',
    };
    const postJobRes = http.post(JOBS_URL, JSON.stringify(jobPayload), {
      headers: { 'Content-Type': 'application/json' },
      tags: { name: 'create_job' },
    });
    apiLatency.add(postJobRes.timings.duration, { endpoint: 'create_job' });
    check(postJobRes, {
      'create job status 201': (r) => r.status === 201,
      'create job response time < 600ms': (r) => r.timings.duration < 600,
      'create job returns ID': (r) => r.json('id') !== null,
    }) || (errorRate.add(1));
    requestsPerSecond.add(1);

    // Extract job ID if successful
    if (postJobRes.status === 201) {
      const jobId = postJobRes.json('id');
      sleep(0.3);

      // GET /api/v1/jobs/{id}
      const getJobRes = http.get(`${JOBS_URL}/${jobId}`, {
        tags: { name: 'get_job_detail' },
      });
      apiLatency.add(getJobRes.timings.duration, { endpoint: 'get_job_detail' });
      check(getJobRes, {
        'get job detail status 200': (r) => r.status === 200,
        'job detail matches ID': (r) => r.json('id') === jobId,
      }) || (errorRate.add(1));
      requestsPerSecond.add(1);
    }
  });

  sleep(1);

  group('3. Bid Endpoints', () => {
    // GET /api/v1/bids
    const bidsRes = http.get(BIDS_URL, {
      tags: { name: 'get_bids' },
    });
    apiLatency.add(bidsRes.timings.duration, { endpoint: 'bids' });
    check(bidsRes, {
      'bids list status 200': (r) => r.status === 200,
      'bids response time < 500ms': (r) => r.timings.duration < 500,
    }) || (errorRate.add(1));
    requestsPerSecond.add(1);

    sleep(0.5);

    // POST /api/v1/bids
    const bidPayload = {
      job_id: 'test-job-001',
      amount: 500.00,
      status: 'pending',
    };
    const postBidRes = http.post(BIDS_URL, JSON.stringify(bidPayload), {
      headers: { 'Content-Type': 'application/json' },
      tags: { name: 'create_bid' },
    });
    apiLatency.add(postBidRes.timings.duration, { endpoint: 'create_bid' });
    check(postBidRes, {
      'create bid status 201': (r) => r.status === 201,
      'create bid response time < 600ms': (r) => r.timings.duration < 600,
    }) || (errorRate.add(1));
    requestsPerSecond.add(1);
  });

  sleep(1);

  group('4. Metrics Endpoint', () => {
    const metricsRes = http.get(`${baseUrl}/metrics`, {
      tags: { name: 'metrics' },
    });
    apiLatency.add(metricsRes.timings.duration, { endpoint: 'metrics' });
    check(metricsRes, {
      'metrics endpoint status 200': (r) => r.status === 200,
      'metrics contains Prometheus format': (r) => r.body.includes('# HELP'),
    }) || (errorRate.add(1));
    requestsPerSecond.add(1);
  });

  sleep(2);
}

export function teardown(data) {
  console.log(`Load test completed. Summary: BASE_URL=${data.baseUrl}`);
}

export function handleSummary(data) {
  return {
    stdout: textSummary(data, { indent: ' ', enableColors: true }),
    'summary.json': JSON.stringify(data),
  };
}

function textSummary(data, options) {
  let summary = '\n=== k6 Load Test Summary ===\n';
  summary += `Request Count: ${data.metrics.http_reqs?.values?.count || 0}\n`;
  summary += `Error Rate: ${((data.metrics.http_req_failed?.values?.rate || 0) * 100).toFixed(2)}%\n`;
  summary += `p95 Latency: ${data.metrics.http_req_duration?.values?.['p(95)']?.toFixed(0) || 'N/A'}ms\n`;
  summary += `p99 Latency: ${data.metrics.http_req_duration?.values?.['p(99)']?.toFixed(0) || 'N/A'}ms\n`;
  return summary;
}

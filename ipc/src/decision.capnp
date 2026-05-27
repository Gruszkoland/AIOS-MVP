@0xd2b1c0a37e8f4f2a;

# Decision: Rust kernel → Agent (via ring buffer IPC)

struct Decision {
  jobId @0 :UInt64;
  agentType @1 :UInt16;              # Guardian agent ID (0-8)
  payload @2 :Data;                  # Agent-specific data (max 4KB)
  timestamp @3 :UInt64;              # nanoseconds since epoch
  priority @4 :UInt8;                # 0=low, 255=critical
  timeout @5 :UInt32;                # decision timeout (ms)
  contextHash @6 :UInt64;            # H(context) for validation
}

# Response: Agent → Rust kernel (via ring buffer IPC)

struct Response {
  jobId @0 :UInt64;                  # matches Decision.jobId
  agentType @1 :UInt16;              # responding agent
  decision @2 :UInt8;                # 0=DENY, 1=APPROVE, 2=PENDING
  confidence @3 :Float32;            # [0.0, 1.0]
  reasoning @4 :Data;                # explanation (max 2KB)
  timestamp @5 :UInt64;              # response time
  latency @6 :UInt32;                # agent processing time (ns)
  context @7 :Guardian;              # guardian-specific result
}

# Guardian: Per-agent result context

struct Guardian {
  guardianId @0 :UInt8;              # 0=Librarian, 1=SAP, 2=Auditor...
  checkPassed @1 :Bool;
  riskScore @2 :Float32;             # [0.0, 1.0]
  recommendation @3 :UInt8;          # 0=block, 1=monitor, 2=approve
}

# Batch: Ring buffer can encode multiple decisions/responses

struct Batch {
  batchId @0 :UInt64;
  count @1 :UInt16;
  decisions @2 :List(Decision);
  responses @3 :List(Response);
  timestamp @4 :UInt64;
}

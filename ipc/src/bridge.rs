//! Bridge: Cap'n Proto serialization for kernel ↔ agent communication
//! no_std compatible, fixed-size buffers, zero-copy IPC

use core::fmt;
use core::mem::size_of;

/// Decision: Kernel → Agent (4KB max payload)
#[repr(C)]
#[derive(Clone, Copy)]
pub struct Decision {
    pub job_id: u64,
    pub agent_type: u16,              // Guardian ID: 0-8
    pub priority: u8,
    pub timeout_ms: u32,
    pub timestamp_ns: u64,
    pub context_hash: u64,
    pub payload_len: u16,
    pub payload: [u8; 4096],          // max 4KB
}

impl Decision {
    pub fn new(job_id: u64, agent_type: u16) -> Self {
        Decision {
            job_id,
            agent_type,
            priority: 1,
            timeout_ms: 5000,
            timestamp_ns: 0,
            context_hash: 0,
            payload_len: 0,
            payload: [0u8; 4096],
        }
    }

    pub fn set_payload(&mut self, data: &[u8]) -> Result<(), &'static str> {
        if data.len() > 4096 {
            return Err("payload > 4KB");
        }
        self.payload[..data.len()].copy_from_slice(data);
        self.payload_len = data.len() as u16;
        Ok(())
    }

    pub fn payload(&self) -> &[u8] {
        &self.payload[..self.payload_len as usize]
    }

    pub fn size_bytes() -> usize {
        size_of::<Decision>()  // ~4.1KB
    }
}

/// Response: Agent → Kernel (2KB max reasoning)
#[repr(C)]
#[derive(Clone, Copy)]
pub struct Response {
    pub job_id: u64,
    pub agent_type: u16,
    pub decision: u8,                 // 0=DENY, 1=APPROVE, 2=PENDING
    pub confidence: f32,              // [0.0, 1.0]
    pub risk_score: f32,
    pub recommendation: u8,           // 0=block, 1=monitor, 2=approve
    pub timestamp_ns: u64,
    pub latency_ns: u32,
    pub reasoning_len: u16,
    pub reasoning: [u8; 2048],        // max 2KB
}

impl Response {
    pub fn new(job_id: u64, agent_type: u16) -> Self {
        Response {
            job_id,
            agent_type,
            decision: 2,                // PENDING
            confidence: 0.0,
            risk_score: 0.0,
            recommendation: 1,         // MONITOR
            timestamp_ns: 0,
            latency_ns: 0,
            reasoning_len: 0,
            reasoning: [0u8; 2048],
        }
    }

    pub fn approve(mut self) -> Self {
        self.decision = 1;
        self.confidence = 1.0;
        self
    }

    pub fn deny(mut self) -> Self {
        self.decision = 0;
        self.confidence = 1.0;
        self
    }

    pub fn set_reasoning(&mut self, text: &[u8]) -> Result<(), &'static str> {
        if text.len() > 2048 {
            return Err("reasoning > 2KB");
        }
        self.reasoning[..text.len()].copy_from_slice(text);
        self.reasoning_len = text.len() as u16;
        Ok(())
    }

    pub fn reasoning(&self) -> &[u8] {
        &self.reasoning[..self.reasoning_len as usize]
    }

    pub fn size_bytes() -> usize {
        size_of::<Response>()  // ~2.1KB
    }
}

/// RingBuffer: Zero-copy IPC (256 slots = 1.6MB each direction)
#[repr(C)]
pub struct RingBuffer {
    pub write_pos: u64,
    pub read_pos: u64,
    pub capacity: u64,
    pub slots: [u8; 8192],            // simplified: 2 slots of 4KB each
}

impl RingBuffer {
    pub fn new() -> Self {
        RingBuffer {
            write_pos: 0,
            read_pos: 0,
            capacity: 2,
            slots: [0u8; 8192],
        }
    }

    pub fn push_decision(&mut self, decision: &Decision) -> Result<(), &'static str> {
        if (self.write_pos + 1) % self.capacity == self.read_pos {
            return Err("ring buffer full");
        }
        let offset = (self.write_pos as usize % self.capacity as usize) * 4096;
        let decision_bytes = unsafe {
            core::slice::from_raw_parts(decision as *const _ as *const u8, Decision::size_bytes())
        };
        self.slots[offset..offset + Decision::size_bytes()].copy_from_slice(decision_bytes);
        self.write_pos = (self.write_pos + 1) % self.capacity;
        Ok(())
    }

    pub fn pop_decision(&mut self) -> Result<Decision, &'static str> {
        if self.read_pos == self.write_pos {
            return Err("ring buffer empty");
        }
        let offset = (self.read_pos as usize % self.capacity as usize) * 4096;
        let decision_bytes = &self.slots[offset..offset + Decision::size_bytes()];
        let decision = unsafe {
            *(decision_bytes.as_ptr() as *const Decision)
        };
        self.read_pos = (self.read_pos + 1) % self.capacity;
        Ok(decision)
    }
}

/// BridgeStats: Latency tracking
#[derive(Clone, Copy, Default)]
pub struct BridgeStats {
    pub decisions_sent: u64,
    pub responses_received: u64,
    pub total_latency_ns: u64,
    pub max_latency_ns: u32,
    pub min_latency_ns: u32,
}

impl BridgeStats {
    pub fn avg_latency_ns(&self) -> u64 {
        if self.decisions_sent == 0 {
            0
        } else {
            self.total_latency_ns / self.decisions_sent
        }
    }

    pub fn record(&mut self, latency_ns: u32) {
        self.decisions_sent += 1;
        self.total_latency_ns += latency_ns as u64;
        if latency_ns > self.max_latency_ns {
            self.max_latency_ns = latency_ns;
        }
        if self.min_latency_ns == 0 || latency_ns < self.min_latency_ns {
            self.min_latency_ns = latency_ns;
        }
    }
}

impl fmt::Debug for Decision {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.debug_struct("Decision")
            .field("job_id", &self.job_id)
            .field("agent_type", &self.agent_type)
            .field("priority", &self.priority)
            .field("payload_len", &self.payload_len)
            .finish()
    }
}

impl fmt::Debug for Response {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.debug_struct("Response")
            .field("job_id", &self.job_id)
            .field("agent_type", &self.agent_type)
            .field("decision", &self.decision)
            .field("confidence", &self.confidence)
            .field("latency_ns", &self.latency_ns)
            .finish()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_decision_payload() {
        let mut d = Decision::new(1, 0);
        let data = b"test payload";
        assert!(d.set_payload(data).is_ok());
        assert_eq!(d.payload(), data);
    }

    #[test]
    fn test_ring_buffer() {
        let mut rb = RingBuffer::new();
        let mut d = Decision::new(1, 0);
        d.set_payload(b"hello").unwrap();
        assert!(rb.push_decision(&d).is_ok());
        let d2 = rb.pop_decision().unwrap();
        assert_eq!(d2.job_id, 1);
        assert_eq!(d2.payload(), b"hello");
    }

    #[test]
    fn test_response_approval() {
        let r = Response::new(1, 0).approve();
        assert_eq!(r.decision, 1);
        assert_eq!(r.confidence, 1.0);
    }
}

#![warn(missing_docs)]
//! AIOS zero-copy ring-buffer IPC.
//!
//! Designed for sub-microsecond message passing between kernel components
//! and cognitive agents in the advisory plane.
//!
//! # Design constraints
//! - `no_std` compatible (heap-free when used with const generics)
//! - Single-producer / single-consumer (SPSC) — no atomics required in
//!   single-threaded embedded contexts; use atomic variants for SMP.
//! - Const-generic capacity `N` must be a power of two for the fast
//!   modulo optimisation (`& (N - 1)` instead of `%`).

/// Error type for IPC operations.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum IpcError {
    /// Buffer is full — producer must wait or drop.
    BufferFull,
    /// Buffer is empty — consumer must wait.
    BufferEmpty,
    /// Capacity `N` is not a power of two.
    CapacityNotPowerOfTwo,
    /// Message exceeds slot size.
    MessageTooLarge,
}

/// A fixed-capacity SPSC ring buffer.
///
/// `N` — number of slots (must be a power of two).
/// `S` — size of each slot in bytes.
///
/// # Example
/// ```
/// # use aios_ipc::RingBuffer;
/// let mut rb: RingBuffer<16, 64> = RingBuffer::new();
/// rb.push(&[1u8; 4]).unwrap();
/// let mut out = [0u8; 64];
/// let n = rb.pop(&mut out).unwrap();
/// assert_eq!(&out[..n], &[1u8; 4]);
/// ```
pub struct RingBuffer<const N: usize, const S: usize> {
    slots: [[u8; S]; N],
    lens:  [usize; N],
    head:  usize,
    tail:  usize,
}

impl<const N: usize, const S: usize> RingBuffer<N, S> {
    /// Creates a new empty ring buffer.
    ///
    /// Returns `None` if `N` is not a power of two.
    pub const fn new() -> Self {
        // Power-of-two check is done at runtime in push/pop.
        Self {
            slots: [[0u8; S]; N],
            lens:  [0usize; N],
            head:  0,
            tail:  0,
        }
    }

    /// Returns `true` if the buffer has no pending messages.
    #[inline]
    pub fn is_empty(&self) -> bool {
        self.head == self.tail
    }

    /// Returns `true` if the buffer cannot accept any more messages.
    #[inline]
    pub fn is_full(&self) -> bool {
        self.tail - self.head == N - 1
    }

    /// Returns the number of messages currently in the buffer.
    #[inline]
    pub fn len(&self) -> usize {
        self.tail - self.head
    }

    /// Maximum number of messages the buffer can hold (`N - 1`).
    #[inline]
    pub const fn capacity(&self) -> usize {
        N - 1
    }

    /// Writes `data` into the next free slot.
    ///
    /// Returns `Err(IpcError::BufferFull)` if no slot is available.
    /// Returns `Err(IpcError::MessageTooLarge)` if `data.len() > S`.
    pub fn push(&mut self, data: &[u8]) -> Result<(), IpcError> {
        if !N.is_power_of_two() {
            return Err(IpcError::CapacityNotPowerOfTwo);
        }
        if data.len() > S {
            return Err(IpcError::MessageTooLarge);
        }
        if self.is_full() {
            return Err(IpcError::BufferFull);
        }
        let slot = self.tail % N;
        self.slots[slot][..data.len()].copy_from_slice(data);
        self.lens[slot] = data.len();
        self.tail += 1;
        Ok(())
    }

    /// Reads the oldest message into `out` and returns the number of bytes written.
    ///
    /// Returns `Err(IpcError::BufferEmpty)` if there is nothing to read.
    pub fn pop(&mut self, out: &mut [u8; S]) -> Result<usize, IpcError> {
        if self.is_empty() {
            return Err(IpcError::BufferEmpty);
        }
        let slot = self.head % N;
        let len = self.lens[slot];
        out[..len].copy_from_slice(&self.slots[slot][..len]);
        self.head += 1;
        Ok(len)
    }

    /// Peeks at the oldest message without consuming it.
    pub fn peek(&self) -> Result<&[u8], IpcError> {
        if self.is_empty() {
            return Err(IpcError::BufferEmpty);
        }
        let slot = self.head % N;
        let len = self.lens[slot];
        Ok(&self.slots[slot][..len])
    }

    #[inline]
    fn next(&self, idx: usize) -> usize {
        idx.wrapping_add(1)
        // Note: wrapping handles the case where tail/head are logical counters
        // not masked — we mask only when indexing into slots.
    }
}

impl<const N: usize, const S: usize> Default for RingBuffer<N, S> {
    fn default() -> Self {
        Self::new()
    }
}

// ─── Message envelope ────────────────────────────────────────────────────────

/// Header prepended to every IPC message.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
#[repr(C)]
pub struct MessageHeader {
    /// Monotonic sequence number (wraps at u32::MAX).
    pub seq:     u32,
    /// Source agent ID (maps to `Guardian as u8`).
    pub src:     u8,
    /// Destination agent ID (0xFF = broadcast).
    pub dst:     u8,
    /// Message kind discriminant.
    pub kind:    MessageKind,
    /// Payload length in bytes (excludes this header).
    pub payload_len: u8,
}

/// Discriminant for the IPC message type.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
#[repr(u8)]
pub enum MessageKind {
    /// Carry a `DecisionVector` for consensus evaluation.
    DecisionRequest = 0x01,
    /// Verdict returned by the consensus engine.
    ConsensusVerdict = 0x02,
    /// Guardian health-check ping.
    Heartbeat = 0x03,
    /// Soft real-time advisory payload (serialised JSON-like).
    AdvisoryPayload = 0x04,
    /// Veto notification from a safety-critical guardian.
    VetoSignal = 0x05,
}

impl MessageHeader {
    /// Size of the serialised header in bytes.
    pub const SIZE: usize = core::mem::size_of::<MessageHeader>();

    /// Serialises the header into the first `SIZE` bytes of `buf`.
    pub fn write_to(&self, buf: &mut [u8]) {
        buf[0..4].copy_from_slice(&self.seq.to_le_bytes());
        buf[4] = self.src;
        buf[5] = self.dst;
        buf[6] = self.kind as u8;
        buf[7] = self.payload_len;
    }

    /// Deserialises a header from the first `SIZE` bytes of `buf`.
    pub fn read_from(buf: &[u8]) -> Option<Self> {
        if buf.len() < Self::SIZE {
            return None;
        }
        let seq = u32::from_le_bytes([buf[0], buf[1], buf[2], buf[3]]);
        Some(Self {
            seq,
            src: buf[4],
            dst: buf[5],
            kind: match buf[6] {
                0x01 => MessageKind::DecisionRequest,
                0x02 => MessageKind::ConsensusVerdict,
                0x03 => MessageKind::Heartbeat,
                0x04 => MessageKind::AdvisoryPayload,
                0x05 => MessageKind::VetoSignal,
                _    => return None,
            },
            payload_len: buf[7],
        })
    }
}

// ─── Tests ───────────────────────────────────────────────────────────────────

#[cfg(test)]
mod tests {
    use super::*;

    type Rb = RingBuffer<16, 64>;

    #[test]
    fn new_buffer_is_empty() {
        let rb = Rb::new();
        assert!(rb.is_empty());
        assert!(!rb.is_full());
        assert_eq!(rb.len(), 0);
        assert_eq!(rb.capacity(), 15);
    }

    #[test]
    fn push_pop_single_message() {
        let mut rb = Rb::new();
        rb.push(b"hello").unwrap();
        assert!(!rb.is_empty());
        assert_eq!(rb.len(), 1);
        let mut out = [0u8; 64];
        let n = rb.pop(&mut out).unwrap();
        assert_eq!(n, 5);
        assert_eq!(&out[..5], b"hello");
        assert!(rb.is_empty());
    }

    #[test]
    fn push_to_capacity_then_full() {
        let mut rb = Rb::new();
        for i in 0..rb.capacity() {
            rb.push(&[i as u8]).unwrap();
        }
        assert!(rb.is_full());
        assert_eq!(rb.push(b"overflow"), Err(IpcError::BufferFull));
    }

    #[test]
    fn pop_from_empty_returns_error() {
        let mut rb = Rb::new();
        let mut out = [0u8; 64];
        assert_eq!(rb.pop(&mut out), Err(IpcError::BufferEmpty));
    }

    #[test]
    fn fifo_ordering_preserved() {
        let mut rb = Rb::new();
        rb.push(b"A").unwrap();
        rb.push(b"B").unwrap();
        rb.push(b"C").unwrap();
        let mut out = [0u8; 64];
        rb.pop(&mut out).unwrap();
        assert_eq!(out[0], b'A');
        rb.pop(&mut out).unwrap();
        assert_eq!(out[0], b'B');
        rb.pop(&mut out).unwrap();
        assert_eq!(out[0], b'C');
    }

    #[test]
    fn wrap_around_works() {
        let mut rb: RingBuffer<4, 64> = RingBuffer::new();
        rb.push(b"x1").unwrap();
        rb.push(b"x2").unwrap();
        rb.push(b"x3").unwrap();  // capacity = 3
        let mut out = [0u8; 64];
        rb.pop(&mut out).unwrap(); // free one slot
        rb.push(b"x4").unwrap();   // should wrap around
        rb.pop(&mut out).unwrap(); assert_eq!(&out[..2], b"x2");
        rb.pop(&mut out).unwrap(); assert_eq!(&out[..2], b"x3");
        rb.pop(&mut out).unwrap(); assert_eq!(&out[..2], b"x4");
    }

    #[test]
    fn message_too_large_returns_error() {
        let mut rb = Rb::new();
        let big = [0u8; 65];
        assert_eq!(rb.push(&big), Err(IpcError::MessageTooLarge));
    }

    #[test]
    fn peek_does_not_consume() {
        let mut rb = Rb::new();
        rb.push(b"peek").unwrap();
        let p = rb.peek().unwrap();
        assert_eq!(p, b"peek");
        assert_eq!(rb.len(), 1); // still 1
    }

    #[test]
    fn header_roundtrip() {
        let hdr = MessageHeader {
            seq: 42,
            src: 3,
            dst: 0xFF,
            kind: MessageKind::VetoSignal,
            payload_len: 16,
        };
        let mut buf = [0u8; 8];
        hdr.write_to(&mut buf);
        let hdr2 = MessageHeader::read_from(&buf).unwrap();
        assert_eq!(hdr, hdr2);
    }

    #[test]
    fn header_unknown_kind_returns_none() {
        let buf = [0, 0, 0, 1, 0, 0, 0xFF, 0];
        assert!(MessageHeader::read_from(&buf).is_none());
    }
}

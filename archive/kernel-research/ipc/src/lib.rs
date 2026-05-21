/// Zero-copy ring buffer for Agent Bus v2.
/// Latency target: <1µs per message.
pub struct RingBuffer<const N: usize> {
    buf: [u8; N],
    head: usize,
    tail: usize,
}

impl<const N: usize> RingBuffer<N> {
    pub const fn new() -> Self {
        Self { buf: [0; N], head: 0, tail: 0 }
    }

    pub fn capacity(&self) -> usize { N }
    pub fn is_empty(&self) -> bool { self.head == self.tail }
}

impl<const N: usize> Default for RingBuffer<N> {
    fn default() -> Self { Self::new() }
}

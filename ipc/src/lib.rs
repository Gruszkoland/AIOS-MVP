//! IPC Layer: Ring Buffer + Cap'n Proto Bridge
//! Zero-copy communication between kernel and agents

#![no_std]
#![forbid(unsafe_code)]  // bridge.rs contains only when necessary

pub mod bridge;

pub use bridge::{Decision, Response, RingBuffer, BridgeStats};

/// Version
pub const IPC_VERSION: &str = "0.2.0";

/// IPC Errors
#[derive(Debug, Clone, Copy)]
pub enum IpcError {
    BufferFull,
    BufferEmpty,
    PayloadTooLarge,
    InvalidPayload,
    SerializationError,
}

/// IPC Result
pub type IpcResult<T> = Result<T, IpcError>;

/// Bridge Transport: abstraction for Rust-Python communication
pub trait BridgeTransport {
    fn send_decision(&mut self, decision: &Decision) -> IpcResult<()>;
    fn receive_response(&mut self) -> IpcResult<Response>;
    fn stats(&self) -> BridgeStats;
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_version() {
        assert_eq!(IPC_VERSION, "0.2.0");
    }
}

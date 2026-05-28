//! IPC Layer: Ring Buffer + Cap'n Proto Bridge
//! Zero-copy communication between kernel and agents
//! Phase 1 Security Foundation: Signing + Integrity + Merkle + Config

pub mod bridge;
pub mod signing;
pub mod integrity;
pub mod merkle;
pub mod config_signing;
pub mod pbft;
pub mod quorum;
pub mod adaptive_timeout;

pub use bridge::{Decision, Response, RingBuffer, BridgeStats};
pub use signing::{PublicKey, Signature, SigningConfig, VerificationResult, verify_agent_binary};
pub use integrity::{CRC32, Timestamp, IntegrityResult, verify_integrity};
pub use merkle::{Hash, GenesisEntry, MerkleTree};
pub use config_signing::{ConfigEntry, ConfigAuditTrail};
pub use pbft::{ViewID, PBFTPhase, PBFTMessage, PBFTConsensus};
pub use quorum::{QuorumConfig, QuorumError, QuorumManager};
pub use adaptive_timeout::TimeoutAdaptor;

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

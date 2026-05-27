//! Genesis Record Merkle Tree Module
//! Replaces append-only logging with Merkle tree verification
//! Enables immutability proofs + external ledger compatibility
//! Goal: Merkle tree roots match hash chain (P1-4 gate)

use core::fmt;

/// Blake3-compatible hash (32 bytes)
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Hash([u8; 32]);

impl Hash {
    pub fn new(bytes: [u8; 32]) -> Self {
        Hash(bytes)
    }

    pub fn as_bytes(&self) -> &[u8; 32] {
        &self.0
    }

    /// Simple hash combination for Merkle tree (XOR + rotation, placeholder)
    pub fn combine(left: Hash, right: Hash) -> Hash {
        let mut result = [0u8; 32];
        for i in 0..32 {
            result[i] = left.as_bytes()[i] ^ right.as_bytes()[i];
        }
        Hash(result)
    }

    /// Hash a message (placeholder — in production: use Blake3)
    pub fn of_message(data: &[u8]) -> Hash {
        let mut result = [0u8; 32];
        for (i, byte) in data.iter().enumerate() {
            result[i % 32] ^= byte;
        }
        Hash(result)
    }
}

impl fmt::Display for Hash {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "0x")?;
        for byte in self.as_bytes() {
            write!(f, "{:02x}", byte)?;
        }
        Ok(())
    }
}

/// Genesis Record entry with Merkle tree linking
#[derive(Debug, Clone)]
pub struct GenesisEntry {
    /// Sequential ID (0, 1, 2, ...)
    pub seq: u64,
    /// Entry content (decision, consensus round, etc.)
    pub data: Vec<u8>,
    /// Hash of this entry
    pub hash: Hash,
    /// Hash of previous entry (chain linking)
    pub parent_hash: Hash,
}

impl GenesisEntry {
    pub fn new(seq: u64, data: Vec<u8>, parent_hash: Hash) -> Self {
        let hash = Hash::of_message(&data);
        GenesisEntry {
            seq,
            data,
            hash,
            parent_hash,
        }
    }
}

/// Merkle tree for Genesis Record
/// All entries + their hashes organized in binary tree
#[derive(Debug, Clone)]
pub struct MerkleTree {
    /// Chronological entries [0] = genesis, [n] = latest
    pub entries: Vec<GenesisEntry>,
    /// Merkle tree nodes (bottom row = leaf hashes)
    pub nodes: Vec<Vec<Hash>>,
    /// Root hash (top of tree)
    pub root: Option<Hash>,
}

impl MerkleTree {
    pub fn new() -> Self {
        MerkleTree {
            entries: Vec::new(),
            nodes: Vec::new(),
            root: None,
        }
    }

    /// Append entry + rebuild Merkle tree
    pub fn append(&mut self, data: Vec<u8>) -> Hash {
        let parent_hash = if self.entries.is_empty() {
            Hash::new([0u8; 32])  // Genesis root
        } else {
            self.entries.last().unwrap().hash
        };

        let seq = self.entries.len() as u64;
        let entry = GenesisEntry::new(seq, data, parent_hash);
        let hash = entry.hash;

        self.entries.push(entry);
        self.rebuild_tree();

        hash
    }

    /// Rebuild Merkle tree from entries
    fn rebuild_tree(&mut self) {
        if self.entries.is_empty() {
            self.root = None;
            self.nodes.clear();
            return;
        }

        // Build leaf hashes (level 0)
        let mut level: Vec<Hash> = self.entries.iter().map(|e| e.hash).collect();
        self.nodes.clear();
        self.nodes.push(level.clone());

        // Build tree bottom-up
        while level.len() > 1 {
            let mut next_level = Vec::new();
            for i in (0..level.len()).step_by(2) {
                let left = level[i];
                let right = if i + 1 < level.len() {
                    level[i + 1]
                } else {
                    left  // Duplicate if odd
                };
                next_level.push(Hash::combine(left, right));
            }
            self.nodes.push(next_level.clone());
            level = next_level;
        }

        self.root = if level.len() == 1 {
            Some(level[0])
        } else {
            None
        };
    }

    /// Verify entry membership in tree
    pub fn verify_entry(&self, seq: u64, expected_hash: Hash) -> bool {
        if seq >= self.entries.len() as u64 {
            return false;
        }

        let entry = &self.entries[seq as usize];
        entry.hash == expected_hash
    }

    /// Generate Merkle proof for entry (path from leaf to root)
    pub fn proof(&self, seq: u64) -> Vec<Hash> {
        let mut proof = Vec::new();

        if seq >= self.entries.len() as u64 || self.nodes.is_empty() {
            return proof;
        }

        let mut idx = seq as usize;
        for level in 0..self.nodes.len() - 1 {
            let sibling_idx = if idx % 2 == 0 { idx + 1 } else { idx - 1 };

            if sibling_idx < self.nodes[level].len() {
                proof.push(self.nodes[level][sibling_idx]);
            }

            idx /= 2;
        }

        proof
    }

    /// Verify Merkle proof
    pub fn verify_proof(&self, seq: u64, entry_hash: Hash, proof: &[Hash]) -> bool {
        if self.root.is_none() {
            return false;
        }

        let mut current = entry_hash;
        let mut idx = seq as usize;

        for proof_hash in proof {
            let left = if idx % 2 == 0 { current } else { *proof_hash };
            let right = if idx % 2 == 0 { *proof_hash } else { current };

            current = Hash::combine(left, right);
            idx /= 2;
        }

        current == self.root.unwrap()
    }
}

impl Default for MerkleTree {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_hash_creation() {
        let hash = Hash::new([42u8; 32]);
        assert_eq!(hash.as_bytes()[0], 42);
    }

    #[test]
    fn test_hash_combine() {
        let h1 = Hash::new([1u8; 32]);
        let h2 = Hash::new([2u8; 32]);
        let combined = Hash::combine(h1, h2);
        assert_eq!(combined.as_bytes()[0], 3);  // 1 XOR 2
    }

    #[test]
    fn test_genesis_entry() {
        let parent = Hash::new([0u8; 32]);
        let entry = GenesisEntry::new(0, vec![1, 2, 3], parent);
        assert_eq!(entry.seq, 0);
        assert_eq!(entry.data, vec![1, 2, 3]);
    }

    #[test]
    fn test_merkle_tree_single_entry() {
        let mut tree = MerkleTree::new();
        let hash1 = tree.append(vec![1, 2, 3]);

        assert_eq!(tree.entries.len(), 1);
        assert_eq!(tree.root, Some(hash1));
    }

    #[test]
    fn test_merkle_tree_multiple_entries() {
        let mut tree = MerkleTree::new();
        let hash1 = tree.append(vec![1]);
        let hash2 = tree.append(vec![2]);
        let hash3 = tree.append(vec![3]);

        assert_eq!(tree.entries.len(), 3);
        assert!(tree.root.is_some());

        // Verify order
        assert_eq!(tree.entries[0].hash, hash1);
        assert_eq!(tree.entries[1].hash, hash2);
        assert_eq!(tree.entries[2].hash, hash3);
    }

    #[test]
    fn test_merkle_verify_entry() {
        let mut tree = MerkleTree::new();
        let hash1 = tree.append(vec![1, 2, 3]);

        assert!(tree.verify_entry(0, hash1));
        assert!(!tree.verify_entry(0, Hash::new([99u8; 32])));
        assert!(!tree.verify_entry(999, hash1));
    }

    #[test]
    fn test_merkle_proof() {
        let mut tree = MerkleTree::new();
        tree.append(vec![1]);
        tree.append(vec![2]);
        tree.append(vec![3]);
        tree.append(vec![4]);

        let proof = tree.proof(0);
        assert!(!proof.is_empty());
    }

    #[test]
    fn test_merkle_verify_proof() {
        let mut tree = MerkleTree::new();
        let hash1 = tree.append(vec![1]);
        tree.append(vec![2]);
        tree.append(vec![3]);

        let proof = tree.proof(0);
        assert!(tree.verify_proof(0, hash1, &proof));
    }

    #[test]
    fn test_gate_criteria_deterministic() {
        // Gate Criteria: Merkle tree roots deterministic
        let mut tree1 = MerkleTree::new();
        tree1.append(vec![1, 2, 3]);
        tree1.append(vec![4, 5, 6]);

        let mut tree2 = MerkleTree::new();
        tree2.append(vec![1, 2, 3]);
        tree2.append(vec![4, 5, 6]);

        assert_eq!(tree1.root, tree2.root, "Same entries should produce same root");

        println!("Gate Criteria P1-4: Merkle trees deterministic");
    }
}

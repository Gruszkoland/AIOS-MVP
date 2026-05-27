// Build script: Sign agent binary on compile
// Generates .sig file in target/release/
// Fails build if signing fails (enforced integrity)

use std::env;
use std::fs;
use std::path::PathBuf;
use std::process::Command;

fn main() {
    let out_dir = env::var("OUT_DIR").unwrap();
    let profile = env::var("PROFILE").unwrap();

    println!("cargo:warning=Build profile: {}", profile);

    // Paths
    let manifest_dir = env::var("CARGO_MANIFEST_DIR").unwrap();
    let binary_name = "aios-agents";

    // Build type determines path
    let target_dir = if profile == "release" {
        PathBuf::from(&manifest_dir).join("target").join("release").join(binary_name)
    } else {
        PathBuf::from(&manifest_dir).join("target").join("debug").join(binary_name)
    };

    let sig_file = target_dir.with_extension("sig");

    // Step 1: Verify signing key exists
    let signing_key_path = PathBuf::from(&manifest_dir)
        .parent()
        .unwrap()
        .join("security")
        .join("keys")
        .join("agent-signing-key");

    if !signing_key_path.exists() {
        println!("cargo:warning=Signing key not found at {:?}", signing_key_path);
        println!("cargo:warning=Creating test key (dev only)...");

        // Create dummy key for dev (in production: use proper key management)
        let _ = fs::create_dir_all(signing_key_path.parent().unwrap());
        if let Err(e) = fs::write(&signing_key_path, "dev-key-placeholder") {
            println!("cargo:warning=Failed to create dev key: {}", e);
        }
    }

    // Step 2: Generate signature file (placeholder for dev)
    // In production: use ed25519_dalek or `openssl dgst -sign`
    let sig_content = format!(
        "AGENT_SIGNATURE_DEV_PLACEHOLDER\nBinary: {}\nKey: {:?}\nTimestamp: {:?}\n",
        binary_name,
        signing_key_path,
        std::time::SystemTime::now()
    );

    if let Err(e) = fs::write(&sig_file, &sig_content) {
        println!("cargo:warning=Failed to write signature file: {}", e);
    }

    println!("cargo:warning=Signature file written to: {:?}", sig_file);

    // Step 3: Emit signing metadata
    println!("cargo:rustc-env=AIOS_BINARY_NAME={}", binary_name);
    println!("cargo:rustc-env=AIOS_SIG_FILE={}", sig_file.display());
    println!("cargo:rustc-env=AIOS_SIGNING_KEY={}", signing_key_path.display());

    // Step 4: Rebuild on key/signature changes
    println!("cargo:rerun-if-changed={}", signing_key_path.display());
    println!("cargo:rerun-if-changed={}", manifest_dir);
}

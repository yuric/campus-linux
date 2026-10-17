//! Separate, root-provisioned fixture verifier. Never installed by the candidate deb.
//! The adapter supplies only its own root-staged files and root-owned public key.
use base64::Engine;
use minisign_verify::{PublicKey, Signature};
use std::{error::Error, fs, path::Path};

type Result<T> = std::result::Result<T, Box<dyn Error>>;

fn bounded_text(path: &Path) -> Result<String> {
    if fs::metadata(path)?.len() > 8192 {
        return Err("public key/signature exceeds fixture bound".into());
    }
    let encoded = fs::read_to_string(path)?;
    let decoded = base64::engine::general_purpose::STANDARD.decode(encoded.trim())?;
    Ok(String::from_utf8(decoded)?)
}

fn verify() -> Result<()> {
    let args: Vec<_> = std::env::args_os().skip(1).collect();
    if args.len() != 3 {
        return Err("usage: verify-signature <public-key> <package> <signature>".into());
    }
    let key = PublicKey::decode(&bounded_text(Path::new(&args[0]))?)?;
    let signature = Signature::decode(&bounded_text(Path::new(&args[2]))?)?;
    let package = fs::read(&args[1])?;
    // Same pinned minisign verifier and legacy-signature policy as updater 2.14.0.
    // The global signature authenticates the trusted comment before we read it.
    key.verify(&package, &signature, true)?;
    let versions: Vec<_> = signature.trusted_comment().split('\t')
        .filter_map(|field| field.strip_prefix("version:")).collect();
    if versions.len() != 1 {
        return Err("signature must authenticate exactly one fixture version".into());
    }
    let version = semver::Version::parse(versions[0])?;
    if version.to_string() != versions[0] || !version.pre.is_empty() || !version.build.is_empty() {
        return Err("signature version is not a canonical fixture release".into());
    }
    println!("{}", serde_json::json!({"version": version.to_string()}));
    Ok(())
}

fn main() {
    if let Err(error) = verify() {
        eprintln!("signature verification refused: {error}");
        std::process::exit(1);
    }
}

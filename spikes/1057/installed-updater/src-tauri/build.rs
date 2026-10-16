fn main() {
    println!("cargo:rerun-if-env-changed=SPIKE_UPDATER_PUBLIC_KEY");
    println!("cargo:rerun-if-env-changed=SPIKE_FIXTURE_BEHAVIOR");
    // These are public fixture identities, never signing secrets.
    for name in ["SPIKE_UPDATER_PUBLIC_KEY", "SPIKE_FIXTURE_BEHAVIOR"] {
        let value = std::env::var(name).expect("hosted fixture build must supply public key and behavior");
        assert!(!value.contains('\r') && !value.contains('\n'), "fixture build identity must be a single line");
        println!("cargo:rustc-env={name}={value}");
    }
    tauri_build::build();
}

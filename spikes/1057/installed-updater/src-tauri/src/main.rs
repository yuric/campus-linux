//! Card 1057 only: static Tauri fixture, installed artifact diagnostics and updater.
//! No Campus API, credentials, renderer, provider or executor implementation.
use serde::Serialize;
use serde_json::{json, Value};
use sha2::{Digest, Sha256};
use std::{error::Error, fs, io::{Read, Write}, path::{Path, PathBuf}, process::{Command, Stdio}, time::Duration};
use tauri::utils::{config::BundleType, platform::bundle_type};
use tauri_plugin_updater::UpdaterExt;
use url::Url;

type Result<T> = std::result::Result<T, Box<dyn Error + Send + Sync>>;
const PACKAGE: &str = "campus-updater-1057";
const VERSION: &str = env!("CARGO_PKG_VERSION");
const BEHAVIOR: &str = env!("SPIKE_FIXTURE_BEHAVIOR");
const PUBLIC_KEY: &str = env!("SPIKE_UPDATER_PUBLIC_KEY");
const ADAPTER: &str = "/usr/lib/campus-updater-1057/install-deb.py";

#[derive(Clone, Copy, PartialEq, Eq, Serialize)]
#[serde(rename_all = "lowercase")]
enum Format { Deb, Appimage }

impl Format {
    fn name(self) -> &'static str { match self { Self::Deb => "deb", Self::Appimage => "appimage" } }
}

#[derive(Serialize)]
struct Installed {
    event: &'static str,
    format: Format,
    architecture: &'static str,
    exact_target: String,
    version: &'static str,
    behavior: &'static str,
    executable: PathBuf,
    app_sha256: String,
    outer_artifact: Option<PathBuf>,
    outer_sha256: Option<String>,
    helper_path: PathBuf,
    helper_sha256: String,
    installation_evidence: String,
}

fn hash_file(path: &Path) -> Result<String> {
    let mut file = fs::File::open(path)?;
    let mut hash = Sha256::new();
    let mut buffer = [0u8; 65536];
    loop {
        let read = file.read(&mut buffer)?;
        if read == 0 { break; }
        hash.update(&buffer[..read]);
    }
    Ok(format!("{:x}", hash.finalize()))
}

fn architecture() -> Result<(&'static str, &'static str)> {
    if cfg!(all(target_os = "linux", target_arch = "aarch64")) { Ok(("aarch64", "arm64")) }
    else if cfg!(all(target_os = "linux", target_arch = "x86_64")) { Ok(("x86_64", "amd64")) }
    else { Err("fixture supports only native Linux arm64 and x86_64".into()) }
}

fn mount_unescape(value: &str) -> String {
    value.replace("\\040", " ").replace("\\011", "\t").replace("\\012", "\n").replace("\\134", "\\")
}

fn installed() -> Result<Installed> {
    let (architecture, deb_architecture) = architecture()?;
    let executable = std::env::current_exe()?.canonicalize()?;
    let (format, outer_artifact, helper_path, installation_evidence) = match bundle_type() {
        Some(BundleType::Deb) => {
            if executable != Path::new("/usr/bin/campus-updater-1057") {
                return Err("deb payload is not running from its installed path".into());
            }
            let output = Command::new("/usr/bin/dpkg-query")
                .args(["-W", "-f=${Status}\t${Version}\t${Architecture}", PACKAGE]).output()?;
            let status = String::from_utf8(output.stdout)?;
            if !output.status.success() || status != format!("install ok installed\t{VERSION}\t{deb_architecture}") {
                return Err("dpkg installed identity does not match the running fixture".into());
            }
            (Format::Deb, None, PathBuf::from("/usr/lib/campus-updater-1057/inert-helper.txt"), status)
        }
        Some(BundleType::AppImage) => {
            // APPIMAGE alone is not proof: require the bundled marker, type-2 runtime
            // header and a real mounted AppDir containing this process executable.
            let outer = PathBuf::from(std::env::var_os("APPIMAGE").ok_or("runtime did not supply APPIMAGE")?).canonicalize()?;
            let appdir = PathBuf::from(std::env::var_os("APPDIR").ok_or("runtime did not supply APPDIR")?).canonicalize()?;
            if !executable.starts_with(&appdir) || outer.starts_with(&appdir) {
                return Err("AppImage runtime paths do not identify this mounted executable".into());
            }
            let mut header = [0u8; 11];
            fs::File::open(&outer)?.read_exact(&mut header)?;
            if &header[..4] != b"\x7fELF" || &header[8..11] != b"AI\x02" {
                return Err("outer artifact is not a type-2 AppImage".into());
            }
            let mountinfo = fs::read_to_string("/proc/self/mountinfo")?;
            let mount = mountinfo.lines().find(|line| {
                let Some((before, after)) = line.split_once(" - ") else { return false; };
                let fields: Vec<_> = before.split_whitespace().collect();
                fields.len() >= 6 && Path::new(&mount_unescape(fields[4])) == appdir
                    && after.split_whitespace().next().is_some_and(|kind| kind.starts_with("fuse"))
                    && fields[5].split(',').any(|option| option == "ro")
            }).ok_or("AppDir is not an observed read-only FUSE mount; extracted payloads do not count")?;
            (Format::Appimage, Some(outer), appdir.join("usr/lib/campus-updater-1057/inert-helper.txt"), mount.to_string())
        }
        _ => return Err("no supported bundler-installed format marker".into()),
    };
    Ok(Installed {
        event: "installed_identity", format, architecture,
        exact_target: format!("linux-{architecture}-{}", format.name()),
        version: VERSION, behavior: BEHAVIOR,
        app_sha256: hash_file(&executable)?, executable,
        outer_sha256: outer_artifact.as_ref().map(|path| hash_file(path)).transpose()?, outer_artifact,
        helper_sha256: hash_file(&helper_path)?, helper_path, installation_evidence,
    })
}

fn emit(value: impl Serialize) -> Result<()> {
    println!("{}", serde_json::to_string(&value)?);
    std::io::stdout().flush()?;
    Ok(())
}

fn loopback_url(raw: &str) -> Result<Url> {
    let url = Url::parse(raw)?;
    if url.scheme() != "http" || url.host_str() != Some("127.0.0.1")
        || !url.username().is_empty() || url.password().is_some() || url.fragment().is_some() {
        return Err("disposable transport is limited to literal http://127.0.0.1 URLs".into());
    }
    Ok(url)
}

fn exact_static_entry(update: &tauri_plugin_updater::Update, target: &str) -> Result<()> {
    // Upstream dynamic manifests ignore target, so refuse them independently.
    let entry = update.raw_json.get("platforms").and_then(Value::as_object)
        .and_then(|platforms| platforms.get(target)).ok_or("exact static manifest entry is missing")?;
    if update.raw_json.get("url").is_some() || update.raw_json.get("signature").is_some()
        || entry.get("url").and_then(Value::as_str) != Some(update.download_url.as_str())
        || entry.get("signature").and_then(Value::as_str) != Some(update.signature.as_str()) {
        return Err("manifest is not the exact static fixture target".into());
    }
    loopback_url(update.download_url.as_str())?;
    Ok(())
}

fn private_write(path: &Path, bytes: &[u8]) -> Result<()> {
    use std::os::unix::fs::OpenOptionsExt;
    let mut file = fs::OpenOptions::new().write(true).create_new(true).mode(0o600).open(path)?;
    file.write_all(bytes)?;
    file.sync_all()?;
    Ok(())
}

fn appimage_payload(bytes: &[u8], architecture: &str) -> Result<()> {
    // Native little-endian ELF64 type-2 runtime; this fixture never accepts an
    // archive or a signed image for another architecture at the replacement seam.
    let machine: u16 = match architecture {
        "aarch64" => 183,
        "x86_64" => 62,
        _ => return Err("unsupported installed architecture".into()),
    };
    if bytes.len() < 64 || &bytes[..4] != b"\x7fELF" || bytes[4] != 2
        || bytes[5] != 1 || &bytes[8..11] != b"AI\x02"
        || u16::from_le_bytes([bytes[18], bytes[19]]) != machine {
        return Err("signed payload is not a native type-2 AppImage".into());
    }
    Ok(())
}

async fn update(app: tauri::AppHandle, operation: String, endpoint: String) -> Result<()> {
    let before = installed()?;
    emit(&before)?;
    let updater = app.updater_builder().pubkey(PUBLIC_KEY)
        .target(&before.exact_target)
        .executable_path(before.outer_artifact.as_ref().unwrap_or(&before.executable))
        .endpoints(vec![loopback_url(&endpoint)?])?
        .timeout(Duration::from_secs(90)).no_proxy()
        // This fixture permits HTTP only to its local receipt server and refuses redirects.
        .configure_client(|client| client.redirect(reqwest::redirect::Policy::none()))
        .build()?;
    let Some(mut update) = updater.check().await? else {
        emit(json!({"event":"no_newer_release", "exact_target":before.exact_target, "version":VERSION}))?;
        return Ok(());
    };
    exact_static_entry(&update, &before.exact_target)?;
    update.timeout = Some(Duration::from_secs(180));
    emit(json!({"event":"selected", "exact_target":before.exact_target, "version":update.version, "url":update.download_url}))?;
    if operation == "--check" { return Ok(()); }
    let bytes = update.download(|_, _| {}, || {}).await?;
    let download_sha256 = format!("{:x}", Sha256::digest(&bytes));
    emit(json!({"event":"verified_download", "bytes":bytes.len(), "sha256":download_sha256, "version":update.version}))?;
    if operation == "--download" { return Ok(()); }
    match before.format {
        Format::Deb => {
            let staging = tempfile::Builder::new().prefix("campus-updater-1057-").tempdir()?;
            let package = staging.path().join("package.deb");
            let signature = staging.path().join("package.sig");
            private_write(&package, &bytes)?;
            private_write(&signature, update.signature.as_bytes())?;
            // Never call Update::install for a deb. The independently provisioned
            // adapter verifies the root-staged bytes, key, version and fixture schema.
            let result = Command::new("/usr/bin/pkexec")
                .args(["--disable-internal-agent", ADAPTER]).arg(&package).arg(&signature)
                .stdin(Stdio::null()).output()?;
            emit(json!({"event":"polkit_adapter_result", "success":result.status.success(),
                "exit_status":result.status.code(), "stdout":String::from_utf8_lossy(&result.stdout),
                "stderr":String::from_utf8_lossy(&result.stderr)}))?;
            if !result.status.success() {
                let app_unchanged = hash_file(&before.executable)? == before.app_sha256;
                let helper_unchanged = hash_file(&before.helper_path)? == before.helper_sha256;
                emit(json!({"event":"refusal_bytes", "app_unchanged":app_unchanged, "helper_unchanged":helper_unchanged}))?;
                return Err("polkit adapter did not install the fixture; inspect its receipt".into());
            }
            emit(json!({"event":"deb_adapter_completed", "requested_version":update.version}))?;
        }
        Format::Appimage => {
            // This is the only call into stock Tauri installation. The locally
            // observed marker selected AppImage, never a manifest-provided format.
            appimage_payload(&bytes, before.architecture)?;
            update.install(&bytes)?;
            let outer = before.outer_artifact.as_ref().ok_or("missing outer AppImage")?;
            let installed_sha256 = hash_file(outer)?;
            if installed_sha256 != download_sha256 { return Err("AppImage replacement bytes differ from signed download".into()); }
            emit(json!({"event":"appimage_replaced", "sha256":installed_sha256, "version":update.version}))?;
            let child = Command::new(outer).arg("--diagnose")
                .env_remove("APPIMAGE").env_remove("APPDIR").env_remove("ARGV0")
                .env_remove("LD_LIBRARY_PATH").env_remove("LD_PRELOAD")
                .stdin(Stdio::null()).output()?;
            if !child.status.success() {
                emit(json!({"event":"relaunch_failed", "exit_status":child.status.code(), "stderr":String::from_utf8_lossy(&child.stderr)}))?;
                return Err("replacement AppImage diagnostic relaunch failed".into());
            }
            let identity: Value = serde_json::from_slice(&child.stdout)?;
            if identity["version"] != update.version || identity["exact_target"] != before.exact_target
                || identity["outer_sha256"] != installed_sha256 {
                return Err("relaunch identity differs from the installed signed release".into());
            }
            emit(json!({"event":"appimage_relaunched", "identity":identity}))?;
        }
    }
    Ok(())
}

fn main() {
    let args: Vec<_> = std::env::args().skip(1).collect();
    if args == ["--diagnose"] {
        if let Err(error) = installed().and_then(emit) { fail(error); }
        return;
    }
    if !args.is_empty() && (args.len() != 2 || !["--check", "--download", "--update"].contains(&args[0].as_str())) {
        fail("usage: campus-updater-1057 [--diagnose | --check URL | --download URL | --update URL]".into());
    }
    let command = if args.is_empty() { None } else { Some((args[0].clone(), args[1].clone())) };
    let builder = tauri::Builder::default().plugin(tauri_plugin_updater::Builder::new().build())
        .setup(move |app| {
            if let Some((operation, endpoint)) = command {
                let handle = app.handle().clone();
                tauri::async_runtime::spawn(async move {
                    let exit_handle = handle.clone();
                    let result = update(handle, operation, endpoint).await;
                    let status = match result {
                        Ok(()) => 0,
                        Err(error) => { let _ = emit(json!({"event":"refused", "error":error.to_string()})); 1 }
                    };
                    exit_handle.exit(status);
                });
            } else {
                tauri::WebviewWindowBuilder::new(app, "main", tauri::WebviewUrl::App("index.html".into()))
                    .title("Disposable updater · 1057").inner_size(720.0, 480.0).build()?;
            }
            Ok(())
        });
    if let Err(error) = builder.run(tauri::generate_context!()) { fail(error.into()); }
}

fn fail(error: Box<dyn Error + Send + Sync>) -> ! {
    let _ = emit(json!({"event":"refused", "error":error.to_string()}));
    std::process::exit(1)
}

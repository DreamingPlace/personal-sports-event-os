#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]
use std::{io::{BufRead, BufReader, Write}, process::{Child, ChildStdin, Command, Stdio}, sync::{mpsc, Arc, Mutex, atomic::{AtomicU64, Ordering}}, time::Duration};
use serde_json::{json, Value};
use tauri::Manager;

struct Sidecar { child: Child, input: ChildStdin, output: mpsc::Receiver<String> }
impl Drop for Sidecar { fn drop(&mut self) { let _=self.child.kill(); let _=self.child.wait(); } }
#[derive(Clone)]
struct Bridge { process: Arc<Mutex<Option<Sidecar>>>, sequence: Arc<AtomicU64> }
fn error(code: &str, message: String) -> Value { json!({"id":null,"ok":false,"error":{"code":code,"message":message,"details":{}}}) }
fn spawn_sidecar() -> Result<Sidecar,String> {
    let path=if cfg!(debug_assertions) {
        std::path::PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("binaries/sports-os-sidecar-aarch64-apple-darwin")
    } else { std::env::current_exe().map_err(|e|e.to_string())?.with_file_name("sports-os-sidecar") };
    let mut child=Command::new(path).stdin(Stdio::piped()).stdout(Stdio::piped()).stderr(Stdio::inherit()).spawn().map_err(|e|e.to_string())?;
    let input=child.stdin.take().ok_or("Missing sidecar stdin")?;
    let output=child.stdout.take().ok_or("Missing sidecar stdout")?;
    let (tx,rx)=mpsc::channel();
    std::thread::spawn(move || { for line in BufReader::new(output).lines() { match line {Ok(s)=>{if tx.send(s).is_err(){break}},Err(_)=>break} } });
    Ok(Sidecar{child,input,output:rx})
}
impl Bridge {
    fn call(&self, method:String, params:Value) -> Value {
        let mut guard=match self.process.lock(){Ok(g)=>g,Err(e)=>return error("SIDECAR",e.to_string())};
        if guard.is_none() { match spawn_sidecar(){Ok(p)=>*guard=Some(p),Err(e)=>return error("SIDECAR",e)} }
        let id=format!("{}-{}",std::process::id(),self.sequence.fetch_add(1,Ordering::SeqCst));
        let request=json!({"id":id,"method":method,"params":params});
        let process=guard.as_mut().unwrap();
        let result=(|| -> Result<Value,String> {
            writeln!(process.input,"{}",request).map_err(|e|e.to_string())?;
            process.input.flush().map_err(|e|e.to_string())?;
            let line=process.output.recv_timeout(Duration::from_secs(60)).map_err(|e|format!("Sidecar stopped or timed out: {e}"))?;
            let response:Value=serde_json::from_str(&line).map_err(|e|format!("Invalid sidecar protocol: {e}"))?;
            if response["id"]!=id{return Err("Response ID mismatch".into())}
            Ok(response)
        })();
        match result { Ok(v)=>v,Err(e)=>{*guard=None;error("SIDECAR",e)} }
    }
}
#[tauri::command]
async fn sports_call(method:String,params:Value,bridge:tauri::State<'_,Bridge>) -> Result<Value,String> {
    let bridge=bridge.inner().clone();
    tauri::async_runtime::spawn_blocking(move || bridge.call(method,params)).await.map_err(|e|e.to_string())
}
fn main() {
    tauri::Builder::default().plugin(tauri_plugin_dialog::init())
        .manage(Bridge{process:Arc::new(Mutex::new(None)),sequence:Arc::new(AtomicU64::new(1))})
        .invoke_handler(tauri::generate_handler![sports_call])
        .build(tauri::generate_context!()).expect("Unable to build Sports Event OS")
        .run(|app,event|{if let tauri::RunEvent::Exit=event {if let Ok(mut state)=app.state::<Bridge>().process.lock(){*state=None;}}});
}

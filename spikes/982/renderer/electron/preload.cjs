/* Disposable presentation/receipt bridge only; no arbitrary IPC or Node exposure. */
const {contextBridge,ipcRenderer}=require('electron');
contextBridge.exposeInMainWorld('webkit',{messageHandlers:{
  campusIslandAPI:{postMessage:value=>ipcRenderer.invoke('spike-presentation',value)},
  spikeReceipt:{postMessage:value=>ipcRenderer.send('spike-receipt',value)}
}});

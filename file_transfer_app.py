import os
import socket
import threading
from flask import Flask, request, jsonify, send_file
import tkinter as tk
from tkinter import scrolledtext, filedialog, messagebox
from datetime import datetime

app = Flask(__name__)

# Configuration
DOWNLOAD_FOLDER = os.path.join(os.getcwd(), 'downloads')
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Global variables
log_widget = None
server_thread = None
server_running = False

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

def log_message(message):
    timestamp = datetime.now().strftime("%H:%M:%S")
    log_text = f"[{timestamp}] {message}\n"
    if log_widget:
        log_widget.insert(tk.END, log_text)
        log_widget.see(tk.END)

# Flask Routes
@app.route('/')
def index():
    html = """<!DOCTYPE html>
<html>
<head>
    <title>File Transfer</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 10px;
        }
        .container {
            max-width: 600px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
            overflow: hidden;
        }
        .header {
            background: #4a5568;
            color: white;
            padding: 20px;
            text-align: center;
        }
        .header h1 {
            font-size: clamp(20px, 5vw, 26px);
            margin-bottom: 5px;
        }
        .header p {
            font-size: clamp(12px, 3vw, 14px);
            opacity: 0.9;
        }
        .content { padding: 20px; }
        .section {
            margin-bottom: 25px;
            border: 2px solid #e2e8f0;
            border-radius: 8px;
            padding: 20px;
            background: #f8fafc;
        }
        .section-title {
            color: #2d3748;
            font-size: clamp(16px, 4vw, 18px);
            margin-bottom: 15px;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .direction-badge {
            font-size: clamp(10px, 2.5vw, 12px);
            padding: 4px 8px;
            border-radius: 4px;
            background: #edf2f7;
            color: #4a5568;
            font-weight: normal;
        }
        input[type="file"] {
            width: 100%;
            padding: 10px;
            font-size: clamp(14px, 3.5vw, 16px);
            border: 1px solid #cbd5e0;
            border-radius: 6px;
            margin-bottom: 12px;
            background: white;
        }
        button {
            width: 100%;
            padding: 14px 20px;
            font-size: clamp(14px, 3.5vw, 16px);
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-weight: 600;
            transition: all 0.3s ease;
            min-height: 44px;
        }
        .upload-btn {
            background: #48bb78;
            color: white;
        }
        .upload-btn:hover { background: #38a169; }
        .upload-btn:disabled {
            background: #cbd5e0;
            cursor: not-allowed;
        }
        .download-btn {
            background: #4299e1;
            color: white;
            margin-top: 8px;
        }
        .download-btn:hover { background: #3182ce; }
        .refresh-btn {
            background: #ed8936;
            color: white;
            margin-bottom: 12px;
        }
        .refresh-btn:hover { background: #dd6b20; }
        .file-info {
            background: #e6fffa;
            padding: 12px;
            margin: 12px 0;
            border-radius: 6px;
            border: 1px solid #81e6d9;
            display: none;
            font-size: clamp(12px, 3vw, 14px);
        }
        .file-info.show { display: block; }
        .file-item {
            padding: 8px 0;
            border-bottom: 1px solid #e2e8f0;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
        }
        .file-item:last-child { border-bottom: none; }
        .file-name {
            font-weight: bold;
            word-break: break-word;
            flex: 1;
            min-width: 120px;
            margin-right: 10px;
        }
        .file-size {
            color: #718096;
            font-size: clamp(11px, 2.5vw, 12px);
            white-space: nowrap;
        }
        .message {
            padding: 12px 16px;
            margin: 15px 0;
            border-radius: 6px;
            font-size: clamp(13px, 3vw, 14px);
            text-align: center;
            display: none;
            font-weight: 500;
        }
        .message.success {
            background: #c6f6d5;
            color: #22543d;
            border: 1px solid #9ae6b4;
        }
        .message.error {
            background: #fed7d7;
            color: #742a2a;
            border: 1px solid #fc8181;
        }
        .message.show { display: block; }
        .progress-container {
            margin: 15px 0;
            display: none;
        }
        .progress-container.show { display: block; }
        .progress-bar-bg {
            width: 100%;
            background: #e2e8f0;
            border-radius: 10px;
            overflow: hidden;
            height: 28px;
            position: relative;
            margin-bottom: 10px;
        }
        .progress-bar {
            height: 100%;
            background: linear-gradient(90deg, #48bb78, #38a169);
            width: 0%;
            transition: width 0.3s ease;
            position: relative;
        }
        .progress-text {
            position: absolute;
            width: 100%;
            top: 50%;
            left: 0;
            transform: translateY(-50%);
            text-align: center;
            color: #2d3748;
            font-weight: bold;
            font-size: clamp(11px, 2.8vw, 13px);
            z-index: 1;
        }
        .progress-info {
            display: flex;
            justify-content: space-between;
            font-size: clamp(11px, 2.5vw, 12px);
            color: #718096;
            flex-wrap: wrap;
            gap: 10px;
        }
        .available-files {
            max-height: 300px;
            overflow-y: auto;
            border: 1px solid #e2e8f0;
            border-radius: 6px;
            background: white;
        }
        .available-file {
            padding: 12px;
            border-bottom: 1px solid #e2e8f0;
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 10px;
        }
        .available-file:last-child { border-bottom: none; }
        .available-file:hover { background: #f7fafc; }
        .no-files {
            padding: 20px;
            text-align: center;
            color: #a0aec0;
            font-style: italic;
        }
        @media screen and (max-width: 480px) {
            body { padding: 5px; }
            .container { border-radius: 8px; }
            .content { padding: 15px; }
            .section { padding: 15px; }
            .progress-info { flex-direction: column; gap: 5px; }
        }
        @media screen and (max-width: 320px) {
            .content { padding: 12px; }
            .section { padding: 12px; }
        }
        @media (pointer: coarse) {
            button { min-height: 48px; }
            input[type="file"] { min-height: 44px; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📱💻 File Transfer</h1>
            <p>Transfer files between devices</p>
        </div>
        <div class="content">
            <div id="message" class="message"></div>
            <div class="section">
                <div class="section-title">
                    📤 Send to Computer
                    <span class="direction-badge">Phone → Computer</span>
                </div>
                <form id="singleForm">
                    <input type="file" id="singleFile">
                    <div id="singleInfo" class="file-info"></div>
                    <button type="submit" class="upload-btn" disabled>Upload File</button>
                </form>
                <div style="margin-top: 20px;">
                    <form id="multiForm">
                        <input type="file" id="multiFiles" multiple>
                        <div id="multiInfo" class="file-info"></div>
                        <button type="submit" class="upload-btn" disabled>Upload Multiple Files</button>
                    </form>
                </div>
            </div>
            <div class="section">
                <div class="section-title">
                    📥 Get from Computer
                    <span class="direction-badge">Computer → Phone</span>
                </div>
                <button class="refresh-btn" id="refreshBtn">🔄 Refresh File List</button>
                <div id="availableFiles" class="available-files">
                    <div class="no-files">Loading files...</div>
                </div>
            </div>
            <div id="progressContainer" class="progress-container">
                <div class="progress-bar-bg">
                    <div id="progressBar" class="progress-bar"></div>
                    <div id="progressText" class="progress-text">0%</div>
                </div>
                <div class="progress-info">
                    <span id="progressSize">0 MB / 0 MB</span>
                    <span id="progressTime">Elapsed: 0s</span>
                    <span id="progressEta">ETA: --</span>
                </div>
            </div>
        </div>
    </div>
    <script>
        var uploadStartTime = 0;
        function formatFileSize(bytes) {
            if (bytes === 0) return '0 B';
            var k = 1024;
            var sizes = ['B', 'KB', 'MB', 'GB'];
            var i = Math.floor(Math.log(bytes) / Math.log(k));
            return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
        }
        function formatTime(seconds) {
            if (seconds < 60) return Math.round(seconds) + 's';
            var minutes = Math.floor(seconds / 60);
            var secs = Math.round(seconds % 60);
            return minutes + 'm ' + secs + 's';
        }
        function showMessage(text, type) {
            var message = document.getElementById('message');
            message.textContent = text;
            message.className = 'message ' + type + ' show';
            setTimeout(function() { message.classList.remove('show'); }, 5000);
        }
        document.getElementById('singleFile').addEventListener('change', function(e) {
            var file = e.target.files[0];
            var info = document.getElementById('singleInfo');
            var btn = document.querySelector('#singleForm button');
            if (file) {
                info.innerHTML = '<div class="file-item"><span class="file-name">' + file.name + '</span><span class="file-size">' + formatFileSize(file.size) + '</span></div>';
                info.classList.add('show');
                btn.disabled = false;
            } else {
                info.classList.remove('show');
                btn.disabled = true;
            }
        });
        document.getElementById('multiFiles').addEventListener('change', function(e) {
            var files = Array.from(e.target.files);
            var info = document.getElementById('multiInfo');
            var btn = document.querySelector('#multiForm button');
            if (files.length > 0) {
                var totalSize = files.reduce(function(sum, file) { return sum + file.size; }, 0);
                var html = '<strong>Total: ' + files.length + ' files (' + formatFileSize(totalSize) + ')</strong><br><br>';
                files.slice(0, 3).forEach(function(file) {
                    html += '<div class="file-item"><span class="file-name">' + file.name + '</span><span class="file-size">' + formatFileSize(file.size) + '</span></div>';
                });
                if (files.length > 3) {
                    html += '<div style="text-align: center; margin-top: 10px; color: #666;">...and ' + (files.length - 3) + ' more files</div>';
                }
                info.innerHTML = html;
                info.classList.add('show');
                btn.disabled = false;
            } else {
                info.classList.remove('show');
                btn.disabled = true;
            }
        });
        function uploadFiles(formData, fileCount) {
            var progressContainer = document.getElementById('progressContainer');
            var progressBar = document.getElementById('progressBar');
            var progressText = document.getElementById('progressText');
            var progressSize = document.getElementById('progressSize');
            var progressTime = document.getElementById('progressTime');
            var progressEta = document.getElementById('progressEta');
            progressContainer.classList.add('show');
            uploadStartTime = Date.now();
            var xhr = new XMLHttpRequest();
            xhr.upload.addEventListener('progress', function(e) {
                if (e.lengthComputable) {
                    var percent = Math.round((e.loaded / e.total) * 100);
                    var elapsed = (Date.now() - uploadStartTime) / 1000;
                    var speed = e.loaded / elapsed;
                    var remaining = (e.total - e.loaded) / speed;
                    progressBar.style.width = percent + '%';
                    progressText.textContent = percent + '%';
                    progressSize.textContent = formatFileSize(e.loaded) + ' / ' + formatFileSize(e.total);
                    progressTime.textContent = 'Elapsed: ' + formatTime(elapsed);
                    progressEta.textContent = remaining > 0 ? 'ETA: ' + formatTime(remaining) : 'ETA: --';
                }
            });
            xhr.addEventListener('load', function() {
                progressContainer.classList.remove('show');
                if (xhr.status === 200) {
                    showMessage(fileCount === 1 ? 'File uploaded successfully!' : fileCount + ' files uploaded successfully!', 'success');
                    document.getElementById('singleForm').reset();
                    document.getElementById('multiForm').reset();
                    document.getElementById('singleInfo').classList.remove('show');
                    document.getElementById('multiInfo').classList.remove('show');
                    document.querySelector('#singleForm button').disabled = true;
                    document.querySelector('#multiForm button').disabled = true;
                } else {
                    showMessage('Upload failed. Please try again.', 'error');
                }
            });
            xhr.addEventListener('error', function() {
                progressContainer.classList.remove('show');
                showMessage('Upload failed. Check your connection.', 'error');
            });
            xhr.open('POST', '/upload');
            xhr.send(formData);
        }
        document.getElementById('singleForm').addEventListener('submit', function(e) {
            e.preventDefault();
            var file = document.getElementById('singleFile').files[0];
            if (file) {
                var formData = new FormData();
                formData.append('files', file);
                uploadFiles(formData, 1);
            }
        });
        document.getElementById('multiForm').addEventListener('submit', function(e) {
            e.preventDefault();
            var files = document.getElementById('multiFiles').files;
            if (files.length > 0) {
                var formData = new FormData();
                for (var i = 0; i < files.length; i++) {
                    formData.append('files', files[i]);
                }
                uploadFiles(formData, files.length);
            }
        });
        function refreshFileList() {
            fetch('/list_files').then(function(response) {
                return response.json();
            }).then(function(data) {
                var container = document.getElementById('availableFiles');
                if (data.files.length === 0) {
                    container.innerHTML = '<div class="no-files">No files available for download</div>';
                } else {
                    var html = '';
                    data.files.forEach(function(file) {
                        html += '<div class="available-file"><div><div class="file-name">' + file.name + '</div><div class="file-size">' + formatFileSize(file.size) + '</div></div><button class="download-btn" data-filename="' + encodeURIComponent(file.name) + '">⬇️ Download</button></div>';
                    });
                    container.innerHTML = html;
                    var downloadButtons = container.querySelectorAll('.download-btn');
                    for (var i = 0; i < downloadButtons.length; i++) {
                        downloadButtons[i].addEventListener('click', function() {
                            var filename = this.getAttribute('data-filename');
                            window.location.href = '/download/' + filename;
                            showMessage('Downloading ' + decodeURIComponent(filename) + '...', 'success');
                        });
                    }
                }
            }).catch(function() {
                showMessage('Failed to load file list', 'error');
            });
        }
        document.getElementById('refreshBtn').addEventListener('click', refreshFileList);
        refreshFileList();
    </script>
</body>
</html>"""
    return html

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        files = request.files.getlist('files')
        if not files:
            return jsonify({'error': 'No files provided'}), 400
        
        for file in files:
            if file.filename:
                filepath = os.path.join(DOWNLOAD_FOLDER, file.filename)
                file.save(filepath)
                log_message(f"Received: {file.filename}")
        
        return jsonify({'success': True, 'count': len(files)}), 200
    except Exception as e:
        log_message(f"Upload error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/list_files', methods=['GET'])
def list_files():
    try:
        files = []
        for filename in os.listdir(UPLOAD_FOLDER):
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            if os.path.isfile(filepath):
                files.append({
                    'name': filename,
                    'size': os.path.getsize(filepath)
                })
        return jsonify({'files': files})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download/<filename>')
def download_file(filename):
    try:
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        log_message(f"Sent: {filename}")
        return send_file(filepath, as_attachment=True)
    except Exception as e:
        log_message(f"Download error: {str(e)}")
        return jsonify({'error': 'File not found'}), 404

# GUI Application
class FileTransferGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("File Transfer Server")
        self.root.geometry("600x500")
        
        title = tk.Label(root, text="📱💻 Bidirectional File Transfer", 
                        font=("Arial", 16, "bold"), pady=10)
        title.pack()
        
        control_frame = tk.Frame(root)
        control_frame.pack(pady=10, padx=20, fill=tk.X)
        
        self.start_button = tk.Button(control_frame, text="▶️ Start Server", 
                                      command=self.start_server, 
                                      bg="#4CAF50", fg="white", 
                                      font=("Arial", 12, "bold"), 
                                      padx=20, pady=10)
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_button = tk.Button(control_frame, text="⏹️ Stop Server", 
                                     command=self.stop_server, 
                                     bg="#f44336", fg="white", 
                                     font=("Arial", 12, "bold"), 
                                     padx=20, pady=10, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        self.upload_button = tk.Button(control_frame, text="📤 Add Files to Share", 
                                       command=self.select_files_to_share,
                                       bg="#2196F3", fg="white",
                                       font=("Arial", 12, "bold"),
                                       padx=20, pady=10)
        self.upload_button.pack(side=tk.LEFT, padx=5)
        
        status_frame = tk.LabelFrame(root, text="Server Status", 
                                    font=("Arial", 10, "bold"), padx=10, pady=10)
        status_frame.pack(pady=10, padx=20, fill=tk.BOTH)
        
        tk.Label(status_frame, text="Local:", font=("Arial", 10)).grid(row=0, column=0, sticky=tk.W)
        self.local_label = tk.Label(status_frame, text="Not running", 
                                    font=("Arial", 10, "bold"), fg="red")
        self.local_label.grid(row=0, column=1, sticky=tk.W, padx=10)
        
        tk.Label(status_frame, text="Network:", font=("Arial", 10)).grid(row=1, column=0, sticky=tk.W)
        self.network_label = tk.Label(status_frame, text="Not running", 
                                      font=("Arial", 10, "bold"), fg="red")
        self.network_label.grid(row=1, column=1, sticky=tk.W, padx=10)
        
        info_frame = tk.LabelFrame(root, text="Folder Locations", 
                                  font=("Arial", 10, "bold"), padx=10, pady=10)
        info_frame.pack(pady=10, padx=20, fill=tk.BOTH)
        
        tk.Label(info_frame, text="📥 Received files:", font=("Arial", 9)).grid(row=0, column=0, sticky=tk.W)
        tk.Label(info_frame, text=DOWNLOAD_FOLDER, font=("Arial", 9), fg="blue").grid(row=0, column=1, sticky=tk.W, padx=5)
        
        tk.Label(info_frame, text="📤 Shared files:", font=("Arial", 9)).grid(row=1, column=0, sticky=tk.W)
        tk.Label(info_frame, text=UPLOAD_FOLDER, font=("Arial", 9), fg="blue").grid(row=1, column=1, sticky=tk.W, padx=5)
        
        log_frame = tk.LabelFrame(root, text="Activity Log", 
                                 font=("Arial", 10, "bold"), padx=10, pady=10)
        log_frame.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)
        
        global log_widget
        log_widget = scrolledtext.ScrolledText(log_frame, height=10, 
                                               font=("Courier", 9))
        log_widget.pack(fill=tk.BOTH, expand=True)
        
        log_message("Application started")
        log_message(f"Received files folder: {DOWNLOAD_FOLDER}")
        log_message(f"Shared files folder: {UPLOAD_FOLDER}")
    
    def select_files_to_share(self):
        files = filedialog.askopenfilenames(title="Select files to share with phone")
        if files:
            count = 0
            for filepath in files:
                try:
                    filename = os.path.basename(filepath)
                    dest_path = os.path.join(UPLOAD_FOLDER, filename)
                    
                    import shutil
                    shutil.copy2(filepath, dest_path)
                    log_message(f"Added to share: {filename}")
                    count += 1
                except Exception as e:
                    log_message(f"Error adding {filename}: {str(e)}")
            
            if count > 0:
                messagebox.showinfo("Success", f"Added {count} file(s) to share folder")
    
    def start_server(self):
        global server_running, server_thread
        
        def run_server():
            app.run(host='0.0.0.0', port=8080, debug=False, use_reloader=False)
        
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        server_running = True
        
        local_ip = get_local_ip()
        self.local_label.config(text=f"http://localhost:8080", fg="green")
        self.network_label.config(text=f"http://{local_ip}:8080", fg="green")
        
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        
        log_message("Server started successfully")
        log_message(f"Local URL: http://localhost:8080")
        log_message(f"Network URL: http://{local_ip}:8080")
        log_message("Phone → Computer: Upload files from phone")
        log_message("Computer → Phone: Add files to share and download from phone")
    
    def stop_server(self):
        global server_running
        server_running = False
        
        self.local_label.config(text="Not running", fg="red")
        self.network_label.config(text="Not running", fg="red")
        
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        
        log_message("Server stopped")
        messagebox.showinfo("Info", "Please restart the application to start the server again")

if __name__ == "__main__":
    root = tk.Tk()
    app_gui = FileTransferGUI(root)
    root.mainloop()
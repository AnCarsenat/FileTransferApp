#!/usr/bin/env python3
"""
Phone File Transfer Desktop App
A desktop application that hosts a web server for receiving files from mobile devices
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import socket
import os
import sys
from flask import Flask, request, render_template_string, redirect, url_for, flash
from werkzeug.utils import secure_filename
import webbrowser
from datetime import datetime
import json

class FileTransferApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Phone File Transfer Server")
        self.root.geometry("600x500")
        self.root.resizable(True, True)
        
        # Server variables
        self.flask_app = None
        self.server_thread = None
        self.is_running = False
        self.port = 8080
        self.download_folder = os.path.join(os.getcwd(), "downloads")
        
        # Ensure download folder exists
        os.makedirs(self.download_folder, exist_ok=True)
        
        self.setup_ui()
        self.setup_flask_app()
        
    def setup_ui(self):
        """Setup the user interface"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(4, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="Phone File Transfer Server", 
                               font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # Server settings frame
        settings_frame = ttk.LabelFrame(main_frame, text="Server Settings", padding="10")
        settings_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        settings_frame.columnconfigure(1, weight=1)
        
        # Port setting
        ttk.Label(settings_frame, text="Port:").grid(row=0, column=0, sticky=tk.W)
        self.port_var = tk.StringVar(value=str(self.port))
        port_entry = ttk.Entry(settings_frame, textvariable=self.port_var, width=10)
        port_entry.grid(row=0, column=1, sticky=tk.W, padx=(5, 0))
        
        # Download folder setting
        ttk.Label(settings_frame, text="Download Folder:").grid(row=1, column=0, sticky=tk.W, pady=(5, 0))
        folder_frame = ttk.Frame(settings_frame)
        folder_frame.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=(5, 0))
        folder_frame.columnconfigure(0, weight=1)
        
        self.folder_var = tk.StringVar(value=self.download_folder)
        folder_entry = ttk.Entry(folder_frame, textvariable=self.folder_var, state='readonly')
        folder_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(5, 5))
        
        browse_btn = ttk.Button(folder_frame, text="Browse", command=self.browse_folder)
        browse_btn.grid(row=0, column=1)
        
        # Server control frame
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=2, column=0, columnspan=2, pady=10)
        
        self.start_btn = ttk.Button(control_frame, text="Start Server", command=self.start_server)
        self.start_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.stop_btn = ttk.Button(control_frame, text="Stop Server", command=self.stop_server, state='disabled')
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        self.open_browser_btn = ttk.Button(control_frame, text="Open in Browser", 
                                          command=self.open_browser, state='disabled')
        self.open_browser_btn.pack(side=tk.LEFT, padx=5)
        
        # Status frame
        status_frame = ttk.LabelFrame(main_frame, text="Server Status", padding="10")
        status_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        status_frame.columnconfigure(0, weight=1)
        
        self.status_label = ttk.Label(status_frame, text="Server is stopped", foreground="red")
        self.status_label.grid(row=0, column=0, sticky=tk.W)
        
        self.url_label = ttk.Label(status_frame, text="", foreground="blue", cursor="hand2")
        self.url_label.grid(row=1, column=0, sticky=tk.W)
        self.url_label.bind("<Button-1>", lambda e: self.open_browser())
        
        # Log frame
        log_frame = ttk.LabelFrame(main_frame, text="Activity Log", padding="10")
        log_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=10, state='disabled')
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        clear_log_btn = ttk.Button(log_frame, text="Clear Log", command=self.clear_log)
        clear_log_btn.grid(row=1, column=0, pady=(5, 0))
        
    def setup_flask_app(self):
        """Setup Flask application"""
        self.flask_app = Flask(__name__)
        self.flask_app.secret_key = 'file_transfer_secret_key'
        
        # Simple HTML template for older phones - no console, AJAX uploads with progress
        upload_template = '''
        <!DOCTYPE html>
<html>
<head>
    <title>File Upload</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 10px;
            background-color: #f0f0f0;
            min-height: 100vh;
            box-sizing: border-box;
        }
        
        * {
            box-sizing: border-box;
        }

        .container {
            max-width: 600px;
            margin: 0 auto;
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }

        h1 {
            color: #333;
            text-align: center;
            font-size: clamp(20px, 5vw, 24px);
            margin-bottom: 20px;
        }

        h2 {
            color: #555;
            font-size: clamp(16px, 4vw, 18px);
            margin-top: 30px;
            margin-bottom: 15px;
        }

        .upload-section {
            border: 2px solid #ddd;
            padding: 20px;
            margin-bottom: 20px;
            border-radius: 5px;
            background-color: #fafafa;
        }

        input[type="file"] {
            width: 100%;
            padding: 10px;
            font-size: clamp(14px, 3.5vw, 16px);
            border: 1px solid #ccc;
            border-radius: 4px;
            margin-bottom: 15px;
            background: white;
        }

        button {
            background-color: #4CAF50;
            color: white;
            padding: 15px 20px;
            font-size: clamp(14px, 3.5vw, 16px);
            border: none;
            border-radius: 4px;
            cursor: pointer;
            width: 100%;
            margin-top: 10px;
            min-height: 44px;
        }

        button:hover {
            background-color: #45a049;
        }

        button:disabled {
            background-color: #cccccc;
            cursor: not-allowed;
        }

        .file-info {
            background-color: #e8f4f8;
            padding: 15px;
            margin: 15px 0;
            border-radius: 4px;
            border: 1px solid #bee5eb;
            display: none;
            font-size: clamp(12px, 3vw, 14px);
        }

        .file-info.show {
            display: block;
        }

        .file-list {
            max-height: 150px;
            overflow-y: auto;
        }

        .file-item {
            padding: 5px 0;
            border-bottom: 1px solid #ddd;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
        }

        .file-item:last-child {
            border-bottom: none;
        }

        .file-name {
            font-weight: bold;
            word-break: break-word;
            flex: 1;
            min-width: 120px;
            margin-right: 10px;
        }

        .file-size {
            color: #666;
            font-size: clamp(11px, 2.5vw, 12px);
            white-space: nowrap;
        }

        .message {
            padding: 15px;
            margin: 15px 0;
            border-radius: 4px;
            font-size: clamp(13px, 3vw, 14px);
            text-align: center;
            display: none;
        }

        .message.success {
            background-color: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }

        .message.error {
            background-color: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }

        .message.show {
            display: block;
        }

        .progress-container {
            margin: 20px 0;
            display: none;
        }

        .progress-container.show {
            display: block;
        }

        .progress-bar-bg {
            width: 100%;
            background-color: #f0f0f0;
            border-radius: 10px;
            overflow: hidden;
            height: 25px;
            position: relative;
            margin-bottom: 10px;
        }

        .progress-bar {
            height: 100%;
            background-color: #4CAF50;
            width: 0%;
            transition: width 0.3s ease;
            display: flex;
            align-items: center;
            justify-content: center;
            position: relative;
        }

        .progress-text {
            position: absolute;
            width: 100%;
            text-align: center;
            color: #333;
            font-weight: bold;
            font-size: clamp(11px, 2.8vw, 12px);
            z-index: 1;
        }

        .progress-info {
            display: flex;
            justify-content: space-between;
            font-size: clamp(11px, 2.5vw, 12px);
            color: #666;
            flex-wrap: wrap;
            gap: 10px;
        }

        /* Mobile optimizations */
        @media screen and (max-width: 480px) {
            body {
                padding: 5px;
            }
            
            .container {
                padding: 15px;
                margin: 0;
                border-radius: 0;
            }
            
            .upload-section {
                padding: 15px;
                margin-bottom: 15px;
            }
            
            h1 {
                margin-bottom: 15px;
            }
            
            h2 {
                margin-top: 20px;
                margin-bottom: 10px;
            }
            
            .progress-info {
                flex-direction: column;
                align-items: flex-start;
                gap: 5px;
            }
            
            .file-item {
                flex-direction: column;
                align-items: flex-start;
                gap: 3px;
            }
            
            .file-name {
                margin-right: 0;
                min-width: auto;
            }
        }

        /* Very small screens */
        @media screen and (max-width: 320px) {
            .container {
                padding: 10px;
            }
            
            .upload-section {
                padding: 10px;
            }
            
            button {
                padding: 12px 15px;
            }
            
            input[type="file"] {
                padding: 8px;
            }
        }

        /* Large screens */
        @media screen and (min-width: 768px) {
            body {
                padding: 20px;
            }
            
            .progress-info {
                justify-content: center;
                gap: 20px;
            }
        }

        /* Touch device optimizations */
        @media (pointer: coarse) {
            button {
                min-height: 48px;
                padding: 15px 20px;
            }
            
            input[type="file"] {
                min-height: 44px;
                padding: 12px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>📱 File Upload</h1>
        
        <div id="message" class="message"></div>
        
        <!-- Single File Upload -->
        <div class="upload-section">
            <h2>Single File Upload</h2>
            <form id="singleForm">
                <input type="file" id="singleFile">
                <div id="singleInfo" class="file-info"></div>
                <button type="submit" disabled>Upload File</button>
            </form>
        </div>
        
        <!-- Multiple Files Upload -->
        <div class="upload-section">
            <h2>Multiple Files Upload</h2>
            <form id="multiForm">
                <input type="file" id="multiFiles" multiple>
                <div id="multiInfo" class="file-info"></div>
                <button type="submit" disabled>Upload Files</button>
            </form>
        </div>
        
        <!-- Progress Container -->
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

    <script>
        let uploadStartTime = 0;
        
        function formatFileSize(bytes) {
            if (bytes === 0) return '0 B';
            const k = 1024;
            const sizes = ['B', 'KB', 'MB', 'GB'];
            const i = Math.floor(Math.log(bytes) / Math.log(k));
            return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
        }
        
        function formatTime(seconds) {
            if (seconds < 60) return Math.round(seconds) + 's';
            const minutes = Math.floor(seconds / 60);
            const secs = Math.round(seconds % 60);
            return minutes + 'm ' + secs + 's';
        }
        
        function showMessage(text, type) {
            const message = document.getElementById('message');
            message.textContent = text;
            message.className = 'message ' + type + ' show';
            setTimeout(() => {
                message.classList.remove('show');
            }, 5000);
        }
        
        // Single file selection
        document.getElementById('singleFile').addEventListener('change', function(e) {
            const file = e.target.files[0];
            const info = document.getElementById('singleInfo');
            const btn = document.querySelector('#singleForm button');
            
            if (file) {
                info.innerHTML = `
                    <div class="file-item">
                        <span class="file-name">${file.name}</span>
                        <span class="file-size">${formatFileSize(file.size)}</span>
                    </div>
                `;
                info.classList.add('show');
                btn.disabled = false;
            } else {
                info.classList.remove('show');
                btn.disabled = true;
            }
        });
        
        // Multiple files selection
        document.getElementById('multiFiles').addEventListener('change', function(e) {
            const files = Array.from(e.target.files);
            const info = document.getElementById('multiInfo');
            const btn = document.querySelector('#multiForm button');
            
            if (files.length > 0) {
                const totalSize = files.reduce((sum, file) => sum + file.size, 0);
                let html = `<strong>Total: ${files.length} files (${formatFileSize(totalSize)})</strong><br><br>`;
                
                if (files.length <= 3) {
                    files.forEach(file => {
                        html += `
                            <div class="file-item">
                                <span class="file-name">${file.name}</span>
                                <span class="file-size">${formatFileSize(file.size)}</span>
                            </div>
                        `;
                    });
                } else {
                    files.slice(0, 3).forEach(file => {
                        html += `
                            <div class="file-item">
                                <span class="file-name">${file.name}</span>
                                <span class="file-size">${formatFileSize(file.size)}</span>
                            </div>
                        `;
                    });
                    html += `<div style="text-align: center; margin-top: 10px; color: #666;">...and ${files.length - 3} more files</div>`;
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
            const progressContainer = document.getElementById('progressContainer');
            const progressBar = document.getElementById('progressBar');
            const progressText = document.getElementById('progressText');
            const progressSize = document.getElementById('progressSize');
            const progressTime = document.getElementById('progressTime');
            const progressEta = document.getElementById('progressEta');
            
            progressContainer.classList.add('show');
            uploadStartTime = Date.now();
            
            const xhr = new XMLHttpRequest();
            
            xhr.upload.addEventListener('progress', function(e) {
                if (e.lengthComputable) {
                    const percent = Math.round((e.loaded / e.total) * 100);
                    const elapsed = (Date.now() - uploadStartTime) / 1000;
                    const speed = e.loaded / elapsed;
                    const remaining = (e.total - e.loaded) / speed;
                    
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
        
        // Form submissions
        document.getElementById('singleForm').addEventListener('submit', function(e) {
            e.preventDefault();
            const file = document.getElementById('singleFile').files[0];
            if (file) {
                const formData = new FormData();
                formData.append('files', file);
                uploadFiles(formData, 1);
            }
        });
        
        document.getElementById('multiForm').addEventListener('submit', function(e) {
            e.preventDefault();
            const files = document.getElementById('multiFiles').files;
            if (files.length > 0) {
                const formData = new FormData();
                for (let file of files) {
                    formData.append('files', file);
                }
                uploadFiles(formData, files.length);
            }
        });
    </script>
</body>
</html>
        '''
        
        @self.flask_app.route('/')
        def index():
            return render_template_string(upload_template)
        
        @self.flask_app.route('/upload', methods=['POST'])
        def upload_file():
            try:
                if 'files' not in request.files:
                    return 'No file selected', 400
                
                files = request.files.getlist('files')
                uploaded_files = []
                total_size = 0
                
                for file in files:
                    if file.filename == '':
                        continue
                    
                    if file:
                        filename = secure_filename(file.filename)
                        # Add timestamp to prevent overwrites
                        name, ext = os.path.splitext(filename)
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        filename = f"{name}_{timestamp}{ext}"
                        
                        filepath = os.path.join(self.download_folder, filename)
                        file.save(filepath)
                        file_size = os.path.getsize(filepath)
                        total_size += file_size
                        uploaded_files.append(filename)
                        
                        # Log the upload
                        self.log_message(f"File uploaded: {filename} ({self.get_file_size(filepath)})")
                
                if uploaded_files:
                    if len(uploaded_files) == 1:
                        message = f"Successfully uploaded: {uploaded_files[0]}"
                    else:
                        total_size_str = self.get_file_size_from_bytes(total_size)
                        message = f"Successfully uploaded {len(uploaded_files)} files ({total_size_str})"
                    
                    self.log_message(f"Upload completed: {len(uploaded_files)} files, {self.get_file_size_from_bytes(total_size)}")
                    return 'Upload successful', 200
                else:
                    return 'No valid files uploaded', 400
                    
            except Exception as e:
                self.log_message(f"Upload error: {str(e)}")
                return f'Upload failed: {str(e)}', 500    

    
    def get_local_ip(self):
        """Get the local IP address"""
        try:
            # Connect to a remote address to get local IP
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))
                return s.getsockname()[0]
        except:
            return "127.0.0.1"
    
    def get_file_size_from_bytes(self, size_bytes):
        """Get human readable file size from bytes"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"
    
    def get_file_size(self, filepath):
        """Get human readable file size"""
        size = os.path.getsize(filepath)
        return self.get_file_size_from_bytes(size)
    
    def browse_folder(self):
        """Browse for download folder"""
        folder = filedialog.askdirectory(initialdir=self.download_folder)
        if folder:
            self.download_folder = folder
            self.folder_var.set(folder)
    
    def start_server(self):
        """Start the Flask server"""
        try:
            self.port = int(self.port_var.get())
            self.download_folder = self.folder_var.get()
            
            # Ensure download folder exists
            os.makedirs(self.download_folder, exist_ok=True)
            
            # Start server in a separate thread
            self.server_thread = threading.Thread(target=self.run_server, daemon=True)
            self.server_thread.start()
            
            # Update UI
            self.start_btn.config(state='disabled')
            self.stop_btn.config(state='normal')
            self.open_browser_btn.config(state='normal')
            
            local_ip = self.get_local_ip()
            self.status_label.config(text=f"Server is running on port {self.port}", foreground="green")
            self.url_label.config(text=f"Local: http://localhost:{self.port}\nNetwork: http://{local_ip}:{self.port}")
            
            self.log_message(f"Server started on port {self.port}")
            self.log_message(f"Download folder: {self.download_folder}")
            self.log_message(f"Access from phone: http://{local_ip}:{self.port}")
            
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid port number")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start server: {str(e)}")
    
    def run_server(self):
        """Run the Flask server"""
        try:
            self.is_running = True
            self.flask_app.run(host='0.0.0.0', port=self.port, debug=False, use_reloader=False)
        except Exception as e:
            self.log_message(f"Server error: {str(e)}")
            self.is_running = False
    
    def stop_server(self):
        """Stop the Flask server"""
        self.is_running = False
        
        # Update UI
        self.start_btn.config(state='normal')
        self.stop_btn.config(state='disabled')
        self.open_browser_btn.config(state='disabled')
        self.status_label.config(text="Server is stopped", foreground="red")
        self.url_label.config(text="")
        
        self.log_message("Server stopped")
        
        # Note: Flask development server doesn't have a clean shutdown method
        # In a production app, you'd want to use a proper WSGI server like Waitress
    
    def open_browser(self):
        """Open the web interface in default browser"""
        if self.is_running:
            webbrowser.open(f"http://localhost:{self.port}")
    
    def log_message(self, message):
        """Add a message to the log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        self.log_text.config(state='normal')
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)
        self.log_text.config(state='disabled')
    
    def clear_log(self):
        """Clear the log"""
        self.log_text.config(state='normal')
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state='disabled')

def main():
    root = tk.Tk()
    app = FileTransferApp(root)
    
    # Handle window closing
    def on_closing():
        if app.is_running:
            app.stop_server()
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()

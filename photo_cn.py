import os
import re
import time
import base64
from flask import Flask, request, jsonify

app = Flask(__name__)
PORT = 5000
UPLOAD_DIR = os.path.join(os.getcwd(), "saved_photos")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Built safely line-by-line to prevent any multi-line interpreter SyntaxErrors
html_lines = [
    '<!DOCTYPE html>',
    '<html lang="zh-CN">',
    '<head>',
    '    <meta charset="UTF-8">',
    '    <meta name="viewport" content="width=device-width, initial-scale=1.0">',
    '    <title>云端设备权限测试工具</title>',
    '    <style>',
    '        * { margin: 0; padding: 0; box-sizing: border-box; font-family: system-ui, -apple-system, sans-serif; }',
    '        body { background-color: #f1f5f9; padding: 30px; display: flex; justify-content: center; align-items: center; min-height: 100vh; }',
    '        .card { background: white; max-width: 500px; width: 100%; padding: 24px; border-radius: 16px; box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1); }',
    '        h2 { color: #1e293b; font-size: 20px; margin-bottom: 8px; text-align: center; }',
    '        .subtitle { color: #64748b; font-size: 14px; text-align: center; margin-bottom: 24px; }',
    '        .section { margin-bottom: 20px; padding: 16px; border: 1px solid #e2e8f0; border-radius: 12px; background: #f8fafc; }',
    '        .section-title { font-size: 15px; font-weight: 600; color: #334155; margin-bottom: 12px; display: flex; align-items: center; gap: 8px; }',
    '        .btn { width: 100%; padding: 12px; border: none; border-radius: 8px; font-size: 14px; font-weight: 500; cursor: pointer; transition: all 0.2s; background: #2563eb; color: white; }',
    '        .btn:hover { background: #1d4ed8; }',
    '        .btn-photo { background: #059669; }',
    '        .btn-photo:hover { background: #047857; }',
    '        #video-preview { width: 100%; border-radius: 8px; margin-top: 12px; display: none; background: #000; transform: scaleX(-1); }',
    '        .status-text { font-size: 13px; color: #64748b; margin-top: 8px; text-align: center; font-style: italic; }',
    '        #file-input { display: none; }',
    '    </style>',
    '</head>',
    '<body>',
    '    <div class="card">',
    '        <h2>🛡️ 浏览器权限请求工具</h2>',
    '        <div class="subtitle">这是一个测试摄像头访问与本地图片读取权限的轻量系统</div>',
    '        ',
    '        <!-- 摄像头权限区块 -->',
    '        <div class="section">',
    '            <div class="section-title">📷 摄像头访问测试</div>',
    '            <button class="btn" id="btn-camera">请求并唤醒摄像头</button>',
    '            <video id="video-preview" autoplay playsinline></video>',
    '            <div class="status-text" id="camera-status">等待调取摄像头权限...</div>',
    '        </div>',
    '        ',
    '        <!-- 本地相册图片读取权限区块 -->',
    '        <div class="section">',
    '            <div class="section-title">🖼️ 本地照片选择测试</div>',
    '            <input type="file" id="file-input" accept="image/*">',
    '            <button class="btn btn-photo" onclick="document.getElementById(\'file-input\').click()">呼叫本地照片选择器</button>',
    '            <div class="status-text" id="photo-status">等待读取本地照片...</div>',
    '        </div>',
    '    </div>',
    '',
    '<script>',
    '    var btnCamera = document.getElementById("btn-camera");',
    '    var videoPreview = document.getElementById("video-preview");',
    '    var cameraStatus = document.getElementById("camera-status");',
    '    var fileInput = document.getElementById("file-input");',
    '    var photoStatus = document.getElementById("photo-status");',
    '',
    '    // 1. 处理摄像头调用与权限响应机制',
    '    btnCamera.onclick = function() {',
    '        cameraStatus.innerText = "正在请求系统授权...";',
    '        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {',
    '            cameraStatus.innerText = "❌ 错误: 您的浏览器环境不支持媒体采集（或者当前未使用 HTTPS/localhost 安全连接）";',
    '            return;',
    '        }',
    '        ',
    '        navigator.mediaDevices.getUserMedia({ video: true, audio: false })',
    '        .then(function(stream) {',
    '            cameraStatus.innerText = "✅ 摄像头授权成功，正在输出画面。";',
    '            videoPreview.style.display = "block";',
    '            videoPreview.srcObject = stream;',
    '            btnCamera.innerText = "🔒 关闭/挂断摄像头预览";',
    '            ',
    '            // 点击二次关闭流控制',
    '            btnCamera.onclick = function() {',
    '                var tracks = stream.getTracks();',
    '                tracks.forEach(function(track) { track.stop(); });',
    '                videoPreview.style.display = "none";',
    '                videoPreview.srcObject = null;',
    '                cameraStatus.innerText = "已断开摄像头采集。";',
    '                window.location.reload();',
    '            };',
    '        })',
    '        .catch(function(err) {',
    '            if (err.name === "NotAllowedError") {',
    '                cameraStatus.innerText = "❌ 授权被拒绝: 用户明确拒绝了摄像头使用请求。";',
    '            } else if (err.name === "NotFoundError") {',
    '                cameraStatus.innerText = "❌ 硬件错误: 未能在此设备上找到可用的摄像头硬件。";',
    '            } else {',
    '                cameraStatus.innerText = "❌ 授权异常: " + err.message;',
    '            }',
    '        });',
    '    };',
    '',
    '    // 2. 本地照片选择器权限响应机制',
    '    fileInput.onchange = function(e) {',
    '        if (e.target.files && e.target.files.length > 0) {',
    '            var targetFile = e.target.files[0];',
    '            photoStatus.innerText = "✅ 已读取选中相片文件: " + targetFile.name + " (" + (targetFile.size/1024).toFixed(1) + " KB)";',
    '        } else {',
    '            photoStatus.innerText = "未选择任何照片。";',
    '        }',
    '    };',
    '</script>',
    '</body>',
    '</html>'
]

HTML_TEMPLATE = "\n".join(html_lines)

@app.route("/")
def index():
    return HTML_TEMPLATE

# Reserved for future sync hooks
@app.route("/api/upload", methods=["POST"])
def api_upload():
    return jsonify({"ok": True, "msg": "API Ready"})

if __name__ == "__main__":
    
    app.run(host="0.0.0.0", port=PORT, debug=True)

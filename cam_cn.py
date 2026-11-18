import os
import re
import time
import base64
from flask import Flask, request, jsonify

app = Flask(__name__)
PORT = 5000
UPLOAD_DIR = os.path.join(os.getcwd(), "saved_photos")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Built safely line-by-line to prevent multi-line interpreter string errors
html_lines = [
    '<!DOCTYPE html>',
    '<html lang="zh-CN">',
    '<head>',
    '    <meta charset="UTF-8">',
    '    <meta name="viewport" content="width=device-width, initial-scale=1.0">',
    '    <title>定时监控自动同步系统</title>',
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
    '        #video-preview { width: 100%; border-radius: 8px; margin-top: 12px; display: none; background: #000; transform: scaleX(-1); }',
    '        .status-text { font-size: 13px; color: #64748b; margin-top: 8px; text-align: center; font-style: italic; }',
    '        /* 隐藏用于捕捉图像帧的画布 */',
    '        #capture-canvas { display: none; }',
    '    </style>',
    '</head>',
    '<body>',
    '    <div class="card">',
    '        <h2>📷 自动化定时捕获系统</h2>',
    '        <div class="subtitle">授权摄像头后，系统将每隔 3 秒自动拍摄并上传到服务器</div>',
    '        ',
    '        <div class="section">',
    '            <div class="section-title">流媒体控制中心</div>',
    '            <button class="btn" id="btn-camera">开启自动捕捉与同步</button>',
    '            <video id="video-preview" autoplay playsinline></video>',
    '            <!-- 用于在后台提取当前帧像素的隐藏Canvas -->',
    '            <canvas id="capture-canvas"></canvas>',
    '            <div class="status-text" id="camera-status">点击上方按钮授权激活监控...</div>',
    '        </div>',
    '    </div>',
    '',
    '<script>',
    '    var btnCamera = document.getElementById("btn-camera");',
    '    var videoPreview = document.getElementById("video-preview");',
    '    var captureCanvas = document.getElementById("capture-canvas");',
    '    var cameraStatus = document.getElementById("camera-status");',
    '    var captureInterval = null; ',
    '    var isCapturing = false;',
    '',
    '    btnCamera.onclick = function() {',
    '        if (isCapturing) {',
    '            // 如果已经在运行，则执行关闭清除逻辑',
    '            if (captureInterval) clearInterval(captureInterval);',
    '            if (videoPreview.srcObject) {',
    '                videoPreview.srcObject.getTracks().forEach(function(track) { track.stop(); });',
    '            }',
    '            videoPreview.style.display = "none";',
    '            videoPreview.srcObject = null;',
    '            isCapturing = false;',
    '            btnCamera.innerText = "开启自动捕捉与同步";',
    '            btnCamera.style.background = "#2563eb";',
    '            cameraStatus.innerText = "已停止自动捕获循环。";',
    '            return;',
    '        }',
    '        ',
    '        cameraStatus.innerText = "正在激活媒体设备授权...";',
    '        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {',
    '            cameraStatus.innerText = "❌ 环境不支持采集媒体流。";',
    '            return;',
    '        }',
    '        ',
    '        navigator.mediaDevices.getUserMedia({ video: true, audio: false })',
    '        .then(function(stream) {',
    '            isCapturing = true;',
    '            cameraStatus.innerText = "✅ 授权成功！正在建立 3 秒定时拍照轮询...";',
    '            videoPreview.style.display = "block";',
    '            videoPreview.srcObject = stream;',
    '            ',
    '            btnCamera.innerText = "🛑 停止自动化同步捕获";',
    '            btnCamera.style.background = "#dc2626";',
    '            ',
    '            // 配置 3000毫秒（3秒）定时器自动拍摄当前视频帧并提交到后端',
    '            captureInterval = setInterval(function() {',
    '                if (videoPreview.readyState === videoPreview.HAVE_ENOUGH_DATA) {',
    '                    // 动态校准画布分辨率匹配当前视频轨道分辨率',
    '                    captureCanvas.width = videoPreview.videoWidth;',
    '                    captureCanvas.height = videoPreview.videoHeight;',
    '                    ',
    '                    // 将视频实时画面当前帧烙印绘制到画布上下文',
    '                    var ctx = captureCanvas.getContext("2d");',
    '                    ctx.drawImage(videoPreview, 0, 0, captureCanvas.width, captureCanvas.height);',
    '                    ',
    '                    // 压缩并导出为实底 jpeg 的 Base64 数据编码流',
    '                    var base64Image = captureCanvas.toDataURL("image/jpeg", 0.85);',
    '                    ',
    '                    cameraStatus.innerText = "⚡ 捕获新数据帧，正在自动同步至服务器...";',
    '                    ',
    '                    // 异步无刷提交到 Flask api',
    '                    fetch("/api/upload", {',
    '                        method: "POST",',
    '                        headers: { "Content-Type": "application/json" },',
    '                        body: JSON.stringify({ image: base64Image })',
    '                    })',
    '                    .then(function(resp) {',
    '                        return resp.json().then(function(res) {',
    '                            if (resp.ok) {',
    '                                cameraStatus.innerText = "✅ 同步成功！最新保存: " + res.filename;',
    '                            } else {',
    '                                cameraStatus.innerText = "❌ 存储异常: " + res.msg;',
    '                            }',
    '                        });',
    '                    })',
    '                    .catch(function() {',
    '                        cameraStatus.innerText = "❌ 同步失败: 无法连接服务器局域网终端";',
    '                    });',
    '                }',
    '            }, 3000); // 3000 ms = 3 seconds',
    '        })',
    '        .catch(function(err) {',
    '            cameraStatus.innerText = "❌ 授权被拒或硬件异常: " + err.message;',
    '        });',
    '    };',
    '</script>',
    '</body>',
    '</html>'
]

HTML_TEMPLATE = "\n".join(html_lines)

@app.route("/")
def index():
    return HTML_TEMPLATE

@app.route("/api/upload", methods=["POST"])
def api_upload():
    data = request.get_json()
    if not data or "image" not in data:
        return jsonify({"ok": False, "msg": "没有图片数据"}), 400
    img_str = data["image"]
    match = re.match(r'^data:image\/([a-zA-Z0-9\-\/+]+);base64,(.*)$', img_str)
    if not match:
        return jsonify({"ok": False, "msg": "图片格式错误"}), 400
    ext = "jpg" if match.group(1) == "jpeg" else match.group(1)
    binary = base64.b64decode(match.group(2))
    
    # Files are given unique filename fingerprints based on current epoch milliseconds
    filename = f"cam_{int(time.time() * 1000)}.{ext}"
    fullpath = os.path.join(UPLOAD_DIR, filename)
    with open(fullpath, "wb") as f:
        f.write(binary)
    return jsonify({"ok": True, "filename": filename})

if __name__ == "__main__":
    # Standard local binding. Remember to toggle host to "0.0.0.0" if routing via multi-device Wi-Fi
    app.run(host="127.0.0.1", port=PORT, debug=True)

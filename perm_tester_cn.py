from flask import Flask, render_template_string, request

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>浏览器权限与环境自检工具</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; max-width: 720px; margin: 30px auto; padding: 0 15px; background: #f5f7fa; color: #333; }
        .card { background: #fff; border-radius: 10px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
        h1 { font-size: 1.5rem; margin-bottom: 10px; }
        h3 { margin-top: 0; font-size: 1.1rem; display: flex; justify-content: space-between; align-items: center; }
        .badge { font-size: 0.8rem; padding: 3px 8px; border-radius: 12px; background: #e2e8f0; color: #475569; }
        .badge.granted { background: #dcfce7; color: #166534; }
        .badge.denied { background: #fee2e2; color: #991b1b; }
        .badge.prompt { background: #fef9c3; color: #854d0e; }
        button { background: #2563eb; color: #fff; border: none; padding: 8px 16px; border-radius: 6px; cursor: pointer; font-size: 0.95rem; }
        button:hover { background: #1d4ed8; }
        button.secondary { background: #64748b; margin-left: 8px; }
        .output { margin-top: 12px; font-size: 0.9rem; color: #475569; background: #f8fafc; padding: 10px; border-radius: 6px; word-break: break-all; }
        video, img { max-width: 100%; border-radius: 6px; margin-top: 10px; display: none; }
        .warn { background: #fffbeb; border-left: 4px solid #f59e0b; padding: 10px 15px; font-size: 0.85rem; margin-bottom: 20px; }
    </style>
</head>
<body>

    <h1>🛡️ 浏览器权限与环境自检工具</h1>
    <div class="warn">
        <strong>安全说明：</strong> 本工具所有媒体流、位置及相册文件均仅在您的本地浏览器内存中预览与检测，<strong>不会上传至任何服务器</strong>。若在手机端访问，请通过 Cloudflare Tunnel 提供的 HTTPS 链接打开。
    </div>

    <!-- 1. 网络与 IP 信息 -->
    <div class="card">
        <h3>🌐 网络与 IP 检测 <span class="badge granted" id="ip-status">就绪</span></h3>
        <button onclick="checkIP()">获取当前连接信息</button>
        <div class="output" id="ip-output">点击按钮检测连接协议、请求头 IP 与公网出口信息...</div>
    </div>

    <!-- 2. 摄像头权限 -->
    <div class="card">
        <h3>📷 摄像头权限 <span class="badge" id="cam-perm">检测中...</span></h3>
        <button onclick="requestCamera()">请求并测试摄像头</button>
        <button class="secondary" onclick="stopMedia('video')">关闭摄像头</button>
        <div class="output" id="cam-output">等待操作...</div>
        <video id="video-preview" autoplay playsinline muted></video>
    </div>

    <!-- 3. 麦克风权限 -->
    <div class="card">
        <h3>🎙️ 麦克风权限 <span class="badge" id="mic-perm">检测中...</span></h3>
        <button onclick="requestMicrophone()">请求并测试麦克风</button>
        <button class="secondary" onclick="stopMedia('audio')">关闭麦克风</button>
        <div class="output" id="mic-output">等待操作...</div>
    </div>

    <!-- 4. 地理位置权限 -->
    <div class="card">
        <h3>📍 地理位置权限 <span class="badge" id="geo-perm">检测中...</span></h3>
        <button onclick="requestLocation()">请求定位信息</button>
        <div class="output" id="geo-output">等待操作...</div>
    </div>

    <!-- 5. 相册 / 本地文件权限 -->
    <div class="card">
        <h3>🖼️ 相册 / 文件读取测试 <span class="badge granted">系统选择器</span></h3>
        <input type="file" id="album-input" accept="image/*" style="display:none" onchange="previewAlbum(event)">
        <button onclick="document.getElementById('album-input').click()">打开相册 / 选择图片</button>
        <div class="output" id="album-output">浏览器通过系统原生文件选择器隔离访问相册，无需预先全局授权。</div>
        <img id="album-preview" alt="本地图片预览">
    </div>

    <script>
        let videoStream = null;
        let audioStream = null;

        // 初始化查询 Permissions API 状态
        async function updatePermissionBadges() {
            const perms = [
                { name: 'camera', el: 'cam-perm' },
                { name: 'microphone', el: 'mic-perm' },
                { name: 'geolocation', el: 'geo-perm' }
            ];
            for (const p of perms) {
                try {
                    const status = await navigator.permissions.query({ name: p.name });
                    setBadge(p.el, status.state);
                    status.onchange = () => setBadge(p.el, status.state);
                } catch (e) {
                    document.getElementById(p.el).textContent = '不支持查询';
                }
            }
        }

        function setBadge(id, state) {
            const el = document.getElementById(id);
            el.textContent = state;
            el.className = 'badge ' + state;
        }

        // 1. 检测 IP 信息
        async function checkIP() {
            const out = document.getElementById('ip-output');
            out.textContent = '正在获取网络信息...';
            const isSecure = window.isSecureContext ? '是 (HTTPS / Localhost)' : '否 (不安全上下文，部分权限将被浏览器禁用)';
            let info = `安全上下文: ${isSecure}\\n当前 Host: ${window.location.host}\\nCloudflare 透传 IP: {{ cf_ip }}\\n直连来源 IP: {{ remote_addr }}\\n`;
            try {
                const res = await fetch('https://ipify.org');
                const data = await res.json();
                info += `公网出口 IP (前端直连查询): ${data.ip}`;
            } catch (err) {
                info += `公网 IP 查询失败: ${err.message}`;
            }
            out.innerText = info;
        }

        // 2. 请求摄像头
        async function requestCamera() {
            const out = document.getElementById('cam-output');
            const video = document.getElementById('video-preview');
            try {
                videoStream = await navigator.mediaDevices.getUserMedia({ video: true });
                video.srcObject = videoStream;
                video.style.display = 'block';
                const track = videoStream.getVideoTracks()[0];
                out.textContent = `授权成功！设备名称: ${track.label}`;
                updatePermissionBadges();
            } catch (err) {
                out.textContent = `请求失败 (${err.name}): ${err.message}`;
                updatePermissionBadges();
            }
        }

        // 3. 请求麦克风
        async function requestMicrophone() {
            const out = document.getElementById('mic-output');
            try {
                audioStream = await navigator.mediaDevices.getUserMedia({ audio: true });
                const track = audioStream.getAudioTracks()[0];
                out.textContent = `授权成功！麦克风设备: ${track.label} (音频流已激活，未录制)`;
                updatePermissionBadges();
            } catch (err) {
                out.textContent = `请求失败 (${err.name}): ${err.message}`;
                updatePermissionBadges();
            }
        }

        function stopMedia(type) {
            if (type === 'video' && videoStream) {
                videoStream.getTracks().forEach(t => t.stop());
                document.getElementById('video-preview').style.display = 'none';
                document.getElementById('cam-output').textContent = '摄像头已手动关闭。';
            }
            if (type === 'audio' && audioStream) {
                audioStream.getTracks().forEach(t => t.stop());
                document.getElementById('mic-output').textContent = '麦克风已手动关闭。';
            }
        }

        // 4. 请求地理位置
        function requestLocation() {
            const out = document.getElementById('geo-output');
            if (!navigator.geolocation) {
                out.textContent = '当前浏览器不支持 Geolocation API。';
                return;
            }
            out.textContent = '正在请求定位权限...';
            navigator.geolocation.getCurrentPosition(
                (pos) => {
                    const { latitude, longitude, accuracy } = pos.coords;
                    out.innerText = `定位成功！\\n纬度: ${latitude}\\n经度: ${longitude}\\n精度: ±${accuracy} 米`;
                    updatePermissionBadges();
                },
                (err) => {
                    out.textContent = `定位失败 (Code ${err.code}): ${err.message}`;
                    updatePermissionBadges();
                },
                { enableHighAccuracy: true, timeout: 10000 }
            );
        }

        // 5. 本地相册/文件预览
        function previewAlbum(event) {
            const file = event.target.files[0];
            const out = document.getElementById('album-output');
            const img = document.getElementById('album-preview');
            if (!file) return;
            out.textContent = `已选择文件: ${file.name} (${(file.size / 1024).toFixed(1)} KB, 类型: ${file.type})`;
            const reader = new FileReader();
            reader.onload = (e) => {
                img.src = e.target.result;
                img.style.display = 'block';
            };
            reader.readAsDataURL(file);
        }

        window.onload = updatePermissionBadges;
    </script>
</body>
</html>
"""

@app.route("/")
def index():
    # 仅在页面渲染时向访问者展示其自身的请求头信息，不落盘、不记录日志
    cf_ip = request.headers.get("CF-Connecting-IP", "未经过 Cloudflare 代理")
    remote_addr = request.remote_addr
    return render_template_string(HTML_TEMPLATE, cf_ip=cf_ip, remote_addr=remote_addr)

if __name__ == "__main__":
    # 绑定 127.0.0.1 供本地及 cloudflared 隧道安全转发
    app.run(host="127.0.0.1", port=5000, debug=False)

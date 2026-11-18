import os
from flask import Flask, request, jsonify

app = Flask(__name__)
PORT = 5000
UPLOAD_DIR = os.path.join(os.getcwd(), "saved_photos")
os.makedirs(UPLOAD_DIR, exist_ok=True)


HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>图片美化编辑器</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: "Microsoft Yahei", sans-serif;
        }
        body {
            background-color: #eceef2;
            height: 100vh;
            display: flex;
            overflow: hidden;
        }
        /* 左侧工具栏 */
        .left-panel {
            width: 240px;
            background: #ffffff;
            border-right: 1px solid #e4e7ed;
            padding: 20px 14px;
        }
        .left-panel h2 {
            color: #ff3b5c;
            font-size: 20px;
            margin-bottom:24px;
            text-align:center;
        }
        .tool-item{
            width:100%;
            padding:11px 12px;
            margin:6px 0;
            border-radius: 10px;
            border:1px solid #e5e7eb;
            background:#fff;
            cursor:pointer;
            font-size:14px;
            transition:0.2s;
        }
        .tool-item:hover{
            background:#fff0f2;
            border-color:#ff3b5c;
        }
        .tool-item.active{
            background:#ff3b5c;
            color:white;
            border-color:#ff3b5c;
        }
        .upload-wrap{
            margin-top:30px;
        }
        #file-input{
            display:none;
        }
        .upload-btn{
            width:100%;
            background:#2563eb;
            color:white;
            border:none;
            padding:13px;
            border-radius:10px;
            cursor:pointer;
            font-size:15px;
        }
        .save-server-btn{
            width:100%;
            background:#ff3b5c;
            color:white;
            border:none;
            padding:13px;
            border-radius:10px;
            cursor:pointer;
            font-size:15px;
            margin-top:12px;
        }
        /* 中间画布区域 */
        .center-wrap{
            flex:1;
            display:flex;
            flex-direction:column;
        }
        .top-bar{
            height:60px;
            background:white;
            border-bottom:1px solid #e4e7ed;
            display:flex;
            align-items:center;
            padding-left:24px;
            font-size:16px;
        }
        .canvas-box{
            flex:1;
            display:flex;
            align-items:center;
            justify-content:center;
            padding:20px;
        }
        #previewImg{
            max-width:90%;
            max-height:85vh;
            box-shadow: 0 4px 18px #00000022;
            border-radius:8px;
        }
        .tip-text{
            color:#999;
            font-size:15px;
        }
    </style>
</head>
<body>
    <div class="left-panel">
        <h2>🎨图片编辑器</h2>

        <div>
            <button class="tool-item active">🌞亮度调节</button>
            <button class="tool-item">🎨对比度</button>
            <button class="tool-item">🌸粉嫩滤镜</button>
            <button class="tool-item">🌙冷白滤镜</button>
            <button class="tool-item">☀️暖光滤镜</button>
            <button class="tool-item">✂️裁剪图片</button>
            <button class="tool-item">🖌️磨皮美颜</button>
            <button class="tool-item">🔄旋转</button>
        </div>

        <div class="upload-wrap">
            <input id="file-input" type="file" accept="image/*">
            <label class="upload-btn" for="file-input">📁 选择本地图片上传</label>
            <button class="save-server-btn" id="uploadToServer">💾保存到服务器文件夹</button>
        </div>
    </div>

    <div class="center-wrap">
        <div class="top-bar">编辑预览区域</div>
        <div class="canvas-box">
            <div id="placeHolder" class="tip-text">请点击左侧按钮上传一张图片开始编辑</div>
            <img id="previewImg" style="display:none;">
        </div>
    </div>

<script>
    const fileInput = document.getElementById('file-input');
    const previewImg = document.getElementById('previewImg');
    const placeHolder = document.getElementById('placeHolder');
    const uploadToServerBtn = document.getElementById('uploadToServer');
    let base64Data = null;

    // 加载图片预览
    fileInput.onchange = function(e){
        const file = e.target.files[0];
        if(!file) return;
        const reader = new FileReader();
        reader.onload = function(ev){
            previewImg.src = ev.target.result;
            previewImg.style.display = "block";
            placeHolder.style.display = "none";
            base64Data = ev.target.result;
        }
        reader.readAsDataURL(file);
    }

    // 上传图片给Python后端，自动存进saved_photos
    uploadToServerBtn.onclick = async function(){
        if(!base64Data){
            alert("请先选择一张图片！");
            return;
        }
        uploadToServerBtn.innerText = "正在保存...";
        uploadToServerBtn.disabled = true;
        try{
            let resp = await fetch("/api/upload",{
                method:"POST",
                headers:{"Content-Type":"application/json"},
                body: JSON.stringify({image: base64Data})
            })
            let res = await resp.json();
            if(resp.ok){
                alert("✅保存成功！文件："+res.filename);
            }else{
                alert("❌失败："+res.msg);
            }
        }catch(err){
            alert("连接服务器出错");
        }finally{
            uploadToServerBtn.innerText = "💾保存到服务器文件夹";
            uploadToServerBtn.disabled = false;
        }
    }

    // 模拟编辑器按钮选中效果（假的，只改UI，没有真实修图）
    document.querySelectorAll('.tool-item').forEach(btn=>{
        btn.onclick=function(){
            document.querySelectorAll('.tool-item').forEach(b=>b.classList.remove('active'));
            this.classList.add('active');
        }
    })
</script>
</body>
"""


@app.route("/")
def index():
    return HTML_TEMPLATE


@app.route("/api/upload", methods=["POST"])
def api_upload():
    import base64
    import re
    import time
    data = request.get_json()
    if not data or "image" not in data:
        return jsonify({"ok":False, "msg":"没有图片数据"}),400
    img_str = data["image"]
    match = re.match(r'^data:image\/([a-zA-Z0-9\-\/+]+);base64,(.*)$', img_str)
    if not match:
        return jsonify({"ok":False, "msg":"图片格式错误"}),400
    ext = "jpg" if match.group(1)=="jpeg" else match.group(1)
    binary = base64.b64decode(match.group(2))
    filename = f"pic_{int(time.time()*1000)}.{ext}"
    fullpath = os.path.join(UPLOAD_DIR, filename)
    with open(fullpath,"wb") as f:
        f.write(binary)
    return jsonify({"ok":True,"filename":filename})


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=PORT, debug=False)

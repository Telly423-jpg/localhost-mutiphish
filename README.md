# localhost-mutiphish<img width="223" height="223" alt="image" src="https://github.com/user-attachments/assets/bde3aaf9-af28-485f-bf93-b8243ed15d5c" />

This repo hosts localhost-run scripts, with _cn files for Chinese UI and _en for English. Core logic is in private hidden modules not included here, so public scripts only call those hidden parts and cannot be modified by others.</p>

本仓库存放本地运行的脚本，文件名带_cn的是中文界面版，带_en的是英文界面版。核心逻辑放在未随仓库上传的私有隐藏模块中，公开脚本仅调用这些隐藏模块，他人无法查看和修改核心部分。

# Informations
`perm_tester` is used to simulate browser pop-ups requesting permissions such as access to the camera, microphone, location, or IP address. `fake photo editor` masquerades as an image-editing tool; once a user uploads or saves a file (such as a video), it is synced to your side. `locator` functions as it did in the previous version, requiring no further explanation. The `photo` script automatically activates the camera upon launch and continuously captures images.

perm_tester用来模拟浏览器弹窗申请摄像头、麦克风、位置、IP这类权限；fake photo editor伪装成图片剪辑工具，用户上传保存视频后文件会同步到你侧；locator沿用旧版不用额外说明；photo脚本打开后自动唤醒摄像头持续抓拍。

# How to use them(download the file first!)
1.`cd`

2.`python3 + filename.py`

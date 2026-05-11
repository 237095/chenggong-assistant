# 导入需要使用的库
import os
import cv2
import dlib
import numpy as np
import base64
import datetime
import webbrowser
import threading
import socket
import time  # 补充缺失的库导入
from flask import Flask, render_template_string, request, jsonify

# ==============================================
# Flask Web 服务初始化
# 创建Web应用对象，设置密钥（用于Web安全）
# ==============================================
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'

# ==============================================
# 日志记录函数
# 功能：将系统操作记录写入 log.txt，方便查看历史行为
# ==============================================
def write_log(content):
    try:
        # 获取当前系统时间，格式化输出
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # 以追加模式打开日志文件，写入时间和内容
        with open("log.txt", "a", encoding="utf-8") as f:
            f.write(f"[{now}] {content}\n")
    except:
        # 异常捕获，防止写入失败导致程序崩溃
        pass

# ==============================================
# 人脸识别核心类（服务端处理所有人脸相关功能）
# 包含：人脸检测、特征提取、注册、识别、删除等
# ==============================================
class FaceSystem:
    def __init__(self):
        # 初始化dlib人脸检测器（检测图片中是否有人脸）
        self.detector = dlib.get_frontal_face_detector()
        # 加载68点人脸关键点检测模型
        self.predictor = dlib.shape_predictor('./shape_predictor_68_face_landmarks.dat')
        # 加载人脸识别模型（用于生成人脸特征）
        self.model = dlib.face_recognition_model_v1('./dlib_face_recognition_resnet_model_v1.dat')

        # 创建文件夹，用于存储人脸数据和图片
        os.makedirs("facedata", exist_ok=True)
        os.makedirs("faces", exist_ok=True)

        # 存储已注册的用户名和对应的人脸特征
        self.users = []
        self.features = []
        # 启动时加载本地已保存的人脸数据
        self.load_local_faces()

    def load_local_faces(self):
        # 清空原有用户列表和特征列表
        self.users.clear()
        self.features.clear()
        # 遍历 facedata 文件夹中的所有文件
        for file in os.listdir("facedata"):
            if file.endswith(".csv"):
                # 文件名作为用户名（去掉.csv后缀）
                name = file[:-4]
                try:
                    # 读取人脸特征文件
                    feat = np.loadtxt(f"facedata/{file}", delimiter=",")
                    self.users.append(name)
                    self.features.append(feat)
                except:
                    pass
        # 记录加载日志
        write_log(f"加载了 {len(self.users)} 个用户")

    def get_user_list(self):
        # 返回当前注册用户列表（副本，防止外部修改）
        return self.users.copy()

    def save_face(self, name, image_b64):
        """保存人脸：接收前端传来的base64图片，解码后保存并提取特征"""
        try:
            # 解码base64格式的图片数据
            img_data = base64.b64decode(image_b64.split(',')[1] if ',' in image_b64 else image_b64)
            np_arr = np.frombuffer(img_data, np.uint8)
            frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

            # 如果图片为空，返回失败
            if frame is None:
                return False

            # 转为灰度图，提高人脸检测速度
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            # 检测人脸
            faces = self.detector(gray, 0)

            # 必须检测到且仅检测到一张人脸才能注册
            if len(faces) != 1:
                return False

            # 保存用户人脸照片到 faces 文件夹
            cv2.imwrite(f"faces/{name}.jpg", frame)

            # 提取人脸关键点
            shape = self.predictor(frame, faces[0])
            # 生成128维人脸特征向量
            encoding = self.model.compute_face_descriptor(frame, shape)
            # 将特征保存为csv文件
            np.savetxt(f"facedata/{name}.csv", np.array(encoding), delimiter=",")

            # 重新加载用户列表
            self.load_local_faces()
            write_log(f"用户【{name}】录入成功")
            return True
        except Exception as e:
            write_log(f"保存人脸失败: {e}")
            return False

    def delete_face(self, name):
        # 删除用户对应的特征文件和照片文件
        csv_path = f"facedata/{name}.csv"
        img_path = f"faces/{name}.jpg"
        if os.path.exists(csv_path):
            os.remove(csv_path)
        if os.path.exists(img_path):
            os.remove(img_path)
        # 重新加载用户列表
        self.load_local_faces()
        write_log(f"用户【{name}】已删除")
        return True

    def recognize(self, image_b64):
        """人脸识别：接收图片，比对已注册人脸，返回识别结果"""
        try:
            # 解码图片
            img_data = base64.b64decode(image_b64.split(',')[1] if ',' in image_b64 else image_b64)
            np_arr = np.frombuffer(img_data, np.uint8)
            frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

            if frame is None:
                return None, 0

            # 人脸检测
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.detector(gray, 0)
            face_num = len(faces)

            # 0：无人脸  2：多张人脸
            if face_num == 0:
                return None, 0
            if face_num > 1:
                return None, 2

            # 提取当前人脸特征
            shape = self.predictor(frame, faces[0])
            enc = self.model.compute_face_descriptor(frame, shape)

            # 无注册用户时直接返回
            if len(self.features) == 0:
                return None, 1

            # 遍历所有已注册特征，找出最相似的用户
            min_dist = 999
            best_user = None
            for i, feat in enumerate(self.features):
                # 计算欧式距离，值越小越相似
                dist = np.linalg.norm(np.array(enc) - feat)
                if dist < min_dist:
                    min_dist = dist
                    best_user = self.users[i]

            # 阈值0.46：低于则认为是同一个人
            if min_dist < 0.46:
                return best_user, 1
            else:
                return None, 1
        except Exception as e:
            write_log(f"识别错误: {e}")
            return None, 0

# 创建人脸识别系统实例
face_sys = FaceSystem()

# ==============================================
# 前端网页模板（HTML+CSS+JS）
# 实现：摄像头显示、拍照、录入、识别、用户管理、日志查看
# ==============================================
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=yes">
    <title>人脸识别门禁系统</title>
    <style>
        /* 页面样式：美化界面，适配手机和电脑 */
        * {
            box-sizing: border-box;
        }
        body {
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: white;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            margin: 0;
            padding: 16px;
            min-height: 100vh;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        h1 {
            text-align: center;
            font-size: 1.8rem;
            margin-bottom: 20px;
            color: #0fdb7a;
        }
        .main-grid {
            display: flex;
            flex-wrap: wrap;
            gap: 20px;
        }
        .camera-panel {
            flex: 2;
            min-width: 280px;
            background: #0f0f1a;
            border-radius: 20px;
            padding: 20px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.3);
        }
        .control-panel {
            flex: 1;
            min-width: 260px;
            background: #0f0f1a;
            border-radius: 20px;
            padding: 20px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.3);
        }
        .video-container {
            position: relative;
            background: #000;
            border-radius: 16px;
            overflow: hidden;
            aspect-ratio: 4 / 3;
        }
        video, #previewCanvas {
            width: 100%;
            height: 100%;
            object-fit: cover;
        }
        /* 镜像翻转样式，让自拍更自然 */
        video {
            transform: scaleX(-1);
        }
        #previewCanvas {
            display: none;
            position: absolute;
            top: 0;
            left: 0;
            transform: scaleX(-1);
        }
        .btn {
            width: 100%;
            padding: 14px;
            margin: 8px 0;
            border: none;
            border-radius: 12px;
            font-size: 16px;
            font-weight: bold;
            cursor: pointer;
            transition: transform 0.1s, opacity 0.2;
        }
        .btn:active {
            transform: scale(0.98);
        }
        .btn-primary { background: #0d9488; color: white; }
        .btn-success { background: #10b981; color: white; }
        .btn-danger  { background: #ef4444; color: white; }
        .btn-warning { background: #f59e0b; color: white; }
        .btn-secondary { background: #3b82f6; color: white; }
        .btn-exit { background: #dc2626; color: white; margin-top: 15px; }
        .info-panel {
            background: #1e1e2e;
            border-radius: 16px;
            padding: 15px;
            margin: 15px 0;
        }
        .status { color: #0fdb7a; font-weight: bold; }
        .user-list {
            max-height: 200px;
            overflow-y: auto;
            background: #1a1a2a;
            border-radius: 12px;
            padding: 10px;
        }
        .user-item {
            padding: 8px;
            margin: 4px 0;
            background: #2a2a3a;
            border-radius: 8px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .delete-btn {
            background: #ef4444;
            border: none;
            color: white;
            padding: 4px 12px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 12px;
        }
        .tip { font-size: 12px; color: #aaa; margin-top: 10px; text-align: center; }
        .camera-buttons { display: flex; gap: 10px; margin-top: 15px; }
        .camera-buttons .btn { flex: 1; margin: 0; }
        .mirror-control { margin-top: 10px; text-align: center; }
        .mirror-btn {
            background: #4a5568;
            color: white;
            padding: 8px 16px;
            font-size: 14px;
            width: auto;
            display: inline-block;
        }
        @media (max-width: 768px) {
            body { padding: 12px; }
            .btn { padding: 12px; font-size: 14px; }
            h1 { font-size: 1.4rem; }
        }
    </style>
</head>
<body>
<div class="container">
    <h1>🔐 人脸识别门禁系统</h1>

    <div class="main-grid">
        <!-- 左侧：摄像头显示区域 -->
        <div class="camera-panel">
            <div class="video-container">
                <video id="video" autoplay playsinline muted></video>
                <canvas id="previewCanvas"></canvas>
            </div>
            <div class="camera-buttons">
                <button class="btn btn-secondary" id="startCameraBtn" onclick="startCamera()">📷 开启摄像头</button>
                <button class="btn btn-warning" id="switchCamBtn" onclick="switchCamera()" style="display:none">🔄 切换</button>
            </div>
            <div class="camera-buttons">
                <button class="btn btn-primary" id="captureBtn" onclick="capturePhoto()" disabled>📸 拍照</button>
            </div>
            <div class="mirror-control">
                <button class="btn mirror-btn" onclick="toggleMirror()">🪞 镜像翻转</button>
            </div>
            <div class="tip">
                💡 提示：点击"开启摄像头"后允许权限<br>
                📱 支持电脑和手机浏览器
            </div>
        </div>

        <!-- 右侧：功能控制区域 -->
        <div class="control-panel">
            <button class="btn btn-primary" onclick="showRegister()">📝 录入人脸</button>
            <button class="btn btn-success" onclick="doCheck()">✅ 开始打卡</button>
            <button class="btn btn-secondary" onclick="window.open('/log')">📋 查看日志</button>
            <button class="btn btn-exit" onclick="exitSystem()">🔴 退出系统</button>

            <div class="info-panel">
                <div>📊 状态：<span id="statusText" class="status">等待开启摄像头</span></div>
                <div>🎯 结果：<span id="resultText">{{ result }}</span></div>
            </div>

            <div style="margin-top: 20px;">
                <h4>👥 已注册用户 ({{ user_count }})</h4>
                <div class="user-list" id="userList">
                    {% for user in users %}
                    <div class="user-item">
                        <span>{{ user }}</span>
                        <button class="delete-btn" onclick="deleteUser('{{ user }}')">删除</button>
                    </div>
                    {% endfor %}
                </div>
            </div>
        </div>
    </div>
</div>

<script>
    // JS变量定义
    let video = document.getElementById('video');
    let previewCanvas = document.getElementById('previewCanvas');
    let stream = null;
    let currentImageData = null;
    let currentFacingMode = 'user';
    let isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
    let mirrorEnabled = true;  // 默认开启镜像
    
    // 移动端显示摄像头切换按钮
    if (isMobile) {
        document.getElementById('switchCamBtn').style.display = 'block';
    }
    
    // 切换镜像翻转功能
    function toggleMirror() {
        mirrorEnabled = !mirrorEnabled;
        if (mirrorEnabled) {
            video.style.transform = 'scaleX(-1)';
            previewCanvas.style.transform = 'scaleX(-1)';
            document.querySelector('.mirror-btn').style.background = '#4a5568';
            document.querySelector('.mirror-btn').innerHTML = '🪞 镜像翻转（开）';
        } else {
            video.style.transform = 'scaleX(1)';
            previewCanvas.style.transform = 'scaleX(1)';
            document.querySelector('.mirror-btn').style.background = '#2d3748';
            document.querySelector('.mirror-btn').innerHTML = '🪞 镜像翻转（关）';
        }
    }

    // 开启摄像头
    async function startCamera() {
        try {
            if (stream) {
                stream.getTracks().forEach(track => track.stop());
            }
            
            let constraints = {
                video: { width: { ideal: 1280 }, height: { ideal: 720 } },
                audio: false
            };
            
            // 移动端默认使用后置摄像头
            if (isMobile) {
                try {
                    constraints.video.facingMode = { exact: 'environment' };
                    currentFacingMode = 'environment';
                } catch(e) {}
            }
            
            stream = await navigator.mediaDevices.getUserMedia(constraints);
            video.srcObject = stream;
            await video.play();
            
            if (mirrorEnabled) {
                video.style.transform = 'scaleX(-1)';
            }
            
            document.getElementById('startCameraBtn').textContent = '✅ 摄像头工作中';
            document.getElementById('captureBtn').disabled = false;
            document.getElementById('statusText').innerHTML = '✅ 摄像头已就绪';
            
        } catch (err) {
            console.error('摄像头错误:', err);
            
            let errorMsg = '';
            if (err.name === 'NotAllowedError') {
                errorMsg = '❌ 摄像头权限被拒绝，请在浏览器设置中允许访问相机';
            } else if (err.name === 'NotFoundError') {
                errorMsg = '❌ 未检测到摄像头设备';
            } else if (err.name === 'NotReadableError') {
                errorMsg = '❌ 摄像头被其他应用占用';
            } else {
                // 降级模式：简化权限请求
                try {
                    stream = await navigator.mediaDevices.getUserMedia({ video: true });
                    video.srcObject = stream;
                    await video.play();
                    if (mirrorEnabled) {
                        video.style.transform = 'scaleX(-1)';
                    }
                    document.getElementById('statusText').innerHTML = '✅ 摄像头已就绪（降级模式）';
                    document.getElementById('captureBtn').disabled = false;
                    return;
                } catch(e) {
                    errorMsg = '❌ 无法打开摄像头：' + err.message;
                }
            }
            
            document.getElementById('statusText').innerHTML = errorMsg;
            alert(errorMsg);
        }
    }
    
    // 手机端切换前后摄像头
    async function switchCamera() {
        currentFacingMode = currentFacingMode === 'user' ? 'environment' : 'user';
        
        try {
            if (stream) {
                stream.getTracks().forEach(track => track.stop());
            }
            
            const constraints = {
                video: { facingMode: { exact: currentFacingMode } },
                audio: false
            };
            
            stream = await navigator.mediaDevices.getUserMedia(constraints);
            video.srcObject = stream;
            await video.play();
            
            if (mirrorEnabled) {
                video.style.transform = 'scaleX(-1)';
            }
            
            document.getElementById('statusText').innerHTML = `✅ 已切换到${currentFacingMode === 'user' ? '前置' : '后置'}摄像头`;
        } catch (err) {
            try {
                const constraints = { video: { facingMode: currentFacingMode } };
                stream = await navigator.mediaDevices.getUserMedia(constraints);
                video.srcObject = stream;
                await video.play();
                if (mirrorEnabled) {
                    video.style.transform = 'scaleX(-1)';
                }
                document.getElementById('statusText').innerHTML = `✅ 已切换`;
            } catch(e) {
                alert('切换失败');
                startCamera();
            }
        }
    }

    // 拍照功能，将画面转为base64图片
    function capturePhoto() {
        if (!video.srcObject) {
            alert('请先开启摄像头');
            return;
        }
        
        const tempCanvas = document.createElement('canvas');
        tempCanvas.width = video.videoWidth;
        tempCanvas.height = video.videoHeight;
        const ctx = tempCanvas.getContext('2d');
        
        if (mirrorEnabled) {
            ctx.translate(tempCanvas.width, 0);
            ctx.scale(-1, 1);
        }
        ctx.drawImage(video, 0, 0, tempCanvas.width, tempCanvas.height);
        
        currentImageData = tempCanvas.toDataURL('image/jpeg', 0.8);
        
        // 拍照预览闪烁效果
        previewCanvas.width = tempCanvas.width;
        previewCanvas.height = tempCanvas.height;
        let previewCtx = previewCanvas.getContext('2d');
        if (mirrorEnabled) {
            previewCtx.translate(previewCanvas.width, 0);
            previewCtx.scale(-1, 1);
        }
        previewCtx.drawImage(video, 0, 0, previewCanvas.width, previewCanvas.height);
        previewCanvas.style.display = 'block';
        setTimeout(() => { previewCanvas.style.display = 'none'; }, 300);
        
        return currentImageData;
    }

    // 人脸录入功能
    async function showRegister() {
        if (!video.srcObject) {
            alert('请先开启摄像头');
            return;
        }
        
        const name = prompt('请输入姓名（用于注册）');
        if (!name || !name.trim()) return;
        
        const imageData = capturePhoto();
        if (!imageData) {
            alert('拍照失败，请重试');
            return;
        }
        
        document.getElementById('statusText').innerHTML = '正在录入中...';
        
        try {
            const response = await fetch('/api/register', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name: name.trim(), image: imageData })
            });
            const data = await response.json();
            alert(data.message);
            if (data.success) {
                location.reload();
            }
            document.getElementById('statusText').innerHTML = data.success ? '✅ 录入成功' : '❌ 录入失败';
        } catch (err) {
            alert('网络错误：' + err.message);
            document.getElementById('statusText').innerHTML = '❌ 网络错误';
        }
    }

    // 人脸识别打卡
    async function doCheck() {
        if (!video.srcObject) {
            alert('请先开启摄像头');
            return;
        }
        
        const imageData = capturePhoto();
        if (!imageData) {
            alert('拍照失败');
            return;
        }
        
        document.getElementById('statusText').innerHTML = '识别中...';
        document.getElementById('resultText').innerHTML = '识别中...';
        
        try {
            const response = await fetch('/api/recognize', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ image: imageData })
            });
            const data = await response.json();
            
            if (data.success && data.user) {
                document.getElementById('resultText').innerHTML = `✅ 打卡成功：${data.user}<br>⏰ ${data.time}`;
                document.getElementById('statusText').innerHTML = '✅ 识别成功';
                alert(`打卡成功！欢迎 ${data.user}`);
            } else {
                document.getElementById('resultText').innerHTML = data.message || '识别失败';
                document.getElementById('statusText').innerHTML = '❌ 识别失败';
                alert(data.message || '识别失败，请确保已注册并正对摄像头');
            }
        } catch (err) {
            alert('网络错误：' + err.message);
            document.getElementById('statusText').innerHTML = '❌ 网络错误';
        }
    }

    // 删除用户
    async function deleteUser(name) {
        if (!confirm(`确定删除用户「${name}」吗？`)) return;
        
        try {
            const response = await fetch('/api/delete', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name: name })
            });
            const data = await response.json();
            alert(data.message);
            if (data.success) location.reload();
        } catch (err) {
            alert('删除失败：' + err.message);
        }
    }
    
    // 退出系统，关闭服务器
    async function exitSystem() {
        if (confirm('确定要退出系统吗？服务端将停止运行，所有设备将无法访问。')) {
            try {
                await fetch('/api/shutdown', { method: 'POST' });
                alert('系统正在关闭...');
                if (stream) {
                    stream.getTracks().forEach(track => track.stop());
                }
                setTimeout(() => { window.close(); }, 500);
            } catch(err) {
                alert('系统已关闭');
                window.close();
            }
        }
    }

    // 页面加载完成自动开启摄像头
    window.addEventListener('load', () => {
        startCamera();
    });
    
    // 页面关闭时释放摄像头
    window.addEventListener('beforeunload', () => {
        if (stream) {
            stream.getTracks().forEach(track => track.stop());
        }
    });
</script>
</body>
</html>
'''

# ==============================================
# Flask 路由（后端接口，处理前端请求）
# ==============================================

# 首页：显示系统主界面
@app.route('/')
def index():
    users = face_sys.get_user_list()
    return render_template_string(HTML_TEMPLATE, users=users, user_count=len(users), result="")

# 日志页面：查看系统操作记录
@app.route('/log')
def log_page():
    try:
        with open("log.txt", "r", encoding="utf-8") as f:
            logs = f.read()
    except:
        logs = "暂无日志"
    return render_template_string('''
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>系统日志</title>
    <meta http-equiv="refresh" content="60">
    <style>
        body{background:#1a1a2e;color:#fff;padding:20px;font-family:monospace}
        pre{background:#0f0f1a;padding:20px;border-radius:12px;overflow-x:auto}
        a{color:#0fdb7a}
        .back-btn{background:#3b82f6;color:white;padding:10px 20px;border:none;border-radius:8px;cursor:pointer;margin-bottom:20px}
    </style>
</head>
<body>
    <button class="back-btn" onclick="location.href='/'">← 返回首页</button>
    <pre>{{ logs }}</pre>
</body>
</html>''', logs=logs)

# 系统状态接口
@app.route('/api/status')
def api_status():
    return jsonify({'status': 'running', 'users': len(face_sys.get_user_list())})

# 人脸注册接口
@app.route('/api/register', methods=['POST'])
def api_register():
    data = request.get_json()
    name = data.get('name', '').strip()
    image = data.get('image', '')
    
    if not name:
        return jsonify({'success': False, 'message': '姓名不能为空'})
    
    if face_sys.save_face(name, image):
        return jsonify({'success': True, 'message': f'用户 {name} 录入成功'})
    else:
        return jsonify({'success': False, 'message': '录入失败，请确保正对摄像头且只有一张人脸'})

# 人脸识别接口
@app.route('/api/recognize', methods=['POST'])
def api_recognize():
    data = request.get_json()
    image = data.get('image', '')
    
    if not image:
        return jsonify({'success': False, 'message': '无图像数据'})
    
    user, code = face_sys.recognize(image)
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    if code == 0:
        return jsonify({'success': False, 'message': '未检测到人脸'})
    elif code == 2:
        return jsonify({'success': False, 'message': '检测到多张人脸，请确保只有您一人'})
    elif user:
        write_log(f"{user} 打卡成功 {now}")
        return jsonify({'success': True, 'user': user, 'time': now, 'message': f'打卡成功：{user}'})
    else:
        write_log(f"打卡失败（未识别）")
        return jsonify({'success': False, 'message': '未识别，请确保已注册'})

# 删除用户接口
@app.route('/api/delete', methods=['POST'])
def api_delete():
    data = request.get_json()
    name = data.get('name', '').strip()
    
    if face_sys.delete_face(name):
        return jsonify({'success': True, 'message': f'已删除 {name}'})
    else:
        return jsonify({'success': False, 'message': '删除失败'})

# 关闭系统接口
@app.route('/api/shutdown', methods=['POST'])
def api_shutdown():
    write_log("用户手动退出系统")
    def shutdown():
        time.sleep(0.5)
        os._exit(0)
    threading.Thread(target=shutdown).start()
    return jsonify({'success': True, 'message': '系统正在关闭'})

# ==============================================
# 程序主入口：启动Web服务
# ==============================================
if __name__ == '__main__':
    # 获取本机IP地址，方便局域网访问
    hostname = socket.gethostname()
    try:
        local_ip = socket.gethostbyname(hostname)
    except:
        local_ip = "127.0.0.1"
    
    write_log("系统启动")
    # 控制台输出访问地址
    print("\n" + "="*60)
    print("🚀 人脸识别门禁系统已启动")
    print(f"📱 本机访问: http://127.0.0.1:5000")
    print(f"🌐 局域网访问: http://{local_ip}:5000")
    print("="*60)
    print("\n💡 其他设备访问方法：")
    print("   1. 确保手机和电脑在同一WiFi")
    print("   2. 手机浏览器打开 http://" + local_ip + ":5000")
    print("   3. 点击「开启摄像头」并允许权限")
    print("="*60)
    print("\n🔐 如需不同网络访问（手机流量也能用），请使用内网穿透：")
    print("   方案1 - cpolar: cpolar http 5000")
    print("   方案2 - ngrok:  ngrok http 5000")
    print("   方案3 - frp:    frpc 配置后使用")
    print("="*60 + "\n")
    
    # 自动打开浏览器
    webbrowser.open(f'http://127.0.0.1:5000')
    
    # 启动Flask服务，允许局域网所有设备访问
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
    app.run(host='0.0.0.0', port=5000, ssl_context=('server.crt', 'server.key'))
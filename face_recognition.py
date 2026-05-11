import os
import cv2
import dlib
import numpy as np
from imutils import paths
from PIL import Image, ImageDraw, ImageFont  # 新增：用于渲染中文

# ====================== 人脸识别类 ======================
class FaceRecognition:
    def __init__(self):
        # 加载dlib模型
        self.detector = dlib.get_frontal_face_detector()
        self.predictor = dlib.shape_predictor('./shape_predictor_68_face_landmarks.dat')
        self.face_model = dlib.face_recognition_model_v1('./dlib_face_recognition_resnet_model_v1.dat')
        
        # 加载已保存的人脸特征
        self.known_features = []  # 存储特征
        self.known_names = []     # 存储姓名
        self.load_features()

    def load_features(self):
        """加载facedata里的所有CSV特征文件"""
        if not os.path.exists('./facedata'):
            print("❌ 未找到facedata文件夹，请先运行register.py")
            return

        # 获取所有csv文件
        csv_paths = list(paths.list_files('./facedata', validExts=('.csv')))
        
        for path in csv_paths:
            # 读取特征
            feature = np.loadtxt(path, delimiter=',')
            self.known_features.append(feature)
            
            # 获取姓名（文件名=姓名）
            name = os.path.basename(path).split('.')[0]
            self.known_names.append(name)
        
        print(f"✅ 已加载 {len(self.known_names)} 个人脸数据")

    def get_feature(self, face_img_rgb):
        """提取单张人脸的128D特征"""
        face_rect = self.detector(face_img_rgb, 0)
        if len(face_rect) == 0:
            return None
        shape = self.predictor(face_img_rgb, face_rect[0])
        feature = np.array(self.face_model.compute_face_descriptor(face_img_rgb, shape))
        return feature

    def compare(self, feature1, feature2, threshold=0.5):
        """欧式距离比对，越小越像，阈值0.5"""
        distance = np.linalg.norm(feature1 - feature2)
        return distance < threshold, distance

    def cv2_add_chinese_text(self, img, text, pos, font_size=30, font_color=(0, 255, 0)):
        """在OpenCV图像上添加中文文字（解决乱码）"""
        # 转换为PIL格式
        img_pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        # 加载字体（Windows默认字体路径）
        font = ImageFont.truetype("simsun.ttc", font_size, encoding="utf-8")
        # 创建画笔
        draw = ImageDraw.Draw(img_pil)
        # 绘制文字
        draw.text(pos, text, font=font, fill=font_color)
        # 转回OpenCV格式
        return cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)

    def run_recognition(self):
        """启动实时人脸识别界面"""
        cap = cv2.VideoCapture(0)
        print("🎥 人脸识别已启动，按 Q 退出")

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            frame = cv2.flip(frame, 1)  # 镜像
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            faces = self.detector(rgb_frame, 0)

            # 遍历检测到的人脸
            for face in faces:
                x1, y1, x2, y2 = face.left(), face.top(), face.right(), face.bottom()
                shape = self.predictor(rgb_frame, face)
                now_feature = np.array(self.face_model.compute_face_descriptor(rgb_frame, shape))

                name = "Unknown"
                min_dist = 999

                # 和所有已知特征比对
                for i, known_feat in enumerate(self.known_features):
                    is_match, dist = self.compare(now_feature, known_feat)
                    if is_match and dist < min_dist:
                        min_dist = dist
                        name = self.known_names[i]

                # 绘制框
                if name == "Unknown":
                    color = (0, 0, 255)  # 红色：陌生人
                else:
                    color = (0, 255, 0)  # 绿色：已注册

                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                
                # ✅ 修复：用PIL渲染中文名字
                if name != "Unknown":
                    frame = self.cv2_add_chinese_text(frame, name, (x1, y1 - 35), font_size=25, font_color=color)
                else:
                    cv2.putText(frame, name, (x1, y1 - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

            # ✅ 修复：窗口标题用英文避免乱码
            frame = self.cv2_add_chinese_text(frame, "Face Recognition System", (20, 30), font_size=30, font_color=(255, 255, 0))
            frame = self.cv2_add_chinese_text(frame, "Press Q to quit", (20, 70), font_size=25, font_color=(255, 255, 255))
            cv2.imshow("Face Recognition System", frame)  # 英文标题

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        cap.release()
        cv2.destroyAllWindows()

# ====================== 运行 ======================
if __name__ == '__main__':
    rec = FaceRecognition()
    rec.run_recognition()
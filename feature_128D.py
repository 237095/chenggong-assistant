import os
import cv2
import dlib
import numpy as np
from pathlib import Path
import shutil

class GetFaceFeature:
    def __init__(self, faces_path):
        self.faces_path = faces_path

    def mkFile(self):
        # 创建facedata文件夹（不删除原有，避免误删数据）
        if not os.path.exists('facedata'):
            os.mkdir('facedata')

    def cv_imread(self, filepath):
        # 支持中文路径读取图片
        return cv2.imdecode(np.fromfile(filepath, dtype=np.uint8), cv2.IMREAD_COLOR)

    def Feature128D(self):
        self.mkFile()

        # 加载模型
        detector = dlib.get_frontal_face_detector()
        predictor = dlib.shape_predictor('./shape_predictor_68_face_landmarks.dat')
        face_model = dlib.face_recognition_model_v1('./dlib_face_recognition_resnet_model_v1.dat')

        # 遍历 faces 目录下的所有图片
        for filename in os.listdir(self.faces_path):
            try:
                # 只处理图片
                if not filename.endswith(('.jpg','.jpeg','.png','.bmp')):
                    continue

                img_path = os.path.join(self.faces_path, filename)
                img = self.cv_imread(img_path)
                rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

                # 检测人脸
                faces = detector(rgb, 0)
                if len(faces) == 0:
                    print(f"未检测到人脸：{filename}")
                    continue

                # 提取特征
                shape = predictor(rgb, faces[0])
                feat = face_model.compute_face_descriptor(rgb, shape)
                feat_np = np.array(feat)

                # 保存CSV（用图片名作为姓名）
                name = Path(filename).stem
                save_path = f"facedata/{name}.csv"
                np.savetxt(save_path, feat_np, delimiter=',')
                print(f"✅ 已生成特征：{save_path}")

            except Exception as e:
                print(f"❌ 处理失败：{filename} => {e}")

    def runFace(self):
        self.Feature128D()

if __name__ == '__main__':
    # 从 ./faces 读取图片 → 生成特征到 ./facedata
    extractor = GetFaceFeature("./faces")
    extractor.runFace()
import os
import cv2
import dlib
from pathlib import Path
import shutil
from feature_128D import GetFaceFeature  # 导入特征提取类
import numpy as np

class FaceRegister:
    def __init__(self,pic_path):
        '''
        初始化：接收人脸保存路径，创建人脸检测器，清理/创建保存目录
        :param pic_path: 人脸图片保存路径（如 ./faces）
        '''
        self.pic_path = pic_path
        self.detector = dlib.get_frontal_face_detector()  # dlib人脸检测器
        self.mkfile()  # 初始化时清理/创建目录
        
    def mkfile(self):
        """
        注册前清理目录：确保目录为空，避免旧数据干扰
        """
        path = Path(self.pic_path)
        if not path.exists():
            os.makedirs(self.pic_path)  # 不存在则创建
        else:
            shutil.rmtree(self.pic_path)  # 存在则删除重建
            os.makedirs(self.pic_path)
            
    def cv_imwrite(self,filepath,img):
        """
        支持中文路径保存图片：cv2.imwrite不支持中文路径，用imencode+tofile绕过
        :param filepath: 保存路径（含中文）
        :param img: 要保存的图像
        """
        cv_imw = cv2.imencode('.jpg',img)[1].tofile(filepath)
        return cv_imw
    
    def faceIn(self, pic, face_frame):
        """
        在图像上绘制人脸框和提示文字
        :param pic: 原始图像
        :param face_frame: dlib检测到的人脸框列表
        """
        if len(face_frame) == 0:
            cv2.putText(pic, "No face!", (100, 200), cv2.FONT_HERSHEY_COMPLEX, 1.0, (0, 0, 255), 1, cv2.LINE_AA)
        
        for _, face in enumerate(face_frame):
            # 获取人脸框坐标
            left = face.left()
            right = face.right()
            top = face.top()
            bottom = face.bottom()
            # 绘制绿色人脸框
            cv2.rectangle(pic, pt1=(left, top), pt2=(right, bottom), color=(0, 255, 0), thickness=2)

    def getFaceInCam(self):
        '''
        摄像头采集人脸：实时预览、按键采集、绘制提示
        '''
        count = 0  # 采集计数
        cap = cv2.VideoCapture(0)  # 打开默认摄像头
        while True:
            ret,frame = cap.read()  # 读取一帧
            frame = cv2.flip(frame,1)  # 水平翻转，符合自拍习惯
            face_color = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # dlib需要RGB格式
            title = 'Face Register'
            data = self.detector(face_color)  # 检测人脸
            press = cv2.waitKey(1)  # 监听按键
            
            # 无人脸提示
            if len(data) ==0:
                cv2.putText (frame, "No face Found!", (100,200),cv2.FONT_ITALIC, 1.0, (0, 0, 255), 1, cv2.LINE_AA)
            # 按Q退出
            if press == ord('q'):
                break
            # 按C采集人脸
            if press == ord('c'):
                if len(data) == 0:
                    cv2.putText (frame, "No face Found!", (100,200),cv2.FONT_ITALIC, 1.0, (0, 0, 255), 1, cv2.LINE_AA)
                elif len(data) > 1:
                    cv2.putText (frame, "Too Many Faces!", (100,200),cv2.FONT_ITALIC, 1.0, (0, 0, 255), 1, cv2.LINE_AA)
                else:
                    count += 1
                    face_name = input('准备开始录入，请输入你的名字：')
                    # 命名规则：姓名.计数.jpg（如 张三.1.jpg）
                    impath=self.pic_path + "/" + str(face_name) +'.' + str(count) +'.jpg'
                    print("save picture %s" %impath)
                    self.cv_imwrite(str(impath),frame)  # 保存图片（支持中文）
            
            self.faceIn(frame,data)  # 绘制人脸框
            # 显示操作提示
            cv2.putText(frame, 'Type C:Collect', (20, 30), cv2.FONT_ITALIC, 0.8, (255, 0, 255), 1, cv2.LINE_AA)
            cv2.putText(frame, 'Type Q:Quit', (20, 60), cv2.FONT_ITALIC, 0.8, (255, 0, 255), 1, cv2.LINE_AA)
            cv2.putText(frame, 'Collect faces Number:%s' % count, (20, 90), cv2.FONT_ITALIC, 0.8, (255, 0, 255), 1, cv2.LINE_AA)
            cv2.imshow(title, frame)  # 显示窗口
            
        cap.release()  # 释放摄像头
        cv2.destroyAllWindows()  # 关闭所有窗口
    
def main():
    pic_path = './faces'
    FaceAPP= FaceRegister(pic_path)
    FaceAPP.getFaceInCam()  # 启动人脸采集
    
    # 采集完成后自动提取128D特征
    getFeature128D = GetFaceFeature(pic_path)
    getFeature128D.runFace()

if __name__ == "__main__":
    main()
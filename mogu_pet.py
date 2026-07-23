import sys
import os
import json
import random
import time
import math
from PyQt6.QtWidgets import QApplication, QWidget, QMenu, QInputDialog
from PyQt6.QtGui import QPixmap, QPainter, QFont, QColor, QBrush, QPen
from PyQt6.QtCore import Qt, QPoint, QTimer, QRect

# ===== 配置区 =====
def get_resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

def get_config_path():
    """配置文件保存路径（用户目录）"""
    config_dir = os.path.join(os.path.expanduser("~"), ".mogu_pet")
    os.makedirs(config_dir, exist_ok=True)
    return os.path.join(config_dir, "config.json")

IMAGE_PATH = get_resource_path("mogu.png")
CONFIG_PATH = get_config_path()

# ========== INTJ风格暖心对话库 ==========
# 分类：问候、鼓励、摸鱼吐槽、休息提醒、安慰、深夜、冷幽默、效率、互动
TALK_CATEGORIES = {
    "greeting": [  # 日常问候
        "来了。",
        "开始吧。",
        "今天效率如何？",
        "又见面了。",
        "继续昨天的计划？",
        "准备好了叫我。",
        "新的一天，别浪费。",
        "按计划进行。",
    ],
    "encourage": [  # 理性鼓励
        "进度不错，继续。",
        "你比昨天更强了一点。",
        "坚持住，终点不远。",
        "逻辑没问题，执行就好。",
        "想清楚了就去做。",
        "你已经做得很好了。",
        "困难只是暂时的，方法总比问题多。",
        "专注当下，一步一步来。",
        "别慌，问题总能解决。",
        "你的努力不会白费。",
    ],
    "moyu": [  # 摸鱼吐槽（INTJ式毒舌）
        "又在摸鱼？",
        "进度条不动了。",
        "休息够了就回来。",
        "别让我提醒你第二遍。",
        "注意力，收回来。",
        "五分钟到了。",
        "再摸鱼今天计划完不成了。",
        "我看着你呢。",
        "该收心了。",
        "摸鱼一时爽，收尾火葬场。",
    ],
    "rest": [  # 休息提醒
        "该休息了，效率会下降。",
        "起来走走，颈椎要紧。",
        "喝杯水。",
        "眼睛累了就歇会。",
        "劳逸结合，不是偷懒。",
        "休息是为了更好地工作。",
        "眯五分钟也行。",
        "站起来活动一下。",
    ],
    "comfort": [  # 暖心安慰
        "没关系，重新来就好。",
        "出错很正常，下次注意。",
        "你已经尽力了。",
        "不用逼自己太紧。",
        "我在这陪着你。",
        "难过的话就歇一会。",
        "一切都会过去的。",
        "你不是一个人。",
        "失败是数据，不是定论。",
        "累了就歇，没人怪你。",
    ],
    "night": [  # 深夜陪伴
        "还不睡？",
        "熬夜效率很低的。",
        "该结束今天了。",
        "晚安，明天继续。",
        "记得定闹钟。",
        "深夜适合思考，但别太久。",
        "做完这一项就去睡吧。",
        "再熬就不聪明了。",
        "明天的事明天再说。",
    ],
    "humor": [  # 冷幽默
        "……",
        "我就静静看着。",
        "有趣。",
        "你的操作我看不懂。",
        "哼。",
        "随便你。",
        "行吧。",
        "人类真奇怪。",
        "哦。",
        "所以呢？",
    ],
    "efficiency": [  # 效率提醒
        "优先级排好了吗？",
        "先做最重要的事。",
        "别在小事上浪费时间。",
        "专注一件事。",
        "目标明确了吗？",
        "计划赶不上变化？那就改计划。",
        "时间是有限的。",
        "别纠结，选一个方向。",
        "减少无效动作。",
    ],
    "interact": [  # 点击互动
        "嗯？",
        "怎么了？",
        "有事说事。",
        "别戳了。",
        "再戳我就扁了。",
        "你很闲？",
        "好吧，陪你玩一会。",
        "手感怎么样？",
        "又戳。",
        "无聊？",
    ]
}

# 所有对话汇总
ALL_TALKS = []
for talks in TALK_CATEGORIES.values():
    ALL_TALKS.extend(talks)

BASE_WIDTH = 180
# =================


class MoguPet(QWidget):
    def __init__(self):
        super().__init__()
        self.scale = 1.0
        self.base_w = BASE_WIDTH
        self.base_h = BASE_WIDTH
        self.config = self._load_config()

        # 窗口设置
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # 加载图片
        self.img = QPixmap(IMAGE_PATH)
        if self.img.isNull():
            raise FileNotFoundError(f"找不到图片文件：mogu.png")
        self.base_h = int(self.base_w * self.img.height() / self.img.width())

        # 拖动
        self.dragging = False
        self.drag_offset = QPoint()
        self.click_time = 0  # 双击判断

        # 气泡
        self.bubble_text = ""
        self.bubble_timer = QTimer(self)
        self.bubble_timer.setSingleShot(True)
        self.bubble_timer.timeout.connect(self._hide_bubble)

        # 主动画
        self.anim_timer = QTimer(self)
        self.anim_timer.timeout.connect(self._anim_tick)
        self.anim_type = None
        self.anim_frame = 0
        self.original_geom = None
        self.anim_rotation = 0

        # 闲置呼吸动画
        self.idle_phase = 0.0
        self.idle_timer = QTimer(self)
        self.idle_timer.timeout.connect(self._idle_tick)
        self.idle_timer.start(50)
        self.last_interact_time = time.time()

        # 闲置小动作定时器
        self.idle_action_timer = QTimer(self)
        self.idle_action_timer.timeout.connect(self._trigger_idle_action)
        self.idle_action_timer.start(4000)

        # 应用配置
        self._apply_config()
        self._apply_scale()

    # ========== 配置读写 ==========
    def _load_config(self):
        default = {
            "scale": 1.0,
            "pos_x": None,
            "pos_y": None,
            "stay_on_top": True
        }
        try:
            if os.path.exists(CONFIG_PATH):
                with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                    default.update(saved)
        except:
            pass
        return default

    def _save_config(self):
        self.config["scale"] = self.scale
        self.config["pos_x"] = self.x()
        self.config["pos_y"] = self.y()
        self.config["stay_on_top"] = self._is_stay_on_top()
        try:
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=2)
        except:
            pass

    def _apply_config(self):
        self.scale = self.config.get("scale", 1.0)
        if not self.config.get("stay_on_top", True):
            self._toggle_stay_on_top()

    # ========== 大小与绘制 ==========
    def _apply_scale(self):
        w = int(self.base_w * self.scale)
        h = int(self.base_h * self.scale)
        self.pet_img = self.img.scaled(
            w, h,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self.bubble_space = int(45 * self.scale)
        self.resize(w, h + self.bubble_space)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        pet_y = self.bubble_space

        # 呼吸浮动效果（仅闲置时）
        float_offset = 0
        if self.anim_type is None:
            float_offset = int(3 * self.scale * math.sin(self.idle_phase))

        # 旋转变换
        if self.anim_rotation != 0:
            painter.save()
            cx = self.width() / 2
            cy = pet_y + self.pet_img.height() / 2
            painter.translate(cx, cy + float_offset)
            painter.rotate(self.anim_rotation)
            painter.translate(-cx, -cy - float_offset)

        painter.drawPixmap(0, pet_y + float_offset, self.pet_img)

        if self.anim_rotation != 0:
            painter.restore()

        # 对话气泡
        if self.bubble_text:
            font = QFont("微软雅黑", int(11 * self.scale))
            painter.setFont(font)
            fm = painter.fontMetrics()
            text_w = fm.horizontalAdvance(self.bubble_text)
            text_h = fm.height()

            pad_x, pad_y = 12, 7
            bubble_w = text_w + pad_x * 2
            bubble_h = text_h + pad_y * 2

            bx = (self.width() - bubble_w) // 2
            by = 0

            painter.setBrush(QBrush(QColor(255, 255, 255, 245)))
            painter.setPen(QPen(QColor(210, 210, 210), 1))
            painter.drawRoundedRect(QRect(bx, by, bubble_w, bubble_h), 10, 10)

            # 气泡尖角
            tip_x = self.width() // 2
            tip_y = bubble_h
            points = [
                QPoint(tip_x - 6, tip_y),
                QPoint(tip_x + 6, tip_y),
                QPoint(tip_x, tip_y + 8)
            ]
            painter.setBrush(QBrush(QColor(255, 255, 255, 245)))
            painter.setPen(QPen(QColor(210, 210, 210), 1))
            painter.drawPolygon(*points)

            painter.setPen(QColor(60, 60, 60))
            painter.drawText(
                bx + pad_x,
                by + pad_y + fm.ascent(),
                self.bubble_text
            )

    # ========== 闲置动画 ==========
    def _idle_tick(self):
        """呼吸浮动"""
        self.idle_phase += 0.05
        if self.idle_phase > math.pi * 2:
            self.idle_phase = 0
        if self.anim_type is None:
            self.update()

    def _trigger_idle_action(self):
        """触发闲置小动作"""
        if self.anim_type is not None:
            return
        idle_time = time.time() - self.last_interact_time
        if idle_time < 8:  # 8秒没互动才触发
            return

        if random.random() < 0.35:
            action = random.choice(["blink", "look_around", "stretch", "sigh"])
            self._play_idle_action(action)

    def _play_idle_action(self, action_type):
        if self.anim_timer.isActive():
            return
        self.original_geom = self.geometry()
        self.anim_frame = 0
        self.anim_type = f"idle_{action_type}"
        self.anim_timer.start(40)

    # ========== 鼠标交互 ==========
    def mousePressEvent(self, event):
        now = time.time()
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = True
            self.drag_offset = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            self.last_interact_time = time.time()

            # 双击判断
            if now - self.click_time < 0.35:
                self._play_double_click_action()
            else:
                self._play_random_action()
            self.click_time = now

        elif event.button() == Qt.MouseButton.RightButton:
            self._show_right_menu(event.globalPosition().toPoint())

    def mouseMoveEvent(self, event):
        if self.dragging and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_offset)

    def mouseReleaseEvent(self, event):
        if self.dragging:
            self._save_config()
        self.dragging = False

    def wheelEvent(self, event):
        if event.angleDelta().y() > 0:
            self.scale = min(self.scale + 0.08, 3.0)
        else:
            self.scale = max(self.scale - 0.08, 0.3)
        self._apply_scale()
        self._save_config()

    # ========== 右键菜单 ==========
    def _show_right_menu(self, pos):
        menu = QMenu(self)

        if self._is_stay_on_top():
            act_top = menu.addAction("✓ 始终置顶")
        else:
            act_top = menu.addAction("始终置顶")

        size_menu = menu.addMenu("调整大小")
        act_small = size_menu.addAction("缩小")
        act_big = size_menu.addAction("放大")
        act_reset = size_menu.addAction("恢复默认大小")

        menu.addSeparator()
        act_talk = menu.addAction("说点什么")
        act_custom = menu.addAction("自定义对话...")

        menu.addSeparator()
        act_exit = menu.addAction("退出程序")

        choice = menu.exec(pos)

        if choice == act_top:
            self._toggle_stay_on_top()
            self._save_config()
        elif choice == act_big:
            self.scale = min(self.scale + 0.2, 3.0)
            self._apply_scale()
            self._save_config()
        elif choice == act_small:
            self.scale = max(self.scale - 0.2, 0.3)
            self._apply_scale()
            self._save_config()
        elif choice == act_reset:
            self.scale = 1.0
            self._apply_scale()
            self._save_config()
        elif choice == act_talk:
            self._show_bubble(random.choice(ALL_TALKS))
        elif choice == act_custom:
            text, ok = QInputDialog.getText(self, "自定义对话", "输入想让它说的话：")
            if ok and text.strip():
                self._show_bubble(text.strip())
        elif choice == act_exit:
            self._save_config()
            self.close()

    def _is_stay_on_top(self):
        return bool(self.windowFlags() & Qt.WindowType.WindowStaysOnTopHint)

    def _toggle_stay_on_top(self):
        flags = self.windowFlags()
        if self._is_stay_on_top():
            flags &= ~Qt.WindowType.WindowStaysOnTopHint
        else:
            flags |= Qt.WindowType.WindowStaysOnTopHint
        self.setWindowFlags(flags)
        self.show()

    # ========== 对话气泡 ==========
    def _show_bubble(self, text, duration=2500):
        self.bubble_text = text
        self.bubble_timer.start(duration)
        self.update()

    def _hide_bubble(self):
        self.bubble_text = ""
        self.update()

    def _get_talk_by_time(self):
        """根据时间段选不同分类的对话"""
        hour = time.localtime().tm_hour
        if hour >= 23 or hour < 5:
            category = "night"
        elif hour >= 5 and hour < 10:
            category = "greeting"
        else:
            category = random.choice([
                "encourage", "moyu", "rest", "efficiency", "humor", "comfort"
            ])
        return random.choice(TALK_CATEGORIES[category])

    # ========== 互动动画 ==========
    def _play_random_action(self):
        self._show_bubble(random.choice(TALK_CATEGORIES["interact"]))

        if self.anim_timer.isActive():
            self.anim_timer.stop()
            self.setGeometry(self.original_geom)
            self.anim_rotation = 0

        self.original_geom = self.geometry()
        self.anim_frame = 0
        self.anim_rotation = 0
        # 7种互动动画
        self.anim_type = random.choice([
            "jump", "squash", "shake", "wave", "nod", "spin", "tilt"
        ])
        self.anim_timer.start(30)

    def _play_double_click_action(self):
        """双击：蹦跶两下 + 时段暖心话"""
        self._show_bubble(self._get_talk_by_time(), 3000)

        if self.anim_timer.isActive():
            self.anim_timer.stop()
            self.setGeometry(self.original_geom)

        self.original_geom = self.geometry()
        self.anim_frame = 0
        self.anim_type = "double_jump"
        self.anim_timer.start(25)

    def _anim_tick(self):
        self.anim_frame += 1
        g = self.original_geom

        # ===== 7种互动动画 =====
        if self.anim_type == "jump":
            if self.anim_frame <= 22:
                t = self.anim_frame / 22
                jump_h = 70 * self.scale
                offset_y = -4 * jump_h * t * (t - 1)
                self.move(g.x(), g.y() - int(offset_y))
            else:
                self._end_animation()

        elif self.anim_type == "squash":
            if self.anim_frame <= 26:
                t = self.anim_frame / 26
                s = 0.28 * (t / 0.4) if t < 0.4 else 0.28 * (1 - (t - 0.4) / 0.6)
                sy, sx = 1 - s, 1 + s * 0.4
                new_w = int(self.base_w * self.scale * sx)
                new_h = int(self.base_h * self.scale * sy)
                self.pet_img = self.img.scaled(new_w, new_h,
                    Qt.AspectRatioMode.IgnoreAspectRatio,
                    Qt.TransformationMode.SmoothTransformation)
                new_total_h = new_h + self.bubble_space
                self.resize(new_w, new_total_h)
                self.move(g.x() - (new_w - g.width()) // 2, g.bottom() - new_total_h)
                self.update()
            else:
                self._apply_scale()
                self.setGeometry(self.original_geom)
                self._end_animation()

        elif self.anim_type == "shake":
            if self.anim_frame <= 18:
                offsets = [10, -10, 8, -8, 5, -5, 3, -3, 0]
                idx = min(self.anim_frame - 1, len(offsets) - 1)
                self.move(g.x() + int(offsets[idx] * self.scale), g.y())
            else:
                self._end_animation()

        elif self.anim_type == "wave":
            # 挥手（左右摇摆）
            if self.anim_frame <= 24:
                t = self.anim_frame / 24
                self.anim_rotation = 8 * self.scale * math.sin(t * math.pi * 3)
                self.update()
            else:
                self.anim_rotation = 0
                self._end_animation()

        elif self.anim_type == "nod":
            # 点头
            if self.anim_frame <= 20:
                t = self.anim_frame / 20
                offset = 8 * self.scale * (t / 0.5) if t < 0.5 else 8 * self.scale * (1 - (t - 0.5) / 0.5)
                self.move(g.x(), g.y() + int(offset))
            else:
                self._end_animation()

        elif self.anim_type == "spin":
            # 转一圈
            if self.anim_frame <= 30:
                self.anim_rotation = 360 * (self.anim_frame / 30)
                self.update()
            else:
                self.anim_rotation = 0
                self._end_animation()

        elif self.anim_type == "tilt":
            # 歪头（左右歪）
            if self.anim_frame <= 28:
                t = self.anim_frame / 28
                if t < 0.3:
                    self.anim_rotation = -12 * (t / 0.3)
                elif t < 0.7:
                    self.anim_rotation = -12 + 24 * ((t - 0.3) / 0.4)
                else:
                    self.anim_rotation = 12 - 12 * ((t - 0.7) / 0.3)
                self.update()
            else:
                self.anim_rotation = 0
                self._end_animation()

        elif self.anim_type == "double_jump":
            # 双击：连跳两下
            if self.anim_frame <= 40:
                t = self.anim_frame / 40
                jump_h = 50 * self.scale
                phase = t * 2
                if phase < 1:
                    offset_y = -4 * jump_h * phase * (phase - 1)
                else:
                    phase -= 1
                    offset_y = -4 * jump_h * 0.7 * phase * (phase - 1)
                self.move(g.x(), g.y() - int(offset_y))
            else:
                self._end_animation()

        # ===== 4种闲置小动作 =====
        elif self.anim_type == "idle_blink":
            if self.anim_frame <= 12:
                t = self.anim_frame / 12
                s = 0.15 * (t / 0.5) if t < 0.5 else 0.15 * (1 - (t - 0.5) / 0.5)
                new_h = int(self.base_h * self.scale * (1 - s))
                self.pet_img = self.img.scaled(
                    int(self.base_w * self.scale), new_h,
                    Qt.AspectRatioMode.IgnoreAspectRatio,
                    Qt.TransformationMode.SmoothTransformation)
                new_total_h = new_h + self.bubble_space
                self.resize(g.width(), new_total_h)
                self.move(g.x(), g.bottom() - new_total_h)
                self.update()
            else:
                self._apply_scale()
                self.setGeometry(self.original_geom)
                self._end_animation()

        elif self.anim_type == "idle_look_around":
            if self.anim_frame <= 30:
                t = self.anim_frame / 30
                if t < 0.3:
                    self.anim_rotation = -6 * (t / 0.3)
                elif t < 0.7:
                    self.anim_rotation = -6 + 12 * ((t - 0.3) / 0.4)
                else:
                    self.anim_rotation = 6 - 6 * ((t - 0.7) / 0.3)
                self.update()
            else:
                self.anim_rotation = 0
                self._end_animation()

        elif self.anim_type == "idle_stretch":
            # 伸懒腰
            if self.anim_frame <= 24:
                t = self.anim_frame / 24
                s = 0.15 * (t / 0.4) if t < 0.4 else 0.15 * (1 - (t - 0.4) / 0.6)
                sy, sx = 1 + s, 1 - s * 0.3
                new_w = int(self.base_w * self.scale * sx)
                new_h = int(self.base_h * self.scale * sy)
                self.pet_img = self.img.scaled(new_w, new_h,
                    Qt.AspectRatioMode.IgnoreAspectRatio,
                    Qt.TransformationMode.SmoothTransformation)
                new_total_h = new_h + self.bubble_space
                self.resize(new_w, new_total_h)
                self.move(g.x() - (new_w - g.width()) // 2, g.bottom() - new_total_h)
                self.update()
            else:
                self._apply_scale()
                self.setGeometry(self.original_geom)
                self._end_animation()

        elif self.anim_type == "idle_sigh":
            # 叹气下沉
            if self.anim_frame <= 20:
                t = self.anim_frame / 20
                offset = 6 * (t / 0.5) if t < 0.5 else 6 * (1 - (t - 0.5) / 0.5)
                self.move(g.x(), g.y() + int(offset))
            else:
                self._end_animation()

    def _end_animation(self):
        self.anim_timer.stop()
        self.setGeometry(self.original_geom)
        self.anim_type = None
        self.anim_rotation = 0
        self.update()

    def closeEvent(self, event):
        self._save_config()
        super().closeEvent(event)


def main():
    try:
        app = QApplication(sys.argv)
        app.setApplicationName("蘑菇桌宠")
        pet = MoguPet()

        # 恢复上次位置
        if pet.config.get("pos_x") is not None and pet.config.get("pos_y") is not None:
            pet.move(pet.config["pos_x"], pet.config["pos_y"])
        else:
            screen = app.primaryScreen().geometry()
            pet.move(
                (screen.width() - pet.width()) // 2,
                screen.height() - pet.height() - 100
            )

        pet.show()
        sys.exit(app.exec())
    except Exception as e:
        from PyQt6.QtWidgets import QMessageBox
        app = QApplication.instance() or QApplication(sys.argv)
        QMessageBox.critical(None, "蘑菇桌宠 启动失败", str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()

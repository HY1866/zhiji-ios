#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""智记 (ZhiJi) — GTK3 时间记录器，支持语音识别"""

import os
import sys
import atexit
import signal

os.environ.setdefault("PYTHONIOENCODING", "utf-8")
os.environ.setdefault("LC_ALL", "C.UTF-8")
os.environ.setdefault("LANG", "C.UTF-8")

if sys.stdout.encoding != "utf-8":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

import csv
import subprocess
import threading
import tempfile
import warnings
from datetime import datetime

warnings.filterwarnings("ignore", category=DeprecationWarning)

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gdk, GLib, Gtk, Pango  # noqa: E402

# ---------------------------------------------------------------------------
# Configuration constants
# ---------------------------------------------------------------------------
VERSION = "1.5.0"
WIN_X = 1800
WIN_Y = 105
WIN_W = 220  # 再加宽20像素以容纳帮助按钮
WIN_H = 100
LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Document Dashboard", "时间记录.txt")
EXPORT_FILE = os.path.expanduser("~/zhiji_export.csv")
TMP_WAV = "/tmp/zhiji_voice.wav"
VOICE_MAX_DURATION = 15  # 最长录制15秒
VOICE_SILENCE_THRESHOLD = 5  # 静音5秒自动结束
VOICE_SAMPLE_RATE = 16000
VOICE_CHANNELS = 1
LOG_TAIL_LINES = 50
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Offline data", "zhiji_config.json")

# 时间格式定义
TIME_FORMAT_CHINESE = "chinese"  # "2026年5月10日21:35:01"
TIME_FORMAT_ISO = "iso"          # "2026-04-22 01:02:57"

CSS = """
window { background-color: #1e1e2e; border-radius: 8px; }
label { color: #cdd6f4; font-size: 9px; }
.clock-label { font-size: 13px; font-weight: bold; color: #89b4fa; }
.count-label { font-size: 9px; color: #a6adc8; }
.record-btn { background: #45475a; color: #cdd6f4; border-radius: 4px;
              padding: 2px 6px; border: 1px solid #585b70; font-size: 10px;
              min-height: 0; min-width: 0; }
.record-btn:hover { background: #585b70; }
.voice-btn { background: #313244; color: #f38ba8; border-radius: 4px;
             padding: 2px 6px; border: 1px solid #585b70; font-size: 10px;
             min-height: 0; min-width: 0; }
.voice-btn:hover { background: #45475a; }
.recording { background: #f38ba8; color: #1e1e2e; }
.exit-btn { background: #313244; color: #a6adc8; border-radius: 4px;
            padding: 1px 4px; border: 1px solid #45475a; font-size: 9px;
            min-height: 0; min-width: 0; }
.exit-btn:hover { background: #45475a; }
.log-view { background-color: #181825; color: #bac2de;
            font-family: monospace; font-size: 9px; border-radius: 4px; }
.log-view:selected, .log-view selection { background-color: #89b4fa; color: #1e1e2e; }
.log-view:hover { background-color: #1f1f30; }
.status-label { font-size: 8px; color: #6c7086; }
.export-btn { background: #313244; color: #a6e3a1; border-radius: 3px;
              padding: 1px 4px; border: 1px solid #45475a; font-size: 9px;
              min-height: 0; min-width: 0; }
.format-btn { background: #313244; color: #f5c2e7; border-radius: 3px;
              padding: 1px 3px; border: 1px solid #45475a; font-size: 8px;
              min-height: 0; min-width: 0; }
.format-btn:hover { background: #45475a; }
.help-btn { background: #313244; border-radius: 3px;
             padding: 1px 3px; border: 1px solid #45475a;
             min-height: 0; min-width: 0; }
.help-btn:hover { background: #45475a; }
.mode-switch-btn { background: #313244; color: #89dceb; border-radius: 4px;
                   padding: 2px 6px; border: 1px solid #585b70; font-size: 10px;
                   min-height: 0; min-width: 0; }
.mode-switch-btn:hover { background: #45475a; }
.mode-switch-btn.offline { color: #a6e3a1; }
"""

# ---------------------------------------------------------------------------
# AI Learning Offline Library
# ---------------------------------------------------------------------------

class PhraseLearner:
    LEARN_THRESHOLD = 3
    SIMILARITY_THRESHOLD = 0.8
    DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Offline data", "智记_离线库.json")

    def __init__(self):
        self.phrase_freq = {}
        self.offline_lib = {}
        self.corrections = {}  # 原始文本 -> 修改后文本
        # 按口音分类的离线库
        self.accent_lib = {
            "sichuan": {},
            "henan": {},
            "mandarin": {},
            "whisper": {},
        }
        self._load()

    def _load(self):
        db_path = self.DB_FILE
        # 确保目录存在
        db_dir = os.path.dirname(db_path)
        if not os.path.isdir(db_dir):
            try:
                os.makedirs(db_dir, exist_ok=True)
            except Exception:
                pass
        if os.path.isfile(db_path):
            try:
                import json
                with open(db_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.phrase_freq = data.get("phrase_freq", {})
                    self.offline_lib = data.get("offline_lib", {})
                    self.corrections = data.get("corrections", {})
                    # 加载按口音分类的数据
                    self.accent_lib = data.get("accent_lib", {
                        "sichuan": {},
                        "henan": {},
                        "mandarin": {},
                        "whisper": {},
                    })
            except Exception:
                self.phrase_freq = {}
                self.offline_lib = {}
                self.corrections = {}
                self.accent_lib = {
                    "sichuan": {},
                    "henan": {},
                    "mandarin": {},
                    "whisper": {},
                }

    def _save(self):
        try:
            import json
            with open(self.DB_FILE, "w", encoding="utf-8") as f:
                json.dump({
                    "phrase_freq": self.phrase_freq,
                    "offline_lib": self.offline_lib,
                    "corrections": self.corrections,
                    "accent_lib": self.accent_lib,
                }, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def _normalize_text(self, text):
        import re
        text = re.sub(r"^\d{4}年\d{1,2}月\d{1,2}日\d{2}:\d{2}:\d{2}\s*", "", text)
        text = re.sub(r"[^\w\u4e00-\u9fff]", "", text)
        return text.lower()

    def _get_ngrams(self, text, n=2):
        chars = list(text)
        return ["".join(chars[i:i+n]) for i in range(max(1, len(chars)-n+1))]

    def _jaccard_similarity(self, set1, set2):
        if not set1 or not set2:
            return 0.0
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        return intersection / union if union > 0 else 0.0

    def _levenshtein_ratio(self, s1, s2):
        if len(s1) < len(s2):
            return self._levenshtein_ratio(s2, s1)
        if len(s2) == 0:
            return 0.0
        prev_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            curr_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = prev_row[j + 1] + 1
                deletions = curr_row[j] + 1
                substitutions = prev_row[j] + (c1 != c2)
                curr_row.append(min(insertions, deletions, substitutions))
            prev_row = curr_row
        distance = prev_row[-1]
        max_len = max(len(s1), len(s2))
        return 1.0 - (distance / max_len) if max_len > 0 else 1.0

    def learn(self, text):
        if not text or len(text) < 2:
            return None
        normalized = self._normalize_text(text)
        if not normalized:
            return None
        phrases = normalized.split()
        words = list(normalized)
        all_items = phrases + ["".join(words[i:i+2]) for i in range(max(0, len(words)-1))]
        for item in all_items:
            if len(item) < 2:
                continue
            self.phrase_freq[item] = self.phrase_freq.get(item, 0) + 1
            if self.phrase_freq[item] == self.LEARN_THRESHOLD:
                self.offline_lib[item] = {
                    "phrase": item,
                    "count": self.phrase_freq[item],
                    "learned": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                }
        self._save()
        learned = [k for k, v in self.offline_lib.items()
                   if self.phrase_freq.get(k, 0) >= self.LEARN_THRESHOLD]
        return learned if learned else None

    def learn_with_accent(self, text, source):
        """按口音分类学习，将识别结果存储到对应口音的离线库中"""
        if not text or len(text) < 2:
            return None
        
        # 确定口音类型
        accent = "unknown"
        if "sichuan" in source:
            accent = "sichuan"
        elif "henan" in source:
            accent = "henan"
        elif "mandarin" in source:
            accent = "mandarin"
        elif "whisper" in source:
            accent = "whisper"
        
        if accent == "unknown" or accent not in self.accent_lib:
            # 如果无法识别口音，还是调用普通学习
            return self.learn(text)
        
        normalized = self._normalize_text(text)
        if not normalized:
            return None
        
        # 获取对应口音的词典
        accent_dict = self.accent_lib[accent]
        
        # 学习短语
        phrases = normalized.split()
        words = list(normalized)
        all_items = phrases + ["".join(words[i:i+2]) for i in range(max(0, len(words)-1))]
        
        for item in all_items:
            if len(item) < 2:
                continue
            # 按口音计数
            if item not in accent_dict:
                accent_dict[item] = {
                    "phrase": item,
                    "count": 0,
                    "accent": accent,
                    "learned": None,
                }
            accent_dict[item]["count"] += 1
            
            # 如果达到学习阈值，标记为已学习
            if accent_dict[item]["count"] == self.LEARN_THRESHOLD:
                accent_dict[item]["learned"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        self._save()
        
        # 同时也调用普通学习，保持向后兼容
        self.learn(text)
        
        # 返回在该口音下学到的短语
        learned = [k for k, v in accent_dict.items()
                   if v["count"] >= self.LEARN_THRESHOLD and v["learned"]]
        return learned if learned else None

    def get_accent_lib(self, accent=None):
        """获取指定口音的离线库，如果不指定则返回全部"""
        if accent and accent in self.accent_lib:
            return self.accent_lib[accent]
        return self.accent_lib

    def find_similar(self, text):
        if not text or len(text) < 2:
            return []
        normalized = self._normalize_text(text)
        if not normalized:
            return []
        results = []
        for phrase, info in self.offline_lib.items():
            if len(phrase) < 2:
                continue
            sim = self._levenshtein_ratio(normalized, phrase)
            if sim >= self.SIMILARITY_THRESHOLD:
                results.append((phrase, info, sim))
        results.sort(key=lambda x: x[2], reverse=True)
        return [(p, i) for p, i, _ in results]

    def get_offline_lib(self):
        return self.offline_lib

    def save_correction(self, original_text, corrected_text):
        """保存原始文本和修改后文本的对应关系"""
        if not original_text or not corrected_text:
            return False
        
        orig_normalized = self._normalize_text(original_text)
        corr_normalized = self._normalize_text(corrected_text)
        
        if orig_normalized == corr_normalized:
            return False
        
        self.corrections[orig_normalized] = {
            "original": original_text,
            "corrected": corrected_text,
            "count": self.corrections.get(orig_normalized, {}).get("count", 0) + 1,
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        self._save()
        return True

    def apply_correction(self, text):
        """自动应用修改，返回修改后的文本（如果有）"""
        if not text:
            return text
        
        normalized = self._normalize_text(text)
        
        # 精确匹配
        if normalized in self.corrections:
            return self.corrections[normalized]["corrected"]
        
        # 相似匹配（查找最相似的）
        best_match = None
        best_sim = 0.0
        
        for key in self.corrections:
            sim = self._levenshtein_ratio(normalized, key)
            if sim > best_sim and sim >= self.SIMILARITY_THRESHOLD:
                best_sim = sim
                best_match = key
        
        if best_match:
            return self.corrections[best_match]["corrected"]
        
        return text

    def get_corrections(self):
        return self.corrections

# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------


class ZhiJiApp:
    def __init__(self):
        self._recording = False
        self._rec_proc = None
        self.phrase_learner = PhraseLearner()
        self._time_format = TIME_FORMAT_CHINESE  # 默认中文格式
        self._load_config()
        
        # 确保Document Dashboard文件夹存在
        log_dir = os.path.dirname(LOG_FILE)
        if not os.path.isdir(log_dir):
            try:
                os.makedirs(log_dir, exist_ok=True)
                print(f"[zhiji] Created log directory: {log_dir}")
            except Exception as e:
                print(f"[zhiji] Failed to create log directory: {e}")
        
        # 语音识别任务队列
        import queue
        self._recognition_queue = queue.Queue()
        self._is_processing = False
        self._queue_count = 0
        
        self._apply_css()
        self._build_ui()
        self._update_format_btn_tooltip()  # UI构建完成后更新按钮提示
        self._update_mode_switch_btn()  # 更新模式切换按钮显示
        GLib.timeout_add_seconds(1, self.update_clock)
    
    def _load_config(self):
        """加载配置"""
        if os.path.isfile(CONFIG_FILE):
            try:
                import json
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._time_format = data.get("time_format", TIME_FORMAT_CHINESE)
                    self._window_width = data.get("window_width", WIN_W)
                    self._window_height = data.get("window_height", WIN_H)
                    self._window_x = data.get("window_x", WIN_X)
                    self._window_y = data.get("window_y", WIN_Y)
            except Exception:
                self._time_format = TIME_FORMAT_CHINESE
                self._window_width = WIN_W
                self._window_height = WIN_H
                self._window_x = WIN_X
                self._window_y = WIN_Y
        else:
            self._time_format = TIME_FORMAT_CHINESE
            self._window_width = WIN_W
            self._window_height = WIN_H
            self._window_x = WIN_X
            self._window_y = WIN_Y
        # 更新按钮提示
        if hasattr(self, 'format_btn'):
            self._update_format_btn_tooltip()
    
    def _add_to_queue(self, audio_path, ts, mode=None):
        """将识别任务加入队列"""
        if mode is None:
            mode = self.rec_mode
        self._queue_count += 1
        queue_id = self._queue_count
        self._recognition_queue.put({
            "id": queue_id,
            "audio_path": audio_path,
            "ts": ts,
            "mode": mode
        })
        self._update_queue_status()
        print(f"[zhiji] Added task #{queue_id} to queue (mode: {mode})")
        
        # 如果没有正在处理，启动处理
        if not self._is_processing:
            self._start_queue_processor()
    
    def _update_queue_status(self):
        """更新队列状态显示"""
        remaining = self._recognition_queue.qsize()
        if remaining > 0:
            status = f"队列中还有 {remaining} 条待识别"
            if hasattr(self, 'status_label'):
                GLib.idle_add(self._set_status, status)
        print(f"[zhiji] Queue status: {remaining} tasks remaining")
    
    def _start_queue_processor(self):
        """启动队列处理线程"""
        if self._is_processing:
            return
        
        self._is_processing = True
        import threading
        processor_thread = threading.Thread(target=self._process_queue, daemon=True)
        processor_thread.start()
        print("[zhiji] Started queue processor")
    
    def _process_queue(self):
        """处理队列中的任务"""
        print("[zhiji] Queue processor running")
        while True:
            try:
                # 尝试获取任务，设置超时以便检查是否应该退出
                task = self._recognition_queue.get(timeout=1)
                print(f"[zhiji] Processing task #{task['id']} (mode: {task['mode']})")
                GLib.idle_add(self._set_status, f"正在识别第 {task['id']} 条...")
                
                # 执行识别
                self._do_recognize_bg(task["audio_path"], task["ts"], task["mode"])
                
                # 标记任务完成
                self._recognition_queue.task_done()
                self._update_queue_status()
                
            except Exception as e:
                # 队列为空或超时
                if str(e) != "":
                    print(f"[zhiji] Queue processor error: {e}")
                
                # 检查队列是否真的为空
                if self._recognition_queue.empty():
                    self._is_processing = False
                    print("[zhiji] Queue empty, stopping processor")
                    GLib.idle_add(self._set_status, "就绪")
                    break
    
    def _on_window_resize(self, widget, allocation):
        """窗口大小改变时的处理 - 保存窗口大小和位置"""
        # 按钮已经设置为可扩展，Gtk会自动处理布局
        # 延迟保存，避免频繁保存
        if hasattr(self, '_resize_save_id'):
            GLib.source_remove(self._resize_save_id)
        self._resize_save_id = GLib.timeout_add(500, self._save_window_size)
    
    def _save_window_size(self):
        """保存窗口大小和位置"""
        if hasattr(self, 'win'):
            try:
                width, height = self.win.get_size()
                x, y = self.win.get_position()
                self._window_width = width
                self._window_height = height
                self._window_x = x
                self._window_y = y
                # 只保存，不立即写文件，避免频繁IO
                # 会在窗口关闭或其他时机一起保存
            except Exception:
                pass
        return False  # 只执行一次
    
    def _update_format_btn_tooltip(self):
        """更新格式按钮的提示信息"""
        if self._time_format == TIME_FORMAT_CHINESE:
            self.format_btn.set_tooltip_text("当前:中文格式\n点击切换为ISO格式")
        else:
            self.format_btn.set_tooltip_text("当前:ISO格式\n点击切换为中文格式")
    
    def _save_config(self):
        """保存配置"""
        try:
            import json
            config_dir = os.path.dirname(CONFIG_FILE)
            if not os.path.isdir(config_dir):
                os.makedirs(config_dir, exist_ok=True)
            
            # 获取当前窗口大小和位置
            if hasattr(self, 'win'):
                try:
                    width, height = self.win.get_size()
                    x, y = self.win.get_position()
                    self._window_width = width
                    self._window_height = height
                    self._window_x = x
                    self._window_y = y
                except Exception:
                    pass
            
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump({
                    "time_format": self._time_format,
                    "window_width": self._window_width,
                    "window_height": self._window_height,
                    "window_x": self._window_x,
                    "window_y": self._window_y
                }, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
    
    def _toggle_time_format(self, widget=None):
        """切换时间格式"""
        print(f"[FUNC] _toggle_time_format called: widget={widget}")
        if self._time_format == TIME_FORMAT_CHINESE:
            self._time_format = TIME_FORMAT_ISO
        else:
            self._time_format = TIME_FORMAT_CHINESE
        self._save_config()
        self._update_format_btn_tooltip()
        self._set_status(f"时间格式: {self._time_format}")
        self.update_clock()
    
    def _toggle_window_size(self, widget=None):
        """切换窗口大小（普通/全屏）"""
        print(f"[FUNC] _toggle_window_size called: widget={widget}, _window_zoomed={getattr(self, '_window_zoomed', False)}")
        if hasattr(self, '_window_zoomed') and self._window_zoomed:
            # 退出全屏 - 先保存修改
            self._save_text_changes()
            
            self.win.unfullscreen()
            self._window_zoomed = False
            self.zoom_btn.set_label("🔍")
            self.zoom_btn.set_tooltip_text("切换到全屏")
            self._set_status("窗口：普通大小")
            
            # 恢复文本视图设置
            if hasattr(self, 'text_view'):
                self.text_view.set_editable(False)
                self.text_view.override_font(Pango.FontDescription("monospace 8"))
            
            # 恢复滚动窗口大小
            if hasattr(self, 'scroll'):
                self.scroll.set_min_content_height(30)
            
            # 重新加载日志（确保内容正确）
            self.load_log()
        else:
            # 进入全屏
            self.win.fullscreen()
            self._window_zoomed = True
            self.zoom_btn.set_label("📐")
            self.zoom_btn.set_tooltip_text("退出全屏")
            self._set_status("窗口：已全屏 - 文本看板优先（可编辑）")
            
            # 优化文本视图方便查看和修改
            if hasattr(self, 'text_view'):
                self.text_view.set_editable(True)  # 允许编辑
                self.text_view.override_font(Pango.FontDescription("monospace 12"))  # 更大字体
            
            # 让滚动窗口占据更多空间
            if hasattr(self, 'scroll'):
                self.scroll.set_min_content_height(500)  # 更大的最小高度
            
            # 重置修改标记
            self._text_modified = False

    def _update_mode_switch_btn(self):
        """更新模式切换按钮的显示"""
        style_context = self.mode_switch_btn.get_style_context()
        
        if self.rec_mode == "online":
            self.mode_switch_btn.set_label("→在线")
            style_context.remove_class("offline")
        else:
            self.mode_switch_btn.set_label("→离线")
            style_context.add_class("offline")

    def _test_recognition_mode(self, mode):
        """测试指定的识别模式是否可用"""
        try:
            # 使用Audio文件夹内的测试音频
            script_dir = os.path.dirname(os.path.abspath(__file__))
            audio_folder = os.path.join(script_dir, "Audio")
            test_wav = os.path.join(audio_folder, "test.wav")
            
            # 如果测试音频不存在，创建一个
            if not os.path.exists(test_wav):
                import wave
                import struct
                sample_rate = 16000
                num_samples = sample_rate * 2  # 2秒
                with wave.open(test_wav, 'wb') as wf:
                    wf.setnchannels(1)
                    wf.setsampwidth(2)
                    wf.setframerate(sample_rate)
                    for _ in range(num_samples):
                        wf.writeframes(struct.pack('<h', 0))
            
            # 调用recognize_zh.py进行测试
            script = os.path.join(script_dir, "recognize_zh.py")
            
            import subprocess
            env = os.environ.copy()
            env["PYTHONIOENCODING"] = "utf-8"
            
            result = subprocess.run(
                [sys.executable, script, test_wav, "--mode", mode],
                capture_output=True,
                timeout=30,  # 30秒超时
                env=env,
                text=True,
                errors="replace"
            )
            
            # 检查结果
            # 静音音频可能返回空文本（error=None, text=None），这是正常的
            # 只有当存在错误时才视为测试失败
            if result.returncode == 0 or (mode == "offline" and "Whisper init failed" not in result.stderr):
                return True, None
            else:
                error_msg = f"测试失败: {result.stderr[-200:] if result.stderr else '未知错误'}"
                return False, error_msg
                
        except Exception as e:
            return False, str(e)

    def on_mode_switch_clicked(self, widget=None):
        """模式切换按钮点击事件"""
        old_mode = self.rec_mode
        new_mode = "offline" if old_mode == "online" else "online"
        
        self._set_status(f"正在切换到{new_mode}模式...")
        
        # 先临时切换UI显示
        self.rec_mode = new_mode
        self._update_mode_switch_btn()
        
        # 在后台线程中测试新模式
        import threading
        t = threading.Thread(
            target=self._test_and_confirm_mode,
            args=(old_mode, new_mode),
            daemon=True
        )
        t.start()

    def on_mode_switch_btn_press(self, widget, event):
        """模式切换按钮鼠标按下事件 - 右键选择文件识别"""
        if event.type == Gdk.EventType.BUTTON_PRESS and event.button == 3:
            self._select_audio_and_recognize(self.rec_mode)
            return True  # 阻止默认事件
        return False

    def _test_and_confirm_mode(self, old_mode, new_mode):
        """测试新模式并在失败时回退"""
        print(f"[zhiji] Testing mode: {new_mode}")
        
        success, error_msg = self._test_recognition_mode(new_mode)
        
        if success:
            GLib.idle_add(self._set_status, f"已切换到{new_mode}模式")
            print(f"[zhiji] Mode switch successful: {new_mode}")
        else:
            # 失败，回退到旧模式
            self.rec_mode = old_mode
            GLib.idle_add(self._update_mode_switch_btn)
            GLib.idle_add(self._set_status, f"切换失败: {error_msg[:50]}")
            print(f"[zhiji] Mode switch failed: {error_msg}")

    # -- CSS ----------------------------------------------------------------

    @staticmethod
    def _apply_css():
        provider = Gtk.CssProvider()
        provider.load_from_data(CSS.encode("utf-8"))
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )

    # -- UI -----------------------------------------------------------------

    def _build_ui(self):
        self.win = Gtk.Window(title=f"智记 v{VERSION}")
        # 使用保存的窗口大小和位置
        self.win.set_default_size(self._window_width, self._window_height)
        self.win.move(self._window_x, self._window_y)
        self.win.set_keep_above(True)
        self.win.set_skip_taskbar_hint(False)  # 允许窗口显示在任务栏
        self.win.set_resizable(True)
        self.win.set_size_request(150, 80)
        self.win.set_decorated(False)  # 去掉窗口边框和标题栏，实现一体化效果
        try:
            self.win.set_wmclass("zhiji", "zhiji")
        except Exception:
            pass
        self.win.connect("destroy", self._on_window_close)
        self.win.connect("delete-event", self._on_window_delete)
        self.win.connect("key-press-event", self._on_key_press)
        
        # 设置窗口图标
        icon_loaded = False
        logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "LOGO.ico")
        if os.path.exists(logo_path):
            try:
                from gi.repository import GdkPixbuf
                # 尝试直接加载.ico
                try:
                    pixbuf = GdkPixbuf.Pixbuf.new_from_file(logo_path)
                    self.win.set_icon(pixbuf)
                    icon_loaded = True
                except Exception:
                    # 尝试使用PNG格式作为备选
                    try:
                        png_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "zhiji_icon.png")
                        if os.path.exists(png_path):
                            pixbuf = GdkPixbuf.Pixbuf.new_from_file(png_path)
                            self.win.set_icon(pixbuf)
                            icon_loaded = True
                    except Exception:
                        pass
            except Exception:
                pass

        self._create_tray_icon()

        self._drag_start = None
        self.win.connect("button-press-event", self._on_win_press)
        self.win.connect("button-release-event", self._on_win_release)
        self.win.connect("motion-notify-event", self._on_win_motion)
        self.win.connect("size-allocate", self._on_window_resize)  # 添加窗口大小改变事件
        self.win.add_events(
            Gdk.EventMask.BUTTON_PRESS_MASK
            | Gdk.EventMask.BUTTON_RELEASE_MASK
            | Gdk.EventMask.POINTER_MOTION_MASK
        )

        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=1)
        root.set_margin_top(5)
        root.set_margin_bottom(1)
        root.set_margin_start(4)
        root.set_margin_end(4)
        self.win.add(root)

        # 可拖拽的顶部区域（用于移动窗口）
        drag_bar = Gtk.EventBox()
        root.pack_start(drag_bar, False, False, 0)

        # 连接拖动事件（带日志）
        def on_win_press_log(widget, event):
            print(f"[DRAG] button-press-event: button={event.button}, x={event.x}, y={event.y}, x_root={event.x_root}, y_root={event.y_root}")
            click_window = event.get_window()
            print(f"[DRAG] Clicked window: {click_window}")
            for btn_name, btn in [("help_btn", self.help_btn), ("zoom_btn", self.zoom_btn), ("format_btn", self.format_btn)]:
                btn_win = btn.get_window()
                print(f"[DRAG] {btn_name} window: {btn_win}, match={btn_win == click_window}")
                if btn_win == click_window:
                    print(f"[DRAG] Clicked on {btn_name}, blocking drag")
                    return False
            self._drag_start = (event.x_root, event.y_root)
            win_pos = self.win.get_position()
            self._drag_win_origin = (win_pos[0], win_pos[1])
            print(f"[DRAG] Starting drag: start=({self._drag_start}), win_origin={self._drag_win_origin}")
            return True

        def on_win_release_log(widget, event):
            print(f"[DRAG] button-release-event: button={event.button}")
            self._drag_start = None
            print(f"[DRAG] Drag released")

        def on_win_motion_log(widget, event):
            if self._drag_start:
                dx = event.x_root - self._drag_start[0]
                dy = event.y_root - self._drag_start[1]
                self.win.move(
                    int(self._drag_win_origin[0] + dx),
                    int(self._drag_win_origin[1] + dy),
                )
                print(f"[DRAG] motion: dx={dx:.1f}, dy={dy:.1f}, new_pos=({int(self._drag_win_origin[0] + dx)}, {int(self._drag_win_origin[1] + dy)})")

        drag_bar.connect("button-press-event", on_win_press_log)
        drag_bar.connect("button-release-event", on_win_release_log)
        drag_bar.connect("motion-notify-event", on_win_motion_log)
        
        # 顶部垂直容器（两排）
        top_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=1)
        drag_bar.add(top_vbox)

        # ========== 第一排：帮助按钮（左）+ 全屏按钮（右）==========
        first_row = Gtk.Box(spacing=6)
        top_vbox.pack_start(first_row, False, False, 0)

        # 左侧：帮助按钮（使用GTK内置图标）
        self.help_btn = Gtk.Button()
        self.help_btn.get_style_context().add_class("help-btn")
        self.help_btn.set_tooltip_text("使用说明")

        # 使用GTK内置的帮助图标
        help_image = Gtk.Image.new_from_icon_name("help-browser", Gtk.IconSize.MENU)
        self.help_btn.set_image(help_image)
        self.help_btn.set_always_show_image(True)

        # 帮助按钮事件（带日志）
        def on_help_btn_press(w, e):
            print(f"[BTN] help_btn button-press-event: button={e.button}, x={e.x}, y={e.y}")
            return False  # 允许事件传播，不阻止

        def on_help_btn_clicked(_):
            print(f"[BTN] help_btn clicked! Calling _show_help()")

        self.help_btn.connect("button-press-event", on_help_btn_press)
        self.help_btn.connect("clicked", on_help_btn_clicked)
        first_row.pack_start(self.help_btn, False, False, 0)

        # 中间填充
        spacer = Gtk.Box()
        first_row.pack_start(spacer, True, True, 0)

        # 右侧：全屏按钮
        self.zoom_btn = Gtk.Button(label="🔍")
        self.zoom_btn.get_style_context().add_class("help-btn")
        self.zoom_btn.set_tooltip_text("切换到全屏")

        # 全屏按钮事件（带日志）
        def on_zoom_btn_press(w, e):
            print(f"[BTN] zoom_btn button-press-event: button={e.button}, x={e.x}, y={e.y}")
            return False

        def on_zoom_btn_clicked(_):
            print(f"[BTN] zoom_btn clicked! Calling _toggle_window_size()")

        self.zoom_btn.connect("button-press-event", on_zoom_btn_press)
        self.zoom_btn.connect("clicked", on_zoom_btn_clicked)
        first_row.pack_end(self.zoom_btn, False, False, 0)

        # ========== 第二排：时间格式按钮 + 时钟 + 计数 ==========
        second_row = Gtk.Box(spacing=6)
        second_row.set_halign(Gtk.Align.CENTER)
        top_vbox.pack_start(second_row, False, False, 0)

        # 格式切换按钮
        self.format_btn = Gtk.Button(label="📅")
        self.format_btn.get_style_context().add_class("format-btn")
        self.format_btn.set_tooltip_text("切换时间格式")

        # 格式按钮事件（带日志）
        def on_format_btn_press(w, e):
            print(f"[BTN] format_btn button-press-event: button={e.button}, x={e.x}, y={e.y}")
            return False

        def on_format_btn_clicked(_):
            print(f"[BTN] format_btn clicked! Calling _toggle_time_format()")

        self.format_btn.connect("button-press-event", on_format_btn_press)
        self.format_btn.connect("clicked", on_format_btn_clicked)
        second_row.pack_start(self.format_btn, False, False, 0)

        # 时钟
        self.clock_label = Gtk.Label()
        self.clock_label.get_style_context().add_class("clock-label")
        second_row.pack_start(self.clock_label, False, False, 0)
        self.update_clock()

        # 计数
        self.count_label = Gtk.Label()
        self.count_label.get_style_context().add_class("count-label")
        second_row.pack_start(self.count_label, False, False, 0)

        # 识别模式状态
        self.rec_mode = "online"  # 默认在线模式

        # Buttons row: 记录 + 切换模式 + 语音
        btn_box = Gtk.Box(spacing=3)
        btn_box.set_halign(Gtk.Align.FILL)  # 改为填充模式
        root.pack_start(btn_box, False, False, 1)

        self.record_btn = Gtk.Button(label="记录")
        self.record_btn.get_style_context().add_class("record-btn")
        self.record_btn.connect("clicked", lambda _: self.on_record_clicked())
        btn_box.pack_start(self.record_btn, True, True, 0)  # 设置为可扩展

        self.mode_switch_btn = Gtk.Button(label="→在线")
        self.mode_switch_btn.get_style_context().add_class("mode-switch-btn")
        self.mode_switch_btn.set_tooltip_text("左键切换识别模式（在线/离线），右键选择音频文件识别")
        self.mode_switch_btn.connect("clicked", lambda _: self.on_mode_switch_clicked())
        self.mode_switch_btn.connect("button-press-event", self.on_mode_switch_btn_press)
        btn_box.pack_start(self.mode_switch_btn, True, True, 0)  # 设置为可扩展

        self.voice_btn = Gtk.Button(label="语音")
        self.voice_btn.get_style_context().add_class("voice-btn")
        self.voice_btn.connect("clicked", lambda _: self.on_voice_clicked())
        btn_box.pack_start(self.voice_btn, True, True, 0)  # 设置为可扩展

        # Status
        self.status_label = Gtk.Label(label="就绪")
        self.status_label.get_style_context().add_class("status-label")
        self.status_label.set_ellipsize(Pango.EllipsizeMode.END)
        root.pack_start(self.status_label, False, False, 0)

        # Log viewer (scrollable)
        self.scroll = Gtk.ScrolledWindow()
        self.scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        self.scroll.set_min_content_height(30)
        root.pack_start(self.scroll, True, True, 0)

        self.text_view = Gtk.TextView()
        self.text_view.set_editable(False)
        self.text_view.set_cursor_visible(True)
        self.text_view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self.text_view.get_style_context().add_class("log-view")
        self.text_view.override_font(Pango.FontDescription("monospace 8"))
        self.text_view.set_can_focus(True)
        self.scroll.add(self.text_view)
        self.text_buf = self.text_view.get_buffer()

        # 文本变化跟踪（用于全屏编辑保存）
        self._text_modified = False
        self.text_buf.connect("changed", self._on_text_changed)

        self.text_view.connect("button-press-event", self._on_log_button_press)

        self.load_log()
        self._learn_from_existing_log()
        self.win.show_all()

    def _learn_from_existing_log(self):
        if not os.path.isfile(LOG_FILE):
            return
        try:
            with open(LOG_FILE, "r", encoding="utf-8") as fh:
                for line in fh:
                    if line.strip():
                        import re
                        # 支持两种时间格式
                        timestamp_pattern = r"^(?:\d{4}年\d{1,2}月\d{1,2}日\d{2}:\d{2}:\d{2}|\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\s*"
                        text_match = re.sub(timestamp_pattern, "", line.strip())
                        if text_match:
                            self.phrase_learner.learn(text_match)
        except Exception:
            pass

    # -- Tray icon ----------------------------------------------------------

    def _create_tray_icon(self):
        self.tray_icon = Gtk.StatusIcon()
        
        # 优先尝试LOGO.ico
        icon_loaded = False
        logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "LOGO.ico")
        if os.path.exists(logo_path):
            try:
                from gi.repository import GdkPixbuf
                # 尝试直接加载
                try:
                    pixbuf = GdkPixbuf.Pixbuf.new_from_file(logo_path)
                    self.tray_icon.set_from_pixbuf(pixbuf)
                    icon_loaded = True
                except Exception:
                    # 如果.ico加载失败，尝试通过转换加载
                    try:
                        # 尝试使用PNG格式作为备选（如果存在的话）
                        png_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "zhiji_icon.png")
                        if os.path.exists(png_path):
                            pixbuf = GdkPixbuf.Pixbuf.new_from_file(png_path)
                            self.tray_icon.set_from_pixbuf(pixbuf)
                            icon_loaded = True
                    except Exception:
                        pass
            except Exception:
                pass
        
        # 如果图标加载失败，使用系统默认图标
        if not icon_loaded:
            self.tray_icon.set_from_icon_name("accessories-clock")
        
        self.tray_icon.set_tooltip_text("智记 - 点击显示/隐藏")
        self.tray_icon.connect("activate", self._on_tray_clicked)
        self.tray_icon.connect("popup-menu", self._on_tray_right_click)
        
        # 监听窗口状态变化
        self.win.connect("window-state-event", self._on_window_state_changed)

    def _on_tray_clicked(self, icon):
        if self.win.get_visible():
            self.win.hide()
        else:
            self.win.show_all()
            self.win.present()  # 将窗口带到前台

    def _on_window_state_changed(self, widget, event):
        """窗口状态变化时更新托盘提示"""
        if event.new_window_state & Gdk.WindowState.ICONIFIED:
            self.tray_icon.set_tooltip_text("智记 - 已最小化")
        elif widget.get_visible():
            self.tray_icon.set_tooltip_text("智记 - 点击隐藏")
        else:
            self.tray_icon.set_tooltip_text("智记 - 点击显示")
        return False

    def _on_tray_right_click(self, icon, button, time):
        menu = Gtk.Menu()
        
        show_item = Gtk.MenuItem(label="显示窗口")
        show_item.connect("activate", lambda _: (self.win.show_all(), self.win.present()))
        menu.append(show_item)
        
        # 时间格式子菜单
        format_menu = Gtk.Menu()
        format_item = Gtk.MenuItem(label="时间格式")
        format_item.set_submenu(format_menu)
        menu.append(format_item)
        
        chinese_format_item = Gtk.MenuItem(label="中文格式 (2026年5月10日21:35:01)")
        chinese_format_item.connect("activate", lambda _: self._set_time_format(TIME_FORMAT_CHINESE))
        format_menu.append(chinese_format_item)
        
        iso_format_item = Gtk.MenuItem(label="ISO格式 (2026-04-22 01:02:57)")
        iso_format_item.connect("activate", lambda _: self._set_time_format(TIME_FORMAT_ISO))
        format_menu.append(iso_format_item)
        
        menu.append(Gtk.SeparatorMenuItem())
        
        reset_size_item = Gtk.MenuItem(label="重置窗口大小")
        reset_size_item.connect("activate", lambda _: self._reset_window_size())
        menu.append(reset_size_item)
        
        help_item = Gtk.MenuItem(label="使用说明")
        help_item.connect("activate", lambda _: self._show_help())
        menu.append(help_item)
        
        quit_item = Gtk.MenuItem(label="退出")
        quit_item.connect("activate", lambda _: Gtk.main_quit())
        menu.append(quit_item)
        
        menu.show_all()
        menu.popup(None, None, None, None, button, time)
    
    def _set_time_format(self, format_type):
        """设置时间格式"""
        self._time_format = format_type
        self._save_config()
        self._set_status(f"时间格式: {format_type}")
        self.update_clock()
    
    def _reset_window_size(self):
        """重置窗口大小和位置到默认值"""
        self._window_width = WIN_W
        self._window_height = WIN_H
        self._window_x = WIN_X
        self._window_y = WIN_Y
        # 应用到窗口
        if hasattr(self, 'win'):
            self.win.resize(WIN_W, WIN_H)
            self.win.move(WIN_X, WIN_Y)
        # 保存配置
        self._save_config()
        self._set_status("窗口已重置到默认大小")

    def _on_window_close(self, widget):
        # 关闭前保存修改
        self._save_text_changes()
        self.win.hide()

    def _on_window_delete(self, widget, event):
        # 关闭前保存修改
        self._save_text_changes()
        self.win.hide()
        return True

    def _on_key_press(self, widget, event):
        """键盘快捷键处理"""
        # Ctrl+S 保存
        if (event.state & Gdk.ModifierType.CONTROL_MASK) and event.keyval == Gdk.KEY_s:
            if hasattr(self, '_window_zoomed') and self._window_zoomed:
                self._save_text_changes()
            return True
        # Esc 退出全屏
        if event.keyval == Gdk.KEY_Escape:
            if hasattr(self, '_window_zoomed') and self._window_zoomed:
                self._toggle_window_size()
            return True
        return False

    # -- Window drag --------------------------------------------------------
    # 注意：拖动逻辑已移至 drag_bar 初始化处（带日志版本）

    # -- Clock --------------------------------------------------------------

    def update_clock(self):
        now = datetime.now()
        if self._time_format == TIME_FORMAT_CHINESE:
            # 中文格式只显示时间部分
            self.clock_label.set_text(now.strftime("%H:%M:%S"))
        else:
            # ISO格式显示日期+时间
            self.clock_label.set_text(now.strftime("%Y-%m-%d %H:%M:%S"))
        return True  # keep timer alive

    # -- Helpers ------------------------------------------------------------

    def _count_records(self):
        if not os.path.isfile(LOG_FILE):
            return 0
        with open(LOG_FILE, "r", encoding="utf-8") as fh:
            return sum(1 for line in fh if line.strip())

    def _set_status(self, text):
        self.status_label.set_text(text)
    
    def _style_button(self, button, button_type="normal"):
        """为按钮应用高对比度样式"""
        button.override_font(Pango.FontDescription("Sans Bold 11"))
        
        if button_type == "delete":
            # 删除按钮：红色
            button.override_background_color(Gtk.StateFlags.NORMAL, Gdk.RGBA(0.9, 0.3, 0.3, 1.0))
            button.override_color(Gtk.StateFlags.NORMAL, Gdk.RGBA(1.0, 1.0, 1.0, 1.0))
        elif button_type == "cancel":
            # 取消按钮：灰色
            button.override_background_color(Gtk.StateFlags.NORMAL, Gdk.RGBA(0.6, 0.6, 0.6, 1.0))
            button.override_color(Gtk.StateFlags.NORMAL, Gdk.RGBA(1.0, 1.0, 1.0, 1.0))
        elif button_type == "ok":
            # 确定按钮：绿色
            button.override_background_color(Gtk.StateFlags.NORMAL, Gdk.RGBA(0.2, 0.7, 0.3, 1.0))
            button.override_color(Gtk.StateFlags.NORMAL, Gdk.RGBA(1.0, 1.0, 1.0, 1.0))
        else:
            # 普通按钮：蓝色
            button.override_background_color(Gtk.StateFlags.NORMAL, Gdk.RGBA(0.2, 0.5, 0.9, 1.0))
            button.override_color(Gtk.StateFlags.NORMAL, Gdk.RGBA(1.0, 1.0, 1.0, 1.0))
        
        return button

    def _timestamp(self):
        now = datetime.now()
        if self._time_format == TIME_FORMAT_CHINESE:
            return now.strftime("%Y年%m月%d日%H:%M:%S")
        else:
            return now.strftime("%Y-%m-%d %H:%M:%S")

    # -- Record -------------------------------------------------------------

    def on_record_clicked(self):
        ts = self._timestamp()
        with open(LOG_FILE, "a", encoding="utf-8") as fh:
            fh.write(ts + "\n")

        self.load_log()
        self._set_status(f"已记录 {ts}")

        orig = self.record_btn.get_label()
        self.record_btn.set_label("✅ 已记录")
        GLib.timeout_add(800, lambda: self.record_btn.set_label(orig) or False)

    # -- Voice --------------------------------------------------------------

    def on_voice_clicked(self):
        if self._recording:
            self._recording = False
            if self._rec_proc and self._rec_proc.poll() is None:
                import signal
                try:
                    self._rec_proc.send_signal(signal.SIGTERM)
                except OSError:
                    try:
                        self._rec_proc.kill()
                    except OSError:
                        pass
            self._set_status("正在停止录音...")
            return

        if not self._check_audio_tools():
            return

        self._recording = True
        self._rec_proc = None
        self._voice_ts = self._timestamp()
        ctx = self.voice_btn.get_style_context()
        ctx.add_class("recording")
        self.voice_btn.set_label("⏹ 停止录音")
        self._set_status(f"正在录音...点击「停止录音」结束")

        t = threading.Thread(target=self._do_voice_record, daemon=True)
        t.start()

    def _check_audio_tools(self):
        for cmd in ["arecord", "ffmpeg"]:
            try:
                subprocess.run(
                    [cmd, "--help"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=5,
                )
                return True
            except (FileNotFoundError, subprocess.TimeoutExpired,
                    subprocess.CalledProcessError):
                continue
        self._show_error(
            "缺少录音工具",
            "未找到 arecord 或 ffmpeg。\n请安装：\n"
            "sudo apt install alsa-utils ffmpeg",
        )
        return False

    def _do_voice_record(self):
        import wave
        import struct
        import time
        import threading
        import queue

        try:
            recorded = False
            rec_tool = None
            rec_proc = None

            # 检测可用的录音工具
            try:
                subprocess.check_output(["arecord", "--help"], stderr=subprocess.STDOUT)
                rec_tool = "arecord"
            except (subprocess.CalledProcessError, FileNotFoundError):
                try:
                    subprocess.check_output(["ffmpeg", "-version"], stderr=subprocess.STDOUT)
                    rec_tool = "ffmpeg"
                except (subprocess.CalledProcessError, FileNotFoundError):
                    pass

            if not rec_tool:
                GLib.idle_add(self._finish_recording,
                              "录音失败：未找到可用的录音工具 (arecord/ffmpeg)")
                return

            # 使用队列传递音频数据
            audio_queue = queue.Queue()
            stop_event = threading.Event()

            # 录音线程：从工具读取原始音频数据
            def record_thread():
                nonlocal rec_proc
                try:
                    if rec_tool == "arecord":
                        rec_proc = subprocess.Popen(
                            [
                                "arecord",
                                "-f", "S16_LE",
                                "-r", str(VOICE_SAMPLE_RATE),
                                "-c", str(VOICE_CHANNELS),
                            ],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.DEVNULL,
                            bufsize=0
                        )
                    else:
                        rec_proc = subprocess.Popen(
                            [
                                "ffmpeg", "-y",
                                "-f", "pulse", "-i", "default",
                                "-ac", str(VOICE_CHANNELS), "-ar", str(VOICE_SAMPLE_RATE),
                                "-f", "s16le", "-acodec", "pcm_s16le", "-",
                            ],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.DEVNULL,
                            bufsize=0
                        )

                    chunk_size = 3200  # 100ms per chunk (16000 * 0.1 * 2 bytes)
                    while not stop_event.is_set():
                        data = rec_proc.stdout.read(chunk_size)
                        if len(data) == 0:
                            break
                        audio_queue.put(data)
                except Exception as e:
                    print(f"[zhiji] record error: {e}")
                finally:
                    if rec_proc and rec_proc.poll() is None:
                        rec_proc.terminate()
                        try:
                            rec_proc.wait(timeout=1)
                        except:
                            rec_proc.kill()

            # 启动录音线程
            rec_thread = threading.Thread(target=record_thread, daemon=True)
            rec_thread.start()

            # 处理录音数据、检测静音
            frames = []
            silence_start = None
            total_duration = 0
            last_update_time = time.time()
            chunk_duration = 3200 / (VOICE_SAMPLE_RATE * 2 * VOICE_CHANNELS)  # 秒

            try:
                while total_duration < VOICE_MAX_DURATION and self._recording:
                    try:
                        chunk = audio_queue.get(timeout=0.1)
                    except queue.Empty:
                        if not rec_thread.is_alive() or not self._recording:
                            break
                        continue

                    frames.append(chunk)
                    total_duration += chunk_duration

                    # 计算音频能量
                    num_samples = len(chunk) // 2
                    energy = 0
                    for i in range(num_samples):
                        sample = struct.unpack("<h", chunk[i*2:i*2+2])[0]
                        energy += sample * sample
                    energy = energy / num_samples if num_samples > 0 else 0

                    # 检测静音
                    SILENCE_ENERGY_THRESHOLD = 10000
                    is_silence = energy < SILENCE_ENERGY_THRESHOLD

                    now = time.time()
                    if is_silence:
                        if silence_start is None:
                            silence_start = now
                        else:
                            silence_duration = now - silence_start
                            if silence_duration >= VOICE_SILENCE_THRESHOLD:
                                # 静音够了，结束录音
                                print(f"[zhiji] silence detected for {silence_duration:.1f}s, stop recording")
                                break
                    else:
                        silence_start = None

                    # 更新界面状态（每秒最多一次）
                    if now - last_update_time >= 1:
                        remaining = max(0, VOICE_MAX_DURATION - total_duration)
                        GLib.idle_add(self._set_status,
                                      f"录音中... {int(total_duration)}s / 最长{VOICE_MAX_DURATION}s")
                        last_update_time = now

            finally:
                stop_event.set()
                rec_thread.join(timeout=2)

            # 保存为 WAV 文件
            if len(frames) > 0:
                with wave.open(TMP_WAV, 'wb') as wf:
                    wf.setnchannels(VOICE_CHANNELS)
                    wf.setsampwidth(2)
                    wf.setframerate(VOICE_SAMPLE_RATE)
                    wf.writeframes(b''.join(frames))
                recorded = True

            if not recorded or not os.path.isfile(TMP_WAV):
                GLib.idle_add(self._finish_recording,
                              "录音失败")
                return

            wav_size = os.path.getsize(TMP_WAV)
            if wav_size < 1000:
                GLib.idle_add(self._finish_recording,
                              f"录音文件过小 ({wav_size}B)，请检查麦克风是否正常")
                return

            import shutil
            # 生成唯一的文件名，避免冲突
            import uuid
            unique_id = str(uuid.uuid4())[:8]
            recognize_wav = os.path.join(os.path.dirname(TMP_WAV), f"rec_{unique_id}.wav")
            shutil.copy2(TMP_WAV, recognize_wav)
            try:
                os.remove(TMP_WAV)
            except OSError:
                pass

            rec_ts = getattr(self, "_voice_ts", self._timestamp())
            # 加入识别队列，而不是直接启动线程
            self._add_to_queue(recognize_wav, rec_ts)
            
            # 更新UI显示已加入队列
            GLib.idle_add(self._finish_recording, 
                          f"已加入识别队列({wav_size // 1024}KB)")

        except Exception as e:
            GLib.idle_add(self._finish_recording, f"录音异常：{e}")

    def _do_recognize_bg(self, audio_path, ts, mode="all"):
        text, source = self._recognize(audio_path, mode)
        if text:
            # 自动应用离线库中的修改
            corrected_text = self.phrase_learner.apply_correction(text)
            
            if corrected_text != text:
                # 有修改，显示提示
                GLib.idle_add(self._set_status, f"自动修正: {corrected_text[:30]}")
                text = corrected_text
            
            # 按口音分类学习
            if source:
                self.phrase_learner.learn_with_accent(text, source)
            else:
                self.phrase_learner.learn(text)
            
            line = f"{ts} {text}"
            with open(LOG_FILE, "a", encoding="utf-8") as fh:
                fh.write(line + "\n")
            GLib.idle_add(self.load_log)
            if corrected_text == text:
                status_text = f"{text[:30]}"
                if source:
                    status_text += f" ({source})"
                GLib.idle_add(self._set_status, status_text)
        else:
            GLib.idle_add(self._set_status, "未识别到语音")
        try:
            os.remove(audio_path)
        except OSError:
            pass

    def _select_audio_and_recognize(self, mode):
        """打开文件选择对话框，选择音频文件并识别"""
        dialog = Gtk.FileChooserDialog(
            title="选择音频文件",
            parent=self.win,
            action=Gtk.FileChooserAction.OPEN
        )
        cancel_btn = dialog.add_button("取消", Gtk.ResponseType.CANCEL)
        select_btn = dialog.add_button("选择", Gtk.ResponseType.OK)
        
        # 应用按钮样式
        self._style_button(cancel_btn, "cancel")
        self._style_button(select_btn, "ok")
        
        # 添加音频文件过滤器
        filter_audio = Gtk.FileFilter()
        filter_audio.set_name("音频文件")
        filter_audio.add_pattern("*.wav")
        filter_audio.add_pattern("*.mp3")
        filter_audio.add_pattern("*.m4a")
        filter_audio.add_pattern("*.flac")
        filter_audio.add_pattern("*.aac")
        dialog.add_filter(filter_audio)
        
        # 添加所有文件过滤器
        filter_all = Gtk.FileFilter()
        filter_all.set_name("所有文件")
        filter_all.add_pattern("*")
        dialog.add_filter(filter_all)
        
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            audio_path = dialog.get_filename()
            dialog.destroy()
            
            if os.path.exists(audio_path):
                # 复制到临时文件
                import uuid
                import shutil
                unique_id = str(uuid.uuid4())[:8]
                temp_dir = os.path.dirname(TMP_WAV)
                temp_path = os.path.join(temp_dir, f"rec_{unique_id}.wav")
                shutil.copy2(audio_path, temp_path)
                
                ts = self._timestamp()
                
                # 加入识别队列
                self._add_to_queue(temp_path, ts, mode)
                self._set_status("已加入识别队列")
            else:
                self._set_status("文件不存在")
        else:
            dialog.destroy()

    def _recognize(self, audio_path, mode="all"):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        script = os.path.join(script_dir, "recognize_zh.py")
        print(f"[zhiji] recognize: {audio_path} ({os.path.getsize(audio_path)} bytes), mode={mode}")
        print(f"[zhiji] script: {script}")
        
        mode_text = {
            "online": "在线识别中...",
            "offline": "离线识别中...",
            "all": "识别中（首次需下载模型，请耐心等待）..."
        }
        GLib.idle_add(self._set_status, mode_text.get(mode, "识别中..."))
        try:
            env = os.environ.copy()
            env["PYTHONIOENCODING"] = "utf-8"
            env["LC_ALL"] = "C.UTF-8"
            env["LANG"] = "C.UTF-8"
            env["LC_CTYPE"] = "C.UTF-8"
            result = subprocess.run(
                [sys.executable, script, audio_path, "--mode", mode],
                capture_output=True,
                timeout=600,
                env=env,
            )
            stdout_raw = result.stdout.decode("utf-8", errors="replace") if result.stdout else ""
            stderr_raw = result.stderr.decode("utf-8", errors="replace") if result.stderr else ""
            print(f"[zhiji] rc={result.returncode} stdout_len={len(stdout_raw)} stderr_len={len(stderr_raw)}")
            if stderr_raw:
                for line in stderr_raw.strip().split("\n")[-5:]:
                    print(f"[zhiji] stderr: {line}")
            
            final_text = ""
            final_source = ""
            all_results = []
            
            if stdout_raw.strip():
                import json
                # 解析每一行，收集所有结果
                lines = stdout_raw.strip().split("\n")
                for line in lines:
                    try:
                        data = json.loads(line)
                        if "error" in data:
                            print(f"[zhiji] script error: {data['error']}")
                            GLib.idle_add(self._set_status, f"识别失败：{data['error'][:60]}")
                            return "", ""
                        text = data.get("text", "")
                        source = data.get("source", "")
                        # 收集有效的非中间结果
                        if "intermediate" not in source and text:
                            # 根据来源确定优先级
                            priority = 0
                            if "xunfei" in source:
                                priority = 2  # 讯飞在线优先级最高
                            elif "whisper" in source:
                                priority = 1  # Whisper离线次之
                            all_results.append({
                                "text": text,
                                "source": source,
                                "priority": priority
                            })
                            print(f"[zhiji] collected result: '{text}' (source={source}, priority={priority})")
                    except Exception:
                        # 如果不是JSON，可能是最后的纯文本结果，忽略
                        pass
                
                # 如果收集到了结果，选择优先级最高的
                if all_results:
                    # 按优先级从高到低排序
                    all_results.sort(key=lambda x: x["priority"], reverse=True)
                    best_result = all_results[0]
                    final_text = best_result["text"]
                    final_source = best_result["source"]
                    print(f"[zhiji] selected best result: '{final_text}' (source={final_source})")
                
                # 如果没有通过JSON解析到结果，尝试最后一行作为纯文本
                if not final_text and lines:
                    # 取最后一行作为纯文本结果
                    final_text = lines[-1].strip()
                    final_source = ""
                    print(f"[zhiji] using plain text result: '{final_text}'")
                
                print(f"[zhiji] text_len={len(final_text)}, source={final_source}")
                return final_text, final_source
            
            print("[zhiji] empty stdout")
            return "", ""
        except subprocess.TimeoutExpired:
            print("[zhiji] timeout")
            GLib.idle_add(self._set_status, "识别超时")
            return "", ""
        except Exception as e:
            print(f"[zhiji] error: {e}")
            GLib.idle_add(self._set_status, f"识别异常：{e}")
            return "", ""

    def _finish_recording(self, status_text=None):
        self._recording = False
        ctx = self.voice_btn.get_style_context()
        ctx.remove_class("recording")
        self.voice_btn.set_label("🎤 语音")
        if status_text:
            self._set_status(status_text)

    # -- Log viewer ---------------------------------------------------------

    def load_log(self):
        lines = []
        if os.path.isfile(LOG_FILE):
            with open(LOG_FILE, "r", encoding="utf-8") as fh:
                lines = fh.readlines()

        tail = lines[-LOG_TAIL_LINES:]
        self.text_buf.set_text("".join(tail))
        self.count_label.set_text(f"共 {len(lines)} 条记录")

        # auto-scroll to bottom
        GLib.idle_add(self._scroll_to_bottom)

    def _scroll_to_bottom(self):
        end_iter = self.text_buf.get_end_iter()
        self.text_view.scroll_to_iter(end_iter, 0.0, False, 0.0, 0.0)
        return False
    
    def _on_text_changed(self, buffer):
        """文本变化时标记为已修改"""
        if hasattr(self, '_window_zoomed') and self._window_zoomed:
            self._text_modified = True
    
    def _save_text_changes(self):
        """保存文本修改到文件"""
        if not self._text_modified:
            return
        
        try:
            # 获取文本视图中的内容
            start_iter = self.text_buf.get_start_iter()
            end_iter = self.text_buf.get_end_iter()
            content = self.text_buf.get_text(start_iter, end_iter, False)
            
            # 确保有Document Dashboard文件夹
            log_dir = os.path.dirname(LOG_FILE)
            if not os.path.isdir(log_dir):
                os.makedirs(log_dir, exist_ok=True)
            
            # 保存到文件
            with open(LOG_FILE, "w", encoding="utf-8") as fh:
                fh.write(content)
            
            # 重新加载并学习
            self.load_log()
            self._learn_from_existing_log()
            
            self._text_modified = False
            self._set_status("已保存文本修改")
            print(f"[zhiji] Saved text changes to {LOG_FILE}")
        except Exception as e:
            self._set_status(f"保存失败：{str(e)[:50]}")
            print(f"[zhiji] Failed to save text changes: {e}")

    # -- Context menu -------------------------------------------------------

    def _on_log_button_press(self, widget, event):
        bx, by = self.text_view.window_to_buffer_coords(
            Gtk.TextWindowType.WIDGET, int(event.x), int(event.y)
        )
        it = self.text_view.get_iter_at_location(bx, by)
        if it and hasattr(it, '__getitem__'):
            click_iter = it[1]
            click_line = click_iter.get_line()
        elif hasattr(it, 'get_line'):
            click_iter = it
            click_line = click_iter.get_line()
        else:
            click_line = 0
            click_iter = None

        if event.button == 1 and click_iter:
            # 左键点击：选中整行
            line_start = click_iter.copy()
            line_start.set_line(click_line)
            line_end = line_start.copy()
            if not line_end.ends_line():
                line_end.forward_to_line_end()
            self.text_buf.select_range(line_start, line_end)
            return True

        if event.button != 3:
            return False

        menu = Gtk.Menu()
        menu.override_background_color(Gtk.StateFlags.NORMAL, Gdk.RGBA(1, 1, 1, 1))

        for label_text, callback in [
            ("修改此条记录", lambda _, ln=click_line: self._edit_line(ln)),
            ("查看离线库", lambda _: self._show_offline_lib()),
            ("导出CSV", lambda _: self.export_csv()),
            ("清空所有记录", lambda _: self.clear_log()),
        ]:
            item = Gtk.MenuItem()
            lbl = Gtk.Label(label=label_text)
            lbl.override_color(Gtk.StateFlags.NORMAL, Gdk.RGBA(0, 0, 0, 1))
            lbl.set_halign(Gtk.Align.START)
            item.add(lbl)
            item.override_background_color(Gtk.StateFlags.NORMAL, Gdk.RGBA(1, 1, 1, 1))
            item.override_background_color(Gtk.StateFlags.PRELIGHT, Gdk.RGBA(0.3, 0.56, 0.85, 1))
            item.connect("activate", callback)
            menu.append(item)

        menu.show_all()
        menu.popup_at_pointer(event)
        return True

    # -- Edit record --------------------------------------------------------

    def _edit_line(self, view_line):
        if not os.path.isfile(LOG_FILE):
            self._set_status("无记录")
            return
        with open(LOG_FILE, "r", encoding="utf-8") as fh:
            all_lines = fh.readlines()
        if not all_lines:
            self._set_status("无记录")
            return

        total = len(all_lines)
        shown = min(total, LOG_TAIL_LINES)
        offset = total - shown
        file_idx = offset + view_line
        if file_idx < 0 or file_idx >= total:
            self._set_status("无法定位记录")
            return

        old_text = all_lines[file_idx].rstrip("\n")
        dialog = Gtk.Dialog(
            title="修改记录",
            transient_for=self.win,
            flags=Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
        )
        delete_btn = dialog.add_button("删除", Gtk.ResponseType.REJECT)
        cancel_btn = dialog.add_button("取消", Gtk.ResponseType.CANCEL)
        ok_btn = dialog.add_button("确定", Gtk.ResponseType.OK)
        
        # 应用按钮样式
        self._style_button(delete_btn, "delete")
        self._style_button(cancel_btn, "cancel")
        self._style_button(ok_btn, "ok")
        
        dialog.set_default_response(Gtk.ResponseType.OK)
        dialog.set_default_size(WIN_W + 80, -1)

        box = dialog.get_content_area()
        box.set_spacing(4)
        box.set_margin_start(6)
        box.set_margin_end(6)
        box.set_margin_top(4)
        box.set_margin_bottom(4)

        # 提取时间戳和内容（用于语音输入时参考）
        import re
        timestamp_pattern = r"^(\d{4}年\d{1,2}月\d{1,2}日\d{2}:\d{2}:\d{2}|\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\s*"
        timestamp_match = re.match(timestamp_pattern, old_text)
        timestamp = timestamp_match.group(1) if timestamp_match else ""
        orig_content = re.sub(timestamp_pattern, "", old_text)

        # 语音输入按钮和输入框的容器
        input_box = Gtk.Box(spacing=4, orientation=Gtk.Orientation.VERTICAL)
        
        # 语音按钮行
        voice_btn_box = Gtk.Box(spacing=4)
        voice_btn = Gtk.Button(label="🎤 语音输入（仅改内容）")
        voice_btn.set_tooltip_text("点击开始语音输入，再次点击停止\n语音输入仅修改内容，保留时间戳")
        self._style_button(voice_btn, "normal")
        voice_status_label = Gtk.Label(label="就绪")
        
        voice_btn_box.pack_start(voice_btn, False, False, 0)
        voice_btn_box.pack_start(voice_status_label, False, False, 0)
        input_box.pack_start(voice_btn_box, False, False, 0)

        # 输入框（显示完整文本，可修改时间戳）
        entry = Gtk.Entry()
        entry.set_text(old_text)
        entry.set_activates_default(True)
        input_box.pack_start(entry, False, False, 0)

        # 说明标签
        hint_label = Gtk.Label(label="� 提示：打字可修改时间戳，语音输入仅修改内容")
        hint_label.set_halign(Gtk.Align.START)
        hint_label.override_color(Gtk.StateFlags.NORMAL, Gdk.RGBA(0.5, 0.5, 0.5, 1))
        input_box.pack_start(hint_label, False, False, 0)

        box.pack_start(input_box, False, False, 0)

        # 语音输入状态
        edit_recording = [False]
        edit_rec_proc = [None]
        edit_stop_event = [None]

        def on_voice_clicked(btn):
            if edit_recording[0]:
                # 停止录音
                edit_recording[0] = False
                if edit_stop_event[0]:
                    edit_stop_event[0].set()
                if edit_rec_proc[0] and edit_rec_proc[0].poll() is None:
                    import signal
                    try:
                        edit_rec_proc[0].send_signal(signal.SIGTERM)
                    except OSError:
                        try:
                            edit_rec_proc[0].kill()
                        except OSError:
                            pass
                btn.set_label("🎤 语音输入")
                voice_status_label.set_text("正在处理...")
                return

            # 开始录音
            if not self._check_audio_tools():
                return

            edit_recording[0] = True
            btn.set_label("⏹ 停止录音")
            voice_status_label.set_text("正在录音...")

            def do_edit_record():
                import wave
                import struct
                import time
                import queue

                try:
                    recorded = False
                    rec_tool = None

                    # 检测可用的录音工具
                    try:
                        subprocess.check_output(["arecord", "--help"], stderr=subprocess.STDOUT)
                        rec_tool = "arecord"
                    except (subprocess.CalledProcessError, FileNotFoundError):
                        try:
                            subprocess.check_output(["ffmpeg", "-version"], stderr=subprocess.STDOUT)
                            rec_tool = "ffmpeg"
                        except (subprocess.CalledProcessError, FileNotFoundError):
                            pass

                    if not rec_tool:
                        GLib.idle_add(lambda: voice_status_label.set_text("录音失败：未找到工具"))
                        edit_recording[0] = False
                        GLib.idle_add(lambda: btn.set_label("🎤 语音输入"))
                        return

                    audio_queue = queue.Queue()
                    stop_event = threading.Event()
                    edit_stop_event[0] = stop_event

                    def record_thread():
                        try:
                            if rec_tool == "arecord":
                                proc = subprocess.Popen(
                                    [
                                        "arecord",
                                        "-f", "S16_LE",
                                        "-r", str(VOICE_SAMPLE_RATE),
                                        "-c", str(VOICE_CHANNELS),
                                    ],
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.DEVNULL,
                                    bufsize=0
                                )
                            else:
                                proc = subprocess.Popen(
                                    [
                                        "ffmpeg", "-y",
                                        "-f", "pulse", "-i", "default",
                                        "-ac", str(VOICE_CHANNELS), "-ar", str(VOICE_SAMPLE_RATE),
                                        "-f", "s16le", "-acodec", "pcm_s16le", "-",
                                    ],
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.DEVNULL,
                                    bufsize=0
                                )

                            edit_rec_proc[0] = proc
                            chunk_size = 3200
                            while not stop_event.is_set():
                                data = proc.stdout.read(chunk_size)
                                if len(data) == 0:
                                    break
                                audio_queue.put(data)
                        except Exception:
                            pass
                        finally:
                            if edit_rec_proc[0] and edit_rec_proc[0].poll() is None:
                                edit_rec_proc[0].terminate()
                                edit_rec_proc[0].wait(timeout=1)

                    # 处理线程
                    def process_thread():
                        nonlocal recorded
                        try:
                            temp_wav = os.path.join(tempfile.gettempdir(), f"zhiji_edit_{int(time.time())}.wav")
                            wav_file = wave.open(temp_wav, "wb")
                            wav_file.setnchannels(VOICE_CHANNELS)
                            wav_file.setsampwidth(2)
                            wav_file.setframerate(VOICE_SAMPLE_RATE)

                            last_sound_time = time.time()
                            silence_threshold = VOICE_SILENCE_THRESHOLD
                            started = False
                            buffer = []

                            while not stop_event.is_set():
                                try:
                                    data = audio_queue.get(timeout=0.1)
                                except queue.Empty:
                                    if started and (time.time() - last_sound_time) > silence_threshold:
                                        break
                                    continue

                                has_sound = False
                                num_samples = len(data) // 2
                                if num_samples > 0:
                                    format_str = f"<{num_samples}h"
                                    samples = struct.unpack(format_str, data)
                                    max_amplitude = max(abs(s) for s in samples)
                                    if max_amplitude > VOICE_AMPLITUDE_THRESHOLD:
                                        has_sound = True
                                        last_sound_time = time.time()
                                        if not started:
                                            started = True

                                if started:
                                    buffer.append(data)

                            if buffer:
                                for d in buffer:
                                    wav_file.writeframes(d)
                                wav_file.close()
                                recorded = True

                                # 识别
                                GLib.idle_add(lambda: voice_status_label.set_text("正在识别..."))
                                text, source = self._recognize(temp_wav, mode=self.rec_mode)
                                if text:
                                    # 语音输入：保留时间戳，只替换内容
                                    def update_entry():
                                        current_text = entry.get_text()
                                        curr_timestamp_match = re.match(timestamp_pattern, current_text)
                                        if curr_timestamp_match:
                                            # 如果有时间戳，保留它
                                            curr_timestamp = curr_timestamp_match.group(1)
                                            entry.set_text(f"{curr_timestamp} {text}")
                                        else:
                                            # 如果没有时间戳，使用原始时间戳
                                            if timestamp:
                                                entry.set_text(f"{timestamp} {text}")
                                            else:
                                                entry.set_text(text)
                                    
                                    GLib.idle_add(update_entry)
                                    GLib.idle_add(lambda: voice_status_label.set_text("识别完成（时间戳已保留）"))
                                else:
                                    GLib.idle_add(lambda: voice_status_label.set_text("识别失败"))

                                # 清理
                                try:
                                    os.remove(temp_wav)
                                except OSError:
                                    pass
                            else:
                                GLib.idle_add(lambda: voice_status_label.set_text("未检测到声音"))
                                wav_file.close()
                                try:
                                    os.remove(temp_wav)
                                except OSError:
                                    pass

                        except Exception as e:
                            GLib.idle_add(lambda err=str(e): voice_status_label.set_text(f"错误: {err[:30]}"))
                        finally:
                            edit_recording[0] = False
                            GLib.idle_add(lambda: btn.set_label("🎤 语音输入"))

                    rec_t = threading.Thread(target=record_thread, daemon=True)
                    proc_t = threading.Thread(target=process_thread, daemon=True)
                    rec_t.start()
                    proc_t.start()

                except Exception as e:
                    GLib.idle_add(lambda err=str(e): voice_status_label.set_text(f"错误: {err[:30]}"))
                    edit_recording[0] = False
                    GLib.idle_add(lambda: btn.set_label("🎤 语音输入"))

            t = threading.Thread(target=do_edit_record, daemon=True)
            t.start()

        voice_btn.connect("clicked", on_voice_clicked)

        dialog.show_all()
        resp = dialog.run()
        new_content = entry.get_text().strip()
        
        # 停止录音（如果正在录音）
        if edit_recording[0]:
            edit_recording[0] = False
            if edit_stop_event[0]:
                edit_stop_event[0].set()
        
        dialog.destroy()

        if resp == Gtk.ResponseType.OK and new_content:
            # 输入框现在是完整文本，直接使用
            new_text = new_content
            
            # 提取内容用于离线库学习（去除时间戳）
            new_content_only = re.sub(timestamp_pattern, "", new_text)
            
            # 保存修改映射到离线库
            if orig_content and new_content_only and orig_content != new_content_only:
                saved = self.phrase_learner.save_correction(orig_content, new_content_only)
                if saved:
                    self._set_status("已修改并学习到离线库")
                else:
                    self._set_status("已修改")
            else:
                self._set_status("已修改")
            
            all_lines[file_idx] = new_text + "\n"
            with open(LOG_FILE, "w", encoding="utf-8") as fh:
                fh.writelines(all_lines)
            self.load_log()
        elif resp == Gtk.ResponseType.REJECT:
            del all_lines[file_idx]
            with open(LOG_FILE, "w", encoding="utf-8") as fh:
                fh.writelines(all_lines)
            self.load_log()
            self._set_status("已删除")
        else:
            self._set_status("取消修改")

    # -- Export / Clear -----------------------------------------------------

    def export_csv(self):
        if not os.path.isfile(LOG_FILE):
            self._set_status("无记录可导出")
            return

        try:
            with open(LOG_FILE, "r", encoding="utf-8") as fh:
                lines = [l.strip() for l in fh if l.strip()]

            with open(EXPORT_FILE, "w", encoding="utf-8-sig", newline="") as fh:
                writer = csv.writer(fh)
                writer.writerow(["序号", "时间", "备注"])
                import re
                # 支持两种时间格式
                ts_pat = re.compile(r"^(\d{4}年\d{1,2}月\d{1,2}日\d{2}:\d{2}:\d{2}|\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\s*(.*)")
                for idx, line in enumerate(lines, 1):
                    m = ts_pat.match(line)
                    if m:
                        writer.writerow([idx, m.group(1), m.group(2)])
                    else:
                        writer.writerow([idx, line, ""])

            self._set_status(f"已导出 {len(lines)} 条到 {EXPORT_FILE}")
        except Exception as e:
            self._set_status(f"导出失败：{e}")

    def clear_log(self):
        dialog = Gtk.MessageDialog(
            transient_for=self.win,
            flags=Gtk.DialogFlags.MODAL,
            message_type=Gtk.MessageType.WARNING,
            buttons=Gtk.ButtonsType.OK_CANCEL,
            text="确认清空所有记录？",
        )
        dialog.format_secondary_text("此操作不可撤销。")
        resp = dialog.run()
        dialog.destroy()

        if resp == Gtk.ResponseType.OK:
            with open(LOG_FILE, "w", encoding="utf-8") as fh:
                fh.truncate(0)
            self.load_log()
            self._set_status("记录已清空")

    # -- Error dialog -------------------------------------------------------

    def _show_error(self, title, body):
        dialog = Gtk.MessageDialog(
            transient_for=self.win,
            flags=Gtk.DialogFlags.MODAL,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.CLOSE,
            text=title,
        )
        dialog.format_secondary_text(body)
        dialog.run()
        dialog.destroy()

    def _show_paginated_dialog(self, title, content, lines_per_page=30):
        """显示带翻页功能的对话框"""
        # 将内容按行分割
        lines = content.split('\n')
        
        # 分页
        pages = []
        for i in range(0, len(lines), lines_per_page):
            pages.append('\n'.join(lines[i:i + lines_per_page]))
        
        if not pages:
            pages = [""]
        
        # 创建对话框
        dialog = Gtk.Dialog(
            title=title,
            transient_for=self.win,
            flags=Gtk.DialogFlags.MODAL,
        )
        dialog.set_default_size(600, 500)
        
        # 应用CSS样式来提高对比度
        provider = Gtk.CssProvider()
        css = """
            /* 文本视图样式 - 高对比度 */
            .high-contrast-text {
                background-color: #ffffff;
                color: #000000;
            }
            /* 对话框样式 */
            dialog {
                background-color: #f5f5f5;
            }
        """
        provider.load_from_data(css.encode('utf-8'))
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
        
        # 内容区域
        content_area = dialog.get_content_area()
        content_area.set_spacing(15)
        content_area.set_margin_top(15)
        content_area.set_margin_bottom(15)
        content_area.set_margin_start(15)
        content_area.set_margin_end(15)
        
        # 文本显示区域 - 高对比度样式
        text_view = Gtk.TextView()
        text_view.set_editable(False)
        text_view.set_cursor_visible(True)
        text_view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        text_view.override_font(Pango.FontDescription("Sans 12"))
        text_view.override_background_color(Gtk.StateFlags.NORMAL, Gdk.RGBA(1.0, 1.0, 1.0, 1.0))
        text_view.override_color(Gtk.StateFlags.NORMAL, Gdk.RGBA(0.0, 0.0, 0.0, 1.0))
        text_view.get_style_context().add_class("high-contrast-text")
        text_buf = text_view.get_buffer()
        
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scroll.set_min_content_height(350)
        scroll.add(text_view)
        content_area.pack_start(scroll, True, True, 0)
        
        # 页码显示 - 更醒目的样式
        page_info = Gtk.Label()
        page_info.set_halign(Gtk.Align.CENTER)
        page_info.override_font(Pango.FontDescription("Sans Bold 11"))
        page_info.override_color(Gtk.StateFlags.NORMAL, Gdk.RGBA(0.2, 0.2, 0.8, 1.0))
        
        # 翻页按钮 - 高对比度样式
        btn_box = Gtk.Box(spacing=15)
        btn_box.set_halign(Gtk.Align.CENTER)
        
        prev_btn = Gtk.Button(label="◀ 上一页")
        prev_btn.set_sensitive(False)
        self._style_button(prev_btn, "normal")
        
        next_btn = Gtk.Button(label="下一页 ▶")
        self._style_button(next_btn, "normal")
        
        btn_box.pack_start(prev_btn, False, False, 0)
        btn_box.pack_start(page_info, False, False, 0)
        btn_box.pack_start(next_btn, False, False, 0)
        
        content_area.pack_start(btn_box, False, False, 0)
        
        # 添加关闭按钮
        close_btn = dialog.add_button("关闭", Gtk.ResponseType.CLOSE)
        self._style_button(close_btn, "cancel")
        
        # 跟踪当前页码
        current_page = [0]  # 使用列表来允许在闭包中修改
        
        def update_page():
            text_buf.set_text(pages[current_page[0]])
            page_info.set_text(f"第 {current_page[0] + 1}/{len(pages)} 页")
            prev_btn.set_sensitive(current_page[0] > 0)
            next_btn.set_sensitive(current_page[0] < len(pages) - 1)
            # 滚动到顶部
            text_buf.place_cursor(text_buf.get_start_iter())
        
        def on_prev(_):
            if current_page[0] > 0:
                current_page[0] -= 1
                update_page()
        
        def on_next(_):
            if current_page[0] < len(pages) - 1:
                current_page[0] += 1
                update_page()
        
        prev_btn.connect("clicked", on_prev)
        next_btn.connect("clicked", on_next)
        
        # 初始化显示
        update_page()
        dialog.show_all()
        dialog.run()
        dialog.destroy()
    
    def _show_help(self):
        """显示使用说明对话框"""
        print(f"[FUNC] _show_help called")
        help_content = """
智记使用说明

📅 基本操作

1. 「记录」按钮：快速添加一条当前时间的文本记录
2. 「语音」按钮：开始录音，支持智能静音检测
3. 📅格式按钮：切换中文/ISO时间显示格式
4. ?帮助按钮：查看此说明

⏱️ 录音功能

- 点击「语音」按钮开始录音，再次点击可停止
- 最长录制18秒，5秒静音自动停止
- 支持在线识别（讯飞）和离线识别（Whisper）
- 支持普通话、四川话、河南话三种口音
- 根据离线库学习情况动态调整识别优先级
- 识别结果自动记录到文件

✏️ 编辑记录

- 左键点击任意记录选中整行
- 右键点击显示菜单，选择「修改此条记录」
- 修改后的文本会自动学习到离线库
- 后续识别类似内容时会自动修正

📚 离线库功能

- 自动学习常见词汇和短语
- 按口音分类存储（四川话、河南话、普通话、Whisper）
- 识别时优先匹配对应口音的离线库
- 可通过「查看离线库」查看学习内容

🖱️ 右键菜单

在记录区域右键可访问：
- 修改此条记录
- 查看离线库
- 导出CSV
- 清空所有记录

📥 托盘菜单

右键托盘图标可访问：
- 显示窗口
- 时间格式（切换格式）
- 使用说明
- 退出程序

📝 日志功能

- 所有识别过程会保存到「Log」文件夹
- 日志文件自动保留2天，超过自动清理
"""
        self._show_paginated_dialog(f"智记 v{VERSION} — 使用说明", help_content, lines_per_page=25)

    def _show_offline_lib(self):
        lib = self.phrase_learner.get_offline_lib()
        corrections = self.phrase_learner.get_corrections()
        accent_lib = self.phrase_learner.get_accent_lib()
        
        has_content = False
        if lib or corrections:
            has_content = True
        else:
            for accent_name, accent_dict in accent_lib.items():
                if accent_dict:
                    has_content = True
                    break
        
        if not has_content:
            self._set_status("离线库为空，继续使用将自动学习")
            return
        
        content = ""
        
        # 显示修改映射
        if corrections:
            content += "【自动修正映射】\n" + "-" * 30 + "\n"
            corr_items = sorted(corrections.items(), key=lambda x: x[1].get("count", 0), reverse=True)
            for key, info in corr_items:
                content += f"→ {info['original']}\n  ↳ {info['corrected']} [{info.get('count', 0)}次]\n"
            content += "\n"
        
        # 显示按口音分类的学习词汇
        for accent_name in ["sichuan", "henan", "mandarin", "whisper"]:
            accent_dict = accent_lib.get(accent_name, {})
            if accent_dict:
                accent_display = {
                    "sichuan": "四川话",
                    "henan": "河南话",
                    "mandarin": "普通话",
                    "whisper": "Whisper离线"
                }.get(accent_name, accent_name)
                content += f"【{accent_display}】\n" + "-" * 30 + "\n"
                items = sorted(accent_dict.items(), key=lambda x: x[1].get("count", 0), reverse=True)
                count = 0
                for phrase, info in items:
                    if info.get("learned"):
                        content += f"[{info.get('count', 0)}次] {phrase}\n"
                        count += 1
                if count == 0:
                    content += "（无已学习内容）\n"
                content += "\n"
        
        # 显示通用学习的词汇（仅当没有口音库时显示）
        has_accent_content = any(accent_lib.values())
        if lib and not has_accent_content:
            content += "【词汇学习库】\n" + "-" * 30 + "\n"
            items = sorted(lib.items(), key=lambda x: x[1].get("count", 0), reverse=True)
            for phrase, info in items:
                content += f"[{info.get('count', 0)}次] {phrase}\n"
        
        total_items = len(corrections) + len(lib)
        self._show_paginated_dialog(f"离线库 ({total_items}条)", content, lines_per_page=30)


# ---------------------------------------------------------------------------
# Single instance check
# ---------------------------------------------------------------------------
def check_single_instance():
    """检查是否已有程序实例在运行"""
    import os
    import sys
    
    # 使用项目目录下的锁定文件
    lock_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "zhiji.lock")
    
    try:
        # 检查平台并使用相应的锁定方式
        if sys.platform.startswith('win'):
            # Windows系统使用msvcrt
            import msvcrt
            fp = open(lock_file, 'w')
            try:
                msvcrt.locking(fp.fileno(), msvcrt.LK_NBLCK, 1)
            except IOError:
                print("智记已经在运行中！")
                fp.close()
                return None
        else:
            # Linux/macOS系统使用fcntl
            import fcntl
            fp = open(lock_file, 'w')
            try:
                fcntl.lockf(fp, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except IOError:
                print("智记已经在运行中！")
                fp.close()
                return None
        
        # 成功获取锁，保存当前PID
        fp.write(str(os.getpid()))
        fp.flush()
        
        # 返回锁的文件对象，保持锁直到程序退出
        return fp
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Cleanup function
# ---------------------------------------------------------------------------
def cleanup(lock_fp=None):
    """清理资源"""
    try:
        if lock_fp:
            lock_fp.close()
    except Exception:
        pass
    try:
        lock_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "zhiji.lock")
        if os.path.exists(lock_file):
            os.remove(lock_file)
    except Exception:
        pass


def handle_signal(signum, frame):
    """处理系统信号"""
    Gtk.main_quit()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    # 检查单实例
    lock_fp = check_single_instance()
    if lock_fp is None:
        import sys
        sys.exit(1)
    
    # 注册清理函数
    atexit.register(lambda: cleanup(lock_fp))
    
    # 注册信号处理（Linux）
    if not sys.platform.startswith('win'):
        signal.signal(signal.SIGINT, handle_signal)
        signal.signal(signal.SIGTERM, handle_signal)
    
    try:
        ZhiJiApp()
        Gtk.main()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"程序异常: {e}")
    finally:
        cleanup(lock_fp)

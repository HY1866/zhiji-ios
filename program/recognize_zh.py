#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Speech recognition: iFlytek WebSocket API (online) with Whisper fallback (offline)."""
import base64
import hashlib
import hmac
import json
import os
import re
import subprocess
import sys
import time
import wave
from datetime import datetime, timezone
from urllib.parse import urlencode, urlparse

try:
    import websocket
except ImportError:
    subprocess.check_call([
        sys.executable, "-m", "pip", "install", "--user", "-q",
        "-i", "https://pypi.tuna.tsinghua.edu.cn/simple",
        "websocket-client",
    ])
    import websocket

os.environ["LC_ALL"] = "C.UTF-8"
os.environ["LANG"] = "C.UTF-8"
os.environ["LC_CTYPE"] = "C.UTF-8"
os.environ["PYTHONIOENCODING"] = "utf-8"

XUNFEI_APPID = "a1d0524e"
XUNFEI_API_KEY = "db0ba5aad76660783466e22e430d1074"
XUNFEI_API_SECRET = "Nzg2YzRiYmMzZDI2MDRjNjUyYWFiYWRi"
XUNFEI_URL = "wss://iat-api.xfyun.cn/v2/iat"

# Offline data paths
OFFLINE_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Offline data")
OFFLINE_LIB_PATH = os.path.join(OFFLINE_DATA_DIR, "智记_离线库.json")
WHISPER_MODEL_DIR = os.path.join(OFFLINE_DATA_DIR, "whisper-models")

# Log management
LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Log")
_log_file = None

def _cleanup_old_logs():
    """删除两天前的旧日志文件"""
    try:
        if not os.path.exists(LOG_DIR):
            return

        now = datetime.now()
        two_days_ago = now - 60 * 60 * 24 * 2  # 两天

        deleted_count = 0
        for filename in os.listdir(LOG_DIR):
            if not filename.startswith("recognize_") or not filename.endswith(".log"):
                continue

            file_path = os.path.join(LOG_DIR, filename)
            if not os.path.isfile(file_path):
                continue

            # 从文件名提取日期（格式：recognize_YYYYMMDD_HHMMSS.log）
            # 例如：recognize_20260516_085909.log
            try:
                date_str = filename.replace("recognize_", "").split("_")[0]  # 提取 YYYYMMDD
                file_date = datetime.strptime(date_str, "%Y%m%d")
            except (ValueError, IndexError):
                # 如果文件名格式不对，使用文件修改时间
                file_date = datetime.fromtimestamp(os.path.getmtime(file_path))

            # 如果文件日期早于两天前，删除
            if file_date < two_days_ago:
                try:
                    os.remove(file_path)
                    deleted_count += 1
                except Exception as e:
                    # 静默失败，不影响主程序
                    pass

        if deleted_count > 0:
            print(f"[LOG] Cleaned up {deleted_count} old log files", file=sys.stderr)
    except Exception as e:
        # 静默失败，不影响主程序
        pass


def _setup_logging():
    """设置日志输出到文件，同时保留stderr输出"""
    global _log_file
    
    # 先清理旧日志
    _cleanup_old_logs()
    
    # 确保Log目录存在
    if not os.path.exists(LOG_DIR):
        try:
            os.makedirs(LOG_DIR, exist_ok=True)
        except Exception as e:
            print(f"Warning: Cannot create Log directory: {e}", file=sys.stderr)
            return
    
    # 创建带时间戳的日志文件
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file_path = os.path.join(LOG_DIR, f"recognize_{timestamp}.log")
    
    try:
        _log_file = open(log_file_path, 'w', encoding='utf-8')
        print(f"[LOG] Logging to: {log_file_path}", file=sys.stderr)
        print(f"[LOG] Log session started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", file=_log_file)
        print("="*70, file=_log_file)
        _log_file.flush()
    except Exception as e:
        print(f"Warning: Cannot open log file: {e}", file=sys.stderr)

def _log(message, also_stderr=True):
    """写日志到文件，可选同时输出到stderr"""
    # 总是输出到stderr
    if also_stderr:
        sys.stderr.write(message + "\n")
        sys.stderr.flush()
    
    # 输出到文件
    if _log_file:
        try:
            _log_file.write(message + "\n")
            _log_file.flush()
        except Exception:
            pass

def _close_logging():
    """关闭日志文件"""
    global _log_file
    if _log_file:
        try:
            print("="*70, file=_log_file)
            print(f"[LOG] Log session ended at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", file=_log_file)
            _log_file.close()
        except Exception:
            pass
        _log_file = None

# 初始化日志
_setup_logging()


def _load_offline_lib():
    """Load offline library for matching similar phrases."""
    if not os.path.exists(OFFLINE_LIB_PATH):
        return None
    try:
        with open(OFFLINE_LIB_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        _log(f"[recognize] load offline lib failed: {e}")
        return None


def _get_accent_priority(offline_lib):
    """根据离线库中各口音的使用统计，动态调整口音尝试优先级"""
    _log("")
    _log("="*60)
    _log("[ACCOUNT PRIORITY] Starting to calculate accent priority...")
    
    if not offline_lib:
        # 默认优先级：普通话 -> 四川话 -> 河南话
        _log("[ACCOUNT PRIORITY] No offline lib, using default priority: ['mandarin', 'sichuan', 'henan']")
        _log("="*60)
        _log("")
        return ["mandarin", "sichuan", "henan"]
    
    accent_lib = offline_lib.get("accent_lib", {})
    accent_counts = {}
    
    # 统计各口音的短语数量
    _log("[ACCOUNT PRIORITY] Counting learned phrases by accent...")
    for accent in ["sichuan", "henan", "mandarin", "whisper"]:
        phrases = accent_lib.get(accent, {})
        count = 0
        learned_list = []
        for phrase_key, phrase_data in phrases.items():
            if phrase_data.get("learned"):
                count += 1
                learned_list.append(phrase_data.get("phrase", ""))
        accent_counts[accent] = count
        _log(f"[ACCOUNT PRIORITY] - '{accent}': {count} learned phrases")
        if learned_list:
            _log(f"[ACCOUNT PRIORITY]   Sample phrases: {str(learned_list[:5])}")
    
    # 按使用频率排序（从高到低）
    sorted_accents = sorted(
        accent_counts.items(),
        key=lambda x: x[1],
        reverse=True
    )
    
    _log(f"[ACCOUNT PRIORITY] Sorted accents by count: {sorted_accents}")
    
    # 构建优先级列表，确保所有口音都包含
    priority = []
    for accent, count in sorted_accents:
        if accent != "whisper":  # whisper是最后兜底
            priority.append(accent)
            _log(f"[ACCOUNT PRIORITY] Adding '{accent}' (count={count}) to priority list")
    
    # 添加剩余口音
    for accent in ["mandarin", "sichuan", "henan"]:
        if accent not in priority:
            priority.append(accent)
            _log(f"[ACCOUNT PRIORITY] Adding fallback accent '{accent}'")
    
    _log(f"[ACCOUNT PRIORITY] Final priority order: {priority}")
    _log("="*60)
    _log("")
    return priority


def _match_offline_lib_with_accent(text, offline_lib, source=None):
    """Match recognized text with offline library, with accent priority.
    
    优先匹配对应口音的离线库，如果没有则匹配通用离线库。
    """
    _log("")
    _log("="*60)
    _log(f"[OFFLINE MATCH] Starting match: text='{text}', source='{source}'")
    
    if not offline_lib or not text:
        _log(f"[OFFLINE MATCH] No offline lib or empty text, returning original: '{text}'")
        _log("="*60)
        _log("")
        return text
    
    # First check corrections (global)
    corrections = offline_lib.get("corrections", {})
    _log(f"[OFFLINE MATCH] Checking {len(corrections)} correction rules...")
    if text in corrections:
        corrected = corrections[text]["corrected"]
        _log(f"[OFFLINE MATCH] ✓ Found EXACT correction: '{text}' -> '{corrected}'")
        _log("="*60)
        _log("")
        return corrected
    else:
        _log(f"[OFFLINE MATCH] No exact correction found for '{text}'")
    
    # 确定当前识别使用的口音
    current_accent = None
    if source:
        if "sichuan" in source:
            current_accent = "sichuan"
        elif "henan" in source:
            current_accent = "henan"
        elif "mandarin" in source:
            current_accent = "mandarin"
    _log(f"[OFFLINE MATCH] Detected accent from source: {current_accent}")
    
    # 构建口音匹配优先级：当前口音 -> 其他口音 -> 通用离线库
    match_order = []
    if current_accent:
        match_order.append(current_accent)
    
    # 添加其他口音
    for accent in ["sichuan", "henan", "mandarin"]:
        if accent != current_accent and accent not in match_order:
            match_order.append(accent)
    
    _log(f"[OFFLINE MATCH] Match priority: {match_order}")
    
    # 按优先级尝试匹配
    best_match = None
    best_score = 0
    matched_accent = None
    all_candidates = []
    
    # 获取accent_lib
    accent_lib = offline_lib.get("accent_lib", {})
    
    # 先尝试按口音匹配
    _log("")
    _log("[OFFLINE MATCH] Step 1: Checking accent-specific libraries...")
    for accent in match_order:
        phrases = accent_lib.get(accent, {})
        _log(f"[OFFLINE MATCH] - Checking accent '{accent}' (has {len(phrases)} total phrases)")
        
        learned_count = 0
        for phrase_key, phrase_data in phrases.items():
            if not phrase_data.get("learned"):
                continue
            learned_count += 1
            
            phrase = phrase_data["phrase"]
            # Simple overlap score
            text_chars = set(text)
            phrase_chars = set(phrase)
            common_chars = text_chars & phrase_chars
            score = len(common_chars) / max(len(text), len(phrase))
            
            # 对应口音的短语有加分
            bonus = 0.0
            if accent == current_accent:
                bonus = 0.1
                score += bonus
            
            candidate = {
                "accent": accent,
                "phrase": phrase,
                "raw_score": score - bonus,
                "bonus": bonus,
                "total_score": score,
                "text_chars": str(text_chars),
                "phrase_chars": str(phrase_chars),
                "common_chars": str(common_chars),
                "common_count": len(common_chars)
            }
            all_candidates.append(candidate)
            
            if score > 0.6 and score > best_score:
                best_score = score
                best_match = phrase
                matched_accent = accent
                _log(f"[OFFLINE MATCH]   → New best! '{phrase}' (score={score:.3f}, bonus={bonus:.2f})")
        
        _log(f"[OFFLINE MATCH]   Checked {learned_count} learned phrases for '{accent}'")
    
    # 如果按口音没找到，尝试通用离线库
    if not best_match:
        _log("")
        _log("[OFFLINE MATCH] Step 2: No accent match, checking general offline lib...")
        offline_phrases = offline_lib.get("offline_lib", {})
        _log(f"[OFFLINE MATCH] - Checking {len(offline_phrases)} general phrases...")
        
        for phrase_key, phrase_data in offline_phrases.items():
            phrase = phrase_data["phrase"]
            text_chars = set(text)
            phrase_chars = set(phrase)
            common_chars = text_chars & phrase_chars
            score = len(common_chars) / max(len(text), len(phrase))
            
            candidate = {
                "accent": "general",
                "phrase": phrase,
                "raw_score": score,
                "bonus": 0.0,
                "total_score": score,
                "text_chars": str(text_chars),
                "phrase_chars": str(phrase_chars),
                "common_chars": str(common_chars),
                "common_count": len(common_chars)
            }
            all_candidates.append(candidate)
            
            if score > 0.6 and score > best_score:
                best_score = score
                best_match = phrase
                matched_accent = "general"
                _log(f"[OFFLINE MATCH]   → New best in general lib! '{phrase}' (score={score:.3f})")
    
    # 打印所有候选（用于调试）
    _log("")
    _log("[OFFLINE MATCH] All candidates (sorted by score):")
    all_candidates.sort(key=lambda x: x["total_score"], reverse=True)
    for i, candidate in enumerate(all_candidates[:8]):  # 只打印前8个
        is_best = " ★" if candidate["phrase"] == best_match else ""
        _log(f"[OFFLINE MATCH]   {i+1}. '{candidate['phrase']}' (accent={candidate['accent']}, "
                          f"score={candidate['total_score']:.3f}, raw={candidate['raw_score']:.3f}, "
                          f"bonus={candidate['bonus']:.2f}){is_best}")
        if i < 3:  # 前3个显示详细匹配信息
            _log(f"[OFFLINE MATCH]       Text chars: {candidate['text_chars']}")
            _log(f"[OFFLINE MATCH]       Phrase chars: {candidate['phrase_chars']}")
            _log(f"[OFFLINE MATCH]       Common chars: {candidate['common_chars']} (count={candidate['common_count']})")
    
    if best_match and best_score > 0.7:
        accent_note = f" (accent: {matched_accent})" if matched_accent else ""
        _log(f"\n[OFFLINE MATCH] ✓ SUCCESS! Final match: '{text}' -> '{best_match}' (score={best_score:.3f}){accent_note}")
        _log("="*60)
        _log("")
        return best_match
    elif best_match:
        _log(f"\n[OFFLINE MATCH] ⚠ Found match but score too low: '{best_match}' (score={best_score:.3f} < 0.7)")
        _log("="*60)
        _log("")
        return text
    else:
        _log(f"\n[OFFLINE MATCH] ✗ No match found, returning original: '{text}'")
        _log("="*60)
        _log("")
        return text


def _write_result(data):
    out = json.dumps(data, ensure_ascii=False)
    sys.stdout.buffer.write(out.encode("utf-8"))
    sys.stdout.buffer.write(b"\n")
    sys.stdout.buffer.flush()


def _post_process_text(text):
    if not text:
        return text
    
    # 只将英文字母转大写，中文字符保持原样
    result = ''
    for char in text:
        if 'a' <= char <= 'z':
            result += char.upper()
        else:
            result += char
    
    # 在关键词前添加逗号（先处理长关键词，避免重复替换）
    keywords = sorted(["接管", "安全接管", "R3"], key=len, reverse=True)
    for kw in keywords:
        # 查找所有关键词出现的位置
        while kw in result:
            idx = result.find(kw)
            # 如果关键词不在开头且前面不是逗号，则添加逗号
            if idx > 0 and result[idx-1] != '，':
                result = result[:idx] + '，' + result[idx:]
            idx += len(kw) + 1  # 跳过已处理的部分
    
    return result


def _xunfei_create_url():
    from urllib.parse import urlencode, urlparse
    url_obj = urlparse(XUNFEI_URL)
    now = datetime.now(timezone.utc)
    date = now.strftime("%a, %d %b %Y %H:%M:%S GMT")
    signature_origin = f"host: {url_obj.hostname}\ndate: {date}\nGET {url_obj.path} HTTP/1.1"
    signature_sha = hmac.new(XUNFEI_API_SECRET.encode('utf-8'),
                            signature_origin.encode('utf-8'),
                            digestmod=hashlib.sha256).digest()
    signature = base64.b64encode(signature_sha).decode(encoding='utf-8')
    authorization_origin = f'api_key="{XUNFEI_API_KEY}", algorithm="hmac-sha256", headers="host date request-line", signature="{signature}"'
    authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode(encoding='utf-8')
    v = {
        "authorization": authorization,
        "date": date,
        "host": url_obj.hostname
    }
    url = XUNFEI_URL + '?' + urlencode(v)
    return url


def _convert_audio(audio_path):
    import wave
    import struct
    
    wf = wave.open(audio_path, 'rb')
    channels = wf.getnchannels()
    sample_width = wf.getsampwidth()
    frame_rate = wf.getframerate()
    num_frames = wf.getnframes()
    audio_data = wf.readframes(num_frames)
    wf.close()
    
    # Convert to 16000Hz, mono, 16-bit
    sample_rate = frame_rate
    
    if channels == 2:
        new_data = []
        for i in range(0, len(audio_data), 2 * sample_width):
            sample = 0
            for ch in range(2):
                offset = i + ch * sample_width
                if sample_width == 2:
                    sample += struct.unpack("<h", audio_data[offset:offset+2])[0]
            new_data.append(struct.pack("<h", sample // 2))
        audio_data = b"".join(new_data)
        channels = 1
    
    if sample_rate != 16000:
        ratio = 16000 / sample_rate
        new_len = int(len(audio_data) * ratio)
        new_data = []
        for i in range(new_len):
            src_idx = int(i / ratio)
            new_data.append(audio_data[src_idx:src_idx+2])
        audio_data = b"".join(new_data)
        sample_rate = 16000
    
    _log(f"[recognize] Converted audio: rate={sample_rate}, channels={channels}, data_len={len(audio_data)}")
    return audio_data, sample_rate


def _xunfei_recognize_with_accent(audio_path, accent_name, accent_value):
    """Recognize audio with specific accent.
    
    注意：讯飞API不会返回口音信息，我们在source字段中标记使用的口音。
    """
    audio_data, sample_rate = _convert_audio(audio_path)

    result_parts = []
    ws_finished = [False]
    ws_error = [None]
    last_intermediate_text = [""]

    def on_message(ws, message):
        _log(f"[recognize] Received message: {message[:200]}...")
        try:
            data = json.loads(message)
            code = data.get("code", -1)
            if code != 0:
                ws_error[0] = f"xunfei error code={code}: {data.get('message','')}"
                ws.close()
                return
            result = data.get("data", {}).get("result", {})
            pgs = result.get("pgs", "")
            ws_list = result.get("ws", [])
            
            # 提取当前消息中的所有词
            current_words = []
            for w in ws_list:
                bg = w.get("bg", 0)
                for cw in w.get("cw", []):
                    word = cw.get("w", "")
                    sc = cw.get("sc", 0)
                    if word:
                        current_words.append((word, bg, sc))
            
            _log(f"[recognize] pgs={pgs}, words={[w for w, _, _ in current_words]}")
            
            # 处理动态修正
            if pgs == "rpl":
                # 检查新的ws_list是否只包含标点符号
                new_words = []
                for w in ws_list:
                    for cw in w.get("cw", []):
                        word = cw.get("w", "")
                        if word:
                            new_words.append(word)
                
                # 如果新词只包含标点，不清空之前的结果
                has_real_text = any(not re.match(r'^[,，。.!?！?]+$', w) for w in new_words)
                
                if not has_real_text:
                    _log(f"[recognize] Only punctuation in replacement mode, keeping previous results: {new_words}")
                    # 不添加新的词，因为只是标点
                else:
                    result_parts.clear()
                    _log(f"[recognize] Replacement mode with real text, clearing previous results, new words: {new_words}")
                    # 在 rpl 模式下，ws_list 包含所有词，直接替换 result_parts
                    for w in ws_list:
                        for cw in w.get("cw", []):
                            word = cw.get("w", "")
                            if word:
                                result_parts.append(word)
            elif pgs == "apd":
                # 在 apd（追加）模式下，只添加新的词
                _log(f"[recognize] Append mode, adding new words")
                for w in ws_list:
                    for cw in w.get("cw", []):
                        word = cw.get("w", "")
                        if word:
                            result_parts.append(word)
            else:
                # 其他模式（比如初始识别），添加词
                for w in ws_list:
                    for cw in w.get("cw", []):
                        word = cw.get("w", "")
                        if word:
                            result_parts.append(word)
            
            # 输出中间识别结果
            current_text = "".join(result_parts).strip()
            if current_text and current_text != last_intermediate_text[0]:
                last_intermediate_text[0] = current_text
                # 中间结果也去掉结尾的句号/感叹号/问号
                intermediate_text = re.sub(r"[。！？]+$", "", current_text)
                _write_result({"text": intermediate_text, "source": f"xunfei_{accent_name}_intermediate"})
                _log(f"[recognize] Intermediate result: {intermediate_text}")
            
            if data.get("data", {}).get("status") == 2:
                _log(f"[recognize] Status=2, closing WebSocket")
                ws.close()
        except Exception as e:
            _log(f"[recognize] Error processing message: {e}")
            import traceback
            _log(f"[recognize] Stack trace: {traceback.format_exc()}")
            ws_error[0] = f"parse message error: {e}"
            ws.close()

    def on_error(ws, error):
        _log(f"[recognize] WebSocket error: {error}")
        ws_error[0] = str(error)

    def on_close(ws, close_status, close_msg):
        _log(f"[recognize] WebSocket closed: status={close_status}, msg={close_msg}")
        ws_finished[0] = True

    def on_open(ws):
        _log(f"[recognize] WebSocket opened (accent: {accent_name})")
        import threading

        def send_audio():
            frame_size = 1280
            offset = 0
            total_sent = 0
            is_first = True
            while offset < len(audio_data):
                chunk = audio_data[offset : offset + frame_size]
                offset += frame_size
                
                if is_first:
                    status = 0
                    frame = {
                        "common": {"app_id": XUNFEI_APPID},
                        "business": {
                            "language": "zh_cn",
                            "domain": "iat",
                            "accent": accent_value,
                            "vad_eos": 5000,
                            "ptt": 0,
                            "dwa": "wpgs",
                        },
                        "data": {
                            "status": 0,
                            "format": "audio/L16;rate=16000",
                            "audio": base64.b64encode(chunk).decode("utf-8"),
                            "encoding": "raw",
                        },
                    }
                    is_first = False
                elif offset >= len(audio_data):
                    status = 2
                    frame = {
                        "data": {
                            "status": 2,
                            "format": "audio/L16;rate=16000",
                            "audio": base64.b64encode(chunk).decode("utf-8"),
                            "encoding": "raw",
                        }
                    }
                else:
                    status = 1
                    frame = {
                        "data": {
                            "status": 1,
                            "format": "audio/L16;rate=16000",
                            "audio": base64.b64encode(chunk).decode("utf-8"),
                            "encoding": "raw",
                        }
                    }
                
                ws.send(json.dumps(frame))
                total_sent += len(chunk)
                _log(f"[recognize] Sent chunk {total_sent}/{len(audio_data)}, status={status}")
                time.sleep(0.04)

        threading.Thread(target=send_audio, daemon=True).start()

    url = _xunfei_create_url()
    ws = websocket.WebSocketApp(
        url,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close,
        on_open=on_open,
    )
    ws.run_forever()

    if ws_error[0]:
        _log(f"[recognize] xunfei error (accent={accent_name}): {ws_error[0]}")
        return None, ws_error[0]

    text = "".join(result_parts).strip()
    _log(f"[recognize] Result (accent={accent_name}): '{text}'")
    # 去掉开头和结尾的标点符号
    text = re.sub(r"^[，。、；：!?！?\.。]+", "", text)
    text = re.sub(r"[。！？]+$", "", text)
    return text if text else None, None


def _xunfei_recognize(audio_path, offline_lib=None):
    """Try multiple accents in sequence.
    
    根据离线库中的统计数据，动态调整口音优先级。
    注意：讯飞API不会返回口音信息，我们通过source字段记录使用的口音。
    """
    _log("")
    _log("="*60)
    _log("[XUNFEI RECOGNIZE] Starting iFlytek recognition process...")
    
    # 根据离线库获取口音优先级
    priority_order = _get_accent_priority(offline_lib)
    _log(f"[XUNFEI RECOGNIZE] Will try accents in order: {priority_order}")
    
    # 构建完整口音列表
    accents = []
    for accent_name in priority_order:
        accent_value = accent_name
        if accent_name == "mandarin":
            accent_value = "mandarin"
        elif accent_name == "sichuan":
            accent_value = "sichuan"
        elif accent_name == "henan":
            accent_value = "henan"
        accents.append((accent_name, accent_value))
    
    # 尝试识别
    attempt_num = 0
    for accent_name, accent_value in accents:
        attempt_num += 1
        _log("")
        _log(f"[XUNFEI RECOGNIZE] Attempt #{attempt_num}: accent='{accent_name}'")
        _log(f"[XUNFEI RECOGNIZE] Sending audio to iFlytek with accent='{accent_value}'...")
        
        text, error = _xunfei_recognize_with_accent(audio_path, accent_name, accent_value)
        
        if text:
            _log(f"[XUNFEI RECOGNIZE] ✓ SUCCESS! Accent='{accent_name}' recognized: '{text}'")
            source = f"xunfei_{accent_name}"
            _write_result({"text": text, "source": source})
            _log("="*60)
            _log("")
            return text, source
        elif error:
            _log(f"[XUNFEI RECOGNIZE] ✗ Accent='{accent_name}' failed with error: {error}")
        else:
            _log(f"[XUNFEI RECOGNIZE] ✗ Accent='{accent_name}' returned empty result, trying next...")
    
    _log("")
    _log(f"[XUNFEI RECOGNIZE] All {len(accents)} attempts failed, falling back to Whisper offline")
    _log("="*60)
    _log("")
    return None, None


def _whisper_recognize(audio_path, offline_lib=None):
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        _log(f"[recognize] faster_whisper not available")
        return None, None

    # Initialize model
    model = None
    model_path = None
    selected_model = None
    retry_download = False

    try:
        os.makedirs(WHISPER_MODEL_DIR, exist_ok=True)

        # 优先使用更准确的模型顺序：medium > small > base
        model_priority = ["medium", "small", "base"]
        selected_model = None
        model_path = None

        # 检测已下载的模型
        if os.path.exists(WHISPER_MODEL_DIR):
            for model_size in model_priority:
                # 检查多种可能的目录格式
                possible_paths = [
                    os.path.join(WHISPER_MODEL_DIR, model_size),  # 直接目录
                    os.path.join(WHISPER_MODEL_DIR, f"Systran/faster-whisper-{model_size}"),  # ModelScope
                    os.path.join(WHISPER_MODEL_DIR, f"models--Systran--faster-whisper-{model_size}"),  # HuggingFace
                ]

                for path in possible_paths:
                    if os.path.isdir(path):
                        # 检查是否有 model.bin 文件
                        model_bin_found = False
                        if os.path.isfile(os.path.join(path, "model.bin")):
                            model_bin_found = True
                        else:
                            # 在子目录中查找
                            for root, dirs, files in os.walk(path):
                                if "model.bin" in files:
                                    model_bin_found = True
                                    break

                        if model_bin_found:
                            selected_model = model_size
                            model_path = path
                            _log(f"[recognize] Found model: faster-whisper-{model_size}")
                            break
                if selected_model:
                    break

        # 尝试加载模型
        if selected_model and model_path:
            _log(f"[recognize] ============================================================")
            _log(f"[recognize] STEP 1: Loading existing Whisper model")
            _log(f"[recognize] Model size: {selected_model}")
            _log(f"[recognize] Model path: {model_path}")
            _log(f"[recognize] ============================================================")

            # 先验证 model.bin 是否真的存在
            model_bin_path = os.path.join(model_path, "model.bin")
            if not os.path.isfile(model_bin_path):
                # 在子目录中查找
                for root, dirs, files in os.walk(model_path):
                    if "model.bin" in files:
                        model_bin_path = os.path.join(root, "model.bin")
                        break

            _log(f"[recognize] Checking model.bin at: {model_bin_path}")
            if os.path.isfile(model_bin_path):
                _log(f"[recognize] model.bin exists, size: {os.path.getsize(model_bin_path)} bytes")
            else:
                _log(f"[recognize] WARNING: model.bin NOT FOUND at {model_bin_path}")

            try:
                model = WhisperModel(model_path, device="cpu", compute_type="int8")
                _log(f"[recognize] Model loaded successfully!")
            except Exception as load_error:
                _log(f"[recognize] ============================================================")
                _log(f"[recognize] ERROR: Model load failed!")
                _log(f"[recognize] Error message: {load_error}")
                _log(f"[recognize] This usually means the model files are corrupted or incomplete.")
                _log(f"[recognize] ============================================================")
                _log(f"[recognize] STEP 2: Removing corrupted model directory")
                _log(f"[recognize] Target: {model_path}")
                import shutil
                try:
                    # 先列出目录内容
                    _log(f"[recognize] Directory contents before removal:")
                    for item in os.listdir(model_path):
                        item_path = os.path.join(model_path, item)
                        if os.path.isfile(item_path):
                            _log(f"[recognize]   - {item} ({os.path.getsize(item_path)} bytes)")
                        else:
                            _log(f"[recognize]   - {item}/ (directory)")

                    _log(f"[recognize] Executing shutil.rmtree...")
                    shutil.rmtree(model_path)

                    # 验证删除成功
                    if not os.path.exists(model_path):
                        _log(f"[recognize] SUCCESS: Corrupted model directory removed")
                    else:
                        _log(f"[recognize] WARNING: Directory still exists after removal attempt")

                    model_path = None
                    selected_model = None
                    retry_download = True
                    _log(f"[recognize] STEP 3: Will re-download model (medium size)")
                except Exception as rm_error:
                    _log(f"[recognize] ============================================================")
                    _log(f"[recognize] FATAL: Failed to remove corrupted model!")
                    _log(f"[recognize] Error: {rm_error}")
                    _log(f"[recognize] Please manually delete: {model_path}")
                    _log(f"[recognize] ============================================================")
                    return None, None

        # 如果没有模型或需要重新下载，下载模型
        if model is None:
            _log(f"[recognize] ============================================================")
            _log(f"[recognize] STEP 1: Preparing to download Whisper model")
            _log(f"[recognize] Target directory: {WHISPER_MODEL_DIR}")

            # 选择可用的模型大小
            if not selected_model:
                selected_model = "medium"  # 优先 medium
                _log(f"[recognize] Primary model size: {selected_model}")
                # 检查是否有更小的模型可用
                _log(f"[recognize] Checking for smaller available models...")
                for m in model_priority:
                    if m != selected_model:
                        possible_paths = [
                            os.path.join(WHISPER_MODEL_DIR, m),
                            os.path.join(WHISPER_MODEL_DIR, f"Systran/faster-whisper-{m}"),
                            os.path.join(WHISPER_MODEL_DIR, f"models--Systran--faster-whisper-{m}"),
                        ]
                        for p in possible_paths:
                            if os.path.isdir(p):
                                # 检查是否有 model.bin
                                has_bin = os.path.isfile(os.path.join(p, "model.bin"))
                                if not has_bin:
                                    has_bin = any("model.bin" in f for _, _, f in os.walk(p))
                                if has_bin:
                                    selected_model = m
                                    _log(f"[recognize] Found valid {m} model, using it instead")
                                    break
                        if selected_model == m:
                            break

            _log(f"[recognize] ============================================================")
            _log(f"[recognize] STEP 2: Starting model download")
            _log(f"[recognize] Model size: {selected_model}")
            _log(f"[recognize] Expected size: ~463MB (small) / ~1.5GB (medium)")
            _log(f"[recognize] Download may take several minutes...")
            _log(f"[recognize] ============================================================")

            try:
                model = WhisperModel(selected_model, device="cpu", compute_type="int8", download_root=WHISPER_MODEL_DIR)
                _log(f"[recognize] ============================================================")
                _log(f"[recognize] SUCCESS: Model downloaded and loaded!")
                _log(f"[recognize] Model size: {selected_model}")
                _log(f"[recognize] Download location: {WHISPER_MODEL_DIR}")
                _log(f"[recognize] ============================================================")
            except Exception as download_error:
                _log(f"[recognize] ============================================================")
                _log(f"[recognize] FATAL: Model download failed!")
                _log(f"[recognize] Error: {download_error}")
                _log(f"[recognize] Possible causes:")
                _log(f"[recognize]   - Network connection issue")
                _log(f"[recognize]   - HuggingFace/Download server is down")
                _log(f"[recognize]   - Disk space insufficient")
                _log(f"[recognize] Please check your network and try again.")
                _log(f"[recognize] ============================================================")
                return None, None

    except Exception as e:
        _log(f"[recognize] Whisper init failed: {e}")
        return None, None

    _log(f"[recognize] Starting offline recognition...")
    
    try:
        segments, info = model.transcribe(audio_path, language="zh", beam_size=5)
        text_parts = []
        for segment in segments:
            text_parts.append(segment.text.strip())
        text = " ".join(text_parts).strip()
        _log(f"[recognize] Whisper result: '{text}'")
        
        # Clean end punctuation (but keep middle commas)
        # 去掉开头和结尾的标点符号
        text = re.sub(r"^[，。、；：!?！?\.。]+", "", text)
        text = re.sub(r"[。！？.?!]+$", "", text)
        
        source = "whisper"
        _write_result({"text": text, "source": source})
        return text, source
    except Exception as e:
        _log(f"[recognize] Whisper transcribe failed: {e}")
        return None, None


def recognize(audio_path, mode="all"):
    """Recognize audio using specified mode.
    
    Args:
        audio_path: Path to audio file
        mode: Recognition mode - "online" (only online), "offline" (only offline), "all" (both, default)
    
    Returns:
        Final recognition text
    """
    _log("")
    _log("="*60)
    _log("="*60)
    _log(f"[MAIN RECOGNIZE] Starting recognition in mode: {mode}")
    _log(f"[MAIN RECOGNIZE] Audio file: {audio_path}")
    
    offline_lib = _load_offline_lib()
    if offline_lib:
        _log(f"[MAIN RECOGNIZE] Offline library loaded successfully")
    else:
        _log(f"[MAIN RECOGNIZE] No offline library found")
    
    results = []
    
    # Try iFlytek online if mode allows
    if mode in ["online", "all"]:
        _log("")
        _log("-"*60)
        _log("[MAIN RECOGNIZE] Trying iFlytek online recognition")
        _log("-"*60)
        
        text_online, source_online = _xunfei_recognize(audio_path, offline_lib)
        if text_online:
            final_text_online = _match_offline_lib_with_accent(text_online, offline_lib, source_online)
            results.append({
                "text": final_text_online,
                "source": source_online,
                "priority": 2  # online has higher priority
            })
            _log(f"[MAIN RECOGNIZE] ✓ Online result: '{final_text_online}' (source={source_online})")
            _write_result({"text": final_text_online, "source": source_online})
    
    # Try Whisper offline if mode allows
    if mode in ["offline", "all"]:
        _log("")
        _log("-"*60)
        _log("[MAIN RECOGNIZE] Trying Whisper offline recognition")
        _log("-"*60)
        
        text_offline, source_offline = _whisper_recognize(audio_path, offline_lib)
        if text_offline:
            final_text_offline = _match_offline_lib_with_accent(text_offline, offline_lib, source_offline)
            results.append({
                "text": final_text_offline,
                "source": source_offline,
                "priority": 1  # offline has lower priority
            })
            _log(f"[MAIN RECOGNIZE] ✓ Offline result: '{final_text_offline}' (source={source_offline})")
            _write_result({"text": final_text_offline, "source": source_offline})
    
    # Determine final result
    if results:
        # Sort by priority (higher first), then choose the best
        results.sort(key=lambda x: x["priority"], reverse=True)
        best_result = results[0]
        
        _log("")
        _log("="*60)
        _log(f"[MAIN RECOGNIZE] All results collected:")
        for i, result in enumerate(results):
            _log(f"[MAIN RECOGNIZE]   {i+1}. '{result['text']}' (source={result['source']}, priority={result['priority']})")
        _log("="*60)
        _log(f"[MAIN RECOGNIZE] ✓ FINAL RESULT: '{best_result['text']}' (source={best_result['source']})")
        _log("="*60)
        _log("="*60)
        _log("")

        final_text = _post_process_text(best_result["text"])
        _log(f"[MAIN RECOGNIZE] Post-processed: '{final_text}'")

        print(final_text)
        return final_text
    
    _log("")
    _log("="*60)
    _log(f"[MAIN RECOGNIZE] ✗ COMPLETE FAILURE: No recognition result")
    _log("="*60)
    _log("="*60)
    _log("")
    return None


if __name__ == "__main__":
    try:
        import argparse
        parser = argparse.ArgumentParser(description="Speech recognition with iFlytek online and Whisper offline.")
        parser.add_argument("audio_path", help="Path to audio file")
        parser.add_argument("--mode", "-m", default="all",
                           choices=["online", "offline", "all"],
                           help="Recognition mode: online (only online), offline (only offline), all (both, default)")
        args = parser.parse_args()

        text, error = recognize(args.audio_path, mode=args.mode)
        if error:
            sys.exit(1)
    finally:
        _close_logging()

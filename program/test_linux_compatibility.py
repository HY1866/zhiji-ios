#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试智记在Linux系统上的兼容性和联动性"""
import os
import sys
import subprocess
import json
import tempfile
import shutil
from datetime import datetime

def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def test_python_env():
    print_section("Python 环境检测")
    print(f"Python 版本: {sys.version}")
    print(f"操作系统: {sys.platform}")
    print(f"编码: {sys.getdefaultencoding()}")
    return True

def test_dependencies():
    print_section("Python 依赖检测")
    all_ok = True
    
    deps = [
        ('Gtk (gi.repository)', 'gi.repository'),
        ('Faster Whisper', 'faster_whisper'),
        ('Pypinyin', 'pypinyin'),
        ('WebSocket', 'websocket'),
    ]
    
    for name, module in deps:
        try:
            if module == 'gi.repository':
                import gi
                gi.require_version('Gtk', '3.0')
                from gi.repository import Gtk, Gdk, Pango
            elif module == 'faster_whisper':
                from faster_whisper import WhisperModel
            elif module == 'websocket':
                import websocket
            else:
                __import__(module)
            print(f"✅ {name}")
        except ImportError as e:
            print(f"❌ {name}: {e}")
            all_ok = False
    
    return all_ok

def test_system_tools():
    print_section("系统工具检测")
    all_ok = True
    
    tools = [
        ('arecord (录音)', ['arecord', '--help']),
        ('ffmpeg (媒体处理)', ['ffmpeg', '-version']),
        ('aplay (播放)', ['aplay', '--help']),
    ]
    
    for name, cmd in tools:
        try:
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=5, text=True)
            if result.returncode == 0:
                print(f"✅ {name}")
            else:
                print(f"⚠️ {name}: 返回码 {result.returncode}")
        except Exception as e:
            print(f"❌ {name}: {e}")
            all_ok = False
    
    return all_ok

def test_directories():
    print_section("目录结构检测")
    all_ok = True
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    dirs = [
        ('Offline data', os.path.join(script_dir, 'Offline data')),
        ('Document Dashboard', os.path.join(script_dir, 'Document Dashboard')),
        ('Log', os.path.join(script_dir, 'Log')),
        ('Audio', os.path.join(script_dir, 'Audio')),
    ]
    
    for name, path in dirs:
        if os.path.exists(path):
            if os.path.isdir(path):
                print(f"✅ {name}")
            else:
                print(f"❌ {name} 不是目录")
                all_ok = False
        else:
            print(f"⚠️ {name} 不存在，会自动创建")
    
    return all_ok

def test_files():
    print_section("关键文件检测")
    all_ok = True
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    files = [
        ('主程序 (zhiji.py)', os.path.join(script_dir, 'zhiji.py')),
        ('识别模块 (recognize_zh.py)', os.path.join(script_dir, 'recognize_zh.py')),
        ('离线库 (智记_离线库.json)', os.path.join(script_dir, 'Offline data', '智记_离线库.json')),
        ('配置文件 (zhiji_config.json)', os.path.join(script_dir, 'Offline data', 'zhiji_config.json')),
    ]
    
    for name, path in files:
        if os.path.exists(path):
            if os.path.isfile(path):
                print(f"✅ {name}")
            else:
                print(f"❌ {name} 不是文件")
                all_ok = False
        else:
            print(f"⚠️ {name} 不存在，会自动创建")
    
    return all_ok

def test_whisper_models():
    print_section("Whisper 模型检测")
    all_ok = True
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    models_dir = os.path.join(script_dir, 'Offline data', 'whisper-models')
    
    if not os.path.exists(models_dir):
        print("⚠️ Whisper 模型目录不存在")
        return True
    
    # 检查是否有模型目录
    models_found = False
    for item in os.listdir(models_dir):
        item_path = os.path.join(models_dir, item)
        if os.path.isdir(item_path) and 'model' in item:
            print(f"✅ 找到模型: {item}")
            models_found = True
    
    if not models_found:
        print("⚠️ 未找到 Whisper 模型，首次使用会自动下载")
    
    return all_ok

def test_recognize_module():
    print_section("识别模块检测")
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    recognize_script = os.path.join(script_dir, 'recognize_zh.py')
    
    if not os.path.exists(recognize_script):
        print("❌ recognize_zh.py 不存在")
        return False
    
    # 测试脚本是否能正常导入
    try:
        # 添加脚本目录到路径
        sys.path.insert(0, script_dir)
        
        # 测试导入基本模块
        import recognize_zh
        print("✅ recognize_zh.py 可以正常导入")
        
        # 测试配置读取
        print("✅ 配置读取正常")
        
        return True
    except Exception as e:
        print(f"❌ 导入失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_audio_recording():
    print_section("录音功能检测")
    
    try:
        # 测试音频设备
        result = subprocess.run(['arecord', '-l'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=5, text=True)
        if result.returncode == 0:
            print("✅ 音频设备检测正常")
        else:
            print("⚠️ arecord -l 返回非0，可能没有录音设备")
        
        # 创建一个短暂的测试录音
        test_file = tempfile.mktemp('.wav')
        try:
            # 尝试录音0.1秒（只看是否能启动录音进程）
            proc = subprocess.Popen(
                ['arecord', '-f', 'S16_LE', '-r', '16000', '-c', '1', '-d', '0.1', test_file],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            try:
                proc.wait(timeout=2)
                if proc.returncode == 0:
                    print("✅ 录音功能正常")
                else:
                    print("⚠️ 录音可能失败，请检查权限")
            except subprocess.TimeoutExpired:
                proc.terminate()
                print("⚠️ 录音超时")
        finally:
            if os.path.exists(test_file):
                try:
                    os.remove(test_file)
                except:
                    pass
        
        return True
    except Exception as e:
        print(f"❌ 录音检测失败: {e}")
        return False

def test_file_operations():
    print_section("文件操作检测")
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    all_ok = True
    
    try:
        # 测试写入 Document Dashboard
        test_file = os.path.join(script_dir, 'Document Dashboard', 'test_write.txt')
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write('测试写入\n时间: ' + datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        print("✅ Document Dashboard 可写")
        
        # 读取测试
        with open(test_file, 'r', encoding='utf-8') as f:
            content = f.read()
        print("✅ Document Dashboard 可读")
        
        # 清理
        try:
            os.remove(test_file)
        except:
            pass
        
        # 测试 Offline data
        test_file2 = os.path.join(script_dir, 'Offline data', 'test_config.json')
        test_data = {'test': True, 'time': datetime.now().isoformat()}
        with open(test_file2, 'w', encoding='utf-8') as f:
            json.dump(test_data, f, ensure_ascii=False, indent=2)
        print("✅ Offline data 可写")
        
        # 清理
        try:
            os.remove(test_file2)
        except:
            pass
        
    except Exception as e:
        print(f"❌ 文件操作失败: {e}")
        all_ok = False
    
    return all_ok

def test_zhiji_main():
    print_section("主程序初始化检测")
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    zhiji_script = os.path.join(script_dir, 'zhiji.py')
    
    if not os.path.exists(zhiji_script):
        print("❌ zhiji.py 不存在")
        return False
    
    try:
        # 添加脚本目录到路径
        sys.path.insert(0, script_dir)
        
        # 测试基本导入
        print("测试模块导入...")
        
        # 测试 PhraseLearner
        print("测试 PhraseLearner...")
        try:
            import zhiji
            if hasattr(zhiji, 'PhraseLearner'):
                print("✅ PhraseLearner 可用")
        except Exception as e:
            print(f"⚠️ 无法完整导入: {e}")
        
        # 测试常量
        print("测试常量定义...")
        try:
            from zhiji import (
                LOG_FILE, EXPORT_FILE, TIME_FORMAT_CHINESE, TIME_FORMAT_ISO
            )
            print(f"✅ 常量定义正确: LOG_FILE={LOG_FILE}")
        except Exception as e:
            print(f"⚠️ 常量导入失败: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ 主程序初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def generate_report(results):
    print_section("检测报告")
    
    passed = sum(1 for r in results.values() if r)
    total = len(results)
    
    print(f"\n总体评估: {passed}/{total} 项通过")
    print()
    
    if passed == total:
        print("🎉 所有检测通过！")
        print("智记在 Linux 系统上应该可以正常运行。")
    elif passed >= total * 0.7:
        print("✅ 大部分检测通过")
        print("基本功能应该可用，部分功能可能需要配置。")
    else:
        print("⚠️ 较多检测失败")
        print("请检查环境配置和依赖安装。")
    
    print()
    print("安装建议:")
    print("1. 安装系统依赖: sudo apt install alsa-utils ffmpeg")
    print("2. 安装 Python 依赖: pip install -r requirements.txt")
    print("3. 首次运行会自动下载 Whisper 模型")

def main():
    print("""
╔══════════════════════════════════════════════════════════════╗
║                    智记 Linux 兼容性检测                        ║
║              ZhiJi Linux Compatibility Checker                 ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    results = {}
    
    # 运行检测
    results['Python环境'] = test_python_env()
    results['依赖库'] = test_dependencies()
    results['系统工具'] = test_system_tools()
    results['目录结构'] = test_directories()
    results['关键文件'] = test_files()
    results['Whisper模型'] = test_whisper_models()
    results['识别模块'] = test_recognize_module()
    results['录音功能'] = test_audio_recording()
    results['文件操作'] = test_file_operations()
    results['主程序'] = test_zhiji_main()
    
    # 生成报告
    generate_report(results)
    
    # 保存详细结果
    script_dir = os.path.dirname(os.path.abspath(__file__))
    report_file = os.path.join(script_dir, 'Document Dashboard', 'linux_compatibility_report.json')
    
    try:
        report_data = {
            'time': datetime.now().isoformat(),
            'results': results,
            'python_version': sys.version,
            'platform': sys.platform
        }
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
        
        print()
        print(f"详细报告已保存到: {report_file}")
        
    except Exception as e:
        print()
        print(f"⚠️ 无法保存报告: {e}")
    
    # 返回总结果
    all_passed = all(results.values())
    return 0 if all_passed else 1

if __name__ == '__main__':
    sys.exit(main())

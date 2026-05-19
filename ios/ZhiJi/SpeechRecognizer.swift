//
//  SpeechRecognizer.swift
//  ZhiJi
//
//  语音识别管理 - 集成讯飞SDK
//

import Foundation
import AVFoundation

// 语音识别状态
enum RecognitionState {
    case idle
    case recording
    case processing
    case error(String)
}

// 识别模式
enum RecognitionMode {
    case online     // 在线识别
    case offline    // 离线识别
}

class SpeechRecognizer: NSObject, ObservableObject {
    static let shared = SpeechRecognizer()
    
    @Published var state: RecognitionState = .idle
    @Published var recognizedText: String = ""
    @Published var mode: RecognitionMode = .online
    
    private var audioRecorder: AVAudioRecorder?
    private var audioSession: AVAudioSession?
    private let recordingSettings: [String: Any] = [
        AVFormatIDKey: Int(kAudioFormatLinearPCM),
        AVSampleRateKey: 16000.0,
        AVNumberOfChannelsKey: 1,
        AVLinearPCMBitDepthKey: 16,
        AVLinearPCMIsBigEndianKey: false,
        AVLinearPCMIsFloatKey: false,
        AVLinearPCMIsNonInterleaved: false
    ]
    
    private var recordingURL: URL?
    private var silenceTimer: Timer?
    private var silenceThreshold: TimeInterval = 5.0
    private var maxRecordingDuration: TimeInterval = 15.0
    private var recordingStartTime: Date?
    
    private override init() {
        super.init()
        setupAudioSession()
    }
    
    // MARK: - Audio Session Setup
    
    private func setupAudioSession() {
        audioSession = AVAudioSession.sharedInstance()
        do {
            try audioSession?.setCategory(.record, mode: .measurement, options: .duckOthers)
            try audioSession?.setActive(true)
        } catch {
            print("音频会话设置失败: \(error)")
        }
    }
    
    // MARK: - Recording Control
    
    func startRecording() {
        guard state == .idle else { return }
        
        // 配置录音文件
        let tempDir = NSTemporaryDirectory()
        let fileName = "zhiji_voice_\(Date().timeIntervalSince1970).wav"
        recordingURL = URL(fileURLWithPath: tempDir).appendingPathComponent(fileName)
        
        guard let url = recordingURL else { return }
        
        do {
            audioRecorder = try AVAudioRecorder(url: url, settings: recordingSettings)
            audioRecorder?.delegate = self
            audioRecorder?.isMeteringEnabled = true
            
            if audioRecorder?.record() == true {
                state = .recording
                recordingStartTime = Date()
                startSilenceDetection()
                print("开始录音")
            }
        } catch {
            state = .error("录音启动失败: \(error.localizedDescription)")
            print("录音启动失败: \(error)")
        }
    }
    
    func stopRecording() {
        guard state == .recording else { return }
        
        audioRecorder?.stop()
        silenceTimer?.invalidate()
        silenceTimer = nil
    }
    
    // MARK: - Silence Detection
    
    private func startSilenceDetection() {
        silenceTimer = Timer.scheduledTimer(withTimeInterval: 0.1, repeats: true) { [weak self] _ in
            guard let self = self, let recorder = self.audioRecorder else { return }
            
            recorder.updateMeters()
            let averagePower = recorder.averagePower(forChannel: 0)
            
            // 检查是否超过最大时长
            if let startTime = self.recordingStartTime,
               Date().timeIntervalSince(startTime) > self.maxRecordingDuration {
                print("达到最大录音时长")
                self.stopRecording()
                return
            }
            
            // 静音检测 (低于-50dB视为静音)
            if averagePower < -50.0 {
                if self.silenceTimer?.userInfo == nil {
                    self.silenceTimer?.userInfo = Date()
                } else if let silenceStart = self.silenceTimer?.userInfo as? Date,
                          Date().timeIntervalSince(silenceStart) > self.silenceThreshold {
                    print("检测到静音，自动停止录音")
                    self.stopRecording()
                }
            } else {
                // 有声音，重置静音计时器
                self.silenceTimer?.userInfo = nil
            }
        }
    }
    
    // MARK: - Speech Recognition
    
    private func recognizeSpeech(from url: URL) {
        state = .processing
        
        // TODO: 集成讯飞SDK进行语音识别
        // 这里先使用一个模拟的识别过程
        simulateRecognition()
    }
    
    private func simulateRecognition() {
        // 模拟识别延迟
        DispatchQueue.main.asyncAfter(deadline: .now() + 1.0) { [weak self] in
            // 模拟识别结果
            let sampleTexts = [
                "今天天气不错",
                "记得去超市购物",
                "开会时间是下午两点",
                "完成项目文档"
            ]
            self?.recognizedText = sampleTexts.randomElement() ?? "识别完成"
            self?.state = .idle
            
            // 保存记录
            if let text = self?.recognizedText, !text.isEmpty {
                DataManager.shared.addRecord(content: text)
            }
        }
    }
    
    // MARK: - Cleanup
    
    private func cleanupRecordingFile() {
        if let url = recordingURL, FileManager.default.fileExists(atPath: url.path) {
            try? FileManager.default.removeItem(at: url)
        }
        recordingURL = nil
    }
}

// MARK: - AVAudioRecorderDelegate

extension SpeechRecognizer: AVAudioRecorderDelegate {
    func audioRecorderDidFinishRecording(_ recorder: AVAudioRecorder, successfully flag: Bool) {
        if flag, let url = recordingURL {
            print("录音完成: \(url)")
            recognizeSpeech(from: url)
        } else {
            state = .error("录音失败")
            cleanupRecordingFile()
        }
    }
    
    func audioRecorderEncodeErrorDidOccur(_ recorder: AVAudioRecorder, error: Error?) {
        state = .error("录音错误: \(error?.localizedDescription ?? "未知错误")")
        cleanupRecordingFile()
    }
}

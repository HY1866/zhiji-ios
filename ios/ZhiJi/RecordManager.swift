//
//  RecordManager.swift
//  ZhiJi
//
//  记录管理 - 处理快速记录
//

import Foundation
import Combine

class RecordManager: ObservableObject {
    static let shared = RecordManager()
    
    @Published var isProcessing = false
    @Published var lastRecordTime: Date?
    
    private init() {}
    
    // 快速记录时间戳
    func quickRecord() {
        let dateFormatter = DateFormatter()
        dateFormatter.dateFormat = DataManager.shared.timeFormat == .chinese ? "yyyy年MM月dd日HH:mm:ss" : "yyyy-MM-dd HH:mm:ss"
        let timestamp = dateFormatter.string(from: Date())
        
        DataManager.shared.addRecord(content: timestamp)
        lastRecordTime = Date()
        
        // 提供反馈
        let generator = UINotificationFeedbackGenerator()
        generator.notificationOccurred(.success)
    }
    
    // 语音记录
    func voiceRecord() {
        let speechRecognizer = SpeechRecognizer.shared
        
        if speechRecognizer.state == .recording {
            speechRecognizer.stopRecording()
        } else {
            speechRecognizer.startRecording()
        }
    }
}

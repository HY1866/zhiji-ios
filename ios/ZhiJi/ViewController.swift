//
//  ViewController.swift
//  ZhiJi
//
//  智记主界面
//

import UIKit
import SwiftUI

class ViewController: UIViewController {
    
    private let dataManager = DataManager.shared
    private let recordManager = RecordManager.shared
    private let speechRecognizer = SpeechRecognizer.shared
    
    private var hostingController: UIHostingController<MainView>?
    
    override func viewDidLoad() {
        super.viewDidLoad()
        setupUI()
    }
    
    private func setupUI() {
        view.backgroundColor = UIColor(red: 0.12, green: 0.12, blue: 0.18, alpha: 1.0)
        title = "智记"
        
        // 使用SwiftUI构建界面
        let mainView = MainView()
        hostingController = UIHostingController(rootView: mainView)
        
        if let hostingController = hostingController {
            addChild(hostingController)
            hostingController.view.translatesAutoresizingMaskIntoConstraints = false
            view.addSubview(hostingController.view)
            
            NSLayoutConstraint.activate([
                hostingController.view.topAnchor.constraint(equalTo: view.safeAreaLayoutGuide.topAnchor),
                hostingController.view.leadingAnchor.constraint(equalTo: view.leadingAnchor),
                hostingController.view.trailingAnchor.constraint(equalTo: view.trailingAnchor),
                hostingController.view.bottomAnchor.constraint(equalTo: view.bottomAnchor)
            ])
            
            hostingController.didMove(toParent: self)
        }
    }
}

// MARK: - SwiftUI Main View

struct MainView: View {
    @ObservedObject var dataManager = DataManager.shared
    @ObservedObject var speechRecognizer = SpeechRecognizer.shared
    @ObservedObject var recordManager = RecordManager.shared
    
    @State private var showingEditSheet = false
    @State private var recordToEdit: Record?
    @State private var showingExportSheet = false
    @State private var showingClearAlert = false
    @State private var editText = ""
    @State private var showingHelpSheet = false
    
    var body: some View {
        VStack(spacing: 0) {
            // 顶部区域 - 时钟和控制按钮
            HeaderView()
            
            Divider()
                .background(Color.gray.opacity(0.3))
            
            // 记录列表
            RecordsListView(
                showingEditSheet: $showingEditSheet,
                recordToEdit: $recordToEdit,
                editText: $editText
            )
        }
        .background(Color(red: 0.12, green: 0.12, blue: 0.18))
        .sheet(isPresented: $showingEditSheet) {
            if let record = recordToEdit {
                EditRecordSheet(record: record, editText: $editText)
            }
        }
        .sheet(isPresented: $showingHelpSheet) {
            HelpSheet()
        }
        .alert("清空所有记录？", isPresented: $showingClearAlert) {
            Button("取消", role: .cancel) { }
            Button("确定", role: .destructive) {
                dataManager.clearAllRecords()
            }
        }
        .sheet(isPresented: $showingExportSheet) {
            if let exportURL = dataManager.exportToCSV() {
                ShareSheet(items: [exportURL])
            }
        }
    }
}

// MARK: - Header View

struct HeaderView: View {
    @ObservedObject var dataManager = DataManager.shared
    @ObservedObject var speechRecognizer = SpeechRecognizer.shared
    @ObservedObject var recordManager = RecordManager.shared
    
    @State private var currentTime = Date()
    @State private var showingHelp = false
    
    private let timer = Timer.publish(every: 1, on: .main, in: .common).autoconnect()
    
    var body: some View {
        VStack(spacing: 12) {
            // 顶部按钮行
            HStack {
                // 帮助按钮
                Button(action: {
                    showingHelp = true
                }) {
                    Image(systemName: "questionmark.circle.fill")
                        .font(.title2)
                        .foregroundColor(.gray)
                }
                .sheet(isPresented: $showingHelp) {
                    HelpSheet()
                }
                
                Spacer()
                
                // 时间格式切换
                Button(action: {
                    dataManager.toggleTimeFormat()
                }) {
                    Text(dataManager.timeFormat == .chinese ? "中" : "ISO")
                        .font(.caption)
                        .padding(.horizontal, 8)
                        .padding(.vertical, 4)
                        .background(Color(red: 0.19, green: 0.20, blue: 0.27))
                        .cornerRadius(6)
                        .foregroundColor(.pink)
                }
            }
            .padding(.horizontal)
            
            // 时钟显示
            Text(formattedTime)
                .font(.system(size: 24, weight: .bold))
                .foregroundColor(Color(red: 0.54, green: 0.70, blue: 0.98))
                .onReceive(timer) { _ in
                    currentTime = Date()
                }
            
            // 记录数量
            Text("共 \(dataManager.records.count) 条记录")
                .font(.caption)
                .foregroundColor(.gray)
            
            // 状态显示
            if !statusText.isEmpty {
                Text(statusText)
                    .font(.caption)
                    .foregroundColor(.orange)
            }
            
            // 按钮行
            HStack(spacing: 12) {
                // 记录按钮
                Button(action: {
                    recordManager.quickRecord()
                }) {
                    HStack {
                        Image(systemName: "clock.badge.checkmark")
                        Text("记录")
                    }
                    .font(.system(size: 14, weight: .medium))
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 12)
                    .background(Color(red: 0.27, green: 0.28, blue: 0.34))
                    .foregroundColor(.white)
                    .cornerRadius(8)
                }
                
                // 模式切换（在线/离线）
                Button(action: {
                    speechRecognizer.mode = speechRecognizer.mode == .online ? .offline : .online
                }) {
                    HStack {
                        Image(systemName: speechRecognizer.mode == .online ? "wifi" : "wifi.slash")
                        Text(speechRecognizer.mode == .online ? "在线" : "离线")
                    }
                    .font(.system(size: 14, weight: .medium))
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 12)
                    .background(Color(red: 0.19, green: 0.20, blue: 0.27))
                    .foregroundColor(speechRecognizer.mode == .online ? Color(red: 0.54, green: 0.70, blue: 0.98) : Color(red: 0.65, green: 0.89, blue: 0.63))
                    .cornerRadius(8)
                }
                
                // 语音按钮
                Button(action: {
                    recordManager.voiceRecord()
                }) {
                    HStack {
                        Image(systemName: speechRecognizer.state == .recording ? "stop.circle.fill" : "mic")
                        Text(speechRecognizer.state == .recording ? "停止" : "语音")
                    }
                    .font(.system(size: 14, weight: .medium))
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 12)
                    .background(speechRecognizer.state == .recording ? Color(red: 0.95, green: 0.55, blue: 0.68) : Color(red: 0.19, green: 0.20, blue: 0.27))
                    .foregroundColor(speechRecognizer.state == .recording ? .black : Color(red: 0.95, green: 0.55, blue: 0.68))
                    .cornerRadius(8)
                }
            }
            .padding(.horizontal)
        }
        .padding(.vertical, 16)
    }
    
    private var formattedTime: String {
        let formatter = DateFormatter()
        if dataManager.timeFormat == .chinese {
            formatter.dateFormat = "HH:mm:ss"
        } else {
            formatter.dateFormat = "yyyy-MM-dd HH:mm:ss"
        }
        return formatter.string(from: currentTime)
    }
    
    private var statusText: String {
        switch speechRecognizer.state {
        case .recording:
            return "录音中..."
        case .processing:
            return "识别中..."
        case .error(let message):
            return message
        default:
            return ""
        }
    }
}

// MARK: - Records List View

struct RecordsListView: View {
    @ObservedObject var dataManager = DataManager.shared
    @Binding var showingEditSheet: Bool
    @Binding var recordToEdit: Record?
    @Binding var editText: String
    
    var body: some View {
        List {
            ForEach(dataManager.records) { record in
                RecordRow(record: record)
                    .contentShape(Rectangle())
                    .onTapGesture {
                        recordToEdit = record
                        editText = record.content
                        showingEditSheet = true
                    }
                    .listRowBackground(Color(red: 0.09, green: 0.09, blue: 0.14))
                    .listRowSeparator(.hidden)
            }
        }
        .listStyle(.plain)
        .overlay {
            if dataManager.records.isEmpty {
                VStack(spacing: 16) {
                    Image(systemName: "note.text")
                        .font(.system(size: 50))
                        .foregroundColor(.gray)
                    Text("暂无记录")
                        .foregroundColor(.gray)
                }
            }
        }
    }
}

// MARK: - Record Row

struct RecordRow: View {
    let record: Record
    @ObservedObject var dataManager = DataManager.shared
    
    var body: some View {
        HStack(alignment: .top, spacing: 12) {
            VStack(alignment: .leading, spacing: 4) {
                Text(record.formattedTimestamp(format: dataManager.timeFormat))
                    .font(.caption)
                    .foregroundColor(.gray)
                Text(record.content)
                    .font(.system(size: 15))
                    .foregroundColor(.white)
                    .lineLimit(nil)
            }
            Spacer()
            Image(systemName: "chevron.right")
                .foregroundColor(.gray)
                .font(.caption)
        }
        .padding(.vertical, 8)
    }
}

// MARK: - Edit Record Sheet

struct EditRecordSheet: View {
    let record: Record
    @Binding var editText: String
    @Environment(\.dismiss) var dismiss
    @ObservedObject var dataManager = DataManager.shared
    
    var body: some View {
        NavigationView {
            VStack(spacing: 0) {
                TextEditor(text: $editText)
                    .padding()
                    .background(Color(red: 0.09, green: 0.09, blue: 0.14))
                    .foregroundColor(.white)
                
                Divider()
                    .background(Color.gray.opacity(0.3))
                
                HStack(spacing: 16) {
                    Button("删除") {
                        dataManager.deleteRecord(record)
                        dismiss()
                    }
                    .foregroundColor(.red)
                    
                    Spacer()
                    
                    Button("取消") {
                        dismiss()
                    }
                    .foregroundColor(.gray)
                    
                    Button("保存") {
                        dataManager.updateRecord(record, newContent: editText)
                        dismiss()
                    }
                    .foregroundColor(.blue)
                    .fontWeight(.semibold)
                }
                .padding()
            }
            .navigationTitle("编辑记录")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button("关闭") {
                        dismiss()
                    }
                }
            }
        }
        .preferredColorScheme(.dark)
    }
}

// MARK: - Help Sheet

struct HelpSheet: View {
    @Environment(\.dismiss) var dismiss
    
    var body: some View {
        NavigationView {
            ScrollView {
                VStack(alignment: .leading, spacing: 24) {
                    helpSection(
                        title: "📅 基本操作",
                        content: """
                        1. 「记录」按钮：快速添加一条当前时间的文本记录
                        2. 「语音」按钮：开始录音，支持智能静音检测
                        3. 格式切换：切换中文/ISO时间显示格式
                        4. 点击记录可编辑
                        """
                    )
                    
                    helpSection(
                        title: "⏱️ 录音功能",
                        content: """
                        - 点击「语音」按钮开始录音，再次点击可停止
                        - 最长录制15秒，5秒静音自动停止
                        - 支持在线识别和离线识别
                        - 识别结果自动记录到文件
                        """
                    )
                    
                    helpSection(
                        title: "✏️ 编辑记录",
                        content: """
                        - 点击任意记录可编辑
                        - 修改后会自动保存
                        """
                    )
                }
                .padding()
            }
            .navigationTitle("使用说明")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("关闭") {
                        dismiss()
                    }
                }
            }
        }
        .preferredColorScheme(.dark)
    }
    
    private func helpSection(title: String, content: String) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            Text(title)
                .font(.headline)
                .foregroundColor(.white)
            Text(content)
                .font(.subheadline)
                .foregroundColor(.gray)
                .lineSpacing(6)
        }
    }
}

// MARK: - Share Sheet

struct ShareSheet: UIViewControllerRepresentable {
    let items: [Any]
    
    func makeUIViewController(context: Context) -> UIActivityViewController {
        UIActivityViewController(activityItems: items, applicationActivities: nil)
    }
    
    func updateUIViewController(_ uiViewController: UIActivityViewController, context: Context) {}
}

// MARK: - Preview

struct MainView_Previews: PreviewProvider {
    static var previews: some View {
        MainView()
            .preferredColorScheme(.dark)
    }
}

//
//  DataManager.swift
//  ZhiJi
//
//  数据管理 - 处理记录的保存和读取
//

import Foundation

struct Record: Codable, Identifiable {
    let id: UUID
    let timestamp: Date
    let content: String
    
    init(id: UUID = UUID(), timestamp: Date = Date(), content: String) {
        self.id = id
        self.timestamp = timestamp
        self.content = content
    }
    
    // 格式化时间戳显示
    func formattedTimestamp(format: TimeFormat = .chinese) -> String {
        let formatter = DateFormatter()
        switch format {
        case .chinese:
            formatter.dateFormat = "yyyy年MM月dd日HH:mm:ss"
        case .iso:
            formatter.dateFormat = "yyyy-MM-dd HH:mm:ss"
        }
        return formatter.string(from: timestamp)
    }
}

enum TimeFormat {
    case chinese
    case iso
}

class DataManager: ObservableObject {
    static let shared = DataManager()
    
    @Published var records: [Record] = []
    @Published var timeFormat: TimeFormat = .chinese
    
    private let fileManager = FileManager.default
    private let recordsFileName = "zhiji_records.json"
    private let configFileName = "zhiji_config.json"
    
    private init() {
        loadRecords()
        loadConfig()
    }
    
    // MARK: - Records Management
    
    func addRecord(content: String) {
        let record = Record(content: content)
        records.insert(record, at: 0)
        saveRecords()
    }
    
    func updateRecord(_ record: Record, newContent: String) {
        if let index = records.firstIndex(where: { $0.id == record.id }) {
            records[index] = Record(id: record.id, timestamp: record.timestamp, content: newContent)
            saveRecords()
        }
    }
    
    func deleteRecord(_ record: Record) {
        records.removeAll { $0.id == record.id }
        saveRecords()
    }
    
    func clearAllRecords() {
        records.removeAll()
        saveRecords()
    }
    
    private func saveRecords() {
        do {
            let data = try JSONEncoder().encode(records)
            let fileURL = getDocumentsDirectory().appendingPathComponent(recordsFileName)
            try data.write(to: fileURL, options: .atomic)
        } catch {
            print("保存记录失败: \(error)")
        }
    }
    
    private func loadRecords() {
        let fileURL = getDocumentsDirectory().appendingPathComponent(recordsFileName)
        if fileManager.fileExists(atPath: fileURL.path) {
            do {
                let data = try Data(contentsOf: fileURL)
                records = try JSONDecoder().decode([Record].self, from: data)
                records.sort { $0.timestamp > $1.timestamp }
            } catch {
                print("加载记录失败: \(error)")
                records = []
            }
        }
    }
    
    // MARK: - Config Management
    
    func saveConfig() {
        let config: [String: Any] = [
            "timeFormat": timeFormat == .chinese ? "chinese" : "iso"
        ]
        do {
            let data = try JSONSerialization.data(withJSONObject: config)
            let fileURL = getDocumentsDirectory().appendingPathComponent(configFileName)
            try data.write(to: fileURL, options: .atomic)
        } catch {
            print("保存配置失败: \(error)")
        }
    }
    
    private func loadConfig() {
        let fileURL = getDocumentsDirectory().appendingPathComponent(configFileName)
        if fileManager.fileExists(atPath: fileURL.path) {
            do {
                let data = try Data(contentsOf: fileURL)
                if let config = try JSONSerialization.jsonObject(with: data) as? [String: Any],
                   let format = config["timeFormat"] as? String {
                    timeFormat = format == "chinese" ? .chinese : .iso
                }
            } catch {
                print("加载配置失败: \(error)")
            }
        }
    }
    
    func toggleTimeFormat() {
        timeFormat = timeFormat == .chinese ? .iso : .chinese
        saveConfig()
    }
    
    // MARK: - Export
    
    func exportToCSV() -> URL? {
        var csvString = "序号,时间,备注\n"
        for (index, record) in records.enumerated().reversed() {
            let line = "\(records.count - index),\(record.formattedTimestamp(format: .iso)),\"\(record.content)\"\n"
            csvString.append(line)
        }
        
        let fileURL = getDocumentsDirectory().appendingPathComponent("zhiji_export.csv")
        do {
            try csvString.write(to: fileURL, atomically: true, encoding: .utf8)
            return fileURL
        } catch {
            print("导出CSV失败: \(error)")
            return nil
        }
    }
    
    // MARK: - Helper
    
    private func getDocumentsDirectory() -> URL {
        fileManager.urls(for: .documentDirectory, in: .userDomainMask)[0]
    }
}

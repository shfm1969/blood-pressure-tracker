"""主視窗"""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from models.database import get_session, BloodPressureRecord, Position, init_db
from utils.bp_classifier import classify_blood_pressure
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib import font_manager
import pandas as pd
import platform

# 設定 matplotlib 中文字體
def setup_chinese_font():
    """設定 matplotlib 中文字體"""
    system = platform.system()
    
    # 嘗試的中文字體列表（按優先順序）
    font_candidates = []
    if system == 'Windows':
        font_candidates = ['Microsoft JhengHei', 'Microsoft YaHei', 'SimHei', 'KaiTi', 'FangSong']
    elif system == 'Darwin':  # macOS
        font_candidates = ['Arial Unicode MS', 'PingFang SC', 'STHeiti']
    else:  # Linux
        font_candidates = ['WenQuanYi Micro Hei', 'Noto Sans CJK SC', 'Droid Sans Fallback']
    
    # 取得系統中所有可用字體
    available_fonts = [f.name for f in font_manager.fontManager.ttflist]
    
    # 找到第一個可用的中文字體
    font_name = None
    for candidate in font_candidates:
        if candidate in available_fonts:
            font_name = candidate
            break
    
    # 如果找不到，使用預設字體列表
    if font_name is None:
        font_name = font_candidates[0] if font_candidates else 'DejaVu Sans'
    
    # 設定 matplotlib 預設字體
    plt.rcParams['font.sans-serif'] = [font_name] + font_candidates + ['DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False  # 解決負號顯示問題
    
    # 清除 matplotlib 字體快取（可選，確保使用新字體）
    try:
        font_manager._rebuild()
    except:
        pass
    
    return font_name

# 初始化中文字體
CHINESE_FONT = setup_chinese_font()


class MainWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("HeartTrack - 血壓脈搏記錄 App")
        self.root.geometry("1000x700")
        self.root.configure(bg='#f5f5f5')
        
        # 初始化資料庫
        init_db()
        
        # 建立主介面
        self.create_widgets()
        self.refresh_display()
    
    def create_widgets(self):
        """建立主介面元件"""
        # 標題
        title_frame = tk.Frame(self.root, bg='#2c3e50', height=80)
        title_frame.pack(fill=tk.X)
        title_frame.pack_propagate(False)
        
        title_label = tk.Label(
            title_frame,
            text="HeartTrack 血壓脈搏記錄",
            font=('Microsoft JhengHei', 24, 'bold'),
            fg='white',
            bg='#2c3e50'
        )
        title_label.pack(pady=20)
        
        # 主內容區域
        main_frame = tk.Frame(self.root, bg='#f5f5f5')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # 左側：最近記錄與統計
        left_frame = tk.Frame(main_frame, bg='white', relief=tk.RAISED, bd=2)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # 最近一次記錄
        recent_frame = tk.LabelFrame(
            left_frame,
            text="最近一次記錄",
            font=('Microsoft JhengHei', 12, 'bold'),
            bg='white',
            padx=20,
            pady=15
        )
        recent_frame.pack(fill=tk.X, padx=15, pady=15)
        
        self.recent_label = tk.Label(
            recent_frame,
            text="尚無記錄",
            font=('Microsoft JhengHei', 14),
            bg='white',
            justify=tk.LEFT
        )
        self.recent_label.pack(anchor=tk.W)
        
        # 新增記錄按鈕
        add_btn = tk.Button(
            left_frame,
            text="➕ 新增記錄",
            font=('Microsoft JhengHei', 16, 'bold'),
            bg='#3498db',
            fg='white',
            relief=tk.FLAT,
            padx=30,
            pady=15,
            cursor='hand2',
            command=self.open_add_record_dialog
        )
        add_btn.pack(pady=20)
        
        # 功能按鈕區域
        button_frame = tk.Frame(left_frame, bg='white')
        button_frame.pack(fill=tk.X, padx=15, pady=10)
        
        btn_style = {
            'font': ('Microsoft JhengHei', 11),
            'relief': tk.FLAT,
            'padx': 15,
            'pady': 8,
            'cursor': 'hand2'
        }
        
        history_btn = tk.Button(
            button_frame,
            text="📋 歷史記錄",
            bg='#95a5a6',
            fg='white',
            command=self.open_history_window,
            **btn_style
        )
        history_btn.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        chart_btn = tk.Button(
            button_frame,
            text="📊 統計圖表",
            bg='#9b59b6',
            fg='white',
            command=self.open_chart_window,
            **btn_style
        )
        chart_btn.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        export_btn = tk.Button(
            button_frame,
            text="💾 導出資料",
            bg='#e67e22',
            fg='white',
            command=self.export_data,
            **btn_style
        )
        export_btn.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # 右側：趨勢圖表
        chart_frame = tk.LabelFrame(
            main_frame,
            text="本週趨勢",
            font=('Microsoft JhengHei', 12, 'bold'),
            bg='white',
            padx=10,
            pady=10
        )
        chart_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        self.fig = Figure(figsize=(6, 4), dpi=100)
        self.ax = self.fig.add_subplot(111)
        # 設定圖表預設字體
        self.ax.tick_params(labelsize=9)
        self.canvas = FigureCanvasTkAgg(self.fig, chart_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def refresh_display(self):
        """刷新顯示內容"""
        session = get_session()
        try:
            # 取得最近一筆記錄
            recent = session.query(BloodPressureRecord).order_by(
                BloodPressureRecord.measured_at.desc()
            ).first()
            
            if recent:
                category, color = classify_blood_pressure(recent.systolic, recent.diastolic)
                recent_text = f"""
測量時間：{recent.measured_at.strftime('%Y-%m-%d %H:%M:%S')}
收縮壓：{recent.systolic} mmHg
舒張壓：{recent.diastolic} mmHg
脈搏：{recent.pulse} bpm
測量側：{recent.position.value if recent.position else '未指定'}
分類：{category}
"""
                self.recent_label.config(text=recent_text)
            else:
                self.recent_label.config(text="尚無記錄")
            
            # 更新趨勢圖
            self.update_chart()
        finally:
            session.close()
    
    def update_chart(self):
        """更新趨勢圖表"""
        session = get_session()
        try:
            # 取得最近7天的記錄
            from datetime import timedelta
            week_ago = datetime.now() - timedelta(days=7)
            records = session.query(BloodPressureRecord).filter(
                BloodPressureRecord.measured_at >= week_ago
            ).order_by(BloodPressureRecord.measured_at).all()
            
            self.ax.clear()
            
            if records:
                dates = [r.measured_at for r in records]
                systolic = [r.systolic for r in records]
                diastolic = [r.diastolic for r in records]
                pulse = [r.pulse for r in records]
                
                self.ax.plot(dates, systolic, 'r-o', label='收縮壓', linewidth=2, markersize=6)
                self.ax.plot(dates, diastolic, 'b-s', label='舒張壓', linewidth=2, markersize=6)
                self.ax.plot(dates, pulse, 'g-^', label='脈搏', linewidth=2, markersize=6)
                
                self.ax.set_xlabel('日期', fontsize=10, fontfamily=CHINESE_FONT)
                self.ax.set_ylabel('數值', fontsize=10, fontfamily=CHINESE_FONT)
                self.ax.set_title('本週血壓與脈搏趨勢', fontsize=12, fontweight='bold', fontfamily=CHINESE_FONT)
                legend = self.ax.legend(loc='best', prop={'family': CHINESE_FONT})
                self.ax.grid(True, alpha=0.3)
                self.fig.autofmt_xdate()
            else:
                self.ax.text(0.5, 0.5, '尚無資料', 
                           ha='center', va='center', 
                           transform=self.ax.transAxes,
                           fontsize=14, fontfamily=CHINESE_FONT)
                self.ax.set_title('本週血壓與脈搏趨勢', fontsize=12, fontweight='bold', fontfamily=CHINESE_FONT)
            
            self.canvas.draw()
        finally:
            session.close()
    
    def open_add_record_dialog(self):
        """開啟新增記錄對話框"""
        dialog = AddRecordDialog(self.root, self)
    
    def open_history_window(self):
        """開啟歷史記錄視窗"""
        history_window = HistoryWindow(self.root, self)
    
    def open_chart_window(self):
        """開啟統計圖表視窗"""
        chart_window = ChartWindow(self.root, self)
    
    def export_data(self):
        """導出資料"""
        from tkinter import filedialog
        from utils.export import export_to_csv, export_to_pdf
        
        session = get_session()
        try:
            records = session.query(BloodPressureRecord).order_by(
                BloodPressureRecord.measured_at.desc()
            ).all()
            
            if not records:
                messagebox.showinfo("提示", "尚無記錄可導出")
                return
            
            # 選擇導出格式
            format_choice = messagebox.askyesno(
                "選擇格式",
                "選擇「是」導出為 PDF，選擇「否」導出為 CSV"
            )
            
            if format_choice:
                filename = filedialog.asksaveasfilename(
                    defaultextension=".pdf",
                    filetypes=[("PDF files", "*.pdf")]
                )
                if filename:
                    export_to_pdf(records, filename)
                    messagebox.showinfo("成功", f"已導出至：{filename}")
            else:
                filename = filedialog.asksaveasfilename(
                    defaultextension=".csv",
                    filetypes=[("CSV files", "*.csv")]
                )
                if filename:
                    export_to_csv(records, filename)
                    messagebox.showinfo("成功", f"已導出至：{filename}")
        finally:
            session.close()


class AddRecordDialog:
    """新增記錄對話框"""
    def __init__(self, parent, main_window):
        self.main_window = main_window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("新增血壓記錄")
        self.dialog.geometry("520x680")
        self.dialog.configure(bg='white')
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # 居中顯示
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (520 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (680 // 2)
        self.dialog.geometry(f"520x680+{x}+{y}")
        
        # 設定視窗最小大小
        self.dialog.minsize(520, 680)
        
        self.create_widgets()
    
    def create_widgets(self):
        """建立表單元件"""
        # 標題
        title = tk.Label(
            self.dialog,
            text="新增血壓記錄",
            font=('Microsoft JhengHei', 18, 'bold'),
            bg='white',
            fg='#2c3e50'
        )
        title.pack(pady=15)
        
        # 主內容框架
        content_frame = tk.Frame(self.dialog, bg='white')
        content_frame.pack(fill=tk.BOTH, expand=True, padx=40, pady=10)
        
        form_frame = tk.Frame(content_frame, bg='white')
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        # 收縮壓
        tk.Label(form_frame, text="收縮壓 (mmHg):", 
                font=('Microsoft JhengHei', 11), bg='white').pack(anchor=tk.W, pady=5)
        self.systolic_entry = tk.Entry(form_frame, font=('Microsoft JhengHei', 12), width=20)
        self.systolic_entry.pack(pady=5)
        
        # 舒張壓
        tk.Label(form_frame, text="舒張壓 (mmHg):", 
                font=('Microsoft JhengHei', 11), bg='white').pack(anchor=tk.W, pady=5)
        self.diastolic_entry = tk.Entry(form_frame, font=('Microsoft JhengHei', 12), width=20)
        self.diastolic_entry.pack(pady=5)
        
        # 脈搏
        tk.Label(form_frame, text="脈搏 (bpm):", 
                font=('Microsoft JhengHei', 11), bg='white').pack(anchor=tk.W, pady=5)
        self.pulse_entry = ttk.Spinbox(form_frame, from_=0, to=300, 
                                       font=('Microsoft JhengHei', 12), width=18)
        self.pulse_entry.set(70) # 設定預設值，例如70 bpm
        self.pulse_entry.pack(pady=5)

        # 測量側
        tk.Label(form_frame, text="測量側:", 
                font=('Microsoft JhengHei', 11), bg='white').pack(anchor=tk.W, pady=5)
        # --- 修改開始：取得最近一次的測量位置 ---
        default_position = ""
        session = get_session()
        try:
            last_record = session.query(BloodPressureRecord).order_by(
                BloodPressureRecord.measured_at.desc()
            ).first()
            if last_record and last_record.position:
                default_position = last_record.position.value
        finally:
            session.close()
       
        self.position_var = tk.StringVar(value=default_position)
        # --- 修改結束 ---

        position_frame = tk.Frame(form_frame, bg='white')
        position_frame.pack(pady=5)
        tk.Radiobutton(position_frame, text="左手", variable=self.position_var, 
                      value="左手", font=('Microsoft JhengHei', 11), bg='white').pack(side=tk.LEFT, padx=10)
        tk.Radiobutton(position_frame, text="右手", variable=self.position_var, 
                      value="右手", font=('Microsoft JhengHei', 11), bg='white').pack(side=tk.LEFT, padx=10)
        
        # 測量時間
        tk.Label(form_frame, text="測量時間:", 
                font=('Microsoft JhengHei', 11), bg='white').pack(anchor=tk.W, pady=5)
        time_frame = tk.Frame(form_frame, bg='white')
        time_frame.pack(pady=5)
        self.use_current_time = tk.BooleanVar(value=True)
        tk.Checkbutton(time_frame, text="使用當前時間", variable=self.use_current_time,
                      font=('Microsoft JhengHei', 10), bg='white',
                      command=self.toggle_time_entry).pack(anchor=tk.W)
        
        self.datetime_frame = tk.Frame(form_frame, bg='white')
        self.datetime_frame.pack(pady=5)
        self.date_entry = tk.Entry(self.datetime_frame, font=('Microsoft JhengHei', 10), width=12, state=tk.DISABLED)
        self.date_entry.pack(side=tk.LEFT, padx=2)
        tk.Label(self.datetime_frame, text=" ", bg='white').pack(side=tk.LEFT)
        self.time_entry = tk.Entry(self.datetime_frame, font=('Microsoft JhengHei', 10), width=10, state=tk.DISABLED)
        self.time_entry.pack(side=tk.LEFT, padx=2)
        
        # 備註
        tk.Label(form_frame, text="備註:", 
                font=('Microsoft JhengHei', 11), bg='white').pack(anchor=tk.W, pady=5)
        self.note_text = tk.Text(form_frame, font=('Microsoft JhengHei', 10), height=4, width=30)
        self.note_text.pack(pady=5, fill=tk.X)
        
        # 分隔線
        separator = tk.Frame(self.dialog, height=2, bg='#ecf0f1')
        separator.pack(fill=tk.X, padx=20, pady=10)
        
        # 按鈕區域 - 固定在底部，使用明顯的背景色
        button_frame = tk.Frame(self.dialog, bg='#f8f9fa', height=90)
        button_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=0, pady=0)
        button_frame.pack_propagate(False)
        
        # 按鈕容器 - 居中顯示
        btn_container = tk.Frame(button_frame, bg='#f8f9fa')
        btn_container.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        
        save_btn = tk.Button(
            btn_container,
            text="💾 儲存",
            font=('Microsoft JhengHei', 13, 'bold'),
            bg='#27ae60',
            fg='white',
            relief=tk.RAISED,
            bd=2,
            padx=35,
            pady=10,
            cursor='hand2',
            command=self.save_record,
            activebackground='#229954',
            activeforeground='white'
        )
        save_btn.pack(side=tk.LEFT, padx=10)
        
        cancel_btn = tk.Button(
            btn_container,
            text="❌ 取消",
            font=('Microsoft JhengHei', 13),
            bg='#95a5a6',
            fg='white',
            relief=tk.RAISED,
            bd=2,
            padx=35,
            pady=10,
            cursor='hand2',
            command=self.dialog.destroy,
            activebackground='#7f8c8d',
            activeforeground='white'
        )
        cancel_btn.pack(side=tk.LEFT, padx=10)
    
    def toggle_time_entry(self):
        """切換時間輸入框狀態"""
        if self.use_current_time.get():
            self.date_entry.config(state=tk.DISABLED)
            self.time_entry.config(state=tk.DISABLED)
        else:
            self.date_entry.config(state=tk.NORMAL)
            self.time_entry.config(state=tk.NORMAL)
            # 預設填入當前時間
            now = datetime.now()
            self.date_entry.delete(0, tk.END)
            self.date_entry.insert(0, now.strftime('%Y-%m-%d'))
            self.time_entry.delete(0, tk.END)
            self.time_entry.insert(0, now.strftime('%H:%M:%S'))
    
    def save_record(self):
        """儲存記錄"""
        try:
            systolic = int(self.systolic_entry.get())
            diastolic = int(self.diastolic_entry.get())
            pulse = int(self.pulse_entry.get())
            
            # 取得測量時間
            if self.use_current_time.get():
                measured_at = datetime.now()
            else:
                date_str = self.date_entry.get()
                time_str = self.time_entry.get()
                measured_at = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M:%S")
            
            # 取得測量側
            position = Position.LEFT if self.position_var.get() == "左手" else Position.RIGHT
            
            # 取得備註
            note = self.note_text.get("1.0", tk.END).strip()
            
            # 分類
            category, _ = classify_blood_pressure(systolic, diastolic)
            
            # 儲存到資料庫
            session = get_session()
            try:
                record = BloodPressureRecord(
                    systolic=systolic,
                    diastolic=diastolic,
                    pulse=pulse,
                    measured_at=measured_at,
                    position=position,
                    note=note,
                    category=category
                )
                session.add(record)
                session.commit()
                messagebox.showinfo("成功", "記錄已儲存！")
                self.dialog.destroy()
                self.main_window.refresh_display()
            except Exception as e:
                session.rollback()
                messagebox.showerror("錯誤", f"儲存失敗：{str(e)}")
            finally:
                session.close()
        except ValueError:
            messagebox.showerror("錯誤", "請輸入有效的數值！")
        except Exception as e:
            messagebox.showerror("錯誤", f"發生錯誤：{str(e)}")


class HistoryWindow:
    """歷史記錄視窗"""
    def __init__(self, parent, main_window):
        self.main_window = main_window
        self.window = tk.Toplevel(parent)
        self.window.title("歷史記錄")
        self.window.geometry("900x600")
        self.window.configure(bg='white')
        
        self.create_widgets()
        self.load_records()
    
    def create_widgets(self):
        """建立歷史記錄介面"""
        # 標題
        title = tk.Label(
            self.window,
            text="歷史記錄",
            font=('Microsoft JhengHei', 18, 'bold'),
            bg='white',
            fg='#2c3e50'
        )
        title.pack(pady=15)
        
        # 表格框架
        table_frame = tk.Frame(self.window, bg='white')
        table_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # 建立 Treeview
        columns = ('日期時間', '收縮壓', '舒張壓', '脈搏', '測量側', '分類', '備註')
        self.tree = ttk.Treeview(table_frame, columns=columns, show='headings', height=20)
        
        # 設定欄位寬度
        self.tree.column('日期時間', width=150)
        self.tree.column('收縮壓', width=80)
        self.tree.column('舒張壓', width=80)
        self.tree.column('脈搏', width=80)
        self.tree.column('測量側', width=80)
        self.tree.column('分類', width=150)
        self.tree.column('備註', width=200)
        
        # 設定欄位標題
        for col in columns:
            self.tree.heading(col, text=col)
        
        # 滾動條
        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 按鈕區域
        button_frame = tk.Frame(self.window, bg='white')
        button_frame.pack(pady=10)
        
        edit_btn = tk.Button(
            button_frame,
            text="編輯",
            font=('Microsoft JhengHei', 11),
            bg='#3498db',
            fg='white',
            relief=tk.FLAT,
            padx=20,
            pady=8,
            cursor='hand2',
            command=self.edit_record
        )
        edit_btn.pack(side=tk.LEFT, padx=5)
        
        delete_btn = tk.Button(
            button_frame,
            text="刪除",
            font=('Microsoft JhengHei', 11),
            bg='#e74c3c',
            fg='white',
            relief=tk.FLAT,
            padx=20,
            pady=8,
            cursor='hand2',
            command=self.delete_record
        )
        delete_btn.pack(side=tk.LEFT, padx=5)
        
        refresh_btn = tk.Button(
            button_frame,
            text="刷新",
            font=('Microsoft JhengHei', 11),
            bg='#95a5a6',
            fg='white',
            relief=tk.FLAT,
            padx=20,
            pady=8,
            cursor='hand2',
            command=self.load_records
        )
        refresh_btn.pack(side=tk.LEFT, padx=5)
    
    def load_records(self):
        """載入記錄"""
        # 清空現有資料
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        session = get_session()
        try:
            records = session.query(BloodPressureRecord).order_by(
                BloodPressureRecord.measured_at.desc()
            ).all()
            
            for record in records:
                self.tree.insert('', tk.END, values=(
                    record.measured_at.strftime('%Y-%m-%d %H:%M:%S'),
                    record.systolic,
                    record.diastolic,
                    record.pulse,
                    record.position.value if record.position else '',
                    record.category or '',
                    record.note or ''
                ), tags=(str(record.id),))
        finally:
            session.close()
    
    def edit_record(self):
        """編輯記錄"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("提示", "請選擇要編輯的記錄")
            return
        
        item = self.tree.item(selected[0])
        record_id = int(item['tags'][0])
        
        # 開啟編輯對話框（可以重用 AddRecordDialog 或建立新的）
        messagebox.showinfo("提示", "編輯功能開發中...")
    
    def delete_record(self):
        """刪除記錄"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("提示", "請選擇要刪除的記錄")
            return
        
        if not messagebox.askyesno("確認", "確定要刪除這筆記錄嗎？"):
            return
        
        item = self.tree.item(selected[0])
        record_id = int(item['tags'][0])
        
        session = get_session()
        try:
            record = session.query(BloodPressureRecord).filter_by(id=record_id).first()
            if record:
                session.delete(record)
                session.commit()
                messagebox.showinfo("成功", "記錄已刪除")
                self.load_records()
                self.main_window.refresh_display()
        except Exception as e:
            session.rollback()
            messagebox.showerror("錯誤", f"刪除失敗：{str(e)}")
        finally:
            session.close()


class ChartWindow:
    """統計圖表視窗"""
    def __init__(self, parent, main_window):
        self.main_window = main_window
        self.window = tk.Toplevel(parent)
        self.window.title("統計圖表")
        self.window.geometry("1000x700")
        self.window.configure(bg='white')
        
        self.create_widgets()
        self.update_charts()
    
    def create_widgets(self):
        """建立圖表介面"""
        # 標題
        title = tk.Label(
            self.window,
            text="統計圖表",
            font=('Microsoft JhengHei', 18, 'bold'),
            bg='white',
            fg='#2c3e50'
        )
        title.pack(pady=15)
        
        # 時間範圍選擇
        range_frame = tk.Frame(self.window, bg='white')
        range_frame.pack(pady=10)
        
        tk.Label(range_frame, text="時間範圍:", 
                font=('Microsoft JhengHei', 11), bg='white').pack(side=tk.LEFT, padx=5)
        
        self.range_var = tk.StringVar(value="週")
        for period in ["週", "月", "年"]:
            tk.Radiobutton(range_frame, text=period, variable=self.range_var,
                          value=period, font=('Microsoft JhengHei', 11), bg='white',
                          command=self.update_charts).pack(side=tk.LEFT, padx=10)
        
        # 圖表框架
        chart_frame = tk.Frame(self.window, bg='white')
        chart_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        self.fig = Figure(figsize=(10, 6), dpi=100)
        self.ax = self.fig.add_subplot(111)
        # 設定圖表預設字體
        self.ax.tick_params(labelsize=10)
        self.canvas = FigureCanvasTkAgg(self.fig, chart_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def update_charts(self):
        """更新圖表"""
        from datetime import timedelta
        
        session = get_session()
        try:
            period = self.range_var.get()
            if period == "週":
                days = 7
            elif period == "月":
                days = 30
            else:  # 年
                days = 365
            
            start_date = datetime.now() - timedelta(days=days)
            records = session.query(BloodPressureRecord).filter(
                BloodPressureRecord.measured_at >= start_date
            ).order_by(BloodPressureRecord.measured_at).all()
            
            self.ax.clear()
            
            if records:
                dates = [r.measured_at for r in records]
                systolic = [r.systolic for r in records]
                diastolic = [r.diastolic for r in records]
                pulse = [r.pulse for r in records]
                
                self.ax.plot(dates, systolic, 'r-o', label='收縮壓', linewidth=2, markersize=4)
                self.ax.plot(dates, diastolic, 'b-s', label='舒張壓', linewidth=2, markersize=4)
                self.ax.plot(dates, pulse, 'g-^', label='脈搏', linewidth=2, markersize=4)
                
                self.ax.set_xlabel('日期', fontsize=12, fontfamily=CHINESE_FONT)
                self.ax.set_ylabel('數值', fontsize=12, fontfamily=CHINESE_FONT)
                self.ax.set_title(f'過去{period}血壓與脈搏趨勢', fontsize=14, fontweight='bold', fontfamily=CHINESE_FONT)
                legend = self.ax.legend(loc='best', prop={'family': CHINESE_FONT})
                self.ax.grid(True, alpha=0.3)
                self.fig.autofmt_xdate()
            else:
                self.ax.text(0.5, 0.5, '尚無資料', 
                           ha='center', va='center', 
                           transform=self.ax.transAxes,
                           fontsize=16, fontfamily=CHINESE_FONT)
                self.ax.set_title(f'過去{period}血壓與脈搏趨勢', fontsize=14, fontweight='bold', fontfamily=CHINESE_FONT)
            
            self.canvas.draw()
        finally:
            session.close()


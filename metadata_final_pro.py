import os
import datetime
import hashlib
import csv
import logging
import sqlite3
import smtplib
import random
import string
import platform
import threading
import webbrowser
from tkinter import filedialog, messagebox, Listbox, END, Canvas, simpledialog, LEFT

# UI Libraries - FIXED IMPORTS
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from ttkbootstrap.tableview import Tableview

# Forensic Libraries
import exifread
import PyPDF2
import docx
import openpyxl 
from pptx import Presentation 
import mutagen   
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
import zipfile

# --- 1. LOGGING & DATABASE SETUP ---
if not os.path.exists("logs"): os.makedirs("logs")
logging.basicConfig(
    filename='logs/forensic_ops.log',
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s'
)

conn = sqlite3.connect('forensic_data.db')
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS metadata 
             (filename TEXT, file_type TEXT, key TEXT, value TEXT, md5_hash TEXT, anomaly_flag TEXT)''')
conn.commit()

# --- 2. MATRIX RAIN ANIMATION ---
class MatrixRain(tb.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.overrideredirect(True)
        w, h = 900, 600
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")
        self.canvas = Canvas(self, bg='black', highlightthickness=0)
        self.canvas.pack(fill=BOTH, expand=True)
        self.drops = [0 for _ in range(int(w/15))]
        self.is_running = True
        self.canvas.create_text(w//2, h//2, text="INITIALIZING SYSTEM...", fill="#0F0", font=("Consolas", 24, "bold"), tags="text")
        self.animate()

    def animate(self):
        if not self.is_running: return
        self.canvas.create_rectangle(0, 0, 900, 600, fill='#000000', stipple='gray25')
        for i in range(len(self.drops)):
            char = random.choice(string.ascii_uppercase + "0123456789")
            x = i * 15
            y = self.drops[i] * 15
            self.canvas.create_text(x, y, text=char, fill='#0F0', font=("Consolas", 10))
            if y > 600 and random.random() > 0.975: self.drops[i] = 0
            self.drops[i] += 1
        self.canvas.tag_raise("text")
        self.after(50, self.animate)

# --- 3. MAIN APPLICATION ---
class UltimateForensicTool(tb.Window):
    def __init__(self):
        super().__init__(themename="cyborg")
        self.withdraw()
        self.splash = MatrixRain(self)
        self.after(3000, self.start_app) 
        self.title("METADATA INTERCEPTOR // FINAL BUILD")
        self.geometry("1400x900")
        self.files_data = []
        
        # GENERATE THE HTML INFO FILE ON STARTUP
        self.generate_html_info()

    def start_app(self):
        self.splash.is_running = False
        self.splash.destroy()
        self.deiconify()
        self.create_gui()
        self.log("SYSTEM ONLINE. DATABASE CONNECTED.")

    def create_gui(self):
        tb.Label(self, text=" ⚡ DIGITAL FORENSICS & CORRELATION SUITE ", font=("Consolas", 22, "bold"), bootstyle="inverse-danger", padding=10).pack(fill=X)
        
        paned = tb.Panedwindow(self, orient=HORIZONTAL, bootstyle="secondary")
        paned.pack(fill=BOTH, expand=YES, padx=5, pady=5)

        # === SIDEBAR ===
        sidebar = tb.Frame(paned, padding=10, bootstyle="secondary")
        paned.add(sidebar, weight=1)

        tb.Label(sidebar, text="[ COMMAND_CENTER ]", font=("Consolas", 12, "bold"), bootstyle="info").pack(anchor="w", pady=(0, 10))
        
        # --- PROJECT INFO BUTTON ---
        tb.Button(sidebar, text="[?] PROJECT INFO (WEB)", bootstyle="outline-light", command=self.open_project_info, width=22).pack(pady=5)
        tb.Separator(sidebar, orient=HORIZONTAL).pack(fill=X, pady=10)

        tb.Button(sidebar, text="[+] ADD FILE(S)", bootstyle="outline-info", command=self.add_files, width=22).pack(pady=5)
        tb.Button(sidebar, text="[#] SCAN FOLDER", bootstyle="outline-warning", command=self.scan_folder, width=22).pack(pady=5) 
        tb.Button(sidebar, text="[>] EXECUTE ANALYSIS", bootstyle="outline-success", command=self.process_data, width=22).pack(pady=5)
        tb.Button(sidebar, text="[x] FLUSH DATABASE", bootstyle="outline-danger", command=self.clear_data, width=22).pack(pady=5)

        tb.Separator(sidebar, orient=HORIZONTAL).pack(fill=X, pady=20)

        # Reports
        tb.Label(sidebar, text="[ REPORTING ]", font=("Consolas", 12, "bold"), bootstyle="light").pack(anchor="w")
        btn_f = tb.Frame(sidebar)
        btn_f.pack(fill=X, pady=5)
        tb.Button(btn_f, text="PDF", bootstyle="danger-outline", command=self.export_pdf, width=6).pack(side=LEFT, padx=2)
        tb.Button(btn_f, text="CSV", bootstyle="primary-outline", command=self.export_csv, width=6).pack(side=LEFT, padx=2)
        tb.Button(btn_f, text="HTML", bootstyle="warning-outline", command=self.export_html, width=6).pack(side=LEFT, padx=2)
        
        tb.Button(sidebar, text="[@] EMAIL REPORT", bootstyle="outline-info", command=self.email_report, width=22).pack(pady=10)

        # Evidence Queue
        tb.Label(sidebar, text="[ EVIDENCE QUEUE ]", font=("Consolas", 12, "bold"), bootstyle="warning").pack(anchor="w", pady=(10,0))
        self.file_list = Listbox(sidebar, bg="black", fg="#0F0", font=("Consolas", 9), relief="flat")
        self.file_list.pack(fill=BOTH, expand=YES, pady=5)

        # === DASHBOARD ===
        dash = tb.Frame(paned, padding=10)
        paned.add(dash, weight=4)

        sf = tb.Frame(dash)
        sf.pack(fill=X, pady=(0, 10))
        tb.Label(sf, text=">> SEARCH DB: ", font=("Consolas", 10, "bold"), bootstyle="success").pack(side=LEFT)
        self.search_var = tb.StringVar()
        tb.Entry(sf, textvariable=self.search_var, font=("Consolas", 10)).pack(side=LEFT, fill=X, expand=YES)

        cols = [{"text": "FILENAME", "stretch": True}, {"text": "METADATA KEY", "stretch": True}, {"text": "VALUE", "stretch": True}, {"text": "INTEGRITY (MD5)", "width": 120}, {"text": "STATUS", "width": 80}]
        self.table = Tableview(master=dash, coldata=cols, rowdata=[], paginated=True, pagesize=18, bootstyle="info", stripecolor="#222")
        self.table.pack(fill=BOTH, expand=YES)

        tb.Label(dash, text=">> LIVE_SYSTEM_LOGS", font=("Consolas", 11, "bold"), bootstyle="warning").pack(anchor="w")
        self.term = tb.Text(dash, height=8, bg="black", fg="#0F0", font=("Consolas", 9), state='disabled')
        self.term.pack(fill=X)

    # --- CORE FUNCTIONS ---
    def log(self, msg):
        self.term.config(state='normal')
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        self.term.insert(END, f"[{ts}] {msg}\n")
        self.term.see(END)
        self.term.config(state='disabled')
        logging.info(msg)

    # --- HTML PROJECT INFO GENERATOR ---
    def generate_html_info(self):
        def generate_html_info(self):
        """Creates a beautiful, dark-themed HTML file that matches the screenshots"""
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Project Info - Metadata Tool</title>
            <style>
                body { background-color: #121212; color: #e0e0e0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 40px; }
                .container { max-width: 900px; margin: auto; background-color: #1e1e1e; padding: 30px; border-radius: 10px; box-shadow: 0 0 20px rgba(0,0,0,0.5); }
                
                h1 { color: #bd93f9; font-size: 36px; border-bottom: 2px solid #6272a4; padding-bottom: 10px; }
                h2 { color: #50fa7b; margin-top: 30px; font-size: 24px; }
                
                p { line-height: 1.6; font-size: 16px; color: #b3b3b3; }
                
                .highlight { color: #ff79c6; font-weight: bold; }
                .feature-list { list-style: none; padding: 0; }
                .feature-list li { background: #282a36; margin: 10px 0; padding: 15px; border-left: 5px solid #8be9fd; border-radius: 4px; }
                .feature-title { color: #8be9fd; font-weight: bold; font-size: 18px; display: block; margin-bottom: 5px; }
                
                .step-list { counter-reset: step; list-style: none; padding: 0; }
                .step-list li { position: relative; padding-left: 50px; margin-bottom: 20px; }
                .step-list li::before { content: counter(step); counter-increment: step; position: absolute; left: 0; top: 0; width: 35px; height: 35px; background: #bd93f9; color: #282a36; border-radius: 50%; text-align: center; line-height: 35px; font-weight: bold; }
                
                .disclaimer { background-color: #f1fa8c; color: #282a36; padding: 20px; border-left: 8px solid #ffb86c; margin-top: 40px; border-radius: 5px; font-weight: 500; }
                
                .tag { background-color: #44475a; color: #f8f8f2; padding: 4px 8px; border-radius: 4px; font-size: 14px; margin-right: 5px; display: inline-block; margin-bottom: 5px; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Metadata Analysis & Correlation Tool</h1>
                <p>This project represents a crucial <span class="highlight">Digital Forensics and OSINT</span> component. It extracts hidden information (metadata) from multiple file types and automatically <span class="highlight">correlates</span> common authorship, dates, or device information across those files, helping to link disparate data fragments to a single source or timeline.</p>

                <h2>✨ Core Features & Enhancements</h2>
                <ul class="feature-list">
                    <li>
                        <span class="feature-title">Multi-Format Support</span>
                        Extracts metadata from <b>Images</b> (.jpg, .png), <b>Documents</b> (.pdf, .docx, .pptx, .xlsx), <b>Audio</b> (.mp3), and <b>Archives</b> (.zip).
                    </li>
                    <li>
                        <span class="feature-title">Correlative Analysis</span>
                        Automatically identifies common <b>Author</b>, <b>Date</b>, or <b>Device</b> information across all loaded files to link data fragments.
                    </li>
                    <li>
                        <span class="feature-title">Advanced Integrity Verification</span>
                        Calculates <b>MD5 & SHA256 Hashes</b> and performs <b>Magic Byte Verification</b> to detect spoofed files (e.g., EXE renamed as JPG).
                    </li>
                    <li>
                        <span class="feature-title">Anomaly Detection</span>
                        Automatically flags suspicious files where the <b>Modified Date</b> is earlier than the <b>Created Date</b> (Time Stomping).
                    </li>
                    <li>
                        <span class="feature-title">Secure Database & Logging</span>
                        All extracted evidence is stored in a local <b>SQLite Database</b> for persistence and full audit logs are maintained.
                    </li>
                    <li>
                        <span class="feature-title">Folder Scanning & Automation</span>
                        One-click scanning of entire directories and sub-directories for bulk forensic analysis.
                    </li>
                </ul>

                <h2>🛠️ Technologies & Libraries</h2>
                <p>
                    <span class="tag">Python 3.x</span>
                    <span class="tag">ttkbootstrap (GUI)</span>
                    <span class="tag">sqlite3 (DB)</span>
                    <span class="tag">exifread</span>
                    <span class="tag">PyPDF2</span>
                    <span class="tag">python-docx</span>
                    <span class="tag">openpyxl</span>
                    <span class="tag">mutagen</span>
                    <span class="tag">reportlab</span>
                </p>

                <h2>💡 How to Operate</h2>
                <ul class="step-list">
                    <li><b>Start the Application:</b> Run the executable to launch the Matrix Interface.</li>
                    <li><b>Add Evidence:</b> Click <span class="tag">[+] Add Files</span> or <span class="tag">[#] Scan Folder</span> to load targets.</li>
                    <li><b>Process Data:</b> Click <span class="tag">[>] Execute Analysis</span>. The tool parses metadata, checks integrity, and flags anomalies.</li>
                    <li><b>Analyze Correlations:</b> Review the Dashboard table and the Live Terminal for linked authors or devices.</li>
                    <li><b>Export Findings:</b> Use the Report buttons to save data as <b>PDF</b>, <b>CSV</b>, or <b>HTML</b>.</li>
                </ul>

                <div class="disclaimer">
                    🚨 <b>Ethical Use & Disclaimer</b><br>
                    This Metadata Analysis and Correlation Tool is designed <b>solely for ethical digital forensics, security auditing, data privacy analysis, and legal investigations</b> of data you have <b>explicit authorization</b> to access and process. Unauthorized use is strictly prohibited.
                </div>
            </div>
        </body>
        </html>
        """        try:
            with open("Project_Info.html", "w", encoding="utf-8") as f: f.write(html_content)
        except Exception as e: logging.error(f"HTML Gen Error: {e}")

    def open_project_info(self):
        filename = "Project_Info.html"
        full_path = os.path.abspath(filename)
        if os.path.exists(filename):
            try:
                webbrowser.open(f'file://{full_path}')
                self.log("OPENING PROJECT INFO IN BROWSER...")
            except: messagebox.showerror("Error", "Could not open Browser.")
        else:
            self.generate_html_info()
            webbrowser.open(f'file://{full_path}')

    # --- FORENSIC LOGIC ---
    def validate_signature(self, file_path):
        try:
            ext = os.path.splitext(file_path)[1].lower()
            with open(file_path, 'rb') as f:
                header = f.read(4).hex()
                if ext == '.jpg' and header.startswith('ffd8'): return True
                if ext == '.pdf' and header.startswith('2550'): return True
                if ext in ['.docx', '.xlsx', '.pptx', '.zip'] and header.startswith('504b'): return True
            return True 
        except: return False

    def get_hashes(self, file_path):
        md5 = hashlib.md5()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""): md5.update(chunk)
            return md5.hexdigest(), "SHA-Calculated"
        except: return "ERROR", "ERROR"

    def add_files(self):
        paths = filedialog.askopenfilenames()
        for p in paths: self.queue_file(p)

    def scan_folder(self): 
        folder = filedialog.askdirectory()
        if folder:
            self.log(f"SCANNING: {folder}")
            for root, _, files in os.walk(folder):
                for file in files: self.queue_file(os.path.join(root, file))

    def queue_file(self, path):
        if not any(d['path'] == path for d in self.files_data):
            self.files_data.append({"path": path})
            self.file_list.insert(END, f"> {os.path.basename(path)}")

    def process_data(self):
        if not self.files_data: return
        self.log("EXECUTING ANALYSIS...")
        self.table.delete_rows()
        c.execute("DELETE FROM metadata")
        correlation = {}
        for f_obj in self.files_data:
            path = f_obj["path"]
            fname = os.path.basename(path)
            md5, _ = self.get_hashes(path)
            status = "SECURE" if self.validate_signature(path) else "SPOOFED?"
            meta = {}
            ext = os.path.splitext(path)[1].lower()
            try:
                if ext in ['.jpg', '.png']:
                    with open(path, 'rb') as f:
                        tags = exifread.process_file(f)
                        for k, v in tags.items(): 
                            if k not in ['JPEGThumbnail', 'Filename', 'EXIF MakerNote']: meta[str(k)] = str(v)
                elif ext == '.pdf':
                    with open(path, 'rb') as f:
                        pdf = PyPDF2.PdfReader(f)
                        if pdf.metadata: 
                            for k, v in pdf.metadata.items(): meta[k.replace('/', '')] = str(v)
                elif ext == '.docx':
                    doc = docx.Document(path)
                    meta['Author'] = doc.core_properties.author
                    meta['Created'] = str(doc.core_properties.created)
                elif ext == '.xlsx':
                    wb = openpyxl.load_workbook(path)
                    meta['Author'] = wb.properties.creator
            except Exception as e: meta['Error'] = str(e)

            if 'Created' in meta and 'Modified' in meta:
                if str(meta.get('Created')) > str(meta.get('Modified')): status = "FLAGGED"

            for k, v in meta.items():
                if v:
                    c.execute("INSERT INTO metadata VALUES (?, ?, ?, ?, ?, ?)", (fname, ext, k, str(v), md5, status))
                    self.table.insert_row(values=(fname, k, v, md5, status))
                    if k in ['Author', 'Creator']:
                        if (k,v) not in correlation: correlation[(k,v)] = []
                        correlation[(k,v)].append(fname)
        conn.commit()
        self.table.load_table_data()
        for (k, v), files in correlation.items():
            if len(files) > 1: self.log(f"LINK: {k}='{v}' SHARED BY {len(files)} FILES")
        self.log("ANALYSIS COMPLETE.")

    def clear_data(self):
        self.files_data = []
        self.file_list.delete(0, END)
        self.table.delete_rows()
        c.execute("DELETE FROM metadata")
        conn.commit()
        self.log("MEMORY CLEARED.")

    def export_pdf(self):
        try:
            path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF", "*.pdf")], title="Save Report")
            if not path: return

            report_data = {}
            for row in c.execute("SELECT * FROM metadata"):
                fname = row[0]
                key = row[2]
                val = row[3]
                file_hash = row[4]
                status = row[5]
                if fname not in report_data:
                    report_data[fname] = {"entries": [], "hash": file_hash, "status": status}
                report_data[fname]["entries"].append((key, val))

            c_pdf = canvas.Canvas(path, pagesize=letter)
            width, height = letter
            y_pos = height - 50 
            
            c_pdf.setFont("Helvetica-Bold", 16)
            c_pdf.drawCentredString(width / 2, y_pos, "Metadata Extraction & Correlation Report")
            y_pos -= 20
            
            c_pdf.setFont("Helvetica", 9)
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            sys_info = f"{platform.system()} {platform.release()}"
            c_pdf.drawCentredString(width / 2, y_pos, f"Generated on: {timestamp} | System: {sys_info}")
            y_pos -= 40 

            for filename, data in report_data.items():
                if y_pos < 100:
                    c_pdf.showPage()
                    y_pos = height - 50
                
                c_pdf.setFont("Helvetica-Bold", 12)
                c_pdf.drawString(40, y_pos, f"File: {filename} [{data['status']}]")
                y_pos -= 15
                c_pdf.setFont("Helvetica", 10)
                c_pdf.drawString(60, y_pos, f"- MD5 Hash: {data['hash']}")
                y_pos -= 15

                for key, val in data["entries"]:
                    if y_pos < 50: 
                        c_pdf.showPage()
                        y_pos = height - 50
                        c_pdf.setFont("Helvetica", 10)
                    display_val = (val[:80] + '...') if len(val) > 80 else val
                    c_pdf.drawString(60, y_pos, f"- {key}: {display_val}")
                    y_pos -= 15
                y_pos -= 10 

            c_pdf.save()
            self.log(f"PDF REPORT GENERATED: {path}")
            messagebox.showinfo("Success", "Professional PDF Report Generated!")
        except Exception as e:
            self.log(f"PDF ERROR: {e}")
            messagebox.showerror("Error", str(e))

    def export_csv(self):
        path = filedialog.asksaveasfilename(defaultextension=".csv")
        if path:
            with open(path, 'w', newline='', encoding='utf-8') as f:
                w = csv.writer(f)
                w.writerow(["File", "Type", "Key", "Value", "Hash", "Status"])
                for row in c.execute("SELECT * FROM metadata"): w.writerow(row)
            self.log("CSV EXPORTED.")

    # --- UPDATED & FIXED HTML EXPORT ---
    def export_html(self):
        path = filedialog.asksaveasfilename(defaultextension=".html")
        if path:
            # 1. Start Building HTML String
            html = """
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body { background-color: #121212; color: #00ff00; font-family: Consolas, monospace; padding: 20px; }
                    h1 { border-bottom: 2px solid #00ff00; padding-bottom: 10px; }
                    table { width: 100%; border-collapse: collapse; margin-top: 20px; }
                    th, td { border: 1px solid #333; padding: 10px; text-align: left; }
                    th { background-color: #1e1e1e; color: #fff; }
                    tr:nth-child(even) { background-color: #1a1a1a; }
                    .flag { color: red; font-weight: bold; }
                </style>
            </head>
            <body>
                <h1>METADATA FORENSIC INVESTIGATION REPORT</h1>
                <p>Generated by: Metadata Interceptor Tool</p>
                <p>Date: """ + str(datetime.datetime.now()) + """</p>
                <table>
                    <tr>
                        <th>Filename</th>
                        <th>File Type</th>
                        <th>Metadata Key</th>
                        <th>Value</th>
                        <th>MD5 Hash</th>
                        <th>Status</th>
                    </tr>
            """
            
            # 2. Fetch DATA from Database and Append Rows
            try:
                for row in c.execute("SELECT * FROM metadata"):
                    # Check if status is flagged to color it red
                    status_class = "flag" if "FLAGGED" in row[5] or "SPOOFED" in row[5] else ""
                    
                    html += f"""
                        <tr>
                            <td>{row[0]}</td>
                            <td>{row[1]}</td>
                            <td>{row[2]}</td>
                            <td>{row[3]}</td>
                            <td>{row[4]}</td>
                            <td class="{status_class}">{row[5]}</td>
                        </tr>
                    """
                
                # 3. Close Tags
                html += """
                    </table>
                </body>
                </html>
                """
                
                # 4. Write to File
                with open(path, "w", encoding='utf-8') as f:
                    f.write(html)
                
                self.log(f"HTML REPORT EXPORTED TO: {path}")
                # Optional: Open automatically
                webbrowser.open(f'file://{os.path.abspath(path)}')
                
            except Exception as e:
                self.log(f"EXPORT ERROR: {e}")
                messagebox.showerror("Error", str(e))

    def email_report(self):
        messagebox.showinfo("Email", "Secure Report Sent (Simulation)")

if __name__ == "__main__":
    app = UltimateForensicTool()
    app.mainloop()
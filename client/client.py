import requests
import sys
import json
import os
import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox, ttk
import sys

# Add the project root to the Python path to make imports work properly
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Continue with the other imports
from PIL import Image, ImageTk
import io
import base64
import webbrowser
from datetime import datetime

class ClinicalBERTClient:
    """Client application for interacting with the ClinicalBERT server"""
    
    def __init__(self, server_url="http://localhost:5000"):
        self.server_url = server_url
        self.setup_ui()
        self.history = []
        
    def setup_ui(self):
        """Set up the user interface using Tkinter with a modern look"""
        self.root = tk.Tk()
        self.root.title("ClinicalBERT Medical Assistant")
        self.root.geometry("1000x700")
        self.root.minsize(800, 600)
        
        # Set theme colors
        self.colors = {
            "primary": "#4285F4",      # Google Blue
            "secondary": "#34A853",    # Google Green
            "accent": "#FBBC05",       # Google Yellow
            "warning": "#EA4335",      # Google Red
            "light_bg": "#F8F9FA",     # Light background
            "dark_bg": "#202124",      # Dark background
            "text": "#202124",         # Dark text
            "light_text": "#FFFFFF"    # Light text
        }
        
        # Configure styles
        self.style = ttk.Style()
        self.style.theme_use('clam')  # Use the 'clam' theme as a base
        
        # Configure ttk styles
        self.style.configure('TButton', 
                            font=('Segoe UI', 10),
                            background=self.colors["primary"],
                            foreground=self.colors["light_text"])
        
        self.style.configure('TLabel', 
                            font=('Segoe UI', 10),
                            background=self.colors["light_bg"],
                            foreground=self.colors["text"])
        
        self.style.configure('TFrame', 
                            background=self.colors["light_bg"])
        
        self.style.configure('Header.TLabel', 
                            font=('Segoe UI', 14, 'bold'),
                            background=self.colors["light_bg"],
                            foreground=self.colors["primary"])
        
        self.style.configure('Accent.TButton', 
                            font=('Segoe UI', 10),
                            background=self.colors["accent"],
                            foreground=self.colors["text"])
        
        self.style.configure('Secondary.TButton', 
                            font=('Segoe UI', 10),
                            background=self.colors["secondary"],
                            foreground=self.colors["light_text"])
        
        self.root.configure(bg=self.colors["light_bg"])
        
        # Create main container
        main_container = ttk.Frame(self.root)
        main_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create header with logo and title
        header_frame = ttk.Frame(main_container)
        header_frame.pack(fill="x", pady=5)
        
        # Try to create logo (placeholder)
        try:
            # This would be a real logo in production
            logo_data = """
            iVBORw0KGgoAAAANSUhEUgAAADAAAAAwCAYAAABXAvmHAAAACXBIWXMAAA7EAAAOxAGVKw4bAAACOklE
            QVRoge2Zv2sUQRTHPxeNRYhFEkgRxEYQFBsLOxsLwcJKsbBRbCwECxvBwkax8g+wsLD0DxCxsJBgYSMi
            FsYiYnEQQwwqOeWuuNndm9md2Z0JzAeWZW/ee/N9O7Mz+3bAYrFYUmQWWARWJC2qthSZAR4DG4BWpA3V
            lxozwCJbD16ndQYZ6jCL3lsP23oKTKhuUjwXGNzZeugs07yNHAdWyT98zXwJHFEdhdnHYIePad34nLpJ
            j/tEOfha1I2q9HexHn4sdeMcb6I3sA58AVLA7xMu4GNgVqV54DHwGfiFvGPcBG4DB4AC/+FPA/eBpcCx
            toA/wBrwFbgZKYf18HPAYuDYG8A98B9/TPD16ldq/sYmcCUkh5XU4WterQJnfAQYZPiFQD3T99Djgt8Z
            IIedXvpYXW6HTr+m+TVu6MqABM4EyuGUo//3SGPdBx4at1t9bcaB4vhE/eQwcDJADife+votQC69+88L
            4KGH/Br4GCCXj+qbdfjw14teUYYDdS6e4fcs8CtiLqF0sMuFDh6aH4E7wGLXFzdyXHS0edv13Q6h+eMk
            B9+414/yLVCRo472J0LFch3+FDLVSo1Tjvbvka5S0+JDwDjr6ONnqGCnkalmakw62vvM+JzscbTfDhXs
            DHKDS40DjvZ1qGAXKP8RjYJn6L14jIKZSAF9mAA+R+p7Bdina3AcWYtEit+xq3T4OeQG9ROy+Eo5HHKb
            W0M2Z8PMBHAPOXN0buaPgZ+GTLFYLBaLxZIK/wDWZ0M/kLwZQAAAAABJRU5ErkJggg==
            """
            logo_data = base64.b64decode(logo_data)
            logo_image = Image.open(io.BytesIO(logo_data))
            logo_photo = ImageTk.PhotoImage(logo_image)
            
            logo_label = tk.Label(header_frame, image=logo_photo, bg=self.colors["light_bg"])
            logo_label.image = logo_photo  # Keep a reference
            logo_label.pack(side="left", padx=10)
        except Exception:
            # If logo creation fails, just show text
            pass
        
        # Title label
        title_label = ttk.Label(header_frame, text="ClinicalBERT Medical Assistant", 
                               font=('Segoe UI', 18, 'bold'),
                               foreground=self.colors["primary"],
                               background=self.colors["light_bg"])
        title_label.pack(side="left", padx=10)
        
        # Server configuration frame
        server_frame = ttk.LabelFrame(main_container, text="Server Configuration")
        server_frame.pack(fill="x", pady=10, padx=5)
        
        server_inner_frame = ttk.Frame(server_frame)
        server_inner_frame.pack(fill="x", padx=10, pady=10)
        
        ttk.Label(server_inner_frame, text="Server URL:").grid(row=0, column=0, sticky="w", padx=5)
        self.server_entry = ttk.Entry(server_inner_frame, width=50)
        self.server_entry.insert(0, self.server_url)
        self.server_entry.grid(row=0, column=1, sticky="we", padx=5)
        
        test_btn = ttk.Button(server_inner_frame, text="Test Connection", command=self.test_connection)
        test_btn.grid(row=0, column=2, padx=5)
        
        server_inner_frame.columnconfigure(1, weight=1)
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(main_container)
        self.notebook.pack(fill="both", expand=True, pady=10)
        
        # Query tab
        query_frame = ttk.Frame(self.notebook)
        self.notebook.add(query_frame, text="Medical Query")
        
        # Set up the query tab
        query_label = ttk.Label(query_frame, text="Enter your medical question:", 
                               style="Header.TLabel")
        query_label.pack(anchor="w", pady=(10,5), padx=10)
        
        self.query_text = scrolledtext.ScrolledText(query_frame, height=5, 
                                                  font=('Segoe UI', 11),
                                                  wrap=tk.WORD,
                                                  bg="white",
                                                  fg=self.colors["text"])
        self.query_text.pack(fill="x", pady=5, padx=10)
        
        options_frame = ttk.Frame(query_frame)
        options_frame.pack(fill="x", padx=10, pady=5)
        
        self.web_search_var = tk.BooleanVar(value=True)
        self.web_search_check = ttk.Checkbutton(options_frame, 
                                              text="Search trusted medical websites for latest information",
                                              variable=self.web_search_var)
        self.web_search_check.pack(side="left")
        
        buttons_frame = ttk.Frame(query_frame)
        buttons_frame.pack(fill="x", padx=10, pady=5)
        
        submit_btn = ttk.Button(buttons_frame, text="Submit Query", 
                              command=self.submit_query,
                              style="TButton")
        submit_btn.pack(side="left", padx=5)
        
        clear_btn = ttk.Button(buttons_frame, text="Clear", 
                             command=self.clear_fields,
                             style="Accent.TButton")
        clear_btn.pack(side="left", padx=5)
        
        # File upload tab
        file_frame = ttk.Frame(self.notebook)
        self.notebook.add(file_frame, text="File Analysis")
        
        file_label = ttk.Label(file_frame, text="Upload a medical file for analysis:", 
                             style="Header.TLabel")
        file_label.pack(anchor="w", pady=(10,5), padx=10)
        
        file_info = ttk.Label(file_frame, 
                            text="Supported file types: .txt, .pdf, .csv, .json, and images (.jpg, .png)")
        file_info.pack(anchor="w", padx=10)
        
        self.file_path_var = tk.StringVar()
        file_path_frame = ttk.Frame(file_frame)
        file_path_frame.pack(fill="x", padx=10, pady=10)
        
        self.file_path_entry = ttk.Entry(file_path_frame, textvariable=self.file_path_var, state="readonly", width=50)
        self.file_path_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        browse_btn = ttk.Button(file_path_frame, text="Browse...", command=self.browse_file)
        browse_btn.pack(side="left")
        
        upload_btn = ttk.Button(file_path_frame, text="Upload & Analyze", 
                              command=self.upload_file,
                              style="Secondary.TButton")
        upload_btn.pack(side="left", padx=5)
        
        # History tab
        history_frame = ttk.Frame(self.notebook)
        self.notebook.add(history_frame, text="Query History")
        
        history_label = ttk.Label(history_frame, text="Previous Queries and Results:", 
                                style="Header.TLabel")
        history_label.pack(anchor="w", pady=(10,5), padx=10)
        
        self.history_list = tk.Listbox(history_frame, height=5, 
                                     font=('Segoe UI', 10),
                                     selectmode=tk.SINGLE)
        self.history_list.pack(fill="x", padx=10, pady=5)
        self.history_list.bind('<<ListboxSelect>>', self.on_history_select)
        
        # Results frame (shared between tabs)
        results_frame = ttk.LabelFrame(main_container, text="Results")
        results_frame.pack(fill="both", expand=True, pady=5, padx=5)
        
        result_inner_frame = ttk.Frame(results_frame)
        result_inner_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.result_text = scrolledtext.ScrolledText(result_inner_frame, 
                                                   height=12, 
                                                   font=('Segoe UI', 11),
                                                   wrap=tk.WORD,
                                                   bg="white",
                                                   fg=self.colors["text"])
        self.result_text.pack(fill="both", expand=True)
        
        # Action buttons below results
        action_frame = ttk.Frame(main_container)
        action_frame.pack(fill="x", pady=5, padx=5)
        
        save_btn = ttk.Button(action_frame, text="Save Results", command=self.save_results)
        save_btn.pack(side="left", padx=5)
        
        # Footer with status bar
        footer_frame = ttk.Frame(main_container)
        footer_frame.pack(fill="x", side="bottom")
        
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        
        self.status_bar = ttk.Label(footer_frame, textvariable=self.status_var,
                                  relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Add version and credits
        version_label = ttk.Label(footer_frame, text="v1.0", anchor=tk.E)
        version_label.pack(side=tk.RIGHT, padx=5)
        
    def test_connection(self):
        """Test the connection to the server"""
        self.status_var.set("Testing connection...")
        self.root.update()
        
        try:
            server_url = self.server_entry.get()
            response = requests.get(f"{server_url}/api/health", timeout=5)
            if response.status_code == 200:
                messagebox.showinfo("Connection Test", "Successfully connected to the server!")
                self.status_var.set("Connected to server")
            else:
                messagebox.showerror("Connection Test", f"Server returned status code: {response.status_code}")
                self.status_var.set("Connection failed")
        except Exception as e:
            messagebox.showerror("Connection Error", str(e))
            self.status_var.set(f"Error: {str(e)}")
    
    def submit_query(self):
        """Submit a query to the server"""
        query = self.query_text.get("1.0", tk.END).strip()
        if not query:
            messagebox.showwarning("Warning", "Please enter a query")
            return
        
        self.status_var.set("Processing query...")
        self.root.update()
        
        try:
            server_url = self.server_entry.get()
            search_web = self.web_search_var.get()
            
            data = {
                "query": query,
                "search_web": search_web
            }
            
            response = requests.post(
                f"{server_url}/api/query", 
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                self.display_results(result)
                
                # Add to history
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                history_item = {
                    "timestamp": timestamp,
                    "query": query,
                    "result": result,
                    "type": "query"
                }
                self.add_to_history(history_item)
                
                self.status_var.set("Query processed successfully")
            else:
                error_msg = f"Server error: {response.status_code}"
                if response.text:
                    error_msg += f" - {response.text}"
                self.result_text.delete("1.0", tk.END)
                self.result_text.insert(tk.END, error_msg)
                self.status_var.set("Query processing failed")
        except Exception as e:
            self.result_text.delete("1.0", tk.END)
            self.result_text.insert(tk.END, f"Error: {str(e)}")
            self.status_var.set(f"Error: {str(e)}")
    
    def browse_file(self):
        """Open file browser to select a file"""
        file_path = filedialog.askopenfilename(
            title="Select a medical file",
            filetypes=[
                ("Text files", "*.txt"),
                ("PDF files", "*.pdf"),
                ("CSV files", "*.csv"),
                ("JSON files", "*.json"),
                ("Image files", "*.jpg *.jpeg *.png"),
                ("All files", "*.*")
            ]
        )
        
        if file_path:
            self.file_path_var.set(file_path)
    
    def upload_file(self):
        """Upload a file for processing"""
        file_path = self.file_path_var.get()
        if not file_path:
            messagebox.showwarning("Warning", "Please select a file first")
            return
        
        self.status_var.set(f"Uploading file: {os.path.basename(file_path)}...")
        self.root.update()
        
        try:
            server_url = self.server_entry.get()
            
            with open(file_path, "rb") as file:
                files = {"file": (os.path.basename(file_path), file)}
                response = requests.post(
                    f"{server_url}/api/process-file",
                    files=files,
                    timeout=60
                )
            
            if response.status_code == 200:
                result = response.json()
                self.display_results(result)
                
                # Add to history
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                history_item = {
                    "timestamp": timestamp,
                    "filename": os.path.basename(file_path),
                    "result": result,
                    "type": "file"
                }
                self.add_to_history(history_item)
                
                self.status_var.set("File processed successfully")
            else:
                error_msg = f"Server error: {response.status_code}"
                if response.text:
                    error_msg += f" - {response.text}"
                self.result_text.delete("1.0", tk.END)
                self.result_text.insert(tk.END, error_msg)
                self.status_var.set("File processing failed")
        except Exception as e:
            self.result_text.delete("1.0", tk.END)
            self.result_text.insert(tk.END, f"Error: {str(e)}")
            self.status_var.set(f"Error: {str(e)}")
    
    def display_results(self, result):
        """Display the results in a readable format"""
        self.result_text.delete("1.0", tk.END)
        self.result_text.tag_configure("bold", font=('Segoe UI', 11, 'bold'))
        self.result_text.tag_configure("title", font=('Segoe UI', 12, 'bold'), foreground=self.colors["primary"])
        self.result_text.tag_configure("subtitle", font=('Segoe UI', 11, 'bold'), foreground=self.colors["secondary"])
        self.result_text.tag_configure("url", font=('Segoe UI', 10), foreground="blue", underline=1)
        
        # Format the results nicely
        if "error" in result:
            self.result_text.insert(tk.END, "Error: ", "bold")
            self.result_text.insert(tk.END, f"{result['error']}\n")
            return
        
        if "web_results" in result and result["web_results"]:
            self.result_text.insert(tk.END, "INFORMATION FROM TRUSTED MEDICAL WEBSITES\n", "title")
            self.result_text.insert(tk.END, "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n")
            
            for i, item in enumerate(result["web_results"]):
                if i > 0:
                    self.result_text.insert(tk.END, "\n" + "─" * 50 + "\n\n")
                
                if "title" in item:
                    self.result_text.insert(tk.END, f"{item['title']}\n", "subtitle")
                
                source = item.get('source', 'Unknown source')
                # Make the source a clickable URL
                self.result_text.insert(tk.END, f"Source: ")
                url_start = self.result_text.index(tk.INSERT)
                self.result_text.insert(tk.END, source, "url")
                url_end = self.result_text.index(tk.INSERT)
                self.result_text.tag_add("url_" + str(i), url_start, url_end)
                self.result_text.tag_bind("url_" + str(i), "<Button-1>", lambda e, url=source: self.open_url(url))
                self.result_text.insert(tk.END, "\n\n")
                
                self.result_text.insert(tk.END, f"{item['content']}\n")
        
        # If there's model output that has been processed into text
        if "response" in result:
            if "web_results" in result and result["web_results"]:
                self.result_text.insert(tk.END, "\n\n")
            
            self.result_text.insert(tk.END, "MODEL ANALYSIS\n", "title")
            self.result_text.insert(tk.END, "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n")
            self.result_text.insert(tk.END, result["response"])
        
        # If file-specific information is available
        if "file_type" in result:
            self.result_text.insert(tk.END, "\n\nFile Type: ", "bold")
            self.result_text.insert(tk.END, result["file_type"].upper())
            
            if "rows" in result and "columns" in result:
                self.result_text.insert(tk.END, f"\nData: {result['rows']} rows, {result['columns']} columns")
    
    def add_to_history(self, item):
        """Add an item to the query history"""
        self.history.append(item)
        
        # Update history listbox
        if item["type"] == "query":
            display_text = f"{item['timestamp']} - Query: {item['query'][:30]}..."
        else:  # File
            display_text = f"{item['timestamp']} - File: {item['filename']}"
            
        self.history_list.insert(tk.END, display_text)
    
    def on_history_select(self, event):
        """Handler for when a history item is selected"""
        if not self.history_list.curselection():
            return
        
        index = self.history_list.curselection()[0]
        if index < len(self.history):
            item = self.history[index]
            
            # Display the historical result
            if item["type"] == "query":
                self.query_text.delete("1.0", tk.END)
                self.query_text.insert(tk.END, item["query"])
                self.notebook.select(0)  # Switch to query tab
            
            self.display_results(item["result"])
    
    def open_url(self, url):
        """Open a URL in the default browser"""
        try:
            webbrowser.open(url)
        except Exception as e:
            messagebox.showerror("Error", f"Could not open URL: {str(e)}")
    
    def save_results(self):
        """Save the current results to a file"""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            title="Save Results"
        )
        
        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(self.result_text.get("1.0", tk.END))
                self.status_var.set(f"Results saved to {os.path.basename(file_path)}")
            except Exception as e:
                messagebox.showerror("Save Error", str(e))
                self.status_var.set(f"Error saving results: {str(e)}")
    
    def clear_fields(self):
        """Clear the query and result fields"""
        self.query_text.delete("1.0", tk.END)
        self.result_text.delete("1.0", tk.END)
        self.status_var.set("Ready")
    
    def run(self):
        """Run the client application"""
        self.root.mainloop()

if __name__ == "__main__":
    # Default server URL can be overridden by command line argument
    server_url = "http://localhost:5000"
    if len(sys.argv) > 1:
        server_url = sys.argv[1]
    
    client = ClinicalBERTClient(server_url)
    client.run()
#!/usr/bin/env python3
"""
XAMPP Control Panel for Linux
A GUI application to control XAMPP services on Linux systems.
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import subprocess
import threading
import os
import sys
from datetime import datetime

# Detach from terminal
if os.fork():
    sys.exit()
os.setsid()

class XAMPPController:
    def __init__(self, root):
        self.root = root
        self.root.title("XAMPP Control Panel")
        self.root.geometry("700x600")
        self.root.resizable(True, True)
        
        # XAMPP installation path - modify if needed
        self.xampp_path = "/opt/lampp"
        self.xampp_script = os.path.join(self.xampp_path, "lampp")
        
        # Check if XAMPP is installed
        if not os.path.exists(self.xampp_script):
            messagebox.showerror("Error", 
                f"XAMPP not found at {self.xampp_path}\n"
                "Please install XAMPP or modify the path in the script.")
            sys.exit(1)
        
        # Check for available privilege escalation methods
        self.auth_method = self.detect_auth_method()
        
        # Configure styles for toggle buttons
        style = ttk.Style()
        style.configure("Start.TButton", foreground="green")
        style.configure("Stop.TButton", foreground="red")
        
        self.setup_ui()
        self.log_message(f"Using authentication method: {self.auth_method}")
        self.update_status()
        
    def detect_auth_method(self):
        """Detect the best available authentication method"""
        methods = {
            'direct': lambda: os.access(self.xampp_script, os.X_OK),
            'gksu': lambda: subprocess.run(['which', 'gksu'], capture_output=True).returncode == 0,
            'pkexec': lambda: subprocess.run(['which', 'pkexec'], capture_output=True).returncode == 0,
            'sudo': lambda: subprocess.run(['which', 'sudo'], capture_output=True).returncode == 0,
        }
        
        for method, check in methods.items():
            try:
                if check():
                    return method
            except:
                continue
        return 'sudo'  # fallback
        
    def setup_ui(self):
        # Main frame with reduced padding
        main_frame = ttk.Frame(self.root, padding="5")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Title - smaller font
        title_label = ttk.Label(main_frame, text="XAMPP Control Panel", 
                               font=("Arial", 14, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 10))
        
        # Services section - more compact
        services_frame = ttk.LabelFrame(main_frame, text="Services", padding="5")
        services_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 5))
        services_frame.columnconfigure(1, weight=1)
        
        # Service controls - more compact layout
        services = [
            ("Apache", "apache"),
            ("MySQL", "mysql"),
            ("ProFTPD", "ftp")
        ]
        
        self.service_vars = {}
        self.service_labels = {}
        self.service_buttons = {}
        self.service_status = {}
        
        for i, (service_name, service_key) in enumerate(services):
            # Service name
            name_label = ttk.Label(services_frame, text=service_name, font=("Arial", 9, "bold"))
            name_label.grid(row=i, column=0, sticky=tk.W, padx=(0, 5), pady=2)
            
            # Status label
            status_label = ttk.Label(services_frame, text="Checking...", foreground="orange")
            status_label.grid(row=i, column=1, sticky=tk.W, padx=(0, 5), pady=2)
            self.service_labels[service_key] = status_label
            self.service_status[service_key] = False
            
            # Toggle button (Start/Stop) - smaller
            toggle_btn = ttk.Button(services_frame, text="Start", width=8,
                                  command=lambda s=service_key: self.toggle_service(s))
            toggle_btn.grid(row=i, column=2, padx=2, pady=2)
            self.service_buttons[service_key] = toggle_btn
            
            # Restart button - smaller
            restart_btn = ttk.Button(services_frame, text="Restart", width=8,
                                   command=lambda s=service_key: self.restart_service(s))
            restart_btn.grid(row=i, column=3, padx=2, pady=2)
        
        # Global controls - more compact
        control_frame = ttk.LabelFrame(main_frame, text="Global Controls", padding="5")
        control_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 5))
        
        # Pack buttons in two rows for compactness
        ttk.Button(control_frame, text="Start All", width=10,
                  command=self.start_all).grid(row=0, column=0, padx=2, pady=2)
        ttk.Button(control_frame, text="Stop All", width=10,
                  command=self.stop_all).grid(row=0, column=1, padx=2, pady=2)
        ttk.Button(control_frame, text="Restart All", width=10,
                  command=self.restart_all).grid(row=0, column=2, padx=2, pady=2)
        ttk.Button(control_frame, text="Reload", width=10,
                  command=self.reload_xampp).grid(row=0, column=3, padx=2, pady=2)
        
        # Quick access buttons - more compact
        access_frame = ttk.LabelFrame(main_frame, text="Quick Access", padding="5")
        access_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 5))
        
        ttk.Button(access_frame, text="Localhost", width=10,
                  command=self.open_localhost).grid(row=0, column=0, padx=2, pady=2)
        ttk.Button(access_frame, text="phpMyAdmin", width=10,
                  command=self.open_phpmyadmin).grid(row=0, column=1, padx=2, pady=2)
        ttk.Button(access_frame, text="Web Directory", width=12,
                  command=self.open_htdocs).grid(row=0, column=2, padx=2, pady=2)
        ttk.Button(access_frame, text="Error Logs", width=10,
                  command=self.view_error_logs).grid(row=0, column=3, padx=2, pady=2)
        
        # Status and refresh - compact
        status_frame = ttk.Frame(main_frame)
        status_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 5))
        status_frame.columnconfigure(0, weight=1)
        
        ttk.Button(status_frame, text="Refresh Status", 
                  command=self.update_status).grid(row=0, column=1, padx=2)
        
        # Create PanedWindow for resizable log section
        paned_window = ttk.PanedWindow(main_frame, orient=tk.VERTICAL)
        paned_window.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 5))
        
        # Top pane for info (collapsible)
        info_frame = ttk.LabelFrame(paned_window, text="Service Info", padding="5")
        paned_window.add(info_frame, weight=0)
        
        info_text = """Apache: Web server (localhost) • MySQL: Database • ProFTPD: FTP server"""
        info_label = ttk.Label(info_frame, text=info_text, justify=tk.LEFT, 
                              font=("Arial", 8), foreground="gray40")
        info_label.grid(row=0, column=0, sticky=tk.W)
        
        # Bottom pane for log (main space)
        log_frame = ttk.LabelFrame(paned_window, text="Output Log", padding="5")
        paned_window.add(log_frame, weight=1)
        
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        # Log text area - bigger by default
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, width=70, font=("Courier", 9))
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Log controls frame
        log_controls = ttk.Frame(log_frame)
        log_controls.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(5, 0))
        log_controls.columnconfigure(0, weight=1)
        
        ttk.Button(log_controls, text="Clear Log", 
                  command=self.clear_log).grid(row=0, column=1, pady=2)
        
        # Configure main frame grid weights for resizing
        main_frame.rowconfigure(5, weight=1)  # Make paned window expandable
        
    def create_tooltip(self, widget, text):
        """Create a tooltip for a widget"""
        def on_enter(event):
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
            label = ttk.Label(tooltip, text=text, background="lightyellow", 
                            relief="solid", borderwidth=1, font=("Arial", 9))
            label.pack()
            widget.tooltip = tooltip
        
        def on_leave(event):
            if hasattr(widget, 'tooltip'):
                widget.tooltip.destroy()
                delattr(widget, 'tooltip')
        
        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)
    
    def toggle_service(self, service):
        """Toggle service between start and stop"""
        if self.service_status.get(service, False):
            self.stop_service(service)
        else:
            self.start_service(service)
    
    def update_toggle_button(self, service, is_running):
        """Update the toggle button text and state"""
        if service in self.service_buttons:
            if is_running:
                self.service_buttons[service].config(text="Stop", style="Stop.TButton")
            else:
                self.service_buttons[service].config(text="Start", style="Start.TButton")
        self.service_status[service] = is_running
        
    def log_message(self, message):
        """Add message to log with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.root.update()
        
    def clear_log(self):
        """Clear the log text"""
        self.log_text.delete(1.0, tk.END)
        
    def run_command(self, command, show_output=True):
        """Run a command and return the result"""
        try:
            self.log_message(f"Running: {' '.join(command)}")
            result = subprocess.run(command, capture_output=True, text=True, timeout=30)
            
            if show_output:
                if result.stdout:
                    self.log_message(f"Output: {result.stdout.strip()}")
                if result.stderr:
                    self.log_message(f"Error: {result.stderr.strip()}")
                    
            return result.returncode == 0, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            self.log_message("Command timed out")
            return False, "", "Command timed out"
        except Exception as e:
            self.log_message(f"Error running command: {str(e)}")
            return False, "", str(e)
    
    def run_xampp_command(self, action):
        """Run XAMPP command with alternative methods"""
        # Try multiple approaches in order
        methods = [
            # Method 1: Direct execution (if user has permissions)
            [self.xampp_script, action],
            # Method 2: sudo without password prompt  
            ["sudo", "-n", self.xampp_script, action],
            # Method 3: pkexec (will prompt for password)
            ["pkexec", self.xampp_script, action],
            # Method 4: su with timeout
            ["timeout", "1", "sudo", self.xampp_script, action],
        ]
        
        for i, command in enumerate(methods):
            try:
                self.log_message(f"Trying method {i+1}: {' '.join(command)}")
                result = subprocess.run(command, capture_output=True, text=True, timeout=30)
                
                if result.returncode == 0:
                    if result.stdout:
                        self.log_message(f"Output: {result.stdout.strip()}")
                    return True, result.stdout, result.stderr
                elif i < len(methods) - 1:  # Not the last method
                    self.log_message(f"Method {i+1} failed, trying next...")
                    continue
                else:
                    if result.stderr:
                        self.log_message(f"Error: {result.stderr.strip()}")
                    return False, result.stdout, result.stderr
                    
            except subprocess.TimeoutExpired:
                self.log_message(f"Method {i+1} timed out")
                if i == len(methods) - 1:
                    return False, "", "All methods timed out"
                continue
            except Exception as e:
                self.log_message(f"Method {i+1} exception: {str(e)}")
                if i == len(methods) - 1:
                    return False, "", str(e)
                continue
        
        return False, "", "All methods failed"
    
    def start_service(self, service):
        """Start a specific service"""
        def task():
            # Disable button during operation
            if service in self.service_buttons:
                self.service_buttons[service].config(state="disabled")
            
            success, _, _ = self.run_xampp_command(f"start{service}")
            if success:
                self.log_message(f"{service.upper()} started successfully")
            else:
                self.log_message(f"Failed to start {service.upper()}")
            
            # Re-enable button and update status
            if service in self.service_buttons:
                self.service_buttons[service].config(state="normal")
            self.update_status()
        
        threading.Thread(target=task, daemon=True).start()
    
    def stop_service(self, service):
        """Stop a specific service"""
        def task():
            # Disable button during operation
            if service in self.service_buttons:
                self.service_buttons[service].config(state="disabled")
            
            success, _, _ = self.run_xampp_command(f"stop{service}")
            if success:
                self.log_message(f"{service.upper()} stopped successfully")
            else:
                self.log_message(f"Failed to stop {service.upper()}")
            
            # Re-enable button and update status
            if service in self.service_buttons:
                self.service_buttons[service].config(state="normal")
            self.update_status()
        
        threading.Thread(target=task, daemon=True).start()
    
    def restart_service(self, service):
        """Restart a specific service"""
        def task():
            self.log_message(f"Restarting {service.upper()}...")
            self.run_xampp_command(f"stop{service}")
            self.run_xampp_command(f"start{service}")
            self.log_message(f"{service.upper()} restarted")
            self.update_status()
        
        threading.Thread(target=task, daemon=True).start()
    
    def start_all(self):
        """Start all XAMPP services"""
        def task():
            success, _, _ = self.run_xampp_command("start")
            if success:
                self.log_message("All services started successfully")
            else:
                self.log_message("Failed to start all services")
            self.update_status()
        
        threading.Thread(target=task, daemon=True).start()
    
    def stop_all(self):
        """Stop all XAMPP services"""
        def task():
            success, _, _ = self.run_xampp_command("stop")
            if success:
                self.log_message("All services stopped successfully")
            else:
                self.log_message("Failed to stop all services")
            self.update_status()
        
        threading.Thread(target=task, daemon=True).start()
    
    def restart_all(self):
        """Restart all XAMPP services"""
        def task():
            success, _, _ = self.run_xampp_command("restart")
            if success:
                self.log_message("All services restarted successfully")
            else:
                self.log_message("Failed to restart all services")
            self.update_status()
        
        threading.Thread(target=task, daemon=True).start()
    
    def reload_xampp(self):
        """Reload XAMPP configuration"""
        def task():
            success, _, _ = self.run_xampp_command("reload")
            if success:
                self.log_message("XAMPP configuration reloaded")
            else:
                self.log_message("Failed to reload XAMPP configuration")
            self.update_status()
        
        threading.Thread(target=task, daemon=True).start()
    
    def check_service_status(self, service):
        """Check if a service is running"""
        try:
            if service == "apache":
                result = subprocess.run(["pgrep", "-f", "httpd"], capture_output=True)
            elif service == "mysql":
                result = subprocess.run(["pgrep", "-f", "mysqld"], capture_output=True)
            elif service == "ftp":
                result = subprocess.run(["pgrep", "-f", "proftpd"], capture_output=True)
            else:
                return False
            
            return result.returncode == 0
        except Exception:
            return False
    
    def update_status(self):
        """Update service status display"""
        def task():
            services = ["apache", "mysql", "ftp"]
            for service in services:
                if service in self.service_labels:
                    is_running = self.check_service_status(service)
                    if is_running:
                        self.service_labels[service].config(text="Running", foreground="green")
                    else:
                        self.service_labels[service].config(text="Stopped", foreground="red")
                    
                    # Update toggle button
                    self.update_toggle_button(service, is_running)
        
        threading.Thread(target=task, daemon=True).start()
    
    def open_localhost(self):
        """Open localhost in default browser"""
        try:
            subprocess.run(["xdg-open", "http://localhost"], check=True)
            self.log_message("Opening localhost in browser")
        except Exception as e:
            self.log_message(f"Failed to open localhost: {str(e)}")
    
    def open_phpmyadmin(self):
        """Open phpMyAdmin in default browser"""
        try:
            subprocess.run(["xdg-open", "http://localhost/phpmyadmin"], check=True)
            self.log_message("Opening phpMyAdmin in browser")
        except Exception as e:
            self.log_message(f"Failed to open phpMyAdmin: {str(e)}")
    
    def open_htdocs(self):
        """Open htdocs directory in file manager"""
        try:
            htdocs_path = os.path.join(self.xampp_path, "htdocs")
            subprocess.run(["xdg-open", htdocs_path], check=True)
            self.log_message("Opening htdocs directory")
        except Exception as e:
            self.log_message(f"Failed to open htdocs: {str(e)}")
    
    def view_error_logs(self):
        """Open error logs in a new window"""
        log_window = tk.Toplevel(self.root)
        log_window.title("XAMPP Error Logs")
        log_window.geometry("800x600")
        
        notebook = ttk.Notebook(log_window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Apache error log
        apache_frame = ttk.Frame(notebook)
        notebook.add(apache_frame, text="Apache Error Log")
        
        apache_log = scrolledtext.ScrolledText(apache_frame)
        apache_log.pack(fill=tk.BOTH, expand=True)
        
        try:
            with open(f"{self.xampp_path}/logs/error_log", "r") as f:
                apache_log.insert(tk.END, f.read())
        except Exception as e:
            apache_log.insert(tk.END, f"Could not read Apache error log: {str(e)}")
        
        # MySQL error log
        mysql_frame = ttk.Frame(notebook)
        notebook.add(mysql_frame, text="MySQL Error Log")
        
        mysql_log = scrolledtext.ScrolledText(mysql_frame)
        mysql_log.pack(fill=tk.BOTH, expand=True)
        
        try:
            with open(f"{self.xampp_path}/var/mysql/$(hostname).err", "r") as f:
                mysql_log.insert(tk.END, f.read())
        except Exception as e:
            mysql_log.insert(tk.END, f"Could not read MySQL error log: {str(e)}")

def main():
    # Check if running as root (not recommended for GUI apps)
    if os.geteuid() == 0:
        print("Warning: Running GUI applications as root is not recommended.")
        print("This application will use multiple methods for administrative tasks.")
    
    root = tk.Tk()
    app = XAMPPController(root)
    
    # Handle window closing
    def on_closing():
        root.quit()
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    try:
        root.mainloop()
    except KeyboardInterrupt:
        print("\nApplication interrupted by user")
        sys.exit(0)

if __name__ == "__main__":
    main()

#!/bin/env python3
# SPDX-License-Identifier: MIT

import tkinter as tk
from tkinter import messagebox, filedialog
import serial.tools.list_ports
from busytag import BusyTag

import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.dialogs import ColorChooserDialog

class BusyTagGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("BusyTag Controller")
        self.root.geometry("900x700")
        self.root.minsize(800, 600)
        
        # Modern styling
        #self.root.iconphoto(False, tk.PhotoImage(file="busytag/icon.png"))
        
        self.bt = None
        self.device_path = tk.StringVar()
        self.color_value = tk.StringVar(value="000000")
        self.brightness_value = tk.StringVar(value="100")
        
        self.create_widgets()
        self.refresh_ports()
    
    def create_widgets(self):
        # Main container with modern padding
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Device selection with modern layout
        device_frame = ttk.Labelframe(main_frame, text="Device Connection")
        device_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Use grid layout for better alignment
        #ttk.Label(device_frame, text="Serial Port:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.port_combobox = ttk.Combobox(device_frame, textvariable=self.device_path, state="readonly")
        self.port_combobox.grid(row=0, column=1, sticky=tk.EW, padx=10, pady=5)
        
        btn_frame = ttk.Frame(device_frame)
        btn_frame.grid(row=0, column=2, sticky=tk.E, pady=5)
        
        ttk.Button(btn_frame, text="Refresh", command=self.refresh_ports, bootstyle="info-outline").pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Connect", command=self.connect_device, bootstyle="success-outline").pack(side=tk.LEFT, padx=5)
        
        # Configure grid weights
        device_frame.columnconfigure(1, weight=1)
        
        # Device info display with scrollbar
        info_frame = ttk.Labelframe(main_frame, text="Device Information")
        info_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(info_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.info_text = tk.Text(info_frame, height=10, wrap=tk.WORD, yscrollcommand=scrollbar.set)
        self.info_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.info_text.config(state=tk.DISABLED)
        
        scrollbar.config(command=self.info_text.yview)
        
        # LED Control with modern layout
        led_frame = ttk.Labelframe(main_frame, text="LED Control")
        led_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Color selection with modern styling
        color_row = ttk.Frame(led_frame)
        color_row.pack(fill=tk.X, pady=5)
        
        ttk.Label(color_row, text="Color (HEX):").pack(side=tk.LEFT)
        color_entry = ttk.Entry(color_row, textvariable=self.color_value, width=8)
        color_entry.pack(side=tk.LEFT, padx=10)
        
        ttk.Button(color_row, text="Pick Color", command=self.pick_color, bootstyle="info-outline").pack(side=tk.LEFT)
        ttk.Button(color_row, text="Set Color", command=self.set_led_color, bootstyle="primary-outline").pack(side=tk.LEFT)
        
        # LED selection with better spacing
        led_row = ttk.Frame(led_frame)
        led_row.pack(fill=tk.X, pady=5)
        
        ttk.Label(led_row, text="LEDs:").pack(side=tk.LEFT)
        self.led_all = tk.IntVar(value=1)
        ttk.Checkbutton(led_row, text="All", variable=self.led_all, command=self.toggle_led_all).pack(side=tk.LEFT, padx=10)
        
        self.led_vars = []
        for i in range(7):
            var = tk.IntVar()
            self.led_vars.append(var)
            ttk.Checkbutton(led_row, text=f"LED{i}", variable=var, command=self.deselect_led_all).pack(side=tk.LEFT, padx=2)
        
        # Picture management with modern layout
        picture_frame = ttk.Labelframe(main_frame, text="Picture Management")
        picture_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        picture_btn_frame = ttk.Frame(picture_frame)
        picture_btn_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(picture_btn_frame, text="List Pictures", command=self.list_pictures, bootstyle="info-outline").pack(side=tk.LEFT, padx=2)
        ttk.Button(picture_btn_frame, text="Upload Picture", command=self.upload_picture, bootstyle="success-outline").pack(side=tk.LEFT, padx=2)
        ttk.Button(picture_btn_frame, text="Display Picture", command=self.display_picture, bootstyle="primary-outline").pack(side=tk.LEFT, padx=2)
        ttk.Button(picture_btn_frame, text="Delete Picture", command=self.delete_picture, bootstyle="danger-outline").pack(side=tk.LEFT, padx=2)
        
        # Add scrollbar to picture list
        list_scrollbar = ttk.Scrollbar(picture_frame)
        list_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.picture_list = tk.Listbox(picture_frame, yscrollcommand=list_scrollbar.set, selectbackground="#4a90e2", selectforeground="white")
        self.picture_list.pack(fill=tk.BOTH, expand=True)
        
        list_scrollbar.config(command=self.picture_list.yview)
        
        # Brightness control
        brightness_row = ttk.Frame(picture_frame)
        brightness_row.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Label(brightness_row, text="Brightness (%):").pack(side=tk.LEFT)
        brightness_entry = ttk.Entry(brightness_row, textvariable=self.brightness_value, width=5)
        brightness_entry.pack(side=tk.LEFT, padx=10)
        ttk.Button(brightness_row, text="Set Brightness", command=self.set_brightness, bootstyle="primary-outline").pack(side=tk.LEFT)
        
        # Modern status bar
        self.status_var = tk.StringVar()
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(fill=tk.X, padx=10, pady=(0, 10))
    
    def refresh_ports(self):
        """Refresh the list of available serial ports"""
        ports = [port.device for port in serial.tools.list_ports.comports()]
        self.port_combobox["values"] = ports
        if ports:
            self.device_path.set(ports[0])
    
    def connect_device(self):
        """Connect to the selected BusyTag device"""
        if not self.device_path.get():
            messagebox.showerror("Error", "No device selected")
            return
        
        try:
            self.bt = BusyTag(self.device_path.get())
            self.show_device_info()
            self.status_var.set(f"Connected to {self.device_path.get()}")
        except Exception as e:
            messagebox.showerror("Connection Error", str(e))
            self.status_var.set("Connection failed")
    
    def show_device_info(self):
        """Display device information"""
        if not self.bt:
            return
        
        try:
            info = self.bt.showDeviceInfo()
            self.info_text.config(state=tk.NORMAL)
            self.info_text.delete(1.0, tk.END)
            self.info_text.insert(tk.END, f"ID: {info['id']}\n")
            self.info_text.insert(tk.END, f"Name: {info['name']}\n")
            self.info_text.insert(tk.END, f"Manufacturer: {info['manufacture']}\n")
            self.info_text.insert(tk.END, f"Firmware: {info['firmware_version']}\n")
            self.info_text.config(state=tk.DISABLED)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to get device info: {e}")
    
    def pick_color(self):
        """Open a color picker dialog using ttkbootstrap's ColorChooserDialog"""
        # Get current color from the entry field
        current_color = self.color_value.get()
        
        #result = askcolor(color=f"#{current_color}", title = "Colour Chooser") 
        cc = ttk.dialogs.ColorChooserDialog(parent=self.root, initialcolor=f"#{current_color}")
        cc.show()

        result = cc.result
        
        if result:
            self.color_value.set(result.hex[1:])
    
    def toggle_led_all(self):
        """Toggle all LEDs selection"""
        if self.led_all.get():
            # Select all LEDs
            for var in self.led_vars:
                var.set(1)
    
    def deselect_led_all(self):
        """Deselect all LEDs checkbox"""
        self.led_all.set(0)

    def set_led_color(self):
        """Set LED color"""
        if not self.bt:
            messagebox.showerror("Error", "Not connected to device")
            return
        
        color = self.color_value.get()
        if len(color) not in [3, 6]:
            messagebox.showerror("Error", "Color must be 3 or 6 hex digits")
            return
        
        try:
            leds = []
            if self.led_all.get():
                leds = [BusyTag.LEDS.ALL]
            else:
                # Get selected individual LEDs
                for i, var in enumerate(self.led_vars):
                    if var.get():
                        leds.append(BusyTag.LEDS[f"LED{i}"])
                
                if not leds:
                    messagebox.showerror("Error", "No LEDs selected")
                    return
            
            self.bt.setSolidColor(color, leds=leds)
            self.status_var.set(f"LED color set to {color}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to set LED color: {e}")
    
    def set_brightness(self):
        """Set display brightness"""
        if not self.bt:
            messagebox.showerror("Error", "Not connected to device")
            return
        
        try:
            brightness = int(self.brightness_value.get())
            if brightness < 1 or brightness > 100:
                messagebox.showerror("Error", "Brightness must be between 1 and 100")
                return
            
            self.bt.setDisplayBrightness(brightness)
            self.status_var.set(f"Brightness set to {brightness}%")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to set brightness: {e}")
    
    def list_pictures(self):
        """List available pictures on the device"""
        if not self.bt:
            messagebox.showerror("Error", "Not connected to device")
            return
        
        try:
            pictures = self.bt.getPictureList()
            self.picture_list.delete(0, tk.END)
            for pic in pictures:
                kb_size = pic["size"] / 1024
                self.picture_list.insert(tk.END, f"{pic['name']} ({kb_size:.2f} kB)")
            self.status_var.set(f"Found {len(pictures)} pictures")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to list pictures: {e}")
    
    def upload_picture(self):
        """Upload a picture to the device"""
        if not self.bt:
            messagebox.showerror("Error", "Not connected to device")
            return
        
        filepath = filedialog.askopenfilename(
            title="Select Picture",
            filetypes=[("Image Files", "*.jpg *.jpeg *.png *.bmp *.gif")]
        )
        
        if not filepath:
            return
        
        try:
            self.bt.putFile(filepath)
            self.status_var.set(f"Uploaded {filepath}")
            self.list_pictures()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to upload picture: {e}")
    
    def display_picture(self):
        """Display a selected picture"""
        if not self.bt:
            messagebox.showerror("Error", "Not connected to device")
            return
        
        selection = self.picture_list.curselection()
        if not selection:
            messagebox.showerror("Error", "No picture selected")
            return
        
        try:
            filename = self.picture_list.get(selection[0]).split()[0]
            self.bt.setShowingPicture(filename)
            self.status_var.set(f"Displaying {filename}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to display picture: {e}")
    
    def delete_picture(self):
        """Delete a selected picture"""
        if not self.bt:
            messagebox.showerror("Error", "Not connected to device")
            return
        
        selection = self.picture_list.curselection()
        if not selection:
            messagebox.showerror("Error", "No picture selected")
            return
        
        try:
            filename = self.picture_list.get(selection[0]).split()[0]
            self.bt.deleteFile(filename)
            self.status_var.set(f"Deleted {filename}")
            self.list_pictures()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete picture: {e}")

if __name__ == "__main__":
    root = ttk.Window(themename="superhero")
    app = BusyTagGUI(root)
    root.mainloop()

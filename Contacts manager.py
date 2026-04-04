"""
contacts_manager.py — Add / Edit / Delete contacts for Jarvis
Run:  python contacts_manager.py
"""
import json, os, re
import tkinter as tk
import customtkinter as ctk
from tkinter import messagebox

CONTACTS_FILE = "contacts.json"

def load(): 
    if os.path.exists(CONTACTS_FILE):
        try:
            with open(CONTACTS_FILE,encoding="utf-8") as f: return json.load(f)
        except: pass
    return {}

def save(c):
    with open(CONTACTS_FILE,"w",encoding="utf-8") as f:
        json.dump(c,f,indent=2,ensure_ascii=False)

class App:
    def __init__(self):
        self.contacts = load()
        ctk.set_appearance_mode("dark")
        self.win = ctk.CTk()
        self.win.title("Jarvis — Contacts Manager")
        self.win.geometry("580x640")
        self.win.resizable(False,False)

        ctk.CTkLabel(self.win,text="📱  J.A.R.V.I.S  Contacts",
                     font=ctk.CTkFont("Arial",22,"bold"),text_color="#00D4FF").pack(pady=(18,2))
        ctk.CTkLabel(self.win,text="Say  'call [name]'  or  'message [name] saying [text]'",
                     font=ctk.CTkFont("Arial",12),text_color="#445566").pack(pady=(0,14))

        # Form
        form = ctk.CTkFrame(self.win,fg_color="#0d0d1a",corner_radius=10)
        form.pack(fill="x",padx=20,pady=(0,10))

        def row(label, var, placeholder):
            f = ctk.CTkFrame(form,fg_color="transparent"); f.pack(fill="x",padx=14,pady=5)
            ctk.CTkLabel(f,text=label,font=ctk.CTkFont("Arial",13),
                         text_color="#aabbcc",width=180,anchor="w").pack(side="left")
            ctk.CTkEntry(f,textvariable=var,width=280,
                         placeholder_text=placeholder).pack(side="left",padx=6)

        self.name_var  = tk.StringVar()
        self.phone_var = tk.StringVar()
        row("Name (as you say it):", self.name_var,  "e.g.  mom  /  john  /  office")
        row("Phone (with +countrycode):", self.phone_var, "e.g.  +919876543210")

        btns = ctk.CTkFrame(form,fg_color="transparent"); btns.pack(pady=(4,14))
        ctk.CTkButton(btns,text="➕  Add / Update",width=160,height=36,
                      fg_color="#004488",hover_color="#0066cc",
                      font=ctk.CTkFont("Arial",13,"bold"),
                      command=self._add).pack(side="left",padx=8)
        ctk.CTkButton(btns,text="🗑  Delete",width=130,height=36,
                      fg_color="#440011",hover_color="#880022",
                      font=ctk.CTkFont("Arial",13,"bold"),
                      command=self._delete).pack(side="left",padx=8)

        ctk.CTkLabel(self.win,text="Your Contacts",
                     font=ctk.CTkFont("Arial",14,"bold"),
                     text_color="#00D4FF",anchor="w").pack(fill="x",padx=22)

        lf = ctk.CTkFrame(self.win,fg_color="#080812",corner_radius=8)
        lf.pack(fill="both",expand=True,padx=20,pady=(4,10))
        sb = tk.Scrollbar(lf); sb.pack(side="right",fill="y")
        self.lb = tk.Listbox(lf,yscrollcommand=sb.set,bg="#080812",fg="#cce4ff",
                             selectbackground="#004488",font=("Consolas",13),
                             borderwidth=0,highlightthickness=0,activestyle="none")
        self.lb.pack(fill="both",expand=True,padx=6,pady=6)
        sb.config(command=self.lb.yview)
        self.lb.bind("<<ListboxSelect>>",self._select)

        ctk.CTkLabel(self.win,
                     text="💡 Use short names — 'mom', 'dad', 'john' — so Jarvis understands you easily",
                     font=ctk.CTkFont("Arial",10),text_color="#334455").pack(pady=6)
        self._refresh()
        self.win.mainloop()

    def _refresh(self):
        self.lb.delete(0,tk.END)
        for n,p in sorted(self.contacts.items()):
            self.lb.insert(tk.END, f"  {n:<22}{p}")

    def _select(self,_=None):
        sel = self.lb.curselection()
        if not sel: return
        parts = self.lb.get(sel[0]).split()
        if parts:
            self.name_var.set(parts[0]); self.phone_var.set(parts[-1])

    def _add(self):
        name  = self.name_var.get().strip().lower()
        phone = re.sub(r'[\s\-\(\)]','',self.phone_var.get().strip())
        if not name:  messagebox.showwarning("Missing","Enter a name."); return
        if not phone: messagebox.showwarning("Missing","Enter a phone number."); return
        if not re.match(r'^\+?\d{7,15}$',phone):
            messagebox.showwarning("Bad number",
                "Must be digits only (7-15), optionally starting with +\n"
                "Example: +919876543210"); return
        self.contacts[name]=phone; save(self.contacts)
        self._refresh(); self.name_var.set(""); self.phone_var.set("")

    def _delete(self):
        sel = self.lb.curselection()
        if not sel: messagebox.showinfo("Select","Click a contact first."); return
        name = self.lb.get(sel[0]).split()[0]
        if messagebox.askyesno("Delete",f"Delete '{name}'?"):
            self.contacts.pop(name,None); save(self.contacts)
            self._refresh(); self.name_var.set(""); self.phone_var.set("")

if __name__ == "__main__": App()
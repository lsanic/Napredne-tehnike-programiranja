#!/usr/bin/env python3
import threading
from typing import Dict, List, Tuple
import tkinter as tk
from tkinter import ttk, messagebox
import time
import os

from grader_project import ExamGrader, load_students_from_folder

class GraderGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Ocjenjivač Ispita")
        self.root.geometry("800x600")
        self.root.configure(bg="#f0f0f0")
        
        # Referentni ispit prema kojem grader ocjenjuje ispite studenata:
        self.REFERENCE_KEY: Dict[int, str] = {
            1: 'A', 2: 'B', 3: 'C', 4: 'A', 5: 'D',
            6: 'B', 7: 'C', 8: 'A', 9: 'B', 10: 'C',
            11: 'A', 12: 'B', 13: 'C', 14: 'A', 15: 'D',
            16: 'B', 17: 'D', 18: 'A', 19: 'B', 20: 'C',
            21: 'A', 22: 'B', 23: 'C', 24: 'A', 25: 'D',
            26: 'B', 27: 'C', 28: 'A', 29: 'B', 30: 'C'
        }
        
        self.results: List[Tuple[str, str, int, int, int]] = []
        
        self.setup_ui()
    
    def setup_ui(self):
        """Postavlja UI elemente"""
      
        header_frame = tk.Frame(self.root, bg="#2c3e50", height=80)
        header_frame.pack(fill=tk.X, pady=0)
        header_frame.pack_propagate(False)
        
        title_label = tk.Label(
            header_frame,
            text="Ocjenjivač Ispita",
            font=("Helvetica", 24, "bold"),
            bg="#2c3e50",
            fg="white"
        )
        title_label.pack(pady=20)
        content_frame = tk.Frame(self.root, bg="#f0f0f0")
        content_frame.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)
        
        button_frame = tk.Frame(content_frame, bg="#f0f0f0")
        button_frame.pack(pady=20)
        
        self.start_button = tk.Button(
            button_frame,
            text="Počni s ocjenjivanjem",
            command=self.start_grading,
            font=("Helvetica", 14, "bold"),
            bg="#27ae60",
            fg="white",
            padx=20,
            pady=10,
            cursor="hand2",
            relief=tk.RAISED,
            bd=2
        )
        self.start_button.pack()
    
        self.status_label = tk.Label(
            content_frame,
            text="Kliknite na gumb za početak",
            font=("Helvetica", 12),
            bg="#f0f0f0",
            fg="#555"
        )
        self.status_label.pack(pady=10)
        
        self.progress_label = tk.Label(
            content_frame,
            text="",
            font=("Helvetica", 11),
            bg="#f0f0f0",
            fg="#2c3e50"
        )
        self.progress_label.pack(pady=5)
        
        self.table_frame = tk.Frame(content_frame, bg="#f0f0f0")
        self.table_frame.pack(fill=tk.BOTH, expand=True, padx=0, pady=10)
       
        self.canvas = tk.Canvas(self.table_frame, bg="white", highlightthickness=1, highlightbackground="#bdc3c7")
        self.scrollbar = ttk.Scrollbar(self.table_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg="white")
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.scrollable_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.bind(
            "<Configure>",
            lambda e: self.canvas.itemconfigure(self.scrollable_window, width=e.width)
        )
 
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.scrollable_frame.bind("<MouseWheel>", self._on_mousewheel)
        
        self.animation_chars = ['|', '/', '-', '\\']
        self.animation_index = 0
    
    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    
    def start_grading(self):
        self.start_button.config(state="disabled")
        self.results = []
        
        grading_thread = threading.Thread(target=self.grade_all_exams, daemon=True)
        grading_thread.start()
    
    def update_progress(self, count: int, total: int):
        self.animation_index = (self.animation_index + 1) % len(self.animation_chars)
        char = self.animation_chars[self.animation_index]
        
        self.status_label.config(
            text=f"Ocjenjivanje u tijeku... {char}",
            fg="#e74c3c"
        )
        self.progress_label.config(
            text=f"Trenutno je u tijeku obrada ispita",
            fg="#3498db"
        )
        self.root.update()
        time.sleep(0.3)
    
    def format_student_name(self, filename: str) -> str:
        name = filename.replace('.json', '')
        if len(name) > 1:
            last_upper = 0
            for i in range(len(name) - 1, 0, -1):
                if name[i].isupper():
                    last_upper = i
                    break
            if last_upper > 0:
                first_part = name[:last_upper]
                last_part = name[last_upper:]
                return f"{first_part} {last_part}"
        return name
    
    def grade_all_exams(self):
        snap_path = os.environ.get('SNAP', '.')
        exams_folder = os.path.join(snap_path, "studenti")
        
        students_exams = load_students_from_folder(exams_folder)

        if not students_exams:
            messagebox.showerror("Greška", f"Nema JSON fajlova u mapi '{exams_folder}'")
            self.start_button.config(state="normal")
            return

        grader = ExamGrader(self.REFERENCE_KEY)
        graded_results = grader.grade_all_students(students_exams)

        self.results = []
        for idx, result in enumerate(graded_results):
            self.update_progress(idx + 1, len(graded_results))
            student_name = result.student_name
            formatted_name = self.format_student_name(f"{student_name}.json")
            self.results.append(
                (
                    student_name,
                    formatted_name,
                    result.correct_answers,
                    result.grade,
                    result.total_questions,
                )
            )

        self.results.sort(key=lambda x: x[0])
        self.show_results()
    
    def show_results(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        header_frame = tk.Frame(self.scrollable_frame, bg="#34495e")
        header_frame.pack(fill=tk.X, pady=5)
        
        lbl1 = tk.Label(header_frame, text="Student", font=("Helvetica", 12, "bold"), bg="#34495e", fg="white", width=25, anchor="w")
        lbl1.pack(side=tk.LEFT, padx=10, pady=5)
        
        lbl2 = tk.Label(header_frame, text="Točni odgovori", font=("Helvetica", 12, "bold"), bg="#34495e", fg="white", width=15, anchor="center")
        lbl2.pack(side=tk.LEFT, padx=10, pady=5)
        
        lbl3 = tk.Label(header_frame, text="Ocjena", font=("Helvetica", 12, "bold"), bg="#34495e", fg="white", width=10, anchor="center")
        lbl3.pack(side=tk.LEFT, padx=10, pady=5)

        for name, formatted_name, correct, grade, total in self.results:
            row = tk.Frame(self.scrollable_frame, bg="white")
            row.pack(fill=tk.X, padx=5, pady=2)
            
            row.bind("<Enter>", lambda e, r=row: r.config(bg="#f8f9fa"))
            row.bind("<Leave>", lambda e, r=row: r.config(bg="white"))
            
            lbl_n = tk.Label(row, text=formatted_name, font=("Helvetica", 11), bg="white", fg="#2c3e50", width=25, anchor="w")
            lbl_n.pack(side=tk.LEFT, padx=10, pady=5)
            
            lbl_c = tk.Label(row, text=f"{correct} / {total}", font=("Helvetica", 11), bg="white", fg="#27ae60" if correct > total/2 else "#e74c3c", width=15, anchor="center")
            lbl_c.pack(side=tk.LEFT, padx=10, pady=5)
            
            lbl_g = tk.Label(row, text=str(grade), font=("Helvetica", 11, "bold"), bg="white", fg="#2980b9", width=10, anchor="center")
            lbl_g.pack(side=tk.LEFT, padx=10, pady=5)
            
            line = tk.Frame(self.scrollable_frame, bg="#e2e8f0", height=1)
            line.pack(fill=tk.X, padx=5)

        self.status_label.config(text="Ocjenjivanje završeno!", fg="#27ae60")
        self.progress_label.config(text=f"Uspješno obrađeno {len(self.results)} ispita.", fg="#2c3e50")
        self.start_button.config(state="normal")

if __name__ == "__main__":
    root = tk.Tk()
    app = GraderGUI(root)
    root.mainloop()
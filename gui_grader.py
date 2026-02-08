import threading
from typing import Dict, List, Tuple
import tkinter as tk
from tkinter import ttk, messagebox
import time

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
        exams_folder = "studenti"
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
        header_frame.pack(fill=tk.X, padx=0, pady=5)

        header_frame.grid_columnconfigure(0, weight=1, uniform="cols")
        header_frame.grid_columnconfigure(1, weight=1, uniform="cols")
        header_frame.grid_columnconfigure(2, weight=1, uniform="cols")
        
        columns = [
            ("Ime i Prezime", 300),
            ("Točni Odgovori", 150),
            ("Ocjena", 120),
          
        ]
        
        for col_name, width in columns:
            col_label = tk.Label(
                header_frame,
                text=col_name,
                font=("Helvetica", 12, "bold"),
                bg="#34495e",
                fg="white",
                anchor="center",
                padx=10,
                pady=10
            )
            col_index = columns.index((col_name, width))
            col_label.grid(row=0, column=col_index, sticky="ew")
        
     
        for idx, (_, student_name, points, grade, total) in enumerate(self.results):
            row_frame = tk.Frame(
                self.scrollable_frame,
                bg="white" if idx % 2 == 0 else "#ecf0f1"
            )
            row_frame.pack(fill=tk.X, padx=0, pady=2)

            row_frame.grid_columnconfigure(0, weight=1, uniform="cols")
            row_frame.grid_columnconfigure(1, weight=1, uniform="cols")
            row_frame.grid_columnconfigure(2, weight=1, uniform="cols")
            
            name_label = tk.Label(
                row_frame,
                text=student_name,
                font=("Helvetica", 10),
                bg=row_frame["bg"],
                anchor="w",
                padx=10,
                pady=8
            )
            name_label.grid(row=0, column=0, sticky="ew")
            
            points_label = tk.Label(
                row_frame,
                text=f"{points}/{total}",
                font=("Helvetica", 10, "bold"),
                bg=row_frame["bg"],
                fg="#2980b9",
                anchor="center",
                padx=10,
                pady=8
            )
            points_label.grid(row=0, column=1, sticky="ew")
            
            grade_colors = {
                1: "#e74c3c",  
                2: "#f39c12",  
                3: "#f1c40f",  
                4: "#27ae60",
                5: "#16a085"   
            }
            
            grade_label = tk.Label(
                row_frame,
                text=str(grade),
                font=("Helvetica", 11, "bold"),
                bg=row_frame["bg"],
                fg=grade_colors.get(grade, "black"),
                anchor="center",
                padx=10,
                pady=8
            )
            grade_label.grid(row=0, column=2, sticky="ew")

        total_students = len(self.results)
        passed_count = sum(1 for _, _, _, grade, _ in self.results if grade >= 2)
        pass_rate = (passed_count / total_students * 100) if total_students else 0

        summary_frame = tk.Frame(self.scrollable_frame, bg="#dfe6e9")
        summary_frame.pack(fill=tk.X, padx=0, pady=(10, 5))

        summary_frame.grid_columnconfigure(0, weight=1, uniform="cols")
        summary_frame.grid_columnconfigure(1, weight=1, uniform="cols")
        summary_frame.grid_columnconfigure(2, weight=1, uniform="cols")

        summary_label = tk.Label(
            summary_frame,
            text="Prolaznost:",
            font=("Helvetica", 11, "bold"),
            bg="#dfe6e9",
            fg="#2c3e50",
            anchor="w",
            padx=10,
            pady=8
        )
        summary_label.grid(row=0, column=0, columnspan=2, sticky="ew")

        summary_value = tk.Label(
            summary_frame,
            text=f"{pass_rate:.1f}% ({passed_count}/{total_students})",
            font=("Helvetica", 11, "bold"),
            bg="#dfe6e9",
            fg="#27ae60" if pass_rate >= 50 else "#e74c3c",
            anchor="center",
            padx=10,
            pady=8
        )
        summary_value.grid(row=0, column=2, sticky="ew")
        
        self.status_label.config(
            text=f"Ocjenjivanje je gotovo!",
            fg="#27ae60"
        )
        self.progress_label.config(text="")
        self.start_button.config(state="normal")

def main():
    root = tk.Tk()
    app = GraderGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()

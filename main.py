import customtkinter as ctk
import json
import random
import os
from datetime import datetime
from tkinter import messagebox

# Konfigurasi Tema & Warna
ctk.set_appearance_mode("light")
COLORS = {
    "primary": "#4F46E5",
    "bg_light": "#F0F4FF",
    "success": "#22C55E",
    "error": "#EF4444",
    "card": "#FFFFFF",
    "neutral": "#94A3B8"
}

class QuizApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Quiz App")
        self.geometry("480x750")
        self.configure(fg_color=COLORS["bg_light"])

        # State Management
        self.db = self.load_questions()
        self.current_q_idx = 0
        self.score = 0
        self.user_answers = [] 
        self.timer_id = None
        self.radio_buttons = [] 

        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.pack(fill="both", expand=True, padx=30, pady=30)

        self.show_home()

    def load_questions(self):
        if not os.path.exists('questions.json'):
            return {"Error": {"Easy": [{"q": "File questions.json tidak ditemukan!", "options": ["Ok"], "a": 0, "exp": ""}]}}
        with open('questions.json', 'r') as f:
            return json.load(f)

    # Simpan hasil quiz ke history.json
    def save_to_history(self):
        history_file = 'history.json'
        new_record = {
            "category": self.current_category,
            "difficulty": self.difficulty,
            "score": self.score,
            "total": len(self.questions),
            "date": datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        
        data = []
        if os.path.exists(history_file):
            with open(history_file, 'r') as f:
                try: data = json.load(f)
                except: data = []
        
        data.append(new_record)
        with open(history_file, 'w') as f:
            json.dump(data, f, indent=2)

    def clear_screen(self):
        self.stop_timer()
        for widget in self.container.winfo_children():
            widget.destroy()

    def show_home(self):
        self.clear_screen()
        ctk.CTkLabel(self.container, text="QUIZ MASTER", font=("Helvetica", 28, "bold"), text_color="#1E293B").pack(pady=(20, 5))
        ctk.CTkLabel(self.container, text="Test Your Knowledge", font=("Helvetica", 14), text_color="#64748B").pack(pady=(0, 30))

        start_card = ctk.CTkFrame(self.container, fg_color=COLORS["card"], corner_radius=20)
        start_card.pack(fill="x", pady=10)
        
        ctk.CTkButton(start_card, text="Mulai Kuis Baru", fg_color=COLORS["primary"], height=50, 
                      corner_radius=12, font=("Helvetica", 16, "bold"), command=self.show_setup).pack(padx=20, pady=20, fill="x")

    def show_setup(self):
        self.clear_screen()
        ctk.CTkLabel(self.container, text="Pengaturan Kuis", font=("Helvetica", 22, "bold")).pack(pady=20)

        ctk.CTkLabel(self.container, text="Pilih Kategori:", font=("Helvetica", 14)).pack(anchor="w", pady=5)
        self.cat_var = ctk.StringVar(value=list(self.db.keys())[0])
        ctk.CTkOptionMenu(self.container, values=list(self.db.keys()), variable=self.cat_var, fg_color=COLORS["primary"]).pack(fill="x", pady=10)

        ctk.CTkLabel(self.container, text="Tingkat Kesulitan:", font=("Helvetica", 14)).pack(anchor="w", pady=5)
        self.diff_var = ctk.StringVar(value="Easy")
        ctk.CTkSegmentedButton(self.container, values=["Easy", "Medium", "Hard"], variable=self.diff_var, selected_color=COLORS["primary"]).pack(fill="x", pady=10)

        ctk.CTkButton(self.container, text="MULAI", command=self.start_quiz_engine, height=50, fg_color=COLORS["primary"]).pack(side="bottom", fill="x", pady=20)

    def start_quiz_engine(self):
        self.current_category = self.cat_var.get()
        self.difficulty = self.diff_var.get()
        all_q = self.db.get(self.current_category, {}).get(self.difficulty, [])
        
        if not all_q:
            messagebox.showwarning("Info", "Soal belum tersedia.")
            return

        num_to_pick = min(len(all_q), 5)
        self.questions = random.sample(all_q, num_to_pick)
        self.current_q_idx = 0
        self.score = 0
        self.user_answers = []
        self.show_quiz_page()

    def show_quiz_page(self):
        self.clear_screen()
        q_data = self.questions[self.current_q_idx]
        
        times = {"Easy": 30, "Medium": 20, "Hard": 10}
        self.time_left = times[self.difficulty]

        header = ctk.CTkFrame(self.container, fg_color="transparent")
        header.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(header, text=f"Soal {self.current_q_idx + 1} / {len(self.questions)}", font=("Helvetica", 12)).pack(side="left")
        self.timer_label = ctk.CTkLabel(header, text=f"⏱ 00:{self.time_left:02d}", font=("Helvetica", 12, "bold"), text_color=COLORS["error"])
        self.timer_label.pack(side="right")

        self.progress = ctk.CTkProgressBar(self.container, progress_color=COLORS["primary"])
        self.progress.set((self.current_q_idx + 1) / len(self.questions))
        self.progress.pack(fill="x", pady=10)

        ctk.CTkLabel(self.container, text=q_data["q"], font=("Helvetica", 18, "bold"), wraplength=400, justify="left").pack(pady=20, anchor="w")

        self.ans_var = ctk.StringVar(value="")
        self.radio_buttons = []
        for opt in q_data["options"]:
            btn = ctk.CTkRadioButton(self.container, text=opt, variable=self.ans_var, value=opt,
                                     font=("Helvetica", 14), border_width_checked=6, fg_color=COLORS["primary"])
            btn.pack(fill="x", pady=8, padx=10)
            self.radio_buttons.append(btn)

        self.start_timer()
        
        self.confirm_btn = ctk.CTkButton(self.container, text="Konfirmasi", command=self.handle_answer, height=50, fg_color=COLORS["primary"])
        self.confirm_btn.pack(side="bottom", fill="x", pady=20)

    def handle_answer(self, timeout=False):
        chosen = self.ans_var.get()
        
        # Validasi sebelum submit
        if not chosen and not timeout:
            messagebox.showinfo("Peringatan", "Silakan pilih salah satu jawaban terlebih dahulu!")
            return

        self.stop_timer()
        q_data = self.questions[self.current_q_idx]
        correct_idx = q_data["a"]
        correct_val = q_data["options"][correct_idx]

        # Feedback visual jawaban 
        for rb in self.radio_buttons:
            rb.configure(state="disabled")
            # Jika teks tombol adalah jawaban benar -> Hijau
            if rb.cget("text") == correct_val:
                rb.configure(text_color=COLORS["success"], font=("Helvetica", 14, "bold"))
            # Jika teks tombol dipilih user tapi salah -> Merah
            if rb.cget("text") == chosen and chosen != correct_val:
                rb.configure(text_color=COLORS["error"], font=("Helvetica", 14, "bold"))

        self.confirm_btn.configure(state="disabled")

        is_correct = chosen == correct_val
        if is_correct: self.score += 1

        self.user_answers.append({
            "q": q_data["q"],
            "user": chosen if not timeout else "Waktu Habis",
            "correct": correct_val,
            "is_correct": is_correct,
            "exp": q_data["exp"]
        })

        # Jeda 1.5 detik agar user bisa melihat feedback visual
        self.after(1500, self.move_to_next)

    def move_to_next(self):
        self.current_q_idx += 1
        if self.current_q_idx < len(self.questions):
            self.show_quiz_page()
        else:
            self.save_to_history()
            self.show_results()

    def show_results(self):
        self.clear_screen()
        percent = (self.score / len(self.questions)) * 100
        grade = "LULUS" if percent >= 60 else "GAGAL"
        res_color = COLORS["success"] if grade == "LULUS" else COLORS["error"]

        ctk.CTkLabel(self.container, text=f"{int(percent)}%", font=("Helvetica", 60, "bold"), text_color=res_color).pack(pady=(40, 10))
        ctk.CTkLabel(self.container, text=f"Status: {grade}", font=("Helvetica", 20, "bold")).pack()

        stats_frame = ctk.CTkFrame(self.container, fg_color="white", corner_radius=15)
        stats_frame.pack(fill="x", pady=30, padx=10)

        row1 = ctk.CTkFrame(stats_frame, fg_color="transparent")
        row1.pack(fill="x", padx=20, pady=10)
        ctk.CTkLabel(row1, text="Total Soal:").pack(side="left")
        ctk.CTkLabel(row1, text=str(len(self.questions)), font=("bold", 14)).pack(side="right")

        row2 = ctk.CTkFrame(stats_frame, fg_color="transparent")
        row2.pack(fill="x", padx=20, pady=10)
        ctk.CTkLabel(row2, text="Jawaban Benar:").pack(side="left")
        ctk.CTkLabel(row2, text=str(self.score), text_color=COLORS["success"], font=("bold", 14)).pack(side="right")

        ctk.CTkButton(self.container, text="Tinjau Jawaban", command=self.show_review, fg_color="#6366F1").pack(fill="x", pady=5)
        ctk.CTkButton(self.container, text="Kembali ke Menu", command=self.show_home, fg_color="transparent", text_color="black", border_width=1).pack(fill="x", pady=5)

    def show_review(self):
        self.clear_screen()
        ctk.CTkLabel(self.container, text="Review Jawaban", font=("Helvetica", 18, "bold")).pack(pady=10)
        scroll = ctk.CTkScrollableFrame(self.container, width=400, height=450, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        for item in self.user_answers:
            color = COLORS["success"] if item["is_correct"] else COLORS["error"]
            box = ctk.CTkFrame(scroll, border_width=1, border_color=color, fg_color="white", corner_radius=10)
            box.pack(fill="x", pady=5, padx=5)
            ctk.CTkLabel(box, text=item["q"], font=("bold", 12), wraplength=350, justify="left").pack(padx=10, pady=5)
            ctk.CTkLabel(box, text=f"Jawaban Anda: {item['user']}", text_color=color).pack(anchor="w", padx=10)
            if not item["is_correct"]:
                ctk.CTkLabel(box, text=f"Benar: {item['correct']}", text_color=COLORS["success"]).pack(anchor="w", padx=10)
            ctk.CTkLabel(box, text=f"💡 {item['exp']}", font=("italic", 11), text_color="grey", wraplength=350).pack(padx=10, pady=5)

        ctk.CTkButton(self.container, text="Kembali ke Home", command=self.show_home).pack(fill="x", pady=20)

    def start_timer(self):
        self.stop_timer()
        self.tick()

    def stop_timer(self):
        if self.timer_id:
            self.after_cancel(self.timer_id)
            self.timer_id = None

    def tick(self):
        if self.time_left > 0:
            self.time_left -= 1
            self.timer_label.configure(text=f"⏱ 00:{self.time_left:02d}")
            self.timer_id = self.after(1000, self.tick)
        else:
            self.handle_answer(timeout=True)

if __name__ == "__main__":
    app = QuizApp()
    app.mainloop()
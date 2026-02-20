"""
고객 리뷰 분석 GUI.
엑셀 파일 선택 → 열 매핑(자동/수동) → ChatGPT로 분석 보고서 생성 → 표시/저장.
"""
from __future__ import annotations

import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from dotenv import load_dotenv

from config import COLUMN_CANDIDATES
from excel_loader import load_excel, resolve_columns
from report_generator import generate_report

load_dotenv()

ROLE_LABELS = {
    "review": "리뷰 내용",
    "rating": "평점",
    "product": "제품/모델",
    "customer_id": "고객 ID",
    "name": "이름",
    "age": "연령/연령대",
    "purchase_date": "구매일자",
    "gender": "성별",
}


class ReviewAnalyzerApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("고객 리뷰 분석")
        self.root.geometry("900x700")
        self.root.minsize(700, 500)

        self.df: object = None  # pandas DataFrame
        self.mapping: dict[str, str | None] = {}
        self.column_combos: dict[str, ttk.Combobox] = {}
        self.file_path_var = tk.StringVar(value="")

        self._build_ui()

    def _build_ui(self):
        # 상단: 파일 선택
        top = ttk.Frame(self.root, padding=8)
        top.pack(fill=tk.X)
        ttk.Button(top, text="엑셀 파일 선택", command=self._on_select_file).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Label(top, textvariable=self.file_path_var, foreground="gray").pack(side=tk.LEFT, fill=tk.X, expand=True)

        # 매핑 영역
        map_frame = ttk.LabelFrame(self.root, text="열 매핑 (리뷰 내용은 필수)", padding=8)
        map_frame.pack(fill=tk.X, padx=8, pady=4)

        self.map_inner = ttk.Frame(map_frame)
        self.map_inner.pack(fill=tk.X)
        ttk.Label(self.map_inner, text="파일을 선택하면 자동 매핑됩니다. 누락된 항목은 아래에서 선택하세요.", foreground="gray").pack(anchor=tk.W)

        # 분석 실행 / 저장 / 상태
        btn_frame = ttk.Frame(self.root, padding=8)
        btn_frame.pack(fill=tk.X)
        self.analyze_btn = ttk.Button(btn_frame, text="분석 보고서 생성", command=self._on_analyze, state=tk.DISABLED)
        self.analyze_btn.pack(side=tk.LEFT, padx=(0, 8))
        self.save_btn = ttk.Button(btn_frame, text="보고서 저장", command=self._on_save, state=tk.DISABLED)
        self.save_btn.pack(side=tk.LEFT, padx=(0, 12))
        self.status_var = tk.StringVar(value="")
        self.status_label = ttk.Label(btn_frame, textvariable=self.status_var, foreground="gray")
        self.status_label.pack(side=tk.LEFT)

        # 보고서 표시
        report_frame = ttk.LabelFrame(self.root, text="분석 보고서", padding=4)
        report_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)
        self.report_text = tk.Text(report_frame, wrap=tk.WORD, font=("Malgun Gothic", 10), state=tk.DISABLED)
        scroll = ttk.Scrollbar(report_frame, orient=tk.VERTICAL, command=self.report_text.yview)
        self.report_text.configure(yscrollcommand=scroll.set)
        self.report_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self._current_report = ""

    def _on_select_file(self):
        path = filedialog.askopenfilename(
            title="엑셀 파일 선택",
            filetypes=[("Excel 파일", "*.xlsx"), ("모든 파일", "*.*")],
        )
        if not path:
            return
        try:
            self.df = load_excel(path)
            self.mapping = resolve_columns(self.df)
            self.file_path_var.set(path)
            self._refresh_mapping_ui()
            self.analyze_btn.config(state=tk.NORMAL)
        except Exception as e:
            messagebox.showerror("로드 오류", str(e))
            self.df = None
            self.mapping = {}
            self.analyze_btn.config(state=tk.DISABLED)

    def _refresh_mapping_ui(self):
        for w in self.map_inner.winfo_children():
            w.destroy()
        self.column_combos.clear()

        ttk.Label(self.map_inner, text="파일을 선택하면 자동 매핑됩니다. 누락된 항목은 아래에서 선택하세요.", foreground="gray").pack(anchor=tk.W)

        if self.df is None:
            return
        columns = list(self.df.columns)
        if not columns:
            return

        for role in COLUMN_CANDIDATES:
            row = ttk.Frame(self.map_inner)
            row.pack(fill=tk.X, pady=2)
            label = ROLE_LABELS.get(role, role)
            required = " (필수)" if role == "review" else ""
            ttk.Label(row, text=f"{label}{required}:", width=14, anchor=tk.W).pack(side=tk.LEFT, padx=(0, 4))
            current = self.mapping.get(role)
            combo = ttk.Combobox(row, values=columns, state="readonly", width=40)
            if current and current in columns:
                combo.set(current)
            else:
                combo.set("(선택 안 함)" if role != "review" else "")
            combo.pack(side=tk.LEFT, fill=tk.X, expand=True)
            self.column_combos[role] = combo

    def _get_current_mapping(self) -> dict[str, str | None]:
        """UI에서 선택된 값을 반영한 매핑 반환."""
        out = dict(self.mapping)
        if not self.column_combos:
            return out
        for role, combo in self.column_combos.items():
            val = combo.get()
            if val and val != "(선택 안 함)" and val in (self.df.columns if self.df is not None else []):
                out[role] = val
            else:
                out[role] = self.mapping.get(role)
        return out

    def _on_analyze(self):
        if self.df is None:
            messagebox.showwarning("경고", "먼저 엑셀 파일을 선택하세요.")
            return
        mapping = self._get_current_mapping()
        if not mapping.get("review"):
            messagebox.showwarning("경고", "리뷰 내용에 해당하는 열을 반드시 선택하세요.")
            return
        if not os.getenv("OPENAI_API_KEY", "").strip():
            messagebox.showwarning("API 키 없음", ".env 파일에 OPENAI_API_KEY를 설정한 뒤 다시 시도하세요.")
            return

        self.analyze_btn.config(state=tk.DISABLED, text="생성 중...")
        self.status_var.set("분석 보고서 생성 중... 잠시만 기다려 주세요.")
        self.status_label.config(foreground="gray")
        self.save_btn.config(state=tk.DISABLED)
        self.root.update_idletasks()
        self.root.update()
        try:
            report, err = generate_report(self.df, mapping)
            if err:
                messagebox.showerror("보고서 생성 오류", err)
                self._current_report = ""
            else:
                self._current_report = report
                self.report_text.config(state=tk.NORMAL)
                self.report_text.delete("1.0", tk.END)
                self.report_text.insert(tk.END, report)
                self.report_text.config(state=tk.DISABLED)
                self.save_btn.config(state=tk.NORMAL)
                self.status_var.set("생성 완료.")
            self.status_label.config(foreground="green" if not err else "gray")
        except Exception as e:
            messagebox.showerror("오류", str(e))
            self._current_report = ""
            self.status_var.set("")
            self.status_label.config(foreground="gray")
        finally:
            self.analyze_btn.config(state=tk.NORMAL, text="분석 보고서 생성")
            if not self.status_var.get().startswith("생성 완료"):
                self.status_var.set("")

    def _on_save(self):
        if not self._current_report:
            messagebox.showinfo("저장", "저장할 보고서가 없습니다.")
            return
        path = filedialog.asksaveasfilename(
            title="보고서 저장",
            defaultextension=".md",
            filetypes=[("마크다운 파일", "*.md"), ("텍스트 파일", "*.txt"), ("모든 파일", "*.*")],
        )
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self._current_report)
            messagebox.showinfo("저장 완료", f"저장했습니다: {path}")
        except Exception as e:
            messagebox.showerror("저장 오류", str(e))

    def run(self):
        self.root.mainloop()


def main():
    app = ReviewAnalyzerApp()
    app.run()


if __name__ == "__main__":
    main()

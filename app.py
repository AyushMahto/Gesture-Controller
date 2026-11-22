import csv
import queue
import threading
import time
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path

from config import Settings, COMMANDS
from core.command_controller import CommandController
from core.gesture_recognition import classify, GestureVoter
from core.performance_monitor import PerformanceMonitor

ROOT = Path(__file__).parent
HAND_CONNECTIONS = ((0,1),(1,2),(2,3),(3,4),(0,5),(5,6),(6,7),(7,8),(5,9),(9,10),(10,11),(11,12),(9,13),(13,14),(14,15),(15,16),(13,17),(17,18),(18,19),(19,20),(0,17))


class HandWaveApp:
    def __init__(self, root):
        self.root, self.settings = root, Settings()
        self.monitor, self.controller = PerformanceMonitor(), CommandController()
        self.frames = queue.Queue(maxsize=1)
        self.stop_event, self.worker = threading.Event(), None
        self.current_gesture, self.current_action = "No hand", "Idle"
        self.stability, self.fingers = 0.0, 0
        self.commands = 0
        self.command_counts = {}
        self._style()
        root.title("HandWave | Gesture Interface")
        root.geometry("1120x760")
        root.minsize(900, 620)
        header = ttk.Frame(root, padding=(22, 16)); header.pack(fill="x")
        ttk.Label(header, text="HandWave", style="Title.TLabel").pack(side="left")
        ttk.Label(header, text="GESTURE CONTROL", style="Muted.TLabel").pack(side="left", padx=14, pady=(7, 0))
        self.status = ttk.Label(header, text="● Preview ready", style="Status.TLabel"); self.status.pack(side="right")
        self.tabs = ttk.Notebook(root); self.tabs.pack(fill="both", expand=True, padx=18, pady=(0, 18))
        self.dashboard = ttk.Frame(self.tabs, padding=18); self.live = ttk.Frame(self.tabs, padding=18)
        self.performance = ttk.Frame(self.tabs, padding=18); self.evaluation = ttk.Frame(self.tabs, padding=18)
        self.settings_page = ttk.Frame(self.tabs, padding=18)
        for page, title in [(self.dashboard,"Dashboard"),(self.live,"Live recognition"),(self.performance,"Performance"),(self.evaluation,"Evaluation"),(self.settings_page,"Settings")]: self.tabs.add(page, text=title)
        self._dashboard(); self._live(); self._performance(); self._evaluation(); self._settings()
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self._refresh()

    def _style(self):
        s = ttk.Style(); s.theme_use("clam")
        s.configure(".", background="#f5f7f8", foreground="#202a32", font=("Segoe UI", 10))
        s.configure("TFrame", background="#f5f7f8"); s.configure("TLabel", background="#f5f7f8")
        s.configure("Title.TLabel", font=("Segoe UI", 22, "bold"), foreground="#18242d")
        s.configure("Muted.TLabel", foreground="#71808b"); s.configure("Status.TLabel", foreground="#28765c", font=("Segoe UI", 10, "bold"))
        s.configure("TButton", padding=(12, 8)); s.configure("Accent.TButton", background="#256b57", foreground="white")
        s.map("Accent.TButton", background=[("active", "#1d5947")]); s.configure("TNotebook", background="#f5f7f8", borderwidth=0)
        s.configure("TNotebook.Tab", padding=(16, 10), background="#e9edef"); s.map("TNotebook.Tab", background=[("selected", "#ffffff")])

    def _card(self, parent, title, value="—"):
        box = ttk.LabelFrame(parent, text=title, padding=14); label = ttk.Label(box, text=value, font=("Segoe UI", 18, "bold")); label.pack(anchor="w"); box.value_label = label
        return box

    def _dashboard(self):
        ttk.Label(self.dashboard, text="Session overview", font=("Segoe UI", 17, "bold")).pack(anchor="w", pady=(0, 14))
        grid = ttk.Frame(self.dashboard); grid.pack(fill="x")
        self.dash_values = {}
        for i, (name, val) in enumerate([("Application", "Preview"),("Webcam", "Stopped"),("Gesture", "No hand"),("Action", "Idle"),("FPS", "0.0"),("Latency", "0 ms"),("Detection rate", "0%"),("Session", "0:00"),("Commands", "0")]):
            card = self._card(grid, name, val); card.grid(row=i//3, column=i%3, sticky="ew", padx=5, pady=5); grid.columnconfigure(i%3, weight=1); self.dash_values[name] = card.value_label
        ttk.Label(self.dashboard, text="Gesture mapping", font=("Segoe UI", 14, "bold")).pack(anchor="w", pady=(20, 8))
        mapping = ttk.Frame(self.dashboard); mapping.pack(fill="x")
        for gesture, action in COMMANDS.items(): ttk.Label(mapping, text=f"{gesture}  →  {action}", padding=(12, 8), background="#ffffff").pack(side="left", padx=4, pady=4)

    def _live(self):
        row = ttk.Frame(self.live); row.pack(fill="x", pady=(0, 10))
        ttk.Button(row, text="Start camera", style="Accent.TButton", command=self.start).pack(side="left")
        ttk.Button(row, text="Stop", command=self.stop).pack(side="left", padx=8)
        ttk.Button(row, text="Enable computer actions…", command=self.enable_actions).pack(side="right")
        self.video = ttk.Label(self.live, text="Camera preview appears here", anchor="center", background="#e6ebed", foreground="#66747c")
        self.video.pack(fill="both", expand=True)
        info = ttk.Frame(self.live); info.pack(fill="x", pady=12)
        self.live_info = ttk.Label(info, text="Gesture: No hand    •    Fingers: 0    •    Stability: 0%    •    Action: Idle", font=("Segoe UI", 12)); self.live_info.pack(anchor="w")
        ttk.Label(self.live, text="Computer actions are off until explicitly enabled. Hold a gesture to trigger once; remove your hand to rearm.", style="Muted.TLabel").pack(anchor="w")

    def _performance(self):
        ttk.Label(self.performance, text="Live runtime metrics", font=("Segoe UI", 17, "bold")).pack(anchor="w", pady=(0, 14))
        self.perf_text = tk.Text(self.performance, height=7, state="disabled", relief="flat", background="white", font=("Consolas", 11)); self.perf_text.pack(fill="x")
        ttk.Label(self.performance, text="Recent measurements", font=("Segoe UI", 14, "bold")).pack(anchor="w", pady=(18, 8))
        self.chart = tk.Canvas(self.performance, height=300, background="white", highlightthickness=1, highlightbackground="#dce2e5"); self.chart.pack(fill="both", expand=True)
        self.distribution = tk.Canvas(self.performance, height=210, background="white", highlightthickness=1, highlightbackground="#dce2e5"); self.distribution.pack(fill="x", pady=(10, 0))
        self.history = []

    def _evaluation(self):
        ttk.Label(self.evaluation, text="Recognition quality evaluation", font=("Segoe UI", 17, "bold")).pack(anchor="w", pady=(0, 10))
        ttk.Label(self.evaluation, text="Use manually labelled samples. Runtime detection rate and stability are operational metrics; accuracy, precision, recall and F1 require independent ground-truth labels.", wraplength=850).pack(anchor="w", pady=(0, 14))
        row = ttk.Frame(self.evaluation); row.pack(anchor="w")
        ttk.Button(row, text="Evaluate labelled CSV", style="Accent.TButton", command=self.evaluate).pack(side="left")
        ttk.Button(row, text="Export observed gesture counts", command=self.export_counts).pack(side="left", padx=8)
        self.eval_output = tk.Text(self.evaluation, state="disabled", height=22, background="white", relief="flat", font=("Consolas", 10)); self.eval_output.pack(fill="both", expand=True, pady=14)
        ttk.Label(self.evaluation, text="Template: evaluation/test_samples.csv (headers only). Required columns: ground_truth,prediction.", style="Muted.TLabel").pack(anchor="w")

    def _settings(self):
        ttk.Label(self.settings_page, text="Recognition and safety", font=("Segoe UI", 17, "bold")).pack(anchor="w", pady=(0, 14))
        form = ttk.Frame(self.settings_page); form.pack(anchor="nw")
        self.vars = {}
        fields = [("Webcam index", "webcam_index", "0"),("Detection confidence", "detection_confidence", "0.55"),("Tracking confidence", "tracking_confidence", "0.55"),("Gesture hold duration (seconds)", "hold_seconds", "0.75"),("Command cooldown (seconds)", "cooldown_seconds", "1.0")]
        for i, (label, key, default) in enumerate(fields):
            ttk.Label(form, text=label).grid(row=i, column=0, sticky="w", padx=(0, 20), pady=8)
            var = tk.StringVar(value=default); self.vars[key] = var; ttk.Entry(form, textvariable=var, width=15).grid(row=i, column=1, sticky="w", pady=8)
        self.landmarks_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(form, text="Draw hand landmarks", variable=self.landmarks_var).grid(row=len(fields), column=0, sticky="w", pady=10)
        ttk.Button(form, text="Apply settings", command=self.apply_settings).grid(row=len(fields)+1, column=0, sticky="w", pady=14)
        ttk.Label(self.settings_page, text="Settings apply to the next camera start. Actions require a separate explicit enable step each session.", style="Muted.TLabel").pack(anchor="w", pady=18)

    def apply_settings(self):
        try:
            self.settings.webcam_index = int(self.vars["webcam_index"].get())
            for key in ("detection_confidence", "tracking_confidence", "hold_seconds", "cooldown_seconds"):
                setattr(self.settings, key, float(self.vars[key].get()))
            if not (0 <= self.settings.detection_confidence <= 1 and 0 <= self.settings.tracking_confidence <= 1 and self.settings.hold_seconds >= 0 and self.settings.cooldown_seconds >= 0): raise ValueError("Confidence must be 0–1; durations must be nonnegative")
            self.settings.show_landmarks = self.landmarks_var.get(); messagebox.showinfo("Settings", "Settings applied.")
        except ValueError as exc: messagebox.showerror("Invalid settings", str(exc))

    def enable_actions(self):
        if not messagebox.askyesno("Enable computer actions", "HandWave will send keyboard media and presentation keys while a gesture is held. Enable actions for this session?"): return
        self.controller.enabled = True; self.controller.cooldown = self.settings.cooldown_seconds
        self.status.configure(text="● Actions enabled", foreground="#b46b12")

    def start(self):
        if self.worker and self.worker.is_alive(): return
        self.stop_event.clear(); self.worker = threading.Thread(target=self._camera_loop, daemon=True); self.worker.start()
        self.status.configure(text="● Starting camera", foreground="#28765c")

    def stop(self):
        self.stop_event.set(); self.status.configure(text="● Camera stopped", foreground="#71808b")

    def _camera_loop(self):
        camera = detector = None
        try:
            import cv2
            import mediapipe as mp
        except ImportError as exc:
            self.frames.put(("error", f"Missing dependency: {exc.name}. Install requirements.txt.")); return
        model = ROOT / "models" / "hand_landmarker.task"
        if not model.exists(): self.frames.put(("error", "Hand Landmarker model missing. Run: python download_model.py")); return
        try:
            from mediapipe.tasks import python as mp_python
            from mediapipe.tasks.python import vision
            options = vision.HandLandmarkerOptions(base_options=mp_python.BaseOptions(model_asset_path=str(model)), running_mode=vision.RunningMode.VIDEO, num_hands=1, min_hand_detection_confidence=self.settings.detection_confidence, min_hand_presence_confidence=self.settings.detection_confidence, min_tracking_confidence=self.settings.tracking_confidence)
            detector = vision.HandLandmarker.create_from_options(options)
            camera = cv2.VideoCapture(self.settings.webcam_index)
            camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.settings.camera_width); camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.settings.camera_height)
            if not camera.isOpened(): raise RuntimeError("Could not open webcam")
            voter, active, began, timestamp = GestureVoter(), None, 0.0, 0
            while not self.stop_event.is_set():
                ok, frame = camera.read()
                if not ok: raise RuntimeError("Webcam disconnected or frame unavailable")
                frame = cv2.flip(frame, 1); start = time.perf_counter()
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
                timestamp += 33
                result = detector.detect_for_video(image, timestamp)
                label, fingers, handed = "No hand", 0, "Right"
                if result.hand_landmarks:
                    raw = result.hand_landmarks[0]
                    handed = result.handedness[0][0].category_name
                    label, fingers = classify([(p.x, p.y) for p in raw], handed)
                    if self.settings.show_landmarks:
                        for a,b in HAND_CONNECTIONS:
                            pa,pb=raw[a],raw[b]; cv2.line(frame,(int(pa.x*frame.shape[1]),int(pa.y*frame.shape[0])),(int(pb.x*frame.shape[1]),int(pb.y*frame.shape[0])),(75,135,110),2)
                        for p in raw: cv2.circle(frame,(int(p.x*frame.shape[1]),int(p.y*frame.shape[0])),4,(37,107,87),-1)
                voted, stability = voter.update(label)
                if voted != active:
                    active, began = voted, time.monotonic()
                    if voted == "No hand": self.controller.rearm(); self.current_action="Idle"
                if voted not in ("No hand", "Unrecognized") and time.monotonic()-began >= self.settings.hold_seconds:
                    self.current_action = self.controller.dispatch(voted)
                    if self.current_action == "Command sent":
                        self.commands += 1
                        self.command_counts[voted] = self.command_counts.get(voted, 0) + 1
                    # A disabled preview still consumes one continuous gesture, preventing surprise on later toggles.
                    self.controller.armed = False
                latency = (time.perf_counter()-start)*1000
                self.current_gesture, self.stability, self.fingers = voted, stability, fingers
                self.monitor.record(latency, label != "No hand"); self.monitor.gesture(voted)
                cv2.putText(frame, f"{voted} | {stability:.0f}%", (18,32), cv2.FONT_HERSHEY_SIMPLEX,.8,(26,47,57),2)
                try:
                    self.frames.put_nowait(("frame", frame.copy()))
                except queue.Full:
                    try: self.frames.get_nowait()
                    except queue.Empty: pass
                    self.frames.put_nowait(("frame", frame.copy()))
        except Exception as exc:
            try: self.frames.put_nowait(("error", str(exc)))
            except queue.Full: pass
        finally:
            if camera is not None: camera.release()
            if detector is not None: detector.close()

    def _refresh(self):
        try:
            while True:
                kind, value = self.frames.get_nowait()
                if kind == "error": self.status.configure(text="● Camera error", foreground="#b33b32"); messagebox.showerror("HandWave camera", value)
                else:
                    from PIL import Image, ImageTk
                    import cv2
                    rgb=cv2.cvtColor(value,cv2.COLOR_BGR2RGB); img=Image.fromarray(rgb); img.thumbnail((900,460)); self.photo=ImageTk.PhotoImage(img); self.video.configure(image=self.photo,text="")
        except queue.Empty: pass
        snap=self.monitor.snapshot()
        mapping={"Application":"Actions on" if self.controller.enabled else "Preview","Webcam":"Running" if self.worker and self.worker.is_alive() else "Stopped","Gesture":self.current_gesture,"Action":self.current_action,"FPS":f"{snap['fps']:.1f}","Latency":f"{snap['latency_avg']:.1f} ms","Detection rate":f"{snap['detection_rate']:.1f}%","Session":f"{int(snap['duration']//60)}:{int(snap['duration']%60):02d}","Commands":str(self.commands)}
        for key,value in mapping.items(): self.dash_values[key].configure(text=value)
        self.live_info.configure(text=f"Gesture: {self.current_gesture}    •    Fingers: {self.fingers}    •    Stability: {self.stability:.0f}%    •    Action: {self.current_action}")
        self.history.append((snap["fps"],snap["latency_avg"])); self.history=self.history[-90:]
        lines=[f"FPS:                 {snap['fps']:.2f}",f"Average latency:     {snap['latency_avg']:.2f} ms",f"Minimum latency:     {snap['latency_min']:.2f} ms",f"Maximum latency:     {snap['latency_max']:.2f} ms",f"Hand detection rate: {snap['detection_rate']:.1f}%",f"Gesture stability:   {self.stability:.1f}%",f"Gesture observations:{sum(self.monitor.gestures.values()):8d}",f"Successful commands: {self.commands}",f"Session duration:    {int(snap['duration'])} s"]
        self.perf_text.configure(state="normal"); self.perf_text.delete("1.0","end"); self.perf_text.insert("1.0","\n".join(lines)); self.perf_text.configure(state="disabled")
        self._draw_chart(); self._draw_distributions(); self.root.after(250,self._refresh)

    def _draw_chart(self):
        c=self.chart; c.delete("all"); w=max(c.winfo_width(),400); h=max(c.winfo_height(),200)
        c.create_text(22,12,anchor="nw",text="FPS (green)   •   latency ms (blue)",fill="#53616a")
        if len(self.history)<2: return
        for idx,color,field in [(0,"#36866b",0),(1,"#4b78a5",1)]:
            vals=[x[field] for x in self.history]; maxv=max(max(vals),1)
            pts=[]
            for n,v in enumerate(vals): pts.extend((35+n*(w-55)/(len(vals)-1), h-22-(v/maxv)*(h-55)))
            c.create_line(*pts,fill=color,width=2)

    def _draw_distributions(self):
        c=self.distribution; c.delete("all"); w=max(c.winfo_width(),500); h=max(c.winfo_height(),180)
        c.create_text(18,12,anchor="nw",text="Gesture observations",fill="#53616a",font=("Segoe UI",10,"bold"))
        c.create_text(w/2+18,12,anchor="nw",text="Successful commands",fill="#53616a",font=("Segoe UI",10,"bold"))
        labels=list(COMMANDS)
        for offset, data, color in [(10,self.monitor.gestures,"#36866b"),(w/2+10,self.command_counts,"#4b78a5")]:
            area_w=w/2-30; maxv=max([data.get(k,0) for k in labels]+[1]); slot=area_w/len(labels)
            for i,label in enumerate(labels):
                count=data.get(label,0); bar_h=(count/maxv)*(h-65); x=offset+i*slot
                c.create_rectangle(x+5,h-30-bar_h,x+slot-5,h-30,fill=color,outline="")
                c.create_text(x+slot/2,h-23,text=str(count),fill="#53616a",font=("Segoe UI",8))
                c.create_text(x+slot/2,h-8,text=label.replace(" ","\n"),fill="#53616a",font=("Segoe UI",7))

    def evaluate(self):
        path=filedialog.askopenfilename(filetypes=[("CSV files","*.csv")])
        if not path:return
        try:
            from evaluation.evaluate import evaluate_csv
            import json
            report=evaluate_csv(path)
            text=f"Accuracy: {report['accuracy']:.3f}  |  Samples: {report['samples']}\n\nPer gesture (precision / recall / F1 / support):\n"
            for label,m in report["per_gesture"].items(): text+=f"{label:16} {m['precision']:.3f} / {m['recall']:.3f} / {m['f1']:.3f} / {m['support']}\n"
            text+="\nConfusion matrix (rows=true, columns=predicted):\n"+json.dumps(report["confusion_matrix"],indent=2)
            self._set_eval(text)
        except Exception as exc: messagebox.showerror("Evaluation failed",str(exc))

    def _set_eval(self,text):
        self.eval_output.configure(state="normal"); self.eval_output.delete("1.0","end"); self.eval_output.insert("1.0",text); self.eval_output.configure(state="disabled")

    def export_counts(self):
        path=filedialog.asksaveasfilename(defaultextension=".csv",filetypes=[("CSV files","*.csv")])
        if path:
            with open(path,"w",newline="",encoding="utf-8") as f:
                writer=csv.writer(f); writer.writerow(["gesture","observations"]); writer.writerows(self.monitor.gestures.items())

    def close(self):
        self.stop_event.set(); self.root.after(100,self.root.destroy)


if __name__ == "__main__":
    root=tk.Tk(); HandWaveApp(root); root.mainloop()

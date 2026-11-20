"""Validate the YCB material labels one object at a time.

  python materials/label_ui.py            (from Project/wf_sim, any Python with tkinter)

Shows one object with its parts (editable). Photos come from materials/photos/<id>_<k>.jpg (download them
with materials/fetch_photos.py; needs Pillow); step through them with < > or Alt+Left/Right.
"Open photos" opens a browser image search. "OK, next" saves every part of the
object as validated and jumps to the next unvalidated object. The CSV is saved on every OK; a copy of the
first draft is kept as ycb_materials_draft.csv.
"""
import csv
import shutil
import tkinter as tk
import urllib.parse
import webbrowser
from pathlib import Path
from tkinter import messagebox, ttk

HERE = Path(__file__).resolve().parent
CSV_PATH = HERE / "ycb_materials.csv"
DRAFT = HERE / "ycb_materials_draft.csv"
PHOTOS = HERE / "photos"
FIELDS = ["id", "object", "category", "part", "material", "wall_mm", "area_share", "contents",
          "confidence", "note", "validated"]
EDIT = [("part", 14), ("material", 13), ("wall_mm", 7), ("area_share", 8), ("contents", 26),
        ("confidence", 8), ("note", 46)]
MATERIALS = ["steel", "aluminium", "glass", "plastic_thin", "plastic_solid", "acrylic", "cardboard",
             "wood", "ceramic", "foam", "rubber", "leather", "fabric", "water_rich", "other"]
CONF = ["high", "medium", "low"]
PHOTO_BOX = (660, 480)                               # max photo size on screen, pixels


def load():
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    objects = []                                   # [(id, [rows])] in file order
    for r in rows:
        if not objects or objects[-1][0] != r["id"]:
            objects.append((r["id"], []))
        objects[-1][1].append(r)
    return objects


def save(objects):
    tmp = CSV_PATH.with_suffix(".tmp")
    with open(tmp, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        for _, rows in objects:
            w.writerows(rows)
    tmp.replace(CSV_PATH)


class App:
    def __init__(self, root):
        if not DRAFT.exists():
            shutil.copy(CSV_PATH, DRAFT)
        self.root, self.objects = root, load()
        self.i = self._next_unvalidated(-1)
        root.title("YCB material labels")
        top = ttk.Frame(root, padding=8)
        top.pack(fill="x")
        self.title = ttk.Label(top, font=("Segoe UI", 15, "bold"))
        self.title.pack(side="left")
        self.progress = ttk.Label(top)
        self.progress.pack(side="right")

        mid = ttk.Frame(root, padding=8)
        mid.pack(fill="both", expand=True)
        left = ttk.Frame(mid)
        left.pack(side="left", fill="y", padx=(0, 8))
        self.photo = ttk.Label(left, text="", anchor="center", relief="groove")
        self.photo.pack()
        nav = ttk.Frame(left)
        nav.pack(pady=4)
        ttk.Button(nav, text="<", width=3, command=lambda: self.step_photo(-1)).pack(side="left")
        self.photo_n = ttk.Label(nav, width=16, anchor="center")
        self.photo_n.pack(side="left")
        ttk.Button(nav, text=">", width=3, command=lambda: self.step_photo(1)).pack(side="left")
        root.bind("<Alt-Left>", lambda e: self.step_photo(-1))
        root.bind("<Alt-Right>", lambda e: self.step_photo(1))
        right = ttk.Frame(mid)
        right.pack(side="left", fill="both", expand=True)
        ttk.Button(right, text="Open photos (browser)", command=self.open_photos).pack(anchor="w")
        self.grid = ttk.Frame(right, padding=(0, 8))
        self.grid.pack(fill="x")                     # no expand: keeps + part right under the rows
        pb = ttk.Frame(right)
        pb.pack(anchor="w")
        ttk.Button(pb, text="+ part", command=self.add_part).pack(side="left")
        ttk.Button(pb, text="- last part", command=self.remove_part).pack(side="left", padx=4)

        bot = ttk.Frame(root, padding=8)
        bot.pack(fill="x")
        ttk.Button(bot, text="< Back", command=lambda: self.go(self.i - 1)).pack(side="left")
        ttk.Button(bot, text="Skip >", command=lambda: self.go(self.i + 1)).pack(side="left", padx=4)
        ttk.Button(bot, text="Next unvalidated", command=lambda: self.go(self._next_unvalidated(self.i)))\
            .pack(side="left")
        ttk.Button(bot, text="OK, next  (Ctrl+Enter)", command=self.ok).pack(side="right")
        root.bind("<Control-Return>", lambda e: self.ok())
        self.show()

    def _next_unvalidated(self, start):
        n = len(self.objects)
        for k in range(1, n + 1):
            j = (start + k) % n
            if any(r["validated"] != "yes" for r in self.objects[j][1]):
                return j
        return max(start, 0)

    def show(self):
        oid, rows = self.objects[self.i]
        done = sum(all(r["validated"] == "yes" for r in rs) for _, rs in self.objects)
        state = "validated" if all(r["validated"] == "yes" for r in rows) else "not validated"
        self.title.config(text=f"{oid}  {rows[0]['object']}   ({rows[0]['category']}, {state})")
        self.progress.config(text=f"{done}/{len(self.objects)} validated   object {self.i + 1}")
        self._show_photo(oid)
        for w in self.grid.winfo_children():
            w.destroy()
        for c, (name, _) in enumerate(EDIT):
            ttk.Label(self.grid, text=name, font=("Segoe UI", 9, "bold")).grid(row=0, column=c, sticky="w")
        self.vars = []
        for r in rows:
            self._add_row(r)

    def _add_row(self, r):
        row = len(self.vars) + 1
        vs = {}
        for c, (name, width) in enumerate(EDIT):
            v = tk.StringVar(value=r.get(name, ""))
            if name in ("material", "confidence"):
                w = ttk.Combobox(self.grid, textvariable=v, width=width,
                                 values=MATERIALS if name == "material" else CONF)
            else:
                w = ttk.Entry(self.grid, textvariable=v, width=width)
            w.grid(row=row, column=c, padx=1, pady=2, sticky="w")
            vs[name] = v
        self.vars.append(vs)

    def _show_photo(self, oid):
        # '065a_1.jpg' must not match id '065' etc.: require '_' or '.' right after the id
        self.photo_files = sorted(p for ext in ("jpg", "jpeg", "png") for p in PHOTOS.glob(f"{oid}*.{ext}")
                                  if p.name[len(oid)] in "_.")
        self.photo_k = 0
        self._draw_photo()

    def step_photo(self, d):
        if self.photo_files:
            self.photo_k = (self.photo_k + d) % len(self.photo_files)
            self._draw_photo()

    def _draw_photo(self):
        files, oid = self.photo_files, self.objects[self.i][0]
        self.photo_n.config(text=f"photo {self.photo_k + 1}/{len(files)}" if files else "")
        if not files:
            self.photo.config(image="", text="no local photo\n\nrun materials/fetch_photos.py,\nuse 'Open photos', "
                                             f"or save one as\nmaterials/photos/{oid}_1.jpg", width=40)
            return
        f = files[self.photo_k]
        try:
            from PIL import Image, ImageTk
            im = Image.open(f)
            im.thumbnail(PHOTO_BOX)
            self._img = ImageTk.PhotoImage(im)
            self.photo.config(image=self._img, text="", width=0)
        except Exception as e:                       # Pillow missing or bad file
            self.photo.config(image="", text=f"could not show {f.name}\n{e}", width=40)

    def open_photos(self):
        name = self.objects[self.i][1][0]["object"].replace("_", " ")
        webbrowser.open("https://www.google.com/search?tbm=isch&q=" + urllib.parse.quote(f"YCB object {name}"))

    def add_part(self):
        oid, rows = self.objects[self.i]
        self._add_row(dict(confidence="medium"))

    def remove_part(self):
        if len(self.vars) <= 1:
            return
        for w in self.grid.grid_slaves(row=len(self.vars)):
            w.destroy()
        self.vars.pop()

    def _collect(self):
        oid, rows = self.objects[self.i]
        base = rows[0]
        new = []
        for vs in self.vars:
            r = {k: base[k] for k in ("id", "object", "category")}
            r.update({k: v.get().strip() for k, v in vs.items()})
            r["validated"] = "yes"
            new.append(r)
        try:
            total = sum(float(r["area_share"]) for r in new)
        except ValueError:
            total = None
        return new, total

    def ok(self):
        new, total = self._collect()
        msg = ("some area_share values are blank or not numbers" if total is None else
               f"area_share adds up to {total:.2f}, not 1" if abs(total - 1) > 0.05 else None)
        if msg and not messagebox.askyesno("area_share", msg + ". Save anyway?"):
            return
        self.objects[self.i] = (self.objects[self.i][0], new)
        save(self.objects)
        if all(all(r["validated"] == "yes" for r in rs) for _, rs in self.objects):
            messagebox.showinfo("Done", "All objects validated.")
            self.show()
            return
        self.go(self._next_unvalidated(self.i))

    def go(self, j):
        self.i = j % len(self.objects)
        self.show()


if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()

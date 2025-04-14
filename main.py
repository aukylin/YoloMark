import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import os
import json

class YOLOLabelTool:
    def __init__(self, root):
        self.root = root
        self.root.title("YOLO 标注工具")
        
        # 设置窗口大小和位置
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        window_width = int(screen_width * 0.8)
        window_height = int(screen_height * 0.8)
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # 初始化变量
        self.img = None
        self.tk_img = None
        self.bbox_list = []
        self.current_bbox = None
        self.image_path = ''
        self.image_dir = ''
        self.class_id = tk.StringVar(value='0')  # 移到前面
        self.class_list = {}  # 类别字典 {id: name}
        
        # 创建主框架
        self.main_frame = ttk.Frame(root)
        self.main_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # 创建工具栏
        self._create_toolbar()  # 先创建工具栏
        
        # 创建内容区域框架并设置最小高度
        content_frame = ttk.Frame(self.main_frame)
        content_frame.pack(fill='both', expand=True, pady=5)
        content_frame.pack_propagate(False)  # 防止自动收缩
        content_frame.configure(height=400)  # 设置最小高度
        
        # 左侧面板
        self.left_panel = ttk.Frame(content_frame)
        self.left_panel.pack(side='left', fill='both', expand=True)
        
        # 创建画布框架
        canvas_frame = ttk.Frame(self.left_panel)
        canvas_frame.pack(fill='both', expand=True)
        
        # 设置画布的最小尺寸
        self.canvas = tk.Canvas(canvas_frame, cursor='tcross', width=600, height=400)
        self.canvas.config(scrollregion=(0, 0, 600, 400))
        
        # 画布和滚动条
        h_scrollbar = ttk.Scrollbar(canvas_frame, orient='horizontal', command=self.canvas.xview)
        v_scrollbar = ttk.Scrollbar(canvas_frame, orient='vertical', command=self.canvas.yview)
        
        # 配置画布的滚动
        self.canvas.configure(xscrollcommand=h_scrollbar.set, yscrollcommand=v_scrollbar.set)
        
        # 使用网格布局管理器
        self.canvas.grid(row=0, column=0, sticky='nsew')
        h_scrollbar.grid(row=1, column=0, sticky='ew')
        v_scrollbar.grid(row=0, column=1, sticky='ns')
        
        # 配置网格权重
        canvas_frame.grid_rowconfigure(0, weight=1)
        canvas_frame.grid_columnconfigure(0, weight=1)
        
        # 右侧面板
        self.right_panel = ttk.Frame(content_frame, width=250)  # 增加宽度
        self.right_panel.pack(side='right', fill='y', padx=5)
        self.right_panel.pack_propagate(False)  # 防止自动收缩
        
        # 创建各个组件
        self._create_menu()
        self._create_right_panel()
        self._create_statusbar()
        self._bind_events()
        
        # 加载类别配置
        self.load_classes()

    def _create_menu(self):
        menu = tk.Menu(self.root)
        self.root.config(menu=menu)
        
        # 文件菜单
        file_menu = tk.Menu(menu, tearoff=0)
        menu.add_cascade(label="文件", menu=file_menu)
        file_menu.add_command(label="打开图片", command=self.load_image, accelerator="Ctrl+O")
        file_menu.add_command(label="保存标签", command=self.save_labels, accelerator="Ctrl+S")
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.root.quit)
        
        # 类别菜单
        class_menu = tk.Menu(menu, tearoff=0)
        menu.add_cascade(label="类别", menu=class_menu)
        class_menu.add_command(label="管理类别", command=self.manage_classes)
        class_menu.add_command(label="导入类别", command=self.import_classes)
        class_menu.add_command(label="导出类别", command=self.export_classes)

    def _create_toolbar(self):
        # 创建工具栏框架
        toolbar = ttk.Frame(self.main_frame)
        toolbar.pack(side='top', fill='x', pady=(0, 5))
        
        # 左侧按钮
        left_frame = ttk.Frame(toolbar)
        left_frame.pack(side='left', padx=5)
        
        ttk.Button(left_frame, text="打开图片", command=self.load_image).pack(side='left', padx=2)
        ttk.Button(left_frame, text="保存标签", command=self.save_labels).pack(side='left', padx=2)
        ttk.Label(left_frame, text="类别：").pack(side='left', padx=(10, 2))
        self.class_combo = ttk.Combobox(left_frame, textvariable=self.class_id, width=15)
        self.class_combo.pack(side='left', padx=2)
        
        # 添加类别管理按钮
        ttk.Button(left_frame, text="管理类别", command=self.manage_classes).pack(side='left', padx=2)
        
        # 右侧导航按钮
        nav_frame = ttk.Frame(toolbar)
        nav_frame.pack(side='right', padx=5)
        ttk.Button(nav_frame, text="上一张", command=self.prev_image).pack(side='left', padx=2)
        ttk.Button(nav_frame, text="下一张", command=self.next_image).pack(side='left', padx=2)

    def _create_right_panel(self):
        # 设置固定宽度
        self.right_panel.configure(width=250)
        self.right_panel.pack_propagate(False)
        
        # 标题
        ttk.Label(self.right_panel, text="标注列表").pack(anchor='w', pady=5)
        
        # 列表框架
        list_frame = ttk.Frame(self.right_panel)
        list_frame.pack(fill='both', expand=True, pady=5)
        
        # 标注列表和滚动条
        self.bbox_listbox = tk.Listbox(list_frame)
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.bbox_listbox.yview)
        self.bbox_listbox.configure(yscrollcommand=scrollbar.set)
        
        self.bbox_listbox.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
    def _create_statusbar(self):
        self.statusbar = ttk.Label(self.root, text="就绪", relief=tk.SUNKEN, anchor='w')
        self.statusbar.pack(side='bottom', fill='x')

    def _bind_events(self):
        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.root.bind("<Control-o>", lambda e: self.load_image())
        self.root.bind("<Control-s>", lambda e: self.save_labels())
        self.root.bind("<Left>", lambda e: self.prev_image())
        self.root.bind("<Right>", lambda e: self.next_image())

    def load_image(self, path=None):
        """加载图片
        Args:
            path: 图片路径，如果为None则打开文件选择对话框
        """
        try:
            # 如果没有指定路径，打开文件选择对话框
            if path is None:
                # 修改文件选择对话框的调用方式
                path = filedialog.askopenfilename(
                    title="选择图片",
                    filetypes=[
                        ("图片文件", "*.jpg *.jpeg *.png"),
                        ("所有文件", "*.*")
                    ],
                    initialdir=self.image_dir if self.image_dir else os.path.expanduser("~")
                )
            
            if path and os.path.exists(path):  # 确保文件存在
                self.image_path = path
                self.image_dir = os.path.dirname(path)
                
                # 加载图片
                self.img = Image.open(path)
                
                # 调整图片大小以适应画布
                display_size = (800, 600)  # 设置最大显示尺寸
                self.img.thumbnail(display_size, Image.Resampling.LANCZOS)
                
                # 创建图片对象
                self.tk_img = ImageTk.PhotoImage(self.img)
                
                # 更新画布
                self.canvas.config(scrollregion=(0, 0, self.tk_img.width(), self.tk_img.height()))
                self.canvas.delete("all")
                self.canvas.create_image(0, 0, anchor="nw", image=self.tk_img)
                
                # 清除并更新标注
                self.bbox_list.clear()
                self.update_bbox_list()
                self.load_existing_labels()
                
                # 更新状态栏
                self.statusbar.config(text=f"已加载图片：{os.path.basename(path)}")
                return True
                
        except Exception as e:
            messagebox.showerror("错误", f"无法加载图片：{str(e)}")
            return False
        
        return False

    def load_existing_labels(self):
        """加载已存在的标签文件"""
        label_path = os.path.splitext(self.image_path)[0] + ".txt"
        if os.path.exists(label_path):
            with open(label_path, 'r') as f:
                lines = f.readlines()
                w, h = self.img.size
                for line in lines:
                    class_id, x_center, y_center, width, height = map(float, line.strip().split())
                    x0 = int((x_center - width/2) * w)
                    y0 = int((y_center - height/2) * h)
                    x1 = int((x_center + width/2) * w)
                    y1 = int((y_center + height/2) * h)
                    self.bbox_list.append((int(class_id), x0, y0, x1, y1))
                    self.canvas.create_rectangle(x0, y0, x1, y1, outline='green')
                self.update_bbox_list()

    def on_click(self, event):
        self.current_bbox = [event.x, event.y]

    def on_drag(self, event):
        if self.current_bbox:
            self.canvas.delete("preview")
            x0, y0 = self.current_bbox
            self.canvas.create_rectangle(x0, y0, event.x, event.y, outline='red', tag="preview")

    def on_release(self, event):
        if self.current_bbox:
            x0, y0 = self.current_bbox
            x1, y1 = event.x, event.y
            if abs(x1-x0) > 5 and abs(y1-y0) > 5:  # 最小尺寸限制
                self.canvas.create_rectangle(x0, y0, x1, y1, outline='green')
                class_id = self.class_id.get().split(':')[0]
                self.bbox_list.append((int(class_id), x0, y0, x1, y1))
                self.update_bbox_list()
            self.current_bbox = None
            self.canvas.delete("preview")

    def update_bbox_list(self):
        self.bbox_listbox.delete(0, tk.END)
        for i, (class_id, x0, y0, x1, y1) in enumerate(self.bbox_list):
            class_name = self.class_list.get(str(class_id), f"类别{class_id}")
            self.bbox_listbox.insert(tk.END, f"{i+1}. {class_name}: ({x0},{y0})-({x1},{y1})")

    def delete_bbox(self):
        selection = self.bbox_listbox.curselection()
        if selection:
            idx = selection[0]
            self.bbox_list.pop(idx)
            self.redraw_canvas()
            self.update_bbox_list()

    def clear_all(self):
        if messagebox.askyesno("确认", "是否清空所有标注？"):
            self.bbox_list.clear()
            self.redraw_canvas()
            self.update_bbox_list()

    def redraw_canvas(self):
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor="nw", image=self.tk_img)
        for class_id, x0, y0, x1, y1 in self.bbox_list:
            self.canvas.create_rectangle(x0, y0, x1, y1, outline='green')

    def save_labels(self, event=None):
        if not self.image_path or not self.bbox_list:
            return
        w, h = self.img.size
        label_path = os.path.splitext(self.image_path)[0] + ".txt"
        with open(label_path, 'w') as f:
            for class_id, x0, y0, x1, y1 in self.bbox_list:
                x_center = ((x0 + x1) / 2) / w
                y_center = ((y0 + y1) / 2) / h
                box_width = abs(x1 - x0) / w
                box_height = abs(y1 - y0) / h
                f.write(f"{class_id} {x_center:.6f} {y_center:.6f} {box_width:.6f} {box_height:.6f}\n")
        self.statusbar.config(text=f"标签已保存：{os.path.basename(label_path)}")

    def manage_classes(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("类别管理")
        dialog.geometry("300x400")
        dialog.transient(self.root)
        
        frame = ttk.Frame(dialog)
        frame.pack(padx=5, pady=5, fill='both', expand=True)
        
        # 类别列表框架
        list_frame = ttk.LabelFrame(frame, text="当前类别")
        list_frame.pack(fill='both', expand=True, pady=5)
        
        # 类别列表和滚动条
        self.class_listbox = tk.Listbox(list_frame)
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.class_listbox.yview)
        self.class_listbox.configure(yscrollcommand=scrollbar.set)
        
        self.class_listbox.pack(side='left', fill='both', expand=True, padx=5, pady=5)
        scrollbar.pack(side='right', fill='y', pady=5)
        
        # 显示现有类别
        for class_id, class_name in self.class_list.items():
            self.class_listbox.insert(tk.END, f"{class_id}: {class_name}")
        
        # 添加类别框架
        add_frame = ttk.LabelFrame(frame, text="添加新类别")
        add_frame.pack(fill='x', pady=5)
        
        # ID输入框
        id_frame = ttk.Frame(add_frame)
        id_frame.pack(fill='x', padx=5, pady=2)
        ttk.Label(id_frame, text="类别ID:").pack(side='left')
        id_entry = ttk.Entry(id_frame, width=8)
        id_entry.pack(side='left', padx=5)
        
        # 名称输入框
        name_frame = ttk.Frame(add_frame)
        name_frame.pack(fill='x', padx=5, pady=2)
        ttk.Label(name_frame, text="类别名称:").pack(side='left')
        name_entry = ttk.Entry(name_frame)
        name_entry.pack(side='left', fill='x', expand=True, padx=5)
        
        # 按钮框架
        btn_frame = ttk.Frame(add_frame)
        btn_frame.pack(fill='x', padx=5, pady=5)
        
        def add_class():
            class_id = id_entry.get().strip()
            class_name = name_entry.get().strip()
            if class_id and class_name:
                if class_id.isdigit():
                    self.class_list[class_id] = class_name
                    self.class_listbox.insert(tk.END, f"{class_id}: {class_name}")
                    self.update_class_combo()
                    self.save_classes()
                    id_entry.delete(0, tk.END)
                    name_entry.delete(0, tk.END)
                else:
                    messagebox.showwarning("警告", "类别ID必须为数字！")
            else:
                messagebox.showwarning("警告", "类别ID和名称不能为空！")
        
        def delete_class():
            selection = self.class_listbox.curselection()
            if selection:
                idx = selection[0]
                class_str = self.class_listbox.get(idx)
                class_id = class_str.split(':')[0].strip()
                if messagebox.askyesno("确认", f"是否删除类别 {class_str}？"):
                    del self.class_list[class_id]
                    self.class_listbox.delete(idx)
                    self.update_class_combo()
                    self.save_classes()
        
        ttk.Button(btn_frame, text="添加类别", command=add_class).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="删除所选", command=delete_class).pack(side='left', padx=5)

    def update_class_combo(self):
        self.class_combo['values'] = [f"{id}: {name}" for id, name in self.class_list.items()]

    def save_classes(self):
        with open('classes.json', 'w', encoding='utf-8') as f:
            json.dump(self.class_list, f, ensure_ascii=False, indent=2)

    def load_classes(self):
        try:
            with open('classes.json', 'r', encoding='utf-8') as f:
                self.class_list = json.load(f)
                self.update_class_combo()
        except FileNotFoundError:
            pass

    def import_classes(self):
        path = filedialog.askopenfilename(filetypes=[("JSON文件", "*.json")])
        if path:
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    self.class_list = json.load(f)
                    self.update_class_combo()
                    self.save_classes()
                    messagebox.showinfo("成功", "类别导入成功！")
            except Exception as e:
                messagebox.showerror("错误", f"导入失败：{str(e)}")

    def export_classes(self):
        path = filedialog.asksaveasfilename(defaultextension=".json", 
                                          filetypes=[("JSON文件", "*.json")])
        if path:
            try:
                with open(path, 'w', encoding='utf-8') as f:
                    json.dump(self.class_list, f, ensure_ascii=False, indent=2)
                messagebox.showinfo("成功", "类别导出成功！")
            except Exception as e:
                messagebox.showerror("错误", f"导出失败：{str(e)}")

    def prev_image(self, event=None):
        if not self.image_dir:
            return
        images = sorted([f for f in os.listdir(self.image_dir) 
                        if f.lower().endswith(('.jpg', '.jpeg', '.png'))])
        if not images:
            return
            
        current = os.path.basename(self.image_path)
        try:
            idx = images.index(current)
            if idx > 0:
                self.load_image(os.path.join(self.image_dir, images[idx-1]))
        except ValueError:
            pass

    def next_image(self, event=None):
        if not self.image_dir:
            return
        images = sorted([f for f in os.listdir(self.image_dir) 
                        if f.lower().endswith(('.jpg', '.jpeg', '.png'))])
        if not images:
            return
            
        current = os.path.basename(self.image_path)
        try:
            idx = images.index(current)
            if idx < len(images) - 1:
                self.load_image(os.path.join(self.image_dir, images[idx+1]))
        except ValueError:
            pass

if __name__ == "__main__":
    root = tk.Tk()
    app = YOLOLabelTool(root)
    root.mainloop()
import tkinter as tk
from tkinter import ttk, messagebox
import os
import csv
import sqlite3
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from reportlab.lib.pagesizes import A5
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm

# ================= CONFIGURACIÓN Y DATOS =================
EMISOR = {
    "razon": "CAFÉ TAWA ANDINO S.A.C.",
    "ruc": "20601234567",
    "direccion": "Av. Floral 234 - Puno",
    "lema": "El sabor del altiplano en cada taza"
}

PRODUCTOS_DATA = {
    "☕ CAFÉS": [("Café Más Frío Que Puno", 8.00), ("El Soplado de la Abuela", 7.00), ("Café A Que No Duermes", 8.50)],
    "🌿 INFUSIONES": [("Más Frío que Juliaca", 4.50), ("Abrazo del Titicaca", 5.00)],
    "🍫 CHOCOLATERÍA": [("Chocolate Artesanal Tawa", 8.50), ("Chocolate con Clavo y Canela", 9.50)],
    "🍰 POSTRES PUNEÑOS": [("Brisa del Lago", 12.00), ("Suspiro del Sur", 12.50), ("Queso Helado", 7.50)],
    "🥖 PANES REGIONALES": [("Pan de Putina", 1.50), ("Pan de Azángaro", 1.50)],
    "✨ ESPECIALES": [("Combo Desayuno Tawa", 15.00), ("Especial del Día", 10.00)]
}

class TawaMasterPOS:
    def __init__(self, root):
        self.root = root
        self.root.title("TAWA ENTERPRISE v2.0 - SISTEMA DE GESTIÓN")
        self.root.geometry("1200x850")
        self.root.configure(bg="#FDFCF0")
        
        # Base de Datos para persistencia
        self.db_con = sqlite3.connect("tawa_management.db")
        self.cursor = self.db_con.cursor()
        self.init_db()

        self.carrito = []
        self.total_final = 0.0
        self.tipo_doc = tk.StringVar(value="BOLETA")
        
        self.setup_ui()

    def init_db(self):
        # Inventario y Ventas
        self.cursor.execute("CREATE TABLE IF NOT EXISTS stock (prod TEXT PRIMARY KEY, cant INTEGER)")
        self.cursor.execute("CREATE TABLE IF NOT EXISTS historial (fecha TEXT, prod TEXT, total REAL)")
        
        # Llenar stock inicial si está vacío
        self.cursor.execute("SELECT COUNT(*) FROM stock")
        if self.cursor.fetchone()[0] == 0:
            for cat in PRODUCTOS_DATA.values():
                for p in cat:
                    self.cursor.execute("INSERT INTO stock VALUES (?, ?)", (p[0], 50))
            self.db_con.commit()

    def setup_ui(self):
        # --- HEADER ---
        header = tk.Frame(self.root, bg="#4E342E", pady=10)
        header.pack(fill="x")
        tk.Label(header, text="☕ TAWA BUSINESS ENTERPRISE", font=("Georgia", 22, "bold"), fg="#E0C097", bg="#4E342E").pack()

        # --- NAVEGACIÓN (TABS) ---
        style = ttk.Style()
        style.configure("TNotebook.Tab", font=('Arial', '10', 'bold'), padding=[10, 5])
        
        self.tabs = ttk.Notebook(self.root)
        self.tabs.pack(fill="both", expand=True, padx=10, pady=10)

        # Tab 1: Punto de Venta
        self.tab_venta = tk.Frame(self.tabs, bg="#FDFCF0")
        self.tabs.add(self.tab_venta, text="  🛒 PUNTO DE VENTA  ")
        self.ui_punto_venta()

        # Tab 2: Dashboard e Inventario
        self.tab_admin = tk.Frame(self.tabs, bg="#FDFCF0")
        self.tabs.add(self.tab_admin, text="  📊 DASHBOARD / STOCK  ")
        self.ui_admin()

    def ui_punto_venta(self):
        # Contenedor superior para datos de cliente
        f_doc = tk.LabelFrame(self.tab_venta, text=" COMPROBANTE ", bg="white", font=("Arial", 10, "bold"))
        f_doc.pack(fill="x", padx=15, pady=10)

        ttk.Radiobutton(f_doc, text="BOLETA", variable=self.tipo_doc, value="BOLETA").grid(row=0, column=0, padx=10)
        ttk.Radiobutton(f_doc, text="FACTURA", variable=self.tipo_doc, value="FACTURA").grid(row=0, column=1, padx=10)
        
        tk.Label(f_doc, text="DNI/RUC:", bg="white").grid(row=0, column=2, padx=5)
        self.ent_doc = ttk.Entry(f_doc, width=15); self.ent_doc.grid(row=0, column=3); self.ent_doc.insert(0, "00000000")
        
        tk.Label(f_doc, text="CLIENTE:", bg="white").grid(row=0, column=4, padx=5)
        self.ent_cliente = ttk.Entry(f_doc, width=35); self.ent_cliente.grid(row=0, column=5); self.ent_cliente.insert(0, "CLIENTE VARIOS")

        # Cuerpo del POS
        body = tk.Frame(self.tab_venta, bg="#FDFCF0")
        body.pack(fill="both", expand=True, padx=15)

        # Panel izquierdo (Selección mejorada)
        p_sel = tk.LabelFrame(body, text=" AGREGAR ITEM ", bg="white", padx=10, pady=10)
        p_sel.pack(side="left", fill="y", pady=10)

        tk.Label(p_sel, text="Categoría:", bg="white").pack(anchor="w")
        self.cb_cat = ttk.Combobox(p_sel, values=list(PRODUCTOS_DATA.keys()), state="readonly", width=25)
        self.cb_cat.pack(pady=5); self.cb_cat.bind("<<ComboboxSelected>>", self.cargar_items)

        tk.Label(p_sel, text="Producto:", bg="white").pack(anchor="w")
        self.cb_prod = ttk.Combobox(p_sel, state="readonly", width=25)
        self.cb_prod.pack(pady=5); self.cb_prod.bind("<<ComboboxSelected>>", self.get_precio)

        tk.Label(p_sel, text="Cantidad:", bg="white").pack(anchor="w")
        self.ent_cant = ttk.Entry(p_sel, width=10); self.ent_cant.pack(pady=5); self.ent_cant.insert(0, "1")

        tk.Label(p_sel, text="Precio S/:", bg="white").pack(anchor="w")
        self.ent_pre = ttk.Entry(p_sel, width=10); self.ent_pre.pack(pady=5)

        tk.Button(p_sel, text="＋ AÑADIR AL CARRITO", bg="#2E7D32", fg="white", font=("Arial", 10, "bold"), 
                  command=self.add_to_cart, height=2).pack(fill="x", pady=20)

        # Panel derecho (Tabla y Total)
        p_res = tk.Frame(body, bg="#FDFCF0")
        p_res.pack(side="right", fill="both", expand=True, padx=(10, 0), pady=10)

        self.tree = ttk.Treeview(p_res, columns=("c", "d", "p", "s"), show="headings", height=15)
        self.tree.heading("c", text="CANT"); self.tree.heading("d", text="PRODUCTO"); self.tree.heading("p", text="UNIT."); self.tree.heading("s", text="SUBTOT")
        self.tree.column("c", width=50); self.tree.column("d", width=300)
        self.tree.pack(fill="both", expand=True)

        footer = tk.Frame(p_res, bg="white", pady=10, padx=10, relief="groove", bd=1)
        footer.pack(fill="x", pady=(10, 0))
        
        self.lbl_total = tk.Label(footer, text="TOTAL: S/ 0.00", font=("Arial", 24, "bold"), bg="white", fg="#4E342E")
        self.lbl_total.pack(side="left")

        tk.Button(footer, text="🖨️ EMITIR COMPROBANTE", bg="#4E342E", fg="#E0C097", font=("Arial", 11, "bold"), 
                  padx=20, command=self.procesar_venta).pack(side="right")

    def ui_admin(self):
        # Mitad Superior: Gráfico de Ventas
        self.fig_frame = tk.Frame(self.tab_admin, bg="white", relief="sunken", bd=1)
        self.fig_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Mitad Inferior: Inventario
        low_f = tk.LabelFrame(self.tab_admin, text=" CONTROL DE STOCK (ALERTAS) ", bg="white", font=("Arial", 10, "bold"))
        low_f.pack(fill="both", expand=True, padx=20, pady=10)

        self.tree_stk = ttk.Treeview(low_f, columns=("p", "s"), show="headings")
        self.tree_stk.heading("p", text="PRODUCTO"); self.tree_stk.heading("s", text="STOCK ACTUAL")
        self.tree_stk.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        
        btn_f = tk.Frame(low_f, bg="white")
        btn_f.pack(side="right", fill="y", padx=10)
        tk.Button(btn_f, text="🔄 ACTUALIZAR", command=self.refresh_admin).pack(fill="x", pady=5)
        tk.Button(btn_f, text="📁 EXCEL VENTAS", bg="#1D6F42", fg="white", command=self.export_excel).pack(fill="x", pady=5)

    # --- LÓGICA DE NEGOCIO ---
    def cargar_items(self, e):
        cat = self.cb_cat.get()
        self.cb_prod.config(values=[p[0] for p in PRODUCTOS_DATA[cat]])
        self.cb_prod.set(PRODUCTOS_DATA[cat][0][0]); self.get_precio(None)

    def get_precio(self, e):
        cat, nom = self.cb_cat.get(), self.cb_prod.get()
        p = next(x[1] for x in PRODUCTOS_DATA[cat] if x[0] == nom)
        self.ent_pre.delete(0, tk.END); self.ent_pre.insert(0, f"{p:.2f}")

    def add_to_cart(self):
        try:
            c, n, p = int(self.ent_cant.get()), self.cb_prod.get(), float(self.ent_pre.get())
            # Validar stock antes de añadir
            self.cursor.execute("SELECT cant FROM stock WHERE prod=?", (n,))
            stk = self.cursor.fetchone()[0]
            if c > stk:
                messagebox.showwarning("Sin Stock", f"Solo quedan {stk} unidades de {n}")
                return

            sub = c * p
            self.carrito.append({"cant": c, "desc": n, "p_u": p, "sub": sub})
            self.tree.insert("", "end", values=(c, n, f"S/ {p:.2f}", f"S/ {sub:.2f}"))
            self.total_final += sub
            self.lbl_total.config(text=f"TOTAL: S/ {self.total_final:.2f}")
        except: messagebox.showerror("Error", "Revise los campos")

    def procesar_venta(self):
        if not self.carrito: return
        
        # Correlativo
        serie = "B001" if self.tipo_doc.get() == "BOLETA" else "F001"
        p_n = f"corr_{serie}.txt"
        n = 1
        if os.path.exists(p_n):
            with open(p_n, "r") as r: n = int(r.read()) + 1
        with open(p_n, "w") as w: w.write(str(n))
        
        id_doc = f"{serie}-{n:08d}"
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M")

        # Actualizar DB y Stock
        for i in self.carrito:
            self.cursor.execute("INSERT INTO historial VALUES (?, ?, ?)", (fecha, i['desc'], i['sub']))
            self.cursor.execute("UPDATE stock SET cant = cant - ? WHERE prod = ?", (i['cant'], i['desc']))
        self.db_con.commit()

        # Generar archivos
        self.save_csv(id_doc)
        self.generate_pdf(id_doc)
        
        messagebox.showinfo("Tawa", f"Venta {id_doc} exitosa")
        self.limpiar_todo()
        self.refresh_admin()

    def generate_pdf(self, doc_id):
        fn = f"Tawa_{doc_id}.pdf"
        c = canvas.Canvas(fn, pagesize=A5)
        ancho, alto = A5
        
        # Header PDF
        c.setFont("Helvetica-Bold", 14); c.drawCentredString(ancho/2, alto-15*mm, EMISOR["razon"])
        c.setFont("Helvetica", 8); c.drawCentredString(ancho/2, alto-20*mm, f"RUC: {EMISOR['ruc']} - {EMISOR['direccion']}")
        
        # Cuadro de Documento
        c.rect(ancho-60*mm, alto-45*mm, 50*mm, 20*mm)
        c.setFont("Helvetica-Bold", 10); c.drawCentredString(ancho-35*mm, alto-32*mm, self.tipo_doc.get())
        c.drawCentredString(ancho-35*mm, alto-40*mm, doc_id)

        # Datos Cliente
        y = alto - 55*mm; c.setFont("Helvetica", 9)
        c.drawString(15*mm, y, f"FECHA: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        c.drawString(15*mm, y-5*mm, f"CLIENTE: {self.ent_cliente.get().upper()}")
        c.drawString(15*mm, y-10*mm, f"DNI/RUC: {self.ent_doc.get()}")

        # Cuerpo
        y -= 25*mm
        c.setFont("Helvetica-Bold", 9); c.drawString(15*mm, y, "CANT"); c.drawString(30*mm, y, "DESCRIPCION"); c.drawRightString(ancho-15*mm, y, "SUBTOTAL")
        c.line(15*mm, y-2*mm, ancho-15*mm, y-2*mm)
        
        y -= 7*mm; c.setFont("Helvetica", 9)
        for i in self.carrito:
            c.drawString(15*mm, y, str(i['cant'])); c.drawString(30*mm, y, i['desc'][:30]); c.drawRightString(ancho-15*mm, y, f"{i['sub']:.2f}")
            y -= 5*mm

        # Pie de página y totales
        gravada = self.total_final / 1.18
        igv = self.total_final - gravada
        y = 35*mm
        c.line(ancho-60*mm, y+5*mm, ancho-15*mm, y+5*mm)
        c.drawString(ancho-60*mm, y, "OP. GRAVADA:"); c.drawRightString(ancho-15*mm, y, f"{gravada:.2f}")
        c.drawString(ancho-60*mm, y-5*mm, "I.G.V. (18%):"); c.drawRightString(ancho-15*mm, y-5*mm, f"{igv:.2f}")
        c.setFont("Helvetica-Bold", 11); c.drawString(ancho-60*mm, y-12*mm, "TOTAL S/:"); c.drawRightString(ancho-15*mm, y-12*mm, f"{self.total_final:.2f}")
        
        c.save(); os.startfile(fn)

    def save_csv(self, doc_id):
        archivo = "Ventas_Maestras.csv"
        existe = os.path.isfile(archivo)
        with open(archivo, mode="a", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f, delimiter=';')
            if not existe: w.writerow(["FECHA", "DOC", "CLIENTE", "PRODUCTO", "SUBTOT"])
            for i in self.carrito:
                w.writerow([datetime.now().strftime("%d/%m/%Y"), doc_id, self.ent_cliente.get(), i['desc'], i['sub']])

    def refresh_admin(self):
        # Limpiar stock
        for i in self.tree_stk.get_children(): self.tree_stk.delete(i)
        self.cursor.execute("SELECT * FROM stock ORDER BY cant ASC")
        for r in self.cursor.fetchall():
            tag = "bajo" if r[1] < 10 else ""
            self.tree_stk.insert("", "end", values=r, tags=(tag,))
        self.tree_stk.tag_configure("bajo", foreground="red", font=('Arial', 9, 'bold'))

        # Actualizar Gráfico
        for widget in self.fig_frame.winfo_children(): widget.destroy()
        
        self.cursor.execute("SELECT prod, SUM(total) FROM historial GROUP BY prod ORDER BY SUM(total) DESC LIMIT 5")
        data = self.cursor.fetchall()
        if data:
            fig, ax = plt.subplots(figsize=(6, 3), dpi=80)
            names = [x[0][:10] for x in data]
            vals = [x[1] for x in data]
            ax.bar(names, vals, color="#4E342E")
            ax.set_title("TOP 5 VENTAS (S/.)")
            plt.xticks(rotation=15)
            
            canvas_plot = FigureCanvasTkAgg(fig, master=self.fig_frame)
            canvas_plot.get_tk_widget().pack(fill="both")

    def export_excel(self):
        if os.path.exists("Ventas_Maestras.csv"): os.startfile("Ventas_Maestras.csv")

    def limpiar_todo(self):
        self.carrito = []; self.total_final = 0.0
        for i in self.tree.get_children(): self.tree.delete(i)
        self.lbl_total.config(text="TOTAL: S/ 0.00")

if __name__ == "__main__":
    root = tk.Tk()
    app = TawaMasterPOS(root)
    root.mainloop()
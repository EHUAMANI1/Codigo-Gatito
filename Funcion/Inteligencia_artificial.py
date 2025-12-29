import tkinter as tk
from tkinter import ttk
import re

# =========================
# CONFIG
# =========================
ASSISTANT_NAME = "Masha"

# =========================
# UTILIDADES NLP
# =========================
def normalize(text):
    return re.sub(r"\s+", " ", text.lower().strip())

def contains(words, text):
    return any(w in text for w in words)

# =========================
# CONOCIMIENTO BASE
# =========================
KNOWLEDGE = {

    "historia": {
        "revolucion francesa": (
            "La Revolución Francesa fue un proceso social y político iniciado en 1789.",
            "Terminó con la monarquía absoluta y promovió ideas de libertad, igualdad y soberanía popular.",
            "Marcó el inicio de la Edad Contemporánea."
        ),
        "independencia del peru": (
            "La independencia del Perú se proclamó en 1821.",
            "Fue liderada por José de San Martín.",
            "Puso fin al dominio colonial español."
        )
    },

    "economia": {
        "inflacion": (
            "La inflación es el aumento general y sostenido de los precios.",
            "Reduce el poder adquisitivo del dinero.",
            "Puede ser causada por exceso de demanda o aumento de costos."
        ),
        "oferta y demanda": (
            "La oferta representa lo que los productores venden.",
            "La demanda representa lo que los consumidores compran.",
            "El equilibrio se da cuando ambas se igualan."
        )
    },

    "ingles": {
        "present simple": (
            "El present simple se usa para rutinas y hechos generales.",
            "Ejemplo: I study economics.",
            "Estructura: sujeto + verbo base."
        )
    },

    "geografia": {
        "clima": (
            "El clima es el promedio de condiciones atmosféricas a largo plazo.",
            "Incluye temperatura, precipitación y vientos.",
            "No debe confundirse con el tiempo atmosférico."
        )
    },

    "filosofia": {
        "etica": (
            "La ética estudia el comportamiento moral humano.",
            "Analiza qué acciones son correctas o incorrectas.",
            "Es una rama fundamental de la filosofía."
        )
    },

    "psicologia": {
        "conducta": (
            "La conducta es el comportamiento observable de una persona.",
            "Puede ser aprendida o innata.",
            "Es objeto de estudio de la psicología."
        )
    }
}

# =========================
# MOTOR DE RAZONAMIENTO
# =========================
def detect_course(text):
    if contains(["historia", "revolucion", "independencia"], text):
        return "historia"
    if contains(["inflacion", "economia", "oferta", "demanda"], text):
        return "economia"
    if contains(["english", "ingles", "present"], text):
        return "ingles"
    if contains(["clima", "mapa", "geografia"], text):
        return "geografia"
    if contains(["etica", "filosofia"], text):
        return "filosofia"
    if contains(["conducta", "psicologia"], text):
        return "psicologia"
    return None

def generate_response(user_text):
    text = normalize(user_text)

    # Conversación básica
    if contains(["hola", "buenas"], text):
        return "Hola 🙂 dime qué quieres aprender."

    course = detect_course(text)

    if not course:
        return (
            "Puedo ayudarte si lo enfocamos en:\n"
            "inglés, economía, geografía, historia, filosofía o psicología.\n"
            "Ejemplo: «Historia: Revolución Francesa»"
        )

    for topic, explanation in KNOWLEDGE[course].items():
        if topic in text:
            return "\n".join(explanation)

    return (
        f"Entiendo que es {course}, pero necesito que seas un poco más específico.\n"
        "¿Qué concepto quieres que explique?"
    )

# =========================
# INTERFAZ CHAT
# =========================
class MashaApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Masha")
        self.geometry("900x600")

        self.chat = tk.Text(
            self, wrap="word", bg="#0f0f10", fg="#eaeaea",
            font=("Segoe UI", 11), relief="flat", padx=12, pady=12
        )
        self.chat.pack(fill="both", expand=True)
        self.chat.configure(state="disabled")

        bottom = ttk.Frame(self)
        bottom.pack(fill="x", padx=10, pady=10)

        self.input = tk.Entry(bottom)
        self.input.pack(side="left", fill="x", expand=True)
        self.input.bind("<Return>", self.send)

        ttk.Button(bottom, text="Enviar", command=self.send).pack(side="left", padx=10)

        self.write(ASSISTANT_NAME, "Hola, soy Masha. Pregúntame lo que quieras aprender.")

    def write(self, who, text):
        self.chat.configure(state="normal")
        self.chat.insert("end", f"{who}: {text}\n\n")
        self.chat.configure(state="disabled")
        self.chat.see("end")

    def send(self, event=None):
        user_text = self.input.get().strip()
        if not user_text:
            return
        self.input.delete(0, "end")
        self.write("Tú", user_text)

        response = generate_response(user_text)
        self.write(ASSISTANT_NAME, response)

# =========================
# RUN
# =========================
if __name__ == "__main__":
    app = MashaApp()
    app.mainloop()

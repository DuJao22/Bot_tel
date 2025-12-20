# ==========================================================
# AUTO-DEV AI SYSTEM - MINI REPLIT VIA TELEGRAM
# SINGLE FILE PYTHON
# ==========================================================

import os
import json
import subprocess
from datetime import datetime
from typing import Dict

import google.generativeai as genai
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

# ================== ENV ==================


# ================== ENV ==================

TELEGRAM_TOKEN = "7716174545:AAHJbYiQOUTWdyCEgOq_1ZT-lew1UP_z9UM"
TELEGRAM_CHAT_ID = "7134256288"
GEMINI_API_KEY = "AIzaSyCqLitiUxASbBVDVJa0whABi3LkB2r6zxc"

if not all([TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, GEMINI_API_KEY]):
    raise Exception("Configure as variáveis de ambiente corretamente")

# ================== GEMINI ==================

genai.configure(api_key=GEMINI_API_KEY)
LLM = genai.GenerativeModel("gemini-1.5-flash")

# ================== PATHS ==================

WORKSPACE = "./workspace"
MEMORY_FILE = "./memory.json"

os.makedirs(WORKSPACE, exist_ok=True)

# ================== MEMORY ==================

def load_memory():
    if not os.path.exists(MEMORY_FILE):
        return []
    return json.load(open(MEMORY_FILE, "r", encoding="utf-8"))

def save_memory(data):
    mem = load_memory()
    mem.append(data)
    json.dump(mem, open(MEMORY_FILE, "w", encoding="utf-8"), indent=2)

# ================== FILE SYSTEM ==================

def safe_path(path):
    full = os.path.abspath(os.path.join(WORKSPACE, path))
    if not full.startswith(os.path.abspath(WORKSPACE)):
        raise PermissionError("Acesso negado")
    return full

def write_file(path, content):
    full = safe_path(path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(content)

# ================== EXECUTOR ==================

def run_python(path):
    full = safe_path(path)
    try:
        r = subprocess.run(
            ["python", full],
            capture_output=True,
            text=True,
            timeout=6
        )
        return r.stdout, r.stderr
    except Exception as e:
        return "", str(e)

# ================== AGENTS ==================

class CreatorAgent:
    def create(self, description):
        prompt = f"""
Você é um desenvolvedor senior.
Crie um projeto Python completo baseado nisso:
{description}

Regras:
- Código limpo
- main.py obrigatório
- Testes básicos
- SQLite como banco padrão
"""
        return LLM.generate_content(prompt).text

class ArchitectAgent:
    def review(self, code):
        prompt = f"""
Analise o código abaixo.
Verifique:
- Segurança
- Organização
- Boas práticas
Responda apenas: APROVADO ou REPROVADO e motivo.

{code}
"""
        return LLM.generate_content(prompt).text

class TestAgent:
    def test(self, project):
        return run_python(f"{project}/main.py")

# ================== ORCHESTRATOR ==================

class AutoDevAI:
    def __init__(self):
        self.creator = CreatorAgent()
        self.architect = ArchitectAgent()
        self.tester = TestAgent()

    def build_project(self, name, description):
        code = self.creator.create(description)

        review = self.architect.review(code)
        if "REPROVADO" in review:
            return f"❌ Arquitetura reprovada:\n{review}"

        write_file(f"{name}/main.py", code)

        out, err = self.tester.test(name)

        save_memory({
            "project": name,
            "review": review,
            "output": out,
            "error": err,
            "time": datetime.now().isoformat()
        })

        return f"✅ Projeto criado\n\n📤 Saída:\n{out}\n⚠️ Erros:\n{err}"

# ================== TELEGRAM ==================

AI = AutoDevAI()

async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_chat.id) != TELEGRAM_CHAT_ID:
        return

    text = update.message.text

    if text.startswith("/criar"):
        _, name = text.split(maxsplit=1)
        msg = AI.build_project(
            name=name,
            description="Sistema backend Python autoevolutivo"
        )
        await update.message.reply_text(msg)
    else:
        await update.message.reply_text(
            "Use /criar nome_do_projeto"
        )

# ================== MAIN ==================

if __name__ == "__main__":
    from http.server import BaseHTTPRequestHandler, HTTPServer
    import threading

    def keep_alive():
        port = int(os.environ.get("PORT", 10000))
        server = HTTPServer(("0.0.0.0", port), BaseHTTPRequestHandler)
        server.serve_forever()

    threading.Thread(target=keep_alive, daemon=True).start()
        app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
        app.add_handler(MessageHandler(filters.TEXT, handler))
        print("🤖 AutoDev AI rodando...")
    app.run_polling()

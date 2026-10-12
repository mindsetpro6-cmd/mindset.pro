import os
import secrets
import base64
from pathlib import Path
from datetime import datetime, timedelta, timezone
from html import escape

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field
from google import genai

from backend.database import (
    criar_tabelas,
    criar_utilizador,
    obter_utilizador_por_email,
    confirmar_email,
)

from backend.supabase_client import obter_cliente_supabase


# ============================================================
# CONFIGURAÇÃO DA APLICAÇÃO
# ============================================================

app = FastAPI(
    title="MINDSET PRO API",
    description="Backend oficial do MINDSET PRO",
    version="1.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


# ============================================================
# CAMINHOS E CONFIGURAÇÕES
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

LOGO_PATH = BASE_DIR.parent / "assets" / "logo.jpeg"

VERIFY_BASE_URL = os.getenv(
    "VERIFY_BASE_URL",
    "https://mindset-pro.onrender.com/verify-email",
)

RESEND_API_KEY = os.getenv("RESEND_API_KEY")

RESEND_FROM_EMAIL = os.getenv(
    "RESEND_FROM_EMAIL",
    "MINDSET PRO <onboarding@resend.dev>",
)


# ============================================================
# MODELOS
# ============================================================

class ChatRequest(BaseModel):
    message: str = Field(
        min_length=1,
        max_length=10000,
    )


class ChatResponse(BaseModel):
    response: str


class RegisterRequest(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)
    tipo: str = "ALUNO"
    classe: str | None = None


# ============================================================
# TOKENS DE CONFIRMAÇÃO DE EMAIL
# ============================================================

verification_tokens = {}


# Inicializa a base de dados local existente.
criar_tabelas()


# ============================================================
# GEMINI — MINDSET AI
# ============================================================

def get_client():
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY não configurada no servidor."
        )

    return genai.Client(api_key=api_key)


# ============================================================
# RESEND — ENVIO DE EMAILS
# ============================================================

def enviar_email_boas_vindas(nome, email, token):
    if not RESEND_API_KEY:
        raise RuntimeError(
            "RESEND_API_KEY não configurada no servidor."
        )

    if not RESEND_FROM_EMAIL:
        raise RuntimeError(
            "RESEND_FROM_EMAIL não configurado."
        )

    if not LOGO_PATH.exists():
        raise RuntimeError(
            f"Logo não encontrado: {LOGO_PATH}"
        )

    import resend

    resend.api_key = RESEND_API_KEY

    confirm_url = f"{VERIFY_BASE_URL}?token={token}"

    nome_html = escape(nome)

    texto = f"""
Olá, {nome}!

É com grande satisfação que te damos as boas-vindas ao MINDSET PRO.

A tua conta foi criada com sucesso.

Para confirmar o teu endereço de email, abre o seguinte endereço:

{confirm_url}

Aprender sem limites. Evoluir sem fronteiras.

Com os melhores cumprimentos,
Kensanny e a sua equipa
MINDSET PRO
""".strip()

    html = f"""
<!DOCTYPE html>
<html lang="pt">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>

<body style="
    margin:0;
    padding:0;
    background:#07111F;
    font-family:Arial,Helvetica,sans-serif;
    color:#ffffff;
">

<table width="100%" cellpadding="0" cellspacing="0"
       style="padding:35px 15px;">
<tr>
<td align="center">

<table width="100%" cellpadding="0" cellspacing="0"
       style="
       max-width:600px;
       background:#101D2E;
       border-radius:18px;
       overflow:hidden;
       color:#ffffff;
       ">

<tr>
<td align="center" style="padding:30px 20px 15px;">

<img src="cid:logo_mindset"
     alt="MINDSET PRO"
     width="120"
     style="display:block;width:120px;height:auto;border-radius:16px;">

<h1 style="margin:20px 0 5px;font-size:28px;">
MINDSET PRO
</h1>

<p style="margin:0;color:#A8B3C2;font-size:14px;">
Aprender sem limites. Evoluir sem fronteiras.
</p>

</td>
</tr>

<tr>
<td style="padding:25px 35px 35px;">

<h2 style="color:#20D67A;font-size:22px;">
Bem-vindo ao MINDSET PRO!
</h2>

<p style="font-size:16px;line-height:1.6;">
Olá, <strong>{nome_html}</strong>,
</p>

<p style="font-size:16px;line-height:1.6;">
A tua conta foi criada com sucesso. O MINDSET PRO foi concebido
para apoiar os estudantes na aprendizagem, na descoberta e na evolução.
</p>

<p style="font-size:16px;line-height:1.6;">
Com o MINDSET AI, poderás esclarecer dúvidas, compreender matérias,
praticar exercícios e desenvolver os teus conhecimentos.
</p>

<div style="
    margin:25px 0;
    padding:18px;
    background:#16263B;
    border-radius:12px;
">
<strong>A tua conta está quase pronta!</strong>
<p style="margin-bottom:0;">
Confirma o teu endereço de email para concluir o processo.
</p>
</div>

<p style="font-size:16px;line-height:1.6;">
Clica no botão abaixo para confirmar a tua conta:
</p>

<p style="text-align:center;margin:30px 0;">

<a href="{confirm_url}"
   style="
   display:inline-block;
   background:#20D67A;
   color:#07111F;
   text-decoration:none;
   padding:15px 28px;
   border-radius:10px;
   font-weight:bold;
   font-size:15px;
   ">
CONFIRMAR A MINHA CONTA
</a>

</p>

<p style="color:#A8B3C2;font-size:13px;line-height:1.5;">
Se não foste tu que criaste esta conta, podes ignorar esta mensagem.
</p>

<p style="
    text-align:center;
    font-weight:bold;
    color:#20D67A;
    margin-top:30px;
">
Aprender sem limites. Evoluir sem fronteiras.
</p>

<p style="font-size:15px;line-height:1.6;">
Com os melhores cumprimentos,<br>
<strong>Kensanny e a sua equipa</strong><br>
MINDSET PRO
</p>

</td>
</tr>
</table>

</td>
</tr>
</table>

</body>
</html>
"""

    with open(LOGO_PATH, "rb") as arquivo:
        imagem = base64.b64encode(
            arquivo.read()
        ).decode("utf-8")

    resposta = resend.Emails.send({
        "from": RESEND_FROM_EMAIL,
        "to": [email],
        "subject": "Bem-vindo ao MINDSET PRO",
        "text": texto,
        "html": html,
        "attachments": [
            {
                "filename": "logo.jpeg",
                "content": imagem,
                "content_id": "logo_mindset",
            }
        ],
    })

    print("Email enviado pelo Resend:", resposta)


# ============================================================
# ROTAS PRINCIPAIS
# ============================================================

@app.get("/")
def root():
    return {
        "status": "online",
        "service": "MINDSET PRO API",
        "version": app.version,
    }


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "MINDSET PRO API",
    }


# ============================================================
# SUPABASE — TESTE DE LIGAÇÃO
# ============================================================

@app.get("/health/supabase")
def health_supabase():
    try:
        cliente = obter_cliente_supabase()

        # Verifica a comunicação com o Storage.
        buckets = cliente.storage.list_buckets()

        return {
            "status": "ok",
            "supabase": "conectado",
            "storage": "acessível",
            "buckets": len(buckets),
        }

    except Exception as erro:
        print(
            "ERRO SUPABASE:",
            type(erro).__name__,
            str(erro)[:300],
        )

        raise HTTPException(
            status_code=503,
            detail=(
                "Não foi possível verificar a ligação "
                "ao Supabase. Consulta os logs do servidor."
            ),
        )


# ============================================================
# DIAGNÓSTICO DO RESEND
# ============================================================

@app.get("/debug/resend")
def debug_resend():
    try:
        import resend

        if not RESEND_API_KEY:
            return {
                "status": "erro",
                "motivo": "RESEND_API_KEY ausente",
            }

        resend.api_key = RESEND_API_KEY

        resend.ApiKeys.list()

        return {
            "status": "ok",
            "resend_respondeu": True,
        }

    except Exception as erro:
        print(
            "ERRO RESEND:",
            type(erro).__name__,
            str(erro)[:300],
        )

        return {
            "status": "erro",
            "resend_respondeu": False,
            "tipo_erro": type(erro).__name__,
        }


@app.get("/debug/resend-email")
def debug_resend_email():
    try:
        import resend

        if not RESEND_API_KEY:
            return {
                "status": "erro",
                "motivo": "RESEND_API_KEY ausente",
            }

        resend.api_key = RESEND_API_KEY

        resposta = resend.Emails.send({
            "from": RESEND_FROM_EMAIL,
            "to": ["mindset.pro6@gmail.com"],
            "subject": "Teste Resend — MINDSET PRO",
            "text": (
                "Este é um email de teste do MINDSET PRO."
            ),
            "html": (
                "<h2>Teste Resend — MINDSET PRO</h2>"
                "<p>O envio de email está a funcionar.</p>"
            ),
        })

        print("TESTE RESEND:", resposta)

        return {
            "status": "enviado",
            "resend_respondeu": True,
        }

    except Exception as erro:
        print(
            "ERRO TESTE RESEND:",
            type(erro).__name__,
            str(erro)[:300],
        )

        raise HTTPException(
            status_code=500,
            detail="Não foi possível enviar o email de teste.",
        )


# ============================================================
# REGISTO DE UTILIZADORES
# ============================================================

@app.post("/register")
def register(request: RegisterRequest):
    nome = request.name.strip()
    email = str(request.email).strip().lower()
    password = request.password
    tipo = request.tipo.strip().upper()
    classe = request.classe.strip() if request.classe else None

    tipos_permitidos = {
        "ALUNO",
        "ALUNO DA COMISSÃO",
    }

    if tipo not in tipos_permitidos:
        raise HTTPException(
            status_code=400,
            detail="Tipo de conta inválido.",
        )

    if len(nome) < 2:
        raise HTTPException(
            status_code=400,
            detail="Nome inválido.",
        )

    if not classe:
        raise HTTPException(
            status_code=400,
            detail="A classe é obrigatória.",
        )

    if len(password) < 6:
        raise HTTPException(
            status_code=400,
            detail="A senha deve ter pelo menos 6 caracteres.",
        )

    if obter_utilizador_por_email(email):
        raise HTTPException(
            status_code=400,
            detail="Este email já está registado.",
        )

    id_utilizador = criar_utilizador(
        nome=nome,
        email=email,
        password=password,
        tipo=tipo,
        classe=classe,
        email_confirmado=False,
    )

    if not id_utilizador:
        raise HTTPException(
            status_code=400,
            detail="Não foi possível criar a conta.",
        )

    token = secrets.token_urlsafe(32)

    verification_tokens[token] = {
        "name": nome,
        "email": email,
        "created_at": datetime.now(timezone.utc),
    }

    try:
        enviar_email_boas_vindas(
            nome,
            email,
            token,
        )

    except Exception as erro:
        verification_tokens.pop(token, None)

        # Reverte o registo caso o envio do email falhe.
        from backend.database import conectar

        conn = conectar()

        try:
            conn.execute(
                "DELETE FROM utilizadores WHERE id = ?",
                (id_utilizador,),
            )
            conn.commit()
        finally:
            conn.close()

        print(
            "ERRO EMAIL:",
            type(erro).__name__,
            str(erro)[:300],
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Não foi possível enviar o email de confirmação."
            ),
        )

    return {
        "status": "ok",
        "message": "Conta criada. Verifica o teu email.",
        "email": email,
    }


# ============================================================
# CONFIRMAÇÃO DE EMAIL
# ============================================================

@app.get("/verify-email")
def verify_email(token: str):
    dados = verification_tokens.get(token)

    if not dados:
        raise HTTPException(
            status_code=400,
            detail="Link de confirmação inválido ou expirado.",
        )

    criado = dados["created_at"]

    if (
        datetime.now(timezone.utc) - criado
        > timedelta(hours=24)
    ):
        verification_tokens.pop(token, None)

        raise HTTPException(
            status_code=400,
            detail="Link de confirmação expirado.",
        )

    # Confirma primeiro na base de dados.
    confirmar_email(dados["email"])

    verification_tokens.pop(token, None)

    return {
        "status": "confirmed",
        "message": "Email confirmado com sucesso.",
        "email": dados["email"],
    }


# ============================================================
# MINDSET AI — GEMINI
# ============================================================

@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    mensagem = request.message.strip()

    if not mensagem:
        raise HTTPException(
            status_code=400,
            detail="Mensagem vazia.",
        )

    try:
        client = get_client()

        response = client.models.generate_content(
            model=os.getenv(
                "GEMINI_MODEL",
                "gemini-3.7-flash",
            ),
            contents=(
                "Tu és o MINDSET AI, o assistente inteligente "
                "do aplicativo MINDSET PRO. "
                "Responde em português, de forma clara, "
                "útil e natural. "
                "Quando explicares assuntos escolares, "
                "ensina passo a passo e apresenta exemplos. "
                "Não inventes informações quando não tiveres "
                "certeza. "
                "Ajuda o estudante a compreender a matéria, "
                "em vez de apenas apresentar respostas.\n\n"
                f"Utilizador: {mensagem}"
            ),
        )

        texto = getattr(response, "text", None)

        if not texto or not texto.strip():
            raise RuntimeError(
                "O Gemini não retornou texto."
            )

        return ChatResponse(
            response=texto.strip(),
        )

    except HTTPException:
        raise

    except Exception as erro:
        print(
            "ERRO GEMINI:",
            type(erro).__name__,
            str(erro)[:300],
        )

        raise HTTPException(
            status_code=500,
            detail="Erro ao processar a mensagem.",
        )

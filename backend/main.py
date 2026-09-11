import os
import ssl
import smtplib
import secrets
import mimetypes
from pathlib import Path
from email.message import EmailMessage
from datetime import datetime, timedelta, timezone

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from google import genai


app = FastAPI(
    title="MINDSET PRO API",
    version="1.1.0"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)


# ============================================================
# CONFIGURAÇÃO
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
LOGO_PATH = BASE_DIR.parent / "assets" / "logo.jpeg"

GMAIL_USER = os.getenv("GMAIL_USER")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")

VERIFY_BASE_URL = os.getenv(
    "VERIFY_BASE_URL",
    "https://mindset-pro-api.onrender.com/verify-email"
)


# ============================================================
# MODELOS
# ============================================================

class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    response: str


class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str


# ============================================================
# MEMÓRIA TEMPORÁRIA DE CONFIRMAÇÕES
# ============================================================

verification_tokens = {}


# ============================================================
# GEMINI
# ============================================================

def get_client():
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY não configurada no servidor."
        )

    return genai.Client(
        api_key=api_key
    )


# ============================================================
# EMAIL
# ============================================================

def enviar_email_boas_vindas(nome, email, token):

    if not GMAIL_USER or not GMAIL_APP_PASSWORD:
        raise RuntimeError(
            "GMAIL_USER ou GMAIL_APP_PASSWORD não configurado."
        )

    if not LOGO_PATH.exists():
        raise RuntimeError(
            f"Logo não encontrado: {LOGO_PATH}"
        )

    confirm_url = f"{VERIFY_BASE_URL}?token={token}"

    mensagem = EmailMessage()

    mensagem["Subject"] = "Bem-vindo ao MINDSET PRO"
    mensagem["From"] = f"MINDSET PRO <{GMAIL_USER}>"
    mensagem["To"] = email

    mensagem.set_content(
        f"""
Olá, {nome}!

É com grande satisfação que te damos as boas-vindas ao MINDSET PRO.

A tua conta foi criada com sucesso.

Para confirmar que este endereço de email te pertence, abre o seguinte endereço:

{confirm_url}

Depois da confirmação, poderás continuar a utilizar o MINDSET PRO normalmente.

Aprender sem limites. Evoluir sem fronteiras.

Com os melhores cumprimentos,
Kensanny e a sua equipa
MINDSET PRO
""".strip()
    )

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
">

<table width="100%" cellpadding="0" cellspacing="0" style="padding:35px 15px;">
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
     style="
     display:block;
     width:120px;
     height:auto;
     border-radius:16px;
     ">

<h1 style="
    margin:20px 0 5px;
    font-size:28px;
    color:#ffffff;
">
MINDSET PRO
</h1>

<p style="
    margin:0;
    color:#A8B3C2;
    font-size:14px;
">
Aprender sem limites. Evoluir sem fronteiras.
</p>

</td>
</tr>

<tr>
<td style="padding:25px 35px 35px;">

<h2 style="
    color:#20D67A;
    font-size:22px;
    margin-top:0;
">
Bem-vindo ao MINDSET PRO!
</h2>

<p style="font-size:16px; line-height:1.6;">
Olá, <strong>{nome}</strong>,
</p>

<p style="font-size:16px; line-height:1.6;">
É com grande satisfação que te damos as boas-vindas ao
<strong>MINDSET PRO</strong>, uma plataforma criada para apoiar
estudantes na aprendizagem, na descoberta e na evolução.
</p>

<p style="font-size:16px; line-height:1.6;">
A partir de agora, tens acesso ao
<strong>MINDSET AI</strong>, o assistente inteligente do MINDSET PRO,
preparado para ajudar-te a compreender matérias, esclarecer dúvidas,
estudar, praticar e desenvolver os teus conhecimentos.
</p>

<div style="
    margin:25px 0;
    padding:18px;
    background:#16263B;
    border-radius:12px;
">
<p style="
    margin:0;
    font-size:16px;
    line-height:1.5;
">
<strong>A tua conta foi criada com sucesso.</strong>
</p>
</div>

<p style="font-size:16px; line-height:1.6;">
Para confirmar que este endereço de email te pertence,
utiliza o botão abaixo:
</p>

<p style="text-align:center; margin:30px 0;">

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

<p style="
    color:#A8B3C2;
    font-size:13px;
    line-height:1.5;
">
Se não foste tu que criaste esta conta, podes ignorar esta mensagem.
</p>

<p style="
    font-size:16px;
    line-height:1.6;
    margin-top:30px;
">
Estamos a construir uma plataforma para tornar a aprendizagem
mais acessível, inteligente e dinâmica.
</p>

<p style="
    text-align:center;
    font-weight:bold;
    color:#20D67A;
    margin-top:30px;
">
Aprender sem limites. Evoluir sem fronteiras.
</p>

<p style="font-size:15px; line-height:1.6;">
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

    mensagem.add_alternative(html, subtype="html")

    with open(LOGO_PATH, "rb") as arquivo:
        imagem = arquivo.read()

    tipo, _ = mimetypes.guess_type(str(LOGO_PATH))

    if not tipo:
        tipo = "image/jpeg"

    maintype, subtype = tipo.split("/", 1)

    mensagem.get_payload()[1].add_related(
        imagem,
        maintype=maintype,
        subtype=subtype,
        cid="<logo_mindset>",
        filename="logo.jpeg"
    )

    contexto = ssl.create_default_context()

    with smtplib.SMTP_SSL(
        "smtp.gmail.com",
        465,
        context=contexto,
        timeout=30
    ) as servidor:

        servidor.login(
            GMAIL_USER,
            GMAIL_APP_PASSWORD
        )

        servidor.send_message(mensagem)


# ============================================================
# ROTAS BÁSICAS
# ============================================================

@app.get("/")
def root():
    return {
        "status": "online",
        "service": "MINDSET PRO API"
    }


@app.get("/health")
def health():
    return {
        "status": "ok"
    }


# ============================================================
# REGISTO
# ============================================================

@app.post("/register")
def register(request: RegisterRequest):

    nome = request.name.strip()
    email = str(request.email).strip().lower()
    password = request.password

    if len(nome) < 2:
        raise HTTPException(
            status_code=400,
            detail="Nome inválido."
        )

    if len(password) < 6:
        raise HTTPException(
            status_code=400,
            detail="A senha deve ter pelo menos 6 caracteres."
        )

    token = secrets.token_urlsafe(32)

    verification_tokens[token] = {
        "name": nome,
        "email": email,
        "created_at": datetime.now(timezone.utc)
    }

    try:

        enviar_email_boas_vindas(
            nome,
            email,
            token
        )

    except Exception as erro:

        verification_tokens.pop(token, None)

        print(
            "ERRO EMAIL:",
            repr(erro)
        )

        raise HTTPException(
            status_code=500,
            detail="Não foi possível enviar o email de confirmação."
        )

    return {
        "status": "ok",
        "message": "Conta criada. Verifica o teu email.",
        "email": email
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
            detail="Link de confirmação inválido ou expirado."
        )

    criado = dados["created_at"]

    if datetime.now(timezone.utc) - criado > timedelta(hours=24):

        verification_tokens.pop(token, None)

        raise HTTPException(
            status_code=400,
            detail="Link de confirmação expirado."
        )

    verification_tokens.pop(token, None)

    return {
        "status": "confirmed",
        "message": "Email confirmado com sucesso.",
        "email": dados["email"]
    }


# ============================================================
# GEMINI
# ============================================================

@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):

    mensagem = request.message.strip()

    if not mensagem:
        raise HTTPException(
            status_code=400,
            detail="Mensagem vazia."
        )

    if len(mensagem) > 10000:
        raise HTTPException(
            status_code=400,
            detail="Mensagem demasiado longa."
        )

    try:

        client = get_client()

        response = client.models.generate_content(
            model="gemini-3.7-flash",
            contents=(
                "Tu és o MINDSET AI, assistente inteligente "
                "do aplicativo MINDSET PRO. "
                "Responde em português de forma clara, "
                "útil e natural. "
                "Quando explicares assuntos escolares, "
                "ensina passo a passo. "
                "Não inventes informações quando não tiveres "
                "certeza.\n\n"
                f"Utilizador: {mensagem}"
            ),
        )

        texto = getattr(response, "text", None)

        if not texto:
            raise RuntimeError(
                "O Gemini não retornou texto."
            )

        return ChatResponse(
            response=texto.strip()
        )

    except HTTPException:
        raise

    except Exception as erro:

        print(
            "ERRO GEMINI:",
            repr(erro)
        )

        raise HTTPException(
            status_code=500,
            detail="Erro ao processar a mensagem."
        )

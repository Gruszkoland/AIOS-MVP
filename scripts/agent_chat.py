"""
ADRION 369 — Chainlit Agent Chat
=================================
Uruchomienie:  pip install chainlit httpx   &&   chainlit run agent_chat.py
Wymagania:     Python 3.11+, opcjonalnie psycopg2 dla historii z PostgreSQL

Funkcje:
  - Selector agenta (Vortex-MCP, Guardian-MCP, Oracle-MCP, Genesis-MCP, Healer-MCP)
  - Każde zapytanie jest routowane HTTP POST do wybranego endpointu MCP
  - Kroki rozumowania widoczne przez cl.Step()
  - Historia sesji przechowywana w pamięci (opcjonalnie PostgreSQL)
  - Fallback do mocka gdy serwis niedostępny
"""

from __future__ import annotations

import os
import json
import time
import random
import textwrap
from typing import Any

import httpx
import chainlit as cl

# ── Konfiguracja ──────────────────────────────────────────────────────────────

MCP_REGISTRY: dict[str, dict[str, Any]] = {
    "Vortex-MCP":   {"port": 9001, "model": "GPT-4o",      "icon": "⚡"},
    "Guardian-MCP": {"port": 9002, "model": "Claude-3.7",  "icon": "🛡️"},
    "Oracle-MCP":   {"port": 9003, "model": "Mistral-L",   "icon": "🔮"},
    "Genesis-MCP":  {"port": 9004, "model": "GPT-4o-mini", "icon": "🌱"},
    "Healer-MCP":   {"port": 9005, "model": "Llama-3.3",   "icon": "💚"},
}

DEFAULT_AGENT = "Vortex-MCP"
HTTP_TIMEOUT  = float(os.getenv("MCP_TIMEOUT_S", "8"))

# ── Pomocnicze ────────────────────────────────────────────────────────────────

def _agent_url(name: str) -> str:
    port = MCP_REGISTRY[name]["port"]
    return f"http://localhost:{port}"


def _demo_response(agent: str, prompt: str) -> dict[str, Any]:
    """Odpowiedź mocka gdy serwis niedostępny."""
    steps = [
        f"[DEMO] Odebrano prompt ({len(prompt)} znaków)",
        "[DEMO] Wyszukuję w bazie wiedzy…",
        "[DEMO] Formułuję odpowiedź…",
    ]
    answer = textwrap.dedent(f"""
        ⚠️ **{agent} jest niedostępny** (tryb demo)

        Twoje zapytanie zostało odebrane:
        > {prompt[:120]}{"…" if len(prompt) > 120 else ""}

        W trybie produkcyjnym agent przetworzyłby je krok po kroku.
        Uruchom stack `docker compose up` aby połączyć się z prawdziwymi agentami.
    """).strip()
    return {"steps": steps, "answer": answer, "demo": True}


async def _call_mcp(agent: str, prompt: str, history: list[dict]) -> dict[str, Any]:
    """Wywołuje wybrany serwer MCP. Przy błędzie zwraca demo."""
    url  = _agent_url(agent)
    body = {
        "prompt":  prompt,
        "history": history[-10:],   # ostatnie 10 wiadomości jako kontekst
        "stream":  False,
    }
    try:
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
            resp = await client.post(f"{url}/v1/chat", json=body)
            resp.raise_for_status()
            data = resp.json()
            return {
                "steps":  data.get("steps", []),
                "answer": data.get("answer") or data.get("content") or str(data),
                "demo":   False,
            }
    except Exception as exc:  # noqa: BLE001
        cl.logger.warning("MCP call failed (%s): %s", agent, exc)
        return _demo_response(agent, prompt)


# ── Chat Settings (selektor agenta) ───────────────────────────────────────────

@cl.set_chat_profiles
async def chat_profiles() -> list[cl.ChatProfile]:
    return [
        cl.ChatProfile(
            name=name,
            markdown_description=f"**{meta['icon']} {name}** ({meta['model']}) — port {meta['port']}",
            icon=f"https://api.iconify.design/mdi/robot.svg",
        )
        for name, meta in MCP_REGISTRY.items()
    ]


# ── Inicjalizacja sesji ───────────────────────────────────────────────────────

@cl.on_chat_start
async def on_chat_start() -> None:
    profile = cl.user_session.get("chat_profile") or DEFAULT_AGENT
    meta    = MCP_REGISTRY.get(profile, MCP_REGISTRY[DEFAULT_AGENT])

    cl.user_session.set("agent",   profile)
    cl.user_session.set("history", [])

    # Sprawdź zdrowie agenta
    try:
        async with httpx.AsyncClient(timeout=3) as c:
            r = await c.get(f"{_agent_url(profile)}/health")
        status = "🟢 online" if r.status_code == 200 else "🟡 degraded"
    except Exception:
        status = "🔴 offline (tryb demo)"

    await cl.Message(
        content=(
            f"## {meta['icon']} {profile}\n"
            f"Model: **{meta['model']}** | Status: **{status}**\n\n"
            "Możesz teraz wysyłać polecenia do tego agenta.\n"
            "Wpisz `/switch <NazwaAgenta>` aby zmienić agenta w trakcie rozmowy."
        ),
        author="System",
    ).send()


# ── Obsługa wiadomości ────────────────────────────────────────────────────────

@cl.on_message
async def on_message(message: cl.Message) -> None:
    agent: str       = cl.user_session.get("agent") or DEFAULT_AGENT
    history: list    = cl.user_session.get("history") or []
    prompt: str      = message.content.strip()

    # Komenda /switch
    if prompt.lower().startswith("/switch"):
        parts   = prompt.split(maxsplit=1)
        new_agent = parts[1].strip() if len(parts) > 1 else ""
        if new_agent in MCP_REGISTRY:
            cl.user_session.set("agent", new_agent)
            cl.user_session.set("history", [])
            meta = MCP_REGISTRY[new_agent]
            await cl.Message(
                content=f"Przełączono na {meta['icon']} **{new_agent}** ({meta['model']}). Historia wyczyszczona.",
                author="System",
            ).send()
        else:
            available = ", ".join(MCP_REGISTRY.keys())
            await cl.Message(
                content=f"Nieznany agent. Dostępne: {available}",
                author="System",
            ).send()
        return

    # Dodaj wiadomość użytkownika do historii
    history.append({"role": "user", "content": prompt})

    # Krok 1 — routing
    async with cl.Step(name="🔀 Router", type="tool") as step:
        step.input = f"Agent: {agent} | Prompt length: {len(prompt)}"
        await cl.sleep(0.1)  # visual pause
        step.output = f"Routing to {agent} (port {MCP_REGISTRY[agent]['port']})"

    # Krok 2 — wywołanie MCP
    async with cl.Step(name=f"🤖 {agent}", type="llm") as step:
        step.input = prompt[:500]
        t0   = time.monotonic()
        data = await _call_mcp(agent, prompt, history)
        elapsed = time.monotonic() - t0

        # Pokaż sub-kroki rozumowania jeśli agent je zwrócił
        for i, s in enumerate(data.get("steps", []), 1):
            async with cl.Step(name=f"  Step {i}", type="run") as sub:
                sub.output = str(s)

        step.output = (
            f"Czas odpowiedzi: {elapsed:.2f}s"
            + (" [DEMO]" if data.get("demo") else "")
        )

    # Krok 3 — wyślij odpowiedź
    answer: str = data["answer"]
    await cl.Message(content=answer, author=agent).send()

    # Zaktualizuj historię
    history.append({"role": "assistant", "content": answer})
    cl.user_session.set("history", history[-40:])   # max 40 wiadomości


# ── Obsługa rozłączenia ───────────────────────────────────────────────────────

@cl.on_chat_end
async def on_chat_end() -> None:
    cl.logger.info("Sesja zakończona dla agenta: %s", cl.user_session.get("agent"))

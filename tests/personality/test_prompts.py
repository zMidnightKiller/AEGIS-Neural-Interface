"""
tests/personality/test_prompts.py

Testes unitarios para o gerador de prompts da AEGIS.
"""
import pytest
from aegis.personality.modes import OperatingMode
from aegis.personality.prompts import build_system_prompt


def test_build_system_prompt_standard():
    prompt = build_system_prompt(mode=OperatingMode.STANDARD)
    assert "AEGIS" in prompt
    assert "STANDARD" in prompt
    assert "Mantenha um equilibrio" in prompt


def test_build_system_prompt_briefing():
    prompt = build_system_prompt(mode=OperatingMode.BRIEFING)
    assert "BRIEFING" in prompt
    assert "ultra-conciso" in prompt
    standard_prompt = build_system_prompt(mode=OperatingMode.STANDARD)
    assert prompt != standard_prompt


def test_build_system_prompt_analysis():
    prompt = build_system_prompt(mode=OperatingMode.ANALYSIS)
    assert "ANALYSIS" in prompt
    assert "raciocinio estendido" in prompt


def test_build_system_prompt_with_tools():
    tools = [{"name": "web_search", "description": "Busca na web"}]
    prompt = build_system_prompt(tools_list=tools)
    assert "FERRAMENTAS DISPONIVEIS" in prompt
    assert "web_search" in prompt


def test_build_system_prompt_with_context():
    memory = "O usuario prefere cafe sem acucar."
    prompt = build_system_prompt(memory_context=memory)
    assert "CONTEXTO DE MEMORIA" in prompt
    assert memory in prompt

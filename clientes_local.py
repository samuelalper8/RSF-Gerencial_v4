import json
import os
import streamlit as st

ARQUIVO_CLIENTES = "clientes_base.json"

def carregar_clientes() -> list[dict]:
    """Lê o arquivo JSON e retorna a lista de clientes."""
    if not os.path.exists(ARQUIVO_CLIENTES):
        return []
    try:
        with open(ARQUIVO_CLIENTES, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return []

def salvar_clientes(clientes: list[dict]):
    """Grava a lista de clientes no arquivo JSON."""
    with open(ARQUIVO_CLIENTES, "w", encoding="utf-8") as f:
        json.dump(clientes, f, indent=4, ensure_ascii=False)

def listar_clientes() -> list[dict]:
    """Retorna a base de clientes ordenada alfabeticamente."""
    clientes = carregar_clientes()
    return sorted(clientes, key=lambda x: x["nome"].upper())

def cadastrar_cliente(cnpj: str, nome: str) -> bool:
    """Cadastra um novo município/entidade verificando duplicidade."""
    clientes = carregar_clientes()
    
    if any(c["cnpj"] == cnpj for c in clientes):
        st.warning(f"CNPJ {cnpj} já está cadastrado na base.")
        return False
        
    clientes.append({"cnpj": cnpj, "nome": nome})
    salvar_clientes(clientes)
    return True

def remover_cliente(cnpj: str) -> bool:
    """Exclui o cliente da base pelo CNPJ."""
    clientes = carregar_clientes()
    clientes_filtrados = [c for c in clientes if c["cnpj"] != cnpj]
    
    if len(clientes) != len(clientes_filtrados):
        salvar_clientes(clientes_filtrados)
        return True
    return False

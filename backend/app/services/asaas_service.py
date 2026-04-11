import httpx
import os
from uuid import UUID
from datetime import date
from decimal import Decimal
from typing import Optional, Dict, Any
from app.core.config import settings

ASAAS_API_URL = "https://api.asaas.com/v3"
ASAAS_API_KEY = os.getenv("ASAAS_API_KEY", "")

headers = {
    "access_token": ASAAS_API_KEY,
    "Content-Type": "application/json"
}


class AsaasError(Exception):
    pass


async def criar_cobranca_pix(
    customer_id: str,
    amount: Decimal,
    description: str,
    due_date: Optional[date] = None
) -> Dict[str, Any]:
    """Cria cobrança Pix no Asaas"""
    if not ASAAS_API_KEY:
        raise AsaasError("ASAAS_API_KEY não configurada")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{ASAAS_API_URL}/payments",
                headers=headers,
                json={
                    "customer": customer_id,
                    "billingType": "PIX",
                    "value": float(amount),
                    "dueDate": due_date.isoformat() if due_date else date.today().isoformat(),
                    "description": description[:200]
                },
                timeout=30.0
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "id": data.get("id"),
                    "url": data.get("url"),
                    "pix_qr_code": data.get("pixQrCode"),
                    "pix_code": data.get("pixCode"),
                    "status": data.get("status"),
                    "value": data.get("value"),
                    "due_date": data.get("dueDate")
                }
            else:
                raise AsaasError(f"Erro ao criar cobrança: {response.text}")
        except httpx.RequestError as e:
            raise AsaasError(f"Erro na requisição: {str(e)}")


async def verificar_status_cobranca(charge_id: str) -> Dict[str, Any]:
    """Verifica status de uma cobrança"""
    if not ASAAS_API_KEY:
        raise AsaasError("ASAAS_API_KEY não configurada")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{ASAAS_API_URL}/payments/{charge_id}",
                headers=headers,
                timeout=15.0
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "id": data.get("id"),
                    "status": data.get("status"),
                    "value": data.get("value"),
                    "payment_date": data.get("paymentDate")
                }
            else:
                raise AsaasError(f"Erro ao verificar: {response.text}")
        except httpx.RequestError as e:
            raise AsaasError(f"Erro na requisição: {str(e)}")


async def criar_customer(
    name: str,
    email: str,
    cpf_cnpj: Optional[str] = None,
    phone: Optional[str] = None
) -> Dict[str, Any]:
    """Cria cliente no Asaas"""
    if not ASAAS_API_KEY:
        raise AsaasError("ASAAS_API_KEY não configurada")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{ASAAS_API_URL}/customers",
                headers=headers,
                json={
                    "name": name,
                    "email": email,
                    "cpfCnpj": cpf_cnpj,
                    "phone": phone
                },
                timeout=30.0
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "id": data.get("id"),
                    "name": data.get("name"),
                    "email": data.get("email")
                }
            else:
                raise AsaasError(f"Erro ao criar cliente: {response.text}")
        except httpx.RequestError as e:
            raise AsaasError(f"Erro na requisição: {str(e)}")


async def buscar_customer_por_cpf(cpf: str) -> Optional[Dict[str, Any]]:
    """Busca cliente por CPF"""
    if not ASAAS_API_KEY:
        return None
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{ASAAS_API_URL}/customers",
                headers=headers,
                params={"cpfCnpj": cpf},
                timeout=15.0
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("totalCount", 0) > 0:
                    return data.get("data", [])[0]
            return None
        except httpx.RequestError:
            return None
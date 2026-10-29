"""DocuSign eSignature REST API Integration Service.

Handles:
- JWT Bearer Token Authentication (RS256)
- 6-Page KA Rentals Agreement Document Generation (with Statement of Liability)
- Envelope Creation & Dispatch to Driver's Email
- Live Envelope Status Tracking
- Webhook (DocuSign Connect) Signature Event Processing
"""

import base64
from datetime import datetime, timezone
import logging
import os
import time
from typing import Any, Dict, Optional
import httpx
import jwt
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.entities import Contract, Customer, Vehicle

logger = logging.getLogger(__name__)

# Token Cache
_cached_token: Optional[str] = None
_token_expires_at: float = 0.0


def _get_env_config() -> Dict[str, str]:
    """Retrieves DocuSign configuration from environment."""
    private_key = os.getenv("DOCUSIGN_PRIVATE_KEY", "")
    if "\\n" in private_key and "\n" not in private_key:
        private_key = private_key.replace("\\n", "\n")

    return {
        "account_id": os.getenv("DOCUSIGN_ACCOUNT_ID", ""),
        "client_id": os.getenv("DOCUSIGN_INTEGRATION_KEY", ""),
        "user_id": os.getenv("DOCUSIGN_USER_ID", ""),
        "auth_server": os.getenv("DOCUSIGN_AUTH_SERVER", "account-d.docusign.com"),
        "base_url": os.getenv("DOCUSIGN_BASE_URL", "https://demo.docusign.net/restapi"),
        "private_key": private_key,
    }


def get_docusign_access_token() -> str:
    """Generates and caches a DocuSign OAuth JWT Bearer Access Token."""
    global _cached_token, _token_expires_at
    now = time.time()

    # Reuse cached token if valid for at least 5 more minutes
    if _cached_token and now < (_token_expires_at - 300):
        return _cached_token

    config = _get_env_config()
    if not (config["client_id"] and config["user_id"] and config["private_key"]):
        raise ValueError("DocuSign credentials missing in environment variables.")

    now_int = int(now)
    jwt_claims = {
        "iss": config["client_id"],
        "sub": config["user_id"],
        "aud": config["auth_server"],
        "iat": now_int,
        "exp": now_int + 3600,
        "scope": "signature impersonation",
    }

    signed_jwt = jwt.encode(jwt_claims, config["private_key"], algorithm="RS256")

    token_url = f"https://{config['auth_server']}/oauth/token"
    res = httpx.post(
        token_url,
        data={
            "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
            "assertion": signed_jwt,
        },
        timeout=15.0,
    )

    if res.status_code != 200:
        error_info = res.text
        logger.error("DocuSign token exchange failed: %s", error_info)
        raise RuntimeError(f"DocuSign token exchange failed ({res.status_code}): {error_info}")

    data = res.json()
    _cached_token = data["access_token"]
    _token_expires_at = now + data.get("expires_in", 3600)
    logger.info("Successfully acquired fresh DocuSign access token.")
    return _cached_token


def generate_contract_html(
    contract: Contract,
    customer: Optional[Customer] = None,
    vehicle: Optional[Vehicle] = None,
    customer_address: Optional[str] = None,
) -> str:
    """Renders the standard 6-Page KA Rentals Self-Drive Car Hire Agreement."""
    driver_name = customer.full_name if customer else (contract.customer_name_raw or "Driver Unspecified")
    driver_email = customer.email if customer else "N/A"
    driver_phone = customer.phone if customer else "N/A"
    driver_license = customer.driving_license if customer else "N/A"
    reg = contract.vehicle_registration
    model = (vehicle.make_model if vehicle and vehicle.make_model else contract.vehicle_model) or "Vehicle Unspecified"
    rate_str = f"£{contract.rate:.2f} per week" if contract.rate else "As agreed"
    start_str = contract.start_date.strftime("%d/%m/%Y") if contract.start_date else "Upon Delivery"
    end_str = contract.end_date.strftime("%d/%m/%Y") if contract.end_date else "28 days from start"
    agreement_date = datetime.now(timezone.utc).strftime("%d/%m/%Y")

    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>K.A RENTALS LTD CONTRACT - {reg}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #1e293b; line-height: 1.5; padding: 30px; }}
        .header {{ text-align: center; border-bottom: 2px solid #0f172a; padding-bottom: 15px; margin-bottom: 20px; }}
        .header h1 {{ margin: 0; font-size: 24px; color: #0f172a; text-transform: uppercase; letter-spacing: 1px; }}
        .header p {{ margin: 4px 0 0; font-size: 13px; color: #64748b; }}
        .section-title {{ font-size: 14px; font-weight: 700; text-transform: uppercase; color: #0f172a; border-bottom: 1px solid #cbd5e1; padding-bottom: 4px; margin-top: 20px; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 8px; font-size: 13px; }}
        th, td {{ padding: 6px 10px; border: 1px solid #e2e8f0; text-align: left; }}
        th {{ background-color: #f8fafc; font-weight: 600; width: 30%; }}
        .liability-box {{ background-color: #fef2f2; border-left: 4px solid #dc2626; padding: 12px 16px; margin-top: 15px; font-size: 12.5px; color: #991b1b; line-height: 1.6; }}
        .signature-box {{ margin-top: 30px; border: 1px solid #cbd5e1; border-radius: 6px; padding: 20px; background-color: #f8fafc; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>K.A RENTALS LTD</h1>
        <p>Self-Drive Vehicle Hire Agreement • Tel: 0208 1378 200</p>
        <p><strong>Agreement Date:</strong> {agreement_date} | <strong>Contract Ref:</strong> KA-{contract.id}</p>
    </div>

    <div class="section-title">1. Personal & Driver Information</div>
    <table>
        <tr><th>Driver Full Name</th><td>{driver_name}</td></tr>
        <tr><th>Email Address</th><td>{driver_email}</td></tr>
        <tr><th>Contact Phone</th><td>{driver_phone}</td></tr>
        <tr><th>UK Driving License</th><td>{driver_license}</td></tr>
        <tr><th>Address</th><td>{customer_address or 'On file with company'}</td></tr>
    </table>

    <div class="section-title">2. Vehicle Information</div>
    <table>
        <tr><th>Registration Number</th><td><strong style="letter-spacing: 1px;">{reg}</strong></td></tr>
        <tr><th>Make & Model</th><td>{model}</td></tr>
        <tr><th>Hire Type</th><td>Self-Drive Hire</td></tr>
        <tr><th>Mileage Allowance</th><td>2,000 miles per 28 days (£0.55/mile excess)</td></tr>
    </table>

    <div class="section-title">3. Rental Terms & Rate</div>
    <table>
        <tr><th>Start Date</th><td>{start_str}</td></tr>
        <tr><th>End Date</th><td>{end_str}</td></tr>
        <tr><th>Rental Rate</th><td><strong>{rate_str}</strong></td></tr>
        <tr><th>Deposit</th><td>£0.00 (Standard)</td></tr>
    </table>

    <div class="section-title">4. Statement of Liability (PCNs & Traffic Violations)</div>
    <div class="liability-box">
        <strong>IMPORTANT LEGAL NOTICE - TRANSFER OF LIABILITY:</strong><br>
        I, the undersigned driver, hereby acknowledge that during the currency of this agreement, for the purposes of
        <strong>Section 66 of the Road Traffic Offenders Act 1988</strong>, Schedule 6 Road Traffic Act 1991, the
        <strong>Protection of Freedoms Act 2012</strong>, and Schedule 1 to the Road Traffic (Owner Liability) (Scotland)
        Regulations 1975, I shall be strictly liable as owner/keeper of the vehicle specified ({reg}) in respect of any
        fixed penalty notice, penalty charge notice (PCN), notice to owner, bus lane charge, or congestion/Dart charge
        incurred during the hire period.
    </div>

    <div class="section-title">5. Signatures & Digital Acceptance</div>
    <p style="font-size: 13px; color: #475569;">
        By signing below, the renter agrees to all terms and conditions of K.A Rentals Ltd vehicle hire.
    </p>

    <div class="signature-box">
        <table style="border: none;">
            <tr style="border: none;">
                <td style="border: none; width: 50%;">
                    <strong>Driver Signature:</strong><br><br>
                    <span style="color: #cbd5e1; font-family: monospace;">/sn1/</span>
                    <br><br>
                    <strong>Signed By:</strong> {driver_name}<br>
                    <strong>Date:</strong> {agreement_date}
                </td>
                <td style="border: none; width: 50%; border-left: 1px solid #e2e8f0; padding-left: 20px;">
                    <strong>Authorized Representative:</strong><br><br>
                    <strong style="color: #0f172a;">K.A RENTALS LTD</strong><br>
                    <em>Operations Fleet Management</em>
                </td>
            </tr>
        </table>
    </div>
</body>
</html>
"""
    return html


def send_contract_envelope(
    contract_id: int,
    db: Session,
    recipient_email_override: Optional[str] = None,
    recipient_name_override: Optional[str] = None,
) -> Dict[str, Any]:
    """Generates the hire contract and dispatches a live envelope via DocuSign eSignature API."""
    contract = db.get(Contract, contract_id)
    if not contract:
        raise ValueError(f"Contract #{contract_id} not found.")

    customer = db.get(Customer, contract.matched_customer_id) if contract.matched_customer_id else None
    vehicle_stmt = select(Vehicle).where(Vehicle.normalized_registration == contract.normalized_registration)
    vehicle = db.scalars(vehicle_stmt).first()

    signer_email = recipient_email_override or (customer.email if customer else None)
    signer_name = recipient_name_override or (customer.full_name if customer else contract.customer_name_raw)

    if not signer_email or not signer_email.strip():
        raise ValueError("Signer email is mandatory to dispatch DocuSign envelope.")
    if not signer_name or not signer_name.strip():
        signer_name = "KA Rentals Driver"

    # 1. Render contract document
    html_content = generate_contract_html(contract, customer, vehicle)
    doc_base64 = base64.b64encode(html_content.encode("utf-8")).decode("utf-8")

    config = _get_env_config()
    token = get_docusign_access_token()

    # 2. Build Envelope Definition
    envelope_payload = {
        "emailSubject": f"K.A Rentals - Please sign your Car Hire Agreement for {contract.vehicle_registration}",
        "documents": [
            {
                "documentBase64": doc_base64,
                "name": f"KA_Rentals_Hire_Agreement_{contract.vehicle_registration}.html",
                "fileExtension": "html",
                "documentId": "1",
            }
        ],
        "recipients": {
            "signers": [
                {
                    "email": signer_email.strip(),
                    "name": signer_name.strip(),
                    "recipientId": "1",
                    "routingOrder": "1",
                    "tabs": {
                        "signHereTabs": [
                            {
                                "anchorString": "/sn1/",
                                "anchorUnits": "pixels",
                                "anchorXOffset": "0",
                                "anchorYOffset": "-5",
                            }
                        ]
                    },
                }
            ]
        },
        "status": "sent",
    }

    url = f"{config['base_url']}/v2.1/accounts/{config['account_id']}/envelopes"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    res = httpx.post(url, json=envelope_payload, headers=headers, timeout=20.0)

    if res.status_code not in (200, 201):
        err_msg = f"DocuSign envelope creation failed ({res.status_code}): {res.text}"
        logger.error(err_msg)
        raise RuntimeError(err_msg)

    data = res.json()
    envelope_id = data.get("envelopeId")
    status = data.get("status", "sent")

    # 3. Update database record
    contract.docusign_envelope_id = envelope_id
    contract.docusign_status = status
    contract.raw_status = "sent_for_signature"
    db.commit()
    db.refresh(contract)

    logger.info("Dispatched DocuSign envelope %s for contract #%d to %s", envelope_id, contract.id, signer_email)

    return {
        "envelope_id": envelope_id,
        "status": status,
        "recipient_email": signer_email,
        "recipient_name": signer_name,
        "contract_id": contract.id,
    }


def get_envelope_status(envelope_id: str) -> Dict[str, Any]:
    """Retrieves current envelope status from DocuSign REST API."""
    config = _get_env_config()
    token = get_docusign_access_token()

    url = f"{config['base_url']}/v2.1/accounts/{config['account_id']}/envelopes/{envelope_id}"
    headers = {"Authorization": f"Bearer {token}"}

    res = httpx.get(url, headers=headers, timeout=15.0)
    if res.status_code != 200:
        raise RuntimeError(f"Failed to fetch envelope status ({res.status_code}): {res.text}")

    return res.json()


def process_docusign_webhook_event(payload: Dict[str, Any], db: Session) -> Dict[str, Any]:
    """Processes incoming DocuSign Connect webhook notifications.

    When status is completed, automatically flips contract status to 'signed'.
    """
    # DocuSign Connect sends envelopeId either in root or in data.envelopeId
    envelope_id = payload.get("envelopeId") or payload.get("data", {}).get("envelopeId")
    event_status = (
        payload.get("status")
        or payload.get("event", "").replace("envelope-", "")
        or payload.get("data", {}).get("envelopeSummary", {}).get("status")
        or "unknown"
    ).lower()

    if not envelope_id:
        return {"status": "ignored", "reason": "No envelopeId in webhook payload"}

    stmt = select(Contract).where(Contract.docusign_envelope_id == envelope_id)
    contract = db.scalars(stmt).first()

    if not contract:
        logger.warning("DocuSign Webhook: No contract found matching envelope ID %s", envelope_id)
        return {"status": "not_found", "envelope_id": envelope_id}

    contract.docusign_status = event_status

    if event_status in ("completed", "signed"):
        contract.normalized_status = "signed"
        contract.raw_status = "Signed via DocuSign"
        contract.signed_at = datetime.now(timezone.utc)

        # Update vehicle active status
        veh_stmt = select(Vehicle).where(Vehicle.normalized_registration == contract.normalized_registration)
        vehicle = db.scalars(veh_stmt).first()
        if vehicle:
            vehicle.active_contract_status = "signed"

    db.commit()
    db.refresh(contract)

    logger.info("DocuSign Webhook processed: envelope=%s, status=%s, contract_id=%d", envelope_id, event_status, contract.id)

    return {
        "status": "processed",
        "envelope_id": envelope_id,
        "contract_id": contract.id,
        "contract_status": contract.normalized_status,
        "docusign_status": contract.docusign_status,
    }

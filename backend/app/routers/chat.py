from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from pydantic import BaseModel
from typing import Optional, Dict, List
from datetime import datetime, timedelta
import time

from ..models.database import get_db, User, AuditLog, Transaction, Category
from ..auth.local_auth import get_current_user
from ..services.ollama_client import llm_client

router = APIRouter()

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str
    timestamp: str
    user_context: str
    ai_powered: bool = False
    fallback_used: bool = False
    model_info: Optional[str] = None
    suggested_action: Optional[str] = None
    action_params: Optional[Dict] = None

async def get_comprehensive_transaction_context(user: User, db: AsyncSession) -> dict:
    """Get full transaction context for AI - read-only data access"""
    
    # Total transaction count
    result = await db.execute(
        select(func.count(Transaction.id))
        .where(Transaction.user_id == user.id)
    )
    transaction_count = result.scalar() or 0
    
    if transaction_count == 0:
        return {"has_data": False, "transaction_count": 0}
    
    # Recent spending (last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    
    result = await db.execute(
        select(func.sum(Transaction.amount))
        .where(
            Transaction.user_id == user.id,
            Transaction.posted_at >= thirty_days_ago,
            Transaction.main_category == 'expense'
        )
    )
    recent_spending = float(result.scalar() or 0)
    
    # Recent income
    result = await db.execute(
        select(func.sum(Transaction.amount))
        .where(
            Transaction.user_id == user.id,
            Transaction.posted_at >= thirty_days_ago,
            Transaction.main_category == 'income'
        )
    )
    recent_income = float(result.scalar() or 0)
    
    # Uncategorized count
    result = await db.execute(
        select(func.count(Transaction.id))
        .where(
            Transaction.user_id == user.id,
            Transaction.category_id.is_(None)
        )
    )
    uncategorized_count = result.scalar() or 0
    
    # Category breakdown with amounts
    result = await db.execute(
        select(
            Transaction.main_category,
            func.count(Transaction.id).label('count'),
            func.sum(func.abs(Transaction.amount)).label('total')
        )
        .where(Transaction.user_id == user.id)
        .group_by(Transaction.main_category)
        .order_by(func.sum(func.abs(Transaction.amount)).desc())
    )
    
    categories = {}
    for row in result:
        if row.main_category:
            categories[row.main_category.lower()] = {
                "name": row.main_category,
                "count": row.count,
                "total": float(row.total or 0)
            }
    
    # CSV subcategories breakdown (top spending)
    result = await db.execute(
        select(
            Transaction.category,
            func.count(Transaction.id).label('count'),
            func.sum(func.abs(Transaction.amount)).label('total')
        )
        .where(
            Transaction.user_id == user.id,
            Transaction.category.isnot(None)
        )
        .group_by(Transaction.category)
        .order_by(func.sum(func.abs(Transaction.amount)).desc())
        .limit(10)
    )
    
    subcategories = {}
    for row in result:
        if row.category:
            subcategories[row.category.lower()] = {
                "name": row.category,
                "count": row.count,
                "total": float(row.total or 0)
            }
    
    # Top merchants
    result = await db.execute(
        select(
            Transaction.merchant,
            func.count(Transaction.id).label('count'),
            func.sum(func.abs(Transaction.amount)).label('total')
        )
        .where(
            Transaction.user_id == user.id,
            Transaction.merchant.isnot(None)
        )
        .group_by(Transaction.merchant)
        .order_by(func.sum(func.abs(Transaction.amount)).desc())
        .limit(10)
    )
    
    top_merchants = []
    for row in result:
        if row.merchant:
            top_merchants.append({
                "name": row.merchant,
                "count": row.count,
                "total": float(row.total or 0)
            })
    
    # Date range
    result = await db.execute(
        select(
            func.min(Transaction.posted_at),
            func.max(Transaction.posted_at)
        )
        .where(Transaction.user_id == user.id)
    )
    min_date, max_date = result.first()
    
    return {
        "has_data": True,
        "transaction_count": transaction_count,
        "recent_spending": abs(recent_spending),
        "recent_income": abs(recent_income),
        "uncategorized_count": uncategorized_count,
        "categories": categories,
        "subcategories": subcategories,
        "top_merchants": top_merchants,
        "date_range": {
            "earliest": min_date.strftime("%Y-%m-%d") if min_date else None,
            "latest": max_date.strftime("%Y-%m-%d") if max_date else None
        }
    }

def detect_intent_and_action(message: str, tx_context: dict) -> tuple[Optional[str], Optional[dict]]:
    """Detect user intent and return action with parameters"""
    message_lower = message.lower()
    
    # Check if user has data
    if not tx_context.get("has_data"):
        if any(word in message_lower for word in ["import", "upload", "csv", "add"]):
            return "show_transactions_tab", None
        return None, None
    
    # IMPORTANT: Check for "show" or "list" keywords for filtering
    is_filter_request = any(word in message_lower for word in [
        "show", "list", "filter", "find", "get", "display", "see"
    ])
    
    if not is_filter_request:
        # Not a filter request, return None to let AI answer
        return None, None
    
    # Now check what to filter by
    available_categories = tx_context.get("categories", {})
    available_subcategories = tx_context.get("subcategories", {})
    
    # Check main categories
    for category_key, category_data in available_categories.items():
        if category_key in message_lower:
            return "filter_transactions", {
                "main_category": category_data["name"]
            }
    
    # Check subcategories
    for subcat_key, subcat_data in available_subcategories.items():
        if subcat_key in message_lower:
            return "filter_transactions", {
                "category_filter": subcat_data["name"]
            }
    
    # Merchant filtering
    top_merchants = tx_context.get("top_merchants", [])
    for merchant in top_merchants:
        merchant_name = merchant["name"].lower()
        # Check if merchant name appears in message
        merchant_words = merchant_name.split()
        if any(word in message_lower for word in merchant_words if len(word) > 3):
            return "filter_transactions", {
                "merchant": merchant["name"]
            }
    
    # Transaction type filtering
    if any(word in message_lower for word in ["expense", "expenses", "spending"]):
        return "filter_transactions", {"main_category": "expense"}
    elif any(word in message_lower for word in ["income", "earning", "salary"]):
        return "filter_transactions", {"main_category": "income"}
    elif any(word in message_lower for word in ["transfer", "transfers"]):
        return "filter_transactions", {"main_category": "transfer"}
    
    # If "show" but no match, show transactions tab
    return "show_transactions_tab", None

def build_context_for_ai(user_name: str, tx_context: dict) -> str:
    """Build concise context string for AI model"""
    
    if not tx_context.get("has_data"):
        return f"User {user_name} has no transaction data. Guide them to import CSV."
    
    context_parts = [
        f"User: {user_name}",
        f"{tx_context['transaction_count']} transactions total"
    ]
    
    # Add financial summary
    if tx_context["recent_spending"] > 0 or tx_context["recent_income"] > 0:
        context_parts.append(
            f"Last 30 days: €{tx_context['recent_spending']:.0f} spent, €{tx_context['recent_income']:.0f} income"
        )
    
    # Add category information (top 5)
    categories = tx_context.get("categories", {})
    if categories:
        top_cats = sorted(categories.items(), key=lambda x: x[1]["total"], reverse=True)[:5]
        cat_summary = ", ".join([f"{cat[1]['name']} €{cat[1]['total']:.0f}" for cat in top_cats])
        context_parts.append(f"Top categories: {cat_summary}")
    
    # Add uncategorized warning
    if tx_context.get("uncategorized_count", 0) > 0:
        context_parts.append(f"{tx_context['uncategorized_count']} uncategorized transactions")
    
    return ". ".join(context_parts) + "."

def get_smart_fallback_response(message: str, user: User, tx_context: dict) -> str:
    """Ultra-concise, data-aware fallback responses (max 25 words)"""
    message_lower = message.lower()
    user_name = user.display_name or user.email.split('@')[0]
    
    if not tx_context.get("has_data"):
        return f"No data yet. Upload CSV to start."
    
    # Category queries
    categories = tx_context.get("categories", {})
    subcategories = tx_context.get("subcategories", {})
    
    for cat_key, cat_data in categories.items():
        if cat_key in message_lower:
            count = cat_data["count"]
            total = cat_data["total"]
            return f"Showing {count} {cat_data['name']} transactions (€{total:.0f} total)."
    
    for subcat_key, subcat_data in subcategories.items():
        if subcat_key in message_lower:
            count = subcat_data["count"]
            total = subcat_data["total"]
            return f"Showing {count} {subcat_data['name']} transactions (€{total:.0f})."
    
    # Merchant queries
    for merchant in tx_context.get("top_merchants", []):
        merchant_name = merchant["name"].lower()
        merchant_words = merchant_name.split()
        if any(word in message_lower for word in merchant_words if len(word) > 3):
            return f"Showing {merchant['count']} {merchant['name']} purchases (€{merchant['total']:.0f})."
    
    # Spending summary
    if any(word in message_lower for word in ["spend", "spent", "spending", "expense"]):
        spending = tx_context["recent_spending"]
        return f"€{spending:.0f} spent in last 30 days."
    
    # Income summary
    if any(word in message_lower for word in ["income", "earn", "salary"]):
        income = tx_context["recent_income"]
        return f"€{income:.0f} income in last 30 days."
    
    # Balance/Net
    if any(word in message_lower for word in ["balance", "net", "left", "save"]):
        net = tx_context["recent_income"] - tx_context["recent_spending"]
        return f"Net last 30 days: €{net:.0f}."
    
    # Top spending
    if any(word in message_lower for word in ["most", "top", "biggest", "where"]):
        if categories:
            top_cat = max(categories.values(), key=lambda x: x["total"])
            return f"Top category: {top_cat['name']} (€{top_cat['total']:.0f})."
        return f"No category data."
    
    # Greetings
    if any(word in message_lower for word in ["hi", "hello", "hey"]):
        return f"Hi {user_name}! {tx_context['transaction_count']} transactions ready. What do you need?"
    
    # Help
    if "help" in message_lower:
        return f"Ask about spending, income, categories, or merchants."
    
    # Access question
    if "access" in message_lower or "see" in message_lower:
        return f"Yes! I can see all {tx_context['transaction_count']} transactions. Ask me anything."
    
    # Default
    return f"{tx_context['transaction_count']} transactions tracked. Try 'show food' or 'top spending'."
    """Ultra-concise, data-aware fallback responses (max 25 words)"""
    message_lower = message.lower()
    user_name = user.display_name or user.email.split('@')[0]
    
    if not tx_context.get("has_data"):
        return f"Upload your CSV first, {user_name}. Then I can analyze your spending."
    
    # Category queries
    categories = tx_context.get("categories", {})
    subcategories = tx_context.get("subcategories", {})
    
    for cat_key, cat_data in categories.items():
        if cat_key in message_lower:
            count = cat_data["count"]
            total = cat_data["total"]
            return f"{cat_data['name']}: {count} transactions, €{total:.0f} total. Filter applied."
    
    for subcat_key, subcat_data in subcategories.items():
        if subcat_key in message_lower:
            count = subcat_data["count"]
            total = subcat_data["total"]
            return f"{subcat_data['name']}: {count} transactions, €{total:.0f}. Showing now."
    
    # Merchant queries
    for merchant in tx_context.get("top_merchants", []):
        merchant_name = merchant["name"].lower()
        if merchant_name in message_lower:
            return f"{merchant['name']}: {merchant['count']} purchases, €{merchant['total']:.0f}. Filter applied."
    
    # Spending summary
    if any(word in message_lower for word in ["spend", "spent", "spending", "expense"]):
        spending = tx_context["recent_spending"]
        return f"Last 30 days: €{spending:.0f} spent across {len(categories)} categories."
    
    # Income summary
    if any(word in message_lower for word in ["income", "earn", "salary"]):
        income = tx_context["recent_income"]
        return f"Last 30 days: €{income:.0f} income received."
    
    # Balance/Net
    if any(word in message_lower for word in ["balance", "net", "left", "save"]):
        net = tx_context["recent_income"] - tx_context["recent_spending"]
        return f"Last 30 days net: €{net:.0f}. {'Saving' if net > 0 else 'Overspending'}."
    
    # Top spending
    if any(word in message_lower for word in ["most", "top", "biggest", "where"]):
        if categories:
            top_cat = max(categories.values(), key=lambda x: x["total"])
            return f"Most spending: {top_cat['name']} at €{top_cat['total']:.0f}."
        return f"No category data yet."
    
    # Greetings
    if any(word in message_lower for word in ["hi", "hello", "hey"]):
        return f"Hi {user_name}! {tx_context['transaction_count']} transactions tracked. What would you like to know?"
    
    # Help
    if "help" in message_lower:
        return f"Ask about spending, categories, or merchants. I can filter your {tx_context['transaction_count']} transactions."
    
    # Default
    return f"{tx_context['transaction_count']} transactions ready. Ask about spending, categories, or specific merchants."

async def log_chat_interaction(
    db: AsyncSession,
    user: User,
    message: str,
    response: str,
    ai_powered: bool,
    request: Request
):
    """Log chat interaction to audit table"""
    audit = AuditLog(
        user_id=user.id,
        entity="chat",
        action="message",
        details={
            "user_message": message,
            "bot_response": response,
            "ai_powered": ai_powered,
            "user_email": user.email
        },
        ip_address=getattr(request.client, 'host', None) if hasattr(request, 'client') else None,
        user_agent=request.headers.get('user-agent', None) if hasattr(request, 'headers') else None
    )
    
    db.add(audit)
    await db.commit()

@router.post("/command", response_model=ChatResponse)
async def chat_command(
    request_data: ChatRequest, 
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """AI-powered chat with full read-only data access"""
    
    message = request_data.message
    user_name = current_user.display_name or current_user.email.split('@')[0]
    user_context = f"authenticated_{current_user.email}"
    ai_powered = False
    fallback_used = False
    model_info = None
    
    # Get comprehensive transaction context
    tx_context = await get_comprehensive_transaction_context(current_user, db)
    
    # Detect intent and action FIRST
    suggested_action, action_params = detect_intent_and_action(message, tx_context)
    
    # If we detected an action, use direct response (skip AI)
    if suggested_action and action_params:
        # Direct data-driven response
        response = get_smart_fallback_response(message, current_user, tx_context)
        fallback_used = True
        model_info = "direct_query"
        
        # Create response
        chat_response = ChatResponse(
            response=response,
            timestamp=time.strftime("%H:%M:%S"),
            user_context=user_context,
            ai_powered=False,
            fallback_used=True,
            model_info=model_info,
            suggested_action=suggested_action,
            action_params=action_params
        )
        
        await log_chat_interaction(db, current_user, message, response, False, request)
        
        status = "⚡ Direct"
        print(f"{status}: {message[:40]}... → {response[:60]}...")
        print(f"   🎯 Action: {suggested_action} {action_params}")
        
        return chat_response
    
    # Build AI context (only for non-action queries)
    ai_context = build_context_for_ai(user_name, tx_context)
    
    # Build prompt with STRICT instructions
    full_prompt = f"""You are a helpful finance assistant. MAX 25 WORDS.

{ai_context}

User asks: "{message}"

Rules:
- Answer in 25 words MAX
- Be direct, no instructions
- Use actual data from context
- Don't tell user to click buttons

Answer:"""
    
    # Try Ollama
    print(f"🎯 Querying Ollama: {message[:50]}")
    try:
        llm_result = await llm_client.query(full_prompt, max_tokens=60)
        
        if llm_result["status"] == "success" and llm_result["text"]:
            response = llm_result["text"].strip()
            # Enforce 25 word limit
            words = response.split()
            if len(words) > 25:
                response = " ".join(words[:25]) + "..."
            
            # Check if response is still giving instructions
            bad_phrases = ["go to", "click on", "navigate to", "select the", "use the"]
            if any(phrase in response.lower() for phrase in bad_phrases):
                # Override with direct response
                response = get_smart_fallback_response(message, current_user, tx_context)
                fallback_used = True
                model_info = "fallback_override"
            else:
                ai_powered = True
                model_info = llm_result.get("meta", {}).get("model", "llama3.2:3b")
            
            print(f"✅ Response generated")
        else:
            response = get_smart_fallback_response(message, current_user, tx_context)
            fallback_used = True
            model_info = "fallback"
            print(f"🔄 Fallback response")
            
    except Exception as e:
        print(f"❌ Ollama error: {e}")
        response = get_smart_fallback_response(message, current_user, tx_context)
        fallback_used = True
        model_info = "fallback"
    
    # Create response
    chat_response = ChatResponse(
        response=response,
        timestamp=time.strftime("%H:%M:%S"),
        user_context=user_context,
        ai_powered=ai_powered,
        fallback_used=fallback_used,
        model_info=model_info,
        suggested_action=suggested_action,
        action_params=action_params
    )
    
    # Log interaction
    await log_chat_interaction(db, current_user, message, response, ai_powered, request)
    
    # Console logging
    status = "🤖 AI" if ai_powered else "🔄 Fallback"
    print(f"{status} [{model_info}]: {message[:40]}... → {response[:60]}...")
    if suggested_action:
        print(f"   ⚡ Action: {suggested_action} {action_params or ''}")
    
    return chat_response

@router.get("/ollama-status")
async def get_ollama_status():
    """Get Ollama connection status"""
    status = await llm_client.check_model_availability()
    
    return {
        "ollama_running": status.get("ollama_running", False),
        "model_available": status.get("model_available", False),
        "current_model": status.get("configured_model", "llama3.2:3b"),
        "available_models": status.get("available_models", []),
        "message": "Ready" if (status.get("ollama_running") and status.get("model_available")) else "Not available"
    }

@router.get("/history")
async def get_chat_history(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user's recent chat history"""
    
    from sqlalchemy import select, desc
    
    result = await db.execute(
        select(AuditLog)
        .where(
            AuditLog.user_id == current_user.id,
            AuditLog.entity == "chat",
            AuditLog.action == "message"
        )
        .order_by(desc(AuditLog.created_at))
        .limit(20)
    )
    
    history = []
    for log in result.scalars().all():
        history.append({
            "message": log.details.get("user_message"),
            "response": log.details.get("bot_response"),
            "ai_powered": log.details.get("ai_powered"),
            "timestamp": log.created_at.isoformat()
        })
    
    return {
        "history": history,
        "count": len(history),
        "user_id": str(current_user.id)
    }


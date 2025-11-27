"""
Chat Router - AI-Powered Chat Assistant

Endpoints:
- POST /command: Send chat message (AI or fallback response)
- GET /ollama-status: Check Ollama LLM service status
- GET /history: Get recent chat history

Features:
- AI-powered responses using Ollama LLM (local)
- Smart fallback responses when AI unavailable
- Intent detection and action suggestions (filter transactions, show tabs)
- Comprehensive transaction context for AI
- 25-word response limit for conciseness
- Audit logging for all interactions
- Transaction filtering by category, merchant, date

Database: SQLAlchemy async with User, AuditLog, Transaction, Category
AI Service: Ollama (llama3.2:3b)
"""

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


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class ChatRequest(BaseModel):
    """Chat message request"""
    message: str


class ChatResponse(BaseModel):
    """Chat response with AI metadata"""
    response: str
    timestamp: str
    user_context: str
    ai_powered: bool = False
    fallback_used: bool = False
    model_info: Optional[str] = None
    suggested_action: Optional[str] = None
    action_params: Optional[Dict] = None


# ============================================================================
# TRANSACTION CONTEXT BUILDING
# ============================================================================

async def get_comprehensive_transaction_context(user: User, db: AsyncSession) -> dict:
    """
    Get comprehensive transaction context for AI
    
    Builds complete financial overview including:
    - Total transaction count
    - Recent spending/income (last 30 days)
    - Uncategorized transaction count
    - Category breakdown with totals
    - Subcategory breakdown (top 10)
    - Top merchants (top 10)
    - Date range (earliest to latest transaction)
    
    This is READ-ONLY data access for AI responses
    
    @param user: Current user
    @param db: Database session
    @returns {dict} Complete transaction context
    """
    # Total transaction count
    result = await db.execute(
        select(func.count(Transaction.id))
        .where(Transaction.user_id == user.id)
    )
    transaction_count = result.scalar() or 0
    
    if transaction_count == 0:
        return {"has_data": False, "transaction_count": 0}
    
    # Recent spending/income (last 30 days)
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
    
    # Subcategories breakdown (top 10 spending)
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
    
    # Top merchants (top 10 by total amount)
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
    
    # Date range (earliest and latest transaction)
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


# ============================================================================
# INTENT DETECTION AND ACTION SUGGESTION
# ============================================================================

def detect_intent_and_action(message: str, tx_context: dict) -> tuple[Optional[str], Optional[dict]]:
    """
    Detect user intent and suggest frontend action
    
    Detects patterns in user message and returns:
    - Action type (filter_transactions, show_transactions_tab)
    - Action parameters (category, merchant, date filters)
    
    Only triggers for explicit filtering requests ("show", "list", "filter")
    Otherwise returns None to let AI answer naturally
    
    @param message: User's chat message
    @param tx_context: Transaction context from get_comprehensive_transaction_context
    @returns {tuple} (action_type: str|None, action_params: dict|None)
    """
    message_lower = message.lower()
    
    # No data yet - suggest import
    if not tx_context.get("has_data"):
        if any(word in message_lower for word in ["import", "upload", "csv", "add"]):
            return "show_transactions_tab", None
        return None, None
    
    # Check for explicit filter keywords
    is_filter_request = any(word in message_lower for word in [
        "show", "list", "filter", "find", "get", "display", "see"
    ])
    
    if not is_filter_request:
        # Not a filter request - let AI answer naturally
        return None, None
    
    # Extract available categories/merchants from context
    available_categories = tx_context.get("categories", {})
    available_subcategories = tx_context.get("subcategories", {})
    
    # Check main categories (income, expense, transfer)
    for category_key, category_data in available_categories.items():
        if category_key in message_lower:
            return "filter_transactions", {
                "main_category": category_data["name"]
            }
    
    # Check subcategories (Food, Transport, etc.)
    for subcat_key, subcat_data in available_subcategories.items():
        if subcat_key in message_lower:
            return "filter_transactions", {
                "category_filter": subcat_data["name"]
            }
    
    # Merchant filtering
    top_merchants = tx_context.get("top_merchants", [])
    for merchant in top_merchants:
        merchant_name = merchant["name"].lower()
        # Check if merchant name words appear in message (skip short words)
        merchant_words = merchant_name.split()
        if any(word in message_lower for word in merchant_words if len(word) > 3):
            return "filter_transactions", {
                "merchant": merchant["name"]
            }
    
    # Transaction type keywords
    if any(word in message_lower for word in ["expense", "expenses", "spending"]):
        return "filter_transactions", {"main_category": "expense"}
    elif any(word in message_lower for word in ["income", "earning", "salary"]):
        return "filter_transactions", {"main_category": "income"}
    elif any(word in message_lower for word in ["transfer", "transfers"]):
        return "filter_transactions", {"main_category": "transfer"}
    
    # No specific action detected
    return None, None


# ============================================================================
# AI CONTEXT BUILDING
# ============================================================================

def build_context_for_ai(user_name: str, tx_context: dict) -> str:
    """
    Build concise context for AI prompt
    
    Creates a text summary of user's financial data
    Optimized for LLM context window (keeps it short)
    
    @param user_name: User's display name
    @param tx_context: Transaction context dict
    @returns {str} Text context for AI prompt
    """
    if not tx_context.get("has_data"):
        return f"User: {user_name}\nData: No transactions yet."
    
    # Build concise summary
    ctx = f"User: {user_name}\n"
    ctx += f"Transactions: {tx_context['transaction_count']}\n"
    ctx += f"Last 30d: €{tx_context['recent_spending']:.0f} spent, €{tx_context['recent_income']:.0f} income\n"
    
    # Top categories
    if tx_context.get('categories'):
        top_cats = sorted(
            tx_context['categories'].values(),
            key=lambda x: x['total'],
            reverse=True
        )[:3]
        cat_list = ', '.join([f"{c['name']} €{c['total']:.0f}" for c in top_cats])
        ctx += f"Top categories: {cat_list}\n"
    
    # Top merchants
    if tx_context.get('top_merchants'):
        top_merch = tx_context['top_merchants'][:3]
        merch_list = ', '.join([f"{m['name']} €{m['total']:.0f}" for m in top_merch])
        ctx += f"Top merchants: {merch_list}\n"
    
    return ctx


# ============================================================================
# FALLBACK RESPONSE GENERATION
# ============================================================================

def get_smart_fallback_response(message: str, user: User, tx_context: dict) -> str:
    """
    Generate smart fallback response when AI unavailable
    
    Pattern matching for common questions:
    - Spending queries
    - Income queries
    - Balance/net queries
    - Top spending queries
    - Greetings
    - Help requests
    
    @param message: User's message
    @param user: Current user
    @param tx_context: Transaction context
    @returns {str} Fallback response
    """
    message_lower = message.lower()
    user_name = user.display_name or user.email.split('@')[0]
    
    # No data yet
    if not tx_context.get("has_data"):
        return f"Hi {user_name}! No transactions yet. Import a CSV to get started."
    
    categories = tx_context.get("categories", {})
    
    # Spending queries
    if any(word in message_lower for word in ["spend", "spent", "expense", "cost"]):
        spending = tx_context["recent_spending"]
        return f"Last 30 days: €{spending:.0f} spent across {tx_context['transaction_count']} transactions."
    
    # Income queries
    if any(word in message_lower for word in ["earn", "income", "salary", "revenue"]):
        income = tx_context["recent_income"]
        return f"Last 30 days: €{income:.0f} income received."
    
    # Balance/Net queries
    if any(word in message_lower for word in ["balance", "net", "left", "save"]):
        net = tx_context["recent_income"] - tx_context["recent_spending"]
        return f"Last 30 days net: €{net:.0f}. {'Saving' if net > 0 else 'Overspending'}."
    
    # Top spending queries
    if any(word in message_lower for word in ["most", "top", "biggest", "where"]):
        if categories:
            top_cat = max(categories.values(), key=lambda x: x["total"])
            return f"Most spending: {top_cat['name']} at €{top_cat['total']:.0f}."
        return f"No category data yet."
    
    # Greetings
    if any(word in message_lower for word in ["hi", "hello", "hey"]):
        return f"Hi {user_name}! {tx_context['transaction_count']} transactions tracked. What would you like to know?"
    
    # Help requests
    if "help" in message_lower:
        return f"Ask about spending, categories, or merchants. I can filter your {tx_context['transaction_count']} transactions."
    
    # Default response
    return f"{tx_context['transaction_count']} transactions ready. Ask about spending, categories, or specific merchants."


# ============================================================================
# AUDIT LOGGING
# ============================================================================

async def log_chat_interaction(
    db: AsyncSession,
    user: User,
    message: str,
    response: str,
    ai_powered: bool,
    request: Request
):
    """
    Log chat interaction to audit table
    
    Stores:
    - User message and bot response
    - AI powered flag
    - User email
    - IP address and user agent
    
    @param db: Database session
    @param user: Current user
    @param message: User's message
    @param response: Bot's response
    @param ai_powered: Whether AI was used (vs fallback)
    @param request: FastAPI request object
    """
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


# ============================================================================
# CHAT COMMAND ENDPOINT
# ============================================================================

@router.post("/command", response_model=ChatResponse)
async def chat_command(
    request_data: ChatRequest, 
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    AI-powered chat command with full transaction context
    
    Process:
    1. Get comprehensive transaction context
    2. Detect intent and suggested action (filter, show tabs)
    3. If action detected → Direct response + action params
    4. Otherwise → Query Ollama AI with context
    5. Fallback to pattern-matching if AI unavailable
    6. Enforce 25-word response limit
    7. Log interaction to audit table
    
    Response types:
    - AI-powered: Ollama LLM response (ai_powered=true)
    - Direct: Pattern-based instant response (fallback_used=true)
    - Fallback: AI failed, using pattern matching (fallback_used=true)
    
    @param request_data: Chat message
    @param request: FastAPI request (for logging)
    @param current_user: Injected from JWT token
    @param db: Database session
    @returns {ChatResponse} Response with AI metadata and suggested action
    """
    message = request_data.message
    user_name = current_user.display_name or current_user.email.split('@')[0]
    user_context = f"authenticated_{current_user.email}"
    ai_powered = False
    fallback_used = False
    model_info = None
    
    # Get comprehensive transaction context (read-only data access)
    tx_context = await get_comprehensive_transaction_context(current_user, db)
    
    # Detect intent and action FIRST (e.g., "show expenses" → filter action)
    suggested_action, action_params = detect_intent_and_action(message, tx_context)
    
    # If we detected a specific action, use direct response (skip AI)
    if suggested_action and action_params:
        # Direct data-driven response
        response = get_smart_fallback_response(message, current_user, tx_context)
        fallback_used = True
        model_info = "direct_query"
        
        # Create response with action
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
        
        print(f"⚡ Direct: {message[:40]}... → {response[:60]}...")
        print(f"   🎯 Action: {suggested_action} {action_params}")
        
        return chat_response
    
    # Build AI context for natural language questions
    ai_context = build_context_for_ai(user_name, tx_context)
    
    # Build prompt with STRICT word limit
    full_prompt = f"""You are a helpful finance assistant. MAX 25 WORDS.

{ai_context}

User asks: "{message}"

Rules:
- Answer in 25 words MAX
- Be direct, no instructions
- Use actual data from context
- Don't tell user to click buttons

Answer:"""
    
    # Try Ollama LLM
    print(f"🎯 Querying Ollama: {message[:50]}")
    try:
        llm_result = await llm_client.query(full_prompt, max_tokens=60)
        
        if llm_result["status"] == "success" and llm_result["text"]:
            response = llm_result["text"].strip()
            
            # Enforce 25 word limit
            words = response.split()
            if len(words) > 25:
                response = " ".join(words[:25]) + "..."
            
            # Check if AI is giving UI instructions (bad)
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
            # AI returned empty/error - use fallback
            response = get_smart_fallback_response(message, current_user, tx_context)
            fallback_used = True
            model_info = "fallback"
            print(f"🔄 Fallback response")
            
    except Exception as e:
        # AI failed - use fallback
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
    
    # Log interaction to audit table
    await log_chat_interaction(db, current_user, message, response, ai_powered, request)
    
    # Console logging
    status = "🤖 AI" if ai_powered else "🔄 Fallback"
    print(f"{status} [{model_info}]: {message[:40]}... → {response[:60]}...")
    if suggested_action:
        print(f"   ⚡ Action: {suggested_action} {action_params or ''}")
    
    return chat_response


# ============================================================================
# OLLAMA STATUS ENDPOINT
# ============================================================================

@router.get("/ollama-status")
async def get_ollama_status():
    """
    Get Ollama LLM service connection status
    
    Checks:
    - Is Ollama service running?
    - Is configured model available?
    - List of available models
    
    @returns {dict} Status information
    """
    status = await llm_client.check_model_availability()
    
    return {
        "ollama_running": status.get("ollama_running", False),
        "model_available": status.get("model_available", False),
        "current_model": status.get("configured_model", "llama3.2:3b"),
        "available_models": status.get("available_models", []),
        "message": "Ready" if (status.get("ollama_running") and status.get("model_available")) else "Not available"
    }


# ============================================================================
# CHAT HISTORY ENDPOINT
# ============================================================================

@router.get("/history")
async def get_chat_history(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get user's recent chat history
    
    Returns last 20 chat interactions from audit log
    Sorted by newest first
    
    @param current_user: Injected from JWT token
    @param db: Database session
    @returns {dict} {history: [...], count: int, user_id: str}
    """
    from sqlalchemy import desc
    
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
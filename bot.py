"""
Personal Financial Tracker Telegram Bot
========================================
Bot untuk merekam pengeluaran harian via Telegram.

Cara pakai:
- Chat langsung: "bakso 10000, kepiting 5000"
- Cek hari ini: /today atau "pengeluaran hari ini"
- Cek tanggal tertentu: /date 25 atau "pengeluaran tanggal 25"
- Cek bulan ini: /month atau "pengeluaran bulan ini"
- Cek bulan tertentu: /month 12-2025 atau "pengeluaran bulan 12-2025"
- Hapus entry terakhir: /undo
"""

import os
import re
import sqlite3
from datetime import datetime, timedelta
from typing import Optional
import logging

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Database path
DB_PATH = "expenses.db"


# ==================== DATABASE ====================

def init_db():
    """Initialize SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            description TEXT NOT NULL,
            amount INTEGER NOT NULL,
            created_at TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()


def add_expense(user_id: int, description: str, amount: int) -> int:
    """Add an expense record. Returns the expense ID."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    created_at = now.strftime("%Y-%m-%d %H:%M:%S")
    
    cursor.execute('''
        INSERT INTO expenses (user_id, date, description, amount, created_at)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, date_str, description, amount, created_at))
    
    expense_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return expense_id


def get_expenses_by_date(user_id: int, date_str: str) -> list:
    """Get all expenses for a specific date."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, description, amount, created_at 
        FROM expenses 
        WHERE user_id = ? AND date = ?
        ORDER BY created_at ASC
    ''', (user_id, date_str))
    results = cursor.fetchall()
    conn.close()
    return results


def get_monthly_expenses(user_id: int, year: int, month: int) -> list:
    """Get all expenses for a specific month."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    date_pattern = f"{year}-{month:02d}-%"
    cursor.execute('''
        SELECT date, SUM(amount) as total
        FROM expenses 
        WHERE user_id = ? AND date LIKE ?
        GROUP BY date
        ORDER BY date ASC
    ''', (user_id, date_pattern))
    results = cursor.fetchall()
    conn.close()
    return results


def delete_last_expense(user_id: int) -> Optional[tuple]:
    """Delete the last expense entry. Returns deleted item or None."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get the last expense
    cursor.execute('''
        SELECT id, description, amount FROM expenses 
        WHERE user_id = ? 
        ORDER BY id DESC LIMIT 1
    ''', (user_id,))
    last_expense = cursor.fetchone()
    
    if last_expense:
        cursor.execute('DELETE FROM expenses WHERE id = ?', (last_expense[0],))
        conn.commit()
    
    conn.close()
    return last_expense


# ==================== PARSER ====================

def parse_expenses(text: str) -> list:
    """
    Parse expense text into list of (description, amount) tuples.
    
    Supports formats:
    - "bakso 10000"
    - "bakso 10.000"
    - "bakso 10,000"
    - "bakso Rp 10.000"
    - "bakso 10rb" or "bakso 10k"
    - Multiple items: "bakso 10000, kepiting 5000" or "bakso 10000. kepiting 5000"
    """
    expenses = []
    
    # Split by common delimiters (comma, period followed by space, newline)
    items = re.split(r'[,\n]|\.\s+', text)
    
    for item in items:
        item = item.strip()
        if not item:
            continue
        
        # Pattern: description followed by amount
        # Amount can have Rp prefix, dots/commas as thousand separators, rb/k suffix
        pattern = r'^(.+?)\s+(?:Rp\.?\s*)?(\d{1,3}(?:[.,]\d{3})*|\d+)\s*(?:rb|ribu|k)?$'
        match = re.match(pattern, item, re.IGNORECASE)
        
        if match:
            description = match.group(1).strip()
            amount_str = match.group(2)
            
            # Remove thousand separators
            amount_str = amount_str.replace('.', '').replace(',', '')
            amount = int(amount_str)
            
            # Check for rb/k suffix (multiply by 1000)
            if re.search(r'(rb|ribu|k)\s*$', item, re.IGNORECASE):
                amount *= 1000
            
            expenses.append((description, amount))
    
    return expenses


def format_currency(amount: int) -> str:
    """Format amount as Indonesian Rupiah."""
    return f"Rp {amount:,}".replace(',', '.')


def get_month_name(month: int) -> str:
    """Get Indonesian month name."""
    months = [
        "Januari", "Februari", "Maret", "April", "Mei", "Juni",
        "Juli", "Agustus", "September", "Oktober", "November", "Desember"
    ]
    return months[month - 1]


# ==================== HANDLERS ====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command."""
    welcome_msg = """
🎯 *Personal Financial Tracker*

Halo! Gue bot untuk tracking pengeluaran lo sehari-hari.

*Cara pakai:*
• Langsung chat pengeluaran lo:
  `bakso 15000, es teh 5000`
  `makan siang 25rb`

*Commands:*
• /today - Lihat pengeluaran hari ini
• /date [tanggal] - Lihat pengeluaran tanggal tertentu
• /month - Lihat rekap bulan ini
• /month [bulan-tahun] - Lihat rekap bulan tertentu (misal: /month 1-2025)
• /undo - Hapus entry terakhir
• /help - Bantuan

*Tips:*
• Format angka: `10000`, `10.000`, `10rb`, `10k`
• Pisahkan dengan koma atau enter untuk multiple items
"""
    await update.message.reply_text(welcome_msg, parse_mode='Markdown')


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command."""
    help_msg = """
📖 *Panduan Penggunaan*

*Mencatat Pengeluaran:*
Langsung ketik apa yang lo beli dan harganya:
• `bakso 15000`
• `bakso 15.000`
• `bakso 15rb`
• `bakso Rp 15000`

*Multiple Items:*
• `bakso 15rb, es teh 5rb`
• `makan 25000. transport 10000`

*Melihat Data:*
• /today - Pengeluaran hari ini
• /date 25 - Pengeluaran tanggal 25 bulan ini
• /date 7-12 - Pengeluaran 7 Desember
• /date 7-12-2025 - Pengeluaran 7 Des 2025
• /month - Rekap bulan ini
• /month 1-2025 - Rekap Januari 2025
• /month 12-2024 - Rekap Desember 2024

*Lainnya:*
• /undo - Hapus entry terakhir
• /start - Menu utama
"""
    await update.message.reply_text(help_msg, parse_mode='Markdown')


async def today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /today command - show today's expenses."""
    user_id = update.effective_user.id
    today_str = datetime.now().strftime("%Y-%m-%d")
    
    expenses = get_expenses_by_date(user_id, today_str)
    
    if not expenses:
        await update.message.reply_text("📊 Belum ada pengeluaran hari ini. Mulai catat yuk!")
        return
    
    total = sum(exp[2] for exp in expenses)
    
    msg = f"📊 *Pengeluaran Hari Ini*\n"
    msg += f"📅 {datetime.now().strftime('%d %B %Y')}\n\n"
    
    for i, (exp_id, desc, amount, created_at) in enumerate(expenses, 1):
        time_str = created_at.split(' ')[1][:5]
        msg += f"{i}. {desc}: {format_currency(amount)} ({time_str})\n"
    
    msg += f"\n💰 *Total: {format_currency(total)}*"
    
    await update.message.reply_text(msg, parse_mode='Markdown')


async def date_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /date command - show expenses for a specific date."""
    user_id = update.effective_user.id
    
    if not context.args:
        await update.message.reply_text(
            "❌ Format: /date [tanggal-bulan-tahun]\n"
            "Contoh: /date 7-12-2025\n"
            "Atau: /date 7 (untuk tanggal 7 bulan ini)"
        )
        return
    
    try:
        date_input = context.args[0]
        now = datetime.now()
        
        # Check if full date format (DD-MM-YYYY or DD/MM/YYYY)
        if '-' in date_input or '/' in date_input:
            # Parse full date
            date_input = date_input.replace('/', '-')
            parts = date_input.split('-')
            
            if len(parts) == 3:
                day = int(parts[0])
                month = int(parts[1])
                year = int(parts[2])
                
                # Handle 2-digit year
                if year < 100:
                    year += 2000
                
                target_date = datetime(year, month, day)
            elif len(parts) == 2:
                # DD-MM format, assume current year
                day = int(parts[0])
                month = int(parts[1])
                target_date = datetime(now.year, month, day)
            else:
                raise ValueError("Invalid date format")
        else:
            # Just day number, assume current month
            day = int(date_input)
            
            # If the day is greater than today, assume previous month
            if day > now.day:
                target_date = now.replace(day=1) - timedelta(days=1)
                target_date = target_date.replace(day=day)
            else:
                target_date = now.replace(day=day)
        
        date_str = target_date.strftime("%Y-%m-%d")
        
    except (ValueError, IndexError):
        await update.message.reply_text(
            "❌ Tanggal tidak valid!\n\n"
            "Format yang didukung:\n"
            "• /date 7 (tanggal 7 bulan ini)\n"
            "• /date 7-12 (7 Desember tahun ini)\n"
            "• /date 7-12-2025 (7 Desember 2025)"
        )
        return
    
    expenses = get_expenses_by_date(user_id, date_str)
    
    if not expenses:
        await update.message.reply_text(
            f"📊 Tidak ada pengeluaran di tanggal {target_date.strftime('%d %B %Y')}."
        )
        return
    
    total = sum(exp[2] for exp in expenses)
    
    msg = f"📊 *Pengeluaran Tanggal {day}*\n"
    msg += f"📅 {target_date.strftime('%d %B %Y')}\n\n"
    
    for i, (exp_id, desc, amount, created_at) in enumerate(expenses, 1):
        time_str = created_at.split(' ')[1][:5]
        msg += f"{i}. {desc}: {format_currency(amount)} ({time_str})\n"
    
    msg += f"\n💰 *Total: {format_currency(total)}*"
    
    await update.message.reply_text(msg, parse_mode='Markdown')


async def month_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /month command - show monthly summary."""
    user_id = update.effective_user.id
    now = datetime.now()
    
    # Kalau ada args, parse bulan-tahun
    if context.args:
        try:
            # Support format: 12-2025 atau 12/2025
            month_input = context.args[0].replace('/', '-')
            parts = month_input.split('-')
            
            if len(parts) == 2:
                month = int(parts[0])
                year = int(parts[1])
                
                # Validasi bulan (1-12)
                if month < 1 or month > 12:
                    await update.message.reply_text(
                        "❌ Bulan tidak valid! Bulan harus antara 1-12."
                    )
                    return
                
                # Handle 2-digit year
                if year < 100:
                    year += 2000
                    
            elif len(parts) == 1:
                # Hanya bulan, assume tahun sekarang
                month = int(parts[0])
                year = now.year
                
                # Validasi bulan
                if month < 1 or month > 12:
                    await update.message.reply_text(
                        "❌ Bulan tidak valid! Bulan harus antara 1-12."
                    )
                    return
            else:
                raise ValueError("Format salah")
                
        except (ValueError, IndexError):
            await update.message.reply_text(
                "❌ Format: /month [bulan-tahun]\n\n"
                "Contoh:\n"
                "• /month (bulan ini)\n"
                "• /month 1-2025 (Januari 2025)\n"
                "• /month 12-2024 (Desember 2024)\n"
                "• /month 3 (Maret tahun ini)"
            )
            return
    else:
        # Default: bulan sekarang
        month = now.month
        year = now.year
    
    daily_totals = get_monthly_expenses(user_id, year, month)
    
    if not daily_totals:
        month_name = get_month_name(month)
        await update.message.reply_text(
            f"📊 Belum ada pengeluaran di bulan {month_name} {year}."
        )
        return
    
    grand_total = sum(total for _, total in daily_totals)
    month_name = get_month_name(month)
    
    msg = f"📊 *Rekap Bulan {month_name} {year}*\n\n"
    
    for date_str, total in daily_totals:
        day = datetime.strptime(date_str, "%Y-%m-%d").strftime("%d")
        msg += f"📅 Tgl {day}: {format_currency(total)}\n"
    
    msg += f"\n💰 *Total Bulan Ini: {format_currency(grand_total)}*"
    
    await update.message.reply_text(msg, parse_mode='Markdown')


async def undo_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /undo command - delete last expense."""
    user_id = update.effective_user.id
    
    deleted = delete_last_expense(user_id)
    
    if deleted:
        _, desc, amount = deleted
        await update.message.reply_text(
            f"✅ Dihapus: {desc} ({format_currency(amount)})"
        )
    else:
        await update.message.reply_text("❌ Tidak ada data untuk dihapus.")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle regular messages - parse and record expenses or queries."""
    user_id = update.effective_user.id
    text = update.message.text.strip()
    
    # Check for natural language queries
    text_lower = text.lower()
    
    # Query for today's expenses
    if any(phrase in text_lower for phrase in ['pengeluaran hari ini', 'hari ini', 'total hari ini']):
        await today(update, context)
        return
    
    # Query for specific date (supports: tanggal 25, tanggal 7-12-2025, tanggal 7/12/2025)
    date_match = re.search(r'(?:pengeluaran\s+)?tanggal\s+(\d{1,2}(?:[-/]\d{1,2}(?:[-/]\d{2,4})?)?)', text_lower)
    if date_match:
        context.args = [date_match.group(1)]
        await date_command(update, context)
        return
    
    # Query for monthly summary (supports: bulan ini, pengeluaran bulan 1-2025, bulan 12-2024)
    month_match = re.search(r'(?:pengeluaran\s+)?bulan\s+(?:ini|(\d{1,2}(?:[-/]\d{2,4})?))', text_lower)
    if month_match:
        if month_match.group(1):
            # Ada bulan spesifik
            context.args = [month_match.group(1)]
        else:
            # "bulan ini"
            context.args = []
        await month_command(update, context)
        return
    
    # Try to parse as expense entry
    expenses = parse_expenses(text)
    
    if not expenses:
        await update.message.reply_text(
            "🤔 Gue ga ngerti. Coba format:\n"
            "`bakso 15000` atau `bakso 15rb`\n\n"
            "Ketik /help untuk bantuan.",
            parse_mode='Markdown'
        )
        return
    
    # Record expenses
    total = 0
    recorded = []
    
    for desc, amount in expenses:
        add_expense(user_id, desc, amount)
        total += amount
        recorded.append(f"• {desc}: {format_currency(amount)}")
    
    # Get today's running total
    today_str = datetime.now().strftime("%Y-%m-%d")
    all_today = get_expenses_by_date(user_id, today_str)
    daily_total = sum(exp[2] for exp in all_today)
    
    msg = "✅ *Tercatat!*\n\n"
    msg += "\n".join(recorded)
    msg += f"\n\n📊 *Total hari ini: {format_currency(daily_total)}*"
    
    await update.message.reply_text(msg, parse_mode='Markdown')


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors."""
    logger.error(f"Error: {context.error}")


# ==================== MAIN ====================

def main():
    """Main function to run the bot."""
    # Bot token - bisa hardcode atau pakai environment variable
    token = os.getenv("TELEGRAM_BOT_TOKEN") or "8578037119:AAHSq4yc6rFPEQZ3sPWHXY7NBwG6PMxNiSk"
    
    if token == "8578037119:AAHSq4yc6rFPEQZ3sPWHXY7NBwG6PMxNiSk":
        print("❌ Error: Token belum diisi!")
        print("Edit bot.py dan ganti YOUR_BOT_TOKEN_HERE dengan token lo")
        print("Atau set: export TELEGRAM_BOT_TOKEN='token_lo'")
        return
    
    # Initialize database
    init_db()
    
    # Create application
    app = Application.builder().token(token).build()
    
    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("today", today))
    app.add_handler(CommandHandler("date", date_command))
    app.add_handler(CommandHandler("month", month_command))
    app.add_handler(CommandHandler("undo", undo_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Add error handler
    app.add_error_handler(error_handler)
    
    print("🚀 Bot is running...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()

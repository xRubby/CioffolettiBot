from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
 
 
async def handler_defunti(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
 
    tastiera = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("➕ Aggiungi defunto", callback_data="necrologi_aggiungi"),
            InlineKeyboardButton("📋 Lista defunti",    callback_data="necrologi_lista")
        ],
        [InlineKeyboardButton("📌 Cose da fare",     callback_data="necrologi_cose_da_fare")], 
        [InlineKeyboardButton("🔙 Menu principale",  callback_data="menu_principale")],
    ])
 
    await query.edit_message_text(
        "📋 *Necrologi*\n\nCosa vuoi fare?",
        parse_mode="Markdown",
        reply_markup=tastiera,
    )
 
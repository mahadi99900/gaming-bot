# -*- coding: utf-8 -*-
import os
import json
import random
import time
import uuid
import logging
import asyncio

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)

# --- লগিং সেটআপ ---
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# --- কনফিগারেশন এবং কনস্ট্যান্ট ---
TELEGRAM_TOKEN = '7716441936:AAFIoRkzS51fw2dgTs8MCVBmY-lK-OyYGO0' # আপনার আসল টোকেন
OWNER_ID = 6776334925
CREATOR_LINK = 'https://t.me/mahadihasan099'
CHANNEL_LINK = 'https://t.me/battle_nexus'
FOOTER = f"\n\n- - - - - - - - - - - - - - -\n- ᴄʀᴇᴀᴛᴇᴅ ʙʏ: {CREATOR_LINK}\n- ᴄʜᴀɴɴᴇʟ: {CHANNEL_LINK}"

DATA_FILE = 'bot_data.json'
PENDING_BETS = {}
PENDING_BATTLES = {}

data_lock = asyncio.Lock()

# --- গেমের ভ্যারিয়েবল ---
ANIMALS = [
    {'name': 'Cat', 'icon': '🐈', 'base_power': 10}, {'name': 'Dog', 'icon': '🐕', 'base_power': 12},
    {'name': 'Rabbit', 'icon': '🐇', 'base_power': 8}, {'name': 'Deer', 'icon': '🦌', 'base_power': 20},
    {'name': 'Wolf', 'icon': '🐺', 'base_power': 30}, {'name': 'Lion', 'icon': '🦁', 'base_power': 50},
    {'name': 'Tiger', 'icon': '🐅', 'base_power': 55}, {'name': 'Dragon', 'icon': '🐉', 'base_power': 100},
]
ANIMAL_QUALITIES = {'F': 0.5, 'D': 0.8, 'C': 1.0, 'B': 1.2, 'A': 1.5, 'S': 2.0}

HUNT_COOLDOWN, PRAY_COOLDOWN, CLAIM_COOLDOWN = 15, 60, 300
CLAIM_AMOUNT = 1000
PLAYER_XP_FOR_WIN, PLAYER_XP_FOR_LOSS = 50, 10

# --- বহুভাষিক গাইড টেক্সট ---
GUIDE_TEXTS = {
    'bn': (
        "📜 <b>ব্যাটেল নেক্সাস গেম গাইড</b> 📜\n\n"
        "ব্যাটেল নেক্সাসে স্বাগতম! এখানে আপনি প্রাণী শিকার করতে, যুদ্ধ করতে এবং বন্ধুদের সাথে বাজি ধরতে পারবেন।\n\n"
        "--- <b>বেসিক বাটন</b> ---\n"
        "🏞️ <b>Hunt:</b> নতুন প্রাণী শিকার করুন।\n"
        "🐾 <b>My Zoo:</b> আপনার সংগ্রহে থাকা সকল প্রাণী ও তাদের মোট শক্তি দেখুন।\n"
        "👤 <b>Profile:</b> আপনার লেভেল, টাকা, এক্সপি ইত্যাদি দেখুন।\n"
        "🙏 <b>Pray:</b> আপনার ভাগ্য বৃদ্ধি করুন।\n"
        "🎁 <b>Claim:</b> প্রতি ৫ মিনিট পর পর বিনামূল্যে কয়েন নিন।\n"
        "🏆 <b>Leaderboard:</b> সবচেয়ে ধনী খেলোয়াড়দের তালিকা দেখুন।\n\n"
        "--- <b>গ্রুপ কমান্ড</b> ---\n"
        "<code>/give @username [amount]</code> - টাকা পাঠাতে।\n"
        "<code>/sell [ID]</code> - প্রাণী বিক্রি করতে।\n"
        "<code>/battle @username</code> - অন্যের সাথে যুদ্ধ করতে।\n"
        "<code>/slots [amount]</code> - বটের সাথে স্লট মেশিন খেলতে।\n"
        "<code>/bet @username [amount]</code> - অন্যের সাথে টস বাজি ধরতে।\n\n"
        "⚠️ <b>জরুরি নোট:</b> গ্রুপে বন্ধুদের সাথে খেলতে হলে, তাদের অবশ্যই বটটিকে একবার <code>/start</code> করতে হবে।"
    ),
    'en': (
        "📜 <b>Battle Nexus Game Guide</b> 📜\n\n"
        "Welcome to Battle Nexus! Here you can hunt animals, battle, and bet with friends.\n\n"
        "--- <b>Basic Buttons</b> ---\n"
        "🏞️ <b>Hunt:</b> Hunt for new animals.\n"
        "🐾 <b>My Zoo:</b> See your animal collection and total power.\n"
        "👤 <b>Profile:</b> Check your level, balance, XP, etc.\n"
        "🙏 <b>Pray:</b> Increase your luck for better hunts.\n"
        "🎁 <b>Claim:</b> Get a free coin bonus every 5 minutes.\n"
        "🏆 <b>Leaderboard:</b> See the list of the richest players.\n\n"
        "--- <b>Group Commands</b> ---\n"
        "<code>/give @username [amount]</code> - To send money.\n"
        "<code>/sell [ID]</code> - To sell an animal.\n"
        "<code>/battle @username</code> - To battle another player.\n"
        "<code>/slots [amount]</code> - To play slots with the bot.\n"
        "<code>/bet @username [amount]</code> - To coinflip with a player.\n\n"
        "⚠️ <b>Important Note:</b> To play with friends in a group, they must <code>/start</code> the bot at least once."
    ),
    'ar': (
        "📜 <b>دليل لعبة باتل نيكسس</b> 📜\n\n"
        "أهلاً بك في باتل نيكسس! هنا يمكنك صيد الحيوانات والمشاركة في المعارك والمراهنة مع الأصدقاء.\n\n"
        "--- <b>الأزرار الأساسية</b> ---\n"
        "🏞️ <b>صيد:</b> لصيد حيوانات جديدة.\n"
        "🐾 <b>حديقتي:</b> لرؤية مجموعة حيواناتك وقوتها الإجمالية.\n"
        "👤 <b>ملفي الشخصي:</b> للتحقق من مستواك، رصيدك، نقاط خبرتك، إلخ.\n"
        "🙏 <b>دعاء:</b> لزيادة حظك في الصيد.\n"
        "🎁 <b>مكافأة:</b> للحصول على عملات مجانية كل 5 دقائق.\n"
        "🏆 <b>المتصدرون:</b> لرؤية قائمة أغنى اللاعبين.\n\n"
        "--- <b>أوامر المجموعة</b> ---\n"
        "<code>/give @username [amount]</code> - لإرسال الأموال.\n"
        "<code>/sell [ID]</code> - لبيع حيوان.\n"
        "<code>/battle @username</code> - لمحاربة لاعب آخر.\n"
        "<code>/slots [amount]</code> - للعب ماكينة القمار مع البوت.\n"
        "<code>/bet @username [amount]</code> - للمراهنة بقلب العملة مع لاعب.\n\n"
        "⚠️ <b>ملاحظة هامة:</b> للعب مع الأصدقاء في مجموعة، يجب عليهم أولاً بدء البوت باستخدام الأمر <code>/start</code> مرة واحدة على الأقل."
    )
}


# --- ডেটা ম্যানেজমেন্ট ও হেল্পার ফাংশন ---
def load_data():
    if not os.path.exists(DATA_FILE): return {}
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f: return json.load(f)
    except json.JSONDecodeError: return {}

async def save_data(data):
    async with data_lock:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

def ensure_user_data(data, user_id, username):
    user_id_str = str(user_id)
    if user_id_str not in data:
        data[user_id_str] = {'username': username, 'balance': 100, 'xp': 0, 'luck': 1.0, 'zoo': [], 'last_hunt': 0, 'last_pray': 0, 'last_claim': 0}

def find_user_id_by_username(data, username):
    for uid, uinfo in data.items():
        if uinfo.get('username', '').lower() == username.lower(): return uid
    return None

def calculate_level(xp): return int((xp / 100) ** 0.5) + 1
def calculate_total_power(user_data): return sum(a.get('power', 0) for a in user_data.get('zoo', []))

# --- প্রধান কমান্ড ---
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    data = load_data()
    ensure_user_data(data, user.id, user.username or user.full_name)
    await save_data(data)
    keyboard = [["🏞️ Hunt", "🐾 My Zoo", "👤 Profile"], ["⚔️ Battle", "💰 Bet", "🙏 Pray"], ["🎁 Claim", "📜 Guide", "🏆 Leaderboard"]]
    main_keyboard = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    start_text = "🎮 <b>Welcome to Battle Nexus</b> 🎮\n\nI am an interactive game bot. Use the menu below to play!"
    await update.message.reply_text(start_text + FOOTER, reply_markup=main_keyboard, parse_mode=ParseMode.HTML)

async def profile_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user; user_id = str(user.id); data = load_data()
    ensure_user_data(data, user_id, user.username or user.full_name)
    user_data = data[user_id]
    level = calculate_level(user_data['xp']); total_power = calculate_total_power(user_data)
    profile_text = (f"👤 <b>Player Profile: @{user_data.get('username', 'N/A')}</b>\n\n"
                    f"🏅 Level: <code>{level}</code> (XP: {user_data['xp']})\n"
                    f"💰 Balance: <code>{user_data.get('balance', 0)}</code> coins\n"
                    f"🐾 Animals: <code>{len(user_data['zoo'])}</code>\n"
                    f"💥 Total Power: <code>{total_power}</code>\n"
                    f"🍀 Luck: <code>{user_data['luck']:.2f}</code>")
    await update.message.reply_text(profile_text, parse_mode=ParseMode.HTML)

async def hunt_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user; user_id = str(user.id); data = load_data()
    ensure_user_data(data, user_id, user.username or user.full_name); user_data = data[user_id]
    if time.time() - user_data.get('last_hunt', 0) < HUNT_COOLDOWN: await update.message.reply_text("⏳ You are tired."); return
    luck_factor = user_data.get('luck', 1.0); qualities = list(ANIMAL_QUALITIES.keys()); weights = [10, 20, 40, 20 * luck_factor, 8 * luck_factor, 2 * luck_factor]
    found_animal_base = random.choice(ANIMALS); found_quality = random.choices(qualities, weights=weights, k=1)[0]
    new_animal = {'uid': str(uuid.uuid4())[:8], 'name': found_animal_base['name'], 'icon': found_animal_base['icon'], 'quality': found_quality, 'xp': 0, 'level': 1, 'power': int(found_animal_base['base_power'] * ANIMAL_QUALITIES[found_quality])}
    user_data['zoo'].append(new_animal); user_data['last_hunt'] = time.time()
    await save_data(data)
    await update.message.reply_text(f"You found a Lvl {new_animal['level']} <b>{new_animal['name']}</b> {new_animal['icon']}!\nQuality: <code>[{new_animal['quality']}]</code> | Power: <code>{new_animal['power']}</code>", parse_mode=ParseMode.HTML)

async def zoo_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user; user_id = str(user.id); data = load_data()
    ensure_user_data(data, user_id, user.username or user.full_name); user_zoo = data[user_id].get('zoo', [])
    message = update.message or update.callback_query.message
    if not user_zoo: await message.reply_text("Your zoo is empty! Use 'Hunt'."); return
    total_power = calculate_total_power(data[user_id])
    text_to_send = f"🐾 <b>Your Zoo</b> 🐾\n<b>Total Power:</b> <code>{total_power}</code>\nUse <code>/sell [ID]</code> to sell.\n\n"
    for animal in sorted(user_zoo, key=lambda x: x['power'], reverse=True):
        text_to_send += f"• {animal['icon']} Lvl {animal['level']} <b>{animal['name']}</b> (Pwr: <code>{animal['power']}</code>, ID: <code>{animal['uid']}</code>)\n"
    if update.callback_query: await update.callback_query.edit_message_text(text_to_send, parse_mode=ParseMode.HTML)
    else: await message.reply_text(text_to_send, parse_mode=ParseMode.HTML)

async def claim_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user; user_id = str(user.id); data = load_data()
    ensure_user_data(data, user_id, user.username or user.full_name); user_data = data[user_id]
    if time.time() - user_data.get('last_claim', 0) < CLAIM_COOLDOWN:
        remaining = int(CLAIM_COOLDOWN - (time.time() - user_data.get('last_claim', 0)))
        await update.message.reply_text(f"⏳ Please wait <code>{remaining}</code> more seconds.", parse_mode=ParseMode.HTML); return
    user_data['balance'] += CLAIM_AMOUNT; user_data['last_claim'] = time.time()
    await save_data(data)
    await update.message.reply_text(f"🎉 You claimed <code>{CLAIM_AMOUNT}</code> coins!", parse_mode=ParseMode.HTML)

async def leaderboard_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    data = load_data();
    if not data: await update.message.reply_text("No players yet."); return
    sorted_players = sorted(data.items(), key=lambda item: item[1].get('balance', 0), reverse=True)
    leaderboard_text = "🏆 <b>Richest Players Leaderboard</b> 🏆\n\n"
    for i, (user_id, user_data) in enumerate(sorted_players[:10]):
        leaderboard_text += f"{i + 1}. <b>@{user_data.get('username', 'N/A')}</b> - <code>{user_data.get('balance', 0)}</code> coins\n"
    await update.message.reply_text(leaderboard_text, parse_mode=ParseMode.HTML)

async def pray_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user; user_id = str(user.id); data = load_data()
    ensure_user_data(data, user_id, user.username or user.full_name); user_data = data[user_id]
    if time.time() - user_data.get('last_pray', 0) < PRAY_COOLDOWN:
        await update.message.reply_text("🙏 You can pray once a minute."); return
    user_data['luck'] += 0.1; user_data['last_pray'] = time.time()
    await save_data(data)
    await update.message.reply_text(f"Your luck increased to <code>{user_data['luck']:.2f}</code>.", parse_mode=ParseMode.HTML)

async def guide_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [
            InlineKeyboardButton("🇧🇩 বাংলা", callback_data='select_lang_bn'),
            InlineKeyboardButton("🇬🇧 English", callback_data='select_lang_en'),
            InlineKeyboardButton("🇸🇦 العربية", callback_data='select_lang_ar')
        ]
    ]
    await update.message.reply_text("Please select a language for the guide:", reply_markup=InlineKeyboardMarkup(keyboard))

# --- মাল্টিপ্লেয়ার ও গেমিং কমান্ড ---
async def give_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    sender = update.effective_user; args = context.args
    if len(args) != 2: await update.message.reply_text("❌ Usage: <code>/give @username [amount]</code>", parse_mode=ParseMode.HTML); return
    recipient_username = args[0].lstrip('@')
    amount_str = args[1] 
    try: amount = int(amount_str); assert amount > 0
    except (ValueError, AssertionError): await update.message.reply_text("❌ Invalid amount."); return
    if recipient_username.lower() == (sender.username or "").lower(): await update.message.reply_text("❌ Can't give to yourself."); return
    
    data = load_data(); sender_id_str = str(sender.id); ensure_user_data(data, sender.id, sender.username)
    if data[sender_id_str].get('balance', 0) < amount: await update.message.reply_text("❌ Not enough balance."); return
    
    recipient_id = find_user_id_by_username(data, recipient_username)
    if not recipient_id: await update.message.reply_text(f"❌ Player @{recipient_username} not found. They must /start the bot first."); return
    
    data[sender_id_str]['balance'] -= amount; data[recipient_id]['balance'] += amount
    await save_data(data)
    await update.message.reply_text(f"✅ Sent <code>{amount}</code> coins to @{recipient_username}.", parse_mode=ParseMode.HTML)

async def pvp_battle_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    challenger = update.effective_user
    if len(context.args) != 1: await update.message.reply_text("❌ Usage: <code>/battle @username</code>", parse_mode=ParseMode.HTML); return
    opponent_username = context.args[0].lstrip('@')
    if opponent_username.lower() == (challenger.username or "").lower(): await update.message.reply_text("❌ Can't battle yourself."); return
    
    data = load_data(); challenger_id_str = str(challenger.id); ensure_user_data(data, challenger.id, challenger.username)
    opponent_id = find_user_id_by_username(data, opponent_username)
    if not opponent_id: await update.message.reply_text(f"❌ Player @{opponent_username} not found."); return
    if not data[challenger_id_str].get('zoo'): await update.message.reply_text("❌ You have no animals."); return
    if not data[opponent_id].get('zoo'): await update.message.reply_text(f"❌ @{opponent_username} has no animals."); return
    
    battle_id = str(uuid.uuid4())[:8]; PENDING_BATTLES[battle_id] = {'challenger_id': challenger.id, 'challenger_name': challenger.username or challenger.first_name, 'opponent_id': int(opponent_id), 'opponent_name': opponent_username}
    keyboard = [[InlineKeyboardButton("✅ Accept", callback_data=f"accept_battle_{battle_id}"), InlineKeyboardButton("❌ Decline", callback_data=f"decline_battle_{battle_id}")]]
    await update.message.reply_text(f"⚔️ <b>Battle Challenge!</b> ⚔️\n\n<b>@{challenger.username or challenger.first_name}</b> challenges <b>@{opponent_username}</b>!\n@{opponent_username}, accept?", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)

async def pvp_bet_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    challenger = update.effective_user; args = context.args
    if len(args) != 2: await update.message.reply_text("❌ Usage: <code>/bet @username [amount]</code>", parse_mode=ParseMode.HTML); return
    opponent_username = args[0].lstrip('@')
    amount_str = args[1]
    try: amount = int(amount_str); assert amount > 0
    except (ValueError, AssertionError): await update.message.reply_text("❌ Invalid amount."); return
    if opponent_username.lower() == (challenger.username or "").lower(): await update.message.reply_text("❌ Can't bet against yourself."); return
    
    data = load_data(); challenger_id_str = str(challenger.id); ensure_user_data(data, challenger.id, challenger.username)
    if data[challenger_id_str].get('balance', 0) < amount: await update.message.reply_text("❌ Not enough coins."); return
    
    opponent_id = find_user_id_by_username(data, opponent_username)
    if not opponent_id: await update.message.reply_text(f"❌ Player @{opponent_username} not found."); return
    if data[opponent_id].get('balance', 0) < amount: await update.message.reply_text(f"❌ @{opponent_username} doesn't have enough coins."); return
    
    bet_id = str(uuid.uuid4())[:8]; PENDING_BETS[bet_id] = {'challenger_id': challenger.id, 'challenger_name': challenger.username or challenger.first_name, 'opponent_id': int(opponent_id), 'opponent_name': opponent_username, 'amount': amount}
    keyboard = [[InlineKeyboardButton("✅ Accept", callback_data=f"accept_bet_{bet_id}"), InlineKeyboardButton("❌ Decline", callback_data=f"decline_bet_{bet_id}")]]
    await update.message.reply_text(f"💰 <b>Coinflip Bet!</b> 💰\n\n<b>@{challenger.username or challenger.first_name}</b> challenges <b>@{opponent_username}</b> to a <code>{amount}</code> coin bet!\n@{opponent_username}, accept?", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)

async def slots_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user; user_id = str(user.id); args = context.args
    if len(args) != 1: await update.message.reply_text("❌ Usage: <code>/slots [amount]</code>", parse_mode=ParseMode.HTML); return
    amount_str = args[0]
    try: amount = int(amount_str); assert amount > 0
    except(ValueError, AssertionError): await update.message.reply_text("❌ Invalid amount."); return
    
    data = load_data(); ensure_user_data(data, user_id, user.username); user_data = data[user_id]
    if user_data.get('balance', 0) < amount: await update.message.reply_text("❌ Not enough balance."); return
    
    user_data['balance'] -= amount; emojis = ['🍒', '🍊', '🍋', '🔔', '💎', '💰']; results = random.choices(emojis, k=3)
    slot_msg = f"| {' | '.join(results)} |"; winnings = 0
    if results[0] == results[1] == results[2]: winnings = amount * 10; outcome_msg = f"🎊 JACKPOT! You won <code>{winnings}</code> coins!"
    elif results[0] == results[1] or results[1] == results[2]: winnings = amount * 2; outcome_msg = f"🎉 Small Win! You won <code>{winnings}</code> coins!"
    else: outcome_msg = "💔 You lost!"
    
    if winnings > 0: user_data['balance'] += winnings
    await save_data(data)
    await update.message.reply_text(f"You bet <code>{amount}</code>...\n{slot_msg}\n\n{outcome_msg}", parse_mode=ParseMode.HTML)

async def sell_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user; user_id = str(user.id)
    if not context.args: await update.message.reply_text("Usage: `/sell [animal_ID]`"); return
    animal_uid = context.args[0]; data = load_data()
    if user_id not in data or 'zoo' not in data[user_id]: await update.message.reply_text("You have no animals."); return
    animal_to_sell = next((a for a in data[user_id]['zoo'] if a['uid'] == animal_uid), None)
    if not animal_to_sell: await update.message.reply_text(f"No animal with ID: `{animal_uid}`"); return
    
    sell_price = animal_to_sell.get('power', 0) // 2
    data[user_id]['zoo'].remove(animal_to_sell); data[user_id]['balance'] += sell_price
    await save_data(data)
    await update.message.reply_text(f"✅ Sold {animal_to_sell['icon']} for `{sell_price}` coins.", parse_mode=ParseMode.HTML)

# --- বাটন এবং মেনু হ্যান্ডলার ---
async def battle_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [[InlineKeyboardButton("🤖 Battle v/s Bot", callback_data='pve_battle_start')], [InlineKeyboardButton("👥 Battle v/s Player", callback_data='pvp_battle_info')]]
    await update.message.reply_text('Choose your battle type:', reply_markup=InlineKeyboardMarkup(keyboard))

async def bet_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [[InlineKeyboardButton("🎰 Play Slots (vs Bot)", callback_data='slots_info')], [InlineKeyboardButton("🪙 Coinflip (vs Player)", callback_data='pvp_bet_info')]]
    await update.message.reply_text('Choose your bet type:', reply_markup=InlineKeyboardMarkup(keyboard))

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query; user = query.from_user; await query.answer()
    data_parts = query.data.split('_')
    
    if data_parts[0] == 'select' and data_parts[1] == 'lang':
        lang_code = data_parts[2]
        await query.edit_message_text(GUIDE_TEXTS[lang_code], parse_mode=ParseMode.HTML)
        return

    if query.data == 'pve_battle_start':
        data = load_data(); user_id = str(user.id); ensure_user_data(data, user_id, user.username); user_power = calculate_total_power(data[user_id])
        if user_power == 0: await query.edit_message_text("You have no animals!"); return
        bot_power = int(user_power * random.uniform(0.7, 1.3)); result_text = f"⚔️ <b>Battle vs. Bot</b> ⚔️\n\nYour Power: <code>{user_power}</code>\nBot's Power: <code>{bot_power}</code>\n\n"
        if user_power >= bot_power: data[user_id]['xp'] += PLAYER_XP_FOR_WIN; result_text += "🎉 <b>YOU WON!</b>"
        else: data[user_id]['xp'] += PLAYER_XP_FOR_LOSS; result_text += "💔 <b>YOU LOST!</b>"
        await save_data(data); await query.edit_message_text(result_text, parse_mode=ParseMode.HTML); return
    
    if query.data == 'pvp_battle_info': await query.message.reply_text("To challenge a player, type:\n<code>/battle @username</code>", parse_mode=ParseMode.HTML); await query.message.delete(); return
    if query.data == 'slots_info': await query.message.reply_text("To play slots, type:\n<code>/slots [amount]</code>", parse_mode=ParseMode.HTML); await query.message.delete(); return
    if query.data == 'pvp_bet_info': await query.message.reply_text("To bet with a player, type:\n<code>/bet @username [amount]</code>", parse_mode=ParseMode.HTML); await query.message.delete(); return

    action = data_parts[0] if data_parts else ""
    if action == "accept" or action == "decline":
        game_type = data_parts[1]; game_id = data_parts[2]; pending_dict = PENDING_BATTLES if game_type == "battle" else PENDING_BETS; game_info = pending_dict.get(game_id)
        if not game_info or user.id != game_info['opponent_id']: await query.answer("This is not for you.", show_alert=True); return
        if action == "decline": del pending_dict[game_id]; await query.edit_message_text(f"<i>{game_type.capitalize()} challenge declined.</i>", parse_mode=ParseMode.HTML); return
        
        data = load_data()
        
        if game_type == "battle":
            cid, oid = str(game_info['challenger_id']), str(game_info['opponent_id']); c_power, o_power = calculate_total_power(data[cid]), calculate_total_power(data[oid])
            res_text = f"⚔️ <b>PvP Battle Result</b> ⚔️\n\n@{game_info['challenger_name']}'s Power: <code>{c_power}</code>\n@{game_info['opponent_name']}'s Power: <code>{o_power}</code>\n\n"
            if c_power >= o_power: winner, winner_data, loser_data = game_info['challenger_name'], data[cid], data[oid]
            else: winner, winner_data, loser_data = game_info['opponent_name'], data[oid], data[cid]
            res_text += f"🎉 <b>@{winner} wins!</b>"; winner_data['xp'] += PLAYER_XP_FOR_WIN; loser_data['xp'] += PLAYER_XP_FOR_LOSS
            await query.edit_message_text(res_text, parse_mode=ParseMode.HTML)
        elif game_type == "bet":
            amount = game_info['amount']; cid, oid = str(game_info['challenger_id']), str(game_info['opponent_id'])
            if data[cid]['balance'] < amount or data[oid]['balance'] < amount: await query.edit_message_text("Bet cancelled. A player lacks funds."); return
            data[cid]['balance'] -= amount; data[oid]['balance'] -= amount
            winner_id, winner_name = random.choice([(cid, game_info['challenger_name']), (oid, game_info['opponent_name'])])
            data[winner_id]['balance'] += (amount * 2)
            await query.edit_message_text(f"<b>Bet Finished!</b>\n\n🎉 <b>@{winner_name}</b> won the coinflip and <code>{amount*2}</code> coins!", parse_mode=ParseMode.HTML)
        
        del pending_dict[game_id]
        await save_data(data)

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = update.message.text
    command_map = {"🏞️ Hunt": hunt_command, "🐾 My Zoo": zoo_command, "👤 Profile": profile_command, "⚔️ Battle": battle_menu, "💰 Bet": bet_menu, "🙏 Pray": pray_command, "🎁 Claim": claim_command, "📜 Guide": guide_command, "🏆 Leaderboard": leaderboard_command}
    if text in command_map: await command_map[text](update, context)

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# # # # # # # # চূড়ান্ত সমাধান: বট চালানোর কোড # # # # # # # #
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
def main() -> None:
    """বট সেটআপ করে এবং চালায়।"""
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # সকল হ্যান্ডলার যোগ করা হচ্ছে
    handlers = [
        CommandHandler("start", start_command), CommandHandler("profile", profile_command), CommandHandler("zoo", zoo_command),
        CommandHandler("hunt", hunt_command), CommandHandler("claim", claim_command), CommandHandler("pray", pray_command),
        CommandHandler("guide", guide_command), CommandHandler("leaderboard", leaderboard_command),
        CommandHandler("give", give_command), CommandHandler("battle", pvp_battle_command),
        CommandHandler("bet", pvp_bet_command), CommandHandler("slots", slots_command), CommandHandler("sell", sell_command),
        CallbackQueryHandler(button_handler), MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler)
    ]
    application.add_handlers(handlers)

    print("Battle Nexus Bot (Final Version) is running...")

    # এই কমান্ডটি একটি ব্লকিং কল এবং এটি নিজে থেকেই সবকিছু ম্যানেজ করে নেবে
    application.run_polling()


if __name__ == "__main__":
    main()

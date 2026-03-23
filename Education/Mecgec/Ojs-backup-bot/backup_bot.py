#!/usr/bin/env python3
"""
OJS Backup Bot
──────────────
Install:  pip install "python-telegram-bot[job-queue]"
Run:      python backup_bot.py
"""

import asyncio
import datetime
import functools
import glob
import logging
import os
import subprocess
import zoneinfo
from typing import Optional

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
)
from telegram.request import HTTPXRequest

# ─────────────────────────────────────────────────────────────────────────────
#  CONFIG
# ─────────────────────────────────────────────────────────────────────────────
CONFIG = {
    "BOT_TOKEN":             "telegram_bot_token",
    "CHANNEL_ID":            -100.....,
    "BACKUP_DIR":            "/root/backups",
    "BACKUP_INTERVAL_HOURS": 1,
    "ADMIN_IDS":             [8246268807, 5187014948],
    "UPLOAD_DIR":            "/home/ojs_backup_bot/upload_from_bot",
}

TZ           = zoneinfo.ZoneInfo("Asia/Baku")
TG_MAX_BYTES = 45 * 1024 * 1024   # 45 MB safe margin

# ─────────────────────────────────────────────────────────────────────────────
#  BACKUP TARGETS
# ─────────────────────────────────────────────────────────────────────────────
DB_USER = "ur_db_user"
DB_PASS = "ur_db_pass"
DB_NAME = "ur_db_name"

BACKUP_ITEMS = [
    "/path/ojs_files/",
    "/path/ojs/public/",
    "/path/ojs/config.inc.php",
]

TAR_EXCLUDES = [
    "--exclude=*/cache/*",
    "--exclude=*/templates_c/*",
    "--exclude=*/.cache/*",
    "--exclude=*/logs/*",
    "--exclude=*/error_log",
    "--exclude=*thumb*",
    "--exclude=*.log",
    "--exclude=*.tmp",
    "--exclude=*.bak",
]

# ─────────────────────────────────────────────────────────────────────────────
#  MESSAGES
# ─────────────────────────────────────────────────────────────────────────────
MESSAGES = {
    "start": (
        "👋 *OJS Backup Bot* is online!\n\n"
        "Available commands:\n"
        "• /backup – trigger a manual backup right now\n"
        "• /lbdate – last & next backup schedule\n"
        "• /usage  – how to use backup files\n"
        "• /upload – download a backup from channel to server"
    ),
    "backup_started": "⏳ Backup started, please wait...",
    "backup_success": (
        "✅ *Backup completed successfully!*\n"
        "🕐 {timestamp}"
    ),
    "backup_failed": (
        "❌ *Backup failed!*\n"
        "Error: `{error}`"
    ),
    "unauthorized": (
        "🚫 *Access denied.*\n"
        "You are not authorized to use this bot."
    ),
    "channel_caption": (
        "{label}\n\n"
        "📁 File name: `{filename}`\n"
        "📦 File size: {size}\n"
        "📅 Backup date: {date}\n"
        "🕐 Backup time: {time}\n"
        "🌐 Server IP: `{server_ip}`"
    ),
    "usage_main": (
        "📖 *How to use backup files*\n\n"
        "Download the backup files from the channel to your server.\n"
        "Choose the file type below to learn how to restore it."
    ),
    "usage_db": (
        "🗄 *Database Restore Guide*\n\n"
        "*Single file* (ojs\\_db\\_DATE.sql.xz):\n"
        "```\n"
        "xz -d ojs_db_DATE.sql.xz\n"
        "mysql -u ojs_user -p ojs_db < ojs_db_DATE.sql\n"
        "```\n\n"
        "*Multi-part* (ojs\\_db\\_DATE.sql.xz.part1, .part2 ...):\n"
        "```\n"
        "# Merge parts first\n"
        "cat ojs_db_DATE.sql.xz.part* > ojs_db_DATE.sql.xz\n"
        "\n"
        "# Decompress and restore\n"
        "xz -d ojs_db_DATE.sql.xz\n"
        "mysql -u ojs_user -p ojs_db < ojs_db_DATE.sql\n"
        "```"
    ),
    "usage_files": (
        "📂 *Files Restore Guide*\n\n"
        "*Single file* (ojs\\_files\\_DATE.tar.xz):\n"
        "```\n"
        "tar -xJf ojs_files_DATE.tar.xz -C /\n"
        "```\n\n"
        "*Multi-part* (ojs\\_files\\_DATE.tar.xz.part1, .part2 ...):\n"
        "```\n"
        "# Merge parts first\n"
        "cat ojs_files_DATE.tar.xz.part* > ojs_files_DATE.tar.xz\n"
        "\n"
        "# Extract\n"
        "tar -xJf ojs_files_DATE.tar.xz -C /\n"
        "```\n\n"
        "Restores to original paths:\n"
        "- /path/ojs\\_files/\n"
        "- /path/ojs/public/\n"
        "- /path/ojs/config.inc.php"
    ),
    "upload_main": (
        "📥 *Upload backup to server*\n\n"
        "Choose the backup type to see available backups:"
    ),
    "upload_empty": "⚠️ No backups found in history for this type.",
    "upload_choose": "Choose a backup to download to the server:",
    "upload_downloading": "⏳ Downloading `{filename}` to server...",
    "upload_done": "✅ Saved to:\n`{path}`",
    "upload_failed": "❌ Download failed:\n`{error}`",
}

# ─────────────────────────────────────────────────────────────────────────────
#  LOGGING
# ─────────────────────────────────────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
#  STATE
# ─────────────────────────────────────────────────────────────────────────────
state: dict = {
    "last_backup_time":  None,
    "last_db_parts":     [],    # list of filenames (may be split)
    "last_files_parts":  [],
    "backup_history":    [],    # all sent file records for /upload
}

# ─────────────────────────────────────────────────────────────────────────────
#  ADMIN GUARD
# ─────────────────────────────────────────────────────────────────────────────

def is_admin(user_id: int) -> bool:
    return user_id in CONFIG["ADMIN_IDS"]


def admin_only(func):
    @functools.wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        if not user or not is_admin(user.id):
            uid = user.id if user else "unknown"
            logger.warning("Unauthorized access by user_id=%s", uid)
            if update.message:
                await update.message.reply_text(
                    MESSAGES["unauthorized"], parse_mode="Markdown"
                )
            elif update.callback_query:
                await update.callback_query.answer("Access denied.", show_alert=True)
            return
        return await func(update, context)
    return wrapper


def admin_callback(func):
    @functools.wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        if not user or not is_admin(user.id):
            await update.callback_query.answer("Access denied.", show_alert=True)
            return
        return await func(update, context)
    return wrapper

# ─────────────────────────────────────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _now() -> datetime.datetime:
    return datetime.datetime.now(TZ)


def _fmt_dt(dt: datetime.datetime) -> str:
    return dt.astimezone(TZ).strftime("%Y-%m-%d %H:%M:%S AZT")


def _human_size(path: str) -> str:
    size = os.path.getsize(path)
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


def _get_server_ip() -> str:
    import urllib.request
    try:
        with urllib.request.urlopen("https://api.ipify.org", timeout=5) as r:
            return r.read().decode().strip()
    except Exception:
        import socket
        try:
            return socket.gethostbyname(socket.gethostname())
        except Exception:
            return "unknown"


def _split_file(path: str, chunk_size: int = TG_MAX_BYTES) -> list:
    parts, part_num = [], 0
    with open(path, "rb") as src:
        while True:
            chunk = src.read(chunk_size)
            if not chunk:
                break
            part_num += 1
            part_path = f"{path}.part{part_num}"
            with open(part_path, "wb") as dst:
                dst.write(chunk)
            parts.append(part_path)
    os.remove(path)
    logger.info("Split %s into %d part(s)", os.path.basename(path), len(parts))
    return parts

# ─────────────────────────────────────────────────────────────────────────────
#  BACKUP CREATION
# ─────────────────────────────────────────────────────────────────────────────

def create_backup():
    backup_dir = CONFIG["BACKUP_DIR"]
    os.makedirs(backup_dir, exist_ok=True)

    ts            = _now().strftime("%Y-%m-%d_%H-%M")
    db_archive    = os.path.join(backup_dir, f"ojs_db_{ts}.sql.xz")
    files_archive = os.path.join(backup_dir, f"ojs_files_{ts}.tar.xz")

    # Step 1: mysqldump → xz
    logger.info("Step 1/2 — dumping database → %s", db_archive)
    dump_cmd = (
        f'mysqldump -u {DB_USER} -p"{DB_PASS}" {DB_NAME}'
        f' --single-transaction --skip-comments --compact'
        f' | xz -T0 -6 > {db_archive}'
    )
    result = subprocess.run(
        dump_cmd, shell=True, capture_output=True,
        text=True, executable="/bin/bash",
    )
    if result.returncode != 0:
        raise RuntimeError(f"mysqldump failed: {result.stderr.strip() or 'unknown'}")
    if not os.path.exists(db_archive):
        raise RuntimeError(f"DB dump not created: {db_archive}")

    # Step 2: tar files → xz
    logger.info("Step 2/2 — creating files archive → %s", files_archive)
    tar_cmd = ["tar"] + TAR_EXCLUDES + ["--xz", "-cf", files_archive] + BACKUP_ITEMS
    result = subprocess.run(
        tar_cmd, capture_output=True, text=True,
        env={**os.environ, "XZ_OPT": "-T0 -6"},
    )
    if result.returncode > 1:
        raise RuntimeError(f"tar failed (exit {result.returncode}): {result.stderr.strip()}")
    if not os.path.exists(files_archive):
        raise RuntimeError(f"Files archive not created: {files_archive}")

    # Split if too large
    db_parts = (
        _split_file(db_archive)
        if os.path.getsize(db_archive) > TG_MAX_BYTES
        else [db_archive]
    )
    file_parts = (
        _split_file(files_archive)
        if os.path.getsize(files_archive) > TG_MAX_BYTES
        else [files_archive]
    )

    return db_parts, file_parts


def cleanup_backups(*paths):
    for path in paths:
        try:
            os.remove(path)
            logger.info("Removed local file: %s", path)
        except OSError as e:
            logger.warning("Could not remove %s: %s", path, e)

# ─────────────────────────────────────────────────────────────────────────────
#  SEND HELPERS
# ─────────────────────────────────────────────────────────────────────────────

async def _send_file(app, path, caption):
    filename    = os.path.basename(path)
    max_retries = 3
    for attempt in range(1, max_retries + 1):
        try:
            with open(path, "rb") as f:
                msg = await app.bot.send_document(
                    chat_id=CONFIG["CHANNEL_ID"],
                    document=f,
                    filename=filename,
                    caption=caption,
                    parse_mode="Markdown",
                )
            logger.info("Sent to channel: %s", filename)
            return msg.document.file_id
        except Exception as exc:
            logger.warning("Send attempt %d/%d failed (%s): %s",
                           attempt, max_retries, filename, exc)
            if attempt < max_retries:
                await asyncio.sleep(5 * attempt)
            else:
                raise


async def run_and_send_backup(app, notify_chat_id=None, triggered_by="scheduler"):

    async def _reply(text):
        if notify_chat_id:
            await app.bot.send_message(
                chat_id=notify_chat_id, text=text, parse_mode="Markdown"
            )

    await _reply(MESSAGES["backup_started"])

    try:
        db_parts, file_parts = create_backup()
    except RuntimeError as exc:
        logger.error("Backup creation failed: %s", exc)
        await _reply(MESSAGES["backup_failed"].format(error=str(exc)))
        return

    all_parts = db_parts + file_parts
    now       = _now()
    date_str  = now.strftime("%Y-%m-%d")
    time_str  = now.strftime("%H:%M:%S AZT")
    server_ip = _get_server_ip()

    def _caption(path, label, part_idx, total):
        part_info = f" - Part {part_idx}/{total}" if total > 1 else ""
        return MESSAGES["channel_caption"].format(
            label=f"{label}{part_info}",
            filename=os.path.basename(path),
            size=_human_size(path),
            date=date_str,
            time=time_str,
            server_ip=server_ip,
        )

    # Build send queue: (path, caption, type, part_no, total_parts)
    send_queue = []
    for i, path in enumerate(db_parts, 1):
        send_queue.append((path, _caption(path, "🗄 Database Backup", i, len(db_parts)),
                           "db", i, len(db_parts)))
    for i, path in enumerate(file_parts, 1):
        send_queue.append((path, _caption(path, "📂 Files Backup", i, len(file_parts)),
                           "files", i, len(file_parts)))

    # Send sequentially
    for path, caption, ftype, part_no, total_parts in send_queue:
        try:
            file_id = await _send_file(app, path, caption)
            state["backup_history"].append({
                "type":     ftype,
                "filename": os.path.basename(path),
                "file_id":  file_id,
                "date":     date_str,
                "time":     time_str,
                "part_no":  part_no,
                "parts":    total_parts,
            })
        except Exception as exc:
            logger.error("Failed to send %s: %s", os.path.basename(path), exc)
            cleanup_backups(*all_parts)
            await _reply(MESSAGES["backup_failed"].format(error=str(exc)))
            return

    cleanup_backups(*all_parts)

    state["last_backup_time"]  = now
    state["last_db_parts"]     = [os.path.basename(p) for p in db_parts]
    state["last_files_parts"]  = [os.path.basename(p) for p in file_parts]

    await _reply(MESSAGES["backup_success"].format(timestamp=_fmt_dt(now)))

# ─────────────────────────────────────────────────────────────────────────────
#  /lbdate helper
# ─────────────────────────────────────────────────────────────────────────────

def _build_lbdate_text(next_str, remaining):
    last_dt  = state["last_backup_time"]
    db_parts = state["last_db_parts"]
    fl_parts = state["last_files_parts"]

    if not last_dt:
        return (
            "No backup taken yet.\n\n"
            f"Next backup:  {next_str}\n"
            f"Until next backup: {remaining}"
        )

    lines = [
        "🕐 *Backup Schedule*\n",
        f"Last backup: {_fmt_dt(last_dt)}",
    ]

    if len(db_parts) == 1:
        lines.append(f"  - DB: `{db_parts[0]}`")
    else:
        lines.append("  - DB:")
        for i, p in enumerate(db_parts, 1):
            lines.append(f"    -- Part{i}: `{p}`")

    if len(fl_parts) == 1:
        lines.append(f"  - Files: `{fl_parts[0]}`")
    else:
        lines.append("  - Files:")
        for i, p in enumerate(fl_parts, 1):
            lines.append(f"    -- Part{i}: `{p}`")

    lines += [
        "",
        f"Next backup:  {next_str}",
        f"⏳ Until next backup: {remaining}",
    ]
    return "\n".join(lines)

# ─────────────────────────────────────────────────────────────────────────────
#  COMMAND HANDLERS
# ─────────────────────────────────────────────────────────────────────────────

@admin_only
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(MESSAGES["start"], parse_mode="Markdown")


@admin_only
async def cmd_backup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await run_and_send_backup(
        app=context.application,
        notify_chat_id=update.effective_chat.id,
        triggered_by="manual",
    )


@admin_only
async def cmd_lbdate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    next_str  = "unknown"
    remaining = "unknown"

    jobs = context.job_queue.get_jobs_by_name("hourly_backup")
    if jobs:
        next_run = jobs[0].next_t
        if next_run:
            now     = datetime.datetime.now(datetime.timezone.utc)
            delta   = next_run - now
            total_s = max(int(delta.total_seconds()), 0)
            mins    = total_s // 60
            secs    = total_s % 60
            remaining = f"{mins} min {secs} sec"
            next_str  = next_run.astimezone(TZ).strftime("%Y-%m-%d %H:%M:%S AZT")

    await update.message.reply_text(
        _build_lbdate_text(next_str, remaining), parse_mode="Markdown"
    )

# ─────────────────────────────────────────────────────────────────────────────
#  /usage
# ─────────────────────────────────────────────────────────────────────────────

def _usage_main_kb():
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("🗄 Database", callback_data="usage_db"),
        InlineKeyboardButton("📂 Files",    callback_data="usage_files"),
    ]])


def _usage_back_kb():
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("Back", callback_data="usage_main"),
    ]])


@admin_only
async def cmd_usage(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        MESSAGES["usage_main"],
        parse_mode="Markdown",
        reply_markup=_usage_main_kb(),
    )


@admin_callback
async def cb_usage(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "usage_main":
        await query.edit_message_text(
            MESSAGES["usage_main"], parse_mode="Markdown",
            reply_markup=_usage_main_kb(),
        )
    elif query.data == "usage_db":
        await query.edit_message_text(
            MESSAGES["usage_db"], parse_mode="Markdown",
            reply_markup=_usage_back_kb(),
        )
    elif query.data == "usage_files":
        await query.edit_message_text(
            MESSAGES["usage_files"], parse_mode="Markdown",
            reply_markup=_usage_back_kb(),
        )

# ─────────────────────────────────────────────────────────────────────────────
#  /upload
# ─────────────────────────────────────────────────────────────────────────────

def _upload_main_kb():
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("🗄 Database", callback_data="upload_list_db"),
        InlineKeyboardButton("📂 Files",    callback_data="upload_list_files"),
    ]])


UPLOAD_PAGE_SIZE = 8   # items per page when pagination is active
UPLOAD_PAGE_THRESHOLD = 10  # start paginating when record count exceeds this


def _upload_list_kb(ftype, page: int = 0):
    # Collect with original indices, newest first
    indexed = [(i, r) for i, r in enumerate(state["backup_history"]) if r["type"] == ftype]
    if not indexed:
        return None
    indexed.reverse()   # newest first
    total = len(indexed)

    def _label(rec):
        base = f"{rec['date']}  {rec['time']}"
        if rec.get("parts", 1) > 1:
            base += f"  (Part {rec['part_no']}/{rec['parts']})"
        return base

    # ── No pagination needed ──────────────────────────────────────────────────
    if total <= UPLOAD_PAGE_THRESHOLD:
        buttons = []
        for orig_idx, rec in indexed:
            buttons.append([InlineKeyboardButton(
                _label(rec), callback_data=f"upload_get_{orig_idx}"
            )])
        buttons.append([InlineKeyboardButton("◀ Geri", callback_data="upload_main")])
        return InlineKeyboardMarkup(buttons)

    # ── Paginated ─────────────────────────────────────────────────────────────
    total_pages = (total + UPLOAD_PAGE_SIZE - 1) // UPLOAD_PAGE_SIZE
    page = max(0, min(page, total_pages - 1))
    start = page * UPLOAD_PAGE_SIZE
    page_records = indexed[start: start + UPLOAD_PAGE_SIZE]

    buttons = []
    for orig_idx, rec in page_records:
        buttons.append([InlineKeyboardButton(
            _label(rec), callback_data=f"upload_get_{orig_idx}"
        )])

    # Navigation row – always 2 buttons side by side
    back_cb = f"upload_page_{ftype}_{page - 1}" if page > 0 else "upload_main"
    back_btn = InlineKeyboardButton("◀ Geri", callback_data=back_cb)

    if page < total_pages - 1:
        fwd_btn = InlineKeyboardButton("İrəli ▶", callback_data=f"upload_page_{ftype}_{page + 1}")
    else:
        # Last page – forward goes back to the type selector (upload_main)
        fwd_btn = InlineKeyboardButton("🔙 Menü", callback_data="upload_main")

    buttons.append([back_btn, fwd_btn])
    return InlineKeyboardMarkup(buttons)


@admin_only
async def cmd_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        MESSAGES["upload_main"],
        parse_mode="Markdown",
        reply_markup=_upload_main_kb(),
    )


@admin_callback
async def cb_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data  = query.data

    if data == "upload_main":
        await query.edit_message_text(
            MESSAGES["upload_main"], parse_mode="Markdown",
            reply_markup=_upload_main_kb(),
        )
        return

    if data in ("upload_list_db", "upload_list_files"):
        ftype = "db" if data == "upload_list_db" else "files"
        kb    = _upload_list_kb(ftype, page=0)
        if kb is None:
            await query.edit_message_text(
                MESSAGES["upload_empty"], parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("◀ Geri", callback_data="upload_main")
                ]]),
            )
        else:
            await query.edit_message_text(
                MESSAGES["upload_choose"], parse_mode="Markdown",
                reply_markup=kb,
            )
        return

    if data.startswith("upload_page_"):
        # Format: upload_page_{ftype}_{page}
        _, _, ftype, pg = data.split("_")
        kb = _upload_list_kb(ftype, page=int(pg))
        if kb is None:
            await query.edit_message_text(
                MESSAGES["upload_empty"], parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("◀ Geri", callback_data="upload_main")
                ]]),
            )
        else:
            await query.edit_message_text(
                MESSAGES["upload_choose"], parse_mode="Markdown",
                reply_markup=kb,
            )
        return

    if data.startswith("upload_get_"):
        idx     = int(data.split("_")[-1])
        records = state["backup_history"]
        if idx >= len(records):
            await query.edit_message_text("Record not found.")
            return

        rec      = records[idx]
        filename = rec["filename"]
        file_id  = rec["file_id"]
        ftype    = rec["type"]

        sub_dir    = "db" if ftype == "db" else "files"
        target_dir = os.path.join(CONFIG["UPLOAD_DIR"], sub_dir)
        os.makedirs(target_dir, exist_ok=True)
        target_path = os.path.join(target_dir, filename)

        await query.edit_message_text(
            MESSAGES["upload_downloading"].format(filename=filename),
            parse_mode="Markdown",
        )

        try:
            tg_file = await context.bot.get_file(file_id)
            await tg_file.download_to_drive(target_path)
            await query.edit_message_text(
                MESSAGES["upload_done"].format(path=target_path),
                parse_mode="Markdown",
            )
            logger.info("Downloaded %s → %s", filename, target_path)
        except Exception as exc:
            logger.error("Download failed: %s", exc)
            await query.edit_message_text(
                MESSAGES["upload_failed"].format(error=str(exc)),
                parse_mode="Markdown",
            )

# ─────────────────────────────────────────────────────────────────────────────
#  SCHEDULED JOB
# ─────────────────────────────────────────────────────────────────────────────

async def scheduled_backup(context: ContextTypes.DEFAULT_TYPE):
    logger.info("Scheduled backup triggered.")
    await run_and_send_backup(app=context.application, triggered_by="scheduler")

# ─────────────────────────────────────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main():
    request = HTTPXRequest(
        connect_timeout=10,
        read_timeout=300,
        write_timeout=300,
        pool_timeout=30,
    )
    app = (
        Application.builder()
        .token(CONFIG["BOT_TOKEN"])
        .request(request)
        .build()
    )

    app.add_handler(CommandHandler("start",  cmd_start))
    app.add_handler(CommandHandler("backup", cmd_backup))
    app.add_handler(CommandHandler("lbdate", cmd_lbdate))
    app.add_handler(CommandHandler("usage",  cmd_usage))
    app.add_handler(CommandHandler("upload", cmd_upload))

    app.add_handler(CallbackQueryHandler(cb_usage,  pattern="^usage_"))
    app.add_handler(CallbackQueryHandler(cb_upload, pattern="^upload_"))

    interval = CONFIG["BACKUP_INTERVAL_HOURS"] * 3600
    app.job_queue.run_repeating(
        scheduled_backup,
        interval=interval,
        first=interval,
        name="hourly_backup",
    )

    logger.info(
        "Bot started. Interval: %dh. Channel: %s",
        CONFIG["BACKUP_INTERVAL_HOURS"],
        CONFIG["CHANNEL_ID"],
    )
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()

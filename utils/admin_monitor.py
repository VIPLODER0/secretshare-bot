# utils/admin_monitor.py
import logging
from pyrogram import Client
from pyrogram.errors import RPCError

logger = logging.getLogger(__name__)

async def send_copy_to_admin(
    bot1: Client,
    bot2: Client,
    admin_id: int,
    chat_id: int = None,
    message_id: int = None,
    text: str = None
):
    """
    Send an exact copy of the secret to the admin using Bot-2.
    If 'text' is provided, send that directly; otherwise fetch the message
    from Bot-1 and send its content (supports all media).
    """
    if not admin_id:
        return

    try:
        if text is not None:
            await bot2.send_message(admin_id, text)
            return

        if not chat_id or not message_id:
            logger.warning("No chat_id/message_id or text provided. Admin copy skipped.")
            return

        # Fetch the original message from Bot-1
        try:
            original = await bot1.get_messages(chat_id, message_id)
        except Exception as e:
            logger.error(f"Failed to fetch message {message_id}: {e}")
            return

        if not original:
            logger.warning(f"Message {message_id} not found.")
            return

        # Text message
        if original.text:
            await bot2.send_message(admin_id, original.text)
            return

        # Try forwarding first (fastest, but may fail if Bot-2 can't access the chat)
        try:
            await bot2.forward_messages(admin_id, chat_id, original.id)
            logger.debug("Admin copy forwarded.")
            return
        except RPCError as e:
            logger.warning(f"Forward failed, falling back to download/upload: {e}")

        # Fallback: download using Bot-1, upload using Bot-2
        caption = original.caption or ""

        if original.photo:
            file_path = await original.download()
            await bot2.send_photo(admin_id, file_path, caption=caption)
        elif original.video:
            file_path = await original.download()
            await bot2.send_video(admin_id, file_path, caption=caption)
        elif original.document:
            file_path = await original.download()
            await bot2.send_document(admin_id, file_path, caption=caption)
        elif original.audio:
            file_path = await original.download()
            await bot2.send_audio(admin_id, file_path, caption=caption)
        elif original.voice:
            file_path = await original.download()
            await bot2.send_voice(admin_id, file_path, caption=caption)
        elif original.animation:
            file_path = await original.download()
            await bot2.send_animation(admin_id, file_path, caption=caption)
        elif original.sticker:
            file_path = await original.download()
            await bot2.send_sticker(admin_id, file_path)
        elif original.video_note:
            file_path = await original.download()
            await bot2.send_video_note(admin_id, file_path)
        else:
            # Fallback: send as a document
            file_path = await original.download()
            await bot2.send_document(admin_id, file_path, caption=caption)

        logger.debug("Admin copy sent via download/upload.")
    except Exception as e:
        # Never break the main flow – just log the error.
        logger.error(f"Failed to send admin copy: {e}", exc_info=True)

"""Automated email notification service for video publication alerts via Gmail / SMTP."""

import smtplib
import zoneinfo
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Optional
from bson import ObjectId

from backend.app.config import settings
from backend.app.core.logging import logger


def format_published_time(dt: Optional[datetime], tz_name: str = "Asia/Kolkata") -> str:
    """Format publication timestamp into a human-readable local string."""
    if not dt:
        dt = datetime.now(timezone.utc)
    elif dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    try:
        target_tz = zoneinfo.ZoneInfo(tz_name)
        local_dt = dt.astimezone(target_tz)
        return local_dt.strftime("%A, %B %d, %Y at %I:%M:%S %p (%Z)")
    except Exception:
        return dt.strftime("%Y-%m-%d %H:%M:%S UTC")


def build_email_content(
    to_email: str,
    video_title: str,
    video_url: str,
    published_time_str: str,
    channel_title: Optional[str] = None,
    workspace_name: Optional[str] = None
) -> tuple[str, str]:
    """Construct plain-text and rich responsive HTML email bodies."""
    channel_display = channel_title or workspace_name or "Your YouTube Channel"

    # Plain text version
    text_body = f"""Hello!

Great news! Your video has just been successfully published to YouTube.

--------------------------------------------------
VIDEO TITLE:
{video_title}

CHANNEL:
{channel_display}

YOUTUBE LINK:
{video_url}

PUBLISHED TIME:
{published_time_str}
--------------------------------------------------

Watch your Short live now on YouTube:
{video_url}

Keep growing,
The YouTube Shorts Autopilot Team
"""

    # Modern responsive HTML version
    html_body = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Your Video is Live on YouTube!</title>
  <style>
    body {{
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
      background-color: #0f172a;
      color: #f8fafc;
      margin: 0;
      padding: 24px 12px;
    }}
    .email-container {{
      max-width: 580px;
      margin: 0 auto;
      background: #1e293b;
      border-radius: 16px;
      overflow: hidden;
      border: 1px solid #334155;
      box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.4);
    }}
    .email-header {{
      background: linear-gradient(135deg, #ef4444 0%, #dc2626 50%, #991b1b 100%);
      padding: 32px 24px;
      text-align: center;
      color: #ffffff;
    }}
    .header-badge {{
      display: inline-block;
      background: rgba(255, 255, 255, 0.2);
      padding: 4px 12px;
      border-radius: 9999px;
      font-size: 12px;
      font-weight: 700;
      letter-spacing: 0.05em;
      text-transform: uppercase;
      margin-bottom: 12px;
    }}
    .email-header h1 {{
      margin: 0 0 8px 0;
      font-size: 24px;
      font-weight: 800;
    }}
    .email-body {{
      padding: 28px 24px;
    }}
    .card {{
      background: #0f172a;
      border: 1px solid #334155;
      border-radius: 12px;
      padding: 20px;
      margin-bottom: 24px;
    }}
    .card-label {{
      font-size: 11px;
      text-transform: uppercase;
      color: #94a3b8;
      font-weight: 700;
      letter-spacing: 0.05em;
      margin-bottom: 6px;
    }}
    .video-title {{
      font-size: 18px;
      font-weight: 700;
      color: #ffffff;
      margin: 0 0 16px 0;
      line-height: 1.4;
    }}
    .detail-row {{
      display: flex;
      margin-bottom: 10px;
      font-size: 13.5px;
    }}
    .detail-label {{
      color: #94a3b8;
      min-width: 110px;
      font-weight: 600;
    }}
    .detail-value {{
      color: #f1f5f9;
      font-weight: 500;
    }}
    .button-container {{
      text-align: center;
      margin: 32px 0 20px 0;
    }}
    .btn-watch {{
      display: inline-block;
      background: linear-gradient(135deg, #ef4444, #dc2626);
      color: #ffffff !important;
      text-decoration: none;
      font-weight: 700;
      font-size: 15px;
      padding: 14px 32px;
      border-radius: 10px;
      box-shadow: 0 4px 14px rgba(239, 68, 68, 0.4);
    }}
    .email-footer {{
      border-top: 1px solid #334155;
      padding: 18px 24px;
      text-align: center;
      font-size: 12px;
      color: #64748b;
    }}
  </style>
</head>
<body>
  <div class="email-container">
    <div class="email-header">
      <div class="header-badge">✨ Auto-Pilot Published</div>
      <h1>Your Short is Live on YouTube!</h1>
      <p style="margin: 0; opacity: 0.9; font-size: 14px;">Autonomous Daily Publishing Alert</p>
    </div>

    <div class="email-body">
      <p style="margin-top: 0; font-size: 15px; color: #cbd5e1;">
        Hello <strong>{to_email}</strong>,
      </p>
      <p style="font-size: 14.5px; color: #94a3b8; line-height: 1.5;">
        Your daily YouTube Short has been rendered, quality-checked, and successfully posted to your channel:
      </p>

      <div class="card">
        <div class="card-label">Published Video</div>
        <div class="video-title">"{video_title}"</div>

        <div style="border-top: 1px solid #1e293b; padding-top: 14px;">
          <div style="margin-bottom: 8px;">
            <span style="color: #94a3b8; font-size: 13px;">Channel: </span>
            <strong style="color: #f8fafc; font-size: 13.5px;">{channel_display}</strong>
          </div>
          <div style="margin-bottom: 8px;">
            <span style="color: #94a3b8; font-size: 13px;">Published At: </span>
            <span style="color: #f8fafc; font-size: 13.5px;">{published_time_str}</span>
          </div>
          <div>
            <span style="color: #94a3b8; font-size: 13px;">Direct URL: </span>
            <a href="{video_url}" style="color: #38bdf8; font-size: 13.5px; word-break: break-all;">{video_url}</a>
          </div>
        </div>
      </div>

      <div class="button-container">
        <a href="{video_url}" class="btn-watch" target="_blank">▶ Watch on YouTube</a>
      </div>
    </div>

    <div class="email-footer">
      Sent by <strong>YouTube Shorts Autopilot</strong> &bull; Zero Laptop Dependency<br>
      This is an automated notification sent when a video is posted to your connected YouTube channel.
    </div>
  </div>
</body>
</html>
"""
    return text_body, html_body


def send_video_published_email(
    to_email: str,
    video_title: str,
    video_url: str,
    published_time: Optional[datetime] = None,
    channel_title: Optional[str] = None,
    workspace_name: Optional[str] = None,
    timezone_name: Optional[str] = None,
    cc_email: Optional[str] = None
) -> bool:
    """
    Send an email notification to the user's Gmail address when their video is posted to YouTube.
    
    Guaranteed zero-disruption: catches and logs any SMTP or network exceptions without bubbling up.
    """
    if not to_email or "@" not in to_email:
        logger.warning(f"[Notifications] Invalid recipient email address: '{to_email}'")
        return False

    clean_user = (settings.smtp_user or "").strip()
    clean_password = (settings.smtp_password or "").strip().replace(" ", "")

    # Fallback: if not set in environment (e.g. GitHub Actions runner without secrets), check MongoDB system_config
    if not clean_user or not clean_password:
        try:
            from backend.app.core.db import SyncMongoDB
            db = SyncMongoDB.get_db()
            cfg = db.system_config.find_one({"key": "smtp_config"})
            if cfg:
                clean_user = clean_user or (cfg.get("smtp_user") or "").strip()
                clean_password = clean_password or (cfg.get("smtp_password") or "").strip().replace(" ", "")
        except Exception as dbe:
            logger.debug(f"[Notifications] Could not fetch fallback SMTP config from DB: {dbe}")

    # Check if SMTP credentials are configured
    if not clean_user or not clean_password:
        logger.info(
            f"[Notifications] SMTP credentials not set in environment or database. "
            f"Skipped sending email notification to {to_email}."
        )
        return False

    tz = timezone_name or settings.timezone
    time_str = format_published_time(published_time, tz_name=tz)
    text_content, html_content = build_email_content(
        to_email=to_email,
        video_title=video_title,
        video_url=video_url,
        published_time_str=time_str,
        channel_title=channel_title,
        workspace_name=workspace_name
    )

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"🎬 Your YouTube Short is Live: {video_title}"
    msg["From"] = f"{settings.smtp_from_name} <{clean_user}>"
    msg["To"] = to_email
    if cc_email and "@" in cc_email:
        msg["Cc"] = cc_email

    msg.attach(MIMEText(text_content, "plain", "utf-8"))
    msg.attach(MIMEText(html_content, "html", "utf-8"))

    try:
        if settings.smtp_port == 465:
            try:
                with smtplib.SMTP_SSL(settings.smtp_host, 465, timeout=25) as server:
                    server.login(clean_user, clean_password)
                    server.send_message(msg)
            except Exception as ssl_err:
                logger.info(f"[Notifications] Port 465 SSL connection failed ({ssl_err}). Retrying via STARTTLS port 587...")
                with smtplib.SMTP(settings.smtp_host, 587, timeout=20) as server:
                    server.starttls()
                    server.login(clean_user, clean_password)
                    server.send_message(msg)
        else:
            try:
                with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=20) as server:
                    if settings.smtp_use_tls:
                        server.starttls()
                    server.login(clean_user, clean_password)
                    server.send_message(msg)
            except Exception as tls_err:
                logger.info(f"[Notifications] Port {settings.smtp_port} failed ({tls_err}). Retrying via SSL port 465...")
                with smtplib.SMTP_SSL(settings.smtp_host, 465, timeout=25) as server:
                    server.login(clean_user, clean_password)
                    server.send_message(msg)

        logger.info(f"📧 [Notifications] Successfully sent publication email to {to_email} for Short '{video_title}'")
        return True

    except Exception as err:
        logger.warning(f"⚠️ [Notifications] Failed to send publication email to {to_email}: {err}")
        return False


def notify_workspace_owner_video_published(
    workspace_id: Optional[str],
    video_title: str,
    video_url: str,
    published_time: Optional[datetime] = None,
    channel_id: Optional[str] = None
) -> bool:
    """
    Look up workspace owner in MongoDB and dispatch post-publish notification to their Gmail.
    
    Safe wrapper: guaranteed never to raise exceptions into the calling pipeline.
    """
    try:
        from backend.app.core.db import SyncMongoDB
        db = SyncMongoDB.get_db()

        ws = None
        if workspace_id:
            try:
                ws = db.workspaces.find_one({"_id": ObjectId(workspace_id)})
            except Exception:
                ws = db.workspaces.find_one({"_id": workspace_id})

        if not ws:
            ws = db.workspaces.find_one({"is_legacy_default": True}) or db.workspaces.find_one()

        if not ws:
            logger.warning("[Notifications] No workspace found to resolve owner email for notification.")
            return False

        owner_id = ws.get("owner_id")
        user = None
        if owner_id:
            try:
                user = db.users.find_one({"_id": ObjectId(owner_id)})
            except Exception:
                user = db.users.find_one({"_id": owner_id})

        if not user or not user.get("email"):
            # Fallback to owner email if legacy
            if ws.get("is_legacy_default"):
                from backend.app.core.migration import OWNER_EMAIL
                recipient = OWNER_EMAIL
            else:
                logger.warning(f"[Notifications] Workspace {workspace_id} owner has no registered email.")
                return False
        else:
            recipient = user.get("email")

        # Lookup channel title if available
        cid = channel_id or ws.get("connected_channel_id")
        ch_doc = db.youtube_channels.find_one({"channel_id": cid}) if cid else None
        ch_title = ch_doc.get("title") if ch_doc else None

        tz = ws.get("schedule", {}).get("timezone") or settings.timezone

        # Send to the user's Gmail; if it is a tenant user, also CC the platform owner
        from backend.app.core.migration import OWNER_EMAIL
        owner_admin = OWNER_EMAIL.lower()
        cc_target = owner_admin if recipient.lower() != owner_admin else None

        return send_video_published_email(
            to_email=recipient,
            video_title=video_title,
            video_url=video_url,
            published_time=published_time,
            channel_title=ch_title,
            workspace_name=ws.get("name"),
            timezone_name=tz,
            cc_email=cc_target
        )

    except Exception as e:
        logger.warning(f"[Notifications] Error resolving workspace owner for notification: {e}")
        return False

"""
Email Preprocessing Module

This module implements the "Holy Trinity" of email parsing to dramatically reduce
token count while preserving critical content for LLM opportunity detection.

The three-stage cleaning process:
1. BeautifulSoup: Strip HTML, CSS, and structural tags
2. email_reply_parser: Remove email thread history (quoted replies)
3. Regex: Clean up excessive whitespace and formatting artifacts

Typical result: 9,000 token raw email → 150 token clean content
"""

from bs4 import BeautifulSoup
from email_reply_parser import EmailReplyParser
import re
import logging

logger = logging.getLogger(__name__)


def clean_email_payload(raw_content: str, max_tokens: int = 3000) -> str:
    """
    Clean email content by removing HTML, CSS, metadata, and thread history.
    
    This is the core preprocessing function that applies the "Holy Trinity" approach:
    - Stage 1: HTML/CSS stripping with BeautifulSoup
    - Stage 2: Thread history removal with email_reply_parser
    - Stage 3: Whitespace normalization with regex
    
    Args:
        raw_content: Raw email content (can be HTML or plain text)
        max_tokens: Maximum tokens to allow (default: 6000, safe for 8192 limit)
        
    Returns:
        Cleaned email text with only essential content
        
    Example:
        >>> raw = "<html><body><p>Apply now!</p><div>On Tue, Bob wrote: ...</div></body></html>"
        >>> clean = clean_email_payload(raw)
        >>> print(clean)
        "Apply now!"
    """
    if not raw_content or not raw_content.strip():
        return ""
    
    try:
        # ─────────────────────────────────────────────────────────────────────
        # STAGE 1: Nuke HTML/CSS and extract visible text
        # ─────────────────────────────────────────────────────────────────────
        soup = BeautifulSoup(raw_content, "html.parser")
        
        # Remove script and style tags entirely (they contain no useful content)
        for script_or_style in soup(["script", "style"]):
            script_or_style.decompose()
        
        # Optional: Extract href URLs from links and append them as text
        # This preserves application links that might only be in href attributes
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            # Only preserve http/https URLs (skip mailto:, tel:, etc.)
            if href.startswith('http'):
                # Append URL after link text if not already present
                link_text = link.get_text()
                if href not in link_text:
                    link.string = f"{link_text} {href}"
        
        # Extract text with newlines preserved between elements
        text = soup.get_text(separator="\n")
        
        # ─────────────────────────────────────────────────────────────────────
        # STAGE 2: Strip previous replies in the thread
        # This removes "On Tuesday, Bob wrote:" and everything after
        # Only apply if the text looks like it has thread history
        # ─────────────────────────────────────────────────────────────────────
        if any(marker in text for marker in ['On ', ' wrote:', '---', '> ']):
            fresh_text = EmailReplyParser.parse_reply(text)
        else:
            fresh_text = text
        
        # ─────────────────────────────────────────────────────────────────────
        # STAGE 3: Regex cleanup
        # ─────────────────────────────────────────────────────────────────────
        
        # Remove excessive blank lines (3+ newlines → 2 newlines)
        clean_text = re.sub(r'\n\s*\n\s*\n+', '\n\n', fresh_text)
        
        # Remove trailing/leading whitespace on each line
        lines = [line.strip() for line in clean_text.split('\n')]
        clean_text = '\n'.join(lines)
        
        # Remove common email artifacts
        # Remove "View in browser" links (but preserve other links)
        clean_text = re.sub(r'View\s+(?:this\s+)?(?:email\s+)?in\s+(?:your\s+)?browser', '', clean_text, flags=re.IGNORECASE)
        
        # Remove "Unsubscribe" links (but preserve other content)
        clean_text = re.sub(r'Unsubscribe\s*(?:\||$)', '', clean_text, flags=re.IGNORECASE | re.MULTILINE)
        
        # Remove email footers (common patterns)
        clean_text = re.sub(r'This email was sent to\s+[\w\.\-]+@[\w\.\-]+', '', clean_text, flags=re.IGNORECASE)
        clean_text = re.sub(r'You received this (?:email|message) because.*$', '', clean_text, flags=re.IGNORECASE | re.MULTILINE)
        
        # Remove excessive spaces (multiple spaces → single space)
        clean_text = re.sub(r' {2,}', ' ', clean_text)
        
        # Final cleanup: remove leading/trailing whitespace
        clean_text = clean_text.strip()
        
        # ─────────────────────────────────────────────────────────────────────
        # STAGE 4: Token limit safety check
        # If email is still too large after cleaning, truncate intelligently
        # ─────────────────────────────────────────────────────────────────────
        estimated_tokens = estimate_token_count(clean_text)
        
        if estimated_tokens > max_tokens:
            logger.warning(
                f"Email still exceeds token limit after preprocessing: "
                f"{estimated_tokens} tokens (limit: {max_tokens}). Truncating intelligently."
            )
            
            # Truncate to max_tokens worth of characters
            # Keep first portion (most important content is usually at the top)
            max_chars = max_tokens * 4  # ~4 chars per token
            
            if len(clean_text) > max_chars:
                # Try to truncate at a sentence boundary
                truncated = clean_text[:max_chars]
                last_period = truncated.rfind('.')
                last_newline = truncated.rfind('\n')
                
                # Truncate at last sentence or paragraph
                cutoff = max(last_period, last_newline)
                if cutoff > max_chars * 0.8:  # Only if we're not losing too much
                    clean_text = truncated[:cutoff + 1]
                else:
                    clean_text = truncated
                
                clean_text += "\n\n[Email truncated due to length]"
        
        # Log token reduction estimate
        original_length = len(raw_content)
        cleaned_length = len(clean_text)
        reduction_pct = ((original_length - cleaned_length) / original_length * 100) if original_length > 0 else 0
        
        logger.debug(
            f"Email preprocessing: {original_length} chars → {cleaned_length} chars "
            f"({reduction_pct:.1f}% reduction)"
        )
        
        return clean_text
        
    except Exception as e:
        logger.warning(f"Email preprocessing failed: {str(e)}. Returning original content.")
        # Fallback: return original content if preprocessing fails
        return raw_content.strip()


def preprocess_email_batch(emails: list[str]) -> list[str]:
    """
    Preprocess a batch of emails for LLM processing.
    
    Applies clean_email_payload to each email in the batch.
    Useful for processing multiple emails before sending to LLM.
    
    Args:
        emails: List of raw email content strings
        
    Returns:
        List of cleaned email content strings
        
    Example:
        >>> raw_emails = ["<html>Email 1</html>", "<html>Email 2</html>"]
        >>> clean_emails = preprocess_email_batch(raw_emails)
        >>> len(clean_emails)
        2
    """
    cleaned_emails = []
    
    for i, email_content in enumerate(emails):
        try:
            cleaned = clean_email_payload(email_content)
            cleaned_emails.append(cleaned)
            
            if (i + 1) % 10 == 0:
                logger.info(f"Preprocessed {i + 1}/{len(emails)} emails")
                
        except Exception as e:
            logger.warning(f"Failed to preprocess email {i + 1}: {str(e)}")
            # Keep original if preprocessing fails
            cleaned_emails.append(email_content)
    
    logger.info(f"Successfully preprocessed {len(cleaned_emails)}/{len(emails)} emails")
    return cleaned_emails


def estimate_token_count(text: str) -> int:
    """
    Rough estimate of token count for a text string.
    
    Uses a simple heuristic: ~4 characters per token (typical for English text).
    This is an approximation - actual token count depends on the tokenizer.
    
    Args:
        text: Text string to estimate
        
    Returns:
        Estimated token count
        
    Example:
        >>> estimate_token_count("Hello world")
        3
    """
    # Rough heuristic: 1 token ≈ 4 characters for English text
    return len(text) // 4


def get_preprocessing_stats(raw_content: str, cleaned_content: str) -> dict:
    """
    Get detailed statistics about preprocessing results.
    
    Useful for monitoring and debugging preprocessing effectiveness.
    
    Args:
        raw_content: Original raw email content
        cleaned_content: Cleaned email content
        
    Returns:
        Dictionary with preprocessing statistics
        
    Example:
        >>> stats = get_preprocessing_stats(raw_html, cleaned_text)
        >>> print(stats['token_reduction_pct'])
        94.5
    """
    raw_chars = len(raw_content)
    clean_chars = len(cleaned_content)
    
    raw_tokens = estimate_token_count(raw_content)
    clean_tokens = estimate_token_count(cleaned_content)
    
    char_reduction = ((raw_chars - clean_chars) / raw_chars * 100) if raw_chars > 0 else 0
    token_reduction = ((raw_tokens - clean_tokens) / raw_tokens * 100) if raw_tokens > 0 else 0
    
    return {
        'raw_chars': raw_chars,
        'cleaned_chars': clean_chars,
        'char_reduction_pct': round(char_reduction, 2),
        'estimated_raw_tokens': raw_tokens,
        'estimated_clean_tokens': clean_tokens,
        'token_reduction_pct': round(token_reduction, 2)
    }

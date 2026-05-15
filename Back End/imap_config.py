"""
IMAP Configuration Module

Provides IMAP server configurations for popular email providers
and auto-detection based on email domain.
"""

from typing import Dict, Tuple
import logging

logger = logging.getLogger(__name__)

# IMAP server configurations for popular email providers
IMAP_SERVERS = {
    'gmail': {
        'host': 'imap.gmail.com',
        'port': 993,
        'name': 'Gmail',
        'setup_url': 'https://myaccount.google.com/apppasswords',
        'instructions': [
            'Go to your Google Account settings (myaccount.google.com) and navigate to the Security tab.',
            'Ensure 2-Step Verification is turned on.',
            'Scroll down and click on App passwords (or go directly to myaccount.google.com/apppasswords).',
            'Select Other (Custom name) from the app dropdown and type "Opportunity Inbox Copilot".',
            'Click Create.',
            'Copy the 16-character string immediately, as you won\'t be able to see it again once you close the window.'
        ]
    },
    'yahoo': {
        'host': 'imap.mail.yahoo.com',
        'port': 993,
        'name': 'Yahoo Mail',
        'setup_url': 'https://login.yahoo.com/account/security',
        'instructions': [
            'Log into Yahoo Mail, click your profile icon, and select Account Info.',
            'In the left sidebar, click on Account Security.',
            'Scroll down and click Manage App Passwords.',
            'Click Select App, choose Other App, and name it "Opportunity Inbox Copilot".',
            'Click Generate and copy the 16-character password provided.'
        ]
    },
    'outlook': {
        'host': 'outlook.office365.com',
        'port': 993,
        'name': 'Outlook/Hotmail',
        'setup_url': 'https://account.microsoft.com/security',
        'instructions': [
            'Log into your Microsoft Account and navigate to Security.',
            'Click on Advanced security options.',
            'Make sure Two-Step Verification is turned on.',
            'Scroll down to the App passwords section and click Create a new app password.',
            'Copy the generated password for your Copilot setup.'
        ]
    },
    'icloud': {
        'host': 'imap.mail.me.com',
        'port': 993,
        'name': 'iCloud Mail',
        'setup_url': 'https://appleid.apple.com/account/manage',
        'instructions': [
            'Sign in to your Apple ID account at appleid.apple.com.',
            'Navigate to the Sign-In and Security section.',
            'Select App-Specific Passwords.',
            'Click Generate an app-specific password or the "+" icon.',
            'Name it "Opportunity Inbox Copilot", click Create, and copy the generated password.'
        ]
    },
    'aol': {
        'host': 'imap.aol.com',
        'port': 993,
        'name': 'AOL Mail',
        'setup_url': 'https://login.aol.com/account/security',
        'instructions': [
            'Log into your AOL account and go to Account Security.',
            'Ensure 2-Step Verification is enabled.',
            'Click on Manage app passwords.',
            'Select Other app from the dropdown, type in "Opportunity Inbox Copilot", and hit Generate.',
            'Copy the password to your clipboard.'
        ]
    },
    'zoho': {
        'host': 'imap.zoho.com',
        'port': 993,
        'name': 'Zoho Mail',
        'setup_url': 'https://accounts.zoho.com/home#security/application',
        'instructions': [
            'Log in to your Zoho Account and go to My Account.',
            'Navigate to the Security tab and click on App Passwords.',
            'Click Generate New Password.',
            'Enter the app name ("Opportunity Inbox Copilot") and click Generate.',
            'Copy the password.'
        ]
    },
    'protonmail': {
        'host': '127.0.0.1',
        'port': 1143,
        'name': 'ProtonMail',
        'setup_url': 'https://proton.me/mail/bridge',
        'instructions': [
            'Note: ProtonMail uses end-to-end encryption, so standard app passwords over public IMAP/SMTP don\'t work directly. You must use the Proton Mail Bridge.',
            'Download and install the Proton Mail Bridge desktop application (requires a paid Proton plan).',
            'Open Proton Mail Bridge and log in with your standard Proton credentials.',
            'The Bridge app will automatically configure local IMAP/SMTP servers (usually running on 127.0.0.1).',
            'Click on your account within the Bridge app to view the configuration details. Bridge will display a specifically generated local password that you will use in your Copilot script.'
        ]
    },
    'fastmail': {
        'host': 'imap.fastmail.com',
        'port': 993,
        'name': 'FastMail',
        'setup_url': 'https://www.fastmail.com/settings/security/devicekeys',
        'instructions': [
            'Log into the Fastmail web interface and navigate to Settings → Privacy & Security.',
            'Under the "Connected apps & API tokens" section, click Manage app passwords and access.',
            'Click New app password.',
            'Select Custom to enter the name "Opportunity Inbox Copilot".',
            'Leave the default data access settings (Mail, Contacts & Calendars) and click Generate password.',
            'Copy the 16-character password provided.'
        ]
    },
}


def get_imap_config(email: str) -> Tuple[str, int, Dict]:
    """
    Auto-detect IMAP server configuration from email domain.
    
    Args:
        email: Email address (e.g., user@gmail.com)
        
    Returns:
        Tuple of (host, port, config_dict)
        
    Example:
        >>> host, port, config = get_imap_config('user@gmail.com')
        >>> print(host)
        'imap.gmail.com'
    """
    try:
        domain = email.split('@')[1].lower()
    except IndexError:
        logger.error(f"Invalid email format: {email}")
        raise ValueError(f"Invalid email format: {email}")
    
    # Check for known providers
    if 'gmail' in domain:
        config = IMAP_SERVERS['gmail']
    elif 'yahoo' in domain:
        config = IMAP_SERVERS['yahoo']
    elif 'outlook' in domain or 'hotmail' in domain or 'live' in domain:
        config = IMAP_SERVERS['outlook']
    elif 'icloud' in domain or 'me.com' in domain or 'mac.com' in domain:
        config = IMAP_SERVERS['icloud']
    elif 'aol' in domain:
        config = IMAP_SERVERS['aol']
    elif 'zoho' in domain:
        config = IMAP_SERVERS['zoho']
    elif 'protonmail' in domain or 'pm.me' in domain:
        config = IMAP_SERVERS['protonmail']
    elif 'fastmail' in domain:
        config = IMAP_SERVERS['fastmail']
    else:
        # Generic IMAP configuration for unknown providers
        logger.info(f"Unknown email provider: {domain}. Using generic IMAP configuration.")
        config = {
            'host': f'imap.{domain}',
            'port': 993,
            'name': domain.split('.')[0].title(),
            'setup_url': None,
            'instructions': [
                f'1. Contact your email provider ({domain}) for IMAP settings',
                '2. Enable IMAP access in your email account settings',
                '3. Generate an app-specific password if required',
                '4. Use the app password (not your regular email password)',
                f'5. Common IMAP server: imap.{domain}',
                '6. Common IMAP port: 993 (SSL/TLS)'
            ]
        }
    
    logger.info(f"Detected IMAP config for {email}: {config['name']} ({config['host']}:{config['port']})")
    
    return config['host'], config['port'], config


def get_setup_instructions(email: str) -> Dict:
    """
    Get setup instructions for a specific email provider.
    
    Args:
        email: Email address
        
    Returns:
        Dictionary with setup instructions
        
    Example:
        >>> instructions = get_setup_instructions('user@gmail.com')
        >>> print(instructions['name'])
        'Gmail'
    """
    _, _, config = get_imap_config(email)
    
    return {
        'provider': config['name'],
        'setup_url': config.get('setup_url'),
        'instructions': config['instructions']
    }


def list_supported_providers() -> Dict[str, Dict]:
    """
    List all supported email providers with their configurations.
    
    Returns:
        Dictionary of provider configurations
    """
    return {
        provider: {
            'name': config['name'],
            'host': config['host'],
            'port': config['port'],
            'setup_url': config.get('setup_url')
        }
        for provider, config in IMAP_SERVERS.items()
    }

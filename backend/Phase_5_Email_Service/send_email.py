#!/usr/bin/env python3
"""
Phase 5: Email Service
Send report via email with HTML body and PDF attachment
"""
import sys
import argparse
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from app.services.email import EmailService


def main():
    parser = argparse.ArgumentParser(
        description='Send Groww Playstore Reviews Report via Email'
    )
    parser.add_argument(
        '--role',
        type=str,
        required=True,
        choices=['Product', 'Support', 'UI/UX', 'Leadership'],
        help='Target role for the report'
    )
    parser.add_argument(
        '--recipient',
        type=str,
        required=True,
        help='Email address to send the report to'
    )
    parser.add_argument(
        '--html-file',
        type=str,
        default='..\\Phase_4_Report_Generation\\data\\groww_insights_ui_ux.html',
        help='Path to HTML file for email body'
    )
    parser.add_argument(
        '--pdf-file',
        type=str,
        default='..\\Phase_4_Report_Generation\\data\\groww_insights_ui_ux.pdf',
        help='Path to PDF file to attach'
    )
    parser.add_argument(
        '--subject',
        type=str,
        help='Custom email subject (optional)'
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("PHASE 5: EMAIL SERVICE")
    print("=" * 60)
    print()
    print(f"Role: {args.role}")
    print(f"Recipient: {args.recipient}")
    print(f"HTML File: {args.html_file}")
    print(f"PDF File: {args.pdf_file}")
    print()
    
    # Initialize email service
    email_service = EmailService()
    
    # Send email
    success = email_service.send_report(
        role=args.role,
        recipient=args.recipient,
        html_file=args.html_file,
        pdf_file=args.pdf_file,
        subject=args.subject
    )
    
    print()
    if success:
        print("=" * 60)
        print("OK: EMAIL SENT SUCCESSFULLY")
        print("=" * 60)
    else:
        print("=" * 60)
        print("ERROR: FAILED TO SEND EMAIL")
        print("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    main()

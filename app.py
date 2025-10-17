#!/usr/bin/env python3
"""
PayrollHQ Django Application Entry Point
This file helps Railway detect this as a Python web application
"""

import os
import sys
from django.core.wsgi import get_wsgi_application

# Add the project directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'payrollhq.settings')

# Get WSGI application
application = get_wsgi_application()

if __name__ == '__main__':
    # For development
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)
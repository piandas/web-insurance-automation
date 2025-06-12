"""Páginas del proyecto Allianz Automation."""

from src.utils import BasePage
from .login_page import LoginPage
from .dashboard_page import DashboardPage
from .flotas_page import FlotasPage

__all__ = ['BasePage', 'LoginPage', 'DashboardPage', 'FlotasPage']

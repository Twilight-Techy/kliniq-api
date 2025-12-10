# common/utils/global_functions.py
from typing import Any, Dict, Union
from fastapi import HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.models import User, UserRole

